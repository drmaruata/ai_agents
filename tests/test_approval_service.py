import pytest

from packages.schemas.domain import ApprovalStatus, RiskLevel
from services.approval.repository import InMemoryApprovalRepository
from services.approval.service import ApprovalService


def test_approval_lifecycle_uses_repository() -> None:
    repository = InMemoryApprovalRepository()
    service = ApprovalService(repository)
    approval = service.request(task_id="TASK-1", action="file.write", risk_level=RiskLevel.HIGH)
    assert service.get(approval.approval_id).status == ApprovalStatus.PENDING
    result = service.decide(approval.approval_id, approved=True, decided_by="reviewer")
    assert result.status == ApprovalStatus.APPROVED
    assert service.list(ApprovalStatus.PENDING) == []


def test_decision_cannot_be_repeated() -> None:
    service = ApprovalService()
    approval = service.request(task_id="TASK-2", action="deploy", risk_level=RiskLevel.CRITICAL)
    service.decide(approval.approval_id, approved=False, decided_by="reviewer")
    with pytest.raises(ValueError, match="no longer pending"):
        service.decide(approval.approval_id, approved=True, decided_by="reviewer-2")


def test_low_risk_request_is_rejected() -> None:
    service = ApprovalService()
    with pytest.raises(ValueError, match="do not require"):
        service.request(task_id="TASK-3", action="read", risk_level=RiskLevel.LOW)
