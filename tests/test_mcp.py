import sys
from pathlib import Path

import pytest

from mini_harness.mcp.client import MCPClient, MCPError, reject_remote_refs
from mini_harness.providers.base import ToolCall
from mini_harness.security.permissions import Permission
from mini_harness.tools.executor import ToolExecutor
from mini_harness.tools.registry import ToolRegistry

SERVER = Path(__file__).resolve().parents[1] / "examples" / "mcp_server.py"


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("normal", None),
        ("tool-error", "execution"),
        ("rpc-error", "execution"),
        ("malformed", "execution"),
        ("slow", "execution"),
    ],
)
async def test_real_stdio(mode, expected):
    async with MCPClient([sys.executable, str(SERVER), mode], label="test", timeout=10) as client:
        registry = ToolRegistry()
        assert await client.register_tools(registry, {"echo": Permission.READ}) == [
            "mcp__test__echo"
        ]
        executor = ToolExecutor(registry)
        bad = await executor.execute(
            ToolCall(id="bad", name="mcp__test__echo", arguments={"text": 1}), "bad"
        )
        assert bad.error_type == "arguments"
        if mode == "slow":
            client.timeout = 0.2
        result = await executor.execute(
            ToolCall(id="good", name="mcp__test__echo", arguments={"text": "hello"}), "good"
        )
        assert result.error_type == expected
        if expected is None:
            assert "hello" in result.content


async def test_remote_defaults_dangerous():
    async with MCPClient([sys.executable, str(SERVER)]) as client:
        registry = ToolRegistry()
        await client.register_tools(registry)
        result = await ToolExecutor(registry).execute(
            ToolCall(id="x", name="mcp__external__echo", arguments={"text": "x"}), "x"
        )
        assert result.error_type == "permission"


async def test_version_rejected_and_closed():
    client = MCPClient([sys.executable, str(SERVER), "unsupported"])
    with pytest.raises(MCPError):
        await client.connect()
    assert client.process is None


async def test_duplicate_namespace():
    async with MCPClient([sys.executable, str(SERVER)]) as client:
        registry = ToolRegistry()
        await client.register_tools(registry)
        with pytest.raises(MCPError):
            await client.register_tools(registry)


def test_remote_refs_rejected():
    with pytest.raises(MCPError):
        reject_remote_refs({"properties": {"x": {"$ref": "https://example.com/schema"}}})
    reject_remote_refs({"$ref": "#/$defs/x"})


async def test_not_connected():
    with pytest.raises(MCPError):
        await MCPClient(["unused"]).request("tools/list", {})


@pytest.mark.parametrize("kind", ["$dynamicRef", "$recursiveRef"])
def test_other_remote_schema_refs_rejected(kind):
    with pytest.raises(MCPError):
        reject_remote_refs({kind: "file:///outside"})


def test_long_mcp_tool_names_fit_provider_limit():
    from mini_harness.mcp.client import MCPTool

    client = MCPClient(["unused"], label="label" * 6)
    tool = MCPTool(client, {"name": "x" * 64, "inputSchema": {"type": "object"}}, Permission.READ)
    assert len(tool.name) == 64 and tool.remote_name == "x" * 64
    assert tool.definition().name == tool.name
