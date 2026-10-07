import asyncio
import json

import pytest

from mini_harness.providers.base import ToolCall
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.tools.base import BaseTool, InputModel
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.builtin.filesystem import (
    MAX_BYTES,
    atomic_write,
    bounded_read,
)
from mini_harness.tools.executor import ToolExecutor


@pytest.fixture
def executor(tmp_path):
    (tmp_path / "app.py").write_text("def entry():\n    return 1\n", encoding="utf-8")
    return ToolExecutor(builtin_registry(Workspace(tmp_path)), PermissionPolicy(set(Permission)))


async def call(executor, name, arguments):
    return await executor.execute(ToolCall(id="1", name=name, arguments=arguments), "key")


async def test_complete_tool_flow(executor, tmp_path):
    assert "app.py" in (await call(executor, "list_dir", {})).content
    assert "app.py:1:" in (await call(executor, "grep", {"pattern": "entry"})).content
    assert "return 1" in (await call(executor, "read_file", {"path": "app.py"})).content
    assert (
        await call(executor, "edit_file", {"path": "app.py", "old": "return 1", "new": "return 2"})
    ).ok
    assert (
        await call(
            executor,
            "write_file",
            {
                "path": "test_app.py",
                "content": "from app import entry\ndef test_entry(): assert entry() == 2\n",
            },
        )
    ).ok
    result = await call(executor, "run_tests", {"paths": ["test_app.py"]})
    assert result.ok and json.loads(result.content)["exit_code"] == 0
    assert "1 passed" in result.content


async def test_registry(executor):
    r = executor.registry
    assert len(r.list()) == 7 and len(r.get_definitions()) == 7
    with pytest.raises(ValueError):
        r.register(r.get("read_file"))
    r.unregister("grep")
    with pytest.raises(KeyError):
        r.get("grep")
    assert r.get_definitions()[0].parameters


@pytest.mark.parametrize(
    "arguments",
    [
        {"path": 1},
        {"path": "app.py", "extra": True},
        "bad",
        "[]",
        {"start_line": 0, "path": "app.py"},
    ],
)
async def test_validation(executor, arguments):
    result = await call(executor, "read_file", arguments)
    assert result.error_type == "arguments"


async def test_json_args_and_unknown(executor):
    assert (await call(executor, "read_file", '{"path":"app.py"}')).ok
    assert (await call(executor, "missing", {})).error_type == "unknown_tool"


async def test_filesystem_errors(executor):
    assert (await call(executor, "read_file", {"path": "missing"})).error_type == "execution"
    assert (
        await call(executor, "edit_file", {"path": "app.py", "old": "missing", "new": "x"})
    ).error_type == "execution"
    assert (
        await call(executor, "read_file", {"path": "app.py", "start_line": 3, "end_line": 1})
    ).error_type == "execution"
    assert (
        await call(executor, "write_file", {"path": "missing/a", "content": "x"})
    ).error_type == "execution"


async def test_default_readonly(tmp_path):
    e = ToolExecutor(builtin_registry(Workspace(tmp_path)))
    assert (await call(e, "write_file", {"path": "x", "content": "x"})).error_type == "permission"


async def test_command_guard(executor):
    assert (
        await call(executor, "run_command", {"argv": ["cmd", "/c", "echo hacked"]})
    ).error_type == "permission"
    assert (
        json.loads(
            (await call(executor, "run_command", {"argv": ["python", "--version"]})).content
        )["exit_code"]
        == 0
    )


async def test_read_lines(executor):
    assert (
        await call(executor, "read_file", {"path": "app.py", "start_line": 2, "end_line": 2})
    ).content.splitlines() == ["    return 1"]


def test_size_caps(tmp_path):
    p = tmp_path / "big"
    p.write_bytes(b"x" * (MAX_BYTES + 1))
    with pytest.raises(ValueError):
        bounded_read(p)
    with pytest.raises(ValueError):
        atomic_write(tmp_path / "x", "x" * (MAX_BYTES + 1))


async def test_search_truncation(executor, tmp_path):
    (tmp_path / "app.py").write_text("entry\nentry\n", encoding="utf-8")
    assert (
        "[truncated]"
        in (await call(executor, "grep", {"pattern": "entry", "max_results": 1})).content
    )
    (tmp_path / "bad.py").write_bytes(b"\xff")
    assert (await call(executor, "grep", {"pattern": "entry", "path": "app.py"})).ok


class SlowTool(BaseTool[InputModel]):
    name, description, input_model, timeout = "slow", "test", InputModel, 0.01

    async def execute(self, arguments):
        await asyncio.sleep(2)
        return "late"


async def test_timeout_and_cancel(executor):
    executor.registry.register(SlowTool())
    assert (await call(executor, "slow", {})).error_type == "timeout"
    task = asyncio.create_task(call(executor, "slow", {}))
    await asyncio.sleep(0.001)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


async def test_git_executable_cannot_be_shadowed_by_workspace_batch(tmp_path):

    from mini_harness.tools.builtin.shell import CommandInput, RunCommand

    marker = tmp_path / "hijacked.txt"
    (tmp_path / "git.bat").write_text("@echo off\necho BAD > hijacked.txt\n", encoding="utf-8")
    tool = RunCommand(Workspace(tmp_path))
    if tool.git_executable is None:
        pytest.skip("Git not installed on absolute host PATH")
    assert not tool.git_executable.startswith(str(tmp_path))
    result = json.loads(await tool.execute(CommandInput(argv=["git", "status", "--short"])))
    assert result["exit_code"] != 0  # ceiling prevents discovering the harness repo above fixture
    assert not marker.exists()
