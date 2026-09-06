from __future__ import annotations

from typing import Any

from services.bridge.manager import BridgeConnectionManager
from services.policy.engine import PolicyContext, PolicyDenied, PolicyEngine
from packages.schemas.domain import AgentRole, RiskLevel


def build_workstation_tools(
    *,
    manager: BridgeConnectionManager,
    policy: PolicyEngine,
    agent: AgentRole,
    project_id: str,
    workspace_id: str,
    device_id: str,
):
    """Create strict, typed function tools backed by the authenticated local bridge."""
    try:
        from agents import function_tool
    except ImportError as exc:
        raise RuntimeError("openai-agents is not installed") from exc

    @function_tool(name_override="workspace_read_file")
    async def read_file(path: str) -> str:
        """Read a UTF-8 text file inside the registered project workspace."""
        policy.authorize(PolicyContext(agent, project_id, workspace_id, "file.read", RiskLevel.LOW, relative_path=path))
        result = await manager.send_tool_request(device_id, "file.read", {"path": path})
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "Local file read failed")
        return str(result.get("result", ""))

    @function_tool(name_override="workspace_write_file", needs_approval=False)
    async def write_file(path: str, content: str) -> str:
        """Write a UTF-8 text file inside an authorized workspace."""
        policy.authorize(PolicyContext(agent, project_id, workspace_id, "file.write", RiskLevel.MEDIUM, relative_path=path), write=True)
        result = await manager.send_tool_request(device_id, "file.write", {"path": path, "content": content})
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "Local file write failed")
        return str(result.get("result", ""))

    @function_tool(name_override="workspace_run_command")
    async def run_command(command: list[str]) -> dict[str, Any]:
        """Run one explicitly allowlisted development command in the workspace."""
        context = PolicyContext(agent, project_id, workspace_id, "terminal.run", RiskLevel.MEDIUM, command=" ".join(command))
        policy.authorize(context)
        result = await manager.send_tool_request(device_id, "terminal.run", {"command": command})
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "Local command failed")
        return dict(result.get("result") or {})

    @function_tool(name_override="workspace_git_diff")
    async def git_diff() -> str:
        """Return the current Git diff for the workspace."""
        policy.authorize(PolicyContext(agent, project_id, workspace_id, "git.diff", RiskLevel.LOW))
        result = await manager.send_tool_request(device_id, "git.diff", {})
        if not result.get("ok"):
            raise RuntimeError(result.get("error") or "Git diff failed")
        value = result.get("result")
        return str(value.get("stdout", value)) if isinstance(value, dict) else str(value)

    return [read_file, write_file, run_command, git_diff]
