"""Scripted offline tutorial with real tools/tests; never a benchmark score."""

import argparse
import asyncio
import hashlib
import json
import shutil
from pathlib import Path
from uuid import uuid4

from mini_harness.agent.completion import CompletionController, CompletionPolicy, VerificationStatus
from mini_harness.agent.observation import ObservationController, ObservationPolicy
from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.agent.verification import VerificationPolicy
from mini_harness.providers.base import ModelResponse, Provider, ProviderError, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.session.store import SessionStore
from mini_harness.tools.builtin.filesystem import ListDir
from mini_harness.tools.builtin.navigation import ReadFileV3, RepositoryMap, SymbolSearch
from mini_harness.tools.builtin.patch import ApplyPatch
from mini_harness.tools.builtin.search import Grep
from mini_harness.tools.builtin.shell import RunTests
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry
from mini_harness.tracing.recorder import TraceRecorder


def scripted_calls(navigation: bool, source: str) -> list[ModelResponse]:
    filename, symbol = ("greeting.py", "greet") if navigation else ("calculator.py", "add")
    old, new = (
        ('return "Hello" + name', 'return "Hello, " + name')
        if navigation
        else ("return left - right", "return left + right")
    )
    calls = (
        [("repository_map", {"path": "."}), ("symbol_search", {"symbol": symbol})]
        if navigation
        else [("list_dir", {"path": "."}), ("grep", {"pattern": "def add", "path": "."})]
    )
    calls += [
        ("read_file", {"path": filename}),
        ("read_file", {"path": "tests/test_" + filename}),
        (
            "apply_patch",
            {
                "path": filename,
                "expected_sha256": hashlib.sha256(source.encode()).hexdigest(),
                "old": old,
                "new": new,
            },
        ),
        ("run_tests", {"paths": ["tests"]}),
    ]
    return [
        ModelResponse(tool_calls=[ToolCall(id=str(i), name=name, arguments=args)])
        for i, (name, args) in enumerate(calls)
    ] + [
        ModelResponse(
            content="Tutorial edit and protected tests completed; inspect observed results."
        )
    ]


async def run_tutorial(args: argparse.Namespace) -> bool:
    navigation = args.demo == "navigation"
    template = (
        Path(__file__).parent
        / "tutorials"
        / ("navigation_greeting" if navigation else "bugfix_calculator")
    )
    output = args.output or Path("work") / ("tutorial-" + uuid4().hex[:12])
    output.mkdir(parents=True, exist_ok=False)
    workspace = output / "workspace"
    shutil.copytree(template, workspace)
    (workspace / "pytest.ini").write_text("[pytest]\n", encoding="utf-8")
    filename = "greeting.py" if navigation else "calculator.py"
    protected = [*workspace.glob("tests/*.py"), workspace / "pytest.ini"]
    hashes = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in protected}
    boundary = Workspace(workspace, readonly_files=protected)
    registry = ToolRegistry()
    for tool in [
        ListDir(boundary),
        Grep(boundary),
        ReadFileV3(boundary),
        RepositoryMap(boundary),
        SymbolSearch(boundary),
        ApplyPatch(boundary),
        RunTests(boundary),
    ]:
        registry.register(tool)
    provider: Provider
    live = bool(getattr(args, "live", False))
    if live:
        provider = OpenAICompatibleProvider(
            args.base_url, args.model, max_tokens=512, reasoning_effort="none"
        )
    else:
        provider = FakeProvider(
            scripted_calls(navigation, (workspace / filename).read_bytes().decode("utf-8"))
        )
    session = SessionStore(output / "session.jsonl")
    executor = ToolExecutor(
        registry, PermissionPolicy({Permission.READ, Permission.WRITE, Permission.EXECUTE}), session
    )
    completion = CompletionController(boundary, CompletionPolicy(targets=[filename]))
    runner = AgentRunner(
        provider,
        executor,
        RunnerConfig(max_iterations=10, model_timeout=60, task_timeout=120),
        session=session,
        trace=TraceRecorder(output / "trace.jsonl"),
        observation=ObservationController(boundary, ObservationPolicy(coding=True)),
        verification=VerificationPolicy(test_paths=["tests"], max_repair_rounds=2),
        completion=completion,
    )
    try:
        if isinstance(provider, OpenAICompatibleProvider):
            await provider.check_model()
        result = await runner.run(
            (workspace / "TASK.md").read_text(encoding="utf-8"),
            system="Inspect and locate before reading/editing. Read source and tests. Use structured tools, apply a SHA/context patch, run tests, and report observed failures or success. /no_think",
        )
        unchanged = all(hashlib.sha256(p.read_bytes()).hexdigest() == h for p, h in hashes.items())
        success = (
            result.stop_reason.value == "final_answer"
            and result.stats.final_test_success is True
            and completion.state.status == VerificationStatus.SUCCESS
            and unchanged
        )
        summary = {
            "label": "TUTORIAL_ONLY_NOT_BENCHMARK",
            "provider": "live-model" if live else "scripted FakeProvider",
            "model_intelligence_claim": False,
            "demo": args.demo,
            "success": success,
            "stop_reason": result.stop_reason.value,
            "protected_tests_unchanged": unchanged,
            "verification": completion.state.status.value,
            "tool_calls": result.stats.tool_calls,
            "model_rounds": result.stats.model_rounds,
        }
        (output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(summary, indent=2))
        print("Private artifacts:", output.as_posix())
        return success
    except (ProviderError, OSError, ValueError) as exc:
        print("Tutorial unavailable:", type(exc).__name__)
        print(
            "Use the offline tutorial, or start Ollama with the requested model already installed."
        )
        print(
            "No model download or whole-attempt retry is performed. Live tutorials are best effort."
        )
        return False
    finally:
        if isinstance(provider, OpenAICompatibleProvider):
            await provider.close()


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--demo", choices=["bugfix", "navigation"], default="bugfix")
    result.add_argument("--output", type=Path)
    return result


if __name__ == "__main__":
    raise SystemExit(0 if asyncio.run(run_tutorial(parser().parse_args())) else 2)
