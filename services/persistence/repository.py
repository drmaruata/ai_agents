from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from packages.schemas.domain import AuditEvent, Task, TaskRun, TaskStatus, validate_task_transition


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Repository(ABC):
    @abstractmethod
    def create_task(self, task: Task) -> Task: ...

    @abstractmethod
    def get_task(self, task_id: str) -> Task | None: ...

    @abstractmethod
    def list_tasks(self, project_id: str | None = None) -> list[Task]: ...

    @abstractmethod
    def transition_task(self, task_id: str, status: TaskStatus, expected_version: int) -> Task: ...

    @abstractmethod
    def record_run(self, run: TaskRun) -> TaskRun: ...

    @abstractmethod
    def audit(self, event: AuditEvent) -> None: ...


class InMemoryRepository(Repository):
    def __init__(self) -> None:
        self.tasks: dict[str, Task] = {}
        self.runs: dict[str, TaskRun] = {}
        self.events: list[AuditEvent] = []

    def create_task(self, task: Task) -> Task:
        if task.task_id in self.tasks:
            raise ValueError(f"Task already exists: {task.task_id}")
        self.tasks[task.task_id] = task.model_copy(deep=True)
        return self.tasks[task.task_id].model_copy(deep=True)

    def get_task(self, task_id: str) -> Task | None:
        task = self.tasks.get(task_id)
        return task.model_copy(deep=True) if task else None

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        values = list(self.tasks.values())
        if project_id is not None:
            values = [task for task in values if task.project_id == project_id]
        return [task.model_copy(deep=True) for task in values]

    def transition_task(self, task_id: str, status: TaskStatus, expected_version: int) -> Task:
        task = self.tasks.get(task_id)
        if task is None:
            raise KeyError(task_id)
        if task.version != expected_version:
            raise RuntimeError("Task version conflict")
        validate_task_transition(task.status, status)
        task.status = status
        task.version += 1
        task.updated_at = utc_now()
        return task.model_copy(deep=True)

    def record_run(self, run: TaskRun) -> TaskRun:
        self.runs[run.run_id] = run.model_copy(deep=True)
        return run.model_copy(deep=True)

    def audit(self, event: AuditEvent) -> None:
        self.events.append(event.model_copy(deep=True))


class PostgresRepository(Repository):
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise ValueError("DATABASE_URL is required for PostgresRepository")
        self.dsn = dsn

    def _connect(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def create_task(self, task: Task) -> Task:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (task_id, project_id, title, description, risk_level, assigned_agent,
                    status, dependencies, allowed_paths, acceptance_criteria, metadata, version, created_at, updated_at)
                VALUES (%(task_id)s,%(project_id)s,%(title)s,%(description)s,%(risk_level)s,%(assigned_agent)s,
                    %(status)s,%(dependencies)s,%(allowed_paths)s,%(acceptance_criteria)s,%(metadata)s,%(version)s,%(created_at)s,%(updated_at)s)
                RETURNING *
                """,
                _task_params(task),
            )
            return _row_to_task(cur.fetchone())

    def get_task(self, task_id: str) -> Task | None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE task_id = %s", (task_id,))
            row = cur.fetchone()
        return _row_to_task(row) if row else None

    def list_tasks(self, project_id: str | None = None) -> list[Task]:
        with self._connect() as conn, conn.cursor() as cur:
            if project_id:
                cur.execute("SELECT * FROM tasks WHERE project_id = %s ORDER BY created_at", (project_id,))
            else:
                cur.execute("SELECT * FROM tasks ORDER BY created_at")
            rows = cur.fetchall()
        return [_row_to_task(row) for row in rows]

    def transition_task(self, task_id: str, status: TaskStatus, expected_version: int) -> Task:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM tasks WHERE task_id = %s FOR UPDATE", (task_id,))
            row = cur.fetchone()
            if row is None:
                raise KeyError(task_id)
            current = _row_to_task(row)
            if current.version != expected_version:
                raise RuntimeError("Task version conflict")
            validate_task_transition(current.status, status)
            cur.execute(
                """
                UPDATE tasks SET status=%s, version=version+1, updated_at=%s
                WHERE task_id=%s AND version=%s RETURNING *
                """,
                (status.value, utc_now(), task_id, expected_version),
            )
            return _row_to_task(cur.fetchone())

    def record_run(self, run: TaskRun) -> TaskRun:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO task_runs (run_id, task_id, agent, status, attempt, started_at, finished_at, error, output_artifact_ids)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (run_id) DO UPDATE SET status=EXCLUDED.status, attempt=EXCLUDED.attempt,
                    started_at=EXCLUDED.started_at, finished_at=EXCLUDED.finished_at, error=EXCLUDED.error,
                    output_artifact_ids=EXCLUDED.output_artifact_ids RETURNING *
                """,
                (run.run_id, run.task_id, run.agent.value, run.status.value, run.attempt, run.started_at, run.finished_at, run.error, run.output_artifact_ids),
            )
            return _row_to_run(cur.fetchone())

    def audit(self, event: AuditEvent) -> None:
        with self._connect() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO audit_events (event_id,event_type,actor,task_id,device_id,metadata,created_at) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                (event.event_id, event.event_type.value, event.actor, event.task_id, event.device_id, Jsonb(event.metadata), event.created_at),
            )


def _task_params(task: Task) -> dict[str, Any]:
    return {
        "task_id": task.task_id,
        "project_id": task.project_id,
        "title": task.title,
        "description": task.description,
        "risk_level": task.risk_level.value,
        "assigned_agent": task.assigned_agent.value if task.assigned_agent else None,
        "status": task.status.value,
        "dependencies": task.dependencies,
        "allowed_paths": task.allowed_paths,
        "acceptance_criteria": task.acceptance_criteria,
        "metadata": Jsonb(task.metadata),
        "version": task.version,
        "created_at": task.created_at,
        "updated_at": task.updated_at,
    }


def _row_to_task(row: dict[str, Any]) -> Task:
    return Task(
        task_id=row["task_id"], project_id=row["project_id"], title=row["title"], description=row["description"],
        risk_level=row["risk_level"], assigned_agent=row["assigned_agent"], status=row["status"],
        dependencies=row["dependencies"] or [], allowed_paths=row["allowed_paths"] or [],
        acceptance_criteria=row["acceptance_criteria"] or [], metadata=row["metadata"] or {},
        version=row["version"], created_at=row["created_at"], updated_at=row["updated_at"],
    )


def _row_to_run(row: dict[str, Any]) -> TaskRun:
    return TaskRun(
        run_id=row["run_id"], task_id=row["task_id"], agent=row["agent"], status=row["status"], attempt=row["attempt"],
        started_at=row["started_at"], finished_at=row["finished_at"], error=row["error"], output_artifact_ids=row["output_artifact_ids"] or [],
    )
