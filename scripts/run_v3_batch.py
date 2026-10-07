"""Bounded execution of frozen protocols; durable per-case records, no replay."""

import argparse
import asyncio
import hashlib
import json
import os
from pathlib import Path

from v3_observed_provider import ObservedProvider, durable_jsonl, utc

from mini_harness.agent.runner import RunnerConfig
from mini_harness.evaluation.behavior import run_behavior_task
from mini_harness.evaluation.real_repository import load_real_tasks
from mini_harness.evaluation.tasks import load_tasks

ROOT = Path(__file__).resolve().parents[1]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".pending")
    with tmp.open("w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp, path)


async def execute(args):
    path = ROOT / "eval/protocol_v3.json"
    protocol = json.loads(path.read_text(encoding="utf-8"))
    for name, digest in protocol["hashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Frozen input changed: " + name)
    diagnostic = args.group == "diagnostic"
    batch_size = min(args.batch_size, 2) if diagnostic else args.batch_size
    if args.model == "qwen3:4b" and not diagnostic:
        raise RuntimeError("QWEN3_4B_FIXED_BUDGET: DEPLOYMENT-INFEASIBLE UNDER CURRENT CPU BUDGET")
    if diagnostic:
        spec = json.loads((ROOT / "eval/protocol_v3_diagnostic.json").read_text())
        assert spec["parent_protocol_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        ids, variants, repeats, config = spec["task_ids"], [spec["variant"]], 1, spec["runner"]
    else:
        spec = protocol["groups"][args.group]
        ids, variants, repeats, config = (
            spec["ids"],
            spec["variants"],
            spec["repeats"],
            protocol["runner"],
        )
    tasks = {t.id: t for t in load_tasks(ROOT / "eval/tasks/v2") + load_real_tasks(ROOT)}
    output = ROOT / "eval/results/v3-batched" / args.model.replace(":", "-") / args.group
    output.mkdir(parents=True, exist_ok=True)
    old = ROOT / "eval/results/v3" / args.model.replace(":", "-") / args.group / "records.jsonl"
    completed = set()
    if old.exists():
        for line in old.read_text(encoding="utf-8").splitlines():
            r = json.loads(line)
            completed.add((r["variant"], r["repeat"], r["task_id"]))
    # Completed failures are final even when an operator chooses a different run directory.
    for result_file in (output / "cases").glob("*/*/*/*/result.json"):
        result = json.loads(result_file.read_text(encoding="utf-8"))
        completed.add((result["variant"], result["repeat"], result["task_id"]))
    jobs = []
    for repeat in range(repeats):
        for variant in variants if repeat % 2 == 0 else list(reversed(variants)):
            for task_id in ids:
                if args.task_filter and task_id not in args.task_filter.split(","):
                    continue
                if args.start_from and ids.index(task_id) < ids.index(args.start_from):
                    continue
                case = output / "cases" / args.run_id / variant / str(repeat) / task_id
                if (
                    (variant, repeat, task_id) in completed
                    or (case / "result.json").exists()
                    or (case / "interrupted.json").exists()
                ):
                    if not args.resume:
                        raise RuntimeError("Existing attempt; --resume required")
                    continue
                if (case / "intent.json").exists():
                    save(
                        case / "interrupted.json",
                        dict(
                            classification="EXTERNAL_INTERRUPTION",
                            model=args.model,
                            task_id=task_id,
                            variant=variant,
                            run_id=f"{args.run_id}:repeat-{repeat}",
                            model_failure=False,
                            replayed=False,
                            observed_at=utc(),
                        ),
                    )
                    continue
                jobs.append((repeat, variant, task_id, case))
    port = 11435 if args.model == "qwen3:4b" else 11434
    for repeat, variant, task_id, case in jobs[:batch_size]:
        save(
            case / "intent.json",
            dict(
                model=args.model,
                split=args.group,
                variant=variant,
                task_id=task_id,
                run_id=f"{args.run_id}:repeat-{repeat}",
                started=utc(),
                parent_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            ),
        )
        print(json.dumps(dict(starting=task_id, model=args.model, variant=variant)), flush=True)
        async with ObservedProvider(
            f"http://127.0.0.1:{port}/v1",
            args.model,
            case / "observations.jsonl",
            timeout=190 if diagnostic else 90,
        ) as provider:
            await provider.check_model()
            record = await run_behavior_task(
                tasks[task_id],
                variant,
                "ollama",
                ROOT,
                case,
                provider,
                repeat=repeat,
                config=RunnerConfig(**config),
            )
        record.update(
            model=args.model,
            run_id=f"{args.run_id}:repeat-{repeat}",
            execution_group=args.group,
            formal_benchmark=not diagnostic,
            experiment_label="MODEL_CAPABILITY_DIAGNOSTIC" if diagnostic else "FIXED_BUDGET",
        )
        record["resume_key"] = dict(
            model=args.model,
            split=record["split"],
            experiment_group=args.group,
            variant=variant,
            task_id=task_id,
            run_id=record["run_id"],
        )
        save(case / "result.json", record)
        durable_jsonl(
            output / "progress.jsonl",
            dict(task_id=task_id, variant=variant, repeat=repeat, finished=utc()),
        )
        print(
            json.dumps(
                dict(finished=task_id, success=record["success"], stop=record.get("stop_reason"))
            ),
            flush=True,
        )
    print(
        json.dumps(
            dict(
                batch_complete=True,
                attempted=min(len(jobs), batch_size),
                remaining=max(0, len(jobs) - batch_size),
            )
        ),
        flush=True,
    )


async def run(args):
    lock = ROOT / "work/v3-batch.lock"
    lock.parent.mkdir(parents=True, exist_ok=True)
    # Acquire before inspecting intents, so an active task cannot be mislabeled interrupted.
    with lock.open("x", encoding="utf-8") as stream:
        json.dump(dict(pid=os.getpid(), started=utc(), model=args.model), stream)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        await execute(args)
    finally:
        lock.unlink()


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", choices=["qwen3:1.7b", "qwen3:4b"], required=True)
    p.add_argument("--group", required=True)
    p.add_argument("--resume", action="store_true")
    p.add_argument(
        "--run-id", choices=["original", "isolated-preflight-recovery"], default="original"
    )
    p.add_argument("--batch-size", type=int, choices=range(1, 6), default=3)
    p.add_argument("--task-filter")
    p.add_argument("--start-from")
    asyncio.run(run(p.parse_args()))
