# Recipe 08 — Structured Logging and Diagnostics

**Pattern:** Deterministic, machine-readable JSON logging to stderr.  
**Stack:** Python 3.12+, PowerShell.  
**Authority:** `docs/engineering/CONSTITUTION.md` §9.

---

## Python Minimal Pattern

```python
from __future__ import annotations
import json, sys
from datetime import datetime, timezone

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _log(level: str, msg: str, **ctx) -> None:
    """Write a structured JSON log line to stderr. Never to stdout."""
    record = {"ts": _now(), "level": level, "msg": msg, **ctx}
    sys.stderr.write(json.dumps(record) + "\n")
    sys.stderr.flush()

# Usage
_log("info", "startup", server="agentcore-memory", version="0.5.0")
_log("warn", "cognee_degraded", reason="tcp_timeout", fallback="postgres_fts")
_log("error", "db_error", error_class="OperationalError", retry=False)
```

## Required Fields

| Field | Type | Notes |
|---|---|---|
| `ts` | ISO-8601 UTC string | Always present |
| `level` | `debug\|info\|warn\|error` | Always present |
| `msg` | string | Short, stable identifier (no interpolated data) |
| context | key=value pairs | Tool call name, project_key, session_id, etc. |

## What NOT to Log

```python
# WRONG — logs a secret value
_log("debug", "db_connect", password=pg_pass)

# CORRECT — logs only the key name
_log("debug", "db_connect", password_key="AGENT_CORE_POSTGRES_PASSWORD", host=PG_HOST)

# WRONG — freeform string
_log("info", f"connecting to {host}:{port} with {user}")

# CORRECT — structured
_log("info", "db_connect", host=host, port=port, user=user)
```

## Boundary Logging Pattern

Log at every external system boundary:

```python
def call_db(query: str, params: tuple) -> list:
    _log("debug", "db_query_start", query_preview=query[:80])
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
        _log("debug", "db_query_ok", row_count=len(rows))
        return rows
    except Exception as exc:
        _log("error", "db_query_fail", error_class=type(exc).__name__)
        raise
```

## Diagnostic Bundle (PowerShell)

```powershell
function Get-AgentCoreDiagnostics {
    [PSCustomObject]@{
        timestamp       = (Get-Date -Format "o")
        python_version  = (python --version 2>&1)
        pg_reachable    = (Test-NetConnection -ComputerName "127.0.0.1" -Port 55433 -WarningAction SilentlyContinue).TcpTestSucceeded
        bifrost_running = ((Get-ScheduledTask -TaskName "AgentCore\AgentCore-Bifrost-Gateway" -ErrorAction SilentlyContinue).State -eq "Running")
        migrations      = (& "F:\PostgreSQL18\bin\psql.exe" "host=127.0.0.1 port=55433 dbname=agent_core user=postgres password=$env:AGENT_CORE_POSTGRES_PASSWORD" -At -c "SELECT string_agg(version, ', ') FROM agentcore.schema_migrations" 2>&1)
        env_vars_set    = @("AGENT_CORE_POSTGRES_PASSWORD") | ForEach-Object { @{ key=$_; set=[bool][System.Environment]::GetEnvironmentVariable($_) } }
    }
}

Get-AgentCoreDiagnostics | ConvertTo-Json -Depth 5
```
