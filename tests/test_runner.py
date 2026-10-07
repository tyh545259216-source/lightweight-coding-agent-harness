import asyncio

import pytest

from mini_harness.agent.runner import AgentRunner, ExecutionResult, RunnerConfig
from mini_harness.agent.stopping import StopReason
from mini_harness.providers.base import ModelResponse, ProviderError, ToolCall, Usage
from mini_harness.providers.fake import FakeProvider


class EchoExecutor:
    def definitions(self):
        return []

    async def execute(self, call, key):
        return ExecutionResult(
            call_id=call.id,
            name=call.name,
            ok=call.name != "bad",
            content="echo",
            error_type="execution" if call.name == "bad" else None,
        )


def response(name="echo", id="1"):
    return ModelResponse(tool_calls=[ToolCall(id=id, name=name)])


@pytest.mark.parametrize("calls", [0, 1, 3])
async def test_loop(calls):
    p = FakeProvider(
        [
            *[response(id=str(i)) for i in range(calls)],
            ModelResponse(
                content="done", usage=Usage(prompt_tokens=4, completion_tokens=2, source="provider")
            ),
        ]
    )
    r = await AgentRunner(p, EchoExecutor()).run("task")
    assert r.stop_reason == StopReason.FINAL
    assert r.stats.tool_calls == calls
    assert r.stats.model_rounds == calls + 1
    assert r.stats.usage.prompt_tokens == 4
    assert len(r.messages) == 3 + 2 * calls


async def test_tool_error_can_be_corrected():
    r = await AgentRunner(
        FakeProvider([response("bad"), ModelResponse(content="recovered")]), EchoExecutor()
    ).run("task")
    assert r.stats.tool_errors == 1 and r.answer == "recovered"


async def test_iteration_bound():
    r = await AgentRunner(
        FakeProvider([response()] * 3), EchoExecutor(), RunnerConfig(max_iterations=2)
    ).run("task")
    assert r.stop_reason == StopReason.MAX_ITERATIONS and r.stats.model_rounds == 2


@pytest.mark.parametrize(
    "script,reason",
    [
        ([ProviderError("offline")], StopReason.PROVIDER_ERROR),
        ([ModelResponse()], StopReason.EMPTY_RESPONSE),
    ],
)
async def test_failure(script, reason):
    assert (await AgentRunner(FakeProvider(script)).run("task")).stop_reason == reason


async def test_missing_executor():
    r = await AgentRunner(FakeProvider([response(), ModelResponse(content="done")])).run("task")
    assert r.stats.tool_errors == 1


async def test_duplicate_call_ids():
    r = await AgentRunner(
        FakeProvider([ModelResponse(tool_calls=[ToolCall(id="x", name="a")] * 2)])
    ).run("task")
    assert r.stop_reason == StopReason.MALFORMED_RESPONSE


async def test_timeout():
    r = await AgentRunner(
        FakeProvider([ModelResponse(content="late")], delay=0.1),
        config=RunnerConfig(model_timeout=0.01),
    ).run("task")
    assert r.stop_reason == StopReason.TIMEOUT


async def test_cancellation():
    task = asyncio.create_task(
        AgentRunner(FakeProvider([ModelResponse(content="late")], delay=1)).run("task")
    )
    await asyncio.sleep(0.01)
    task.cancel()
    assert (await task).stop_reason == StopReason.CANCELLED


async def test_fake_exhaustion():
    with pytest.raises(ProviderError):
        await FakeProvider([]).complete([], [])
