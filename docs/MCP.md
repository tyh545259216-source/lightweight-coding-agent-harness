# MCP support and limits

Implemented: a small legacy **2025-06-18 stdio JSON-RPC subset**, initialized over a trusted child process, with tool discovery/call adaptation and one outstanding request. The code implements its own client; `jsonschema` validates external argument schemas. There is no MCP SDK dependency.

Remote tools become namespaced `MCPTool` entries through `MCPClient.register_tools`. They use the same ToolRegistry/ToolExecutor validation, host grants and journal as built-in tools. Remote schema references are rejected; server annotations cannot authorize read/write/execute. Side-effect classification follows the host permission mapping.

Not implemented: a full modern MCP platform, HTTP/Streamable HTTP transport, OAuth/server discovery, general protocol coverage, or a security boundary around untrusted servers. The server is a trusted process with host privileges.

```sh
python examples/mcp_demo.py
```

This offline demo starts the included stdio server and uses a scripted FakeProvider to call its echo tool through the real adapter/executor. It tests engineering integration, not model intelligence. [Client code](../src/mini_harness/mcp/client.py) · [Server example](../examples/mcp_server.py).
