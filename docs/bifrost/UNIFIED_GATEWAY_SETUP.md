# Unified AgentCore Gateway Setup (All Non-Swarm IDEs)

**Authority:** `contracts/agentcore-gateway-client.json`, `contracts/bifrost-upstream-mcp-registry.json`
**Direct endpoint:** `http://127.0.0.1:8080/mcp` for clients that can reference the Windows User environment securely
**Compatibility endpoint:** `http://127.0.0.1:18082/mcp` for approved header-hostile Trust Class A clients
**Auth:** Windows User env `BIFROST_MCP_VIRTUAL_KEY` (never print, commit, or persist in header-hostile client files)
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
4. After relaunch, confirm the current builder tools from the live gateway; do not use historical server names as the acceptance list.

`MCP_DOCKER` is not part of the normal Cursor baseline. The Docker profile
`r3lentless_grind` overlapped Bifrost for Playwright/sequential thinking and
contained a broken `desktop-commander` entry with missing `paths`; rollback is
the timestamped Cursor MCP backup, not a second active gateway.

The canonical active Cursor gateway entry belongs only in `C:\Users\ynotf\.cursor\mcp.json`.
Repo-level `.cursor\mcp.json` / `.mcp.json` gateway duplicates are rollback or drift, not the
normal topology. Exact enrollment, signed project identity, and the selected worktree enforce
project continuity. `agentcore-project-router` remains an operator-only maintenance surface.

---

## Architecture (unify every non-Swarm agent)

```text
IDE / agent host
  └─ ONE AgentCore MCP entry: agentcore-gateway
       ├─ header-capable: http://127.0.0.1:8080/mcp + environment-backed Bearer
       └─ approved header-hostile Trust Class A: http://127.0.0.1:18082/mcp
            └─ exact Windows process/ancestor attestation, then in-memory Bearer injection
       └─ Bifrost (F:\AgentCore\runtime\bifrost)
            └─ upstream STDIO/HTTP MCP clients from
               contracts/bifrost-upstream-mcp-registry.json
  └─ OPTIONAL host-native direct companion
       └─ requires the parity, scope, security, and rollback evidence in the current global policy
```

| Do | Don't |
| -- | -- |
| Put **only** `agentcore-gateway` as the AgentCore MCP baseline | Paste full Depwire/Serena/Arabold blocks into every IDE |
| Preserve a documented host-native companion only when current policy and parity evidence allow it | Treat a prior Zoo-Code exception as general permission for direct MCP servers |
| Keep Swarm products on their own installs | Add SwarmRecall/SwarmVault to non-Swarm IDE baselines |
| Add new MCPs in the **registry + Bifrost**, then re-render | Add new MCPs only in one IDE’s `mcp.json` |
| Filter tools via Bifrost VK `tools_to_execute` / profiles | Rely on each IDE’s ad-hoc disable toggles as the source of truth |
| Treat OpenClaw/ClawX as AgentCore-owned clients governed by their declared profile and single `agentcore-gateway` route | Fold them into SwarmClaw governance or grant routes outside their enrolled AgentCore profile |

---

## Canonical config blocks (sanitized)

Use `${env:BIFROST_MCP_VIRTUAL_KEY}` or a native named-token field wherever the client expands Windows User environment references safely. Approved header-hostile Trust Class A clients use `http://127.0.0.1:18082/mcp` without a persisted authorization header. The proxy accepts only an exact approved Windows executable or process ancestor, injects the User-scope key in memory, and fails closed for missing, ambiguous, or unapproved callers. Resolve the route from `contracts/agentcore-gateway-client.json` `gateway_url` and `gateway_auth_mode`; do not infer it from `supports_env_headers` prose.

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

The gateway task is currently triggered `AtLogOn` and runs as the owning user
with an `Interactive`, `Limited` principal so it can consume User-scope secret
environment variables. It is intended to remain running after login; true
pre-login availability is not guaranteed by this topology.

The watchdog allows 120 seconds for startup, requires two consecutive failed
probes, starts a `Ready` or other non-`Running` task idempotently, and uses a
controlled stop/start recycle when the task is `Running`. Stop/start failures use
a bounded 60-second retry backoff. A maintenance marker suppresses automated
launch and recycle.

The `:18082` compatibility proxy is subordinate to core `:8080`. If proxy
startup fails, the launcher records `BUILDER_COMPAT_PROXY_DEGRADED` but keeps
core Bifrost running. Only clients assigned to `:18082` are degraded by that
failure.

Repository wrappers:

```powershell
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Start-AgentCoreBifrostGateway.ps1
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Stop-AgentCoreBifrostGateway.ps1
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

Runtime logs:

```text
F:\AgentCore\runtime\bifrost\logs\bifrost-gateway.stdout.log
F:\AgentCore\runtime\bifrost\logs\bifrost-gateway.stderr.log
F:\AgentCore\runtime\bifrost\logs\logs.db
```

### Claude Desktop — `%APPDATA%\Claude\claude_desktop_config.json`

Claude Desktop has no currently approved environment-backed or process-attested
AgentCore gateway route. Do not materialize a virtual key into its live file.
Treat any legacy credential-bearing entry as preserved drift until a separate
backup-first cleanup or secure-route task is approved.

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

### MiniMax — `C:\Users\ynotf\.minimax\mcp.json`

```json
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "streamable-http",
      "url": "http://127.0.0.1:18082/mcp",
      "timeout": 300000
    }
  }
}
```

MiniMax reads the MCP server `timeout` field in milliseconds, so this entry requires `timeout: 300000` ms. `C:\Users\ynotf\.minimax\mcp\mcp.json` is a legacy path that the app no longer reads for server configuration; it survives only to hide legacy proxy skill names.

MiniMax Code's agent-turn tool discovery caps the HTTP connect budget at 2000 ms (`Math.min(configuredTimeout, turnDiscoveryTimeoutMs ?? 2000)`, and `turnDiscoveryTimeoutMs` is never assigned), so this timeout governs the uncapped settings-panel connect path only. Binding the gateway tools inside an agent session additionally requires the process-attested proxy cold connect to finish inside 2 s.

### Mavis — `C:\Users\ynotf\.mavis\mcp\mcp.json`

`C:\Users\ynotf\.mavis` is the same MiniMax Code data root, not a separate client configuration.

### Antigravity / Gemini — path from contract (`~/.gemini/config/mcp_config.json` or Antigravity User `mcp.json`)

Use `serverUrl: http://127.0.0.1:18082/mcp` with no persisted authorization header.

### Open Interpreter — `%APPDATA%\interpreter\config.json`

The desktop JSON uses `http://127.0.0.1:18082/mcp` without a persisted authorization header. The CLI TOML uses the direct `:8080` endpoint with `bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"`.

Sanitized renderers: `renderers/gateway-clients/<ide>.json`.

### Supported IDE Matrix

| Client | Active config path | Schema / syntax | Env header support | Timeout field | Restart behavior | Rollback |
| -- | -- | -- | -- | -- | -- | -- |
| Cursor | `C:\Users\ynotf\.cursor\mcp.json` | `mcpServers.agentcore-gateway` JSON, `type=http`, `url`, `headers` | Yes: `${env:BIFROST_MCP_VIRTUAL_KEY}` | `timeout: 300` | Fully quit all Cursor processes, relaunch, verify `user-agentcore-gateway` ready | Restore timestamped `mcp.json` backup |
| Codex | `C:\Users\ynotf\.codex\config.toml` | `[mcp_servers.agentcore-gateway]`, `url`, `bearer_token_env_var` | Yes: named User env read by Codex | `startup_timeout_sec = 300`, `tool_timeout_sec = 300` | Restart Codex session/CLI host | Restore timestamped `config.toml` backup |
| Claude Code | `C:\Users\ynotf\.claude.json` | JSON `mcpServers` entry | Yes where supported by installed client | Client default or renderer field | Restart Claude Code | Restore `.claude.json` backup |
| Claude Desktop | `C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json` | No approved secure route | Unsupported until a credential-free or native-token route is proven | Client default | No enrollment action | Preserve legacy config; clean up only through a separate backup-first task |
| MiniMax | `C:\Users\ynotf\.minimax\mcp.json` | JSON `mcpServers` entry at `:18082` | Process-attested proxy; no persisted bearer | `timeout: 300000` (milliseconds) | Restart MiniMax | Restore config backup |
| Mavis | Junction to `C:\Users\ynotf\.minimax` | Same MiniMax Code configuration | Same as MiniMax | Same as MiniMax | Restart MiniMax | Restore config backup |
| Antigravity | `C:\Users\ynotf\.gemini\config\mcp_config.json` or `C:\Users\ynotf\AppData\Roaming\Antigravity IDE\User\mcp.json` | JSON MCP config at `:18082` | Process-attested proxy; no persisted bearer | Client default or renderer field | Restart Antigravity host | Restore config backup |
| Devin | `C:\Users\ynotf\AppData\Roaming\devin\mcp_config.json` | JSON `mcpServers` entry at `:18082` | Process-attested proxy; no persisted bearer | Client default | Restart Devin | Restore config backup |
| ZCode | `C:\Users\ynotf\.zcode\cli\config.json` | JSON `mcp.servers` entry at `:18082` | Process-attested proxy; no persisted bearer | `timeoutMs: 300000` | Restart ZCode | Restore config backup |
| Open Interpreter desktop | `C:\Users\ynotf\AppData\Roaming\interpreter\config.json` | JSON app config at `:18082` | Process-attested proxy; no persisted bearer | Client default | Restart Open Interpreter | Restore config backup |
| Open Interpreter CLI | `C:\Users\ynotf\.openinterpreter\config.toml` | TOML direct entry at `:8080` | `bearer_token_env_var` | Client default | Restart CLI session | Restore config backup |
| Cherry Studio | `%APPDATA%\CherryStudio` Local Storage (`persist:cherry-studio`) | No approved secure route | Unsupported until a credential-free or native-token route is proven | 300s | No enrollment action | Preserve legacy LevelDB; clean up only under `E:\AgentCore\Backups\<stamp>` |
| LangGraph prod / Studio | shared Python adapter (not an IDE `mcp.json`) | `scripts/agentcore_workflow/mcp_client.py` → localhost gateway | Bearer from `BIFROST_MCP_VK_WORKFLOW` or `BIFROST_MCP_VIRTUAL_KEY` | 300s | Restart worker / Studio process | Disable workflow; gateway unchanged |

For every client, validate Bifrost first with `ops\bifrost\Test-AgentCoreBifrostGateway.ps1`,
then validate IDE discovery and one safe read-only tool call through `agentcore-gateway`.

**OpenRouter MCP:** never add `https://mcp.openrouter.ai/mcp` as a direct IDE MCP entry. Gateway + M6 lease only — `docs/operations/OPENROUTER_MCP.md`.

---

## How to add a new MCP server (correct path)

This path applies to AgentCore-governed MCP servers. A host-native direct MCP companion is permitted only after a documented Bifrost parity failure, exact host/tool scope, security review, rollback proof, and proof that the companion does not duplicate AgentCore memory, database, Swarm, administrative, or upstream-registry routes. Zoo-Code's historical exception remains subject to this current policy.

1. **Decide classification** in `docs/bifrost/MCP_CLASSIFICATION_MATRIX.md` (global vs project-scoped, Swarm exclusion).
2. **Edit** `contracts/bifrost-upstream-mcp-registry.json`:
   - Add server entry (`enabled`, `connection_type`, command/url, args, `bifrost_client_name`, rollback notes).
   - Add id to the right `capability_profiles.*.allowed_server_ids`.
3. **Render** Bifrost config: `scripts\.venv\Scripts\python.exe scripts/bifrost/render_bifrost_config.py` (or approved ops script).
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
Used today for disabled servers such as `mcp-debugger`.

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

### D. Require a named inventory before activation

Do not activate a new server or profile with `tools_to_execute: ["*"]`. Keep the
server disabled while its exact `tools/list` inventory is captured, classify each
tool, set `permitted_tools` to the approved names, then render and validate the
matching `tools_to_execute` list. Existing wildcard placeholders are allowed only
on disabled or dormant entries and are not an activation template.

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
2. **Resolve project locally** through the IDE/workflow host. Serena, Depwire, Tentra, filesystem, and Context Fabric stay dormant in shared Bifrost profiles until a per-session project identity is injected; use native project tools or explicit-cwd local diagnostics.
3. **Builder VK** for Trust Class A. Header-capable clients use it by environment reference; approved header-hostile clients receive it only through the process-attested proxy. Use reviewer/docs VKs for constrained agents.
4. **Arabold first** for library docs (`arabold_docs-search_docs` with pinned versions in `.agentcore/docs/DOCS_INDEX.md`).
5. **Keep Bifrost under the approved AgentCore runtime:** (`F:\AgentCore\runtime\bifrost`); start via Scheduled Task `\AgentCore\AgentCore-Bifrost-Gateway` or `ops/bifrost/Launch-AgentCoreBifrostGateway.ps1`.
6. After changing User env vars, **fully restart** every IDE that expands `${env:…}`.

---

## Quick health checklist

```powershell
Invoke-WebRequest http://127.0.0.1:8080/health -UseBasicParsing
Invoke-WebRequest http://127.0.0.1:18082/healthz -UseBasicParsing
# User env present (do not print value):
[Environment]::GetEnvironmentVariable('BIFROST_MCP_VIRTUAL_KEY','User').Length
```

Then fully quit/relaunch the IDE and confirm `agentcore-gateway` tools appear.

---

## See also

- Architecture authority: `BLUEPRINT.md`
- Mutable live posture: `CONTEXT_BLOCK.md` §0 ("Current posture")
- Classification / profiles: `docs/bifrost/MCP_CLASSIFICATION_MATRIX.md`, `docs/bifrost/CAPABILITY_PROFILES.md`
- OpenRouter MCP runbook: `docs/operations/OPENROUTER_MCP.md`
- LangGraph + Studio runbook: `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
- Dormant catalog: `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md`
- Enrollment evidence: `audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md`, `audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md`
