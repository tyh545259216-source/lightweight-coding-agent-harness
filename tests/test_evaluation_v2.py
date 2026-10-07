import hashlib
import json
from pathlib import Path

import pytest

from mini_harness.agent.result import AgentResult
from mini_harness.agent.stopping import StopReason
from mini_harness.evaluation.evaluator import run_task
from mini_harness.evaluation.fixtures import fixture_for, materialize
from mini_harness.evaluation.graders import grade
from mini_harness.evaluation.tasks import TaskV2, load_tasks

ROOT = Path(__file__).resolve().parents[1]


def test_v2_frozen_counts_and_checksums():
    tasks = load_tasks(ROOT / "eval/tasks/v2")
    assert len(tasks) == 90 and len({t.category for t in tasks}) == 10
    assert len([t for t in tasks if t.split == "development"]) == 50
    assert len([t for t in tasks if t.split == "heldout"]) == 40
    manifest = json.loads((ROOT / "eval/tasks/v2/manifest.json").read_text())
    for name, digest in manifest["hashes"].items():
        assert hashlib.sha256((ROOT / "eval/tasks/v2" / name).read_bytes()).hexdigest() == digest


@pytest.mark.parametrize(
    "category",
    [
        "Code Understanding",
        "File Navigation",
        "Bug Fix",
        "Test Generation",
        "Multi-tool",
        "Tool Failure",
        "Context Stress",
        "Permission / Safety",
        "Recovery",
        "Skills",
    ],
)
async def test_v2_development_reference_pipeline(category, tmp_path):
    task = next(
        t for t in load_tasks(ROOT / "eval/tasks/v2", "development") if t.category == category
    )
    record = await run_task(task, "full", "fake", ROOT, tmp_path)
    assert record["success"], record
    assert record["dataset_version"] == 2


async def test_v2_signature_regression_and_empty_tests_are_rejected(tmp_path):
    task = next(
        t for t in load_tasks(ROOT / "eval/tasks/v2", "development") if t.category == "Bug Fix"
    )
    assert isinstance(task, TaskV2)
    f = fixture_for(task, tmp_path)
    workspace = tmp_path / "repo"
    materialize(f, workspace)
    (workspace / "engine.py").write_text(
        task.correct_source.replace("values, count", "items, count").replace("values[", "items[")
    )
    (workspace / "test_generated.py").write_text("def test_trivial(): assert True")
    (workspace / "pytest.ini").write_text("[pytest]\n")
    success, details = await grade(
        task, f, workspace, AgentResult(turn_id="t", stop_reason=StopReason.FINAL)
    )
    assert not success and details["signature_preserved"] is False


async def test_v2_read_evidence_requires_each_actual_path(tmp_path):
    task = next(
        t
        for t in load_tasks(ROOT / "eval/tasks/v2", "development")
        if t.category == "Code Understanding"
    )
    assert isinstance(task, TaskV2)
    f = fixture_for(task, tmp_path)
    workspace = tmp_path / "repo"
    materialize(f, workspace)
    success, details = await grade(
        task,
        f,
        workspace,
        AgentResult(turn_id="t", stop_reason=StopReason.FINAL, answer=" ".join(task.expected)),
    )
    assert not success and details["required_file_evidence"] is False
