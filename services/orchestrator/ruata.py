from dataclasses import dataclass, field
from enum import StrEnum


class TaskPhase(StrEnum):
    ANALYZING = "analyzing"
    RESEARCH = "research"
    PLANNED = "planned"
    IMPLEMENTING = "implementing"
    VALIDATING = "validating"
    REVIEW = "review"
    HUMAN_APPROVAL = "human_approval"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(slots=True)
class TaskSpec:
    task_id: str
    title: str
    description: str
    risk_level: str = "low"
    phase: TaskPhase = TaskPhase.ANALYZING
    dependencies: list[str] = field(default_factory=list)


class RuataOrchestrator:
    """Initial orchestration skeleton; production model/tool adapters are added in later phases."""

    def plan(self, task: TaskSpec, research_required: bool = False) -> list[dict[str, str]]:
        tasks = []
        if research_required:
            tasks.append({"agent": "kimi", "action": "research", "task_id": task.task_id})
        tasks.extend(
            [
                {"agent": "john", "action": "backend", "task_id": task.task_id},
                {"agent": "manasseh", "action": "frontend", "task_id": task.task_id},
                {"agent": "ian", "action": "validate", "task_id": task.task_id},
            ]
        )
        return tasks
