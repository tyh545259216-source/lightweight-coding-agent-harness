"""Execution statistics are separate from model messages."""

from pydantic import BaseModel, Field

from mini_harness.providers.base import Usage


class AgentStats(BaseModel):
    no_op_edits: int = 0
    stale_edits: int = 0
    patch_attempts: int = 0
    patch_successes: int = 0
    recovered_argument_errors: int = 0
    repeated_invalid_calls: int = 0
    invalid_path_calls: int = 0
    policy_violations: int = 0
    premature_finals: int = 0
    edits_before_read: int = 0
    replanning_count: int = 0
    model_rounds: int = 0
    tool_calls: int = 0
    tool_successes: int = 0
    tool_errors: int = 0
    argument_errors: int = 0
    permission_denials: int = 0
    initial_patch_success: bool | None = None
    repair_rounds: int = 0
    final_test_success: bool | None = None
    verification_tool_calls: int = 0
    latency_seconds: float = 0
    usage: Usage = Field(default_factory=Usage)
