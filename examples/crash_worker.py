"""Process-level fault injection, confined to a caller-supplied temporary workspace."""

import asyncio
import os
import sys
from pathlib import Path

from mini_harness.agent.runner import AgentRunner
from mini_harness.providers.base import ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission, PermissionPolicy
from mini_harness.session.store import SessionStore
from mini_harness.tools.base import BaseTool, InputModel
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry


class Effect(BaseTool[InputModel]):
    name, description, input_model = "effect", "Fault injection counter write", InputModel
    permission, side_effect = Permission.WRITE, True

    def __init__(self, workspace: Path, mode: str) -> None:
        self.workspace, self.mode = workspace, mode

    async def execute(self, arguments: InputModel) -> str:
        (self.workspace / "counter.txt").write_text("1", encoding="utf-8")
        if self.mode == "uncertain":
            os._exit(91)
        return "written"


class CrashStore(SessionStore):
    def append(self, event, data):
        super().append(event, data)
        if event == "execution_completed":
            os._exit(92)


async def main() -> None:
    root = Path(sys.argv[1])
    mode = sys.argv[2]
    store = (CrashStore if mode == "committed" else SessionStore)(root / "session.jsonl")
    registry = ToolRegistry()
    registry.register(Effect(root, mode))
    executor = ToolExecutor(registry, PermissionPolicy({Permission.WRITE}), store)
    provider = FakeProvider([ModelResponse(tool_calls=[ToolCall(id="effect", name="effect")])])
    await AgentRunner(provider, executor, session=store).run("write counter once")


if __name__ == "__main__":
    asyncio.run(main())
