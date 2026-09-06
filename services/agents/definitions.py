from __future__ import annotations

from typing import Any

from .registry import AGENT_CONFIGS
from .runtime import AgentRuntime


ROLE_FOCUS = {
    "ruata": "Coordinate software engineering work. Prefer structured plans, bounded delegation, explicit dependencies, validation evidence, and human approval for consequential actions.",
    "kimi": "Research technical questions and produce evidence-backed architecture decisions and implementation specifications. Prefer primary documentation and record uncertainty.",
    "manasseh": "Implement frontend changes against approved contracts. Preserve design-system consistency, accessibility, responsive behavior, and frontend test coverage.",
    "john": "Implement backend and data changes against approved contracts. Preserve security, authorization, migrations, observability, and backend test coverage.",
    "ian": "Validate code and behavior. Run relevant checks, detect regressions and security issues, and report reproducible evidence. Never hide failures.",
}


def build_agent(runtime: AgentRuntime, agent_id: str, tools: list[Any] | None = None):
    config = AGENT_CONFIGS[agent_id]
    instructions = runtime.instructions(agent_id) + "\n\nRuntime focus:\n" + ROLE_FOCUS[agent_id]
    return runtime.build_openai_agent_with_instructions(config.name, instructions, tools=tools)


def build_team(runtime: AgentRuntime, tools_by_agent: dict[str, list[Any]] | None = None):
    """Build the five-agent team with Ruata as the manager."""
    tools_by_agent = tools_by_agent or {}
    kimi = build_agent(runtime, "kimi", tools_by_agent.get("kimi"))
    manasseh = build_agent(runtime, "manasseh", tools_by_agent.get("manasseh"))
    john = build_agent(runtime, "john", tools_by_agent.get("john"))
    ian = build_agent(runtime, "ian", tools_by_agent.get("ian"))
    specialist_tools = [
        kimi.as_tool(tool_name="kimi_research", tool_description="Research and produce architecture decisions."),
        manasseh.as_tool(tool_name="manasseh_frontend", tool_description="Implement and validate frontend changes."),
        john.as_tool(tool_name="john_backend", tool_description="Implement and validate backend/data changes."),
        ian.as_tool(tool_name="ian_validate", tool_description="Run quality, security, and reliability validation."),
    ]
    ruata = build_agent(runtime, "ruata", specialist_tools + list(tools_by_agent.get("ruata", [])))
    return {"ruata": ruata, "kimi": kimi, "manasseh": manasseh, "john": john, "ian": ian}
