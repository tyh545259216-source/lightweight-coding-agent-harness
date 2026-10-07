"""Completion requires actual changed targets, current canonical tests and host checks."""

import ast

import pytest

from mini_harness.agent.completion import (
    CompletionController,
    CompletionPolicy,
    IndependentCheck,
    IndependentOutcome,
)
from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.agent.verification import VerificationPolicy
from mini_harness.providers.base import ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.session.recovery import RecoveryBlocked
from mini_harness.session.store import SessionStore
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor


def patch(text, key="edit"):
    return ModelResponse(
        tool_calls=[
            ToolCall(id=key, name="write_file", arguments={"path": "unit.py", "content": text})
        ]
    )


def setup(tmp_path, independent=False, grants=None):
    (tmp_path / "unit.py").write_text("def inc(x): return x+2\n", encoding="utf-8")
    (tmp_path / "test_unit.py").write_text(
        "from unit import inc\ndef test_value(): assert inc(0)==1\n", encoding="utf-8"
    )
    (tmp_path / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    workspace = Workspace(tmp_path)
    registry = builtin_registry(workspace)
    checks = []
    if independent:

        async def check():
            checks.append("observed")
            node = ast.parse((tmp_path / "unit.py").read_text()).body[0]
            return IndependentOutcome(
                passed=[a.arg for a in node.args.args] == ["x"],
                summary="Public API parameter contract checked independently.",
            )

        registry.register(IndependentCheck(check))
    executor = ToolExecutor(
        registry,
        PermissionPolicy(
            grants
            if grants is not None
            else {Permission.READ, Permission.WRITE, Permission.EXECUTE}
        ),
    )
    gate = CompletionController(
        workspace, CompletionPolicy(targets=["unit.py"], require_independent=independent)
    )
    return executor, gate, checks


async def test_current_actual_change_and_real_tests_allow_verified_success(tmp_path):
    ex, gate, checks = setup(tmp_path, True)
    result = await AgentRunner(
        FakeProvider([patch("def inc(x): return x+1\n"), ModelResponse(content="done")]),
        ex,
        verification=VerificationPolicy(),
        completion=gate,
    ).run("fix")
    assert (
        result.verification_status.value == "VERIFIED_SUCCESS"
        and result.stop_reason.value == "final_answer"
    )
    assert checks == ["observed"] and result.stats.verification_tool_calls == 2
    assert "independent_check" not in [d.name for d in ex.definitions()]


async def test_model_cannot_invoke_host_independent_checker(tmp_path):
    ex, gate, checks = setup(tmp_path, True)
    result = await ex.execute(ToolCall(id="fake", name="independent_check", arguments={}), "fake")
    assert result.error_type == "permission" and checks == []


async def test_noop_rewrite_with_passing_tests_is_unverified(tmp_path):
    ex, gate, _ = setup(tmp_path)
    # Existing target is already correct; a rewrite of identical normalized text cannot prove a fix.
    (tmp_path / "test_unit.py").write_text(
        "from unit import inc\ndef test_value(): assert inc(0)==2\n", encoding="utf-8"
    )
    provider = FakeProvider([patch("def inc(x): return x+2\n"), ModelResponse(content="done")])
    result = await AgentRunner(
        provider,
        ex,
        RunnerConfig(max_iterations=2),
        verification=VerificationPolicy(),
        completion=gate,
    ).run("fix")
    assert (
        result.stats.final_test_success is True and result.verification_status.value == "UNVERIFIED"
    )
    assert result.stop_reason.value != "final_answer" and gate.state.rejected_finals == 1


async def test_api_failure_cannot_be_overridden_by_passing_visible_tests(tmp_path):
    ex, gate, checks = setup(tmp_path, True)
    result = await AgentRunner(
        FakeProvider([patch("def inc(value): return value+1\n"), ModelResponse(content="done")]),
        ex,
        verification=VerificationPolicy(max_repair_rounds=0),
        completion=gate,
    ).run("fix")
    assert result.stats.final_test_success is True
    assert (
        result.verification_status.value == "VERIFIED_FAILURE"
        and result.stop_reason.value == "max_repair_rounds"
    )
    assert checks == ["observed"]


async def test_independent_failure_allows_bounded_actual_repair(tmp_path):
    ex, gate, checks = setup(tmp_path, True)
    result = await AgentRunner(
        FakeProvider(
            [
                patch("def inc(value): return value+1\n"),
                patch("def inc(x): return x+1\n", "repair"),
                ModelResponse(content="done"),
            ]
        ),
        ex,
        verification=VerificationPolicy(max_repair_rounds=1),
        completion=gate,
    ).run("fix")
    assert (
        result.verification_status.value == "VERIFIED_SUCCESS" and result.stats.repair_rounds == 1
    )
    assert checks == ["observed", "observed"]


async def test_independent_check_never_grants_execute(tmp_path):
    ex, gate, checks = setup(tmp_path, True, grants={Permission.READ, Permission.WRITE})
    result = await AgentRunner(
        FakeProvider([patch("def inc(x): return x+1\n")]),
        ex,
        verification=VerificationPolicy(),
        completion=gate,
    ).run("fix")
    assert (
        result.stop_reason.value == "verification_failed"
        and result.verification_status.value == "VERIFIED_FAILURE"
    )
    assert not checks


async def test_external_target_change_invalidates_test_snapshot(tmp_path):
    ex, gate, _ = setup(tmp_path)
    gate.state.canonical_passed = True
    gate.state.tested_hashes = gate.hashes()
    (tmp_path / "unit.py").write_text("def inc(x): return x+1\n", encoding="utf-8")
    status, missing = gate.evaluate()
    assert status.value == "UNVERIFIED" and "observed_current_canonical_pass" in missing


async def test_saved_gate_cannot_be_removed_on_resume(tmp_path):
    ex, gate, _ = setup(tmp_path)
    store = SessionStore(tmp_path / "session.jsonl")
    store.append(
        "turn_started",
        {
            "turn_id": "t",
            "task": "fix",
            "completion": gate.policy.model_dump(),
            "completion_workspace": str(gate.workspace.root),
            "completion_initial": gate.state.model_dump(),
        },
    )
    with pytest.raises(RecoveryBlocked, match="Completion policy"):
        await AgentRunner(FakeProvider([]), ex, session=store).resume()


def test_empty_target_policy_and_missing_canonical_policy_rejected(tmp_path):
    ex, gate, _ = setup(tmp_path)
    with pytest.raises(ValueError):
        CompletionPolicy(targets=[])
    with pytest.raises(ValueError, match="canonical"):
        AgentRunner(FakeProvider([]), ex, completion=gate)


async def test_canonical_pytest_reads_new_bytes_despite_same_size_and_mtime(tmp_path):
    import json
    import os

    ex, gate, _ = setup(tmp_path)
    source = tmp_path / "unit.py"
    fixed = 1700000000000000000
    source.write_bytes(b"def inc(x): return x+1\n")
    os.utime(source, ns=(fixed, fixed))
    one = await ex.execute(ToolCall(id="t1", name="run_tests", arguments={"paths": ["."]}), "t1")
    assert json.loads(one.content)["exit_code"] == 0
    source.write_bytes(b"def inc(x): return x+4\n")
    os.utime(source, ns=(fixed, fixed))
    two = await ex.execute(ToolCall(id="t2", name="run_tests", arguments={"paths": ["."]}), "t2")
    assert json.loads(two.content)["exit_code"] == 1


async def test_host_checker_receives_only_completed_message_pairs(tmp_path):
    from mini_harness.context.manager import message_groups

    ex, gate, _ = setup(tmp_path)
    gate.policy.require_independent = True
    snapshots = []

    async def check():
        groups = message_groups(gate.candidate_messages)
        snapshots.append((len(groups), len(gate.candidate_messages)))
        assert not any(m.name == "harness_independent" for m in gate.candidate_messages)
        return IndependentOutcome(passed=True, summary="Completed evidence checked.")

    ex.registry.register(IndependentCheck(check))
    result = await AgentRunner(
        FakeProvider([patch("def inc(x): return x+1\n"), ModelResponse(content="done")]),
        ex,
        verification=VerificationPolicy(),
        completion=gate,
    ).run("fix")
    assert result.verification_status.value == "VERIFIED_SUCCESS"
    assert snapshots
    assert len(gate.candidate_messages) == snapshots[0][1]
