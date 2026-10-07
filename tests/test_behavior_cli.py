"""V3 CLI never infers write/execute grants from a coding task or skill."""

import json

import pytest

from mini_harness.behavior_cli import parser, run
from mini_harness.providers.base import ModelResponse
from mini_harness.providers.fake import FakeProvider


async def test_read_only_cli_actual_journal_and_structured_result(tmp_path, monkeypatch, capsys):
    class LocalProvider(FakeProvider):
        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def check_model(self):
            pass

    monkeypatch.setattr(
        "mini_harness.behavior_cli.OpenAICompatibleProvider",
        lambda *a, **kw: LocalProvider([ModelResponse(content="hello")]),
    )
    workspace = tmp_path / "repo"
    workspace.mkdir()
    args = parser().parse_args(
        ["Say hello", "--workspace", str(workspace), "--output", str(tmp_path / "run")]
    )
    await run(args)
    result = json.loads(capsys.readouterr().out)
    assert result["stop_reason"] == "final_answer" and result["verification_status"] == "UNVERIFIED"
    assert (tmp_path / "run" / "session.jsonl").is_file()
    assert not args.allow_write and not args.allow_execute


async def test_coding_cli_requires_explicit_changed_target(tmp_path):
    args = parser().parse_args(
        ["Fix", "--coding", "--workspace", str(tmp_path), "--output", str(tmp_path / "out")]
    )
    with pytest.raises(ValueError, match="target"):
        await run(args)
    assert not (tmp_path / "out").exists()
