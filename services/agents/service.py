from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from packages.schemas.domain import AgentRole, RunStatus, TaskRun
from services.persistence.repository import Repository

from .runtime import AgentRuntime


class AgentExecutionService:
    def __init__(self, repository: Repository, runtime: AgentRuntime) -> None:
        self.repository = repository
        self.runtime = runtime

    async def run(self, *, task_id: str, agent: AgentRole, prompt: str) -> tuple[TaskRun, str]:
        run = TaskRun(run_id=f"RUN-{uuid4().hex[:10].upper()}", task_id=task_id, agent=agent, status=RunStatus.RUNNING, started_at=datetime.now(timezone.utc))
        self.repository.record_run(run)
        try:
            output = await self.runtime.run(agent.value, prompt)
        except Exception as exc:
            run.status = RunStatus.FAILED
            run.error = str(exc)
            run.finished_at = datetime.now(timezone.utc)
            self.repository.record_run(run)
            raise
        run.status = RunStatus.SUCCEEDED
        run.finished_at = datetime.now(timezone.utc)
        self.repository.record_run(run)
        return run, output
