from pathlib import Path

import pytest

from mini_harness.agent.result import AgentResult
from mini_harness.agent.runner import AgentRunner
from mini_harness.agent.stopping import StopReason
from mini_harness.evaluation.evaluator import evaluate, run_task
from mini_harness.evaluation.fixtures import fixture_for, materialize
from mini_harness.evaluation.graders import grade
from mini_harness.evaluation.tasks import Task, load_tasks
from mini_harness.providers.base import ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tracing.recorder import TraceRecorder

ROOT = Path(__file__).resolve().parents[1]


def test_frozen_suite():
    tasks = load_tasks(ROOT / "eval/tasks")
    assert len(tasks) == 54 and len(load_tasks(ROOT / "eval/tasks", "heldout")) == 18
    assert len({t.category for t in tasks}) == 9


@pytest.mark.parametrize(
    "category",
    [
        "Code Understanding",
        "File Search",
        "Bug Fix",
        "Test Generation",
        "Multi-tool",
        "Tool Failure",
        "Context Stress",
        "Permission / Safety",
        "Recovery",
    ],
)
async def test_scripted_fixture(category, tmp_path):
    task = next(
        t for t in load_tasks(ROOT / "eval/tasks") if t.category == category and t.case == 0
    )
    record = await run_task(task, "full", "fake", ROOT, tmp_path)
    assert record["success"], record


async def test_trace_layers_and_latency(tmp_path):
    (tmp_path / "app.py").write_text("code", encoding="utf-8")
    trace = TraceRecorder(tmp_path / "trace.jsonl")
    provider = FakeProvider(
        [
            ModelResponse(tool_calls=[ToolCall(id="bad", name="read_file", arguments={"path": 3})]),
            ModelResponse(content="done"),
        ]
    )
    await AgentRunner(
        provider, ToolExecutor(builtin_registry(Workspace(tmp_path))), trace=trace
    ).run("task")
    events = trace.store.load()
    assert {"model_requested", "model_received", "tool_requested", "tool_result", "terminal"} <= {
        e["event"] for e in events
    }
    tool_result = next(e for e in events if e["event"] == "tool_result")["data"]
    assert tool_result["layer"] == "tool_arguments" and tool_result["data"]["latency_seconds"] >= 0
    assert events[-1]["data"]["data"]["stop_reason"] == "final_answer"


async def test_weak_tests_rejected(tmp_path):
    task = Task(
        id="weak",
        category="Test Generation",
        case=0,
        split="development",
        description="grader integrity",
    )
    f = fixture_for(task, tmp_path)
    workspace = tmp_path / "repo"
    materialize(f, workspace)
    (workspace / "test_generated.py").write_text(
        "def test_trivial(): assert True", encoding="utf-8"
    )
    success, details = await grade(
        task, f, workspace, AgentResult(turn_id="t", stop_reason=StopReason.FINAL)
    )
    assert not success and details["correct_exit"] == 0 and details["mutant_exit"] == 0


async def test_disabled_recovery_explicit(tmp_path):
    task = next(t for t in load_tasks(ROOT / "eval/tasks") if t.category == "Recovery")
    record = await run_task(task, "baseline", "fake", ROOT, tmp_path)
    assert record["status"] == "UNSUPPORTED" and not record["success"]


async def test_not_run_metrics_and_manifest(tmp_path):
    tasks = load_tasks(ROOT / "eval/tasks")[:1]
    summary = await evaluate(
        ROOT, tmp_path / "not-run", tasks, ["full"], "ollama", not_run_reason="offline"
    )
    assert summary["full"]["all"]["task_success_rate"] is None
    assert summary["full"]["all"]["prompt_tokens"] is None
    assert (tmp_path / "not-run/manifest.json").is_file()


async def test_relative_output_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    task = next(t for t in load_tasks(ROOT / "eval/tasks") if t.category == "Test Generation")
    record = await run_task(task, "full", "fake", ROOT, Path("relative-output"))
    assert record["success"], record


def test_unsupported_tasks_do_not_invent_zero_latency():
    from mini_harness.agent.state import AgentStats
    from mini_harness.evaluation.metrics import aggregate

    actual = {
        "status": "RUN",
        "category": "Bug Fix",
        "success": True,
        "unsafe_action": False,
        "stats": AgentStats(latency_seconds=2, model_rounds=3).model_dump(),
    }
    unsupported = {
        "status": "UNSUPPORTED",
        "category": "Recovery",
        "success": False,
        "unsafe_action": False,
        "stats": AgentStats().model_dump(),
    }
    summary = aggregate([actual, unsupported])
    assert summary["task_success_rate"] == 0.5
    assert summary["mean_agent_latency_seconds"] == 2 and summary["mean_model_rounds"] == 3
    assert summary["executed"] == 1 and summary["evaluated"] == 2
