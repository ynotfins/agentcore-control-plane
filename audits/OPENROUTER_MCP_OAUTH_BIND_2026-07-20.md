# OpenRouter MCP OAuth Bind Evidence (2026-07-20)

**Claim:** `OPENROUTER MCP AVAILABLE THROUGH AGENTCORE-GATEWAY`  
**No new OAuth consent issued. No duplicate OpenRouter MCP client created. No secrets printed in this artifact.**

## Pre-restart proof

| Check | Result |
| --- | --- |
| Backup `E:\AgentCore-Backups\bifrost-pre-oauth-20260720-000116` | present |
| SHA256MANIFEST.json | 4/4 OK |
| `data/config.db` ACL | `ynotf`, Administrators, SYSTEM only |
| `BIFROST_ENCRYPTION_KEY` | present User+Process; launcher copies User env |
| OpenRouter MCP clients | exactly 1 (`56631c8f-…`) |
| OAuth config `aa25b02d-…` | `authorized`; token `310917b6-…` encrypted |
| Runtime `oauth-clients.json` | only `oauth_config_id` + `mcp_client_id` |
| Runtime `config.json` | `oauth_config_id` present; no fresh `oauth_config` |
| Git renderers | sanitized pre-enrollment `oauth_config` (no runtime IDs) |
| VK OpenRouter tools pre-bind | 0 on all checked VKs |

## Restart

| Field | Value |
| --- | --- |
| Owner | `\AgentCore\AgentCore-Bifrost-Gateway` |
| Old PID | 5524 (start 2026-07-20 00:29:13) |
| New PID | 15976 (start 2026-07-20 01:22:10) |
| Health | `{"status":"ok","components":{"db_pings":"ok"}}` |
| Process count | 1 |
| Manual `bifrost-http.exe` launch | no |

## Post-restart binding

| Check | Result |
| --- | --- |
| OAuth status | `authorized` (same config + same token id) |
| Client `oauth_config_id` | `aa25b02d-…` |
| Client state | `connected` |
| Log | `[Bifrost MCP] Connected to MCP server 'openrouter'` at 01:22:11 |
| `complete-oauth` | **not required** |
| Duplicate clients | none |
| New pending OAuth configs | none |
| `oauth2 config not found` after restart | absent |

## Authenticated inventory

Live tools (20), hash SHA-256:

`83d1a8d3b4e259ebec5fb511a02fdc664670516bceb2b45da010871ad3ada52e`

```
generate-image, generate-speech, get-credits, get-generation, get-model,
get-preset, list-app-rankings, list-benchmarks, list-daily-model-rankings,
list-model-endpoints, list-models, list-presets, list-providers,
list-task-classifications, ping, search-docs, send-feedback, send-message,
transcribe-audio, view-skills
```

Reconcile vs registry:

- `permitted_tools` (14): all present live
- `denied_tools` present live: `send-message`, `generate-image` (must remain ungated)
- live-only unclassified: `generate-speech`, `get-preset`, `list-presets`, `transcribe-audio`

## Lease / profile proofs

| Proof | Result |
| --- | --- |
| builder without lease | 0 OpenRouter tools; memory = 10 |
| reviewer without lease | 0 OpenRouter tools; memory = 10 |
| operator without lease | 0 OpenRouter tools; memory = 10 |
| discovery lease + VK grant | operator sees exactly 11 `openrouter-*` discovery tools |
| account/billable on discovery lease | not visible |
| `openrouter-list-models` limit=1 | OK |
| revoke lease + VK remove | OpenRouter tools = 0 |
| short lease expiry + VK remove | OpenRouter tools = 0 |
| OAuth after lease expiry | still `authorized` |
| paid / billable calls | **0** |

## Orphan key dashboard

**Paused for operator:** compare OpenRouter Keys dashboard timestamps for Bifrost/MCP-labeled keys from failed pending attempts. Revoke orphans only. Do not revoke the working authorized grant backing encrypted token `310917b6-…`.

## Invariants

- No new authorize URL / browser consent
- No duplicate OpenRouter MCP client
- No secrets in Git / docs / this evidence
- Ten-tool `agentcore-memory` surface unchanged
- Swarm untouched
