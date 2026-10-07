"""Pinned real-source contracts are deterministic, protected and stronger than empty tests."""

import json
from pathlib import Path

import pytest

from mini_harness.agent.result import AgentResult
from mini_harness.agent.stopping import StopReason
from mini_harness.evaluation.behavior import run_behavior_task
from mini_harness.evaluation.fixtures import fixture_for, materialize
from mini_harness.evaluation.real_repository import grade_real, load_real_tasks
from mini_harness.providers.base import Message, ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.result import ExecutionResult

ROOT = Path(__file__).resolve().parents[1]


def tasks():
    if not (ROOT / "work/real-repositories/schedule-v3").exists():
        pytest.skip("Network-fetched pinned repository is optional; fetch to run integration")
    return load_real_tasks(ROOT)


@pytest.mark.parametrize("index", [4, 5, 6])
async def test_seeded_real_defect_fails_contract_then_original_passes(tmp_path, index):
    task = tasks()[index]
    materialize(fixture_for(task, tmp_path), tmp_path / "repo")
    workspace = Workspace(
        tmp_path / "repo", readonly_files=[tmp_path / "repo" / p for p in task.readonly_paths]
    )
    ex = ToolExecutor(
        builtin_registry(workspace),
        PermissionPolicy({Permission.READ, Permission.WRITE, Permission.EXECUTE}),
    )
    bad = await ex.execute(
        ToolCall(id="bad", name="run_tests", arguments={"paths": ["test_contract_v3.py"]}), "bad"
    )
    assert json.loads(bad.content)["exit_code"] == 1
    (workspace.root / task.source_path).write_text(
        task.correct_source, encoding="utf-8", newline="\n"
    )
    good = await ex.execute(
        ToolCall(id="good", name="run_tests", arguments={"paths": ["test_contract_v3.py"]}), "good"
    )
    assert json.loads(good.content)["exit_code"] == 0
    message = Message(
        role="tool", name="run_tests", tool_call_id="good", content=good.model_dump_json()
    )
    result = AgentResult(
        turn_id="t",
        stop_reason=StopReason.FINAL,
        messages=[
            Message(
                role="assistant",
                tool_calls=[
                    ToolCall(
                        id="good", name="run_tests", arguments={"paths": ["test_contract_v3.py"]}
                    )
                ],
            ),
            message,
        ],
    )
    # Canonical outcomes plus independent contract/API grading, not preset model intelligence.
    success, details = await grade_real(task, workspace.root, result)
    assert success and details["signature_preserved"] and details["source_changed"]


async def test_pass_only_generated_tests_are_rejected_by_real_mutant(tmp_path):
    task = tasks()[-1]
    workspace = tmp_path / "repo"
    materialize(fixture_for(task, tmp_path), workspace)
    (workspace / task.generated_test).write_text("def test_empty(): pass\n", encoding="utf-8")
    outcome = ExecutionResult(
        call_id="t", name="run_tests", ok=True, content=json.dumps({"exit_code": 0})
    )
    result = AgentResult(
        turn_id="t",
        stop_reason=StopReason.FINAL,
        messages=[
            Message(
                role="assistant",
                tool_calls=[ToolCall(id="t", name="run_tests", arguments={"paths": ["."]})],
            ),
            Message(
                role="tool", name="run_tests", tool_call_id="t", content=outcome.model_dump_json()
            ),
        ],
    )
    success, details = await grade_real(task, workspace, result)
    assert not success and details["correct_exit"] == 0 and details["mutant_exit"] == 0


async def test_pinned_contract_file_is_readable_but_not_writable(tmp_path):
    task = tasks()[4]
    workspace = tmp_path / "repo"
    materialize(fixture_for(task, tmp_path), workspace)
    guard = Workspace(workspace, readonly_files=[workspace / p for p in task.readonly_paths])
    ex = ToolExecutor(
        builtin_registry(guard, patch=True), PermissionPolicy({Permission.READ, Permission.WRITE})
    )
    read = await ex.execute(
        ToolCall(id="r", name="read_file", arguments={"path": "test_contract_v3.py"}), "r"
    )
    assert read.ok
    write = await ex.execute(
        ToolCall(
            id="w", name="write_file", arguments={"path": "test_contract_v3.py", "content": "pass"}
        ),
        "w",
    )
    assert write.error_type == "permission"


async def test_real_adapter_preserves_contract_scope_and_attribution(tmp_path):
    task = tasks()[0]
    provider = FakeProvider([ModelResponse(content="guessed schedule/__init__.py get_jobs tag")])
    record = await run_behavior_task(task, "FREE_LOOP", "scripted_test", ROOT, tmp_path, provider)
    assert not record["success"] and record["grade"]["required_file_evidence"] is False
    assert record["status"] == "RUN"
    assert task.commit == "82a43db1b938d8fdf60103bd41f329e06c8d3651" and task.license == "MIT"
