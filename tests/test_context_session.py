import pytest

from mini_harness.agent.runner import AgentRunner
from mini_harness.context.budget import TokenBudget, estimate_messages
from mini_harness.context.manager import ContextLimitError, ContextManager, message_groups
from mini_harness.providers.base import Message, ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.session.store import SessionCorruptError, SessionStore


def exchange(id="1", text="result"):
    return [
        Message(role="assistant", tool_calls=[ToolCall(id=id, name="read_file")]),
        Message(role="tool", tool_call_id=id, content=text),
    ]


def test_compaction_atomic():
    history = [
        Message(role="system", content="instructions"),
        Message(role="user", content="old task"),
        *exchange(text="x" * 300),
        Message(role="assistant", content="y" * 300),
        Message(role="user", content="new task"),
        *exchange("2"),
    ]
    manager = ContextManager(TokenBudget(max_tokens=1200, reserve_output=100, summary_chars=100))
    projected = manager.prepare(history, [])
    assert manager.dropped_groups > 0
    assert estimate_messages(projected, []) <= 1100
    assert "new task" in [m.content for m in projected]
    assert history[3].content == "x" * 300
    message_groups(projected)


def test_tool_truncation():
    history = [Message(role="user", content="task"), *exchange(text="x" * 10000)]
    result = ContextManager(TokenBudget(tool_output_chars=64)).prepare(history, [])
    assert "truncated" in result[-1].content and history[-1].content == "x" * 10000


@pytest.mark.parametrize(
    "messages",
    [
        [Message(role="tool", tool_call_id="x")],
        [Message(role="assistant", tool_calls=[ToolCall(id="x", name="a")])],
        [
            Message(role="assistant", tool_calls=[ToolCall(id="x", name="a")]),
            Message(role="tool", tool_call_id="other"),
        ],
    ],
)
def test_bad_groups(messages):
    with pytest.raises(ContextLimitError):
        message_groups(messages)


def test_pinned_overflow():
    with pytest.raises(ContextLimitError):
        ContextManager(TokenBudget(max_tokens=100, reserve_output=1)).prepare(
            [Message(role="user", content="x" * 500)], []
        )


def test_no_summary():
    m = ContextManager(TokenBudget(max_tokens=500, reserve_output=1), compact=False)
    m.prepare(
        [
            Message(role="user", content="old"),
            Message(role="assistant", content="x" * 600),
            Message(role="user", content="new"),
        ],
        [],
    )
    assert m.dropped_groups == 2 and not m.summary


def test_session_torn_tail(tmp_path):
    store = SessionStore(tmp_path / "session.jsonl")
    store.append("message", {"role": "user", "content": "中文"})
    with store.path.open("ab") as h:
        h.write(b'{"event":')
    assert len(store.load()) == 1
    store.append("terminal", {"reason": "final"})
    assert len(store.load()) == 2
    assert all("timestamp" in r for r in store.load())


def test_interior_corruption(tmp_path):
    store = SessionStore(tmp_path / "bad")
    store.path.write_bytes(b"bad\n")
    with pytest.raises(SessionCorruptError):
        store.load()
    with pytest.raises(SessionCorruptError):
        store.append("x", {})


async def test_session_continue(tmp_path):
    store = SessionStore(tmp_path / "s")
    await AgentRunner(FakeProvider([ModelResponse(content="first")]), session=store).run("hello")
    provider = FakeProvider([ModelResponse(content="second")])
    r = await AgentRunner(provider, session=store).run("continue")
    assert len(r.messages) == 5
    assert provider.requests[0][0][1].content == "hello"
    assert store.load()[-1]["event"] == "terminal"


async def test_context_limit_stop():
    r = await AgentRunner(
        FakeProvider([]), context=ContextManager(TokenBudget(max_tokens=100, reserve_output=1))
    ).run("x" * 500)
    assert r.stop_reason.value == "context_limit"


@pytest.mark.parametrize(
    "envelope",
    [
        {"event": 3, "timestamp": "2026-10-04T00:00:00+00:00", "data": {}},
        {"event": "message", "timestamp": "not-a-date", "data": {}},
        {"event": "message", "timestamp": "2026-10-04T00:00:00+00:00", "data": []},
    ],
)
def test_semantically_corrupt_session_rejected(tmp_path, envelope):
    import json

    store = SessionStore(tmp_path / "session")
    store.path.write_text(json.dumps(envelope) + "\n", encoding="utf-8")
    with pytest.raises(SessionCorruptError):
        store.load()
