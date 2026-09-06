from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from packages.schemas.domain import AgentRole
from services.agents.runtime import AgentRuntime
from services.agents.service import AgentExecutionService
from services.agents.workstation_tools import build_workstation_tools
from services.bridge.manager import BridgeConnectionManager
from services.persistence.repository import Repository
from services.policy.engine import PolicyEngine


class LocalAgentRun(BaseModel):
    task_id: str = Field(min_length=1)
    agent: AgentRole
    prompt: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    workspace_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)


def build_router(repository: Repository, manager: BridgeConnectionManager, policy: PolicyEngine, runtime: AgentRuntime) -> APIRouter:
    router = APIRouter(tags=["agent-execution"])
    execution = AgentExecutionService(repository, runtime)

    @router.post("/agents/run/local")
    async def run_local(payload: LocalAgentRun) -> dict[str, Any]:
        if repository.get_task(payload.task_id) is None:
            raise HTTPException(status_code=404, detail="Task not found")
        if payload.device_id not in manager.connections:
            raise HTTPException(status_code=409, detail="Device bridge is not connected")
        tools = build_workstation_tools(
            manager=manager,
            policy=policy,
            agent=payload.agent,
            project_id=payload.project_id,
            workspace_id=payload.workspace_id,
            device_id=payload.device_id,
        )
        try:
            run, output = await execution.run(task_id=payload.task_id, agent=payload.agent, prompt=payload.prompt, tools=tools)
        except Exception as exc:
            raise HTTPException(status_code=502, detail=f"Local agent execution failed: {exc}") from exc
        return {"run": run.model_dump(mode="json"), "output": output}

    return router
