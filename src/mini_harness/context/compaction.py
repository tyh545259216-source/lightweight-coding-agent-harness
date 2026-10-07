"""Lossy deterministic extractive summary; never pretend it is full history."""

from mini_harness.providers.base import Message


def summarize(messages: list[Message], limit: int) -> str:
    snippets = []
    for message in messages:
        names = ",".join(c.name for c in message.tool_calls)
        snippets.append(f"{message.role} {names}: {message.content[:160]}")
    return ("[Lossy history summary; re-read files to verify facts]\n" + "\n".join(snippets))[
        :limit
    ]
