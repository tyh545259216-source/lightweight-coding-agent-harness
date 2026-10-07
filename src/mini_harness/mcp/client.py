"""Minimal legacy MCP 2025-06-18 stdio JSON-RPC client; one outstanding request."""

import asyncio
import hashlib
import json
import re
from typing import Any

from jsonschema import Draft202012Validator
from pydantic import RootModel

from mini_harness.providers.base import ToolDefinition
from mini_harness.security.permissions import Permission
from mini_harness.tools.base import BaseTool
from mini_harness.tools.registry import ToolRegistry


class MCPError(RuntimeError):
    pass


class ExternalArguments(RootModel[dict[str, Any]]):
    pass


def reject_remote_refs(value: Any) -> None:
    if isinstance(value, dict):
        if any(
            k in value and not str(value[k]).startswith("#")
            for k in ("$ref", "$dynamicRef", "$recursiveRef")
        ):
            raise MCPError("Remote JSON Schema references are forbidden")
        for child in value.values():
            reject_remote_refs(child)
    elif isinstance(value, list):
        for child in value:
            reject_remote_refs(child)


class MCPTool(BaseTool[ExternalArguments]):
    input_model = ExternalArguments
    side_effect = True  # never trust server readOnlyHint as authorization

    def __init__(self, client: "MCPClient", remote: dict[str, Any], permission: Permission) -> None:
        self.client, self.remote_name, self.permission = client, remote["name"], permission
        self.name = f"mcp__{client.label}__{self.remote_name}"
        if len(self.name) > 64:
            self.name = self.name[:53] + "_" + hashlib.sha256(self.name.encode()).hexdigest()[:10]
        self.description = str(remote.get("description", self.remote_name))
        self.schema = remote["inputSchema"]
        reject_remote_refs(self.schema)
        Draft202012Validator.check_schema(self.schema)
        self.validator = Draft202012Validator(self.schema)
        self.side_effect = permission != Permission.READ

    def definition(self) -> ToolDefinition:
        return ToolDefinition(name=self.name, description=self.description, parameters=self.schema)

    def validate(self, arguments: dict[str, Any]) -> ExternalArguments:
        try:
            self.validator.validate(arguments)
        except Exception as exc:
            raise ValueError(f"External schema/arguments invalid: {exc}") from exc
        return ExternalArguments.model_validate(arguments)

    async def execute(self, arguments: ExternalArguments) -> str:
        result = await self.client.request(
            "tools/call", {"name": self.remote_name, "arguments": arguments.root}
        )
        if result.get("isError"):
            raise MCPError(json.dumps(result.get("content", []), ensure_ascii=False))
        return json.dumps(result, ensure_ascii=False)


class MCPClient:
    def __init__(self, argv: list[str], *, label: str = "external", timeout: float = 15) -> None:
        if not argv or not re.fullmatch(r"[a-zA-Z0-9_-]{1,32}", label):
            raise ValueError("Invalid MCP command or label")
        self.argv, self.label, self.timeout = argv, label, timeout
        self.process: asyncio.subprocess.Process | None = None
        self._stderr: asyncio.Task[None] | None = None
        self.stderr_tail = b""
        self._lock = asyncio.Lock()
        self._id = 0

    async def __aenter__(self) -> "MCPClient":
        await self.connect()
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.close()

    async def connect(self) -> None:
        if self.process is not None:
            raise MCPError("Already connected")
        self.process = await asyncio.create_subprocess_exec(
            *self.argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            limit=1_048_576,
        )
        stderr = self.process.stderr

        async def drain() -> None:
            assert stderr is not None
            while chunk := await stderr.read(4096):
                self.stderr_tail = (self.stderr_tail + chunk)[-8192:]

        self._stderr = asyncio.create_task(drain())
        try:
            result = await self.request(
                "initialize",
                {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {"name": "mini-harness", "version": "0.1.0"},
                },
            )
            if result.get("protocolVersion") != "2025-06-18":
                raise MCPError("Unsupported protocol version (only 2025-06-18)")
            if "tools" not in result.get("capabilities", {}):
                raise MCPError("Server does not expose tools")
            await self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        except BaseException:
            await self.close()
            raise

    async def _send(self, packet: dict[str, Any]) -> None:
        if self.process is None or self.process.stdin is None:
            raise MCPError("Not connected")
        encoded = (json.dumps(packet, separators=(",", ":")) + "\n").encode()
        if len(encoded) > 1_048_576:
            raise MCPError("MCP message exceeds 1 MiB")
        self.process.stdin.write(encoded)
        await self.process.stdin.drain()

    async def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        async with self._lock:
            self._id += 1
            request_id = self._id
            try:
                async with asyncio.timeout(self.timeout):
                    await self._send(
                        {"jsonrpc": "2.0", "id": request_id, "method": method, "params": params}
                    )
                    assert self.process is not None and self.process.stdout is not None
                    for _ in range(1000):
                        line = await self.process.stdout.readline()
                        if not line:
                            raise MCPError("Server closed stdout")
                        response = json.loads(line)
                        if not isinstance(response, dict):
                            raise MCPError("Expected JSON-RPC object")
                        if response.get("jsonrpc") != "2.0":
                            raise MCPError("Invalid JSON-RPC version")
                        if "method" in response:
                            if "id" in response:
                                await self._send(
                                    {
                                        "jsonrpc": "2.0",
                                        "id": response["id"],
                                        "error": {
                                            "code": -32601,
                                            "message": "Server requests unsupported",
                                        },
                                    }
                                )
                            continue
                        if response.get("id") != request_id:
                            raise MCPError("Mismatched response ID")
                        if "error" in response:
                            raise MCPError(json.dumps(response["error"]))
                        result = response.get("result")
                        if not isinstance(result, dict):
                            raise MCPError("Expected object result")
                        return result
                    raise MCPError("Excessive notifications")
            except asyncio.CancelledError:
                await self.close()
                raise
            except (OSError, ValueError, TimeoutError, MCPError) as exc:
                await self.close()
                raise MCPError(f"MCP request {method} failed: {exc}") from exc

    async def register_tools(
        self, registry: ToolRegistry, grants: dict[str, Permission] | None = None
    ) -> list[str]:
        remote: list[dict[str, Any]] = []
        cursor: str | None = None
        seen: set[str] = set()
        for _ in range(128):
            result = await self.request("tools/list", {"cursor": cursor} if cursor else {})
            tools = result.get("tools")
            if not isinstance(tools, list):
                raise MCPError("Invalid tools/list result")
            remote.extend(tools)
            cursor = result.get("nextCursor")
            if not cursor:
                break
            if not isinstance(cursor, str) or cursor in seen:
                raise MCPError("Invalid/repeated pagination cursor")
            seen.add(cursor)
        else:
            raise MCPError("Tool pagination exceeds 128 pages")
        prepared: list[MCPTool] = []
        for tool in remote:
            if not isinstance(tool, dict) or not re.fullmatch(
                r"[a-zA-Z0-9_-]{1,64}", str(tool.get("name", ""))
            ):
                raise MCPError("Invalid remote tool name")
            if not isinstance(tool.get("inputSchema"), dict):
                raise MCPError("Missing input schema")
            prepared.append(
                MCPTool(self, tool, (grants or {}).get(tool["name"], Permission.DANGEROUS))
            )
        names = [tool.name for tool in prepared]
        if len(set(names)) != len(names) or set(names).intersection(registry.list()):
            raise MCPError("Tool name collision")
        for registered_tool in prepared:
            registry.register(registered_tool)
        return names

    async def close(self) -> None:
        process, self.process = self.process, None
        if process is None:
            return
        if process.stdin:
            process.stdin.close()
        try:
            async with asyncio.timeout(2):
                await process.wait()
        except TimeoutError:
            process.kill()
            await process.wait()
        if self._stderr:
            await self._stderr
            self._stderr = None
