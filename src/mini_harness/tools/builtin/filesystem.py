"""Bounded filesystem tools with exact, atomic edits and workspace guards."""

import os
import tempfile
from pathlib import Path

from pydantic import Field

from mini_harness.security.permissions import Permission
from mini_harness.security.workspace import Workspace
from mini_harness.tools.base import BaseTool, InputModel

MAX_BYTES = 1_048_576


class PathInput(InputModel):
    path: str = "."


class ReadInput(InputModel):
    path: str
    start_line: int = Field(default=1, ge=1)
    end_line: int | None = Field(default=None, ge=1)


class WriteInput(InputModel):
    path: str
    content: str = Field(max_length=MAX_BYTES)


class EditInput(InputModel):
    path: str
    old: str = Field(min_length=1)
    new: str
    expected_count: int = Field(default=1, ge=1)


def bounded_read(path: Path) -> str:
    with path.open("rb") as handle:
        data = handle.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("File exceeds 1 MiB read limit")
    return data.decode("utf-8")


def atomic_write(path: Path, content: str) -> None:
    data = content.encode("utf-8")
    if len(data) > MAX_BYTES:
        raise ValueError("File exceeds 1 MiB write limit")
    if not path.parent.is_dir():
        raise FileNotFoundError("Parent directory must exist")
    fd, name = tempfile.mkstemp(prefix=".harness-edit-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if path.exists():
            os.chmod(name, path.stat().st_mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)


class ListDir(BaseTool[PathInput]):
    name, description, input_model = (
        "list_dir",
        "List immediate workspace entries (up to 200).",
        PathInput,
    )

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def execute(self, arguments: PathInput) -> str:
        path = self.workspace.resolve(arguments.path)
        entries = sorted(path.iterdir(), key=lambda p: p.name)
        return "\n".join(p.name + ("/" if p.is_dir() else "") for p in entries[:200]) + (
            "\n[truncated]" if len(entries) > 200 else ""
        )


class ReadFile(BaseTool[ReadInput]):
    name, description, input_model = (
        "read_file",
        "Read UTF-8 workspace file with optional 1-based line range.",
        ReadInput,
    )

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def execute(self, arguments: ReadInput) -> str:
        if arguments.end_line is not None and arguments.end_line < arguments.start_line:
            raise ValueError("end_line must be >= start_line")
        text = bounded_read(self.workspace.resolve(arguments.path))
        lines = text.splitlines(keepends=True)
        return "".join(lines[arguments.start_line - 1 : arguments.end_line])


class WriteFile(BaseTool[WriteInput]):
    name, description, input_model = (
        "write_file",
        "Create or replace a UTF-8 file inside workspace. Parent must exist.",
        WriteInput,
    )
    permission, side_effect = Permission.WRITE, True

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def execute(self, arguments: WriteInput) -> str:
        path = self.workspace.resolve(arguments.path, write=True)
        atomic_write(path, arguments.content)
        return f"Wrote {len(arguments.content.encode('utf-8'))} bytes to {arguments.path}"


class EditFile(BaseTool[EditInput]):
    name, description, input_model = (
        "edit_file",
        "Exact replacement; old must occur expected_count times. Atomic write.",
        EditInput,
    )
    permission, side_effect = Permission.WRITE, True

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def execute(self, arguments: EditInput) -> str:
        path = self.workspace.resolve(arguments.path, write=True)
        text = bounded_read(path)
        count = text.count(arguments.old)
        if count != arguments.expected_count:
            raise ValueError(f"Expected {arguments.expected_count} matches; found {count}")
        atomic_write(path, text.replace(arguments.old, arguments.new))
        return f"Replaced {count} matches in {arguments.path}"
