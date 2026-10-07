"""Dependency-free, runnable MCP 2025-06-18 stdio fixture. stdout is protocol only."""

import json
import sys
import time


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "normal"
    for line in sys.stdin:
        request = json.loads(line)
        if "id" not in request:
            continue
        method, params = request["method"], request.get("params", {})
        response = {"jsonrpc": "2.0", "id": request["id"]}
        if method == "initialize":
            result = {
                "protocolVersion": "bad" if mode == "unsupported" else "2025-06-18",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "harness-fixture", "version": "1"},
            }
        elif method == "tools/list":
            result = {
                "tools": [
                    {
                        "name": "echo",
                        "description": "Echo trusted fixture text",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"text": {"type": "string"}},
                            "required": ["text"],
                            "additionalProperties": False,
                        },
                    }
                ]
            }
        elif method == "tools/call":
            if mode == "slow":
                time.sleep(5)
            if mode == "malformed":
                print("not json", flush=True)
                continue
            if mode == "rpc-error":
                response["error"] = {"code": -32603, "message": "fixture failure"}
                print(json.dumps(response), flush=True)
                continue
            result = {
                "content": [{"type": "text", "text": params["arguments"]["text"]}],
                "isError": mode == "tool-error",
            }
        else:
            response["error"] = {"code": -32601, "message": "unknown method"}
            print(json.dumps(response), flush=True)
            continue
        response["result"] = result
        print(json.dumps(response), flush=True)


if __name__ == "__main__":
    main()
