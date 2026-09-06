import pytest

from packages.schemas.domain import ApprovalStatus, RiskLevel
from services.approval.service import ApprovalService


def test_high_risk_action_requires_human_approval():
    service = ApprovalService()
    approval = service.request(task_id="TASK-1", action="production migration", risk_level=RiskLevel.HIGH, requested_by="john")
    assert approval.status == ApprovalStatus.PENDING
    decided = service.decide(approval.approval_id, approved=True, decided_by="owner")
    assert decided.status == ApprovalStatus.APPROVED


def test_low_risk_does_not_create_approval():
    with pytest.raises(ValueError):
        ApprovalService().request(task_id="TASK-1", action="read file", risk_level=RiskLevel.LOW)
