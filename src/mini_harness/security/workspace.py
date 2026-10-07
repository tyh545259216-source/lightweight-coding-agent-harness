"""Resolved path containment including existing symlinks/junctions."""

from collections.abc import Sequence
from pathlib import Path, PureWindowsPath


class WorkspaceViolation(PermissionError):
    pass


class Workspace:
    def __init__(
        self,
        root: Path,
        protected_files: Sequence[Path] = (),
        *,
        readonly_files: Sequence[Path] = (),
    ) -> None:
        self.root = root.resolve(strict=True)
        self._readonly_files = {p.resolve() for p in readonly_files}
        self._protected_files = {p.resolve() for p in protected_files}
        self._protected_files.update(
            p.with_suffix(p.suffix + ".lock") for p in list(self._protected_files)
        )
        if not self.root.is_dir():
            raise ValueError("Workspace must be a directory")

    def resolve(self, raw: str, *, write: bool = False) -> Path:
        if not raw or "\x00" in raw:
            raise WorkspaceViolation("Invalid path")
        relative = Path(raw)
        if ".." in relative.parts or ".." in PureWindowsPath(raw).parts:
            raise WorkspaceViolation("Parent traversal is forbidden")
        if PureWindowsPath(raw).drive and not relative.is_absolute():
            raise WorkspaceViolation("Foreign or drive-relative path")
        candidate = (self.root / relative).resolve()
        if not candidate.is_relative_to(self.root):
            raise WorkspaceViolation("Path escapes workspace")
        if write and candidate in self._readonly_files:
            raise WorkspaceViolation("Task contract file is read-only for model file tools")
        if candidate in self._protected_files:
            raise WorkspaceViolation("Configured session/trace file is protected")
        protected = {".git", ".venv", ".sessions", ".traces", ".harness"}
        if any(p.lower() in protected for p in candidate.relative_to(self.root).parts):
            raise WorkspaceViolation("Harness bookkeeping and Git internals are protected")
        return candidate
