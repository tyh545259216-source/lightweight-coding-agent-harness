"""HTTP-only OpenAI-compatible Chat Completions provider for local Ollama."""

import json
from typing import Any
from uuid import uuid4

import httpx
from pydantic import ValidationError

from mini_harness.providers.base import (
    Message,
    ModelResponse,
    ProviderError,
    ToolCall,
    ToolDefinition,
    Usage,
)


def wire_message(message: Message) -> dict[str, Any]:
    result: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_calls:
        result["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {
                    "name": call.name,
                    "arguments": json.dumps(call.arguments, ensure_ascii=False)
                    if isinstance(call.arguments, dict)
                    else call.arguments,
                },
            }
            for call in message.tool_calls
        ]
    if message.role == "tool":
        result["tool_call_id"] = message.tool_call_id
    return result


class OpenAICompatibleProvider:
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434/v1",
        model: str = "qwen3:1.7b",
        *,
        api_key: str = "ollama",
        max_tokens: int = 512,
        reasoning_effort: str | None = None,
        timeout: float = 90,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.base_url, self.model, self.max_tokens = base_url.rstrip("/"), model, max_tokens
        self.reasoning_effort = reasoning_effort
        self._owns_client = client is None
        self.client = client or httpx.AsyncClient(
            timeout=timeout, headers={"Authorization": f"Bearer {api_key}"}, trust_env=False
        )

    async def __aenter__(self) -> "OpenAICompatibleProvider":
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owns_client:
            await self.client.aclose()

    async def check_model(self) -> None:
        try:
            response = await self.client.get(self.base_url + "/models", timeout=5)
            response.raise_for_status()
            models = response.json()["data"]
            if not any(m["id"] == self.model for m in models):
                raise ProviderError(f"Model not installed: {self.model}")
        except (httpx.HTTPError, ValueError, KeyError, TypeError) as exc:
            raise ProviderError(f"Model discovery failed: {exc}") from exc

    async def complete(self, messages: list[Message], tools: list[ToolDefinition]) -> ModelResponse:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": [wire_message(m) for m in messages],
            "temperature": 0,
            "max_tokens": self.max_tokens,
            "stream": False,
        }
        if self.reasoning_effort is not None:
            payload["reasoning_effort"] = self.reasoning_effort
        if tools:
            payload["tools"] = [tool.wire() for tool in tools]
        try:
            response = await self.client.post(self.base_url + "/chat/completions", json=payload)
            response.raise_for_status()
            packet = response.json()
            message = packet["choices"][0]["message"]
            if not isinstance(message, dict):
                raise ValueError("Expected assistant message object")
            calls = []
            for call in message.get("tool_calls") or []:
                if call.get("type", "function") != "function":
                    raise ValueError("Unsupported tool call type")
                function = call["function"]
                calls.append(
                    ToolCall(
                        id=call.get("id") or uuid4().hex,
                        name=function["name"],
                        arguments=function.get("arguments", {}),
                    )
                )
            raw_usage = packet.get("usage") or {}
            reported = "prompt_tokens" in raw_usage and "completion_tokens" in raw_usage
            usage = Usage(
                prompt_tokens=raw_usage.get("prompt_tokens", 0),
                completion_tokens=raw_usage.get("completion_tokens", 0),
                source="provider" if reported else "unavailable",
            )
            return ModelResponse(
                content=message.get("content") or "", tool_calls=calls, usage=usage
            )
        except (
            httpx.HTTPError,
            ValueError,
            KeyError,
            IndexError,
            TypeError,
            ValidationError,
        ) as exc:
            raise ProviderError(f"Chat completion failed ({type(exc).__name__}): {exc}") from exc
