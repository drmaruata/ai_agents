from __future__ import annotations

from typing import Any

from .runtime import AgentRuntime


ROLE_PROMPTS = {
    "ruata": "Coordinate software engineering work. Prefer structured plans, bounded delegation, explicit dependencies, validation evidence, and human approval for consequential actions.",
    "kimi": "Research technical questions and produce evidence-backed architecture decisions and implementation specifications. Prefer primary documentation and record uncertainty.",
    "manasseh": "Implement frontend changes against approved contracts. Preserve design-system consistency, accessibility, responsive behavior, and frontend test coverage.",
    "john": "Implement backend and data changes against approved contracts. Preserve security, authorization, migrations, observability, and backend test coverage.",
    "ian": "Validate code and behavior. Run relevant checks, detect regressions and security issues, and report reproducible evidence. Never hide failures.",
}


def build_agent(runtime: AgentRuntime, agent_id: str, tools: list[Any] | None = None):
    """Build one OpenAI Agents SDK Agent when the SDK is installed.

    Tools are injected by the control-plane/tool gateway so the agent definitions
    remain decoupled from workstation and external-service implementations.
    """
    try:
        from agents import Agent
    except ImportError as exc:
        raise RuntimeError("openai-agents is not installed") from exc

    kwargs: dict[str, Any] = {
        "name": runtime.__class__.__name__ + ":" + agent_id,
        "instructions": runtime.instructions(agent_id) + "\n\nRuntime focus:\n" + ROLE_PROMPTS[agent_id],
    }
    if runtime.model:
        kwargs["model"] = runtime.model
    if tools:
        kwargs["tools"] = tools
    return Agent(**kwargs)
