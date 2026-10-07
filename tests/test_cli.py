import json
from argparse import Namespace

import pytest

from mini_harness.cli import execute


def args(tmp_path, command="run"):
    return Namespace(
        command=command,
        workspace=tmp_path,
        provider="fake",
        script=tmp_path / "script.json",
        task="hello",
        allow_write=False,
        allow_execute=False,
        session=None,
        trace=None,
        skills=None,
        max_iterations=8,
        model_timeout=10,
        task_timeout=30,
        context_budget=8192,
    )


async def test_cli_offline_run(tmp_path, capsys):
    a = args(tmp_path)
    a.script.write_text('[{"content":"done"}]', encoding="utf-8")
    assert await execute(a) == 0
    assert json.loads(capsys.readouterr().out)["answer"] == "done"


async def test_cli_fake_requires_script(tmp_path):
    a = args(tmp_path)
    a.script = None
    with pytest.raises(ValueError):
        await execute(a)


async def test_demo_requires_new_workspace(tmp_path):
    a = args(tmp_path, "demo")
    with pytest.raises(ValueError):
        await execute(a)


async def test_offline_demo(tmp_path, capsys):
    a = args(tmp_path, "demo")
    a.workspace = tmp_path / "demo"
    assert await execute(a) == 0
    result = json.loads(capsys.readouterr().out)
    assert result["stats"]["tool_successes"] == 6 and result["stop_reason"] == "final_answer"
