"""V3 adapters preserve frozen graders and distinguish host verification from prose."""

from pathlib import Path

from mini_harness.agent.runner import RunnerConfig
from mini_harness.evaluation.behavior import run_behavior_task
from mini_harness.evaluation.tasks import load_tasks
from mini_harness.providers.base import ModelResponse
from mini_harness.providers.fake import FakeProvider

ROOT = Path(__file__).resolve().parents[1]


async def test_frozen_synthetic_grader_rejects_imagined_coding_completion(tmp_path):
    task = next(
        task for task in load_tasks(ROOT / "eval/tasks/v2", "development") if task.kind == "Bug Fix"
    )
    provider = FakeProvider([ModelResponse(content="all tests passed")])
    record = await run_behavior_task(
        task,
        "FREE_LOOP",
        "scripted_test",
        ROOT,
        tmp_path,
        provider,
        config=RunnerConfig(max_iterations=1),
    )
    assert not record["success"] and record["verification_status"] == "UNVERIFIED"
    assert record["behavior_metrics"]["premature_finals"] == 1
    assert record["grade"]["error"] == "missing regression/generated test file"


async def test_observation_rejects_prose_in_same_frozen_task(tmp_path):
    task = next(
        task for task in load_tasks(ROOT / "eval/tasks/v2", "development") if task.kind == "Bug Fix"
    )
    provider = FakeProvider([ModelResponse(content="all tests passed")])
    record = await run_behavior_task(
        task,
        "OBSERVATION_FIRST",
        "scripted_test",
        ROOT,
        tmp_path,
        provider,
        config=RunnerConfig(max_iterations=1),
    )
    assert not record["success"] and record["stop_reason"] == "max_iterations"
    assert record["stats"]["replanning_count"] == 1


async def test_recovery_recipe_still_uses_original_journal(tmp_path):
    task = next(
        task
        for task in load_tasks(ROOT / "eval/tasks/v2", "development")
        if task.kind == "Recovery" and task.case == 1
    )
    record = await run_behavior_task(
        task,
        "FULL_V3",
        "scripted_test",
        ROOT,
        tmp_path,
        FakeProvider([]),
        config=RunnerConfig(max_iterations=2),
    )
    assert record["success"] and record["stop_reason"] == "recovery_blocked"
