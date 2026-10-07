"""Fixed argv templates; no shell expansion. Execute permission is not an OS sandbox."""

import asyncio
import json
import os
import signal
import subprocess
import sys
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import Field

from mini_harness.security.permissions import Permission
from mini_harness.security.workspace import Workspace
from mini_harness.tools.base import BaseTool, InputModel


async def run_process(
    argv: list[str], cwd: str, limit: int = 16000, *, extra_env: dict[str, str] | None = None
) -> str:
    options: dict[str, Any] = (
        {"creationflags": subprocess.CREATE_NEW_PROCESS_GROUP}
        if sys.platform == "win32"
        else {"start_new_session": True}
    )
    env = {k: v for k, v in os.environ.items() if not k.startswith(("PYTHON", "GIT_"))}
    env.update(
        {"PYTHONIOENCODING": "utf-8", "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
    )

    env.update(extra_env or {})

    async def terminate(process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        if sys.platform == "win32":
            killer = await asyncio.create_subprocess_exec(
                "taskkill",
                "/PID",
                str(process.pid),
                "/T",
                "/F",
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.DEVNULL,
            )
            await killer.wait()
            if killer.returncode != 0 and process.returncode is None:
                process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
        await process.wait()

    # Shield spawn: cancellation while asyncio creates the process must not lose its handle.
    spawning = asyncio.create_task(
        asyncio.create_subprocess_exec(
            *argv,
            cwd=cwd,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **options,
        )
    )
    try:
        process = await asyncio.shield(spawning)
    except asyncio.CancelledError:
        process = await spawning
        await terminate(process)
        if process.stdout:
            await process.stdout.read()
        if process.stderr:
            await process.stderr.read()
        raise

    async def drain(stream: asyncio.StreamReader | None) -> str:
        assert stream is not None
        data = bytearray()
        truncated = False
        while block := await stream.read(4096):
            room = max(0, limit - len(data))
            data.extend(block[:room])
            truncated |= len(block) > room
        return data.decode("utf-8", errors="replace") + ("\n[truncated]" if truncated else "")

    out_task, err_task = (
        asyncio.create_task(drain(process.stdout)),
        asyncio.create_task(drain(process.stderr)),
    )
    try:
        await process.wait()
        stdout, stderr = await asyncio.gather(out_task, err_task)
    except BaseException:
        await terminate(process)
        await asyncio.gather(out_task, err_task, return_exceptions=True)
        raise
    return json.dumps(
        {"exit_code": process.returncode, "stdout": stdout, "stderr": stderr}, ensure_ascii=False
    )


class CommandInput(InputModel):
    argv: list[str] = Field(min_length=1, max_length=8)
    cwd: str = "."


class TestInput(InputModel):
    paths: list[str] = Field(default_factory=lambda: ["tests"], min_length=1, max_length=20)
    maxfail: int = Field(default=1, ge=1, le=10)


def trusted_git(workspace: Workspace) -> str | None:
    """Pin an executable from absolute host PATH entries outside the mutable workspace."""
    filename = "git.exe" if sys.platform == "win32" else "git"
    for entry in os.get_exec_path():
        directory = Path(entry)
        if not directory.is_absolute():
            continue
        try:
            candidate = (directory / filename).resolve()
            if candidate.is_relative_to(workspace.root):
                continue
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
        except OSError:
            continue
    return None


class RunCommand(BaseTool[CommandInput]):
    name, description, input_model = (
        "run_command",
        'Only argv ["python","--version"], ["git","status","--short"], ["git","diff","--stat"] allowed. No shell.',
        CommandInput,
    )
    permission, side_effect = Permission.EXECUTE, True

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace
        self.git_executable = trusted_git(workspace)

    async def execute(self, arguments: CommandInput) -> str:
        allowed = [["python", "--version"], ["git", "status", "--short"], ["git", "diff", "--stat"]]
        if arguments.argv not in allowed:
            raise PermissionError(
                "Command template not authorized; arbitrary executables/shell syntax forbidden"
            )
        cwd = str(self.workspace.resolve(arguments.cwd))
        if arguments.argv[0] == "python":
            return await run_process([sys.executable, "--version"], cwd)
        if self.git_executable is None:
            raise FileNotFoundError(
                "No trusted Git executable outside workspace found on absolute host PATH"
            )
        git_args = arguments.argv[1:]
        if git_args[0] == "diff":
            git_args = ["diff", "--no-ext-diff", "--no-textconv", "--stat"]
        return await run_process(
            [self.git_executable, "-c", "core.fsmonitor=false", *git_args],
            cwd,
            extra_env={"GIT_CEILING_DIRECTORIES": str(self.workspace.root.parent)},
        )


class RunTests(BaseTool[TestInput]):
    name, description, input_model = (
        "run_tests",
        "Run installed pytest against workspace paths; requires trusted code and execute permission.",
        TestInput,
    )
    permission, side_effect, timeout = Permission.EXECUTE, True, 90

    def __init__(self, workspace: Workspace) -> None:
        self.workspace = workspace

    async def execute(self, arguments: TestInput) -> str:
        paths = [str(self.workspace.resolve(p)) for p in arguments.paths]
        temp = self.workspace.root / ".harness" / ("pytest-" + uuid4().hex)
        temp.parent.mkdir(exist_ok=True)
        return await run_process(
            [
                sys.executable,
                "-B",
                "-X",
                f"pycache_prefix={temp / 'bytecode'}",
                "-m",
                "pytest",
                "-q",
                "--disable-warnings",
                f"--rootdir={self.workspace.root}",
                f"--basetemp={temp}",
                f"--maxfail={arguments.maxfail}",
                "--",
                *paths,
            ],
            str(self.workspace.root),
        )
