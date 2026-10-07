"""Reconstruct an interrupted turn from conversation and execution journal."""

from dataclasses import dataclass
from typing import Any

from mini_harness.agent.state import AgentStats
from mini_harness.providers.base import Message, ToolCall, Usage
from mini_harness.session.store import SessionStore
from mini_harness.tools.result import ExecutionResult


class RecoveryBlocked(RuntimeError):
    """Human reconciliation required; automatic side-effect retry is forbidden."""


@dataclass
class RecoveryPlan:
    turn_id: str
    messages: list[Message]
    next_iteration: int
    pending: list[tuple[ToolCall, str]]
    stats: AgentStats
    final_answer: str | None = None
    missing_user: bool = False


def unfinished(store: SessionStore) -> bool:
    events = store.load()
    started = max((i for i, e in enumerate(events) if e["event"] == "turn_started"), default=-1)
    if started < 0:
        return False
    return not any(e["event"] == "terminal" for e in events[started + 1 :])


def plan_recovery(store: SessionStore) -> RecoveryPlan:
    events = store.load()
    started = max((i for i, e in enumerate(events) if e["event"] == "turn_started"), default=-1)
    if started < 0:
        raise RecoveryBlocked("No recoverable turn")
    turn: dict[str, Any] = events[started]["data"]
    tail = events[started + 1 :]
    terminals = [e for e in tail if e["event"] == "terminal"]
    if terminals and terminals[-1]["data"]["stop_reason"] == "final_answer":
        raise RecoveryBlocked("Turn already finished; start a new task to continue")
    messages = [Message.model_validate(e["data"]) for e in events if e["event"] == "message"]
    missing_user = False
    if not any(
        e["event"] == "message"
        and e["data"].get("_turn_id") == turn["turn_id"]
        and e["data"]["role"] == "user"
        for e in tail
    ):
        messages.append(Message(role="user", content=turn["task"]))
        missing_user = True
    requested = [e["data"]["iteration"] for e in tail if e["event"] == "model_requested"]
    next_iteration = max(requested, default=-1) + 1
    stats = AgentStats(
        model_rounds=sum(
            1 for e in tail if e["event"] == "model_requested" and not e["data"].get("synthetic")
        )
    )
    for event in tail:
        if event["event"] == "model_received":
            stats.usage.add(Usage.model_validate(event["data"]["usage"]))
        if event["event"] == "message" and event["data"]["role"] == "tool":
            result = ExecutionResult.model_validate_json(event["data"]["content"])
            stats.tool_calls += 1
            stats.tool_successes += int(result.ok)
            stats.tool_errors += int(not result.ok)
            stats.argument_errors += int(result.error_type == "arguments")
            stats.permission_denials += int(result.error_type == "permission")
    attempted = [e for e in tail if e["event"] == "tool_requested"]
    if attempted:
        stats.tool_calls = len(attempted)
        stats.verification_tool_calls = sum(
            e["data"].get("origin") == "verification" for e in attempted
        )
    pending: list[tuple[ToolCall, str]] = []
    assistant_events = [
        e for e in tail if e["event"] == "message" and e["data"]["role"] == "assistant"
    ]
    if assistant_events:
        latest = assistant_events[-1]["data"]
        assistant = Message.model_validate(latest)
        if not assistant.tool_calls and assistant.content.strip():
            return RecoveryPlan(
                turn["turn_id"], messages, next_iteration, [], stats, assistant.content
            )
        # IDs need only be unique within a round; select results with matching iteration metadata.
        iteration = latest["_iteration"]
        completed = {
            e["data"]["tool_call_id"]
            for e in tail
            if e["event"] == "message"
            and e["data"]["role"] == "tool"
            and e["data"].get("_iteration") == iteration
        }
        pending = [
            (c, f"{turn['turn_id']}:{iteration}:{c.id}")
            for c in assistant.tool_calls
            if c.id not in completed
        ]
    return RecoveryPlan(
        turn["turn_id"], messages, next_iteration, pending, stats, missing_user=missing_user
    )
