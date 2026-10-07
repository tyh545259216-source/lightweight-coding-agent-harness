"""Real pytest outcomes verify repair bounds and permission/recovery invariants."""

import hashlib
import json

import pytest

from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.agent.verification import TestOutcome as Outcome
from mini_harness.agent.verification import VerificationPolicy, VerificationState
from mini_harness.providers.base import Message, ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.session.recovery import RecoveryBlocked
from mini_harness.session.store import SessionStore
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.result import ExecutionResult
from mini_harness.tracing.recorder import TraceRecorder


def patch(content, call_id="patch", path="module.py"):
    return ModelResponse(
        tool_calls=[
            ToolCall(id=call_id, name="write_file", arguments={"path": path, "content": content})
        ]
    )


def setup(tmp_path, grants=None, journal=None):
    (tmp_path / "module.py").write_text("def inc(x): return x+2\n", encoding="utf-8")
    (tmp_path / "test_regression.py").write_text(
        "from module import inc\ndef test_boundary():\n    assert inc(0)==1\n    assert inc(2)==3\n",
        encoding="utf-8",
    )
    (tmp_path / "pytest.ini").write_text("[pytest]\ntestpaths = .\n", encoding="utf-8")
    return ToolExecutor(
        builtin_registry(Workspace(tmp_path)),
        PermissionPolicy(
            grants
            if grants is not None
            else {Permission.READ, Permission.WRITE, Permission.EXECUTE}
        ),
        journal,
    )


async def test_initial_patch_verified_by_real_pytest(tmp_path):
    provider = FakeProvider(
        [patch("def inc(x): return x+1\n"), ModelResponse(content="Verified fix")]
    )
    result = await AgentRunner(
        provider,
        setup(tmp_path),
        verification=VerificationPolicy(test_paths=["test_regression.py"]),
    ).run("Fix inc and verify")
    assert result.stop_reason.value == "final_answer"
    assert result.stats.initial_patch_success is True and result.stats.final_test_success is True
    assert result.stats.repair_rounds == 0 and result.stats.verification_tool_calls == 1
    payload = json.loads(
        json.loads(
            next(m.content for m in result.messages if m.role == "tool" and m.name == "run_tests")
        )["content"]
    )
    assert payload["passed"] is True and payload["exit_code"] == 0


async def test_failed_patch_repair_succeeds_and_trace_records_actual_failures(tmp_path):
    trace = TraceRecorder(tmp_path / "trace.jsonl")
    provider = FakeProvider(
        [
            patch("def inc(x): return x+2\n"),
            patch("def inc(x): return x+1\n", "repair"),
            ModelResponse(content="done"),
        ]
    )
    result = await AgentRunner(
        provider,
        setup(tmp_path),
        verification=VerificationPolicy(test_paths=["test_regression.py"], max_repair_rounds=1),
        trace=trace,
    ).run("Fix inc")
    assert result.stop_reason.value == "final_answer"
    assert result.stats.initial_patch_success is False and result.stats.final_test_success is True
    assert result.stats.repair_rounds == 1 and result.stats.verification_tool_calls == 2
    outcomes = [
        e["data"]["data"]["outcome"]
        for e in trace.store.load()
        if e["event"] == "verification_result"
    ]
    assert [o["exit_code"] for o in outcomes] == [1, 0]
    assert any(e["event"] == "repair_requested" for e in trace.store.load())


async def test_max_repair_rounds_stops_before_extra_patch(tmp_path):
    provider = FakeProvider(
        [
            patch("def inc(x): return x+2\n"),
            patch("def inc(x): return x+3\n", "badrepair"),
            patch("def inc(x): return x+1\n", "unreachable"),
        ]
    )
    result = await AgentRunner(
        provider,
        setup(tmp_path),
        verification=VerificationPolicy(test_paths=["test_regression.py"], max_repair_rounds=1),
    ).run("Fix inc")
    assert result.stop_reason.value == "max_repair_rounds" and len(provider.requests) == 2
    assert result.stats.repair_rounds == 1 and result.stats.final_test_success is False
    assert "x+3" in (tmp_path / "module.py").read_text(encoding="utf-8")


async def test_no_test_collection_is_failure_then_test_repair(tmp_path):
    provider = FakeProvider(
        [
            patch("", path="test_generated.py"),
            patch(
                "from module import inc\ndef test_api(): assert inc(0)==2\n",
                "repair",
                "test_generated.py",
            ),
            ModelResponse(content="done"),
        ]
    )
    result = await AgentRunner(
        provider,
        setup(tmp_path),
        verification=VerificationPolicy(test_paths=["test_generated.py"], max_repair_rounds=1),
    ).run("Generate executable tests")
    outcomes = [
        json.loads(json.loads(m.content)["content"])
        for m in result.messages
        if m.role == "tool" and m.name == "run_tests"
    ]
    assert [o["kind"] for o in outcomes] == ["no_tests", "passed"]
    assert result.stats.initial_patch_success is False and result.stats.final_test_success is True


async def test_verification_never_grants_execute(tmp_path):
    provider = FakeProvider(
        [patch("def inc(x): return x+1\n"), ModelResponse(content="unreachable")]
    )
    result = await AgentRunner(
        provider, setup(tmp_path, {Permission.WRITE}), verification=VerificationPolicy()
    ).run("Fix inc")
    assert result.stop_reason.value == "verification_failed" and len(provider.requests) == 1
    assert result.stats.permission_denials == 1 and result.stats.final_test_success is False


async def test_unapproved_outside_patch_is_never_overwritten(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("SAFE", encoding="utf-8")
    provider = FakeProvider([patch("bad", path="../outside.txt"), ModelResponse(content="done")])
    result = await AgentRunner(
        provider, setup(repo), RunnerConfig(max_iterations=2), verification=VerificationPolicy()
    ).run("No outside edits")
    assert outside.read_text(encoding="utf-8") == "SAFE" and result.stats.permission_denials == 1
    assert result.stop_reason.value != "final_answer"


def test_structured_failure_truncation_keeps_failure_tail():
    result = ExecutionResult(
        call_id="t",
        name="run_tests",
        ok=True,
        content=json.dumps(
            {"exit_code": 1, "stdout": "START" + "x" * 1000 + "FAIL_END", "stderr": ""}
        ),
    )
    outcome = Outcome.from_result(result, 256)
    assert outcome.passed is False and outcome.truncated and len(outcome.stdout) <= 256
    assert outcome.stdout.startswith("START") and outcome.stdout.endswith("FAIL_END")


def test_malformed_test_result_cannot_claim_success():
    result = ExecutionResult(call_id="t", name="run_tests", ok=True, content='{"exit_code":true}')
    assert Outcome.from_result(result, 256).kind == "tool_error"


async def test_saved_rejected_final_cannot_bypass_verification_on_resume(tmp_path):
    store = SessionStore(tmp_path / "session.jsonl")
    policy = VerificationPolicy()
    store.append(
        "turn_started",
        {
            "turn_id": "turn",
            "task": "fix",
            "config": {"max_iterations": 2},
            "verification": policy.model_dump(),
        },
    )
    store.append(
        "message",
        {**Message(role="user", content="fix").model_dump(), "_turn_id": "turn", "_iteration": 0},
    )
    store.append("model_requested", {"iteration": 0})
    store.append(
        "message",
        {
            **Message(role="assistant", content="imagined tests passed").model_dump(),
            "_iteration": 0,
        },
    )
    store.append(
        "verification_state", {"turn_id": "turn", "state": VerificationState().model_dump()}
    )
    result = await AgentRunner(
        FakeProvider([ModelResponse(content="another plan")]), session=store
    ).resume()
    assert (
        result.stop_reason.value != "final_answer" and result.stats.final_test_success is not True
    )


async def test_resume_refuses_changed_verification_policy(tmp_path):
    store = SessionStore(tmp_path / "session.jsonl")
    store.append(
        "turn_started",
        {
            "turn_id": "turn",
            "task": "fix",
            "verification": VerificationPolicy(max_repair_rounds=1).model_dump(),
        },
    )
    with pytest.raises(RecoveryBlocked, match="Verification policy changed"):
        await AgentRunner(
            FakeProvider([]), session=store, verification=VerificationPolicy(max_repair_rounds=2)
        ).resume()


async def test_new_edit_invalidates_previous_passing_revision(tmp_path):
    provider = FakeProvider(
        [
            patch("def inc(x): return x+1\n"),
            patch("def inc(x): return x+4\n", "regression"),
            ModelResponse(content="unreachable stale success"),
        ]
    )
    result = await AgentRunner(
        provider,
        setup(tmp_path),
        verification=VerificationPolicy(test_paths=["test_regression.py"], max_repair_rounds=0),
    ).run("Fix inc")
    assert result.stats.initial_patch_success is True and result.stats.final_test_success is False
    assert result.stop_reason.value == "max_repair_rounds" and len(provider.requests) == 2


async def test_resume_cached_verification_never_reexecutes_test_effect(tmp_path):
    from mini_harness.tools.base import BaseTool
    from mini_harness.tools.builtin.shell import TestInput
    from mini_harness.tools.registry import ToolRegistry

    class NeverRun(BaseTool[TestInput]):
        name, description, input_model = "run_tests", "cached test must not execute", TestInput
        permission, side_effect = Permission.EXECUTE, True

        async def execute(self, arguments):
            raise AssertionError("cached verification was rerun")

    store = SessionStore(tmp_path / "session.jsonl")
    policy = VerificationPolicy(test_paths=["test_regression.py"])
    call = ToolCall(id="harness_verify_1", name="run_tests", arguments={"paths": policy.test_paths})
    key = "turn:0:harness_verify_1"
    store.append(
        "turn_started",
        {
            "turn_id": "turn",
            "task": "fix",
            "config": {"max_iterations": 3},
            "verification": policy.model_dump(),
        },
    )
    store.append(
        "message",
        {**Message(role="user", content="fix").model_dump(), "_turn_id": "turn", "_iteration": 0},
    )
    store.append("model_requested", {"iteration": 0})
    store.append(
        "message",
        {
            **Message(
                role="assistant", name="harness_verification", tool_calls=[call]
            ).model_dump(),
            "_iteration": 0,
        },
    )
    fingerprint = hashlib.sha256(
        json.dumps(
            {"name": call.name, "args": call.arguments}, sort_keys=True, ensure_ascii=False
        ).encode()
    ).hexdigest()
    result = ExecutionResult(
        call_id=call.id,
        name=call.name,
        ok=True,
        content=json.dumps({"exit_code": 0, "stdout": "passed", "stderr": ""}),
    )
    store.append(
        "execution_completed",
        {"key": key, "fingerprint": fingerprint, "result": result.model_dump()},
    )
    state = VerificationState(
        revision=1,
        tested_revision=1,
        initial_patch_success=True,
        final_test_success=True,
        last_outcome=Outcome(passed=True, exit_code=0, kind="passed"),
        observed_keys=[key],
    )
    store.append("verification_state", {"turn_id": "turn", "state": state.model_dump()})
    registry = ToolRegistry()
    registry.register(NeverRun())
    executor = ToolExecutor(registry, PermissionPolicy({Permission.EXECUTE}), store)
    resumed = await AgentRunner(
        FakeProvider([ModelResponse(content="verified")]), executor, session=store
    ).resume()
    assert resumed.stop_reason.value == "final_answer" and resumed.stats.final_test_success is True
    assert resumed.stats.verification_tool_calls == 1
    tool = json.loads(next(m.content for m in resumed.messages if m.role == "tool"))
    assert tool["replayed"] is True
