import pytest

from packages.schemas.domain import Approval, ApprovalStatus, RiskLevel, Task
from services.control_plane.main import validate_high_risk_approval
from services.approval.repository import InMemoryApprovalRepository
from services.approval.service import ApprovalService


def _task() -> Task:
    return Task(task_id="TASK-1", project_id="PROJECT-1", title="test", description="test")


def _approval(**overrides) -> Approval:
    values = {
        "approval_id": "APR-1",
        "task_id": "TASK-1",
        "action": "file.write",
        "risk_level": RiskLevel.HIGH,
        "status": ApprovalStatus.APPROVED,
    }
    values.update(overrides)
    return Approval(**values)


def test_high_risk_approval_allows_exact_matching_execution() -> None:
    validate_high_risk_approval(
        approval=_approval(),
        task_id="TASK-1",
        project_id="PROJECT-1",
        tool="file.write",
        risk_level=RiskLevel.HIGH,
        task=_task(),
    )


@pytest.mark.parametrize(
    ("approval", "task_id", "project_id", "tool", "risk_level", "task", "message"),
    [
        (_approval(), None, "PROJECT-1", "file.write", RiskLevel.HIGH, _task(), "task_id"),
        (None, "TASK-1", "PROJECT-1", "file.write", RiskLevel.HIGH, _task(), "not approved"),
        (_approval(task_id="TASK-OTHER"), "TASK-1", "PROJECT-1", "file.write", RiskLevel.HIGH, _task(), "does not match task"),
        (_approval(action="terminal.run"), "TASK-1", "PROJECT-1", "file.write", RiskLevel.HIGH, _task(), "does not authorize this tool"),
        (_approval(risk_level=RiskLevel.HIGH), "TASK-1", "PROJECT-1", "file.write", RiskLevel.CRITICAL, _task(), "insufficient"),
        (_approval(), "TASK-1", "PROJECT-OTHER", "file.write", RiskLevel.HIGH, _task(), "does not belong to project"),
        (_approval(), "TASK-1", "PROJECT-1", "file.write", RiskLevel.HIGH, None, "task_id"),
        (_approval(status=ApprovalStatus.EXPIRED), "TASK-1", "PROJECT-1", "file.write", RiskLevel.HIGH, _task(), "not approved"),
    ],
)
def test_high_risk_approval_fails_closed(
    approval, task_id, project_id, tool, risk_level, task, message
) -> None:
    with pytest.raises(ValueError, match=message):
        validate_high_risk_approval(
            approval=approval,
            task_id=task_id,
            project_id=project_id,
            tool=tool,
            risk_level=risk_level,
            task=task,
        )


def test_approval_expiry_only_expires_old_pending_records() -> None:
    from datetime import datetime, timedelta, timezone

    repository = InMemoryApprovalRepository()
    service = ApprovalService(repository)
    pending = service.request(task_id="TASK-OLD", action="file.write", risk_level=RiskLevel.HIGH)
    recent = service.request(task_id="TASK-NEW", action="file.write", risk_level=RiskLevel.HIGH)
    old_time = datetime.now(timezone.utc) - timedelta(hours=3)
    repository._items[pending.approval_id].created_at = old_time

    expired = service.expire(ttl=timedelta(hours=1))

    assert [item.approval_id for item in expired] == [pending.approval_id]
    assert service.get(pending.approval_id).status == ApprovalStatus.EXPIRED
    assert service.get(recent.approval_id).status == ApprovalStatus.PENDING
