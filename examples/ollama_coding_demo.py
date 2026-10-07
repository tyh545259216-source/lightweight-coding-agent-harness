"""Guided live tool integration: human supplies exact fix; not an autonomous benchmark score."""

import asyncio
import json
from pathlib import Path
from uuid import uuid4

from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tracing.recorder import TraceRecorder


async def main() -> None:
    output = Path.cwd() / "eval/results" / ("guided-coding-smoke-" + uuid4().hex[:8])
    workspace = output / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "module.py").write_text(
        "def clamp(value, low, high):\n    return max(low, min(value, high - 1))\n",
        encoding="utf-8",
        newline="\n",
    )
    (workspace / "test_regression.py").write_text(
        "from module import clamp\ndef test_boundaries():\n    assert clamp(4,0,4)==4\n    assert clamp(9,0,4)==4\n    assert clamp(-1,0,4)==0\n",
        encoding="utf-8",
        newline="\n",
    )
    prompt = 'Use structured tools to execute these actions in order: 1. read_file path module.py. 2. edit_file path module.py, old exact string "return max(low, min(value, high - 1))", new exact string "return max(low, min(value, high))". 3. run_tests paths ["test_regression.py"]. 4. Give a one-sentence final answer only after tests finish. Do not just describe the steps. /no_think'
    async with OpenAICompatibleProvider(reasoning_effort="none") as provider:
        runner = AgentRunner(
            provider,
            ToolExecutor(
                builtin_registry(Workspace(workspace)),
                PermissionPolicy({Permission.READ, Permission.WRITE, Permission.EXECUTE}),
            ),
            RunnerConfig(max_iterations=8, model_timeout=90, task_timeout=300),
            trace=TraceRecorder(output / "trace.jsonl"),
        )
        result = await runner.run(
            prompt,
            system="You must use actual tools for each requested step. Never claim a file changed or tests passed without executing those tools. Follow the supplied exact patch. Keep final answer concise.",
        )
    calls = [json.loads(m.content) for m in result.messages if m.role == "tool"]
    tests = any(
        c["name"] == "run_tests" and c["ok"] and json.loads(c["content"])["exit_code"] == 0
        for c in calls
    )
    fixed = "high - 1" not in (workspace / "module.py").read_text(encoding="utf-8")
    success = fixed and tests and result.stop_reason.value == "final_answer"
    report = {
        "label": "GUIDED LIVE INTEGRATION, exact patch provided by human; not autonomous benchmark",
        "success": success,
        "fixed": fixed,
        "tests_passed": tests,
        "result": result.model_dump(mode="json"),
    }
    (output / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "output": str(output),
                "success": success,
                "fixed": fixed,
                "tests_passed": tests,
                "stats": result.stats.model_dump(),
            },
            ensure_ascii=False,
        ),
        flush=True,
    )


if __name__ == "__main__":
    asyncio.run(main())
