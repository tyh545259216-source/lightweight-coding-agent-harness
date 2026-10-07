"""Finite and auditable stopping conditions."""

from enum import StrEnum


class StopReason(StrEnum):
    POLICY_LIMIT = "policy_limit"
    FINAL = "final_answer"
    MAX_ITERATIONS = "max_iterations"
    PROVIDER_ERROR = "provider_error"
    EMPTY_RESPONSE = "empty_response"
    MALFORMED_RESPONSE = "malformed_response"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"
    CONTEXT_LIMIT = "context_limit"
    RECOVERY_BLOCKED = "recovery_blocked"
    REPAIR_LIMIT = "max_repair_rounds"
    VERIFICATION_FAILED = "verification_failed"
