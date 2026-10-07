import hashlib
import json
import os

import pytest

from mini_harness.agent.runner import AgentRunner
from mini_harness.providers.base import Message, ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace, WorkspaceViolation
from mini_harness.session.recovery import RecoveryBlocked
from mini_harness.session.store import SessionBusyError, SessionStore
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor


@pytest.mark.parametrize(
    "path",
    ["../outside", "a/../../x", r"..\escape", ".git/config", ".sessions/state", "C:relative", ""],
)
def test_workspace_denial(tmp_path, path):
    with pytest.raises(WorkspaceViolation):
        Workspace(tmp_path).resolve(path)


def test_absolute_scope(tmp_path):
    w = Workspace(tmp_path)
    assert w.resolve(str(tmp_path / "safe")) == tmp_path / "safe"
    with pytest.raises(WorkspaceViolation):
        w.resolve(str(tmp_path.parent / "outside"))


def test_symlink_escape(tmp_path):
    outside = tmp_path.parent / "outside"
    outside.mkdir(exist_ok=True)
    link = tmp_path / "link"
    try:
        link.symlink_to(outside, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            pytest.skip("OS denied symlink creation")
        import subprocess

        result = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(link), str(outside)], capture_output=True
        )
        if result.returncode:
            pytest.skip("OS denied both symlink and junction creation")
    with pytest.raises(WorkspaceViolation):
        Workspace(tmp_path).resolve("link/secret")


async def test_permission_approval():
    requests = []

    async def approve(name, level, args):
        requests.append((name, level, args))
        return name == "allowed"

    p = PermissionPolicy(approval=approve)
    await p.check("allowed", Permission.DANGEROUS, {"x": 1})
    with pytest.raises(PermissionError):
        await p.check("denied", Permission.EXECUTE, {})
    assert len(requests) == 2


def setup(tmp_path):
    s = SessionStore(tmp_path / "journal.jsonl")
    e = ToolExecutor(
        builtin_registry(Workspace(tmp_path)),
        PermissionPolicy({Permission.READ, Permission.WRITE}),
        s,
    )
    return s, e


async def test_cached_side_effect(tmp_path):
    s, e = setup(tmp_path)
    c = ToolCall(id="w", name="write_file", arguments={"path": "code.py", "content": "v1"})
    assert (await e.execute(c, "key")).ok
    (tmp_path / "code.py").write_text("changed", encoding="utf-8")
    r = await e.execute(c, "key")
    assert r.replayed and (tmp_path / "code.py").read_text(encoding="utf-8") == "changed"
    with pytest.raises(RecoveryBlocked):
        await e.execute(
            c.model_copy(update={"arguments": {"path": "code.py", "content": "v2"}}), "key"
        )


async def test_in_doubt_never_replayed(tmp_path):
    s, e = setup(tmp_path)
    c = ToolCall(id="w", name="write_file", arguments={"path": "code.py", "content": "v1"})
    fingerprint = hashlib.sha256(
        json.dumps(
            {"name": c.name, "args": c.arguments}, sort_keys=True, ensure_ascii=False
        ).encode()
    ).hexdigest()
    s.append("execution_started", {"key": "key", "fingerprint": fingerprint, "side_effect": True})
    with pytest.raises(RecoveryBlocked):
        await e.execute(c, "key")
    assert not (tmp_path / "code.py").exists()


async def test_read_retry_is_safe(tmp_path):
    s, e = setup(tmp_path)
    c = ToolCall(id="r", name="read_file", arguments={"path": "code.py"})
    fp = hashlib.sha256(
        json.dumps(
            {"name": c.name, "args": c.arguments}, sort_keys=True, ensure_ascii=False
        ).encode()
    ).hexdigest()
    s.append("execution_started", {"key": "key", "fingerprint": fp, "side_effect": False})
    (tmp_path / "code.py").write_text("safe", encoding="utf-8")
    assert (await e.execute(c, "key")).content == "safe"


def persist_pending(s, call):
    s.append("message", Message(role="system", content="system").model_dump())
    s.append("turn_started", {"turn_id": "turn", "task": "fix"})
    s.append(
        "message",
        {**Message(role="user", content="fix").model_dump(), "_turn_id": "turn", "_iteration": 0},
    )
    s.append("model_requested", {"iteration": 0})
    s.append(
        "message",
        {
            **Message(role="assistant", tool_calls=[call]).model_dump(),
            "_turn_id": "turn",
            "_iteration": 0,
        },
    )


async def test_crash_after_effect_before_conversation(tmp_path):
    s, e = setup(tmp_path)
    c = ToolCall(id="w", name="write_file", arguments={"path": "code.py", "content": "v1"})
    persist_pending(s, c)
    await e.execute(c, "turn:0:w")
    (tmp_path / "code.py").write_text("preserved", encoding="utf-8")
    r = await AgentRunner(FakeProvider([ModelResponse(content="done")]), e, session=s).resume()
    assert r.answer == "done" and r.stats.tool_calls == 1
    assert (tmp_path / "code.py").read_text(encoding="utf-8") == "preserved"
    assert json.loads(r.messages[-2].content)["replayed"]


async def test_crash_before_tool_can_resume(tmp_path):
    s, e = setup(tmp_path)
    persist_pending(
        s, ToolCall(id="w", name="write_file", arguments={"path": "code.py", "content": "v1"})
    )
    r = await AgentRunner(FakeProvider([ModelResponse(content="done")]), e, session=s).resume()
    assert r.answer == "done" and (tmp_path / "code.py").exists()


async def test_uncertain_recovery_stops(tmp_path):
    s, e = setup(tmp_path)
    c = ToolCall(id="w", name="write_file", arguments={"path": "code.py", "content": "v1"})
    persist_pending(s, c)
    fp = hashlib.sha256(
        json.dumps(
            {"name": c.name, "args": c.arguments}, sort_keys=True, ensure_ascii=False
        ).encode()
    ).hexdigest()
    s.append("execution_started", {"key": "turn:0:w", "fingerprint": fp, "side_effect": True})
    p = FakeProvider([])
    r = await AgentRunner(p, e, session=s).resume()
    assert r.stop_reason.value == "recovery_blocked" and not p.requests


async def test_new_task_rejects_unfinished(tmp_path):
    s, e = setup(tmp_path)
    persist_pending(s, ToolCall(id="r", name="list_dir"))
    with pytest.raises(RecoveryBlocked):
        await AgentRunner(FakeProvider([]), e, session=s).run("new")


def test_single_writer_lock(tmp_path):
    a = SessionStore(tmp_path / "s")
    b = SessionStore(tmp_path / "s")
    with a.lease():
        with pytest.raises(SessionBusyError):
            with b.lease():
                pass
    with b.lease():
        pass


def test_configured_journal_and_lock_are_protected(tmp_path):
    journal = tmp_path / "custom-journal.jsonl"
    workspace = Workspace(tmp_path, protected_files=[journal])
    with pytest.raises(WorkspaceViolation):
        workspace.resolve("custom-journal.jsonl")
    with pytest.raises(WorkspaceViolation):
        workspace.resolve("custom-journal.jsonl.lock")
    assert workspace.resolve("ordinary.py") == tmp_path / "ordinary.py"


async def test_partial_effect_then_permission_error_is_uncertain(tmp_path):
    from mini_harness.tools.base import BaseTool, InputModel

    class PartialEffect(BaseTool[InputModel]):
        name, description, input_model = "partial", "Partial write then failure", InputModel
        permission, side_effect = Permission.WRITE, True

        async def execute(self, arguments):
            (tmp_path / "partial.txt").write_text("1", encoding="utf-8")
            raise PermissionError("failed after partial mutation")

    s, e = setup(tmp_path)
    e.registry.register(PartialEffect())
    call = ToolCall(id="p", name="partial")
    result = await e.execute(call, "partial-key")
    assert result.error_type == "permission"
    assert s.load()[-1]["event"] == "execution_uncertain"
    (tmp_path / "partial.txt").write_text("human change", encoding="utf-8")
    with pytest.raises(RecoveryBlocked):
        await e.execute(call, "partial-key")
    assert (tmp_path / "partial.txt").read_text(encoding="utf-8") == "human change"
