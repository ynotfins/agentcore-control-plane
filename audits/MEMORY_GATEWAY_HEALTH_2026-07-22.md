# AgentCore Memory Gateway Health — 2026-07-22

**Status:** REPAIRED (runtime) + lifecycle PROVED via `agentcore-gateway`  
**Root cause:** PostgreSQL 18 listener at `127.0.0.1:55433` was down (`AgentCore-PostgreSQL18` Windows service Stopped; no accepting connections). Bifrost itself was healthy; `tools/list` showed ten `agentcore-memory` tools; `memory_status` / `startup_context` timed out waiting on DB.

## Investigation

| Check | Result |
| --- | --- |
| Bifrost `/health` | ok |
| `tools/list` agentcore_memory prefix | present (10 permitted tools in registry) |
| agentcore-memory process | stdio child via Bifrost; Python 3.13 `-u scripts/agentcore_memory/server.py` |
| Registry timeout | 30s (not increased) |
| PG18 TCP 55433 | was CLOSED / rejecting |
| Windows service `AgentCore-PostgreSQL18` | Stopped (Automatic); Start-Service required elevation |
| Repair action | `ops/Start-AgentCorePostgres.ps1 -StartIfStopped` via `pg_ctl` (approved ops path) |
| Cognee | available after PG restore (`memory_status`) |
| Bifrost stderr historical | `file already closed` / reconnect churn while DB down; Serena also reconnect-failing (out of scope) |

**Ownership note:** After `pg_ctl` start, port 55433 accepts connections while Windows service may still report `Stopped`. Canonical long-term ownership remains the Windows service (M8). Operator should elevate and start `AgentCore-PostgreSQL18` when possible so service and cluster stay aligned. Do not invent a second cluster.

## Lifecycle proof (via gateway)

| Step | Result |
| --- | --- |
| 1. memory_status | PASS — healthy; PG reachable; migrations include m6.001/m8.* |
| 2. session_open | PASS — session `e1a52554-…` resumed |
| 3. startup_context | PASS — standard-context packet |
| 4. append_event | PASS — event `58f36a3b-…` |
| 5. idempotent repeated append | PASS — `idempotent_replay: true` |
| 6. retrieve_context | PASS |
| 7. pagination / continuation cursor | PARTIAL — page_size honored; confirm cursor field in follow-up if absent from packet |
| 8. expand_source | PASS — exact event payload recovered |
| 9. build_handoff | PASS |
| 10. session_close | PASS — isolation probe session closed |
| 11. resume | PASS — same session_key reopened existing session |
| 12. project isolation | PASS — probe project retrieve did not return `PROJECT_A_PROTECTED_DATA` |
| 13. exactly ten memory tools | PASS — registry `permitted_tools` length 10 |
| 14. no raw admin/database tools | PASS — no sql/admin/postgres/psql in surface |

## Cursor Auto context posture (this chat)

| Field | Value |
| --- | --- |
| provider_policy | cursor-auto |
| actual_model | dynamically routed / not reliably observable |
| active_context_profile | standard-context (conservative model-limit-aware; safe ceiling 98304) |
| durable_history | AgentCore canonical / effectively unbounded |

## Do not

- Increase Bifrost/memory timeouts to hide a hung server
- Modify live registry contracts without evidence they are wrong
- Claim Windows service ownership is healthy while it remains Stopped

## Follow-up

- Elevate and start `AgentCore-PostgreSQL18` so Automatic service owns the cluster after reboot
- Serena Bifrost reconnect failures remain a separate upstream issue
