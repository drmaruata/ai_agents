from __future__ import annotations

import json
import hmac
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row

from fastapi import Depends, FastAPI, Header, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from packages.schemas.domain import AgentRole, AuditEvent, AuditEventType, ApprovalStatus, DeviceStatus, RiskLevel, Task, TaskStatus, Workspace, utc_now
from services.agents.local_routes import build_router
from services.agents.runtime import AgentRuntime
from services.agents.service import AgentExecutionService
from services.approval.repository import InMemoryApprovalRepository, PostgresApprovalRepository
from services.approval.service import ApprovalService
from services.bridge.manager import BridgeConnectionManager
from services.identity.repository import PostgresIdentityRepository, InMemoryIdentityRepository
from services.identity.service import IdentityService
from services.observability.events import emit
from services.orchestrator.service import OrchestrationService
from services.persistence.repository import InMemoryRepository, PostgresRepository, Repository
from services.policy.defaults import DEFAULT_POLICIES
from services.policy.engine import PolicyContext, PolicyDenied, PolicyEngine

from .auth import authenticate, issue_dev_token
from .settings import settings


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    repository_url: str | None = Field(default=None, max_length=2048)
    default_branch: str = Field(default="main", min_length=1, max_length=255)


class TaskCreate(BaseModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: RiskLevel = RiskLevel.LOW
    acceptance_criteria: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskTransition(BaseModel):
    status: TaskStatus
    expected_version: int = Field(ge=1)


class AgentRunCreate(BaseModel):
    task_id: str = Field(min_length=1)
    agent: AgentRole
    prompt: str = Field(min_length=1)


class BridgeExecuteRequest(BaseModel):
    task_id: str | None = None
    approval_id: str | None = None
    device_id: str = Field(min_length=1)
    agent: AgentRole
    project_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    tool: str = Field(min_length=1)
    args: dict[str, Any] = Field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW


class ApprovalDecision(BaseModel):
    approved: bool
    reason: str | None = None


class EnrollmentComplete(BaseModel):
    code: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    hostname: str = Field(min_length=1)
    vscode_version: str | None = None
    bridge_version: str | None = None


class WorkspaceRegister(BaseModel):
    workspace_id: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    path: str = Field(min_length=1)


if settings.environment.lower() == "production":
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL must be configured in production; refusing in-memory persistence")
    if not (settings.supabase_url and settings.supabase_publishable_key):
        raise RuntimeError("Supabase Auth must be configured in production")
    if not settings.local_bridge_token or len(settings.local_bridge_token) < 32:
        raise RuntimeError("LOCAL_BRIDGE_TOKEN must be configured with at least 32 characters in production")


repository: Repository = PostgresRepository(settings.database_url) if settings.database_url else InMemoryRepository()
identity_repository = PostgresIdentityRepository(settings.database_url) if settings.database_url else InMemoryIdentityRepository()
orchestrator = OrchestrationService(repository)
agent_execution = AgentExecutionService(repository, AgentRuntime(settings.model_name))
identity = IdentityService(identity_repository)
bridge_manager = BridgeConnectionManager()
policy_engine = PolicyEngine(DEFAULT_POLICIES)
approval_repository = PostgresApprovalRepository(settings.database_url) if settings.database_url else InMemoryApprovalRepository()
approvals = ApprovalService(approval_repository)
app = FastAPI(title="Ruata Control Plane", version="0.11.0")
app.add_middleware(CORSMiddleware, allow_origins=list(dict.fromkeys(["http://localhost:3000", "http://127.0.0.1:3000"] + ([settings.dashboard_origin.rstrip("/")] if settings.dashboard_origin else []))), allow_credentials=True, allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "Idempotency-Key"])
event_connections: set[WebSocket] = set()


def supabase_auth_enabled() -> bool:
    return bool(settings.supabase_url and settings.supabase_publishable_key)


_RISK_ORDER = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


def validate_high_risk_approval(
    *,
    approval: Any,
    task_id: str | None,
    project_id: str,
    tool: str,
    risk_level: RiskLevel,
    task: Task | None,
) -> None:
    """Fail closed unless an approved record authorizes this exact execution."""
    if not task_id or task is None:
        raise ValueError("A valid task_id is required for high-risk local execution")
    if task.project_id != project_id:
        raise ValueError("Task does not belong to project")
    if approval is None or approval.status != ApprovalStatus.APPROVED:
        raise ValueError("Provided approval is not approved")
    if approval.task_id != task_id:
        raise ValueError("Approval does not match task")
    if approval.action != tool:
        raise ValueError("Approval does not authorize this tool")
    if approval.created_at < datetime.now(timezone.utc) - timedelta(hours=1):
        raise ValueError("Approval has expired")
    if _RISK_ORDER[approval.risk_level] < _RISK_ORDER[risk_level]:
        raise ValueError("Approval risk level is insufficient for this execution")


def require_project_access(user_id: str, project_id: str) -> None:
    if supabase_auth_enabled() and not identity.can_access_project(project_id, user_id):
        raise HTTPException(status_code=403, detail="User is not authorized for this project")


def require_workspace_access(user_id: str, workspace_id: str, project_id: str, device_id: str) -> None:
    if not supabase_auth_enabled():
        return
    require_project_access(user_id, project_id)
    if not identity.can_access_device(device_id, user_id):
        raise HTTPException(status_code=403, detail="User does not own the device")
    accessible = {item.workspace_id: item for item in identity.repository.list_workspaces(user_id=user_id)}
    workspace = accessible.get(workspace_id)
    if workspace is None or workspace.project_id != project_id or workspace.device_id != device_id:
        raise HTTPException(status_code=403, detail="User is not authorized for this workspace")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-plane", "environment": settings.environment}


@app.post("/api/auth/dev-token")
def dev_token() -> dict[str, str]:
    if settings.environment != "development" or supabase_auth_enabled():
        raise HTTPException(status_code=404, detail="Not found")
    return {"access_token": issue_dev_token()}


@app.get("/api/auth/me")
def auth_me(user_id: str = Depends(authenticate)) -> dict[str, str]:
    return {"user_id": user_id, "provider": "supabase" if supabase_auth_enabled() else "development"}


@app.get("/api/projects")
def list_projects(user_id: str = Depends(authenticate)) -> list[dict[str, Any]]:
    """List only projects owned by the authenticated user or shared through a workspace."""
    if not supabase_auth_enabled() or not settings.database_url:
        raise HTTPException(status_code=503, detail="Project listing requires configured Supabase Auth and PostgreSQL")
    with psycopg.connect(settings.database_url, row_factory=dict_row) as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT p.project_id, p.name, p.repository_url, p.default_branch, p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN workspaces w ON w.project_id = p.project_id
            LEFT JOIN workspace_members wm ON wm.workspace_id = w.workspace_id
            WHERE p.owner_id = %s OR wm.user_id = %s
            ORDER BY p.created_at DESC
            """,
            (user_id, user_id),
        )
        return [dict(row) for row in cur.fetchall()]


@app.post("/api/projects", status_code=201)
def create_project(payload: ProjectCreate, user_id: str = Depends(authenticate)) -> dict[str, Any]:
    """Create a project owned by the authenticated Supabase user."""
    if not supabase_auth_enabled() or not settings.database_url:
        raise HTTPException(status_code=503, detail="Project creation requires configured Supabase Auth and PostgreSQL")
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Project name cannot be blank")
    project_id = f"PRJ-{uuid4().hex[:12].upper()}"
    try:
        with psycopg.connect(settings.database_url, row_factory=dict_row) as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO projects (project_id, owner_id, name, repository_url, default_branch)
                VALUES (%s, %s, %s, %s, %s)
                RETURNING project_id, owner_id, name, repository_url, default_branch, created_at, updated_at
                """,
                (project_id, user_id, name, payload.repository_url, payload.default_branch),
            )
            created = dict(cur.fetchone())
    except psycopg.Error as exc:
        # Do not return database error text or SQL details to clients.
        emit("project.create.failed", actor=user_id, error=type(exc).__name__)
        raise HTTPException(status_code=503, detail="Unable to create project") from exc
    emit("project.created", actor=user_id, project_id=project_id)
    return created


@app.get("/api/agents")
def agents(_: str = Depends(authenticate)) -> list[dict[str, str]]:
    return [
        {"id": AgentRole.RUATA.value, "name": "Ruata", "role": "orchestrator", "status": "idle"},
        {"id": AgentRole.KIMI.value, "name": "Kimi", "role": "research_architecture", "status": "idle"},
        {"id": AgentRole.MANASSEH.value, "name": "Manasseh", "role": "frontend", "status": "idle"},
        {"id": AgentRole.JOHN.value, "name": "John", "role": "backend_data", "status": "idle"},
        {"id": AgentRole.MOSES.value, "name": "Moses", "role": "mobile", "status": "idle"},
        {"id": AgentRole.IAN.value, "name": "Ian", "role": "qa_security_reliability", "status": "idle"},
    ]


@app.post("/api/agents/run")
async def run_agent(payload: AgentRunCreate, user_id: str = Depends(authenticate)) -> dict[str, Any]:
    task = repository.get_task(payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    require_project_access(user_id, task.project_id)
    emit("agent.run.requested", actor=user_id, task_id=payload.task_id, agent=payload.agent.value)
    try:
        run, output = await agent_execution.run(task_id=payload.task_id, agent=payload.agent, prompt=payload.prompt)
    except Exception as exc:
        emit("agent.run.failed", actor=payload.agent.value, task_id=payload.task_id, error=str(exc))
        raise HTTPException(status_code=502, detail=f"Agent execution failed: {exc}") from exc
    emit("agent.run.completed", actor=payload.agent.value, task_id=payload.task_id, run_id=run.run_id)
    return {"run": run.model_dump(mode="json"), "output": output}


@app.post("/api/approvals/request")
def request_approval(task_id: str, action: str, risk_level: RiskLevel = RiskLevel.HIGH, user_id: str = Depends(authenticate)) -> dict[str, Any]:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    require_project_access(user_id, task.project_id)
    try:
        approval = approvals.request(task_id=task_id, action=action, risk_level=risk_level, requested_by=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    emit("approval.requested", actor=user_id, task_id=task_id, approval_id=approval.approval_id, risk_level=risk_level.value)
    return approval.model_dump(mode="json")


@app.get("/api/approvals")
def list_approvals(status: ApprovalStatus | None = None, user_id: str = Depends(authenticate)) -> list[dict[str, Any]]:
    values = []
    for item in approvals.list(status):
        task = repository.get_task(item.task_id)
        if task and (not supabase_auth_enabled() or identity.can_access_project(task.project_id, user_id)):
            values.append(item)
    return [item.model_dump(mode="json") for item in values]


@app.post("/api/approvals/{approval_id}/decide")
def decide_approval(approval_id: str, payload: ApprovalDecision, user_id: str = Depends(authenticate)) -> dict[str, Any]:
    existing = approvals.get(approval_id)
    if existing is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    task = repository.get_task(existing.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    require_project_access(user_id, task.project_id)
    try:
        approval = approvals.decide(approval_id, approved=payload.approved, decided_by=user_id, reason=payload.reason)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Approval not found") from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    emit("approval.decided", actor=user_id, task_id=approval.task_id, approval_id=approval.approval_id, status=approval.status.value)
    return approval.model_dump(mode="json")


@app.post("/api/devices/enrollment-code")
def create_enrollment(user_id: str = Depends(authenticate)) -> dict[str, str]:
    return {"code": identity.create_enrollment_code(user_id)}


@app.post("/api/devices/enroll")
def enroll_device(payload: EnrollmentComplete, user_id: str = Depends(authenticate)) -> dict[str, Any]:
    try:
        device = identity.enroll_device(code=payload.code, user_id=user_id, device_id=payload.device_id, name=payload.name, platform=payload.platform, hostname=payload.hostname, vscode_version=payload.vscode_version, bridge_version=payload.bridge_version)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"device": device.model_dump(mode="json"), "status": "registered"}


@app.get("/api/devices")
def list_devices(user_id: str = Depends(authenticate)) -> list[dict[str, Any]]:
    devices = identity.repository.list_devices(user_id=user_id) if supabase_auth_enabled() else identity.repository.list_devices()
    return [device.model_dump(mode="json") | {"bridge_connected": device.device_id in bridge_manager.connections} for device in devices]


@app.post("/api/workspaces", response_model=Workspace)
def register_workspace(payload: WorkspaceRegister, user_id: str = Depends(authenticate)) -> Workspace:
    require_project_access(user_id, payload.project_id)
    try:
        return identity.register_workspace(Workspace(**payload.model_dump()), user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/workspaces")
def list_workspaces(user_id: str = Depends(authenticate)) -> list[dict[str, Any]]:
    workspaces = identity.repository.list_workspaces(user_id=user_id) if supabase_auth_enabled() else identity.repository.list_workspaces()
    return [workspace.model_dump(mode="json") for workspace in workspaces]


@app.post("/api/bridge/execute")
async def execute_on_device(payload: BridgeExecuteRequest, user_id: str = Depends(authenticate)) -> dict[str, Any]:
    task = repository.get_task(payload.task_id) if payload.task_id else None
    if payload.task_id and task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    require_workspace_access(user_id, payload.workspace_id, payload.project_id, payload.device_id)
    if payload.task_id and task and task.project_id != payload.project_id:
        raise HTTPException(status_code=403, detail="Task does not belong to project")
    if payload.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
        approval = approvals.get(payload.approval_id) if payload.approval_id else None
        try:
            validate_high_risk_approval(
                approval=approval,
                task_id=payload.task_id,
                project_id=payload.project_id,
                tool=payload.tool,
                risk_level=payload.risk_level,
                task=task,
            )
        except ValueError as exc:
            repository.audit(AuditEvent(
                event_id=str(uuid4()),
                event_type=AuditEventType.TOOL_DENIED,
                actor=user_id,
                task_id=payload.task_id,
                device_id=payload.device_id,
                metadata={"tool": payload.tool, "reason": str(exc), "approval_id": payload.approval_id},
            ))
            raise HTTPException(status_code=403, detail=str(exc)) from exc
    try:
        policy_engine.authorize(PolicyContext(payload.agent, payload.project_id, payload.workspace_id, payload.tool, payload.risk_level, relative_path=payload.args.get("path"), command=shlex_join(payload.args.get("command", []))), write=payload.tool in {"file.write", "file.patch"})
        response = await bridge_manager.send_tool_request(payload.device_id, payload.tool, payload.args)
    except PolicyDenied as exc:
        repository.audit(AuditEvent(event_id=str(uuid4()), event_type=AuditEventType.TOOL_DENIED, actor=payload.agent.value, task_id=payload.task_id, device_id=payload.device_id, metadata={"tool": payload.tool, "reason": str(exc)}))
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except (ConnectionError, TimeoutError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    repository.audit(AuditEvent(event_id=str(uuid4()), event_type=AuditEventType.TOOL_EXECUTED, actor=payload.agent.value, task_id=payload.task_id, device_id=payload.device_id, metadata={"tool": payload.tool, "ok": response.get("ok", False)}))
    return response


def shlex_join(command: Any) -> str | None:
    if not command:
        return None
    if isinstance(command, list):
        import shlex
        return shlex.join([str(item) for item in command])
    return str(command)


@app.post("/api/tasks", response_model=Task)
async def create_task(payload: TaskCreate, user_id: str = Depends(authenticate), idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")) -> Task:
    require_project_access(user_id, payload.project_id)
    scope = f"task.create:{user_id}"
    if idempotency_key:
        stored = repository.get_idempotency(idempotency_key, scope)
        if stored:
            existing = Task.model_validate(stored)
            same_request = (
                existing.project_id == payload.project_id
                and existing.title == payload.title
                and existing.description == payload.description
                and existing.risk_level == payload.risk_level
                and existing.acceptance_criteria == payload.acceptance_criteria
                and existing.allowed_paths == payload.allowed_paths
                and existing.metadata == payload.metadata
            )
            if not same_request:
                raise HTTPException(status_code=409, detail="Idempotency-Key was already used for a different request")
            return existing
    task = Task(task_id=f"TASK-{uuid4().hex[:8].upper()}", **payload.model_dump())
    repository.create_task(task)
    repository.audit(AuditEvent(event_id=str(uuid4()), event_type=AuditEventType.TASK_CREATED, actor=user_id, task_id=task.task_id, metadata={"project_id": task.project_id}))
    if idempotency_key:
        repository.put_idempotency(idempotency_key, scope, task.model_dump(mode="json"))
    await broadcast({"event": "task.created", "task": task.model_dump(mode="json")})
    return task


@app.post("/api/tasks/{task_id}/plan", response_model=list[Task])
async def plan_task(task_id: str, user_id: str = Depends(authenticate)) -> list[Task]:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    require_project_access(user_id, task.project_id)
    if task.status == TaskStatus.BACKLOG:
        task = repository.transition_task(task.task_id, TaskStatus.ANALYZING, task.version, actor=user_id, reason="begin planning")
        task = repository.transition_task(task.task_id, TaskStatus.PLANNED, task.version, actor=user_id, reason="planning complete")
    children = orchestrator.plan_task(task)
    await broadcast({"event": "task.planned", "task_id": task_id, "children": [item.model_dump(mode="json") for item in children]})
    return children


@app.get("/api/tasks", response_model=list[Task])
def list_tasks(project_id: str | None = None, user_id: str = Depends(authenticate)) -> list[Task]:
    if supabase_auth_enabled():
        if not project_id:
            raise HTTPException(status_code=400, detail="project_id is required when Supabase authorization is enabled")
        require_project_access(user_id, project_id)
    return repository.list_tasks(project_id)


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: str, user_id: str = Depends(authenticate)) -> Task:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    require_project_access(user_id, task.project_id)
    return task


@app.post("/api/tasks/{task_id}/transition", response_model=Task)
async def transition_task(task_id: str, payload: TaskTransition, user_id: str = Depends(authenticate)) -> Task:
    current = repository.get_task(task_id)
    if current is None:
        raise HTTPException(status_code=404, detail="Task not found")
    require_project_access(user_id, current.project_id)
    try:
        task = repository.transition_task(task_id, payload.status, payload.expected_version, actor=user_id, reason="API transition")
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    repository.audit(AuditEvent(event_id=str(uuid4()), event_type=AuditEventType.TASK_TRANSITIONED, actor=user_id, task_id=task_id, metadata={"status": task.status.value, "version": task.version}))
    await broadcast({"event": "task.transitioned", "task": task.model_dump(mode="json")})
    return task


app.include_router(build_router(repository, bridge_manager, policy_engine, AgentRuntime(settings.model_name)))


@app.websocket("/ws/events")
async def events(websocket: WebSocket) -> None:
    await websocket.accept()
    event_connections.add(websocket)
    try:
        await websocket.send_json({"event": "connection.ready", "at": utc_now().isoformat()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_connections.discard(websocket)


@app.websocket("/ws/bridge")
async def bridge(websocket: WebSocket) -> None:
    device_id = websocket.query_params.get("device_id")
    provided = websocket.headers.get("authorization", "").removeprefix("Bearer ").strip()
    if not device_id or not provided:
        await websocket.close(code=1008, reason="unauthorized")
        return
    if settings.local_bridge_token:
        if not hmac.compare_digest(provided, settings.local_bridge_token):
            await websocket.close(code=1008, reason="unauthorized")
            return
    elif settings.environment.lower() == "production":
        await websocket.close(code=1008, reason="bridge authentication is not configured")
        return
    await websocket.accept()
    await bridge_manager.register(device_id, websocket)
    if device_id in identity.devices:
        identity.update_device_status(device_id, DeviceStatus.ONLINE)
    try:
        await websocket.send_json({"event": "bridge.ready", "protocol": "1", "device_id": device_id})
        while True:
            raw = await websocket.receive_text()
            bridge_manager.resolve_response(json.loads(raw))
    except WebSocketDisconnect:
        bridge_manager.unregister(device_id, websocket)
        if device_id in identity.devices:
            identity.update_device_status(device_id, DeviceStatus.OFFLINE)


async def broadcast(message: dict[str, Any]) -> None:
    stale: list[WebSocket] = []
    for connection in event_connections:
        try:
            await connection.send_json(message)
        except Exception:
            stale.append(connection)
    for connection in stale:
        event_connections.discard(connection)
