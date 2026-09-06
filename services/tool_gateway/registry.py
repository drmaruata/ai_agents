from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from packages.schemas.domain import AgentRole, RiskLevel, ToolDefinition
from services.policy.engine import PolicyContext, PolicyEngine, PolicyDenied


@dataclass(frozen=True, slots=True)
class ToolHandler:
    definition: ToolDefinition
    handler: Callable[[dict[str, Any]], Any]


class ToolRegistry:
    def __init__(self, policy: PolicyEngine) -> None:
        self._policy = policy
        self._tools: dict[str, ToolHandler] = {}

    def register(self, definition: ToolDefinition, handler: Callable[[dict[str, Any]], Any]) -> None:
        if definition.name in self._tools:
            raise ValueError(f"Tool already registered: {definition.name}")
        self._tools[definition.name] = ToolHandler(definition, handler)

    def list(self) -> list[ToolDefinition]:
        return [item.definition for item in self._tools.values()]

    def execute(
        self,
        *,
        agent: AgentRole,
        project_id: str,
        workspace_id: str,
        name: str,
        args: dict[str, Any],
    ) -> Any:
        tool = self._tools.get(name)
        if tool is None:
            raise KeyError(name)
        self._policy.authorize(
            PolicyContext(
                agent=agent,
                project_id=project_id,
                workspace_id=workspace_id,
                tool_name=name,
                risk_level=tool.definition.risk_level,
            )
        )
        return tool.handler(args)


def build_default_registry(policy: PolicyEngine, handlers: dict[str, Callable[[dict[str, Any]], Any]] | None = None) -> ToolRegistry:
    registry = ToolRegistry(policy)
    handlers = handlers or {}
    definitions = [
        ToolDefinition(name="workspace.info", description="Return selected workspace metadata", risk_level=RiskLevel.LOW),
        ToolDefinition(name="file.read", description="Read a text file inside an authorized workspace", risk_level=RiskLevel.LOW),
        ToolDefinition(name="file.write", description="Write a text file inside an authorized workspace", risk_level=RiskLevel.MEDIUM),
        ToolDefinition(name="file.patch", description="Apply a bounded patch to an authorized workspace", risk_level=RiskLevel.MEDIUM),
        ToolDefinition(name="git.status", description="Return Git status", risk_level=RiskLevel.LOW),
        ToolDefinition(name="git.diff", description="Return Git diff", risk_level=RiskLevel.LOW),
        ToolDefinition(name="terminal.run", description="Run an allowlisted development command", risk_level=RiskLevel.MEDIUM),
        ToolDefinition(name="test.run", description="Run an allowlisted test command", risk_level=RiskLevel.MEDIUM),
        ToolDefinition(name="database.query", description="Execute an explicitly authorized database query", risk_level=RiskLevel.HIGH),
        ToolDefinition(name="security.scan", description="Run security validation checks", risk_level=RiskLevel.MEDIUM),
        ToolDefinition(name="browser.run", description="Run approved browser automation", risk_level=RiskLevel.MEDIUM),
    ]
    for definition in definitions:
        registry.register(definition, handlers.get(definition.name, _not_implemented))
    return registry


def _not_implemented(_: dict[str, Any]) -> Any:
    raise NotImplementedError("Tool handler is not configured")
