"""Bounded model-produced argument corrections; never replay a side effect automatically."""

import hashlib
import json

from pydantic import BaseModel, Field

from mini_harness.providers.base import ToolCall
from mini_harness.tools.errors import ToolErrorDetail
from mini_harness.tools.result import ExecutionResult


class ArgumentRepairState(BaseModel):
    errors: int = 0
    recovered: int = 0
    repeated: int = 0
    attempts: dict[str, int] = Field(default_factory=dict)
    pending_tools: dict[str, str] = Field(default_factory=dict)
    observed_keys: list[str] = Field(default_factory=list)


class ArgumentRepairController:
    def __init__(self, max_retries: int = 2, *, enforce: bool = True):
        if not 0 <= max_retries <= 10:
            raise ValueError("max_retries must be0..10")
        self.max_retries = max_retries
        self.enforce = enforce
        self.state = ArgumentRepairState()

    def fingerprint(self, call: ToolCall) -> str:
        try:
            args = json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
        except ValueError:
            args = call.arguments
        return hashlib.sha256(json.dumps([call.name, args], sort_keys=True).encode()).hexdigest()

    def before(self, call: ToolCall) -> ToolErrorDetail | None:
        if not self.enforce:
            return None
        if self.state.attempts.get(self.fingerprint(call), 0) > self.max_retries:
            return ToolErrorDetail(
                error_type="retry_limit",
                tool=call.name,
                retryable=False,
                hint="Repeated invalid call budget exhausted; inspect the schema/path evidence and change the arguments. No automatic retry was executed.",
            )
        return None

    def observe(self, call: ToolCall, key: str, result: ExecutionResult) -> None:
        if key in self.state.observed_keys or result.replayed:
            return
        self.state.observed_keys.append(key)
        fp = self.fingerprint(call)
        if (
            result.error_detail
            and result.error_detail.retryable
            and result.error_detail.error_type in {"arguments", "range", "path_not_found"}
        ):
            self.state.errors += 1
            self.state.repeated += int(fp in self.state.attempts)
            self.state.attempts[fp] = self.state.attempts.get(fp, 0) + 1
            self.state.pending_tools[call.name] = fp
        elif (
            result.ok
            and call.name in self.state.pending_tools
            and self.state.pending_tools[call.name] != fp
        ):
            self.state.recovered += 1
            del self.state.pending_tools[call.name]
