from packages.schemas.domain import Task, TaskStatus
from services.persistence.repository import InMemoryRepository


def make_task() -> Task:
    return Task(
        task_id="TASK-PERSIST-1",
        project_id="demo",
        title="Persistence test",
        description="Verify durable-state semantics",
    )


def test_in_memory_repository_records_task_state_history() -> None:
    repository = InMemoryRepository()
    task = repository.create_task(make_task())

    assert repository.state_history[0]["to_status"] == TaskStatus.BACKLOG.value
    updated = repository.transition_task(task.task_id, TaskStatus.ANALYZING, task.version, actor="tester", reason="start analysis")

    assert updated.status == TaskStatus.ANALYZING
    assert updated.version == 2
    assert repository.state_history[-1]["from_status"] == TaskStatus.BACKLOG.value
    assert repository.state_history[-1]["to_status"] == TaskStatus.ANALYZING.value
    assert repository.state_history[-1]["actor"] == "tester"


def test_in_memory_repository_rejects_version_conflicts() -> None:
    repository = InMemoryRepository()
    task = repository.create_task(make_task())
    repository.transition_task(task.task_id, TaskStatus.ANALYZING, task.version)

    try:
        repository.transition_task(task.task_id, TaskStatus.PLANNED, task.version)
    except RuntimeError as exc:
        assert "version conflict" in str(exc).lower()
    else:
        raise AssertionError("Expected version conflict")
