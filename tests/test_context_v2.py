import json

import pytest

from mini_harness.context.budget import TokenBudget, estimate_messages
from mini_harness.context.manager import (
    ContextLimitError,
    ContextManager,
    ContextMode,
    message_groups,
)
from mini_harness.providers.base import Message, ToolCall


def pair(id, name="read_file", path="module.py", payload="data", ok=True):
    return [
        Message(
            role="assistant",
            tool_calls=[
                ToolCall(
                    id=id,
                    name=name,
                    arguments={"path": path} if name != "run_tests" else {"paths": ["tests"]},
                )
            ],
        ),
        Message(
            role="tool",
            tool_call_id=id,
            name=name,
            content=json.dumps(
                {"ok": ok, "content": payload, "error_type": None if ok else "arguments"}
            ),
        ),
    ]


def test_raw_budget_and_naive_exchange_integrity():
    history = [
        Message(role="system", content="rules"),
        Message(role="user", content="old"),
        *pair("old", payload="x" * 4000),
        Message(role="user", content="new"),
        *pair("new"),
    ]
    budget = TokenBudget(max_tokens=1600, reserve_output=100, tool_output_chars=1000)
    with pytest.raises(ContextLimitError, match="Uncompacted"):
        ContextManager(budget, mode=ContextMode.NO_COMPACTION).prepare(history, [])
    result = ContextManager(budget, mode=ContextMode.NAIVE_TRUNCATION).prepare(history, [])
    message_groups(result)
    assert [c.id for m in result for c in m.tool_calls] == ["new"]
    assert estimate_messages(result, []) <= 1500
    assert not any(m.name == "harness_summary" for m in result)


def test_managed_retains_recent_and_execution_evidence():
    history = [
        Message(role="system", content="rules"),
        Message(role="user", content="fix"),
        *pair("write", "edit_file", "src/calc.py", "edited"),
        *pair(
            "fail",
            "run_tests",
            payload=json.dumps(
                {
                    "exit_code": 1,
                    "passed": False,
                    "stdout": "F" * 3000 + "AssertionError: expected 3",
                    "stderr": "",
                }
            ),
        ),
        *pair("noise1", payload="x" * 2000),
        *pair("noise2", payload="y" * 2000),
    ]
    manager = ContextManager(
        TokenBudget(max_tokens=2200, reserve_output=100, tool_output_chars=200, summary_chars=200)
    )
    result = manager.prepare(history, [])
    message_groups(result)
    ids = [c.id for m in result for c in m.tool_calls]
    assert "noise1" in ids and "noise2" in ids and "write" not in ids
    state = next(m.content for m in result if m.name == "harness_state")
    assert "src/calc.py" in state and '"exit_code": 1' in state and '"passed": false' in state
    assert "F" * 3000 in history[5].content


def test_structured_test_tail_survives_truncation():
    history = [
        Message(role="user", content="task"),
        *pair(
            "test",
            "run_tests",
            payload=json.dumps(
                {
                    "exit_code": 5,
                    "passed": False,
                    "stdout": "x" * 4000 + "NO TESTS COLLECTED",
                    "stderr": "",
                }
            ),
        ),
    ]
    result = ContextManager(TokenBudget(tool_output_chars=100)).prepare(history, [])
    payload = json.loads(json.loads(result[-1].content)["content"])
    assert payload["exit_code"] == 5 and payload["passed"] is False
    assert payload["stdout"].endswith("NO TESTS COLLECTED") and len(payload["stdout"]) == 100


def test_skills_and_current_feedback_have_priority():
    manager = ContextManager(TokenBudget(max_tokens=2500, reserve_output=100, summary_chars=100))
    manager.set_skills({"python-testing": "Write collected tests; preserve API."})
    history = [
        Message(role="system", content="security rules"),
        Message(role="system", name="harness_verification", content="old feedback"),
        Message(role="user", content="task"),
        Message(role="assistant", content="old" * 1200),
        Message(role="system", name="harness_verification", content="current feedback"),
    ]
    result = manager.prepare(history, [])
    text = "\n".join(m.content for m in result)
    assert (
        "security rules" in text and "Write collected tests" in text and "current feedback" in text
    )
    assert "old feedback" not in text
    manager.set_skills({"too-large": "z" * 4000})
    with pytest.raises(ContextLimitError):
        manager.prepare(history, [])


def test_rolling_summary_tracks_new_dropped_facts_without_duplicates():
    manager = ContextManager(
        TokenBudget(max_tokens=1300, reserve_output=100, summary_chars=180), recent_exchanges=0
    )
    history = [
        Message(role="user", content="old"),
        Message(role="assistant", content="FIRST " + "x" * 1800),
        Message(role="user", content="task"),
        Message(role="assistant", content="current"),
    ]
    manager.prepare(history, [])
    assert "FIRST" in manager.summary
    old_facts = list(manager._summary_facts)
    manager.prepare(history, [])
    assert manager._summary_facts == old_facts
    history.extend(
        [
            Message(role="assistant", content="SECOND " + "y" * 1800),
            Message(role="user", content="latest"),
            Message(role="assistant", content="done"),
        ]
    )
    manager.prepare(history, [])
    assert "SECOND" in manager.summary and len(manager.summary) <= 180


def test_recent_exchange_is_pinned_even_when_it_cannot_fit():
    manager = ContextManager(TokenBudget(max_tokens=800, reserve_output=100), recent_exchanges=2)
    with pytest.raises(ContextLimitError, match="Pinned"):
        manager.prepare(
            [Message(role="user", content="task"), *pair("one", payload="x" * 1000), *pair("two")],
            [],
        )
