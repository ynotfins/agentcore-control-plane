# Recipe 02 — Secure Environment Variable Loading

**Pattern:** Fail-fast env var validation at startup. Never `.env` files for AgentCore.  
**Stack:** Python 3.12+, PowerShell 5.1+.  
**Authority:** `docs/engineering/CONSTITUTION.md` §10.

---

## Python

```python
from __future__ import annotations
import os
import sys

# Single function; call at module import
def _require_env(key: str) -> str:
    val = os.environ.get(key, "")
    if not val:
        sys.stderr.write(f"[startup] FATAL: environment variable {key!r} is not set\n")
        sys.exit(1)
    return val

PG_PASSWORD = _require_env("AGENT_CORE_POSTGRES_PASSWORD")
```

### Optional env var with validated default

```python
def _env(key: str, default: str, *, choices: tuple[str, ...] | None = None) -> str:
    val = os.environ.get(key, default)
    if choices and val not in choices:
        raise ValueError(f"{key}={val!r} must be one of {choices}")
    return val

LOG_LEVEL = _env("LOG_LEVEL", "info", choices=("debug", "info", "warn", "error"))
```

### Never do

```python
# WRONG — hardcoded secrets, .env files, truthy checks on secret values
import dotenv; dotenv.load_dotenv()          # .env files forbidden
PG_PASSWORD = "my_secret_password"           # hardcoded secret
if not os.environ.get("PG_PASSWORD"):        # might be '0' or 'false' — truthy check unreliable
    raise ...
```

---

## PowerShell

```powershell
function Get-RequiredEnv {
    param([string]$Key)
    $val = [System.Environment]::GetEnvironmentVariable($Key)
    if ([string]::IsNullOrEmpty($val)) {
        Write-Error "Environment variable '$Key' is not set. Set it as a Windows User-scope variable."
        exit 1
    }
    return $val
}

$PgPassword = Get-RequiredEnv -Key "AGENT_CORE_POSTGRES_PASSWORD"
```

---

## Setting Windows User-scope Variables

```powershell
# One-time setup by operator (not in scripts)
[System.Environment]::SetEnvironmentVariable("AGENT_CORE_POSTGRES_PASSWORD", "...", "User")
# Restart IDEs/terminals after setting
```

---

## Validation in Startup Context

All services that need credentials must validate at startup, before serving any requests:

```python
def _startup_validation() -> None:
    required = ["AGENT_CORE_POSTGRES_PASSWORD"]
    missing = [k for k in required if not os.environ.get(k)]
    if missing:
        sys.stderr.write(f"[startup] FATAL: missing env vars: {missing}\n")
        sys.exit(1)
    _log("info", "startup_validation_passed", keys=required)

_startup_validation()
```
