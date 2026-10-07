"""Actual read-only local model task; saves raw result and trace."""

import asyncio
from pathlib import Path
from uuid import uuid4

from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tracing.recorder import TraceRecorder


async def main() -> None:
    root = Path.cwd()
    output = root / ("eval/results/ollama-smoke-" + uuid4().hex[:8])
    output.mkdir(parents=True, exist_ok=True)
    async with OpenAICompatibleProvider(max_tokens=512, reasoning_effort="none") as provider:
        await provider.check_model()
        result = await AgentRunner(
            provider,
            ToolExecutor(builtin_registry(Workspace(root))),
            RunnerConfig(max_iterations=6, model_timeout=90, task_timeout=180),
            trace=TraceRecorder(output / "trace.jsonl"),
        ).run(
            "Find the exact file defining class AgentRunner under src. Use literal grep with pattern class AgentRunner and path src, then read the matching file and return its path. /no_think"
        )
        (output / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(main())
