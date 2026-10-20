from pathlib import Path

import pytest

from local.bridge.main import LocalAgentBridge, WorkspacePolicyError
from packages.schemas.domain import AgentRole, RiskLevel


def test_local_bridge_reads_and_writes_within_workspace(tmp_path: Path) -> None:
    bridge = LocalAgentBridge(str(tmp_path), "device-test", agent=AgentRole.MANASSEH)
    bridge.write_file("src/example.py", "print('ok')")

    assert bridge.read_file("src/example.py") == "print('ok')"
    assert (tmp_path / "src" / "example.py").exists()


def test_local_bridge_rejects_path_traversal(tmp_path: Path) -> None:
    bridge = LocalAgentBridge(str(tmp_path), "device-test")

    with pytest.raises(WorkspacePolicyError, match="outside the allowed workspace scope"):
        bridge.resolve_path("../outside.txt")


@pytest.mark.parametrize("path", [".env", ".env.local", "config/secrets.json", "credentials/token.txt"])
def test_local_bridge_blocks_sensitive_paths(tmp_path: Path, path: str) -> None:
    bridge = LocalAgentBridge(str(tmp_path), "device-test")

    with pytest.raises(WorkspacePolicyError, match="Sensitive path is blocked"):
        bridge.resolve_path(path)


def test_local_bridge_command_runs_without_shell(tmp_path: Path) -> None:
    bridge = LocalAgentBridge(str(tmp_path), "device-test", agent=AgentRole.JOHN)
    result = bridge.run_command(
        ["python", "-c", "print('bridge-ok')"],
        risk_level=RiskLevel.LOW,
    )

    assert result["status"] == "succeeded"
    assert result["exit_code"] == 0
    assert "bridge-ok" in result["stdout"]
