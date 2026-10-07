"""Scripted provider for deterministic harness regression; not a simulated intelligence score."""

import asyncio
from collections.abc import Sequence

from mini_harness.providers.base import Message, ModelResponse, ProviderError, ToolDefinition


class FakeProvider:
    model = "fake-scripted"

    def __init__(self, responses: Sequence[ModelResponse | Exception], delay: float = 0) -> None:
        self.responses = list(responses)
        self.requests: list[tuple[list[Message], list[ToolDefinition]]] = []
        self.delay = delay

    async def complete(self, messages: list[Message], tools: list[ToolDefinition]) -> ModelResponse:
        self.requests.append(([m.model_copy(deep=True) for m in messages], tools.copy()))
        if self.delay:
            await asyncio.sleep(self.delay)
        if not self.responses:
            raise ProviderError("FakeProvider script exhausted")
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response.model_copy(deep=True)
