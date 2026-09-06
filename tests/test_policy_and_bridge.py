from pathlib import Path

import pytest

from local.bridge.main import LocalAgentBridge, WorkspacePolicyError
from packages.schemas.domain import AgentRole
from services.policy.engine import PolicyContext, PolicyDenied, PolicyEngine
from services.policy.defaults import DEFAULT_POLICIES


def test_policy_denies_unapproved_command():
    engine = PolicyEngine(DEFAULT_POLICIES)
    context = PolicyContext(
        agent=AgentRole.MANASSEH,
        project_id="p",
        workspace_id="w",
        tool_name="terminal.run",
        risk_level="medium",
        command="rm -rf .",
    )
    with pytest.raises(PolicyDenied):
        engine.authorize(context)


def test_bridge_blocks_sensitive_file(tmp_path: Path):
    (tmp_path / ".env").write_text("SECRET=x", encoding="utf-8")
    bridge = LocalAgentBridge(str(tmp_path), agent=AgentRole.MANASSEH)
    with pytest.raises(WorkspacePolicyError):
        bridge.read_file(".env")


def test_bridge_allows_scoped_frontend_write(tmp_path: Path):
    bridge = LocalAgentBridge(str(tmp_path), agent=AgentRole.MANASSEH)
    target = tmp_path / "frontend" / "app.tsx"
    bridge.write_file("frontend/app.tsx", "export const App = () => null")
    assert target.read_text(encoding="utf-8") == "export const App = () => null"
