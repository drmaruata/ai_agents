from __future__ import annotations

from pathlib import Path
from typing import Any

from .registry import AGENT_CONFIGS


class AgentRuntimeError(RuntimeError):
    pass


class AgentRuntime:
    """Provider-neutral runtime with an OpenAI Agents SDK adapter."""

    def __init__(self, model: str | None = None) -> None:
        self.model = model

    def instructions(self, agent_id: str) -> str:
        config = AGENT_CONFIGS[agent_id]
        return Path(config.instructions_file).read_text(encoding="utf-8")

    def build_openai_agent(self, agent_id: str, tools: list[Any] | None = None):
        config = AGENT_CONFIGS[agent_id]
        return self.build_openai_agent_with_instructions(config.name, self.instructions(agent_id), tools=tools)

    def build_openai_agent_with_instructions(self, name: str, instructions: str, *, tools: list[Any] | None = None):
        try:
            from agents import Agent
        except ImportError as exc:
            raise AgentRuntimeError("Install openai-agents to build model-backed agents") from exc
        kwargs: dict[str, Any] = {"name": name, "instructions": instructions}
        if self.model:
            kwargs["model"] = self.model
        if tools:
            kwargs["tools"] = tools
        return Agent(**kwargs)

    async def run(self, agent_id: str, prompt: str) -> str:
        try:
            from agents import Runner
        except ImportError as exc:
            raise AgentRuntimeError("Install openai-agents to run model-backed agents") from exc
        agent = self.build_openai_agent(agent_id)
        result = await Runner.run(agent, prompt)
        return str(result.final_output)
