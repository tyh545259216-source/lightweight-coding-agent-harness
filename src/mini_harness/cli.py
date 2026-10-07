"""Small CLI: run, resume and deterministic offline coding demo."""

import argparse
import asyncio
import json
import logging
import os
from pathlib import Path

from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.agent.verification import VerificationPolicy
from mini_harness.context.budget import TokenBudget
from mini_harness.context.manager import ContextManager
from mini_harness.evaluation.fixtures import fixture_for, materialize
from mini_harness.evaluation.oracle import scripted_responses
from mini_harness.evaluation.tasks import Task
from mini_harness.providers.base import ModelResponse, Provider, ProviderError
from mini_harness.providers.fake import FakeProvider
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.security.workspace import Workspace
from mini_harness.session.recovery import RecoveryBlocked
from mini_harness.session.store import SessionBusyError, SessionStore
from mini_harness.skills.loader import ActivateSkill, SkillLoader, SkillMode
from mini_harness.tools.builtin import builtin_registry
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tracing.recorder import TraceRecorder


async def execute(args: argparse.Namespace) -> int:
    if args.command == "demo":
        workspace = args.workspace.resolve()
        if workspace.exists():
            raise ValueError(
                "Demo workspace must be a new directory; existing content is preserved"
            )
        workspace.parent.mkdir(parents=True, exist_ok=True)
        task = Task(
            id="demo",
            category="Multi-tool",
            case=0,
            split="development",
            description="offline exact-edit/test loop",
        )
        fixture = fixture_for(task, workspace.parent)
        materialize(fixture, workspace)
        args.task = fixture.prompt
        args.allow_write, args.allow_execute = True, True
        provider: Provider = FakeProvider(scripted_responses(task, fixture, False))
    elif args.provider == "fake":
        if not args.script:
            raise ValueError(
                "Fake run/resume requires --script containing a JSON list of ModelResponse objects"
            )
        script = json.loads(args.script.read_text(encoding="utf-8"))
        provider = FakeProvider([ModelResponse.model_validate(r) for r in script])
    else:
        provider = OpenAICompatibleProvider(
            args.base_url,
            args.model,
            api_key=os.environ.get("HARNESS_API_KEY", "ollama"),
            reasoning_effort="none",
        )
    workspace = Workspace(
        args.workspace, protected_files=[p for p in (args.session, args.trace) if p is not None]
    )
    registry = builtin_registry(workspace)
    policy = {Permission.READ}
    if args.allow_write:
        policy.add(Permission.WRITE)
    if args.allow_execute:
        policy.add(Permission.EXECUTE)
    session = SessionStore(args.session) if args.session else None
    trace = TraceRecorder(args.trace) if args.trace else None
    system = "You are a coding assistant. Inspect before editing; use structured tools and verify tests. Final answers must report evidence and failures accurately. /no_think"
    loader = None
    if args.skills:
        loader = SkillLoader(args.skills)
        registry.register(ActivateSkill(loader))
        system += "\n" + loader.catalog()
    executor = ToolExecutor(registry, PermissionPolicy(policy), session)
    runner = AgentRunner(
        provider,
        executor,
        RunnerConfig(
            max_iterations=args.max_iterations,
            model_timeout=args.model_timeout,
            task_timeout=args.task_timeout,
        ),
        context=ContextManager(
            TokenBudget(
                max_tokens=args.context_budget, reserve_output=min(1024, args.context_budget // 4)
            )
        ),
        session=session,
        trace=trace,
        skills=loader,
        skill_mode=SkillMode(getattr(args, "skill_mode", "MODEL_SELECTED")),
        verification=VerificationPolicy(
            test_paths=args.test_paths, max_repair_rounds=args.max_repair_rounds
        )
        if getattr(args, "verify", False)
        else None,
    )
    try:
        if args.command == "resume":
            result = await runner.resume()
        else:
            result = await runner.run(args.task, system=system)
        print(result.model_dump_json(indent=2))
        return 0 if result.stop_reason.value == "final_answer" else 2
    finally:
        if isinstance(provider, OpenAICompatibleProvider):
            await provider.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["run", "resume", "demo"]:
        command = sub.add_parser(name)
        if name == "run":
            command.add_argument("task")
        command.add_argument("--workspace", type=Path, required=True)
        command.add_argument(
            "--verify",
            action="store_true",
            help="Require a real patch and verified tests; never grants permissions",
        )
        command.add_argument("--test-paths", nargs="+", default=["."])
        command.add_argument("--max-repair-rounds", type=int, default=2)
        command.add_argument("--provider", choices=["ollama", "fake"], default="ollama")
        command.add_argument("--model", default="qwen3:1.7b")
        command.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
        command.add_argument("--script", type=Path)
        command.add_argument("--session", type=Path)
        command.add_argument("--trace", type=Path)
        command.add_argument("--skills", type=Path)
        command.add_argument(
            "--skill-mode", choices=[m.value for m in SkillMode], default="MODEL_SELECTED"
        )
        command.add_argument("--allow-write", action="store_true")
        command.add_argument("--allow-execute", action="store_true")
        command.add_argument("--max-iterations", type=int, default=12)
        command.add_argument("--model-timeout", type=float, default=90)
        command.add_argument("--task-timeout", type=float, default=300)
        command.add_argument("--context-budget", type=int, default=16384)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    try:
        code = asyncio.run(execute(args))
    except (ValueError, OSError, ProviderError, RecoveryBlocked, SessionBusyError) as exc:
        logging.error("%s: %s", type(exc).__name__, exc)
        code = 2
    raise SystemExit(code)


if __name__ == "__main__":
    main()
