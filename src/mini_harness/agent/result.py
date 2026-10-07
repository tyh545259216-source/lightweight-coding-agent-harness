from pydantic import BaseModel, Field

from mini_harness.agent.completion import VerificationStatus
from mini_harness.agent.state import AgentStats
from mini_harness.agent.stopping import StopReason
from mini_harness.providers.base import Message


class AgentResult(BaseModel):
    turn_id: str
    answer: str = ""
    stop_reason: StopReason
    error: str | None = None
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    stats: AgentStats = Field(default_factory=AgentStats)
    messages: list[Message] = Field(default_factory=list)
