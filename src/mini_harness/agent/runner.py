"""Original bounded loop with durable pending-call recovery; no agent framework."""

import asyncio
import json
import time
from contextlib import nullcontext
from typing import Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

from mini_harness.agent.completion import (
    CompletionController,
    CompletionPolicy,
    CompletionState,
    VerificationStatus,
)
from mini_harness.agent.observation import (
    ObservationController,
    ObservationPolicy,
    ObservationState,
)
from mini_harness.agent.result import AgentResult
from mini_harness.agent.state import AgentStats
from mini_harness.agent.stopping import StopReason
from mini_harness.agent.verification import (
    VerificationController,
    VerificationPolicy,
    VerificationState,
)
from mini_harness.context.manager import ContextLimitError, ContextManager, message_groups
from mini_harness.providers.base import Message, Provider, ProviderError, ToolCall, ToolDefinition
from mini_harness.session.recovery import RecoveryBlocked, plan_recovery, unfinished
from mini_harness.session.store import SessionStore
from mini_harness.skills.loader import SkillLoader, SkillMode
from mini_harness.tools.argument_repair import ArgumentRepairState
from mini_harness.tools.result import ExecutionResult
from mini_harness.tracing.recorder import TraceRecorder


class Executor(Protocol):
    def definitions(self) -> list[ToolDefinition]: ...
    async def execute(self, call: ToolCall, key: str) -> ExecutionResult: ...


class RunnerConfig(BaseModel):
    max_iterations: int = Field(default=12, ge=1, le=1000)
    model_timeout: float = Field(default=120, gt=0)
    task_timeout: float = Field(default=300, gt=0)


class AgentRunner:
    def __init__(
        self,
        provider: Provider,
        executor: Executor | None = None,
        config: RunnerConfig | None = None,
        *,
        context: ContextManager | None = None,
        session: SessionStore | None = None,
        use_context: bool = True,
        trace: TraceRecorder | None = None,
        verification: VerificationPolicy | None = None,
        skills: SkillLoader | None = None,
        skill_mode: SkillMode = SkillMode.MODEL_SELECTED,
        observation: ObservationController | None = None,
        completion: CompletionController | None = None,
    ) -> None:
        self.provider, self.executor = provider, executor
        self.config = config or RunnerConfig()
        self.context = (context or ContextManager()) if use_context else None
        self.session = session
        self.trace = trace
        self.verification = verification
        self.skills, self.skill_mode = skills, skill_mode
        self.completion = completion
        if completion and not verification:
            raise ValueError("Completion gate requires canonical VerificationPolicy")
        self.observation = observation
        if observation:
            from mini_harness.tools.executor import ToolExecutor

            if not isinstance(executor, ToolExecutor):
                raise ValueError("Observation policy requires the unified ToolExecutor")
            executor.observation = observation

    async def run(
        self,
        task: str,
        *,
        system: str = "You are a coding assistant. Use tools to inspect and verify.",
        history: list[Message] | None = None,
    ) -> AgentResult:
        with self.session.lease() if self.session else nullcontext():
            if self.completion:
                self.completion.state = CompletionState(initial_hashes=self.completion.hashes())
            repair = getattr(self.executor, "argument_repair", None)
            if repair:
                repair.state = ArgumentRepairState()
            if self.observation:
                self.observation.state = ObservationState()
                self.observation.events.clear()
            if self.skills:
                self.skills.configure(self.skill_mode, task)
            return await self._drive(task, system, history, resume=False)

    async def resume(self) -> AgentResult:
        if self.session is None:
            raise RecoveryBlocked("Recovery requires a persistent session")
        with self.session.lease():
            return await self._drive("", "", None, resume=True)

    async def _drive(
        self, task: str, system: str, history: list[Message] | None, *, resume: bool
    ) -> AgentResult:
        start = time.perf_counter()
        turn_id, stats, iteration_start = uuid4().hex, AgentStats(), 0
        pending: list[tuple[ToolCall, str]] = []
        final_answer: str | None = None
        verification = VerificationController(self.verification) if self.verification else None
        if resume:
            assert self.session is not None
            plan = plan_recovery(self.session)
            turn_id, messages, stats = plan.turn_id, plan.messages, plan.stats
            if plan.missing_user:
                self.session.append(
                    "message",
                    {
                        **Message(role="user", content=plan.messages[-1].content).model_dump(),
                        "_turn_id": turn_id,
                        "_iteration": 0,
                    },
                )
            iteration_start, pending, final_answer = (
                plan.next_iteration,
                plan.pending,
                plan.final_answer,
            )
            starts = [e for e in self.session.load() if e["event"] == "turn_started"]
            saved_limit = (
                starts[-1]["data"]
                .get("config", {})
                .get("max_iterations", self.config.max_iterations)
            )
            iteration_limit = min(self.config.max_iterations, saved_limit)
            if self.skills:
                skill_states = [
                    e["data"]
                    for e in self.session.load()
                    if e["event"] == "skill_state" and e["data"].get("turn_id") == turn_id
                ]
                names = (
                    skill_states[-1]["names"]
                    if skill_states
                    else starts[-1]["data"].get("skills", [])
                )
                self.skills.mode = SkillMode(starts[-1]["data"].get("skill_mode", "MODEL_SELECTED"))
                self.skills.active.clear()
                for name in names:
                    details = skill_states[-1].get("details", {}) if skill_states else {}
                    self.skills.activate(
                        name, full=details[name] == "full" if name in details else None
                    )
            saved_completion = starts[-1]["data"].get("completion")
            if saved_completion is not None:
                if (
                    self.completion is None
                    or self.completion.policy != CompletionPolicy.model_validate(saved_completion)
                ):
                    raise RecoveryBlocked("Completion policy changed or missing")
                if str(self.completion.workspace.root) != starts[-1]["data"].get(
                    "completion_workspace"
                ):
                    raise RecoveryBlocked("Completion workspace changed")
                states = [
                    e["data"]["state"]
                    for e in self.session.load()
                    if e["event"] == "completion_state" and e["data"].get("turn_id") == turn_id
                ]
                self.completion.state = CompletionState.model_validate(
                    states[-1] if states else starts[-1]["data"]["completion_initial"]
                )
                if self.completion.evaluate()[0] != VerificationStatus.SUCCESS:
                    final_answer = None
            saved_argument_repair = starts[-1]["data"].get("argument_repair")
            if saved_argument_repair is not None:
                repair = getattr(self.executor, "argument_repair", None)
                if (
                    repair is None
                    or repair.max_retries != saved_argument_repair
                    or repair.enforce != starts[-1]["data"].get("argument_repair_enforce", True)
                ):
                    raise RecoveryBlocked("Argument repair policy changed or missing")
                states = [
                    e["data"]["state"]
                    for e in self.session.load()
                    if e["event"] == "argument_repair_state" and e["data"].get("turn_id") == turn_id
                ]
                repair.state = (
                    ArgumentRepairState.model_validate(states[-1])
                    if states
                    else ArgumentRepairState()
                )
            saved_observation = starts[-1]["data"].get("observation")
            if saved_observation is not None:
                if (
                    self.observation is None
                    or self.observation.policy
                    != ObservationPolicy.model_validate(saved_observation)
                ):
                    raise RecoveryBlocked(
                        "Observation policy changed or missing; reconciliation required"
                    )
                if str(self.observation.workspace.root) != starts[-1]["data"].get(
                    "observation_workspace"
                ):
                    raise RecoveryBlocked("Observation workspace changed")
                observations = [
                    e["data"]["state"]
                    for e in self.session.load()
                    if e["event"] == "observation_state" and e["data"].get("turn_id") == turn_id
                ]
                self.observation.state = (
                    ObservationState.model_validate(observations[-1])
                    if observations
                    else ObservationState()
                )
                if self.observation.before_final():
                    final_answer = None
            saved_verification = starts[-1]["data"].get("verification")
            if saved_verification is not None:
                saved_policy = VerificationPolicy.model_validate(saved_verification)
                # Resume must not silently weaken saved test requirements or enlarge repair budget.
                if self.verification is not None and self.verification != saved_policy:
                    raise RecoveryBlocked(
                        "Verification policy changed; explicit reconciliation required"
                    )
                states = [
                    e["data"]["state"]
                    for e in self.session.load()
                    if e["event"] == "verification_state" and e["data"].get("turn_id") == turn_id
                ]
                verification = VerificationController(
                    saved_policy, VerificationState.model_validate(states[-1]) if states else None
                )
                verification.sync_stats(stats)
                if not verification.ready:
                    final_answer = None
        else:
            if self.session and unfinished(self.session):
                raise RecoveryBlocked("Interrupted turn exists; use resume")
            messages = (
                [m.model_copy(deep=True) for m in history]
                if history
                else [Message(role="system", content=system)]
            )
            if self.session and not history:
                restored = [
                    Message.model_validate(e["data"])
                    for e in self.session.load()
                    if e["event"] == "message"
                ]
                if restored:
                    try:
                        message_groups(restored)
                    except ContextLimitError as exc:
                        raise RecoveryBlocked("Pending tool exchange requires resume") from exc
                    messages = restored
                else:
                    self.session.append("message", messages[0].model_dump())
            if self.session:
                self.session.append(
                    "turn_started",
                    {
                        "turn_id": turn_id,
                        "task": task,
                        "config": self.config.model_dump(),
                        "skills": sorted(self.skills.active) if self.skills else [],
                        "skill_mode": self.skill_mode.value,
                        "completion": self.completion.policy.model_dump()
                        if self.completion
                        else None,
                        "completion_workspace": str(self.completion.workspace.root)
                        if self.completion
                        else None,
                        "completion_initial": self.completion.state.model_dump()
                        if self.completion
                        else None,
                        "argument_repair_enforce": getattr(
                            getattr(self.executor, "argument_repair", None), "enforce", None
                        ),
                        "argument_repair": getattr(
                            getattr(self.executor, "argument_repair", None), "max_retries", None
                        ),
                        "observation": self.observation.policy.model_dump()
                        if self.observation
                        else None,
                        "observation_workspace": str(self.observation.workspace.root)
                        if self.observation
                        else None,
                        "verification": self.verification.model_dump()
                        if self.verification
                        else None,
                    },
                )
        current_iteration = max(0, iteration_start - 1)

        def append(message: Message) -> None:
            messages.append(message)
            if self.session:
                self.session.append(
                    "message",
                    {**message.model_dump(), "_turn_id": turn_id, "_iteration": current_iteration},
                )

        if not resume:
            iteration_limit = self.config.max_iterations
            append(Message(role="user", content=task))
        reason, answer, error = StopReason.MAX_ITERATIONS, "", None

        def record(event: str, layer: str, **data: object) -> None:
            if self.trace:
                self.trace.record(
                    event, turn_id, current_iteration, self.provider.model, layer, **data
                )

        record("turn_started", "runner", resume=resume, task=task)

        def save_verification() -> None:
            if verification:
                verification.sync_stats(stats)
                if self.session:
                    self.session.append(
                        "verification_state",
                        {"turn_id": turn_id, "state": verification.state.model_dump()},
                    )

        def save_observation() -> None:
            if self.observation:
                stats.policy_violations = sum(self.observation.state.violations.values())
                stats.premature_finals = self.observation.state.violations.get("premature_final", 0)
                stats.edits_before_read = self.observation.state.violations.get(
                    "edit_before_observation", 0
                )
                stats.replanning_count = self.observation.state.replanning_count
                for event in self.observation.events:
                    record(
                        str(event["event"]),
                        "policy",
                        **{k: v for k, v in event.items() if k != "event"},
                    )
                self.observation.events.clear()
                if self.session:
                    self.session.append(
                        "observation_state",
                        {"turn_id": turn_id, "state": self.observation.state.model_dump()},
                    )

        def save_completion() -> None:
            if self.completion:
                self.completion.evaluate()
                if self.session:
                    self.session.append(
                        "completion_state",
                        {"turn_id": turn_id, "state": self.completion.state.model_dump()},
                    )

        async def execute(call: ToolCall, key: str, *, origin: str = "model") -> None:
            stats.tool_calls += 1
            stats.verification_tool_calls += int(origin == "verification")
            if self.session:
                self.session.append(
                    "tool_requested",
                    {
                        "key": key,
                        "turn_id": turn_id,
                        "iteration": current_iteration,
                        "call_id": call.id,
                        "origin": origin,
                    },
                )
            tool_start = time.perf_counter()
            record(
                "tool_requested", "tool_selection", call=call.model_dump(), key=key, origin=origin
            )
            from mini_harness.tools.executor import ToolExecutor

            result = (
                (
                    await self.executor.execute(call, key, origin=origin)
                    if isinstance(self.executor, ToolExecutor)
                    else await self.executor.execute(call, key)
                )
                if self.executor
                else ExecutionResult(
                    call_id=call.id,
                    name=call.name,
                    ok=False,
                    content="No tools configured",
                    error_type="unknown_tool",
                )
            )
            repair = getattr(self.executor, "argument_repair", None)
            if repair:
                stats.recovered_argument_errors = repair.state.recovered
                stats.repeated_invalid_calls = repair.state.repeated
                if self.session:
                    self.session.append(
                        "argument_repair_state",
                        {"turn_id": turn_id, "state": repair.state.model_dump()},
                    )
            if call.name == "apply_patch":
                stats.patch_attempts += 1
                stats.patch_successes += int(
                    result.ok and json.loads(result.content).get("changed", False)
                )
                stats.no_op_edits += int(
                    result.error_detail is not None and result.error_detail.error_type == "no_op"
                )
                stats.stale_edits += int(
                    result.error_detail is not None
                    and result.error_detail.error_type == "stale_revision"
                )
            stats.invalid_path_calls += int(
                result.error_detail is not None
                and result.error_detail.error_type == "path_not_found"
            )
            save_observation()
            record(
                "tool_result",
                "tool_arguments" if result.error_type == "arguments" else "tool_execution",
                result=result.model_dump(),
                latency_seconds=time.perf_counter() - tool_start,
                origin=origin,
            )
            if self.skills and call.name == "activate_skill" and result.ok:
                arguments = (
                    json.loads(call.arguments)
                    if isinstance(call.arguments, str)
                    else call.arguments
                )
                # Executor activation already selected compact/full; never overwrite it.
                if arguments["name"] not in self.skills.active:
                    self.skills.activate(
                        arguments["name"], full=arguments.get("detail", "compact") == "full"
                    )
            stats.tool_successes += int(result.ok)
            stats.tool_errors += int(not result.ok)
            stats.argument_errors += int(result.error_type == "arguments")
            stats.permission_denials += int(result.error_type == "permission")
            if verification:
                verification.observe(call, key, result, canonical=verification.canonical_call(call))
                save_verification()
                if call.name == "run_tests" and verification.canonical_call(call):
                    record(
                        "verification_result",
                        "verification",
                        outcome=verification.state.last_outcome.model_dump()
                        if verification.state.last_outcome
                        else None,
                        state=verification.state.model_dump(exclude={"observed_keys"}),
                    )
            if self.completion:
                if verification and verification.canonical_call(call):
                    self.completion.observe_test(
                        result, verification.state.final_test_success is True
                    )
                if call.name == "independent_check" and origin == "verification":
                    self.completion.observe_independent(result)
                save_completion()
            if verification and result.ok and verification.canonical_call(call):
                # Keep the execution journal/raw trace untouched; give the model bounded,
                # explicit passed/exit/kind fields, never infer pass from tool-level ok.
                from mini_harness.agent.verification import TestOutcome

                outcome = TestOutcome.from_result(result, verification.policy.output_chars)
                if verification.policy.compact_failures and not outcome.passed:
                    outcome.stdout = (
                        outcome.failure_summary
                        or outcome.stdout[-verification.policy.output_chars :]
                    )
                    outcome.stderr = outcome.stderr[:1000]
                result = result.model_copy(update={"content": outcome.model_dump_json()})
            append(
                Message(
                    role="tool",
                    name=call.name,
                    tool_call_id=call.id,
                    content=result.model_dump_json(),
                )
            )

        async def verify_dirty() -> None:
            if verification and verification.dirty:
                check = ToolCall(
                    id=f"harness_verify_{verification.state.revision}",
                    name="run_tests",
                    arguments={"paths": verification.policy.test_paths},
                )
                append(Message(role="assistant", name="harness_verification", tool_calls=[check]))
                record(
                    "verification_requested",
                    "verification",
                    revision=verification.state.revision,
                    paths=verification.policy.test_paths,
                )
                await execute(
                    check, f"{turn_id}:{current_iteration}:{check.id}", origin="verification"
                )

        async def independent_check() -> None:
            if self.completion and self.completion.needs_independent:
                self.completion.candidate_messages = [
                    message.model_copy(deep=True) for message in messages
                ]
                self.completion.candidate_stats = stats
                check = ToolCall(
                    id=f"harness_independent_{verification.state.revision if verification else 0}",
                    name="independent_check",
                    arguments={},
                )
                append(Message(role="assistant", name="harness_independent", tool_calls=[check]))
                record(
                    "independent_requested", "verification", targets=self.completion.policy.targets
                )
                await execute(
                    check, f"{turn_id}:{current_iteration}:{check.id}", origin="verification"
                )

        try:
            async with asyncio.timeout(self.config.task_timeout):
                for call, key in pending:
                    host_origin = False
                    if self.session:
                        host_origin = any(
                            e["event"] == "message"
                            and e["data"].get("name")
                            in {"harness_verification", "harness_independent"}
                            and e["data"].get("_iteration") == current_iteration
                            and any(c["id"] == call.id for c in e["data"].get("tool_calls", []))
                            for e in self.session.load()
                        )
                    await execute(call, key, origin="verification" if host_origin else "model")
                if resume:
                    await verify_dirty()
                    await independent_check()
                if final_answer is not None:
                    reason, answer = StopReason.FINAL, final_answer
                else:
                    for iteration in range(iteration_start, iteration_limit):
                        current_iteration = iteration
                        if self.observation and self.observation.exhausted:
                            reason, error = (
                                StopReason.POLICY_LIMIT,
                                "Observation replanning budget exhausted",
                            )
                            break
                        gate_failed = (
                            self.completion is not None
                            and self.completion.evaluate()[0] == VerificationStatus.FAILURE
                        )
                        if verification and (verification.failed or gate_failed):
                            if (
                                verification.state.last_outcome
                                and verification.state.last_outcome.kind == "tool_error"
                            ) or (self.completion and self.completion.state.independent_tool_error):
                                reason, error = (
                                    StopReason.VERIFICATION_FAILED,
                                    "Test tool failed; no automatic uncertain replay",
                                )
                                break
                            if verification.exhausted or (
                                gate_failed
                                and verification.state.repair_rounds
                                >= verification.policy.max_repair_rounds
                            ):
                                reason, error = (
                                    StopReason.REPAIR_LIMIT,
                                    "Verification repair budget exhausted",
                                )
                                break
                            verification.start_repair()
                            save_verification()
                            record(
                                "repair_requested",
                                "verification",
                                repair_round=verification.state.repair_rounds,
                            )
                        if self.skills:
                            if self.context:
                                self.context.set_skills(self.skills.active)
                            if self.session:
                                self.session.append(
                                    "skill_state",
                                    {
                                        "turn_id": turn_id,
                                        "names": sorted(self.skills.active),
                                        "details": self.skills.active_details,
                                    },
                                )
                        definitions = self.executor.definitions() if self.executor else []
                        working = (
                            self.context.prepare(messages, definitions)
                            if self.context
                            else messages
                        )
                        record(
                            "context_prepared",
                            "context",
                            messages=len(working),
                            estimated_input=self.context.last_estimate if self.context else None,
                            dropped_groups=self.context.dropped_groups if self.context else 0,
                            inspection=self.context.last_inspection
                            if self.context and self.context.inspection
                            else None,
                        )
                        stats.model_rounds += 1
                        model_start = time.perf_counter()
                        record("model_requested", "model", tool_names=[t.name for t in definitions])
                        if self.session:
                            self.session.append(
                                "model_requested", {"turn_id": turn_id, "iteration": iteration}
                            )
                        try:
                            async with asyncio.timeout(self.config.model_timeout):
                                response = await self.provider.complete(working, definitions)
                        except ProviderError as exc:
                            record(
                                "model_error",
                                "model",
                                error=str(exc),
                                latency_seconds=time.perf_counter() - model_start,
                            )
                            reason, error = StopReason.PROVIDER_ERROR, str(exc)
                            break
                        record(
                            "model_received",
                            "model",
                            content=response.content,
                            tool_calls=[c.model_dump() for c in response.tool_calls],
                            usage=response.usage.model_dump(),
                            latency_seconds=time.perf_counter() - model_start,
                        )
                        stats.usage.add(response.usage)
                        if self.session:
                            self.session.append(
                                "model_received",
                                {
                                    "turn_id": turn_id,
                                    "iteration": iteration,
                                    "usage": response.usage.model_dump(),
                                },
                            )
                        if len({c.id for c in response.tool_calls}) != len(response.tool_calls):
                            reason, error = StopReason.MALFORMED_RESPONSE, "Duplicate tool call IDs"
                            break
                        if not response.tool_calls:
                            if not response.content.strip():
                                reason = StopReason.EMPTY_RESPONSE
                                break
                            append(Message(role="assistant", content=response.content))
                            if self.observation:
                                feedback = self.observation.before_final()
                                save_observation()
                                if feedback:
                                    append(
                                        Message(
                                            role="system",
                                            name="harness_observation",
                                            content=json.dumps(feedback),
                                        )
                                    )
                                    continue
                            if verification and not verification.ready:
                                record(
                                    "completion_rejected",
                                    "verification",
                                    state=verification.state.model_dump(exclude={"observed_keys"}),
                                )
                                append(
                                    Message(
                                        role="system",
                                        name="harness_verification",
                                        content=verification.feedback(),
                                    )
                                )
                                continue
                            if self.completion:
                                if (
                                    self.completion.state.tested_hashes != self.completion.hashes()
                                    and verification
                                    and verification.state.revision > 0
                                ):
                                    verification.state.revision += 1
                                    save_verification()
                                    await verify_dirty()
                                await independent_check()
                                status, _ = self.completion.evaluate()
                                if status != VerificationStatus.SUCCESS:
                                    self.completion.state.rejected_finals += 1
                                    save_completion()
                                    record(
                                        "completion_rejected",
                                        "completion",
                                        status=status.value,
                                        missing=self.completion.evaluate()[1],
                                    )
                                    append(
                                        Message(
                                            role="system",
                                            name="harness_completion",
                                            content=self.completion.feedback(),
                                        )
                                    )
                                    continue
                            reason, answer = StopReason.FINAL, response.content
                            break
                        append(
                            Message(
                                role="assistant",
                                content=response.content,
                                tool_calls=response.tool_calls,
                            )
                        )
                        for call in response.tool_calls:
                            await execute(call, f"{turn_id}:{iteration}:{call.id}")
                        if verification:
                            await verify_dirty()
                            await independent_check()
                            append(
                                Message(
                                    role="system",
                                    name="harness_verification",
                                    content=verification.feedback(),
                                )
                            )
        except ContextLimitError as exc:
            record(
                "context_failed",
                "context",
                inspection=self.context.last_inspection if self.context else None,
                error=str(exc),
            )
            reason, error = StopReason.CONTEXT_LIMIT, str(exc)
        except RecoveryBlocked as exc:
            reason, error = StopReason.RECOVERY_BLOCKED, str(exc)
        except TimeoutError:
            reason, error = StopReason.TIMEOUT, "Task or provider timeout"
        except asyncio.CancelledError:
            reason, error = (
                StopReason.CANCELLED,
                "Cancelled by caller; pending effects require recovery",
            )
        save_observation()
        if verification:
            verification.sync_stats(stats)
        stats.latency_seconds = time.perf_counter() - start
        result = AgentResult(
            turn_id=turn_id,
            answer=answer,
            stop_reason=reason,
            error=error,
            stats=stats,
            verification_status=self.completion.evaluate()[0]
            if self.completion
            else VerificationStatus.UNVERIFIED,
            messages=messages,
        )
        record(
            "terminal",
            "final_answer",
            answer=answer,
            stop_reason=reason.value,
            error=error,
            stats=stats.model_dump(),
        )
        if self.session:
            self.session.append("terminal", result.model_dump(mode="json", exclude={"messages"}))
        return result
