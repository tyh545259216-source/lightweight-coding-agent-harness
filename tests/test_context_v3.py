"""V3 pins real recent source/map/failure groups while preserving bounded pairs."""

import json

import pytest

from mini_harness.context.budget import TokenBudget
from mini_harness.context.manager import (
    ContextLimitError,
    ContextManager,
    ContextMode,
    message_groups,
)
from mini_harness.providers.base import Message, ToolCall


def exchange(key, name, payload, args=None):
    return [
        Message(role="assistant", tool_calls=[ToolCall(id=key, name=name, arguments=args or {})]),
        Message(
            role="tool",
            name=name,
            tool_call_id=key,
            content=json.dumps(
                {"call_id": key, "name": name, "ok": True, "content": json.dumps(payload)}
            ),
        ),
    ]


def history():
    rows = [
        Message(role="system", content="Trusted rules"),
        Message(role="user", content="Fix observed code"),
    ]
    rows += exchange("map", "repository_map", {"files": [{"path": "src/code.py"}]})
    rows += exchange(
        "read",
        "read_file",
        {
            "path": "src/code.py",
            "content": "def inc(x): return x+2",
            "total_lines": 1,
            "sha256": "0" * 64,
        },
        {"path": "src/code.py"},
    )
    rows += exchange(
        "test",
        "run_tests",
        {"exit_code": 1, "stdout": "FAILED test_inc", "passed": False},
        {"paths": ["."]},
    )
    for i in range(10):
        rows += exchange(str(i), "list_dir", {"entries": ["old"]}, {"path": "."})
    return rows


def test_real_source_map_and_failure_survive_old_listing_pressure():
    rows = history()
    original = [m.model_dump() for m in rows]
    manager = ContextManager(
        TokenBudget(max_tokens=4000, reserve_output=200, summary_chars=0),
        mode=ContextMode.MANAGED_V3,
        recent_exchanges=1,
        inspection=True,
    )
    result = manager.prepare(rows, [])
    names = [m.name for m in result if m.role == "tool"]
    assert {"repository_map", "read_file", "run_tests"} <= set(names)
    assert manager.dropped_groups > 0 and manager.last_estimate <= manager.budget.input_limit
    message_groups(result)
    assert original == [m.model_dump() for m in rows]
    assert (
        manager.last_inspection["dropped_messages"] and manager.last_inspection["retained_messages"]
    )
    assert manager.last_inspection["estimate_unit"] == "UTF-8 serialized byte proxy"


def test_active_skill_priority_and_inspection_are_not_terminal_output(capsys):
    manager = ContextManager(mode=ContextMode.MANAGED_V3, inspection=True)
    manager.set_skills({"demo": "Keep API"})
    result = manager.prepare(history(), [])
    assert any(m.name == "harness_skill" for m in result)
    assert capsys.readouterr().out == ""


def test_pinned_evidence_overflow_fails_closed():
    manager = ContextManager(
        TokenBudget(max_tokens=1000, reserve_output=200, summary_chars=0),
        mode=ContextMode.MANAGED_V3,
        inspection=True,
    )
    with pytest.raises(ContextLimitError):
        manager.prepare(history(), [])
    assert "safe stop" in manager.last_inspection["reason"]


def test_structured_read_content_is_bounded_with_honest_marker():
    rows = [
        Message(role="system", content="rules"),
        Message(role="user", content="read"),
    ] + exchange(
        "r", "read_file", {"content": "x" * 5000, "total_lines": 1, "start_line": 1, "end_line": 1}
    )
    manager = ContextManager(TokenBudget(tool_output_chars=200), mode=ContextMode.MANAGED_V3)
    result = manager.prepare(rows, [])
    data = json.loads(json.loads(result[-1].content)["content"])
    assert data["content_truncated"] and len(data["content"]) <= 200
    assert data["total_lines"] == 1


def test_repeated_policy_feedback_only_keeps_latest_system_requirement():
    rows = [Message(role="system", content="rules"), Message(role="user", content="fix")]
    rows += [
        Message(role="system", name="harness_observation", content=f"Feedback{i}") for i in range(5)
    ]
    rows += [Message(role="assistant", content="next")]
    result = ContextManager(mode=ContextMode.MANAGED_V3).prepare(rows, [])
    assert [m.content for m in result if m.name == "harness_observation"] == ["Feedback4"]
