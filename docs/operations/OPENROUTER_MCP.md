# OpenRouter MCP — Canonical Runbook

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`  
**Registry ID:** `openrouter`  
**Bifrost client name:** `openrouter`  
**Status:** OPENROUTER MCP REGISTERED DORMANT BEHIND BIFROST — OAUTH AND JIT ACTIVATION NOT VALIDATED  
**Last tool inventory:** 16 tools claimed 2026-07-17 — **pre-auth, not yet verified by authenticated live tools/list**  
**Updated:** 2026-07-18  

> **Accepted state of commit 96c2528:** dormant scaffold only.  
> Not accepted as a completed OpenRouter MCP deployment.  
> Required before status may advance: encryption verification (§ Encryption Blocker), isolated
> OAuth create/restart test, operator browser consent, authenticated tools/list, JIT lease
> proof, restart/rerender proof, Cursor + Codex + third-client read-only calls.  
> Do not use `OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY` until all acceptance
> gates in § Complete Acceptance pass.

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

## Encryption Blocker — STOP BEFORE OAUTH

**BIFROST_ENCRYPTION_KEY is ABSENT from the scheduled-task runtime.**

Evidence (2026-07-18):
- `[System.Environment]::GetEnvironmentVariable("BIFROST_ENCRYPTION_KEY", "User")` → null
- `[System.Environment]::GetEnvironmentVariable("BIFROST_ENCRYPTION_KEY", "Machine")` → null
- The Bifrost launcher (`ops/bifrost/Launch-AgentCoreBifrostGateway.ps1`) copies Windows User-scope
  env vars into the Bifrost process; if the key is absent at launch time, Bifrost has no encryption key.

**Consequence:** Without `BIFROST_ENCRYPTION_KEY`, Bifrost stores OAuth material (access token,
refresh token) in `config.db` in plaintext. `config.db` must be treated as secret-bearing under
all circumstances, but plaintext storage violates the credential-storage policy.

**Required before OAuth can be initiated:**

1. Generate a strong random encryption key (operator — never share, never print).
2. Set `BIFROST_ENCRYPTION_KEY` in Windows User-scope environment variables only:
   ```powershell
   # Generate (example — operator sets; agent never generates or stores):
   # [System.Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
   # Store via Windows credential manager or securely; then:
   [System.Environment]::SetEnvironmentVariable("BIFROST_ENCRYPTION_KEY", "<value>", "User")
   ```
3. Restart the Bifrost scheduled task so the new variable is loaded.
4. Verify the variable is present in the process (name only — no value):
   ```powershell
   # In the running bifrost process context:
   [System.Environment]::GetEnvironmentVariable("BIFROST_ENCRYPTION_KEY", "User") -ne $null
   ```
5. Verify Bifrost recognizes encryption as enabled (check Bifrost startup log for encryption-enabled
   message; absence of "encryption disabled" or equivalent).
6. Verify `config.db` ACLs are restricted (operator/SYSTEM only, no Everyone/Users read).
7. Test isolated backup and restore of `config.db` before OAuth token is written.

**Do not initiate OAuth browser consent until this check passes.**

---

## OAuth Architecture

### Lifecycle clarification

OAuth enrollment uses the **Bifrost management API**, not config.json reconciliation.
The renderer writes `oauth_config` (public parameters only: `server_url`, `scopes`) into the
rendered `client_configs` so Bifrost registers the client as OAuth-pending on startup. This is
the **pre-enrollment state**. After enrollment:

- Bifrost returns `oauth_config_id` in the management API response.
- The operator stores `oauth_config_id` in a **runtime-only state file**:  
  `H:\AgentRuntime\bifrost\state\oauth-clients.json` (never committed to Git).
- On the next render, the renderer reads this state file and substitutes `oauth_config_id`
  for `oauth_config` in the rendered config, preserving the enrolled binding.
- Re-rendering without the state file reverts to pre-enrollment `oauth_config` (creates a new
  pending client; existing enrolled client may be orphaned — do not re-render after enrollment
  without the state file present).

**Required isolated test before production OAuth:**  
Prove on a test/isolated Bifrost runtime that:  
(a) POST to `/api/mcp/client` with `auth_type=oauth` and `oauth_config` returns `pending_oauth` + `authorize_url` + `oauth_config_id`.  
(b) After consent, the token is stored in config.db.  
(c) Restart with `oauth_config_id` in config.json preserves the token (no new pending_oauth).  
(d) Re-render with `oauth_config` (not `oauth_config_id`) creates a new pending client.  
Document the reconciliation behavior before enabling production OAuth.

### One-time enrollment (operator-initiated)

**Pre-flight checks (all must PASS before opening browser):**
- `BIFROST_ENCRYPTION_KEY` present in Bifrost process: YES (see § Encryption Blocker above)
- `config.db` ACLs restricted: YES
- Bifrost healthy: `GET http://127.0.0.1:8080/health → 200`
- Requested scopes: `mcp`
- Default spending cap: $10 (OpenRouter default — operator should set a deliberately low custom cap)
- Token expiry: 7 days from consent
- OpenRouter account: operator's account at openrouter.ai

**Enrollment procedure:**

1. Confirm all pre-flight checks pass.
2. **Create the OAuth client via management API** (POST — required first step):
   ```powershell
   $body = @{
     name = "openrouter"
     connection_type = "http"
     connection_string = "https://mcp.openrouter.ai/mcp"
     auth_type = "oauth"
     oauth_config = @{ server_url = "https://openrouter.ai"; scopes = @("mcp") }
   } | ConvertTo-Json -Depth 5
   $resp = Invoke-RestMethod -Uri "http://127.0.0.1:8080/api/mcp/client" -Method POST `
     -Headers @{Authorization="Bearer $env:BIFROST_ADMIN_KEY"; "Content-Type"="application/json"} `
     -Body $body
   # Expected: resp.status = "pending_oauth"
   # Save runtime state (no token values in this call):
   $state = @{ openrouter = @{ oauth_config_id = $resp.oauth_config_id; mcp_client_id = $resp.mcp_client_id } }
   $stateDir = "H:\AgentRuntime\bifrost\state"
   New-Item -ItemType Directory -Force -Path $stateDir | Out-Null
   $state | ConvertTo-Json | Set-Content "$stateDir\oauth-clients.json" -Encoding UTF8
   Write-Host "authorize_url (open in browser): $($resp.authorize_url)"
   ```
3. Note the `authorize_url` from the response (do not print or log the full URL in persistent artifacts).
4. Open `authorize_url` in browser — operator browser consent only.
5. OpenRouter consent screen appears — set spending cap, confirm scopes, approve.
6. Bifrost receives callback → exchanges code → stores token in `config.db` (encrypted if key present).
7. State transitions to `authenticated_dormant`.
8. Re-render config.json to embed `oauth_config_id`:
   ```powershell
   python D:\github\agentcore-control-plane\scripts\bifrost\render_bifrost_config.py
   # Renderer reads H:\AgentRuntime\bifrost\state\oauth-clients.json
   # Emits oauth_config_id for openrouter (not oauth_config)
   ```

**Post-enrollment confirmations (no token values printed):**
- `GET /api/mcp/clients` → openrouter status = `connected` or `active`
- `config.db` file size increases (token stored and encrypted)
- `H:\AgentRuntime\bifrost\state\oauth-clients.json` contains `oauth_config_id` (not token values)
- Token absent from `config.json`, source renderers, logs, IDE configs, Git
- Revocation possible at any time: see **Revocation** section

### Token storage

| Location | Content | Classification |
|---|---|---|
| `H:\AgentRuntime\bifrost\data\config.db` | OAuth token (encrypted — requires BIFROST_ENCRYPTION_KEY) | **SECRET-BEARING — restricted ACLs required** |
| `H:\AgentRuntime\bifrost\state\oauth-clients.json` | `oauth_config_id` and `mcp_client_id` only (no token values) | Runtime only — never committed to Git |
| `renderers/bifrost/config.json` | `oauth_config` public params pre-enrollment; `oauth_config_id` post-enrollment | Post-enrollment: no secret content |
| `H:\AgentRuntime\bifrost\config.json` | Rendered from above; `oauth_config_id` after enrollment | Runtime only — never commit |
| Windows env, IDE configs, Git | Nothing | Enforced |

> **Security note:** `config.db` encryption requires `BIFROST_ENCRYPTION_KEY` to be set before
> OAuth enrollment. Without it, tokens are stored in plaintext. Always verify encryption is
> active before initiating consent. `config.db` and all backups are secret-bearing regardless
> of encryption state — restrict ACLs and backup only to `E:` and `G:` secure paths.

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

## Tool Inventory (claimed 2026-07-17 — pre-auth, pending live verification)

> **Status:** These tools were claimed from OpenRouter documentation and pre-auth discovery.
> They have NOT been verified by an authenticated `tools/list` call.
> Accept only after authenticated live `tools/list` proves each tool exists.
> Authenticated verification requires OAuth enrollment (blocked by § Encryption Blocker above).
>
> Official published OpenRouter documentation lists 11 tools and states only `send-message` is
> billable. The following tools are claimed but need reconciliation against live inventory:
> `list-task-classifications`, `view-skills`, `ping`, `send-feedback`, `generate-image`.
> Do not infer `generate-image` from the separate OpenRouter API server-tools feature.

### Group: openrouter-discovery-read (11 claimed tools) — `jit_short`
Short task-scoped JIT lease. No approval required.

| Tool | Purpose | Verified |
|---|---|---|
| `list-models` | Search and filter the full live model catalog | pre-auth only |
| `get-model` | Full details for one model by author/slug | pre-auth only |
| `list-model-endpoints` | Which providers serve a model, with price/latency | pre-auth only |
| `list-providers` | Available providers for routing preferences | pre-auth only |
| `list-daily-model-rankings` | Most-used and trending models by token volume | pre-auth only |
| `list-app-rankings` | Apps driving most OpenRouter traffic | pre-auth only |
| `list-benchmarks` | Third-party quality scores (Artificial Analysis, Design Arena) | pre-auth only |
| `list-task-classifications` | OpenRouter traffic breakdown by task type | **UNVERIFIED** |
| `search-docs` | Search full OpenRouter documentation | pre-auth only |
| `view-skills` | Read bundled skill files from OpenRouter knowledge base | **UNVERIFIED** |
| `ping` | Health check | **UNVERIFIED** |

### Group: openrouter-account (3 claimed tools) — `operator_scope`
Operator scope required. Approval required.

| Tool | Purpose | Verified |
|---|---|---|
| `get-credits` | Remaining account credit balance | pre-auth only |
| `get-generation` | Cost, token counts, provider for a specific generation | pre-auth only |
| `send-feedback` | Report a problem with one of your own generations | **UNVERIFIED** |

### Group: openrouter-billable (2 claimed tools) — `billable_approval` — **DENIED BY DEFAULT**
These tools are in `denied_tools` and require: operator approval + declared cost ceiling + invocation bound + expiry + per-action confirmation.

| Tool | Purpose | Risk | Verified |
|---|---|---|---|
| `send-message` | Send a message to any model | **Billable inference** | pre-auth only |
| `generate-image` | Generate an image from a text prompt | **Billable inference — source: OpenRouter server-tools, not MCP inventory** | **UNVERIFIED** |

**Total claimed:** 16. **Official documented:** 11 read-only tools. Discrepancy requires authenticated tools/list reconciliation.

**Accepted tool inventory manifest:** not yet committed. To be committed after authenticated tools/list with SHA-256 schema hashes, protocol version, and discovery timestamp.

**Never include** repository source, secrets, credentials, private records, or unrelated project context in billable payloads.

---

## JIT Lease Activation — Bridge DEFERRED

**Current status: Bifrost activation is manual. The M6-to-Bifrost dynamic bridge is not yet implemented.**

Blocker: Bifrost does not currently expose a management API that allows dynamic, lease-scoped
tool injection without a full config.json re-render and process restart. Native Bifrost
virtual-key and tool-group controls may support dynamic grants, but this has not been verified
against the running Bifrost binary. Until a validated, restart-free bridge exists, OpenRouter
remains operator-dormant.

**Required behavior (deferred until M6 bridge is implemented):**
- A valid PostgreSQL M6 lease grants only the named OpenRouter tool group to the requesting
  project/client virtual key.
- No permanent `allowed_server_ids` grant is created.
- No wildcard is used.
- Lease duration and invocation count are enforced.
- Billable tools require operator approval and exact cost ceiling.
- Lease expiration automatically removes the tools.
- Explicit revocation automatically removes the tools.
- Process interruption cannot leave an expired grant active.
- No normal workflow requires manual source edits or a full Bifrost restart.
- Concurrent projects cannot inherit one another's grant.

**Current workaround (manual, operator-only):**
1. Request a lease via the M6 capability lease system.
2. Manually update the relevant VK config via Bifrost management API to add openrouter tools.
3. Monitor expiry; manually revoke when the lease expires.
4. This approach does NOT meet the zero-touch JIT requirement above.

### Discovery group activation (manual workaround only)

```python
# Via agentcore workflow or direct lease API
# tool_group_id: "openrouter-discovery-read"
# max_duration_seconds: 3600 (1h max per lease_defaults)
# max_invocations: 100 (per lease_defaults)
# requires_approval: false (per lease_defaults)
```

After lease is recorded in PostgreSQL `capability_leases`:
- Operator manually adds `openrouter` tools to the operator VK via Bifrost management API
- Discovery tools become visible in tools/list for the lease duration
- On lease expiry: operator manually removes from VK

### Billable group (openrouter-billable) — additional requirements

Beyond standard JIT (when bridge is implemented):
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
| `BIFROST_ENCRYPTION_KEY` absent | n/a (pre-enrollment blocker) | OAuth blocked | Set key in Windows User env; restart Bifrost |
| OAuth expired/revoked | Bifrost marks client disconnected | Zero tools | Revoke + re-enroll |
| Endpoint unreachable | Bifrost connection timeout | Zero tools; gateway healthy | Check network; OpenRouter status page |
| Tool drift (new tools added) | tools/list count != manifest | Audit WARN | Re-classify, update registry and manifest |
| Re-render after enrollment without state file | New pending_oauth; possible orphan client | OAuth disconnected | Restore state file; re-enroll |

The AgentCore gateway remains healthy in all failure states. No IDE is affected by OpenRouter degradation.

---

## Complete Acceptance Gates

Status may not advance to `OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY` until
**all** of the following pass:

| Gate | Requirement |
|---|---|
| STOP-0 | `BIFROST_ENCRYPTION_KEY` present and Bifrost recognizes encryption enabled |
| STOP-1 | `config.db` ACLs restricted; isolated backup/restore succeeds |
| STOP-2 | Isolated test: OAuth create → pending → consent → restart → re-render without binding loss |
| AUTH-1 | Production OAuth browser consent (operator) |
| AUTH-2 | `GET /api/mcp/clients` → openrouter `connected`/`active`; `oauth_config_id` recorded in state file |
| INV-1 | Authenticated `tools/list`; initialize request; negotiated protocol version captured |
| INV-2 | Tool inventory manifest committed with SHA-256 schema hashes and discovery timestamp |
| INV-3 | Claimed additional tools (`list-task-classifications`, `view-skills`, `ping`, `send-feedback`, `generate-image`) accepted only when live tools/list proves they exist |
| LEASE-1 | `list-models` safe call via JIT lease (operator VK) |
| LEASE-2 | `get-model` safe call via JIT lease |
| LEASE-3 | `search-docs` safe call via JIT lease |
| DENY-1 | Reviewer VK denied `get-credits` |
| DENY-2 | Builder VK denied `send-message` |
| DENY-3 | Operator-only account access confirmed |
| BILL-1 | Temporary billable-tool visibility through a lease without executing a paid call |
| BILL-2 | Automatic lease expiration removes tools; explicit revocation removes tools |
| RST-1 | Bifrost restart: OAuth reconnects; `oauth_config_id` preserved in config.json |
| REND-1 | Re-render after enrollment: no OAuth-binding loss (state file present) |
| MEM-1 | Exact 10-tool agentcore-memory invariant confirmed post-enrollment |
| IDE-1 | No direct IDE OpenRouter entries confirmed |
| SWM-1 | No Swarm changes confirmed |
| SEC-1 | Full secret scan: no token literals in source, logs, IDE configs, command history |
| CLI-1 | Cursor read-only call succeeds via gateway |
| CLI-2 | Codex read-only call after Codex enrollment |
| CLI-3 | One additional enrolled client read-only call |

**No paid `send-message` or image request may occur without separate approval for the exact
model, payload, invocation count, and maximum cost.**

---

## Why IDE Configs Remain Unchanged

OpenRouter MCP is added once behind Bifrost. Every enrolled non-Swarm IDE already uses `agentcore-gateway` at `http://127.0.0.1:8080/mcp`. No per-IDE MCP config change is required or permitted. Tool discovery through the gateway gives all IDEs access to OpenRouter tools after a JIT lease is activated.

---

## Monitoring and Audit

Checks in `ops/Test-AgentCoreDurabilityAndPlacement.ps1`:
- OR-0: `BIFROST_ENCRYPTION_KEY` name present in Bifrost scheduled-task env; encryption active
- OR-1: `openrouter` registered exactly once; status = dormant; not in any `capability_profiles[*].allowed_server_ids`; no direct IDE entries
- OR-2: tools/list via operator VK: zero openrouter tools without a confirmed lease; agentcore-memory at exactly 10 tools
- OR-3: `config.db` present; ACLs restrict read to operator/SYSTEM only
- OR-4: No OpenRouter token literals in source files
- OR-5: OAuth status: reports `not_verified` if encryption absent; `pending` / `connected` / `expired` / `revoked` accurately; expiry WARN ≥48h only when authenticated
- OR-6: Runtime config.json contains no token literals
- OR-7: Tool inventory matches accepted manifest (count and schema hashes); drift triggers WARN
- OR-8: `log_content: false` enforced for openrouter client; no content in Bifrost logs
- OR-9: No expired PostgreSQL leases still retaining Bifrost exposure; billable tools absent from permanent VK grants
- OR-10: `oauth_config_id` in state file only (never in source renderers, Git, or logs)

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

# 4. Revoke OAuth token (required — removes Bifrost OAuth record AND OpenRouter dashboard key)
# openrouter.ai/keys -> find and revoke the Bifrost key
# If state file exists: remove H:\AgentRuntime\bifrost\state\oauth-clients.json

# 5. Validate gateway healthy + openrouter tools absent
```

No IDE configs need to be changed during rollback.

---

## Open Interpreter Profile Evidence

**This section is separate from OpenRouter MCP activation.**
Open Interpreter uses the OpenRouter LLM API (inference) — not the OpenRouter MCP server.

| Field | Value |
|---|---|
| Open Interpreter version | 0.0.10 |
| Profile path | `C:\Users\ynotf\AppData\Roaming\interpreter\profiles\autonomous-os.yaml` |
| SHA-256 (current, 2026-07-18) | `C72FF7EE455BE876507506F0EBDA86E7365930EE7487FB63C71EB8BC4F7E70AB` |
| SHA-256 (backup, 2026-07-17 pre-change) | `6644C2264E9330FC479CFA29C0355385F0635AFE81A445E3EBFF183A6E388522` |
| Default model | `minimax/minimax-m3` (verified by grep: `model: "minimax/minimax-m3"`) |
| Provider | `openrouter` (verified: `provider: "openrouter"`) |
| Provider base URL | `https://openrouter.ai/api/v1` |
| OPENROUTER_API_KEY | Referenced by name only — not materialized in YAML (verified: no `sk-or-v1-` literal present) |
| minimax/minimax-m2.7 fallback | **Present** in `fallbacks:` list |
| Change in commit 96c2528 | **None** — autonomous-os.yaml is not source-controlled; git show confirms no change |
| Difference from backup | Added `- "minimax/minimax-m2.7"` to `fallbacks:` and corresponding system-instruction lines |
| agentcore-gateway unchanged | Confirmed: `C:\Users\ynotf\.cursor\mcp.json` still references `agentcore-gateway` |
| No direct OpenRouter MCP in Cursor mcp.json | Confirmed |

**Rollback path:** `C:\Users\ynotf\AppData\Roaming\interpreter\profiles\autonomous-os.yaml.backup-20260717-221926` (removes minimax-m2.7 fallback; reverts to prior state)
