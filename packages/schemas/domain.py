from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class AgentRole(StrEnum):
    RUATA = "ruata"
    KIMI = "kimi"
    MANASSEH = "manasseh"
    JOHN = "john"
    MOSES = "moses"
    IAN = "ian"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(StrEnum):
    BACKLOG = "backlog"
    ANALYZING = "analyzing"
    RESEARCH = "research"
    PLANNED = "planned"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    REPAIR = "repair"
    REVIEW = "review"
    HUMAN_APPROVAL = "human_approval"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class DeviceStatus(StrEnum):
    OFFLINE = "offline"
    ONLINE = "online"
    REVOKED = "revoked"


class ApprovalStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class RunStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class AuditEventType(StrEnum):
    TASK_CREATED = "task.created"
    TASK_TRANSITIONED = "task.transitioned"
    AGENT_ASSIGNED = "agent.assigned"
    TOOL_REQUESTED = "tool.requested"
    TOOL_EXECUTED = "tool.executed"
    TOOL_DENIED = "tool.denied"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_DECIDED = "approval.decided"
    DEVICE_CONNECTED = "device.connected"
    DEVICE_DISCONNECTED = "device.disconnected"
    EXECUTION_STARTED = "execution.started"
    EXECUTION_FINISHED = "execution.finished"
    SECURITY_EVENT = "security.event"


class DomainModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Project(DomainModel):
    project_id: str
    name: str = Field(min_length=1)
    repository_url: str | None = None
    default_branch: str = "main"
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Workspace(DomainModel):
    workspace_id: str
    project_id: str
    device_id: str
    path: str = Field(min_length=1)
    name: str = Field(min_length=1)
    registered: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class Device(DomainModel):
    device_id: str
    name: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    hostname: str = Field(min_length=1)
    status: DeviceStatus = DeviceStatus.OFFLINE
    vs_code_version: str | None = None
    bridge_version: str | None = None
    last_seen: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class Task(DomainModel):
    task_id: str
    project_id: str
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: RiskLevel = RiskLevel.LOW
    assigned_agent: AgentRole | None = None
    status: TaskStatus = TaskStatus.BACKLOG
    dependencies: list[str] = Field(default_factory=list)
    allowed_paths: list[str] = Field(default_factory=list)
    acceptance_criteria: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    version: int = 1
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class TaskDependency(DomainModel):
    task_id: str
    depends_on_task_id: str


class TaskRun(DomainModel):
    run_id: str
    task_id: str
    agent: AgentRole
    status: RunStatus = RunStatus.QUEUED
    attempt: int = 1
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None
    output_artifact_ids: list[str] = Field(default_factory=list)


class Execution(DomainModel):
    execution_id: str
    run_id: str
    tool_name: str
    input: dict[str, Any] = Field(default_factory=dict)
    status: RunStatus = RunStatus.QUEUED
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    duration_ms: int | None = None


class ToolPermission(DomainModel):
    tool_name: str
    agent: AgentRole
    project_id: str | None = None
    workspace_id: str | None = None
    allowed: bool = True
    risk_level: RiskLevel = RiskLevel.LOW
    path_globs: list[str] = Field(default_factory=list)
    command_allowlist: list[str] = Field(default_factory=list)
    network_allowlist: list[str] = Field(default_factory=list)


class ToolDefinition(DomainModel):
    name: str
    description: str
    risk_level: RiskLevel
    local: bool = True
    cancellable: bool = True
    timeout_seconds: int = 120


class Approval(DomainModel):
    approval_id: str
    task_id: str
    action: str
    risk_level: RiskLevel
    status: ApprovalStatus = ApprovalStatus.PENDING
    requested_by: str | None = None
    decided_by: str | None = None
    reason: str | None = None
    created_at: datetime = Field(default_factory=utc_now)
    decided_at: datetime | None = None


class Artifact(DomainModel):
    artifact_id: str
    task_id: str
    kind: str
    name: str
    uri: str | None = None
    content_type: str | None = None
    sha256: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class AgentMessage(DomainModel):
    message_id: str
    task_id: str
    sender: AgentRole
    recipient: AgentRole | None = None
    message_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


class TestCheck(DomainModel):
    name: str
    status: str
    severity: str | None = None
    message: str | None = None


class TestRun(DomainModel):
    test_run_id: str
    task_id: str
    status: RunStatus
    checks: list[TestCheck] = Field(default_factory=list)
    started_at: datetime = Field(default_factory=utc_now)
    finished_at: datetime | None = None
    recommendation: str | None = None


class Evaluation(DomainModel):
    evaluation_id: str
    agent: AgentRole | None = None
    suite: str
    scenario: str
    score: float = Field(ge=0, le=1)
    passed: bool
    notes: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class AuditEvent(DomainModel):
    event_id: str
    event_type: AuditEventType
    actor: str
    task_id: str | None = None
    device_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)


TASK_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.BACKLOG: {TaskStatus.ANALYZING, TaskStatus.BLOCKED},
    TaskStatus.ANALYZING: {TaskStatus.RESEARCH, TaskStatus.PLANNED, TaskStatus.BLOCKED},
    TaskStatus.RESEARCH: {TaskStatus.PLANNED, TaskStatus.BLOCKED},
    TaskStatus.PLANNED: {TaskStatus.IMPLEMENTING, TaskStatus.BLOCKED},
    TaskStatus.IMPLEMENTING: {TaskStatus.VALIDATING, TaskStatus.REPAIR, TaskStatus.FAILED, TaskStatus.BLOCKED},
    TaskStatus.VALIDATING: {TaskStatus.REVIEW, TaskStatus.REPAIR, TaskStatus.FAILED, TaskStatus.BLOCKED},
    TaskStatus.REPAIR: {TaskStatus.IMPLEMENTING, TaskStatus.VALIDATING, TaskStatus.FAILED, TaskStatus.BLOCKED},
    TaskStatus.REVIEW: {TaskStatus.HUMAN_APPROVAL, TaskStatus.REPAIR, TaskStatus.FAILED, TaskStatus.BLOCKED},
    TaskStatus.HUMAN_APPROVAL: {TaskStatus.COMPLETED, TaskStatus.REPAIR, TaskStatus.FAILED, TaskStatus.BLOCKED},
    TaskStatus.COMPLETED: set(),
    TaskStatus.FAILED: set(),
    TaskStatus.BLOCKED: set(),
}


def validate_task_transition(current: TaskStatus, target: TaskStatus) -> None:
    if target not in TASK_TRANSITIONS[current]:
        raise ValueError(f"Invalid task transition: {current.value} -> {target.value}")
