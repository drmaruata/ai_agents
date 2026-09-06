from __future__ import annotations

import asyncio
import subprocess
import uuid
from typing import Any

from .base import Sandbox, SandboxSpec


class DockerSandbox(Sandbox):
    """Development sandbox adapter using local Docker.

    A remote sandbox provider can implement the same interface later without
    changing orchestrator or agent code.
    """

    def __init__(self) -> None:
        self.containers: set[str] = set()

    async def provision(self, spec: SandboxSpec) -> str:
        sandbox_id = f"ruata-sbx-{uuid.uuid4().hex[:12]}"
        args = ["docker", "run", "-d", "--name", sandbox_id]
        if not spec.network_enabled:
            args += ["--network", "none"]
        args += [spec.image, "sleep", str(spec.timeout_seconds)]
        result = await asyncio.to_thread(subprocess.run, args, text=True, capture_output=True, check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr.strip() or "Unable to provision Docker sandbox")
        self.containers.add(sandbox_id)
        return sandbox_id

    async def execute(self, sandbox_id: str, command: list[str]) -> dict[str, Any]:
        if sandbox_id not in self.containers:
            raise KeyError(sandbox_id)
        result = await asyncio.to_thread(
            subprocess.run,
            ["docker", "exec", sandbox_id, *command],
            text=True,
            capture_output=True,
            check=False,
        )
        return {"status": "succeeded" if result.returncode == 0 else "failed", "exit_code": result.returncode, "stdout": result.stdout, "stderr": result.stderr}

    async def destroy(self, sandbox_id: str) -> None:
        if sandbox_id not in self.containers:
            return
        await asyncio.to_thread(subprocess.run, ["docker", "rm", "-f", sandbox_id], text=True, capture_output=True, check=False)
        self.containers.discard(sandbox_id)
