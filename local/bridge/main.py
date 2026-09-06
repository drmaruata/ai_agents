from __future__ import annotations

import argparse
import asyncio
import json
import shlex
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from packages.schemas.domain import AgentRole, RiskLevel
from services.policy.defaults import DEFAULT_POLICIES
from services.policy.engine import PolicyContext, PolicyDenied, PolicyEngine


class WorkspacePolicyError(RuntimeError):
    pass


@dataclass(slots=True)
class LocalAgentBridge:
    """Secure workstation execution boundary."""

    workspace: Path
    device_id: str
    agent: AgentRole = AgentRole.RUATA
    project_id: str = "local"
    workspace_id: str = "local-workspace"
    allowed_paths: list[Path] | None = None

    def __init__(self, workspace: str, device_id: str, *, agent: AgentRole = AgentRole.RUATA, project_id: str = "local", workspace_id: str = "local-workspace", allowed_paths: list[str] | None = None) -> None:
        self.workspace = Path(workspace).resolve()
        self.device_id = device_id
        self.agent = agent
        self.project_id = project_id
        self.workspace_id = workspace_id
        self.allowed_paths = [(self.workspace / path).resolve() for path in (allowed_paths or ["."])]
        self.policy = PolicyEngine(DEFAULT_POLICIES)

    def resolve_path(self, relative_path: str) -> Path:
        candidate = (self.workspace / relative_path).resolve()
        if not any(candidate == allowed or allowed in candidate.parents for allowed in self.allowed_paths or []):
            raise WorkspacePolicyError(f"Path is outside the allowed workspace scope: {relative_path}")
        if any(part.lower() in {".env", ".env.local", "credentials", "secrets"} for part in candidate.parts):
            raise WorkspacePolicyError("Sensitive path is blocked by policy")
        return candidate

    def read_file(self, relative_path: str) -> str:
        path = self.resolve_path(relative_path)
        self.policy.authorize(PolicyContext(self.agent, self.project_id, self.workspace_id, "file.read", RiskLevel.LOW, relative_path=relative_path))
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> Path:
        path = self.resolve_path(relative_path)
        self.policy.authorize(PolicyContext(self.agent, self.project_id, self.workspace_id, "file.write", RiskLevel.MEDIUM, relative_path=relative_path), write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def run_command(self, command: list[str], *, tool_name: str = "terminal.run", risk_level: RiskLevel = RiskLevel.MEDIUM, timeout: int = 120) -> dict[str, Any]:
        if not command:
            raise ValueError("Command cannot be empty")
        context = PolicyContext(self.agent, self.project_id, self.workspace_id, tool_name, risk_level, command=shlex.join(command))
        self.policy.authorize(context)
        started = time.perf_counter()
        try:
            completed = subprocess.run(command, cwd=self.workspace, text=True, capture_output=True, timeout=timeout, shell=False, check=False)
        except subprocess.TimeoutExpired as exc:
            return {"status": "timeout", "exit_code": None, "stdout": exc.stdout or "", "stderr": exc.stderr or "", "duration_ms": int((time.perf_counter() - started) * 1000)}
        return {"status": "succeeded" if completed.returncode == 0 else "failed", "exit_code": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr, "duration_ms": int((time.perf_counter() - started) * 1000)}


class BridgeProtocol:
    VERSION = "1"

    @classmethod
    def response(cls, request_id: str, *, ok: bool, result: Any = None, error: str | None = None) -> dict[str, Any]:
        return {"version": cls.VERSION, "type": "tool.response", "request_id": request_id, "ok": ok, "result": result, "error": error}


def with_device_id(url: str, device_id: str) -> str:
    parsed = urlsplit(url)
    query = dict(parse_qsl(parsed.query))
    query["device_id"] = device_id
    return urlunsplit((parsed.scheme, parsed.netloc, parsed.path, urlencode(query), parsed.fragment))


async def run_bridge_client(url: str, token: str, bridge: LocalAgentBridge) -> None:
    import websockets

    target = with_device_id(url, bridge.device_id)
    async with websockets.connect(target, additional_headers={"Authorization": f"Bearer {token}"}, ping_interval=20, ping_timeout=20, close_timeout=5) as websocket:
        await websocket.send(json.dumps({"type": "bridge.hello", "protocol": BridgeProtocol.VERSION, "device_id": bridge.device_id}))
        async for raw in websocket:
            message = json.loads(raw)
            if message.get("type") != "tool.request":
                continue
            request_id = str(message.get("request_id"))
            tool = str(message.get("tool"))
            args = message.get("args") or {}
            try:
                if tool == "file.read":
                    result = bridge.read_file(str(args["path"]))
                elif tool == "file.write":
                    result = str(bridge.write_file(str(args["path"]), str(args["content"])))
                elif tool == "terminal.run":
                    result = bridge.run_command(list(args["command"]))
                elif tool == "git.diff":
                    result = bridge.run_command(["git", "diff"], tool_name="git.diff", risk_level=RiskLevel.LOW)
                else:
                    raise PolicyDenied(f"Unsupported bridge tool: {tool}")
                await websocket.send(json.dumps(BridgeProtocol.response(request_id, ok=True, result=result)))
            except Exception as exc:
                await websocket.send(json.dumps(BridgeProtocol.response(request_id, ok=False, error=str(exc))))


def main() -> None:
    parser = argparse.ArgumentParser(description="Ruata Local Agent Bridge")
    parser.add_argument("--workspace", required=True)
    parser.add_argument("--url", required=True)
    parser.add_argument("--token", required=True)
    parser.add_argument("--device-id", required=True)
    parser.add_argument("--agent", default="ruata", choices=[role.value for role in AgentRole])
    parser.add_argument("--project-id", default="local")
    parser.add_argument("--workspace-id", default="local-workspace")
    args = parser.parse_args()
    bridge = LocalAgentBridge(args.workspace, args.device_id, agent=AgentRole(args.agent), project_id=args.project_id, workspace_id=args.workspace_id)
    asyncio.run(run_bridge_client(args.url, args.token, bridge))


if __name__ == "__main__":
    main()
