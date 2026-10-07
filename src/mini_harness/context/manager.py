"""Project durable history into bounded working context without splitting tool exchanges."""

import json
from enum import StrEnum
from hashlib import sha256

from mini_harness.context.budget import TokenBudget, estimate_messages
from mini_harness.providers.base import Message, ToolDefinition


class ContextLimitError(ValueError):
    pass


def message_groups(messages: list[Message]) -> list[list[Message]]:
    groups: list[list[Message]] = []
    index = 0
    while index < len(messages):
        message = messages[index]
        if message.role == "tool":
            raise ContextLimitError("Orphan tool result")
        group = [message]
        index += 1
        if message.tool_calls:
            if message.role != "assistant":
                raise ContextLimitError("Only assistant can call tools")
            pending = {c.id for c in message.tool_calls}
            if len(pending) != len(message.tool_calls):
                raise ContextLimitError("Duplicate call IDs")
            while index < len(messages) and messages[index].role == "tool":
                result = messages[index]
                if result.tool_call_id not in pending:
                    raise ContextLimitError("Unexpected/duplicate tool result")
                pending.remove(result.tool_call_id)
                group.append(result)
                index += 1
            if pending:
                raise ContextLimitError("Incomplete tool exchange; recover before model request")
        groups.append(group)
    return groups


class ContextMode(StrEnum):
    NO_COMPACTION = "NO_COMPACTION"
    NAIVE_TRUNCATION = "NAIVE_TRUNCATION"
    MANAGED_V3 = "MANAGED_V3"
    MANAGED_CONTEXT = "MANAGED_CONTEXT"


def bounded(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    marker = "\n[tool output truncated]\n"
    remaining = max(0, limit - len(marker))
    head = (remaining + 1) // 2
    tail = remaining - head
    return text[:head] + marker + (text[-tail:] if tail else "")


def truncate_output(message: Message, limit: int) -> None:
    """Keep envelope and structured test status intact; bound leaf output strings."""
    if message.role != "tool":
        return
    try:
        envelope = json.loads(message.content)
        if not isinstance(envelope, dict) or "content" not in envelope:
            raise ValueError
        payload = envelope["content"]
        if isinstance(payload, str):
            try:
                structured = json.loads(payload)
            except ValueError:
                structured = None
            if isinstance(structured, dict):
                for key in ("stdout", "stderr", "output", "content", "diff", "failure_summary"):
                    if isinstance(structured.get(key), str):
                        original = structured[key]
                        structured[key] = bounded(original, limit)
                        if key == "content" and len(original) > limit:
                            structured["content_truncated"] = True
                envelope["content"] = json.dumps(structured, ensure_ascii=False)
            else:
                envelope["content"] = bounded(payload, limit)
        message.content = json.dumps(envelope, ensure_ascii=False)
    except (ValueError, TypeError):
        message.content = bounded(message.content, limit)


def execution_state(groups: list[list[Message]]) -> str:
    """Extract evidence, never infer success from a model's prose or tool-level ok."""
    paths: list[str] = []
    latest_test: dict[str, object] | None = None
    latest_error: str | None = None
    for group in groups:
        calls = {c.id: c for c in group[0].tool_calls}
        for message in group[1:]:
            call = calls.get(message.tool_call_id or "")
            if call is None:
                continue
            try:
                result = json.loads(message.content)
                arguments = call.arguments
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                if not isinstance(result, dict) or not isinstance(arguments, dict):
                    continue
                if not result.get("ok"):
                    latest_error = f"{call.name}: {result.get('error_type', 'tool_error')}"
                    continue
                path = arguments.get("path")
                if isinstance(path, str) and call.name in {"read_file", "write_file", "edit_file"}:
                    if path in paths:
                        paths.remove(path)
                    paths.append(path)
                if call.name == "run_tests":
                    payload = result.get("content", "")
                    if isinstance(payload, str):
                        payload = json.loads(payload)
                    if isinstance(payload, dict):
                        latest_test = {
                            "paths": arguments.get("paths"),
                            "exit_code": payload.get("exit_code"),
                            "passed": payload.get("passed"),
                            "kind": payload.get("kind"),
                        }
            except (ValueError, TypeError):
                continue
    state = {
        "recent_file_paths": paths[-8:],
        "latest_test": latest_test,
        "latest_tool_error": latest_error,
    }
    if not paths and latest_test is None and latest_error is None:
        return ""
    return "[Execution evidence; test status applies only to listed paths]\n" + json.dumps(
        state, ensure_ascii=False
    )


class ContextManager:
    def __init__(
        self,
        budget: TokenBudget | None = None,
        compact: bool = True,
        *,
        mode: ContextMode | None = None,
        recent_exchanges: int = 2,
        inspection: bool = False,
    ) -> None:
        if recent_exchanges < 0:
            raise ValueError("recent_exchanges must be nonnegative")
        self.budget = budget or TokenBudget()
        self.mode = mode or (
            ContextMode.MANAGED_CONTEXT if compact else ContextMode.NAIVE_TRUNCATION
        )
        self.compact = self.mode in {ContextMode.MANAGED_CONTEXT, ContextMode.MANAGED_V3}
        self.recent_exchanges = recent_exchanges
        self.summary = ""
        self.last_estimate = 0
        self.dropped_groups = 0
        self.skills: dict[str, str] = {}
        self._summary_facts: list[str] = []
        self._summarized: set[str] = set()
        self.inspection = inspection
        self.last_inspection: dict[str, object] = {}

    def set_skills(self, active: dict[str, str]) -> None:
        # Bodies originate from the configured trusted skill root, not tool stdout.
        self.skills = dict(active)

    def _remember(self, group: list[Message]) -> None:
        digest = sha256("".join(m.model_dump_json() for m in group).encode()).hexdigest()
        if digest in self._summarized or not self.budget.summary_chars:
            return
        self._summarized.add(digest)
        names = ",".join(c.name for c in group[0].tool_calls)
        snippet = " | ".join(f"{m.role}: {m.content[:100]}" for m in group)
        self._summary_facts.append(f"{names} {snippet}")
        # Keep newest facts under a character bound, not an ever-growing memory store.
        while len("\n".join(self._summary_facts)) > self.budget.summary_chars:
            if len(self._summary_facts) == 1:
                self._summary_facts[0] = self._summary_facts[0][-self.budget.summary_chars :]
                break
            self._summary_facts.pop(0)
        self.summary = (
            (
                "[Lossy rolling history; re-read files before editing]\n"
                + "\n".join(self._summary_facts)
            )[: self.budget.summary_chars]
            if self.budget.summary_chars
            else ""
        )

    def prepare(self, history: list[Message], tools: list[ToolDefinition]) -> list[Message]:
        self.last_inspection = {}
        copies = [m.model_copy(deep=True) for m in history]
        skill_messages = [
            Message(role="system", name="harness_skill", content=f"Skill {name}:\n{body}")
            for name, body in sorted(self.skills.items())
        ]
        index = next((i for i, m in enumerate(copies) if m.role != "system"), len(copies))
        copies[index:index] = skill_messages
        groups = message_groups(copies)
        self.dropped_groups = 0
        if self.mode == ContextMode.NO_COMPACTION:
            self.last_estimate = estimate_messages(copies, tools)
            if self.last_estimate > self.budget.input_limit:
                raise ContextLimitError("Uncompacted history exceeds context budget")
            if self.inspection:
                self.last_inspection = {
                    "mode": self.mode.value,
                    "retained_messages": [m.model_dump() for m in copies],
                    "dropped_messages": [],
                    "summary": "",
                    "estimate": self.last_estimate,
                    "estimate_unit": "UTF-8 serialized byte proxy",
                    "reason": "raw input within common budget",
                }
            return copies
        for message in copies:
            truncate_output(message, self.budget.tool_output_chars)
        latest_user = max((i for i, g in enumerate(groups) if g[0].role == "user"), default=-1)
        kept = list(range(len(groups)))
        pinned = {latest_user, len(groups) - 1}
        systems: dict[str, int] = {}
        for i, group in enumerate(groups):
            if group[0].role == "system":
                if group[0].name in {
                    "harness_verification",
                    "harness_observation",
                    "harness_completion",
                }:
                    old = systems.get(group[0].name or "")
                    if old is not None:
                        kept.remove(old)
                    systems[group[0].name or ""] = i
                else:
                    pinned.add(i)
        pinned.update(systems.values())
        managed = self.mode in {ContextMode.MANAGED_CONTEXT, ContextMode.MANAGED_V3}
        state = execution_state(groups) if managed else ""
        if managed:
            exchanges = [i for i, g in enumerate(groups) if i > latest_user and g[0].tool_calls]
            if self.recent_exchanges:
                pinned.update(exchanges[-self.recent_exchanges :])
            # Compatibility for explicit activation without a host SkillLoader.
            pinned.update(
                i
                for i, g in enumerate(groups)
                if any(c.name == "activate_skill" and not self.skills for c in g[0].tool_calls)
            )
        if self.mode == ContextMode.MANAGED_V3:
            latest_read = None
            latest_failure = None
            latest_map = None
            for i, group in enumerate(groups):
                if i <= latest_user:
                    continue
                for message in group[1:]:
                    if message.role != "tool":
                        continue
                    try:
                        envelope = json.loads(message.content)
                        if message.name == "read_file" and envelope.get("ok"):
                            latest_read = i
                        if message.name in {"repository_map", "symbol_search"} and envelope.get(
                            "ok"
                        ):
                            latest_map = i
                        payload = envelope.get("content", "")
                        data = json.loads(payload) if isinstance(payload, str) else payload
                        if (
                            message.name == "run_tests"
                            and isinstance(data, dict)
                            and data.get("exit_code") not in {None, 0}
                        ):
                            latest_failure = i
                    except (ValueError, TypeError):
                        continue
            pinned.update(i for i in [latest_read, latest_failure, latest_map] if i is not None)
        auxiliary = True

        def project() -> list[Message]:
            result = [m for i in kept for m in groups[i]]
            if managed:
                index = next((i for i, m in enumerate(result) if m.role != "system"), len(result))
                injected: list[Message] = []
                if auxiliary:
                    if self.summary:
                        injected.append(
                            Message(role="assistant", name="harness_summary", content=self.summary)
                        )
                    if state:
                        injected.append(
                            Message(role="assistant", name="harness_state", content=state)
                        )
                result[index:index] = injected
            return result

        while estimate_messages(project(), tools) > self.budget.input_limit:
            removable = next((i for i in kept if i not in pinned), None)
            if removable is None:
                # Derived summaries are advisory. Never evict actual recent exchanges or skills.
                if auxiliary and managed:
                    auxiliary = False
                    continue
                if self.inspection:
                    self.last_inspection = {
                        "mode": self.mode.value,
                        "retained_group_indexes": kept,
                        "pinned_group_indexes": sorted(pinned),
                        "estimate": estimate_messages(project(), tools),
                        "reason": "pinned evidence cannot fit; safe stop",
                    }
                raise ContextLimitError(
                    "Pinned instructions/task/recent exchanges exceed context budget"
                )
            kept.remove(removable)
            self.dropped_groups += 1
            if managed:
                self._remember(groups[removable])
        result = project()
        self.last_estimate = estimate_messages(result, tools)
        if self.inspection:
            self.last_inspection = {
                "mode": self.mode.value,
                "retained_messages": [m.model_dump() for m in result],
                "dropped_messages": [
                    {
                        "group_index": i,
                        "roles": [m.role for m in groups[i]],
                        "tool_names": [c.name for c in groups[i][0].tool_calls],
                    }
                    for i in range(len(groups))
                    if i not in kept
                ],
                "summary": self.summary if auxiliary else "",
                "estimate": self.last_estimate,
                "estimate_unit": "UTF-8 serialized byte proxy",
                "pinned_group_indexes": sorted(pinned),
                "reason": "complete exchanges; system/skills/latest task/recent turns pinned; V3 additionally pins latest source/map/test failure"
                if self.mode == ContextMode.MANAGED_V3
                else "V2/naive projection under common budget",
            }
        return result
