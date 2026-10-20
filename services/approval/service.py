from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from packages.schemas.domain import Approval, ApprovalStatus, RiskLevel
from services.approval.repository import ApprovalRepository, InMemoryApprovalRepository


class ApprovalService:
    """Human approval gate with repository-backed state."""

    def __init__(self, repository: ApprovalRepository | None = None) -> None:
        self.repository = repository or InMemoryApprovalRepository()

    def request(self, *, task_id: str, action: str, risk_level: RiskLevel, requested_by: str | None = None) -> Approval:
        if risk_level in {RiskLevel.LOW, RiskLevel.MEDIUM}:
            raise ValueError("Low and medium risk operations do not require an approval record")
        approval = Approval(
            approval_id=f"APR-{uuid4().hex[:10].upper()}",
            task_id=task_id,
            action=action,
            risk_level=risk_level,
            requested_by=requested_by,
        )
        return self.repository.create(approval)

    def get(self, approval_id: str) -> Approval | None:
        return self.repository.get(approval_id)

    def list(self, status: ApprovalStatus | None = None) -> list[Approval]:
        return self.repository.list(status)

    def decide(self, approval_id: str, *, approved: bool, decided_by: str, reason: str | None = None) -> Approval:
        existing = self.repository.get(approval_id)
        if existing is None:
            raise KeyError(approval_id)
        if existing.status != ApprovalStatus.PENDING:
            raise ValueError("Approval is no longer pending")
        item = self.repository.decide(approval_id, approved=approved, decided_by=decided_by, reason=reason)
        if item is None:
            raise ValueError("Approval is no longer pending")
        return item

    def expire(self, ttl: timedelta = timedelta(hours=1)) -> list[Approval]:
        now = datetime.now(timezone.utc)
        return self.repository.expire(now, now - ttl)
