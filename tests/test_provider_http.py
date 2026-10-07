import json

import httpx
import pytest

from mini_harness.providers.base import Message, ProviderError, ToolCall, ToolDefinition
from mini_harness.providers.openai_compatible import OpenAICompatibleProvider, wire_message


async def test_wire_roundtrip_with_mock_http():
    requests = []

    def handler(request):
        requests.append(json.loads(request.content))
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "message": {
                            "content": None,
                            "tool_calls": [
                                {
                                    "id": "1",
                                    "type": "function",
                                    "function": {
                                        "name": "read_file",
                                        "arguments": '{"path":"app.py"}',
                                    },
                                }
                            ],
                        }
                    }
                ],
                "usage": {"prompt_tokens": 11, "completion_tokens": 5},
            },
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        provider = OpenAICompatibleProvider(client=client)
        response = await provider.complete(
            [Message(role="user", content="read")],
            [ToolDefinition(name="read_file", description="read", parameters={"type": "object"})],
        )
    assert (
        response.tool_calls[0].arguments == '{"path":"app.py"}'
        and response.usage.source == "provider"
    )
    assert requests[0]["tools"][0]["function"]["name"] == "read_file"
    assert requests[0]["temperature"] == 0


@pytest.mark.parametrize(
    "packet",
    [
        {},
        {"choices": []},
        {"choices": [{"message": {"tool_calls": [{"function": {"name": "x", "arguments": []}}]}}]},
    ],
)
async def test_malformed_http(packet):
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=packet))
    ) as client:
        with pytest.raises(ProviderError):
            await OpenAICompatibleProvider(client=client).complete([], [])


async def test_network_failure():
    def broken(request):
        raise httpx.ConnectError("offline", request=request)

    async with httpx.AsyncClient(transport=httpx.MockTransport(broken)) as client:
        with pytest.raises(ProviderError):
            await OpenAICompatibleProvider(client=client).complete([], [])


async def test_missing_usage_and_id():
    packet = {
        "choices": [
            {
                "message": {
                    "content": "",
                    "tool_calls": [{"function": {"name": "x", "arguments": "bad json"}}],
                }
            }
        ]
    }
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda r: httpx.Response(200, json=packet))
    ) as client:
        response = await OpenAICompatibleProvider(client=client).complete([], [])
        assert response.tool_calls[0].id and response.usage.source == "unavailable"


async def test_model_discovery():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(
            lambda r: httpx.Response(200, json={"data": [{"id": "qwen3:1.7b"}]})
        )
    ) as client:
        await OpenAICompatibleProvider(client=client).check_model()
        with pytest.raises(ProviderError):
            await OpenAICompatibleProvider(model="missing", client=client).check_model()


def test_correlated_tool_wire():
    assistant = Message(
        role="assistant", tool_calls=[ToolCall(id="1", name="x", arguments={"a": 1})]
    )
    assert json.loads(wire_message(assistant)["tool_calls"][0]["function"]["arguments"]) == {"a": 1}
    assert (
        wire_message(Message(role="tool", tool_call_id="1", content="result"))["tool_call_id"]
        == "1"
    )


async def test_null_message_and_reasoning_control():
    captured = []

    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={"choices": [{"message": None}]})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        with pytest.raises(ProviderError):
            await OpenAICompatibleProvider(client=client, reasoning_effort="none").complete([], [])
    assert captured[0]["reasoning_effort"] == "none"
