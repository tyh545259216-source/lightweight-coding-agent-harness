"""One genuine toy coding smoke with scoped tools/protected tests; not a benchmark score."""

import ast
import asyncio
import json
import sys
from pathlib import Path

from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.agent.verification import VerificationPolicy
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.tools.builtin.filesystem import EditFile, ReadFile
from mini_harness.tools.builtin.shell import RunTests, run_process
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry
from mini_harness.tracing.recorder import TraceRecorder


async def main() -> None:
    output = Path.cwd() / "eval/results/v2-coding-smoke"
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    workspace.mkdir()
    original = "def add(left, right):\n    return left - right\n"
    (workspace / "calculator.py").write_text(original, encoding="utf-8")
    tests = "from calculator import add\ndef test_add():\n    assert add(2,3)==5\n    assert add(-2,1)==-1\n    assert add(0,0)==0\n"
    test_path = workspace / "test_calculator.py"
    test_path.write_text(tests, encoding="utf-8")
    (workspace / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    boundary = Workspace(workspace, protected_files=[test_path])
    registry = ToolRegistry()
    for tool in [ReadFile(boundary), EditFile(boundary), RunTests(boundary)]:
        registry.register(tool)
    executor = ToolExecutor(
        registry, PermissionPolicy({Permission.READ, Permission.WRITE, Permission.EXECUTE})
    )
    config = RunnerConfig(max_iterations=10, model_timeout=60, task_timeout=120)
    async with OpenAICompatibleProvider(max_tokens=512, reasoning_effort="none") as provider:
        await provider.check_model()
        result = await AgentRunner(
            provider,
            executor,
            config,
            verification=VerificationPolicy(test_paths=["."], max_repair_rounds=2),
            trace=TraceRecorder(output / "trace.jsonl"),
        ).run(
            "Fix calculator.py add(left, right) to return the arithmetic sum of its two inputs. Read the implementation before an exact edit, preserve the signature and leave existing tests unchanged. Verify the actual tests and report evidence. /no_think"
        )
        source = (workspace / "calculator.py").read_text(encoding="utf-8")
        try:
            function = next(
                n
                for n in ast.parse(source).body
                if isinstance(n, ast.FunctionDef) and n.name == "add"
            )
            signature = [arg.arg for arg in function.args.args] == ["left", "right"]
        except (SyntaxError, StopIteration):
            signature = False
        hidden = json.loads(
            await run_process(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    "from calculator import add; assert add(2,3)==5; assert add(-4,2)==-2; assert add(0,7)==7",
                ],
                str(workspace),
            )
        )
        observed_read = any(
            m.role == "tool" and m.name == "read_file" and json.loads(m.content)["ok"]
            for m in result.messages
        )
        success = (
            result.stop_reason.value == "final_answer"
            and result.stats.final_test_success is True
            and hidden["exit_code"] == 0
            and signature
            and observed_read
            and test_path.read_text(encoding="utf-8") == tests
        )
        (output / "result.json").write_text(result.model_dump_json(indent=2), encoding="utf-8")
        summary = {
            "success": success,
            "scope": "one toy arithmetic repair with three scoped tools and protected pre-existing tests; not a dataset/general coding reliability score",
            "model": provider.model,
            "config": config.model_dump(),
            "signature_preserved": signature,
            "independent_exit": hidden["exit_code"],
            "observed_read": observed_read,
            "source_changed": source != original,
            "stop_reason": result.stop_reason.value,
            "stats": result.stats.model_dump(),
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
