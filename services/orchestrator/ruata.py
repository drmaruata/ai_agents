from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from packages.schemas.domain import AgentRole, RiskLevel, TaskStatus


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
    project_id: str
    title: str
    description: str
    risk_level: RiskLevel = RiskLevel.LOW
    acceptance_criteria: list[str] = field(default_factory=list)
    allowed_paths: list[str] = field(default_factory=list)
    metadata: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class PlannedTask:
    id: str
    parent_task_id: str
    agent: AgentRole
    action: str
    depends_on: list[str] = field(default_factory=list)
    risk_level: RiskLevel = RiskLevel.LOW
    acceptance_criteria: list[str] = field(default_factory=list)


class RuataOrchestrator:
    """Deterministic task planner; model-backed reasoning can refine the plan later."""

    def classify(self, task: TaskSpec) -> dict[str, bool]:
        text = f"{task.title} {task.description}".lower()
        research_terms = ("research", "compare", "architecture", "library", "framework", "integration", "migration")
        mobile_terms = (
            "mobile", "ios", "android", "react native", "react-native", "expo", "flutter", "swiftui",
            "swift", "kotlin", "apk", "ipa", "mobile app", "app store", "play store"
        )
        return {
            "research_required": any(term in text for term in research_terms),
            "frontend_required": any(term in text for term in ("ui", "ux", "frontend", "page", "component", "form", "dashboard", "web app")),
            "backend_required": any(term in text for term in ("api", "backend", "database", "auth", "server", "supabase")),
            "mobile_required": any(term in text for term in mobile_terms),
            "qa_required": True,
        }

    def plan(self, task: TaskSpec, research_required: bool | None = None) -> list[PlannedTask]:
        classification = self.classify(task)
        if research_required is None:
            research_required = classification["research_required"]

        plan: list[PlannedTask] = []
        research_id = f"{task.task_id}.research"
        if research_required:
            plan.append(PlannedTask(
                id=research_id,
                parent_task_id=task.task_id,
                agent=AgentRole.KIMI,
                action="research_and_architecture",
                acceptance_criteria=["research.md", "architecture decision", "implementation guidance"],
            ))

        implementation_dependency = [research_id] if research_required else []
        if classification["backend_required"]:
            plan.append(PlannedTask(
                id=f"{task.task_id}.backend",
                parent_task_id=task.task_id,
                agent=AgentRole.JOHN,
                action="backend_implementation",
                depends_on=implementation_dependency,
                risk_level=max(task.risk_level, RiskLevel.MEDIUM, key=lambda r: list(RiskLevel).index(r)),
                acceptance_criteria=["backend tests pass", "contract validated"],
            ))
        if classification["frontend_required"]:
            plan.append(PlannedTask(
                id=f"{task.task_id}.frontend",
                parent_task_id=task.task_id,
                agent=AgentRole.MANASSEH,
                action="frontend_implementation",
                depends_on=implementation_dependency.copy(),
                risk_level=task.risk_level,
                acceptance_criteria=["frontend tests pass", "browser validation passes"],
            ))
        if classification["mobile_required"]:
            plan.append(PlannedTask(
                id=f"{task.task_id}.mobile",
                parent_task_id=task.task_id,
                agent=AgentRole.MOSES,
                action="mobile_implementation",
                depends_on=implementation_dependency.copy(),
                risk_level=task.risk_level,
                acceptance_criteria=["mobile tests pass", "platform build validation passes", "mobile accessibility checks pass"],
            ))

        implementation_ids = [
            item.id for item in plan
            if item.agent in {AgentRole.JOHN, AgentRole.MANASSEH, AgentRole.MOSES}
        ]
        plan.append(PlannedTask(
            id=f"{task.task_id}.qa",
            parent_task_id=task.task_id,
            agent=AgentRole.IAN,
            action="validate_and_review",
            depends_on=implementation_ids or implementation_dependency,
            risk_level=task.risk_level,
            acceptance_criteria=["static checks pass", "tests pass", "security checks pass"],
        ))
        return plan

    def next_status(self, current: TaskStatus, *, validation_passed: bool, requires_approval: bool) -> TaskStatus:
        if current == TaskStatus.VALIDATING:
            return TaskStatus.REVIEW if validation_passed else TaskStatus.REPAIR
        if current == TaskStatus.REVIEW:
            return TaskStatus.HUMAN_APPROVAL if requires_approval else TaskStatus.COMPLETED
        if current == TaskStatus.HUMAN_APPROVAL:
            return TaskStatus.COMPLETED if validation_passed else TaskStatus.REPAIR
        raise ValueError(f"No orchestration transition defined for {current.value}")
