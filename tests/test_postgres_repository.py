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
