"""Conservative UTF-8 byte estimator; explicitly not model-token accounting."""

from pydantic import BaseModel, Field, model_validator

from mini_harness.providers.base import Message, ToolDefinition


class TokenBudget(BaseModel):
    max_tokens: int = Field(default=16384, ge=64)
    reserve_output: int = Field(default=1024, ge=0)
    tool_output_chars: int = Field(default=12000, ge=64)
    summary_chars: int = Field(default=1000, ge=0)

    @model_validator(mode="after")
    def valid(self) -> "TokenBudget":
        if self.reserve_output >= self.max_tokens:
            raise ValueError("Output reserve must be smaller than context limit")
        return self

    @property
    def input_limit(self) -> int:
        return self.max_tokens - self.reserve_output


def estimate_messages(messages: list[Message], tools: list[ToolDefinition]) -> int:
    return sum(len(m.model_dump_json().encode("utf-8")) + 8 for m in messages) + sum(
        len(t.model_dump_json().encode("utf-8")) + 8 for t in tools
    )
