"""Genuine read-only structured-tool smoke; not an autonomous coding benchmark."""

import asyncio
import json
from pathlib import Path

from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin.filesystem import ReadFile
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry
from mini_harness.tracing.recorder import TraceRecorder


async def main() -> None:
    output = Path.cwd() / "eval/results/v2-ollama-smoke"
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    (workspace / "hello.py").write_text(
        'def greet(name):\n    return "Hello " + name\n', encoding="utf-8"
    )
    registry = ToolRegistry()
    registry.register(ReadFile(Workspace(workspace)))
    config = RunnerConfig(max_iterations=6, model_timeout=60, task_timeout=120)
    async with OpenAICompatibleProvider(max_tokens=512, reasoning_effort="none") as provider:
        await provider.check_model()
        result = await AgentRunner(
            provider, ToolExecutor(registry), config, trace=TraceRecorder(output / "trace.jsonl")
        ).run(
            "Read hello.py with read_file, then report what greet('Ada') returns. This task is read-only. /no_think"
        )
        reads = [json.loads(m.content) for m in result.messages if m.role == "tool"]
        success = (
            result.stop_reason.value == "final_answer"
            and any(r["ok"] and r["name"] == "read_file" for r in reads)
            and "Hello Ada" in result.answer
        )
        (output / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
        summary = {
            "success": success,
            "scope": "real provider plus actual read-only structured tool; not autonomous coding intelligence",
            "model": provider.model,
            "config": config.model_dump(),
            "stop_reason": result.stop_reason.value,
            "stats": result.stats.model_dump(),
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
