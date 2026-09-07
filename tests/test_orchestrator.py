from packages.schemas.domain import AgentRole, RiskLevel, TaskStatus
from services.orchestrator.ruata import RuataOrchestrator, TaskSpec


def test_ruata_plans_research_backend_frontend_and_qa():
    task = TaskSpec(
        task_id="TASK-1",
        project_id="project-1",
        title="Add booking cancellation UI and API",
        description="Add a frontend page and backend API with Supabase database changes.",
        risk_level=RiskLevel.HIGH,
    )
    plan = RuataOrchestrator().plan(task)
    assert [item.agent for item in plan] == [AgentRole.JOHN, AgentRole.MANASSEH, AgentRole.IAN]
    assert plan[-1].depends_on == ["TASK-1.backend", "TASK-1.frontend"]


def test_ruata_detects_research_requirement():
    task = TaskSpec(
        task_id="TASK-2",
        project_id="project-1",
        title="Compare payment libraries",
        description="Research compatible payment libraries and choose one.",
    )
    plan = RuataOrchestrator().plan(task)
    assert plan[0].agent == AgentRole.KIMI
    assert plan[0].action == "research_and_architecture"


def test_ruata_routes_mobile_work_to_moses():
    task = TaskSpec(
        task_id="TASK-3",
        project_id="project-1",
        title="Build iOS and Android mobile app",
        description="Create a React Native/Expo mobile app with Supabase authentication.",
    )
    plan = RuataOrchestrator().plan(task)
    mobile = next(item for item in plan if item.agent == AgentRole.MOSES)
    assert mobile.action == "mobile_implementation"
    assert mobile.id == "TASK-3.mobile"
    assert "mobile tests pass" in mobile.acceptance_criteria
    assert plan[-1].depends_on == ["TASK-3.backend", "TASK-3.mobile"]


def test_ruata_routes_cross_platform_work_to_all_required_specialists():
    task = TaskSpec(
        task_id="TASK-4",
        project_id="project-1",
        title="Add mobile and web booking experiences",
        description="Build a responsive web UI and Android/iOS client using the shared Supabase backend API.",
    )
    plan = RuataOrchestrator().plan(task)
    agents = [item.agent for item in plan]
    assert AgentRole.JOHN in agents
    assert AgentRole.MANASSEH in agents
    assert AgentRole.MOSES in agents
    assert plan[-1].agent == AgentRole.IAN
    assert plan[-1].depends_on == ["TASK-4.backend", "TASK-4.frontend", "TASK-4.mobile"]


def test_ruata_status_transition_logic():
    planner = RuataOrchestrator()
    assert planner.next_status(TaskStatus.VALIDATING, validation_passed=True, requires_approval=False) == TaskStatus.REVIEW
    assert planner.next_status(TaskStatus.VALIDATING, validation_passed=False, requires_approval=False) == TaskStatus.REPAIR
    assert planner.next_status(TaskStatus.REVIEW, validation_passed=True, requires_approval=True) == TaskStatus.HUMAN_APPROVAL
