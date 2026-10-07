import pytest

from mini_harness.agent.runner import AgentRunner, RunnerConfig
from mini_harness.context.budget import TokenBudget
from mini_harness.providers.base import Message, ModelResponse, ToolCall, Usage
from mini_harness.providers.fake import FakeProvider
from mini_harness.session.recovery import RecoveryBlocked
from mini_harness.session.store import SessionStore


def test_invalid_budget():
    with pytest.raises(ValueError):
        TokenBudget(max_tokens=100, reserve_output=100)


async def test_final_message_committed_before_terminal(tmp_path):
    store = SessionStore(tmp_path / "s")
    store.append("turn_started", {"turn_id": "turn", "task": "hello"})
    store.append(
        "message",
        {**Message(role="user", content="hello").model_dump(), "_turn_id": "turn", "_iteration": 0},
    )
    store.append("model_requested", {"iteration": 0})
    store.append(
        "model_received",
        {"usage": Usage(prompt_tokens=5, completion_tokens=1, source="provider").model_dump()},
    )
    store.append(
        "message", {**Message(role="assistant", content="done").model_dump(), "_iteration": 0}
    )
    p = FakeProvider([])
    result = await AgentRunner(p, session=store).resume()
    assert result.answer == "done" and not p.requests and result.stats.usage.prompt_tokens == 5
    with pytest.raises(RecoveryBlocked):
        await AgentRunner(p, session=store).resume()


async def test_turn_start_before_user_append(tmp_path):
    store = SessionStore(tmp_path / "s")
    store.append("message", Message(role="system", content="system").model_dump())
    store.append("turn_started", {"turn_id": "turn", "task": "recover lost append"})
    result = await AgentRunner(
        FakeProvider([ModelResponse(content="done")]), session=store
    ).resume()
    assert result.answer == "done"
    users = [e for e in store.load() if e["event"] == "message" and e["data"]["role"] == "user"]
    assert len(users) == 1 and users[0]["data"]["content"] == "recover lost append"


async def test_resume_cannot_increase_original_round_limit(tmp_path):
    store = SessionStore(tmp_path / "s")
    store.append(
        "turn_started", {"turn_id": "turn", "task": "task", "config": {"max_iterations": 1}}
    )
    store.append(
        "message",
        {**Message(role="user", content="task").model_dump(), "_turn_id": "turn", "_iteration": 0},
    )
    store.append("model_requested", {"iteration": 0})
    provider = FakeProvider([ModelResponse(content="should not request")])
    result = await AgentRunner(
        provider, config=RunnerConfig(max_iterations=10), session=store
    ).resume()
    assert result.stop_reason.value == "max_iterations" and not provider.requests


async def test_pending_cancel_blocks_new_task(tmp_path):
    store = SessionStore(tmp_path / "s")
    store.append("turn_started", {"turn_id": "turn", "task": "task"})
    store.append(
        "message",
        Message(role="assistant", tool_calls=[ToolCall(id="x", name="list_dir")]).model_dump(),
    )
    store.append("terminal", {"stop_reason": "cancelled"})
    with pytest.raises(RecoveryBlocked):
        await AgentRunner(FakeProvider([]), session=store).run("new")
