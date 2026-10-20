import os
from pathlib import Path

import pytest
import psycopg

from packages.schemas.domain import Task, TaskStatus
from services.persistence.repository import PostgresRepository


@pytest.mark.integration
def test_postgres_repository_persists_task_and_state_history() -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")

    with psycopg.connect(dsn) as connection:
        for migration in sorted(Path("infra/db").glob("*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"))

        connection.execute(
            """
            INSERT INTO projects (project_id, name)
            VALUES ('test-project', 'Integration Test Project')
            ON CONFLICT (project_id) DO NOTHING
            """
        )
        connection.execute(
            """
            INSERT INTO agents (agent_id, name, role)
            VALUES ('ruata', 'Ruata', 'ruata')
            ON CONFLICT (agent_id) DO NOTHING
            """
        )

    repository = PostgresRepository(dsn)
    task = repository.create_task(
        Task(
            task_id="TASK-PG-1",
            project_id="test-project",
            title="Postgres persistence",
            description="Verify task and history persistence",
        )
    )
    updated = repository.transition_task(
        task.task_id,
        TaskStatus.ANALYZING,
        task.version,
        actor="integration-test",
        reason="phase 2 acceptance",
    )

    assert updated.status == TaskStatus.ANALYZING
    assert updated.version == 2

    with psycopg.connect(dsn) as connection:
        rows = connection.execute(
            """
            SELECT from_status, to_status, version, actor, reason
            FROM task_state_history
            WHERE task_id = %s
            ORDER BY version
            """,
            (task.task_id,),
        ).fetchall()

    assert rows == [
        (None, "backlog", 1, None, "created"),
        ("backlog", "analyzing", 2, "integration-test", "phase 2 acceptance"),
    ]

    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM tasks WHERE task_id = %s", (task.task_id,))
        connection.commit()



@pytest.mark.integration
def test_postgres_approval_persists_and_allows_only_one_decision() -> None:
    from packages.schemas.domain import Approval, ApprovalStatus, RiskLevel
    from services.approval.repository import PostgresApprovalRepository

    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")

    with psycopg.connect(dsn) as connection:
        for migration in sorted(Path("infra/db").glob("*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"))
        connection.execute(
            """
            INSERT INTO projects (project_id, name)
            VALUES ('approval-integration-project', 'Approval Integration')
            ON CONFLICT (project_id) DO NOTHING
            """
        )
        connection.execute(
            """
            INSERT INTO tasks (task_id, project_id, title, description)
            VALUES ('TASK-APPROVAL-INTEGRATION', 'approval-integration-project', 'Approval integration', 'Verify durable approval state')
            ON CONFLICT (task_id) DO NOTHING
            """
        )

    first_repository = PostgresApprovalRepository(dsn)
    approval = Approval(
        approval_id="APR-INTEGRATION-TEST",
        task_id="TASK-APPROVAL-INTEGRATION",
        action="file.write",
        risk_level=RiskLevel.HIGH,
    )
    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM approvals WHERE approval_id=%s", (approval.approval_id,))
    first_repository.create(approval)

    restarted_repository = PostgresApprovalRepository(dsn)
    loaded = restarted_repository.get(approval.approval_id)
    assert loaded is not None
    assert loaded.status == ApprovalStatus.PENDING
    assert loaded.action == "file.write"

    decided = restarted_repository.decide(
        approval.approval_id,
        approved=True,
        decided_by="integration-reviewer",
        reason="verified",
    )
    repeated = restarted_repository.decide(
        approval.approval_id,
        approved=False,
        decided_by="second-reviewer",
        reason="must not overwrite",
    )

    assert decided is not None
    assert decided.status == ApprovalStatus.APPROVED
    assert repeated is None
    assert restarted_repository.get(approval.approval_id).status == ApprovalStatus.APPROVED

    with psycopg.connect(dsn) as connection:
        connection.execute("DELETE FROM approvals WHERE approval_id=%s", (approval.approval_id,))
        connection.execute("DELETE FROM tasks WHERE task_id=%s", (approval.task_id,))
        connection.execute("DELETE FROM projects WHERE project_id=%s", ("approval-integration-project",))


@pytest.mark.integration
def test_postgres_idempotent_task_creation_returns_one_durable_task() -> None:
    dsn = os.getenv("DATABASE_URL")
    if not dsn:
        pytest.skip("DATABASE_URL is not configured")

    with psycopg.connect(dsn) as connection:
        for migration in sorted(Path("infra/db").glob("*.sql")):
            connection.execute(migration.read_text(encoding="utf-8"))
        connection.execute(
            """
            INSERT INTO projects (project_id, name)
            VALUES ('idempotency-integration-project', 'Idempotency Integration')
            ON CONFLICT (project_id) DO NOTHING
            """
        )
        connection.execute(
            """
            INSERT INTO agents (agent_id, name, role)
            VALUES ('ruata', 'Ruata', 'ruata')
            ON CONFLICT (agent_id) DO NOTHING
            """
        )

    repository = PostgresRepository(dsn)
    candidate = Task(
        task_id="TASK-IDEMPOTENCY-ONCE",
        project_id="idempotency-integration-project",
        title="Idempotency acceptance",
        description="A retry must return the original task",
    )
    try:
        first = repository.create_task_idempotent(candidate, "integration-key-once", "task.create:test-user")
        second = repository.create_task_idempotent(
            candidate.model_copy(update={"task_id": "TASK-IDEMPOTENCY-RETRY"}),
            "integration-key-once",
            "task.create:test-user",
        )
        assert first.task_id == second.task_id == "TASK-IDEMPOTENCY-ONCE"
        with psycopg.connect(dsn) as connection:
            count = connection.execute(
                "SELECT count(*) FROM tasks WHERE project_id=%s",
                ("idempotency-integration-project",),
            ).fetchone()[0]
            assert count == 1
    finally:
        with psycopg.connect(dsn) as connection:
            connection.execute("DELETE FROM idempotency_keys WHERE key=%s AND scope=%s", ("integration-key-once", "task.create:test-user"))
            connection.execute("DELETE FROM tasks WHERE project_id=%s", ("idempotency-integration-project",))
            connection.execute("DELETE FROM projects WHERE project_id=%s", ("idempotency-integration-project",))

