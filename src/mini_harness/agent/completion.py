"""Task-specific completion gate consumes observed tests and trusted independent checks."""

import hashlib
import json
from collections.abc import Awaitable, Callable
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from mini_harness.agent.state import AgentStats
from mini_harness.providers.base import Message
from mini_harness.security.permissions import Permission
from mini_harness.security.workspace import Workspace
from mini_harness.tools.base import BaseTool, InputModel
from mini_harness.tools.result import ExecutionResult


class VerificationStatus(StrEnum):
    SUCCESS = "VERIFIED_SUCCESS"
    FAILURE = "VERIFIED_FAILURE"
    UNVERIFIED = "UNVERIFIED"


class CompletionPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid")
    targets: list[str] = Field(min_length=1, max_length=20)
    require_independent: bool = False
    all_targets_changed: bool = False


class CompletionState(BaseModel):
    initial_hashes: dict[str, str | None] = Field(default_factory=dict)
    tested_hashes: dict[str, str | None] = Field(default_factory=dict)
    independent_hashes: dict[str, str | None] = Field(default_factory=dict)
    canonical_passed: bool | None = None
    independent_passed: bool | None = None
    independent_tool_error: bool = False
    independent_summary: str = ""
    status: VerificationStatus = VerificationStatus.UNVERIFIED
    rejected_finals: int = 0


class IndependentOutcome(BaseModel):
    passed: bool
    summary: str = Field(max_length=1500)


class IndependentInput(InputModel):
    pass


class IndependentCheck(BaseTool[IndependentInput]):
    name, description, input_model = (
        "independent_check",
        "Host-configured independent behavior/API/mutant check.",
        IndependentInput,
    )
    host_only = True
    permission, side_effect = Permission.EXECUTE, True
    timeout = 60

    def __init__(self, check: Callable[[], Awaitable[IndependentOutcome]]):
        self.check = check

    async def execute(self, arguments: IndependentInput) -> str:
        return (await self.check()).model_dump_json()


class CompletionController:
    def __init__(
        self, workspace: Workspace, policy: CompletionPolicy, state: CompletionState | None = None
    ):
        self.workspace, self.policy = workspace, policy
        self.state = state or CompletionState(initial_hashes=self.hashes())
        self.candidate_messages: list[Message] = []
        self.candidate_stats = AgentStats()

    def hashes(self) -> dict[str, str | None]:
        result = {}
        for raw in self.policy.targets:
            path = self.workspace.resolve(raw)
            result[raw] = (
                hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                if path.is_file()
                else None
            )
        return result

    @property
    def changed(self) -> bool:
        now = self.hashes()
        changes = [now[p] is not None and now[p] != self.state.initial_hashes.get(p) for p in now]
        return all(changes) if self.policy.all_targets_changed else any(changes)

    def observe_test(self, result: ExecutionResult, passed: bool) -> None:
        self.state.canonical_passed = bool(result.ok and passed)
        self.state.tested_hashes = self.hashes()
        self.state.independent_passed = None
        self.state.independent_hashes = {}

    def observe_independent(self, result: ExecutionResult) -> None:
        try:
            outcome = IndependentOutcome.model_validate_json(result.content)
            passed = result.ok and outcome.passed
            summary = outcome.summary
        except ValueError:
            passed, summary = (
                False,
                "Independent check failed or returned invalid data; no success inferred.",
            )
        self.state.independent_tool_error = not result.ok
        self.state.independent_passed = passed
        self.state.independent_summary = summary
        self.state.independent_hashes = self.hashes()

    @property
    def needs_independent(self) -> bool:
        return (
            self.policy.require_independent
            and self.state.canonical_passed is True
            and self.state.tested_hashes == self.hashes()
            and self.state.independent_hashes != self.hashes()
        )

    def evaluate(self) -> tuple[VerificationStatus, list[str]]:
        current = self.hashes()
        missing = []
        if not self.changed:
            missing.append("actual_target_change")
        if self.state.canonical_passed is not True or self.state.tested_hashes != current:
            missing.append("observed_current_canonical_pass")
        if self.policy.require_independent and (
            self.state.independent_passed is not True or self.state.independent_hashes != current
        ):
            missing.append("observed_current_independent_pass")
        failed = (self.state.canonical_passed is False and self.state.tested_hashes == current) or (
            self.policy.require_independent
            and self.state.independent_passed is False
            and self.state.independent_hashes == current
        )
        status = (
            VerificationStatus.SUCCESS
            if not missing
            else VerificationStatus.FAILURE
            if failed
            else VerificationStatus.UNVERIFIED
        )
        self.state.status = status
        return status, missing

    def feedback(self) -> str:
        status, missing = self.evaluate()
        return json.dumps(
            {
                "status": status,
                "missing": missing,
                "independent_failure": self.state.independent_summary
                if self.state.independent_passed is False
                else "",
                "hint": "Read observed source/tests, make an actual authorized target change, repair observed failures and verify. A textual completion is not verified success.",
            }
        )
