from __future__ import annotations

import asyncio
import json
import shlex
import subprocess
import time
from pathlib import Path
from typing import Any

from packages.schemas.domain import AgentRole, RiskLevel
from services.policy.defaults import DEFAULT_POLICIES
from services.policy.engine import PolicyContext, PolicyDenied, PolicyEngine


class WorkspacePolicyError(RuntimeError):
    pass


class LocalAgentBridge:
    """Secure workstation execution boundary.

    The bridge only operates inside an explicitly registered workspace and
    delegates authorization to the shared policy engine before touching files
    or starting subprocesses.
    """

    def __init__(
        self,
        workspace: str,
        *,
        agent: AgentRole = AgentRole.RUATA,
        project_id: str = "local",
        workspace_id: str = "local-workspace",
        allowed_paths: list[str] | None = None,
    ) -> None:
        self.workspace = Path(workspace).resolve()
        self.agent = agent
        self.project_id = project_id
        self.workspace_id = workspace_id
        self.allowed_paths = [
            (self.workspace / path).resolve() for path in (allowed_paths or ["."])
        ]
        self.policy = PolicyEngine(DEFAULT_POLICIES)

    def resolve_path(self, relative_path: str) -> Path:
        candidate = (self.workspace / relative_path).resolve()
        if not any(candidate == allowed or allowed in candidate.parents for allowed in self.allowed_paths):
            raise WorkspacePolicyError(f"Path is outside the allowed workspace scope: {relative_path}")
        if any(part.lower() in {".env", ".env.local", "credentials", "secrets"} for part in candidate.parts):
            raise WorkspacePolicyError("Sensitive path is blocked by policy")
        return candidate

    def read_file(self, relative_path: str) -> str:
        path = self.resolve_path(relative_path)
        context = PolicyContext(
            agent=self.agent,
            project_id=self.project_id,
            workspace_id=self.workspace_id,
            tool_name="file.read",
            risk_level=RiskLevel.LOW,
            relative_path=relative_path,
        )
        self.policy.authorize(context)
        return path.read_text(encoding="utf-8")

    def write_file(self, relative_path: str, content: str) -> Path:
        path = self.resolve_path(relative_path)
        context = PolicyContext(
            agent=self.agent,
            project_id=self.project_id,
            workspace_id=self.workspace_id,
            tool_name="file.write",
            risk_level=RiskLevel.MEDIUM,
            relative_path=relative_path,
        )
        self.policy.authorize(context, write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def git_diff(self) -> str:
        return self.run_command(["git", "diff"], tool_name="git.diff", risk_level=RiskLevel.LOW)["stdout"]

    def run_command(self, command: list[str], *, tool_name: str = "terminal.run", risk_level: RiskLevel = RiskLevel.MEDIUM, timeout: int = 120) -> dict[str, Any]:
        if not command:
            raise ValueError("Command cannot be empty")
        command_text = shlex.join(command)
        context = PolicyContext(
            agent=self.agent,
            project_id=self.project_id,
            workspace_id=self.workspace_id,
            tool_name=tool_name,
            risk_level=risk_level,
            command=command_text,
        )
        self.policy.authorize(context)
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                command,
                cwd=self.workspace,
                text=True,
                capture_output=True,
                timeout=timeout,
                shell=False,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            return {
                "status": "timeout",
                "exit_code": None,
                "stdout": exc.stdout or "",
                "stderr": exc.stderr or "",
                "duration_ms": int((time.perf_counter() - started) * 1000),
            }
        return {
            "status": "succeeded" if completed.returncode == 0 else "failed",
            "exit_code": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "duration_ms": int((time.perf_counter() - started) * 1000),
        }


class BridgeProtocol:
    """Request/response protocol used by the outbound WebSocket client."""

    VERSION = "1"

    @classmethod
    def request(cls, request_id: str, tool: str, args: dict[str, Any]) -> dict[str, Any]:
        return {"version": cls.VERSION, "type": "tool.request", "request_id": request_id, "tool": tool, "args": args}

    @classmethod
    def response(cls, request_id: str, *, ok: bool, result: Any = None, error: str | None = None) -> dict[str, Any]:
        return {"version": cls.VERSION, "type": "tool.response", "request_id": request_id, "ok": ok, "result": result, "error": error}


async def run_bridge_client(url: str, token: str, bridge: LocalAgentBridge) -> None:
    """Maintain an outbound authenticated WebSocket connection with fail-closed execution."""
    import websockets

    async with websockets.connect(
        url,
        additional_headers={"Authorization": f"Bearer {token}"},
        ping_interval=20,
        ping_timeout=20,
        close_timeout=5,
    ) as websocket:
        await websocket.send(json.dumps({"type": "bridge.hello", "protocol": BridgeProtocol.VERSION}))
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
                elif tool == "git.diff":
                    result = bridge.git_diff()
                elif tool == "terminal.run":
                    result = bridge.run_command(list(args["command"]))
                else:
                    raise PolicyDenied(f"Unsupported bridge tool: {tool}")
                await websocket.send(json.dumps(BridgeProtocol.response(request_id, ok=True, result=result)))
            except Exception as exc:
                await websocket.send(json.dumps(BridgeProtocol.response(request_id, ok=False, error=str(exc))))
