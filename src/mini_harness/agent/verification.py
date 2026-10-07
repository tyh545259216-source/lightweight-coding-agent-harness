"""Bounded test verification state; the runner still delegates all effects to its executor."""

import json
from typing import Literal

from pydantic import BaseModel, Field

from mini_harness.agent.state import AgentStats
from mini_harness.providers.base import ToolCall
from mini_harness.tools.result import ExecutionResult


class VerificationPolicy(BaseModel):
    test_paths: list[str] = Field(default_factory=lambda: ["."], min_length=1, max_length=20)
    max_repair_rounds: int = Field(default=2, ge=0, le=10)
    output_chars: int = Field(default=4000, ge=256, le=16000)
    require_patch: bool = True
    compact_failures: bool = False


TestKind = Literal[
    "passed",
    "assertion_failure",
    "collection_error",
    "internal_error",
    "usage_error",
    "no_tests",
    "tool_error",
]


def bounded_output(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    marker = "\n[test output truncated]\n"
    head = (limit - len(marker)) // 3
    return text[:head] + marker + text[-(limit - len(marker) - head) :]


class TestOutcome(BaseModel):
    passed: bool
    exit_code: int | None = None
    kind: TestKind
    stdout: str = ""
    stderr: str = ""
    truncated: bool = False
    failed_tests: list[str] = Field(default_factory=list)
    failure_summary: str = ""

    @classmethod
    def from_result(cls, result: ExecutionResult, limit: int) -> "TestOutcome":
        if not result.ok:
            return cls(
                passed=False,
                kind="tool_error",
                stderr=bounded_output(result.content, limit),
                truncated=len(result.content) > limit,
            )
        try:
            payload = json.loads(result.content)
            code = payload["exit_code"]
            if not isinstance(code, int) or isinstance(code, bool):
                raise ValueError("Invalid test exit code")
            stdout, stderr = str(payload.get("stdout", "")), str(payload.get("stderr", ""))
        except (ValueError, TypeError, KeyError):
            return cls(passed=False, kind="tool_error", stderr="Malformed test result")
        kinds: dict[int, TestKind] = {
            0: "passed",
            1: "assertion_failure",
            2: "collection_error",
            3: "internal_error",
            4: "usage_error",
            5: "no_tests",
        }
        failed_tests = [
            line.split(" - ", 1)[0][7:]
            for line in stdout.splitlines()
            if line.startswith("FAILED ")
        ][:10]
        relevant = [
            line
            for line in stdout.splitlines()
            if line.startswith(("E ", "> ", "FAILED ", "ERROR "))
            or "Error:" in line
            or "Exception:" in line
        ]
        summary = bounded_output("\n".join(relevant), limit)
        return cls(
            failed_tests=failed_tests,
            failure_summary=summary,
            passed=code == 0,
            exit_code=code,
            kind=kinds.get(code, "internal_error"),
            stdout=bounded_output(stdout, limit),
            stderr=bounded_output(stderr, limit),
            truncated=len(stdout) > limit or len(stderr) > limit,
        )


class VerificationState(BaseModel):
    revision: int = 0
    tested_revision: int = -1
    repair_rounds: int = 0
    initial_patch_success: bool | None = None
    final_test_success: bool | None = None
    last_outcome: TestOutcome | None = None
    observed_keys: list[str] = Field(default_factory=list)
    changed_paths: list[str] = Field(default_factory=list)


class VerificationController:
    def __init__(self, policy: VerificationPolicy, state: VerificationState | None = None) -> None:
        self.policy, self.state = policy, state or VerificationState()

    @property
    def ready(self) -> bool:
        return (
            self.state.final_test_success is True
            and self.state.tested_revision == self.state.revision
            and (self.state.revision > 0 or not self.policy.require_patch)
        )

    @property
    def dirty(self) -> bool:
        return self.state.revision > self.state.tested_revision and self.state.revision > 0

    @property
    def failed(self) -> bool:
        return self.state.last_outcome is not None and not self.state.last_outcome.passed

    @property
    def exhausted(self) -> bool:
        return self.failed and self.state.repair_rounds >= self.policy.max_repair_rounds

    def observe(
        self, call: ToolCall, key: str, result: ExecutionResult, *, canonical: bool = False
    ) -> None:
        if key in self.state.observed_keys:
            return
        if call.name not in {"write_file", "edit_file", "apply_patch", "run_tests"}:
            return
        self.state.observed_keys.append(key)
        if call.name in {"write_file", "edit_file", "apply_patch"} and result.ok:
            if call.name == "apply_patch" and not json.loads(result.content).get("changed"):
                return
            self.state.revision += 1
            self.state.final_test_success = None
            args = json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
            path = str(args.get("path", ""))
            if path not in self.state.changed_paths:
                self.state.changed_paths.append(path)
        elif call.name == "run_tests" and canonical:
            outcome = TestOutcome.from_result(result, self.policy.output_chars)
            self.state.tested_revision = self.state.revision
            self.state.last_outcome = outcome
            self.state.final_test_success = outcome.passed
            if self.state.initial_patch_success is None and self.state.revision > 0:
                self.state.initial_patch_success = outcome.passed

    def canonical_call(self, call: ToolCall) -> bool:
        if call.name != "run_tests":
            return False
        try:
            args = json.loads(call.arguments) if isinstance(call.arguments, str) else call.arguments
            return bool(args.get("paths", ["tests"]) == self.policy.test_paths)
        except (ValueError, AttributeError):
            return False

    def start_repair(self) -> None:
        self.state.repair_rounds += 1

    def sync_stats(self, stats: AgentStats) -> None:
        stats.initial_patch_success = self.state.initial_patch_success
        stats.repair_rounds = self.state.repair_rounds
        stats.final_test_success = self.state.final_test_success

    def feedback(self) -> str:
        paths = json.dumps(self.policy.test_paths)
        if self.ready:
            return "[Harness verification] Required tests passed for the latest observed edit. Give a concise final answer grounded in these tool results."
        if self.failed:
            assert self.state.last_outcome is not None
            return f"[Harness verification] Tests failed ({self.state.last_outcome.kind}, exit={self.state.last_outcome.exit_code}). Read the preceding test result and repair using authorized tools, then verify. Do not claim success. Required test paths: {paths}."
        return f"[Harness verification] Task is incomplete: apply an authorized patch/test change and run actual tests at paths {paths}. A plan or imagined test result is not completion. Inspect full source and existing tests, preserve the public API."
