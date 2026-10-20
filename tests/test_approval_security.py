import pytest
from fastapi.testclient import TestClient

from packages.schemas.domain import Approval, ApprovalStatus, AuditEvent, RiskLevel, Task
from services.control_plane.auth import issue_dev_token
from services.control_plane import main as control_plane
from services.control_plane.main import validate_high_risk_approval
from services.persistence.repository import InMemoryRepository
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



def test_bridge_api_denies_approval_for_different_tool(monkeypatch) -> None:
    repository = InMemoryRepository()
    task = _task()
    repository.create_task(task)
    approval_service = ApprovalService(InMemoryApprovalRepository())
    approval = approval_service.request(
        task_id=task.task_id,
        action="terminal.run",
        risk_level=RiskLevel.HIGH,
    )
    approval_service.decide(approval.approval_id, approved=True, decided_by="reviewer")

    monkeypatch.setattr(control_plane, "repository", repository)
    monkeypatch.setattr(control_plane, "approvals", approval_service)
    monkeypatch.setattr(control_plane, "require_workspace_access", lambda *args: None)
    monkeypatch.setattr(control_plane.policy_engine, "authorize", lambda *args, **kwargs: None)

    async def should_not_execute(*args, **kwargs):
        raise AssertionError("bridge must not execute when approval does not match")

    monkeypatch.setattr(control_plane.bridge_manager, "send_tool_request", should_not_execute)
    client = TestClient(control_plane.app)
    response = client.post(
        "/api/bridge/execute",
        headers={"Authorization": f"Bearer {issue_dev_token()}"},
        json={
            "task_id": task.task_id,
            "approval_id": approval.approval_id,
            "device_id": "device-1",
            "agent": "ruata",
            "project_id": task.project_id,
            "workspace_id": "workspace-1",
            "tool": "file.write",
            "args": {"path": "src/example.py", "content": "safe"},
            "risk_level": "high",
        },
    )

    assert response.status_code == 403
    assert "does not authorize this tool" in response.json()["detail"]
    assert repository.events[-1].event_type.value == "tool.denied"


def test_bridge_api_requires_task_for_high_risk_execution(monkeypatch) -> None:
    repository = InMemoryRepository()
    approval_service = ApprovalService(InMemoryApprovalRepository())
    approval = approval_service.request(
        task_id="TASK-1",
        action="file.write",
        risk_level=RiskLevel.HIGH,
    )
    approval_service.decide(approval.approval_id, approved=True, decided_by="reviewer")

    monkeypatch.setattr(control_plane, "repository", repository)
    monkeypatch.setattr(control_plane, "approvals", approval_service)
    monkeypatch.setattr(control_plane, "require_workspace_access", lambda *args: None)

    client = TestClient(control_plane.app)
    response = client.post(
        "/api/bridge/execute",
        headers={"Authorization": f"Bearer {issue_dev_token()}"},
        json={
            "approval_id": approval.approval_id,
            "device_id": "device-1",
            "agent": "ruata",
            "project_id": "PROJECT-1",
            "workspace_id": "workspace-1",
            "tool": "file.write",
            "args": {"path": "src/example.py", "content": "safe"},
            "risk_level": "high",
        },
    )

    assert response.status_code == 403
    assert "task_id is required" in response.json()["detail"]
    assert repository.events[-1].event_type.value == "tool.denied"



def test_bridge_api_executes_matching_approved_tool_and_audits(monkeypatch) -> None:
    repository = InMemoryRepository()
    task = _task()
    repository.create_task(task)
    approval_service = ApprovalService(InMemoryApprovalRepository())
    approval = approval_service.request(
        task_id=task.task_id,
        action="file.write",
        risk_level=RiskLevel.HIGH,
    )
    approval_service.decide(approval.approval_id, approved=True, decided_by="reviewer")

    monkeypatch.setattr(control_plane, "repository", repository)
    monkeypatch.setattr(control_plane, "approvals", approval_service)
    monkeypatch.setattr(control_plane, "require_workspace_access", lambda *args: None)
    monkeypatch.setattr(control_plane.policy_engine, "authorize", lambda *args, **kwargs: None)

    async def fake_execute(device_id, tool, args):
        return {"ok": True, "tool": tool, "device_id": device_id}

    monkeypatch.setattr(control_plane.bridge_manager, "send_tool_request", fake_execute)
    client = TestClient(control_plane.app)
    response = client.post(
        "/api/bridge/execute",
        headers={"Authorization": f"Bearer {issue_dev_token()}"},
        json={
            "task_id": task.task_id,
            "approval_id": approval.approval_id,
            "device_id": "device-1",
            "agent": "ruata",
            "project_id": task.project_id,
            "workspace_id": "workspace-1",
            "tool": "file.write",
            "args": {"path": "src/example.py", "content": "safe"},
            "risk_level": "high",
        },
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert repository.events[-1].event_type.value == "tool.executed"
    assert repository.events[-1].task_id == task.task_id
