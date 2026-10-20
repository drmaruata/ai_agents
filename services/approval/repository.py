from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

import psycopg
from psycopg.rows import dict_row

from packages.schemas.domain import Approval, ApprovalStatus, RiskLevel


class ApprovalRepository(ABC):
    @abstractmethod
    def create(self, approval: Approval) -> Approval: ...

    @abstractmethod
    def get(self, approval_id: str) -> Approval | None: ...

    @abstractmethod
    def list(self, status: ApprovalStatus | None = None) -> list[Approval]: ...

    @abstractmethod
    def decide(self, approval_id: str, *, approved: bool, decided_by: str, reason: str | None) -> Approval | None: ...

    @abstractmethod
    def expire(self, now: datetime, cutoff: datetime) -> list[Approval]: ...


class InMemoryApprovalRepository(ApprovalRepository):
    def __init__(self) -> None:
        self._items: dict[str, Approval] = {}

    def create(self, approval: Approval) -> Approval:
        if approval.approval_id in self._items:
            raise ValueError(f"Approval already exists: {approval.approval_id}")
        self._items[approval.approval_id] = approval.model_copy(deep=True)
        return approval.model_copy(deep=True)

    def get(self, approval_id: str) -> Approval | None:
        item = self._items.get(approval_id)
        return item.model_copy(deep=True) if item else None

    def list(self, status: ApprovalStatus | None = None) -> list[Approval]:
        items = list(self._items.values())
        if status is not None:
            items = [item for item in items if item.status == status]
        return [item.model_copy(deep=True) for item in items]

    def decide(self, approval_id: str, *, approved: bool, decided_by: str, reason: str | None) -> Approval | None:
        item = self._items.get(approval_id)
        if item is None or item.status != ApprovalStatus.PENDING:
            return None
        item.status = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        item.decided_by = decided_by
        item.reason = reason
        from packages.schemas.domain import utc_now
        item.decided_at = utc_now()
        return item.model_copy(deep=True)

    def expire(self, now: datetime, cutoff: datetime) -> list[Approval]:
        expired = []
        for item in self._items.values():
            if item.status == ApprovalStatus.PENDING and item.created_at < cutoff:
                item.status = ApprovalStatus.EXPIRED
                item.decided_at = now
                expired.append(item.model_copy(deep=True))
        return expired


class PostgresApprovalRepository(ApprovalRepository):
    """PostgreSQL persistence for approvals with atomic conditional state transitions."""

    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("DATABASE_URL is required for PostgresApprovalRepository")
        self.dsn = dsn

    def _connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def create(self, approval: Approval) -> Approval:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO public.approvals
                    (approval_id, task_id, action, risk_level, status, requested_by,
                     decided_by, reason, created_at, decided_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING *
                """,
                (approval.approval_id, approval.task_id, approval.action,
                 approval.risk_level.value, approval.status.value, _uuid_or_none(approval.requested_by),
                 _uuid_or_none(approval.decided_by), approval.reason, approval.created_at, approval.decided_at),
            )
            return _from_row(cur.fetchone())

    def get(self, approval_id: str) -> Approval | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM public.approvals WHERE approval_id=%s", (approval_id,))
            row = cur.fetchone()
        return _from_row(row) if row else None

    def list(self, status: ApprovalStatus | None = None) -> list[Approval]:
        with self._connect() as conn, conn.cursor() as cur:
            if status is None:
                cur.execute("SELECT * FROM public.approvals ORDER BY created_at DESC")
            else:
                cur.execute("SELECT * FROM public.approvals WHERE status=%s ORDER BY created_at DESC", (status.value,))
            rows = cur.fetchall()
        return [_from_row(row) for row in rows]

    def decide(self, approval_id: str, *, approved: bool, decided_by: str, reason: str | None) -> Approval | None:
        from packages.schemas.domain import utc_now
        target = ApprovalStatus.APPROVED if approved else ApprovalStatus.REJECTED
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.approvals
                SET status=%s, decided_by=%s, reason=%s, decided_at=%s
                WHERE approval_id=%s AND status=%s
                RETURNING *
                """,
                (target.value, _uuid_or_none(decided_by), reason, utc_now(), approval_id, ApprovalStatus.PENDING.value),
            )
            row = cur.fetchone()
        return _from_row(row) if row else None

    def expire(self, now: datetime, cutoff: datetime) -> list[Approval]:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE public.approvals
                SET status=%s, decided_at=%s, reason=COALESCE(reason, %s)
                WHERE status=%s AND created_at < %s
                RETURNING *
                """,
                (ApprovalStatus.EXPIRED.value, now, "Approval expired", ApprovalStatus.PENDING.value, cutoff),
            )
            rows = cur.fetchall()
        return [_from_row(row) for row in rows]


def _uuid_or_none(value: str | None) -> str | None:
    if not value:
        return None
    # Supabase's approvals table stores user IDs as UUIDs. Ignore non-UUID
    # development subjects rather than causing an invalid database write.
    from uuid import UUID
    try:
        return str(UUID(value))
    except (ValueError, TypeError, AttributeError):
        return None


def _from_row(row: dict[str, Any]) -> Approval:
    return Approval(
        approval_id=row["approval_id"],
        task_id=row["task_id"],
        action=row["action"],
        risk_level=RiskLevel(row["risk_level"]),
        status=ApprovalStatus(row["status"]),
        requested_by=str(row["requested_by"]) if row.get("requested_by") else None,
        decided_by=str(row["decided_by"]) if row.get("decided_by") else None,
        reason=row.get("reason"),
        created_at=row["created_at"],
        decided_at=row.get("decided_at"),
    )
