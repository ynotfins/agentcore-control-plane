# OpenRouter MCP — Canonical Runbook

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`  
**Registry ID:** `openrouter`  
**Bifrost client name:** `openrouter`  
**Status:** dormant by default (zero tools without a live M6 capability lease)  
**Last tool inventory:** 16 tools, verified 2026-07-17  
**Updated:** 2026-07-17

---

## Distinction: OpenRouter MCP ≠ OpenRouter LLM Provider

These are **separate** concerns:

| Aspect | OpenRouter MCP (this runbook) | OpenRouter LLM Provider |
|---|---|---|
| Purpose | Development-assistant tooling (model discovery, docs, catalog) | Inference API for model calls |
| Endpoint | `https://mcp.openrouter.ai/mcp` | `https://openrouter.ai/api/v1` |
| Auth for IDE | Via Bifrost OAuth (config.db) | `OPENROUTER_API_KEY` in Windows env |
| Changes IDE model | No — never | Only when explicitly configured |
| Open Interpreter | Tools available via gateway | Inference via `autonomous-os` profile (OPENROUTER_API_KEY) |

Adding OpenRouter MCP does **not** change any IDE's default model or provider.

---

## Official Endpoint and Transport

```
Endpoint:  https://mcp.openrouter.ai/mcp
Transport: MCP Streamable HTTP (spec 2025-03-26)
Auth:      OAuth 2.1 + PKCE + Dynamic Client Registration
```

---

## Lifecycle States

```
installed_dormant
  → config registered in Bifrost, OAuth not yet initiated
  → Connection fails with "oauth2 config not found" (expected)
  → Zero tools exposed

ready_auth_on_first_use (current default posture)
  → Bifrost has oauth_config but no registered token in config.db
  → No 7-day expiry clock running on idle capability
  → Operator initiates OAuth flow when the capability is first needed

authenticated_dormant
  → OAuth completed; token stored in config.db
  → Connection active but zero tools exposed to any VK
  → Tools require an M6 capability lease to become visible

jit_leased
  → Active M6 capability lease grants tools to a specific VK
  → Tools visible for lease duration only
  → Lease expiry/revocation returns to authenticated_dormant
```

**Preferred posture for rarely-used capability:** `ready_auth_on_first_use`. This avoids mandatory 7-day reauthorization cycles for a dormant capability. OAuth is initiated only when the operator decides to activate it.

---

## OAuth Architecture

### One-time enrollment (operator-initiated)

**Pre-flight information to confirm before opening browser:**
- Requested scopes: `mcp`
- Default spending cap: $10 (OpenRouter default — operator should set a deliberately low custom cap)
- Token expiry: 7 days from consent
- OpenRouter account: operator's account at openrouter.ai

**Enrollment procedure:**

1. Confirm Bifrost is running: `GET http://127.0.0.1:8080/health → 200`
2. Query Bifrost client API for pending OAuth URL:
   ```powershell
   Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/mcp/clients" -Headers @{Authorization="Bearer $env:BIFROST_ADMIN_KEY"} | ConvertTo-Json
   # Find the openrouter client entry → pending_oauth_url
   ```
3. Open `pending_oauth_url` in browser
4. OpenRouter consent screen appears — set spending cap, confirm scopes, approve
5. Bifrost receives callback → exchanges code → stores token in `config.db`
6. State transitions to `authenticated_dormant`

**Post-enrollment confirmations (no token values printed):**
- `GET /api/mcp/clients` → openrouter status = `connected` or `active`
- `config.db` file size increases (token stored; treat as secret-bearing)
- Token absent from `config.json`, source renderers, logs, IDE configs, Git
- Revocation possible at any time: see **Revocation** section

### Token storage

| Location | Content | Classification |
|---|---|---|
| `H:\AgentRuntime\bifrost\data\config.db` | OAuth token (possibly encrypted — unverified) | **SECRET-BEARING — treat as sensitive** |
| `renderers/bifrost/config.json` | `oauth_config` with public params only (server_url, scopes) | Safe to commit |
| `H:\AgentRuntime\bifrost\config.json` | Same as renderers copy before OAuth; may gain `oauth_config_id` after | Runtime only — never commit |
| Windows env, IDE configs, Git | Nothing | Enforced |

> **Security note:** The Bifrost documentation states "encrypted token storage at rest" for config.db, but this has not been verified against source code. Until verified, treat `config.db` and all its backups as secret-bearing.

### Reauthorization

Token expires after 7 days. With `ready_auth_on_first_use` posture, the clock starts only when enrollment is triggered. Reauthorization:
1. Revoke old key at `openrouter.ai/keys`
2. Re-run enrollment procedure above
3. New 7-day token stored in config.db

The durability audit (`ops/Test-AgentCoreDurabilityAndPlacement.ps1`) issues a `WARNING` 48 hours before expiry. The audit **never** attempts to approve a new OAuth grant automatically.

### Revocation

```
1. Navigate to openrouter.ai/keys
2. Find the Bifrost-created key → Revoke
3. State returns to ready_auth_on_first_use
4. No tools are exposed during the revoked state
5. Re-enroll when needed
```

---

## Tool Inventory (16 tools, verified 2026-07-17)

### Group: openrouter-discovery-read (11 tools) — `jit_short`
Short task-scoped JIT lease. No approval required.

| Tool | Purpose |
|---|---|
| `list-models` | Search and filter the full live model catalog |
| `get-model` | Full details for one model by author/slug |
| `list-model-endpoints` | Which providers serve a model, with price/latency |
| `list-providers` | Available providers for routing preferences |
| `list-daily-model-rankings` | Most-used and trending models by token volume |
| `list-app-rankings` | Apps driving most OpenRouter traffic |
| `list-benchmarks` | Third-party quality scores (Artificial Analysis, Design Arena) |
| `list-task-classifications` | OpenRouter traffic breakdown by task type |
| `search-docs` | Search full OpenRouter documentation |
| `view-skills` | Read bundled skill files from OpenRouter knowledge base |
| `ping` | Health check |

### Group: openrouter-account (3 tools) — `operator_scope`
Operator scope required. Approval required.

| Tool | Purpose |
|---|---|
| `get-credits` | Remaining account credit balance |
| `get-generation` | Cost, token counts, provider for a specific generation |
| `send-feedback` | Report a problem with one of your own generations |

### Group: openrouter-billable (2 tools) — `billable_approval` — **DENIED BY DEFAULT**
These tools are in `denied_tools` and require: operator approval + declared cost ceiling + invocation bound + expiry + per-action confirmation.

| Tool | Purpose | Risk |
|---|---|---|
| `send-message` | Send a message to any model | **Billable inference** |
| `generate-image` | Generate an image from a text prompt | **Billable inference** |

**Never include** repository source, secrets, credentials, private records, or unrelated project context in billable payloads.

---

## JIT Lease Activation

### Discovery group (openrouter-discovery-read)

1. Request a lease via the M6 capability lease system:
   ```python
   # Via agentcore workflow or direct lease API
   # tool_group_id: "openrouter-discovery-read"
   # max_duration_seconds: 3600 (1h max per lease_defaults)
   # max_invocations: 100 (per lease_defaults)
   # requires_approval: false (per lease_defaults)
   ```
2. M6 records the lease in PostgreSQL `capability_leases` table
3. **Bifrost activation** (current: manual config update + restart):
   - Add `openrouter` to the relevant capability profile's `allowed_server_ids` temporarily
   - OR update the VK config via Bifrost API to include openrouter tools
   - Re-render and restart Bifrost
4. Discovery tools become visible in tools/list for the lease duration
5. On lease expiry: remove from profile/VK, re-render, restart
6. _Planned:_ Bifrost API integration with M6 leases for dynamic tool injection without restart

### Billable group (openrouter-billable)

Additional requirements beyond standard JIT:
- Operator declares exact cost ceiling (e.g., $0.50)
- Operator declares max invocation count
- Exact prompt/model/cost approved before execution
- No repository source code, secrets, or private project context in payload
- After use: lease immediately revoked, no carryover

---

## Failure and Degraded Behavior

| State | Symptom | Impact | Recovery |
|---|---|---|---|
| `ready_auth_on_first_use` | `oauth2 config not found` in Bifrost log | Zero tools (expected) | Run OAuth enrollment |
| OAuth expired/revoked | Bifrost marks client disconnected | Zero tools | Revoke + re-enroll |
| Endpoint unreachable | Bifrost connection timeout | Zero tools; gateway healthy | Check network; OpenRouter status page |
| Tool drift (new tools added) | tools/list count != 16 | Audit WARN | Re-classify and update registry |

The AgentCore gateway remains healthy in all failure states. No IDE is affected by OpenRouter degradation.

---

## Why IDE Configs Remain Unchanged

OpenRouter MCP is added once behind Bifrost. Every enrolled non-Swarm IDE already uses `agentcore-gateway` at `http://127.0.0.1:8080/mcp`. No per-IDE MCP config change is required or permitted. Tool discovery through the gateway gives all IDEs access to OpenRouter tools after a JIT lease is activated.

---

## Monitoring and Audit

Checks in `ops/Test-AgentCoreDurabilityAndPlacement.ps1`:
- `openrouter` registered exactly once; status = dormant
- Not in any `capability_profiles[*].allowed_server_ids`
- No direct openrouter entries in IDE configs
- Bifrost client status: not in error/reconnect_loop
- OAuth expiry warning: ≥48h notice, alert only (no auto-reauth)
- tools/list: zero openrouter tools unless lease active
- Billable tools absent from all VK tool lists
- `log_content: false` enforced for openrouter client
- No token literals in source files or renderers
- config.db classified as secret-bearing (restricted permissions, not in Git)
- JIT lease cleanup: no expired leases still marked active in PostgreSQL

---

## Rollback

```powershell
# 1. Disable openrouter in registry
# Set "enabled": false in contracts/bifrost-upstream-mcp-registry.json -> openrouter

# 2. Re-render
python D:\github\agentcore-control-plane\scripts\bifrost\render_bifrost_config.py

# 3. Restart Bifrost
Stop-ScheduledTask  -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Start-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'

# 4. Revoke OAuth token (optional but recommended)
# openrouter.ai/keys -> find and revoke the Bifrost key

# 5. Validate gateway healthy + openrouter tools absent
```

No IDE configs need to be changed during rollback.
