"""Opt-in V3 behavior CLI; read-only permissions remain the default."""

import argparse
import asyncio
from pathlib import Path

from mini_harness.agent.completion import CompletionController, CompletionPolicy
from mini_harness.agent.observation import ObservationController, ObservationPolicy
from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.agent.verification import VerificationPolicy
from mini_harness.context.budget import TokenBudget
from mini_harness.context.manager import ContextManager, ContextMode
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.session.store import SessionStore
from mini_harness.skills.loader import ActivateSkill, SkillLoader, SkillMode
from mini_harness.tools.argument_repair import ArgumentRepairController
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tracing.recorder import TraceRecorder


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("task", nargs="?", default="")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument(
        "--output",
        type=Path,
        required=True,
        help="New private journal/trace directory, or existing directory with --resume",
    )
    p.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    p.add_argument("--model", default="qwen3:1.7b")
    p.add_argument(
        "--coding",
        action="store_true",
        help="Explicitly enable observation and task-target canonical completion gate",
    )
    p.add_argument("--target", action="append", default=[])
    p.add_argument("--test-path", action="append", default=[])
    p.add_argument("--allow-write", action="store_true")
    p.add_argument("--allow-execute", action="store_true")
    p.add_argument("--skills", type=Path)
    p.add_argument(
        "--skill-mode",
        choices=["MODEL_SELECTED", "SELECTED_SKILL_COMPACT", "SELECTED_SKILL_FULL"],
        default="MODEL_SELECTED",
    )
    p.add_argument("--context-mode", choices=[m.value for m in ContextMode], default="MANAGED_V3")
    p.add_argument("--max-iterations", type=int, default=10)
    p.add_argument("--model-timeout", type=float, default=60)
    p.add_argument("--task-timeout", type=float, default=120)
    p.add_argument("--resume", action="store_true")
    return p


async def run(args: argparse.Namespace) -> None:
    if args.coding and not args.target:
        raise ValueError("Coding gate requires explicit --target")
    if not args.resume:
        args.output.mkdir(parents=True, exist_ok=False)
    store = SessionStore(args.output / "session.jsonl")
    trace = TraceRecorder(args.output / "trace.jsonl")
    workspace = Workspace(args.workspace, protected_files=[store.path, trace.store.path])
    registry = builtin_registry(workspace, navigation_v2=True, patch=True)
    loader = SkillLoader(args.skills) if args.skills else None
    if loader:
        registry.register(ActivateSkill(loader))
    grants = {Permission.READ}
    if args.allow_write:
        grants.add(Permission.WRITE)
    if args.allow_execute:
        grants.add(Permission.EXECUTE)
    observation = ObservationController(
        workspace,
        ObservationPolicy(coding=args.coding, require_complete_read=False, prefer_patch=True),
    )
    executor = ToolExecutor(
        registry,
        PermissionPolicy(grants),
        store,
        observation=observation,
        argument_repair=ArgumentRepairController(2),
    )
    verification = (
        VerificationPolicy(test_paths=args.test_path or ["."], compact_failures=True)
        if args.coding
        else None
    )
    completion = (
        CompletionController(workspace, CompletionPolicy(targets=args.target))
        if args.coding
        else None
    )
    async with OpenAICompatibleProvider(
        args.base_url, args.model, reasoning_effort="none", max_tokens=512
    ) as provider:
        await provider.check_model()
        runner = AgentRunner(
            provider,
            executor,
            RunnerConfig(
                max_iterations=args.max_iterations,
                model_timeout=args.model_timeout,
                task_timeout=args.task_timeout,
            ),
            context=ContextManager(
                TokenBudget(max_tokens=16384, reserve_output=1024, tool_output_chars=5000),
                mode=ContextMode(args.context_mode),
                inspection=True,
            ),
            session=store,
            trace=trace,
            observation=observation,
            verification=verification,
            completion=completion,
            skills=loader,
            skill_mode=SkillMode(args.skill_mode),
        )
        system = "Use actual repository tools, not a plan alone. Locate and read relevant source ranges; continue has_more as needed. Use apply_patch with observed exact context and sha256 for existing source. Run canonical tests, repair observed failures within budget, preserve API and respect permissions. Report observed limitations. /no_think"
        if loader:
            system += "\n" + loader.catalog()
        result = (
            await runner.resume() if args.resume else await runner.run(args.task, system=system)
        )
        (args.output / "agent_result.json").write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )
        print(result.model_dump_json(exclude={"messages"}, indent=2))


if __name__ == "__main__":
    p = parser()
    args = p.parse_args()
    if args.coding and not args.target:
        p.error("--coding requires one or more --target paths")
    if not args.resume and not args.task:
        p.error("Supply a task or --resume")
    asyncio.run(run(args))
