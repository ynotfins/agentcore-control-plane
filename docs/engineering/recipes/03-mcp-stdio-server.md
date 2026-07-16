# Recipe 03 — MCP Stdio Server (Bifrost-compatible)

**Pattern:** NDJSON-RPC stdio MCP server that works behind the Bifrost gateway.  
**Stack:** Python 3.12+, psycopg 3.x.  
**Reference implementation:** `docs/engineering/reference-implementations/mcp-stdio-server/`  
**Authority:** `docs/engineering/CONSTITUTION.md` §6.

---

## Key Constraints

- Bifrost speaks **newline-delimited JSON-RPC** (NDJSON), not Content-Length framing.
- Accept and echo the negotiated protocol version.
- stdout is the JSON-RPC channel. Log only to stderr.
- Never expose credentials or admin tools.

## Minimal Implementation

```python
#!/usr/bin/env python3
"""Minimal MCP stdio server (Bifrost-compatible NDJSON-RPC)."""
from __future__ import annotations

import json, os, sys
from typing import Any

SERVER_NAME = "my-server"
SERVER_VERSION = "0.1.0"
PROTOCOL_VERSION = "2025-06-18"


def _log(msg: str) -> None:
    sys.stderr.write(f"[{SERVER_NAME}] {msg}\n")
    sys.stderr.flush()


def _send(obj: Any) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _send_error(req_id: Any, code: int, message: str) -> None:
    _send({"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}})


def tool_defs() -> list[dict]:
    return [
        {
            "name": "my_tool",
            "description": "Does something useful.",
            "inputSchema": {
                "type": "object",
                "properties": {"input": {"type": "string"}},
                "required": ["input"],
                "additionalProperties": False,
            },
        },
    ]


def handle_tool_call(name: str, args: dict) -> Any:
    if name == "my_tool":
        return {"ok": True, "result": f"processed: {args['input']}"}
    raise ValueError(f"unknown tool: {name!r}")


def main() -> None:
    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        method = msg.get("method", "")
        req_id = msg.get("id")
        params = msg.get("params", {})

        try:
            if method == "initialize":
                _send({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {
                        "protocolVersion": PROTOCOL_VERSION,
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
                    },
                })
            elif method == "tools/list":
                _send({"jsonrpc": "2.0", "id": req_id, "result": {"tools": tool_defs()}})
            elif method == "tools/call":
                result = handle_tool_call(params.get("name", ""), params.get("arguments", {}))
                _send({
                    "jsonrpc": "2.0", "id": req_id,
                    "result": {"content": [{"type": "text", "text": json.dumps(result)}]},
                })
            elif method in ("notifications/initialized", "initialized"):
                pass  # no response for notifications
            else:
                if req_id is not None:
                    _send_error(req_id, -32601, f"method not found: {method}")
        except Exception as exc:
            _log(f"error handling {method}: {exc}")
            if req_id is not None:
                _send_error(req_id, -32000, str(exc))


if __name__ == "__main__":
    main()
```

## Bifrost Registry Entry

```json
{
  "id": "my-server",
  "command": "python",
  "args": ["path/to/server.py"],
  "permitted_tools": ["my_tool"]
}
```

## Testing Without Bifrost

```powershell
# Pipe test messages
@"
{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{}}}
{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}
{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"my_tool","arguments":{"input":"hello"}}}
"@ | python server.py
```
