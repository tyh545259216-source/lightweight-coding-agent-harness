import asyncio
import json
import sys
from pathlib import Path

import pytest

from mini_harness.agent.runner import AgentRunner
from mini_harness.providers.base import ModelResponse
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.session.store import SessionStore
from mini_harness.tools.base import BaseTool, InputModel
from mini_harness.tools.builtin.shell import run_process
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry

ROOT = Path(__file__).resolve().parents[1]


class NeverRepeat(BaseTool[InputModel]):
    name, description, input_model = "effect", "Do not execute after recovery", InputModel
    permission, side_effect = Permission.WRITE, True

    async def execute(self, arguments):
        raise AssertionError("side effect was repeated")


@pytest.mark.parametrize(
    "mode,exit_code,expected",
    [("uncertain", 91, "recovery_blocked"), ("committed", 92, "final_answer")],
)
async def test_actual_process_crash_and_os_lock_release(tmp_path, mode, exit_code, expected):
    process = await asyncio.create_subprocess_exec(
        sys.executable,
        str(ROOT / "examples/crash_worker.py"),
        str(tmp_path),
        mode,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await process.communicate()
    assert process.returncode == exit_code, (stdout, stderr)
    assert (tmp_path / "counter.txt").read_text(encoding="utf-8") == "1"
    (tmp_path / "counter.txt").write_text("2", encoding="utf-8")
    store = SessionStore(tmp_path / "session.jsonl")
    registry = ToolRegistry()
    registry.register(NeverRepeat())
    executor = ToolExecutor(registry, PermissionPolicy({Permission.WRITE}), store)
    result = await AgentRunner(
        FakeProvider([ModelResponse(content="done")]), executor, session=store
    ).resume()
    assert result.stop_reason.value == expected
    assert (tmp_path / "counter.txt").read_text(encoding="utf-8") == "2"


async def test_subprocess_output_bounded(tmp_path):
    result = json.loads(
        await run_process([sys.executable, "-c", 'print("x"*50000)'], str(tmp_path), limit=1024)
    )
    assert (
        result["exit_code"] == 0
        and len(result["stdout"]) < 1100
        and "[truncated]" in result["stdout"]
    )


async def test_subprocess_timeout_kills_child(tmp_path):
    # The delayed side effect must not appear after timeout, proving process termination.
    code = (
        'import time; from pathlib import Path; time.sleep(3); Path("late.txt").write_text("bad")'
    )
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.2):
            await run_process([sys.executable, "-c", code], str(tmp_path))
    await asyncio.sleep(3.1)
    assert not (tmp_path / "late.txt").exists()


async def test_cancellation_during_spawn_does_not_orphan_process(tmp_path, monkeypatch):
    original = asyncio.create_subprocess_exec

    async def delayed_spawn(*args, **kwargs):
        process = await original(*args, **kwargs)
        if args[0] == sys.executable:
            await asyncio.sleep(0.3)
        return process

    monkeypatch.setattr(asyncio, "create_subprocess_exec", delayed_spawn)
    code = (
        'import time; from pathlib import Path; time.sleep(2); Path("orphan.txt").write_text("bad")'
    )
    with pytest.raises(TimeoutError):
        async with asyncio.timeout(0.05):
            await run_process([sys.executable, "-c", code], str(tmp_path))
    await asyncio.sleep(2.1)
    assert not (tmp_path / "orphan.txt").exists()
