from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SandboxSpec:
    project_id: str
    task_id: str
    image: str = "ubuntu:24.04"
    network_enabled: bool = False
    timeout_seconds: int = 1800
    environment: dict[str, str] = field(default_factory=dict)


class Sandbox(ABC):
    @abstractmethod
    async def provision(self, spec: SandboxSpec) -> str: ...

    @abstractmethod
    async def execute(self, sandbox_id: str, command: list[str]) -> dict[str, Any]: ...

    @abstractmethod
    async def destroy(self, sandbox_id: str) -> None: ...
