"""Literal bounded search avoids regex DoS and external process dependencies."""

import os
from fnmatch import fnmatch
from pathlib import Path

from pydantic import Field

from mini_harness.security.workspace import Workspace, WorkspaceViolation
from mini_harness.tools.base import BaseTool, InputModel
from mini_harness.tools.builtin.filesystem import bounded_read


class GrepInput(InputModel):
    pattern: str = Field(min_length=1, max_length=1000)
    path: str = "."
    glob: str = "*.py"
    max_results: int = Field(default=100, ge=1, le=500)


class Grep(BaseTool[GrepInput]):
    name, description, input_model = (
        "grep",
        "Literal text search; returns workspace path:line:text. Bounded to 2000 files.",
        GrepInput,
    )

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def execute(self, arguments: GrepInput) -> str:
        root = self.workspace.resolve(arguments.path)
        results: list[str] = []
        count = 0
        candidates: list[Path] = []
        if root.is_file():
            candidates = [root]
        else:
            for current, dirs, files in os.walk(root, followlinks=False):
                dirs[:] = [
                    d
                    for d in dirs
                    if d not in {".git", ".venv", "__pycache__", ".sessions", ".traces", ".harness"}
                    and not (Path(current) / d).is_symlink()
                ]
                for name in sorted(files):
                    if fnmatch(name, arguments.glob):
                        candidates.append(Path(current) / name)
                        if len(candidates) >= 2000:
                            break
                if len(candidates) >= 2000:
                    break
        for path in candidates:
            count += 1
            try:
                safe = self.workspace.resolve(str(path))
                text = bounded_read(safe)
            except (UnicodeError, ValueError, OSError, WorkspaceViolation):
                continue
            for number, line in enumerate(text.splitlines(), 1):
                if arguments.pattern in line:
                    results.append(
                        f"{safe.relative_to(self.workspace.root).as_posix()}:{number}:{line[:1000]}"
                    )
                    if len(results) >= arguments.max_results:
                        return "\n".join(results) + "\n[truncated]"
        return "\n".join(results) + ("\n[file scan truncated]" if count >= 2000 else "")
