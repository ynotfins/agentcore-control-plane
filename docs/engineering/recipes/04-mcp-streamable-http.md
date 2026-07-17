# Recipe 04 — MCP Streamable HTTP Server

**Pattern:** HTTP-based MCP server using the official Python SDK.  
**Stack:** Python 3.12+, `mcp>=1.28.1,<2.0`.  
**Authority:** `docs/engineering/CONSTITUTION.md` §6.

---

## Key Constraints

- Bind to `127.0.0.1` only by default.
- Bearer token from env var. Never hardcode.
- Health endpoint at `/health`.
- Pin to `mcp<2.0` until stable v2 is released and tested.

## Minimal Implementation

```python
#!/usr/bin/env python3
"""Minimal MCP Streamable HTTP server."""
from __future__ import annotations

import os
from mcp.server.fastmcp import FastMCP

BEARER_TOKEN = os.environ.get("MY_SERVER_TOKEN", "")

mcp = FastMCP("my-http-server")


@mcp.tool()
def my_tool(input: str) -> str:
    """Does something useful."""
    return f"processed: {input}"


if __name__ == "__main__":
    mcp.run(transport="streamable-http", host="127.0.0.1", port=8090)
```

## Authentication Middleware (production)

```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class BearerAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health",):
            return await call_next(request)
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer ") or auth[7:] != BEARER_TOKEN:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return await call_next(request)
```

## Health Endpoint

```python
from starlette.routing import Route
from starlette.responses import JSONResponse

async def health(_):
    return JSONResponse({"ok": True, "server": "my-http-server"})

# Add to app routes before mcp routes
```

## pyproject.toml Dependencies

```toml
[project]
dependencies = [
    "mcp>=1.28.1,<2.0",
    "starlette>=0.41,<1.0",
    "uvicorn[standard]>=0.31,<1.0",
]
```

## Starting as a Windows Scheduled Task

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "server.py" -WorkingDirectory "D:\myserver"
$trigger = New-ScheduledTaskTrigger -AtStartup
Register-ScheduledTask -TaskName "MyServer" -Action $action -Trigger $trigger -RunLevel Highest
```
