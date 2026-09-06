from __future__ import annotations

from pathlib import Path


class WorkspacePolicyError(RuntimeError):
    pass


class LocalAgentBridge:
    """Minimal local execution boundary.

    This scaffold intentionally implements policy checks before process execution is
    added. Production execution should use an explicit command/tool allowlist.
    """

    def __init__(self, workspace: str, allowed_paths: list[str] | None = None) -> None:
        self.workspace = Path(workspace).resolve()
        self.allowed_paths = [
            (self.workspace / path).resolve() for path in (allowed_paths or ["."])
        ]

    def resolve_path(self, relative_path: str) -> Path:
        candidate = (self.workspace / relative_path).resolve()
        if not any(candidate == allowed or allowed in candidate.parents for allowed in self.allowed_paths):
            raise WorkspacePolicyError(f"Path is outside the allowed workspace scope: {relative_path}")
        if any(part in {".env", ".env.local", "credentials", "secrets"} for part in candidate.parts):
            raise WorkspacePolicyError("Sensitive path is blocked by policy")
        return candidate
