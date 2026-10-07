"""Metadata/chunk navigation preserves bounds, path security and real source coverage."""

import json

import pytest

from mini_harness.agent.observation import ObservationController, ObservationPolicy
from mini_harness.providers.base import ToolCall
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor


def setup(tmp_path):
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "logic.py").write_text(
        "class Counter:\n    pass\n\ndef increment(value):\n    return value+1\n", encoding="utf-8"
    )
    workspace = Workspace(tmp_path)
    return ToolExecutor(builtin_registry(workspace, navigation_v2=True))


async def invoke(executor, name, args):
    return await executor.execute(
        ToolCall(id=name, name=name, arguments=args), name + json.dumps(args)
    )


async def test_map_symbols_and_locations_without_source_dump(tmp_path):
    ex = setup(tmp_path)
    result = await invoke(ex, "repository_map", {})
    data = json.loads(result.content)
    row = data["files"][0]
    assert row["path"] == "nested/logic.py" and row["line_count"] == 5
    assert [x["name"] for x in row["symbols"]] == ["Counter", "increment"]
    assert "return value" not in result.content
    result = await invoke(ex, "symbol_search", {"symbol": "INCREM"})
    match = json.loads(result.content)["matches"][0]
    assert match["start_line"] == 4 and match["end_line"] == 5


async def test_read_chunk_has_explicit_continuation_and_complete_revision(tmp_path):
    ex = setup(tmp_path)
    (tmp_path / "long.py").write_text("value=1\n" * 420, encoding="utf-8")
    one = json.loads((await invoke(ex, "read_file", {"path": "long.py"})).content)
    two = json.loads(
        (await invoke(ex, "read_file", {"path": "long.py", "start_line": 201})).content
    )
    last = json.loads(
        (await invoke(ex, "read_file", {"path": "long.py", "start_line": 401})).content
    )
    assert (one["start_line"], one["end_line"], one["total_lines"], one["has_more"]) == (
        1,
        200,
        420,
        True,
    )
    assert two["sha256"] == one["sha256"] == last["sha256"] and not last["has_more"]
    assert len(last["content"].splitlines()) == 20


@pytest.mark.parametrize(
    "args", [{"start_line": 9}, {"start_line": 3, "end_line": 2}, {"end_line": 12}]
)
async def test_invalid_range_reports_total_and_never_silently_returns_empty(tmp_path, args):
    ex = setup(tmp_path)
    result = await invoke(ex, "read_file", {"path": "nested/logic.py", **args})
    assert not result.ok and "total_lines=5" in result.content


async def test_metadata_scan_bound_excludes_runtime_and_credentials(tmp_path):
    ex = setup(tmp_path)
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "secret.py").write_text("SECRET=1")
    (tmp_path / ".env").write_text("SECRET=2")
    (tmp_path / "x.py").write_text("def another(): pass")
    result = await invoke(ex, "repository_map", {"max_files": 1})
    data = json.loads(result.content)
    assert len(data["files"]) == 1 and data["truncated"]
    result = await invoke(ex, "repository_map", {})
    assert "secret.py" not in result.content and '".env"' not in result.content


async def test_empty_and_invalid_python_files_have_honest_metadata(tmp_path):
    ex = setup(tmp_path)
    (tmp_path / "empty.py").write_text("")
    (tmp_path / "invalid.py").write_text("def :")
    data = json.loads((await invoke(ex, "read_file", {"path": "empty.py"})).content)
    assert data["total_lines"] == 0 and data["content"] == "" and not data["has_more"]
    rows = json.loads((await invoke(ex, "repository_map", {})).content)["files"]
    assert next(x for x in rows if x["path"] == "invalid.py")["symbols"] == []


async def test_partial_read_is_not_complete_edit_evidence(tmp_path):
    ex = setup(tmp_path)
    controller = ObservationController(Workspace(tmp_path), ObservationPolicy(coding=True))
    ex.observation = controller
    await invoke(ex, "repository_map", {})
    await invoke(ex, "read_file", {"path": "nested/logic.py", "end_line": 1})
    denial = controller.before_edit("edit_file", {"path": "nested/logic.py"})
    assert denial and "target_full_source_read" in denial["missing_evidence"]
    await invoke(ex, "read_file", {"path": "nested/logic.py", "start_line": 2})
    assert controller.before_edit("edit_file", {"path": "nested/logic.py"}) is None


@pytest.mark.parametrize(
    "name,args",
    [
        ("repository_map", {"path": "../outside"}),
        ("symbol_search", {"symbol": "inc", "path": "../outside"}),
        ("read_file", {"path": "../outside"}),
    ],
)
async def test_all_navigation_resolves_workspace_paths(tmp_path, name, args):
    ex = setup(tmp_path)
    result = await invoke(ex, name, args)
    assert result.error_type == "permission"


async def test_function_span_can_authorize_only_observed_patch_context(tmp_path):
    ex = setup(tmp_path)
    controller = ObservationController(
        Workspace(tmp_path), ObservationPolicy(coding=True, require_complete_read=False)
    )
    ex.observation = controller
    await invoke(ex, "repository_map", {})
    await invoke(ex, "read_file", {"path": "nested/logic.py", "start_line": 4, "end_line": 5})
    assert (
        controller.before_edit("edit_file", {"path": "nested/logic.py", "old": "return value+1"})
        is None
    )
    missing = controller.before_edit(
        "edit_file", {"path": "nested/logic.py", "old": "class Counter:"}
    )
    assert missing and "edit_context_not_observed" in missing["missing_evidence"]
