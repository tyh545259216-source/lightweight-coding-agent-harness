"""python examples/mcp_demo.py: actual stdio MCP call routed through AgentRunner."""

import asyncio
import sys
from pathlib import Path

from mini_harness.agent.runner import AgentRunner
from mini_harness.mcp.client import MCPClient
from mini_harness.providers.base import ModelResponse, ToolCall
from mini_harness.providers.fake import FakeProvider
from mini_harness.security.permissions import Permission
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry


async def demo() -> None:
    async with MCPClient(
        [sys.executable, str(Path(__file__).with_name("mcp_server.py"))], label="demo"
    ) as client:
        registry = ToolRegistry()
        await client.register_tools(registry, {"echo": Permission.READ})
        provider = FakeProvider(
            [
                ModelResponse(
                    tool_calls=[
                        ToolCall(
                            id="1",
                            name="mcp__demo__echo",
                            arguments={"text": "MCP → unified registry → agent loop"},
                        )
                    ]
                ),
                ModelResponse(content="MCP tool completed."),
            ]
        )
        result = await AgentRunner(provider, ToolExecutor(registry)).run("Echo with MCP")
        print(result.model_dump_json(indent=2))


if __name__ == "__main__":
    asyncio.run(demo())
