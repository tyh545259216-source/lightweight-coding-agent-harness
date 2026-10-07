"""Run predeclared genuine model comparisons, preserving every task attempt."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from mini_harness.agent.runner import RunnerConfig
from mini_harness.evaluation.behavior import run_behavior_task
from mini_harness.evaluation.real_repository import load_real_tasks
from mini_harness.evaluation.tasks import load_tasks
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider

ROOT = Path(__file__).resolve().parents[1]


async def run(args):
    protocol_path = ROOT / "eval/protocol_v3.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    for name, digest in protocol["hashes"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            raise RuntimeError("Frozen experiment input changed: " + name)
    spec = protocol["groups"][args.group]
    tasks = (
        load_real_tasks(ROOT)
        if spec["dataset"] == "real_repository"
        else load_tasks(ROOT / "eval/tasks/v2")
    )
    indexed = {task.id: task for task in tasks}
    output = ROOT / "eval/results/v3" / args.model.replace(":", "-") / args.group
    output.mkdir(parents=True, exist_ok=True)
    manifest_path = output / "manifest.json"
    manifest = {
        "protocol_sha256": hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        "model": args.model,
        "base_url": args.base_url,
        "group": args.group,
        "spec": spec,
    }
    if manifest_path.exists():
        if json.loads(manifest_path.read_text()) != manifest:
            raise RuntimeError("Existing experiment manifest differs")
        if not args.continue_run:
            raise RuntimeError("Existing run preserved; use --continue-run explicitly")
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    records_path = output / "records.jsonl"
    previous = (
        [json.loads(line) for line in records_path.read_text().splitlines()]
        if records_path.exists()
        else []
    )
    completed = {(r["variant"], r["repeat"], r["task_id"]) for r in previous}
    async with OpenAICompatibleProvider(
        args.base_url, args.model, max_tokens=512, reasoning_effort="none"
    ) as provider:
        await provider.check_model()
        for repeat in range(spec["repeats"]):
            # Alternating variant order limits fixed-order bias without task-dependent selection.
            variants = spec["variants"] if repeat % 2 == 0 else list(reversed(spec["variants"]))
            for variant in variants:
                for task_id in spec["ids"]:
                    if (variant, repeat, task_id) in completed:
                        continue
                    artifact = output / "artifacts" / variant / str(repeat) / task_id
                    if artifact.exists():
                        raise RuntimeError(
                            "Interrupted attempt preserved; choose a separately declared rerun: "
                            + str(artifact)
                        )
                    print(
                        json.dumps({"starting": task_id, "variant": variant, "repeat": repeat}),
                        flush=True,
                    )
                    record = await run_behavior_task(
                        indexed[task_id],
                        variant,
                        "ollama",
                        ROOT,
                        output,
                        provider,
                        repeat=repeat,
                        config=RunnerConfig(**protocol["runner"]),
                    )
                    with records_path.open("a", encoding="utf-8") as stream:
                        stream.write(json.dumps(record, ensure_ascii=False) + "\n")
                    print(
                        json.dumps(
                            {
                                "finished": task_id,
                                "success": record["success"],
                                "stop": record.get("stop_reason"),
                            }
                        ),
                        flush=True,
                    )
    (output / "completed.json").write_text(
        json.dumps(
            {"expected_records": len(spec["ids"]) * len(spec["variants"]) * spec["repeats"]}
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--continue-run", action="store_true")
    asyncio.run(run(parser.parse_args()))
