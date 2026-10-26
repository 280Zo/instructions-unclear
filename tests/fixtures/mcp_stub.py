"""Minimal stdio MCP server for permission tests: one harmless "ping" tool."""

import json
import sys


def reply(message_id, result):
    sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": message_id, "result": result}) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    if len(line) > 1_000_000:
        continue
    try:
        message = json.loads(line)
    except json.JSONDecodeError:
        continue
    method = message.get("method")
    if "id" not in message:
        continue
    if method == "initialize":
        reply(message["id"], {
            "protocolVersion": message.get("params", {}).get("protocolVersion", "2025-06-18"),
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "mcp-stub", "version": "1.0.0"},
        })
    elif method == "tools/list":
        reply(message["id"], {"tools": [{
            "name": "ping", "description": "Return pong. Permission test fixture.",
            "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        }]})
    elif method == "tools/call":
        reply(message["id"], {"content": [{"type": "text", "text": "MCP_STUB_PONG"}]})
    else:
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": message["id"],
                                     "error": {"code": -32601, "message": "Method not found"}}) + "\n")
        sys.stdout.flush()
