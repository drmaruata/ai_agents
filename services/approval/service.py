from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from packages.schemas.domain import Approval, ApprovalStatus, RiskLevel


class ApprovalService:
    """Explicit human approval gate for consequential actions."""

    def __init__(self) -> None:
        self.approvals: dict[str, Approval] = {}

    def request(self, *, task_id: str, action: str, risk_level: RiskLevel, requested_by: str | None = None) -> Approval:
        if risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM}:
            raise ValueError("Low and medium risk operations do not require an approval record")
        approval = Approval(
            approval_id=f"APR-{uuid4().hex[:10].upper()}",
            task_id=task_id,
            action=action,
            risk_level=risk_level,
            # The domain model currently represents agent requesters separately from authenticated users.
            # The authenticated user is retained in the audit event by the control plane.
            requested_by=None,
        )
        self.approvals[approval.approval_id] = approval
        return approval

    def decide(self, approval_id: str, *, approved: bool, decided_by: str, reason: str | None = None) -> Approval:
        approval = self.approvals.get(approval_id)
        if approval is None:
            raise KeyError(approval_id)
        if approval.status != ApprovalStatus.PENDING:
            raise ValueError("Approval is no longer pending")
        approval.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        approval.decided_by = decided_by
        approval.reason = reason
        approval.decided_at = datetime.now(timezone.utc)
        return approval

    def expire(self, ttl: timedelta = timedelta(hours=1)) -> list[Approval]:
        now = datetime.now(timezone.utc)
        expired: list[Approval] = []
        for approval in self.approvals.values():
            if approval.status == ApprovalStatus.PENDING and now - approval.created_at > ttl:
                approval.status = ApprovalStatus.EXPIRED
                expired.append(approval)
        return expired
