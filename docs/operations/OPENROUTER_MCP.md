# OpenRouter MCP — Canonical Runbook

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`  
**Registry ID:** `openrouter`  
**Bifrost client name:** `openrouter`  
**Status:** OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY  
**Last tool inventory:** authenticated live discovery = **20 tools** (SHA-256 `83d1a8d3b4e259ebec5fb511a02fdc664670516bceb2b45da010871ad3ada52e`); registry `permitted_tools` = **18** classified tools; `denied_tools` keep `send-message` / `generate-image`  
**Updated:** 2026-07-20  

> **Handoff & Verification Status (2026-07-20 bind + classification):**  
> - **BIFROST_ENCRYPTION_KEY:** Present in Windows User-scope; launcher copies into Bifrost process.  
> - **config.db ACL:** Restricted to `ynotf`, Administrators, SYSTEM.  
> - **OAuth:** Authorized config `aa25b02d-…` + encrypted token bound to live client `56631c8f-…`. Client state `connected`.  
> - **Four-tool classification:** `get-preset`/`list-presets` → discovery JIT; `generate-speech` → media-generation operator JIT; `transcribe-audio` → transcription operator JIT (`raw_untrusted`). Manifest: `contracts/openrouter-tool-manifest.json`.  
> - **JIT bridge:** `scripts/bifrost/jit_vk_bridge.py` — PostgreSQL lease → exact VK `mcp_configs` grant (preserves ids + `mcp_client_name`) → revoke removes; fail-closed.  
> - **Lease proofs:** discovery lease exposes exactly 13 `openrouter-*` discovery tools including presets; revocation returns to zero; memory surface stays exactly 10 tools.  
> - **MCP OAuth key:** Treat dashboard key labeled `MCP: OpenRouter MCP: Bifrost MCP Gateway` as the working grant — do not revoke.  
> - **API inference keys** (`agent-orchestrator`, `cherry`, `langgraph`, `OPENROUTER_API_KEY`) are not MCP OAuth orphans.  

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

authenticated_dormant  ← **current live posture (2026-07-20)**
  → OAuth completed; token stored in config.db
  → Registry `status` remains `dormant` (zero default exposure)
  → Connection may be active but zero OpenRouter tools on VKs without a lease
  → Tools require an M6 capability lease + JIT VK bridge to become visible

jit_leased
  → Active M6 capability lease grants exact named tools to a specific VK
  → Tools visible for lease duration only
  → Lease expiry/revocation returns to authenticated_dormant
```

**Status vocabulary:** registry `status: "dormant"` means zero default exposure. Lifecycle
`authenticated_dormant` means OAuth is bound. Do not confuse the two strings.

**Preferred posture when OAuth is not yet bound:** `ready_auth_on_first_use` (avoids idle
7-day reauth clocks). After bind, remain `authenticated_dormant` until a lease grants tools.

---

## Encryption prerequisite (historical blocker — resolved 2026-07-20)

**Live status:** `BIFROST_ENCRYPTION_KEY` is present in Windows User-scope; the Bifrost launcher
copies it into the process. OAuth bind evidence:
`audits/OPENROUTER_MCP_OAUTH_BIND_2026-07-20.md`.

**Still required before any new OAuth enrollment or re-bind:**

1. Confirm `BIFROST_ENCRYPTION_KEY` is set in Windows User-scope (name only — never print value).
2. Restart `\AgentCore\AgentCore-Bifrost-Gateway` so the process loads the key.
3. Verify `config.db` ACLs are restricted (operator/SYSTEM only).
4. Treat `config.db` and backups as secret-bearing regardless of encryption state.

Without the key, Bifrost may store OAuth tokens in plaintext — do not initiate consent in that state.

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

## Tool Inventory (authenticated 2026-07-20)

Live tools = **20**. Manifest: contracts/openrouter-tool-manifest.json.

### Group: openrouter-discovery-read (13 tools) — jit_short

Includes original catalog tools plus **get-preset** and **list-presets** (read-only). Short project/task-scoped JIT. Zero default exposure.

### Group: openrouter-account (3 tools) — operator_scope

get-credits, get-generation, send-feedback.

### Group: openrouter-media-generation (1 tool) — billable_approval

`generate-speech` — cost-sensitive; operator-approved JIT only; content `raw_untrusted`.

### Group: openrouter-transcription (1 tool) — billable_approval

`transcribe-audio` — sensitive upload + billable processing; operator-approved JIT only;
results `raw_untrusted` unless promoted; never upload repository files, secrets, private records,
or unrelated context.

### Group: openrouter-billable (2 tools) — **DENIED BY DEFAULT**

send-message, generate-image remain in denied_tools. Never grant from discovery leases.

**Never include** repository source, secrets, credentials, private records, or unrelated project context in billable/media/transcription payloads.

---

## JIT Lease Activation — Automatic Bridge

**Status: IMPLEMENTED** via `scripts/bifrost/jit_vk_bridge.py` (hooked from `agentcore_workflow.db.create_jit_lease` / `revoke_lease` / `expire_jit_leases`).

Flow:

```
PostgreSQL capability lease created (tool/group name)
  → ensure openrouter MCP client tools_to_execute ⊆ registry permitted_tools
  → PUT /api/governance/virtual-keys/{vk} with preserved mcp_configs[].id
     + mcp_client_name=openrouter + exact tools_to_execute
  → tools become visible on that VK
  → lease expiry/revocation removes the openrouter mcp_config entry
  → failure leaves tools hidden (deny-by-default)
```

Invariants:
- Idempotent; project/VK scoped (default `vk-agentcore-operator`)
- No wildcard grants; `send-message` / `generate-image` never granted
- Existing mcp_configs IDs preserved (avoids Bifrost 409)
- Restart-safe; rollback-safe; no Bifrost admin tools exposed to graph nodes

### Discovery group activation

```python
from jit_vk_bridge import sync_lease_group
sync_lease_group("openrouter-discovery-read", active=True)   # 13 tools incl. presets
sync_lease_group("openrouter-discovery-read", active=False)  # zero OpenRouter tools
```

Or via M6:

```python
db.create_jit_lease(project_id, "openrouter-discovery-read", step_id, 3600, "discovery")
db.revoke_lease(project_id, lease_id, "openrouter-discovery-read")
```

### Media / transcription (operator-approved)

- `openrouter-media-generation` → `generate-speech` only
- `openrouter-transcription` → `transcribe-audio` only; results `raw_untrusted`; never upload repo/secrets/private records

### Billable group (openrouter-billable) — remains denied

`send-message` and `generate-image` stay in `denied_tools`. Never grant from discovery leases.

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
