"""Observation evidence cannot be fabricated by model prose or failed tools."""

import json

import pytest

from mini_harness.agent.observation import ObservationController, ObservationPolicy
from mini_harness.agent.runner import AgentRunner
from mini_harness.providers.base import Message, ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.session.recovery import RecoveryBlocked
from mini_harness.session.store import SessionStore
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tracing.recorder import TraceRecorder


def calls(*specs):
    return ModelResponse(
        tool_calls=[
            ToolCall(id=f"c{i}", name=name, arguments=args) for i, (name, args) in enumerate(specs)
        ]
    )


def setup(tmp_path, policy=None, grants=None):
    (tmp_path / "unit.py").write_text("def inc(x):\n    return x+2\n", encoding="utf-8")
    workspace = Workspace(tmp_path)
    controller = ObservationController(workspace, policy or ObservationPolicy(coding=True))
    executor = ToolExecutor(
        builtin_registry(workspace),
        PermissionPolicy(grants if grants is not None else {Permission.READ, Permission.WRITE}),
    )
    executor.observation = controller
    return controller, executor


async def test_unread_edit_is_blocked_then_observed_edit_executes(tmp_path):
    controller, executor = setup(tmp_path)
    trace = TraceRecorder(tmp_path / "trace.jsonl")
    provider = FakeProvider(
        [
            calls(("edit_file", {"path": "unit.py", "old": "x+2", "new": "x+1"})),
            calls(
                ("list_dir", {}),
                ("read_file", {"path": "unit.py"}),
                ("edit_file", {"path": "unit.py", "old": "x+2", "new": "x+1"}),
            ),
            ModelResponse(content="done"),
        ]
    )
    result = await AgentRunner(provider, executor, observation=controller, trace=trace).run(
        "Fix increment"
    )
    assert result.stop_reason.value == "final_answer"
    assert result.stats.edits_before_read == 1 and result.stats.replanning_count == 1
    assert "x+1" in (tmp_path / "unit.py").read_text()
    first = json.loads(next(m.content for m in result.messages if m.role == "tool"))
    assert first["error_type"] == "policy" and json.loads(first["content"])["retryable"]
    assert {"policy_violation", "evidence_collected"} <= {e["event"] for e in trace.store.load()}


async def test_noncoding_tasks_do_not_require_workflow(tmp_path):
    controller, executor = setup(tmp_path, ObservationPolicy(coding=False))
    result = await AgentRunner(
        FakeProvider([ModelResponse(content="hello")]), executor, observation=controller
    ).run("Say hello")
    assert result.stop_reason.value == "final_answer" and result.stats.policy_violations == 0


async def test_prose_is_not_source_evidence_and_replans_are_bounded(tmp_path):
    controller, executor = setup(tmp_path, ObservationPolicy(coding=True, max_replans=1))
    provider = FakeProvider([ModelResponse(content="I inspected everything and fixed it")] * 3)
    result = await AgentRunner(provider, executor, observation=controller).run("fix")
    assert result.stop_reason.value == "policy_limit" and len(provider.requests) == 2
    assert result.stats.premature_finals == 2 and not controller.state.read


async def test_a_read_without_location_or_inspection_cannot_edit(tmp_path):
    controller, executor = setup(tmp_path)
    await executor.execute(
        ToolCall(id="read", name="read_file", arguments={"path": "unit.py"}), "r"
    )
    result = await executor.execute(
        ToolCall(
            id="edit", name="edit_file", arguments={"path": "./unit.py", "old": "x+2", "new": "x+1"}
        ),
        "e",
    )
    assert result.error_type == "policy"
    assert "target_located" in json.loads(result.content)["missing_evidence"]


async def test_failed_read_and_permission_do_not_create_evidence(tmp_path):
    controller, executor = setup(tmp_path, grants={Permission.READ})
    bad = await executor.execute(
        ToolCall(id="bad", name="read_file", arguments={"path": "missing.py"}), "b"
    )
    assert not bad.ok and not controller.state.read
    for i, (name, args) in enumerate([("list_dir", {}), ("read_file", {"path": "unit.py"})]):
        await executor.execute(ToolCall(id=str(i), name=name, arguments=args), str(i))
    result = await executor.execute(
        ToolCall(
            id="edit", name="edit_file", arguments={"path": "unit.py", "old": "x+2", "new": "x+1"}
        ),
        "e",
    )
    assert result.error_type == "permission" and "x+2" in (tmp_path / "unit.py").read_text()


async def test_new_file_requires_inspected_parent_and_existing_source(tmp_path):
    controller, executor = setup(tmp_path)
    for i, (name, args) in enumerate([("list_dir", {}), ("read_file", {"path": "unit.py"})]):
        await executor.execute(ToolCall(id=str(i), name=name, arguments=args), str(i))
    result = await executor.execute(
        ToolCall(
            id="new",
            name="write_file",
            arguments={"path": "test_unit.py", "content": "def test_ok(): pass"},
        ),
        "new",
    )
    assert result.ok


async def test_audit_mode_counts_violation_without_enforcing(tmp_path):
    controller, executor = setup(tmp_path, ObservationPolicy(coding=True, enforce=False))
    result = await executor.execute(
        ToolCall(
            id="edit", name="edit_file", arguments={"path": "unit.py", "old": "x+2", "new": "x+1"}
        ),
        "e",
    )
    assert result.ok and controller.state.violations["edit_before_observation"] == 1
    assert controller.state.replanning_count == 0


async def test_resume_cannot_drop_observation_policy(tmp_path):
    controller, executor = setup(tmp_path)
    store = SessionStore(tmp_path / "session.jsonl")
    store.append(
        "turn_started",
        {
            "turn_id": "t",
            "task": "fix",
            "observation": controller.policy.model_dump(),
            "observation_workspace": str(controller.workspace.root),
        },
    )
    store.append(
        "message",
        {**Message(role="user", content="fix").model_dump(), "_turn_id": "t", "_iteration": 0},
    )
    with pytest.raises(RecoveryBlocked, match="Observation policy"):
        await AgentRunner(FakeProvider([]), executor, session=store).resume()


async def test_empty_file_is_not_relevant_source_evidence(tmp_path):
    controller, executor = setup(tmp_path)
    (tmp_path / "empty.py").write_text("")
    await executor.execute(
        ToolCall(id="read", name="read_file", arguments={"path": "empty.py"}), "r"
    )
    assert not controller.state.read
