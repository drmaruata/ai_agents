from __future__ import annotations

from dataclasses import dataclass
import shlex
from fnmatch import fnmatch
from typing import Final

from packages.schemas.domain import AgentRole, RiskLevel


class PolicyDenied(PermissionError):
    pass


@dataclass(frozen=True, slots=True)
class PolicyContext:
    agent: AgentRole
    project_id: str
    workspace_id: str
    tool_name: str
    risk_level: RiskLevel
    relative_path: str | None = None
    command: str | None = None
    network_target: str | None = None


@dataclass(frozen=True, slots=True)
class ToolPolicy:
    agent: AgentRole
    tool_names: frozenset[str]
    read_paths: tuple[str, ...] = ()
    write_paths: tuple[str, ...] = ()
    commands: frozenset[str] = frozenset()
    network_targets: frozenset[str] = frozenset()
    max_risk: RiskLevel = RiskLevel.LOW


_RISK_ORDER: Final = {
    RiskLevel.LOW: 0,
    RiskLevel.MEDIUM: 1,
    RiskLevel.HIGH: 2,
    RiskLevel.CRITICAL: 3,
}


class PolicyEngine:
    def __init__(self, policies: list[ToolPolicy]) -> None:
        self._policies = policies

    def authorize(self, context: PolicyContext, *, write: bool = False) -> None:
        risk = RiskLevel(context.risk_level)
        policy = next((item for item in self._policies if item.agent == context.agent), None)
        if policy is None or context.tool_name not in policy.tool_names:
            raise PolicyDenied(f"Tool denied: {context.agent.value} cannot use {context.tool_name}")

        if _RISK_ORDER[risk] > _RISK_ORDER[policy.max_risk]:
            raise PolicyDenied(f"Risk level denied: {risk.value} exceeds policy maximum")

        if context.relative_path:
            relative = context.relative_path.replace("\\", "/").lstrip("./")
            patterns = policy.write_paths if write else policy.read_paths
            if not any(fnmatch(relative, pattern) for pattern in patterns):
                raise PolicyDenied(f"Path denied by policy: {context.relative_path}")

        if context.command:
            parts = shlex.split(context.command, posix=True)
            if not parts or parts[0] not in policy.commands:
                raise PolicyDenied(f"Command denied by policy: {parts[0] if parts else '<empty>'}")

        if context.network_target and context.network_target not in policy.network_targets:
            raise PolicyDenied(f"Network target denied by policy: {context.network_target}")
