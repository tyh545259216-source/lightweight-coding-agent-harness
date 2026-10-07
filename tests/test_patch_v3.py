"""Patch preconditions/preview preserve files, API neutrality, guards and verification revision."""

import hashlib
import json

import pytest

from mini_harness.agent.verification import VerificationController, VerificationPolicy
from mini_harness.providers.base import ToolCall
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor


def setup(tmp_path):
    source = "def inc(x):\n    return x+2\n"
    (tmp_path / "unit.py").write_text(source, encoding="utf-8")
    ex = ToolExecutor(
        builtin_registry(Workspace(tmp_path), patch=True),
        PermissionPolicy({Permission.READ, Permission.WRITE}),
    )
    args = {
        "path": "unit.py",
        "expected_sha256": hashlib.sha256((tmp_path / "unit.py").read_bytes()).hexdigest(),
        "old": "return x+2",
        "new": "return x+1",
    }
    return ex, args


async def invoke(ex, args, key="p"):
    call = ToolCall(id=key, name="apply_patch", arguments=args)
    return call, await ex.execute(call, key)


async def test_patch_reports_actual_diff_and_new_revision(tmp_path):
    ex, args = setup(tmp_path)
    call, result = await invoke(ex, args)
    data = json.loads(result.content)
    assert result.ok and data["changed"] and data["changed_line_count"] == 2
    assert "-    return x+2" in data["diff"] and "+    return x+1" in data["diff"]
    assert data["sha256"] == hashlib.sha256((tmp_path / "unit.py").read_bytes()).hexdigest()
    controller = VerificationController(VerificationPolicy())
    controller.observe(call, "p", result)
    assert controller.dirty and controller.state.revision == 1


async def test_preview_never_changes_source_or_marks_verification_dirty(tmp_path):
    ex, args = setup(tmp_path)
    call, result = await invoke(ex, {**args, "preview_only": True})
    data = json.loads(result.content)
    assert not data["changed"] and data["sha256"] == args["expected_sha256"]
    assert "x+2" in (tmp_path / "unit.py").read_text()
    controller = VerificationController(VerificationPolicy())
    controller.observe(call, "p", result)
    assert not controller.dirty and controller.state.revision == 0


@pytest.mark.parametrize(
    "change,kind",
    [
        ({"expected_sha256": "0" * 64}, "stale_revision"),
        ({"old": "absent"}, "context_mismatch"),
        ({"new": "return x+2"}, "no_op"),
    ],
)
async def test_invalid_patch_preserves_original_bytes(tmp_path, change, kind):
    ex, args = setup(tmp_path)
    original = (tmp_path / "unit.py").read_bytes()
    _, result = await invoke(ex, {**args, **change})
    assert not result.ok and result.error_detail.error_type == kind
    assert (tmp_path / "unit.py").read_bytes() == original


async def test_stale_read_after_external_change_is_rejected(tmp_path):
    ex, args = setup(tmp_path)
    (tmp_path / "unit.py").write_text("external=1\n", encoding="utf-8")
    _, result = await invoke(ex, args)
    assert result.error_detail.error_type == "stale_revision"
    assert (tmp_path / "unit.py").read_text() == "external=1\n"


async def test_patch_workspace_escape_and_read_only_grant(tmp_path):
    ex, args = setup(tmp_path)
    _, escape = await invoke(ex, {**args, "path": "../unit.py"})
    assert escape.error_type == "permission"
    ex.policy = PermissionPolicy()
    _, denial = await invoke(ex, args, "deny")
    assert denial.error_type == "permission"


async def test_api_change_is_not_hardcoded_in_editor(tmp_path):
    ex, args = setup(tmp_path)
    _, result = await invoke(ex, {**args, "old": "inc(x)", "new": "inc(value)"})
    assert result.ok
    # Task-specific API verification, not an editor name blacklist, must reject this.


async def test_crlf_read_hash_is_valid_patch_precondition(tmp_path):
    ex, args = setup(tmp_path)
    (tmp_path / "unit.py").write_bytes(b"def inc(x):\r\n    return x+2\r\n")
    args["expected_sha256"] = hashlib.sha256((tmp_path / "unit.py").read_bytes()).hexdigest()
    _, result = await invoke(ex, args)
    assert result.ok and b"return x+1\r\n" in (tmp_path / "unit.py").read_bytes()
