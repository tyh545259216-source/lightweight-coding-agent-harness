"""Hints are bounded data and never silently execute a guessed corrected effect."""

import json

from mini_harness.providers.base import ToolCall
from mini_harness.security.workspace import Workspace
from mini_harness.tools.argument_repair import ArgumentRepairController
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor


def setup(tmp_path, limit=1):
    (tmp_path / "module.py").write_text("x=1\ny=2\n", encoding="utf-8")
    return ToolExecutor(
        builtin_registry(Workspace(tmp_path), navigation_v2=True),
        argument_repair=ArgumentRepairController(limit),
    )


async def invoke(ex, name, args, key):
    return await ex.execute(ToolCall(id=key, name=name, arguments=args), key)


async def test_schema_error_points_at_field_and_does_not_echo_unbounded_input(tmp_path):
    ex = setup(tmp_path)
    result = await invoke(ex, "grep", {"pattern": "x", "max_results": 999}, "bad")
    data = json.loads(result.content)
    assert data["error_type"] == "arguments" and data["invalid_field"] == "max_results"
    assert data["received"] == 999 and data["retryable"]
    result = await invoke(ex, "read_file", {"path": "x" * 10000, "start_line": "wrong"}, "other")
    assert result.error_detail and len(result.content) < 1200


async def test_range_error_contains_total_and_corrected_call_recovers(tmp_path):
    ex = setup(tmp_path)
    result = await invoke(ex, "read_file", {"path": "module.py", "start_line": 12}, "bad")
    assert result.error_detail.total_lines == 2 and result.error_detail.legal_range == [1, 2]
    fixed = await invoke(ex, "read_file", {"path": "module.py", "start_line": 1}, "fixed")
    assert fixed.ok and ex.argument_repair.state.recovered == 1


async def test_missing_path_has_only_confirmable_workspace_candidates(tmp_path):
    ex = setup(tmp_path)
    result = await invoke(ex, "read_file", {"path": "modul.py"}, "bad")
    detail = result.error_detail
    assert detail.error_type == "path_not_found" and detail.candidates == ["module.py"]
    assert not ex.argument_repair.state.recovered
    assert (tmp_path / "module.py").read_text() == "x=1\ny=2\n"


async def test_repeated_identical_invalid_calls_are_bounded(tmp_path):
    ex = setup(tmp_path)
    for key in ["bad1", "bad2"]:
        result = await invoke(ex, "read_file", {"path": "missing.py"}, key)
        assert result.error_detail.error_type == "path_not_found"
    blocked = await invoke(ex, "read_file", {"path": "missing.py"}, "bad3")
    assert blocked.error_type == "retry_limit" and not blocked.error_detail.retryable
    assert ex.argument_repair.state.errors == 2 and ex.argument_repair.state.repeated == 1


async def test_escape_never_returns_outside_candidates_or_retry_authority(tmp_path):
    ex = setup(tmp_path)
    result = await invoke(ex, "read_file", {"path": "../secret"}, "escape")
    assert result.error_type == "permission" and not result.error_detail.retryable
    assert result.error_detail.candidates == []


async def test_retry_does_not_convert_uncertain_write_to_replay(tmp_path):
    import pytest

    from mini_harness.security.permissions import Permission, PermissionPolicy
    from mini_harness.session.recovery import RecoveryBlocked
    from mini_harness.session.store import SessionStore

    ex = setup(tmp_path)
    ex.policy = PermissionPolicy({Permission.READ, Permission.WRITE})
    ex.journal = SessionStore(tmp_path / "journal.jsonl")
    args = {"path": "module.py", "old": "absent", "new": "x"}
    failed = await invoke(ex, "edit_file", args, "same")
    assert not failed.ok
    with pytest.raises(RecoveryBlocked, match="In-doubt"):
        await invoke(ex, "edit_file", args, "same")
