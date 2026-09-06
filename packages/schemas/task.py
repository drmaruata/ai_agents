from enum import StrEnum
from typing import Any
from pydantic import BaseModel, Field


class AgentRole(StrEnum):
    RUATA = "ruata"
    KIMI = "kimi"
    MANASSEH = "manasseh"
    JOHN = "john"
    IAN = "ian"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


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


class TaskSpec(BaseModel):
    task_id: str
    project_id: str
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_level: RiskLevel = RiskLevel.LOW
    assigned_agent: AgentRole | None = None
    status: TaskStatus = TaskStatus.BACKLOG
    dependencies: list[str] = []
    allowed_paths: list[str] = []
    acceptance_criteria: list[str] = []
    metadata: dict[str, Any] = {}
