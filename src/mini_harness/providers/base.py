"""Typed wire-independent conversation protocol."""

from typing import Any, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field


class ToolCall(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    arguments: dict[str, Any] | str = Field(default_factory=dict)


class Message(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    tool_call_id: str | None = None
    name: str | None = None


class ToolDefinition(BaseModel):
    name: str
    description: str
    parameters: dict[str, Any]

    def wire(self) -> dict[str, Any]:
        return {"type": "function", "function": self.model_dump()}


class Usage(BaseModel):
    prompt_tokens: int = Field(default=0, ge=0)
    completion_tokens: int = Field(default=0, ge=0)
    source: Literal["provider", "estimated", "unavailable"] = "unavailable"

    def add(self, other: "Usage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        if self.source == "unavailable":
            self.source = other.source
        elif self.source != other.source:
            self.source = "estimated"


class ModelResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    usage: Usage = Field(default_factory=Usage)


class ProviderError(RuntimeError):
    """Transport, protocol, or model failure (no automatic retries)."""


class Provider(Protocol):
    model: str

    async def complete(
        self, messages: list[Message], tools: list[ToolDefinition]
    ) -> ModelResponse: ...
