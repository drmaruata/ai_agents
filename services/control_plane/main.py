from __future__ import annotations

from typing import Any
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from packages.schemas.domain import AgentRole, AuditEvent, AuditEventType, Task, TaskStatus, Workspace, utc_now
from services.agents.runtime import AgentRuntime
from services.agents.service import AgentExecutionService
from services.identity.service import IdentityService
from services.orchestrator.service import OrchestrationService
from services.persistence.repository import InMemoryRepository, PostgresRepository, Repository

from .auth import authenticate, issue_dev_token
from .settings import settings


class TaskCreate(BaseModel):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: str = "low"
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


repository: Repository = PostgresRepository(settings.database_url) if settings.database_url else InMemoryRepository()
orchestrator = OrchestrationService(repository)
agent_execution = AgentExecutionService(repository, AgentRuntime(settings.model_name))
identity = IdentityService()
app = FastAPI(title="Ruata Control Plane", version="0.5.0")
connections: set[WebSocket] = set()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "control-plane", "environment": settings.environment}


@app.post("/api/auth/dev-token")
def dev_token() -> dict[str, str]:
    if settings.environment != "development":
        raise HTTPException(status_code=404, detail="Not found")
    return {"access_token": issue_dev_token()}


@app.get("/api/agents")
def agents(_: str = Depends(authenticate)) -> list[dict[str, str]]:
    return [
        {"id": AgentRole.RUATA.value, "name": "Ruata", "role": "orchestrator", "status": "idle"},
        {"id": AgentRole.KIMI.value, "name": "Kimi", "role": "research_architecture", "status": "idle"},
        {"id": AgentRole.MANASSEH.value, "name": "Manasseh", "role": "frontend", "status": "idle"},
        {"id": AgentRole.JOHN.value, "name": "John", "role": "backend_data", "status": "idle"},
        {"id": AgentRole.IAN.value, "name": "Ian", "role": "qa_security_reliability", "status": "idle"},
    ]


@app.post("/api/agents/run")
async def run_agent(payload: AgentRunCreate, _: str = Depends(authenticate)) -> dict[str, Any]:
    if repository.get_task(payload.task_id) is None:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        run, output = await agent_execution.run(task_id=payload.task_id, agent=payload.agent, prompt=payload.prompt)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Agent execution failed: {exc}") from exc
    return {"run": run.model_dump(mode="json"), "output": output}


@app.post("/api/devices/enrollment-code")
def create_enrollment(_: str = Depends(authenticate)) -> dict[str, str]:
    return {"code": identity.create_enrollment_code("local-developer")}


@app.post("/api/devices/enroll")
def enroll_device(payload: EnrollmentComplete) -> dict[str, Any]:
    try:
        device = identity.enroll_device(
            code=payload.code,
            device_id=payload.device_id,
            name=payload.name,
            platform=payload.platform,
            hostname=payload.hostname,
            vs_code_version=payload.vscode_version,
            bridge_version=payload.bridge_version,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"device": device.model_dump(mode="json"), "status": "registered"}


@app.get("/api/devices")
def list_devices(_: str = Depends(authenticate)) -> list[dict[str, Any]]:
    return [device.model_dump(mode="json") for device in identity.devices.values()]


@app.post("/api/workspaces", response_model=Workspace)
def register_workspace(payload: WorkspaceRegister, _: str = Depends(authenticate)) -> Workspace:
    try:
        return identity.register_workspace(Workspace(**payload.model_dump()))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/workspaces")
def list_workspaces(_: str = Depends(authenticate)) -> list[dict[str, Any]]:
    return [workspace.model_dump(mode="json") for workspace in identity.workspaces.values()]


@app.post("/api/tasks", response_model=Task)
async def create_task(payload: TaskCreate, user_id: str = Depends(authenticate)) -> Task:
    task = Task(task_id=f"TASK-{uuid4().hex[:8].upper()}", **payload.model_dump())
    repository.create_task(task)
    repository.audit(AuditEvent(event_id=str(uuid4()), event_type=AuditEventType.TASK_CREATED, actor=user_id, task_id=task.task_id, metadata={"project_id": task.project_id}))
    await broadcast({"event": "task.created", "task": task.model_dump(mode="json")})
    return task


@app.post("/api/tasks/{task_id}/plan", response_model=list[Task])
async def plan_task(task_id: str, _: str = Depends(authenticate)) -> list[Task]:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    if task.status == TaskStatus.BACKLOG:
        task = repository.transition_task(task.task_id, TaskStatus.ANALYZING, task.version)
        task = repository.transition_task(task.task_id, TaskStatus.PLANNED, task.version)
    children = orchestrator.plan_task(task)
    await broadcast({"event": "task.planned", "task_id": task_id, "children": [item.model_dump(mode="json") for item in children]})
    return children


@app.get("/api/tasks", response_model=list[Task])
def list_tasks(project_id: str | None = None, _: str = Depends(authenticate)) -> list[Task]:
    return repository.list_tasks(project_id)


@app.get("/api/tasks/{task_id}", response_model=Task)
def get_task(task_id: str, _: str = Depends(authenticate)) -> Task:
    task = repository.get_task(task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks/{task_id}/transition", response_model=Task)
async def transition_task(task_id: str, payload: TaskTransition, user_id: str = Depends(authenticate)) -> Task:
    try:
        task = repository.transition_task(task_id, payload.status, payload.expected_version)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Task not found") from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    repository.audit(AuditEvent(event_id=str(uuid4()), event_type=AuditEventType.TASK_TRANSITIONED, actor=user_id, task_id=task_id, metadata={"status": task.status.value, "version": task.version}))
    await broadcast({"event": "task.transitioned", "task": task.model_dump(mode="json")})
    return task


@app.websocket("/ws/events")
async def events(websocket: WebSocket) -> None:
    await websocket.accept()
    connections.add(websocket)
    try:
        await websocket.send_json({"event": "connection.ready", "at": utc_now().isoformat()})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connections.discard(websocket)


@app.websocket("/ws/bridge")
async def bridge(websocket: WebSocket) -> None:
    provided = websocket.query_params.get("token")
    if settings.local_bridge_token and provided != settings.local_bridge_token:
        await websocket.close(code=1008, reason="unauthorized")
        return
    await websocket.accept()
    try:
        await websocket.send_json({"event": "bridge.ready", "protocol": "1"})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        return


async def broadcast(message: dict[str, Any]) -> None:
    stale: list[WebSocket] = []
    for connection in connections:
        try:
            await connection.send_json(message)
        except Exception:
            stale.append(connection)
    for connection in stale:
        connections.discard(connection)
