# Unified AgentCore Gateway Setup (All Non-Swarm IDEs)

**Authority:** `contracts/agentcore-gateway-client.json`, `contracts/bifrost-upstream-mcp-registry.json`
**Endpoint:** `http://127.0.0.1:8080/mcp`
**Auth:** Windows User env `BIFROST_MCP_VIRTUAL_KEY` (never print / never commit)
**Copy-paste agent prompt:** `docs/prompts/install-agentcore-gateway-in-ide.md`

---

## Fact: Cursor already has the gateway

Live file `C:\Users\ynotf\.cursor\mcp.json` already contains:

```json
"agentcore-gateway": {
  "type": "http",
  "url": "http://127.0.0.1:8080/mcp",
  "headers": {
    "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
  },
  "timeout": 300
}
```

It will **not** appear as a server named `bifrost`. In Cursor MCP UI / tool routing it shows as **`agentcore-gateway`** (internally `user-agentcore-gateway`).

If tools are missing / status is error:

1. Confirm Bifrost is up: `http://127.0.0.1:8080/health` → 200.
2. Confirm User env `BIFROST_MCP_VIRTUAL_KEY` exists (length ~80; do not print).
3. **Fully quit Cursor** (all windows + tray) and relaunch so `${env:BIFROST_MCP_VIRTUAL_KEY}` expands. Cursor started before the VK was created will get empty Bearer → 401 → discovery failure.
4. After relaunch, MCP tools should be prefixed like `arabold_docs-*`, `depwire-*`, `tentra-*`, etc.

`MCP_DOCKER` is not part of the normal Cursor baseline. The Docker profile
`r3lentless_grind` overlapped Bifrost for Playwright/sequential thinking and
contained a broken `desktop-commander` entry with missing `paths`; rollback is
the timestamped Cursor MCP backup, not a second active gateway.

The canonical active Cursor gateway entry belongs only in `C:\Users\ynotf\.cursor\mcp.json`.
Repo-level `.cursor\mcp.json` / `.mcp.json` gateway duplicates are rollback or drift, not the
normal topology. Use `agentcore_project_router` for per-project identity instead of duplicate
gateway entries.

---

## Architecture (unify every non-Swarm agent)

```text
IDE / agent host
  └─ ONE MCP entry: agentcore-gateway
       └─ http://127.0.0.1:8080/mcp + Bearer BIFROST_MCP_VIRTUAL_KEY
            └─ Bifrost (H:\AgentRuntime\bifrost)
                 └─ upstream STDIO/HTTP MCP clients from
                    contracts/bifrost-upstream-mcp-registry.json
```

| Do | Don't |
| -- | -- |
| Put **only** `agentcore-gateway` as the AgentCore MCP baseline | Paste full Depwire/Serena/Arabold blocks into every IDE |
| Keep Swarm products on their own installs | Add SwarmRecall/SwarmVault to non-Swarm IDE baselines |
| Add new MCPs in the **registry + Bifrost**, then re-render | Add new MCPs only in one IDE’s `mcp.json` |
| Filter tools via Bifrost VK `tools_to_execute` / profiles | Rely on each IDE’s ad-hoc disable toggles as the source of truth |
| Touch OpenClaw/ClawX | — leave them alone |

---

## Canonical config blocks (sanitized)

Use `${env:BIFROST_MCP_VIRTUAL_KEY}` wherever the client expands env in headers.
If a client **cannot** expand env headers, materialize the User-env value into the **live** config only (never Git).

### Cursor — `C:\Users\ynotf\.cursor\mcp.json`

```json
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      },
      "timeout": 300
    }
  }
}
```

Do not keep `MCP_DOCKER` unless the operator explicitly approves a documented
exception for a unique capability that cannot be served through Bifrost.

### Windows Startup Owner

The native Windows owner is the scheduled task:

```powershell
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Stop-ScheduledTask  -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Get-ScheduledTask   -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Get-ScheduledTaskInfo -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
```

Repository wrappers:

```powershell
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Start-AgentCoreBifrostGateway.ps1
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Stop-AgentCoreBifrostGateway.ps1
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

Runtime logs:

```text
H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log
H:\AgentRuntime\bifrost\logs\bifrost-gateway.stderr.log
H:\AgentRuntime\bifrost\logs\logs.db
```

### Claude Desktop — `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "agentcore-gateway": {
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      }
    }
  }
}
```

If Desktop ignores `${env:…}`, materialize Bearer in the live file only.

### Claude Code — `C:\Users\ynotf\.claude.json` (`mcpServers` section)

```json
"agentcore-gateway": {
  "type": "http",
  "url": "http://127.0.0.1:8080/mcp",
  "headers": {
    "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
  }
}
```

### Codex — `C:\Users\ynotf\.codex\config.toml`

```toml
[mcp_servers.agentcore-gateway]
url = "http://127.0.0.1:8080/mcp"
bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"
enabled = true
startup_timeout_sec = 300
tool_timeout_sec = 300
```

Codex constructs `Authorization: Bearer` from `bearer_token_env_var`; this keeps
the secret in the Windows environment. `http_headers` is for static values, and
the generic contract timeout maps to Codex's `startup_timeout_sec` and
`tool_timeout_sec`. Re-check the installed Codex schema when its version changes.

### MiniMax — `C:\Users\ynotf\.minimax\mcp\mcp.json`

```json
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      }
    }
  }
}
```

### Mavis — `C:\Users\ynotf\.mavis\mcp\mcp.json`

Same shape as MiniMax / Cursor HTTP block above.

### Antigravity / Gemini — path from contract (`~/.gemini/config/mcp_config.json` or Antigravity User `mcp.json`)

Same HTTP + Bearer env header shape.

### Open Interpreter — `%APPDATA%\interpreter\config.json`

Prefer env expansion if supported; otherwise materialize Bearer in live config only (`supports_env_headers: false` in contract).

Sanitized renderers: `renderers/gateway-clients/<ide>.json`.

### Supported IDE Matrix

| Client | Active config path | Schema / syntax | Env header support | Timeout field | Restart behavior | Rollback |
| -- | -- | -- | -- | -- | -- | -- |
| Cursor | `C:\Users\ynotf\.cursor\mcp.json` | `mcpServers.agentcore-gateway` JSON, `type=http`, `url`, `headers` | Yes: `${env:BIFROST_MCP_VIRTUAL_KEY}` | `timeout: 300` | Fully quit all Cursor processes, relaunch, verify `user-agentcore-gateway` ready | Restore timestamped `mcp.json` backup |
| Codex | `C:\Users\ynotf\.codex\config.toml` | `[mcp_servers.agentcore-gateway]`, `url`, `bearer_token_env_var` | Yes: named User env read by Codex | `startup_timeout_sec = 300`, `tool_timeout_sec = 300` | Restart Codex session/CLI host | Restore timestamped `config.toml` backup |
| Claude Code | `C:\Users\ynotf\.claude.json` | JSON `mcpServers` entry | Yes where supported by installed client | Client default or renderer field | Restart Claude Code | Restore `.claude.json` backup |
| Claude Desktop | `C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json` | JSON `mcpServers` entry | Contract marks unsupported; materialize live secret only as last resort | Client default | Fully quit/reopen Claude Desktop | Restore config backup |
| MiniMax | `C:\Users\ynotf\.minimax\mcp\mcp.json` | JSON `mcpServers` entry | Yes | Client default or renderer field | Restart MiniMax | Restore config backup |
| Mavis | `C:\Users\ynotf\.mavis\mcp\mcp.json` | JSON `mcpServers` entry | Yes | Client default or renderer field | Restart Mavis | Restore config backup |
| Antigravity | `C:\Users\ynotf\.gemini\config\mcp_config.json` or `C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json` | JSON MCP config | Yes | Client default or renderer field | Restart Antigravity/Gemini host | Restore config backup |
| Open Interpreter | `C:\Users\ynotf\AppData\Roaming\interpreter\config.json` | JSON app config | Contract marks unsupported; materialize live secret only as last resort | Client default | Restart Open Interpreter | Restore config backup |

For every client, validate Bifrost first with `ops\bifrost\Test-AgentCoreBifrostGateway.ps1`,
then validate IDE discovery and one safe read-only tool call through `agentcore-gateway`.

---

## How to add a new MCP server (correct path)

1. **Decide classification** in `docs/bifrost/MCP_CLASSIFICATION_MATRIX.md` (global vs project-scoped, Swarm exclusion).
2. **Edit** `contracts/bifrost-upstream-mcp-registry.json`:
   - Add server entry (`enabled`, `connection_type`, command/url, args, `bifrost_client_name`, rollback notes).
   - Add id to the right `capability_profiles.*.allowed_server_ids`.
3. **Render** Bifrost config: `python scripts/bifrost/render_bifrost_config.py` (or approved ops script).
4. **Validate** contracts / validators.
5. **Restart / reload** Bifrost (`ops/bifrost/Start-AgentCoreBifrostGateway.ps1` or Scheduled Task).
6. **Do not** add the new server to Cursor/Claude/Codex `mcp.json` — IDEs keep the single `agentcore-gateway` entry.
7. Confirm via Bifrost API clients list + IDE tool discovery after reconnect.

Never add SwarmRecall/SwarmVault here.

---

## How to prevent tools you don’t want from loading

Bifrost `version: 2` governance is **deny-by-default** for MCP tools: a client/tool is only exposed to an IDE if it appears under that virtual key’s `mcp_configs[].tools_to_execute`.

### A. Disable an entire upstream (strongest)

In `contracts/bifrost-upstream-mcp-registry.json` set `"enabled": false`, re-render, restart Bifrost.
Used today for deferred servers (e.g. artiforge inactive PAT).

### B. Keep server connected but hide all its tools from a profile

Omit that `mcp_client_name` from the profile VK’s `mcp_configs`, **or** set:

```json
"tools_to_execute": []
```

Empty list = deny all tools for that client on that VK (Bifrost v2 semantics).

### C. Allow only named tools

```json
{
  "mcp_client_name": "agentcore_memory",
  "tools_to_execute": [
    "memory_status",
    "startup_context",
    "retrieve_context",
    "append_event",
    "propose_fact",
    "expand_source",
    "session_open",
    "session_close",
    "build_handoff",
    "docs_search"
  ]
}
```

### D. Allow all tools on one client

```json
"tools_to_execute": ["*"]
```

### E. Use a narrower profile VK in an IDE

| Profile | Env var | Use when |
| -- | -- | -- |
| builder (default) | `BIFROST_MCP_VIRTUAL_KEY` | Full coding surface |
| reviewer | `BIFROST_MCP_VK_REVIEWER` | Read-focused review |
| database-validator | `BIFROST_MCP_VK_DATABASE_VALIDATOR` | Memory health only |
| docs-knowledge | `BIFROST_MCP_VK_DOCS_KNOWLEDGE` | Docs + vault |
| operator | `BIFROST_MCP_VK_OPERATOR` | Ops / routing |

Point that IDE’s Bearer header at the narrower env var. See `docs/bifrost/CAPABILITY_PROFILES.md`.

### F. IDE-side disable (optional only)

Toggling a tool off inside Cursor does **not** change Bifrost policy. Prefer A–E so every IDE stays consistent.

### G. Do not load tools via auto-inject

Gateway config keeps `mcp_disable_auto_tool_inject: true` so Bifrost does not inject MCP tools into LLM provider calls unless you explicitly want that.

---

## Optimize for AgentCore workflow

1. **One gateway entry per IDE** — minimizes MCP process sprawl.
2. **Activate project** via `agentcore_project_router` / `project_activate` before Serena/Depwire/Tentra/filesystem work.
3. **Builder VK** for daily Cursor/Claude/Codex; use reviewer/docs VKs for constrained agents.
4. **Arabold first** for library docs (`arabold_docs-search_docs` with pinned versions in `.agentcore/docs/DOCS_INDEX.md`).
5. **Keep Bifrost on H:** (`H:\AgentRuntime\bifrost`); start via Scheduled Task `\AgentCore\AgentCore-Bifrost-Gateway` or `ops/bifrost/Launch-AgentCoreBifrostGateway.ps1`.
6. After changing User env vars, **fully restart** every IDE that expands `${env:…}`.

---

## Quick health checklist

```powershell
Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing
# User env present (do not print value):
[Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY','User').Length
```

Then fully quit/relaunch the IDE and confirm `agentcore-gateway` tools appear.
