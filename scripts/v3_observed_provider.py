"""Observe unchanged non-streaming requests; HTTP chunks are never called model tokens."""

import asyncio
import json
import os
import time
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import httpx

from mini_harness.providers.openai_compatible import OpenAICompatibleProvider

UNAVAILABLE = "UNAVAILABLE"


def utc():
    return datetime.now(UTC).isoformat()


def durable_jsonl(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(value, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


class ObservedStream(httpx.AsyncByteStream):
    def __init__(self, original, observation, start):
        self.original, self.observation, self.start = original, observation, start
        self.buffer = bytearray()

    async def __aiter__(self):
        async for chunk in self.original:
            if chunk and self.observation["first_response_body_chunk"] == UNAVAILABLE:
                self.observation["first_response_body_chunk"] = utc()
                self.observation["first_chunk_latency"] = time.perf_counter() - self.start
            self.observation["body_bytes_observed"] += len(chunk)
            if len(self.buffer) + len(chunk) <= 4 * 1024 * 1024:
                self.buffer.extend(chunk)
            yield chunk
        self.observation["response_body_end"] = utc()
        self.observation["full_http_body_latency"] = time.perf_counter() - self.start
        try:
            packet = json.loads(self.buffer)
            message = packet["choices"][0]["message"]
            self.observation["finish_reason"] = packet["choices"][0].get(
                "finish_reason", UNAVAILABLE
            )
            self.observation["wire_message_fields"] = sorted(message)
            self.observation["wire_content_characters"] = (
                len(message.get("content") or "")
                if isinstance(message.get("content") or "", str)
                else UNAVAILABLE
            )
            self.observation["wire_usage"] = packet.get("usage") or UNAVAILABLE
            self.observation["reasoning_fields"] = {
                key: {
                    "characters": len(message[key])
                    if isinstance(message[key], str)
                    else UNAVAILABLE
                }
                for key in ["reasoning_content", "reasoning", "thinking"]
                if key in message
            } or UNAVAILABLE
            self.observation["content_contains_think_marker"] = "<think>" in (
                message.get("content") or ""
            )
        except (ValueError, KeyError, IndexError, TypeError):
            self.observation["packet_metadata"] = UNAVAILABLE

    async def aclose(self):
        await self.original.aclose()


class ObservedTransport(httpx.AsyncHTTPTransport):
    current = None
    start = None

    async def handle_async_request(self, request):
        response = await super().handle_async_request(request)
        if self.current is not None and request.url.path.endswith("/chat/completions"):
            self.current["response_headers_received"] = utc()
            self.current["response_headers_latency"] = time.perf_counter() - self.start
            response.stream = ObservedStream(response.stream, self.current, self.start)
        return response


class ObservedProvider(OpenAICompatibleProvider):
    def __init__(self, base_url, model, path: Path, *, timeout=90):
        self.observations_path = path
        self.observed_transport = ObservedTransport(trust_env=False)
        client = httpx.AsyncClient(
            transport=self.observed_transport,
            timeout=timeout,
            headers={"Authorization": "Bearer ollama"},
            trust_env=False,
        )
        super().__init__(base_url, model, max_tokens=512, reasoning_effort="none", client=client)
        self._owns_client = True

    async def complete(self, messages, tools):
        start = time.perf_counter()
        row = {
            "request_id": uuid4().hex,
            "observation_format_version": 2,
            "model": self.model,
            "request_start": utc(),
            "request_end": UNAVAILABLE,
            "first_response_body_chunk": UNAVAILABLE,
            "first_chunk_latency": UNAVAILABLE,
            "first_token_time": UNAVAILABLE,
            "ttft": UNAVAILABLE,
            "tool_call_complete": UNAVAILABLE,
            "time_to_complete_tool_call": UNAVAILABLE,
            "final_response_complete": UNAVAILABLE,
            "full_response_latency": UNAVAILABLE,
            "response_body_end": UNAVAILABLE,
            "body_bytes_observed": 0,
            "stream_requested": False,
            "max_output_tokens_requested": 512,
            "reasoning_effort_requested": "none",
            "native_think_parameter_sent": False,
            "reasoning_tokens": UNAVAILABLE,
            "tokens_per_second": UNAVAILABLE,
            "first_token_limit": "Non-streaming HTTP body chunks are not generated model tokens; no body before cancellation does not prove server generated zero tokens.",
        }
        self.observed_transport.current = row
        self.observed_transport.start = start
        try:
            result = await super().complete(messages, tools)
            elapsed = time.perf_counter() - start
            row["full_response_latency"] = elapsed
            row["parsed_response_kind"] = (
                "TOOL_CALL"
                if result.tool_calls
                else "FINAL_TEXT"
                if result.content.strip()
                else "EMPTY_RESPONSE"
            )
            row["has_parsed_decision"] = bool(result.tool_calls or result.content.strip())
            if result.tool_calls:
                row["tool_call_complete"] = utc()
                row["time_to_complete_tool_call"] = elapsed
                row["tool_names"] = [call.name for call in result.tool_calls]
            elif result.content.strip():
                row["final_response_complete"] = utc()
            if result.usage.source == "provider":
                row["observed_prompt_tokens"] = result.usage.prompt_tokens
                row["observed_completion_tokens"] = result.usage.completion_tokens
                row["end_to_end_reported_completion_tokens_per_second"] = (
                    result.usage.completion_tokens / elapsed
                )
                usage = row.get("wire_usage")
                if isinstance(usage, dict):
                    details = usage.get("completion_tokens_details")
                    if isinstance(details, dict):
                        row["reasoning_tokens"] = details.get("reasoning_tokens", UNAVAILABLE)
            row["status"] = "COMPLETE"
            return result
        except asyncio.CancelledError:
            row["status"] = "CANCELLED_BY_RUNTIME"
            raise
        except Exception as exc:
            row["status"] = "ERROR"
            row["error_type"] = type(exc).__name__
            raise
        finally:
            row["request_end"] = utc()
            row["request_elapsed_seconds"] = time.perf_counter() - start
            if row["status"] == "COMPLETE":
                row["response_timeout_observation"] = "NOT_APPLICABLE_COMPLETE_RESPONSE"
            elif row.get("response_body_end", UNAVAILABLE) != UNAVAILABLE:
                row["response_timeout_observation"] = "COMPLETE_HTTP_BODY_WITH_RESPONSE_ERROR"
            elif row["body_bytes_observed"]:
                row["response_timeout_observation"] = "PARTIAL_HTTP_BODY_RECEIVED"
            else:
                row["response_timeout_observation"] = "NO_HTTP_BODY_OBSERVED"
            durable_jsonl(self.observations_path, row)
            self.observed_transport.current = None
