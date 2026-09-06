from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess


class WorktreeError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class WorktreeSpec:
    task_id: str
    repository: Path
    root: Path
    branch: str


class WorktreeManager:
    """Local Git worktree lifecycle helper.

    The caller is responsible for applying the policy/approval gate before
    invoking mutating operations.
    """

    def create(self, spec: WorktreeSpec) -> Path:
        target = spec.root / spec.task_id
        target.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "-C", str(spec.repository), "worktree", "add", "-b", spec.branch, str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise WorktreeError(result.stderr.strip() or "git worktree add failed")
        return target

    def remove(self, repository: Path, target: Path) -> None:
        result = subprocess.run(
            ["git", "-C", str(repository), "worktree", "remove", "--force", str(target)],
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise WorktreeError(result.stderr.strip() or "git worktree remove failed")
