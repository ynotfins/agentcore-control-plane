# Context Engine Final Acceptance — 2026-08-02 (revised)

**Authority:** AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE  
**Status:** ACCEPTED — prior provisional report superseded; false residuals closed with live evidence

## Repository table (live)

| Repo | Branch | Commit | Remote |
|---|---|---|---|
| `agentcore-control-plane` | `main` | see post-commit SHA after this acceptance push | `https://github.com/ynotfins/agentcore-control-plane.git` |
| `agentcore-context-engine` | `main` | `57c32fe79a6bd20d45b535f00f101a8540603f9f` (+ CERTIFICATION_NOTE commit) | `https://github.com/ynotfins/agentcore-context-engine` (private) |
| `swarmclaw` | `local/swarm-ecosystem-s5` | `b28f558b11fe42ef97df629e3092f28d86d43578` | origin pushed |
| `swarm-ecosystem-control` | `master` | `98576b98cc5457978fd026c97519c175446fd473` | origin |

Inherited Langfuse/M6–M8 WIP in control-plane remains **unstaged**.

## Contradiction closure

| # | Prior false residual | Resolution |
|---|---|---|
| 1 | Claimed 105/105 while portability failed | Fixed hard-coded `D:\` docs; **110 passed** (pytest) + ruff + mypy |
| 2 | SwarmClaw `void` vs uncommitted `await` | Committed+pushed `await` at `b28f558b`; tree clean |
| 3 | RUN9 oversold as live cert | Reclassified deterministic-only; empty evidence / null completed_at documented |
| 4 | M1 closed despite failures | Re-opened criteria; closed only after native hosts + RUN11 live + reviews |
| 5 | “No GitHub remote” for CE | Remote exists; `main` at `57c32fe` |
| 6 | Codex companion_only | Native hooks installed+certified; `live_validated_native_hooks` |
| 7 | Claude “not installed” | Claude Code present; native hooks installed+certified |
| 8 | Cursor bootstrap ≠ signed proof | `CURSOR_DEVICE_PROOF_LIVE_2026-08-02.json` includes signed/unsigned/replay/project mismatch + restore |
| 9 | Unsigned Bifrost MCP writes | **Option B implemented:** write tools always require `device_assertion`; LangGraph `memory_gateway` signs; reads remain legacy under window. Option C (Bifrost VK middleware) deferred — ask Tony only if unsigned reads must also be closed without signed clients |

## Host matrix (live)

| Host | Mode | Certification | Backup |
|---|---|---|---|
| Cursor | native-hooks | `live_validated_native_hooks_signed_gateway` | Stage B project hooks |
| Claude Code | native-hooks | `live_validated_native_hooks` | `…\rollbacks\native-hooks\claude-code\20260802T072226Z` |
| Codex | native-hooks | `live_validated_native_hooks` | `…\rollbacks\native-hooks\codex\20260802T072225Z` (Stop audit preserved) |
| Generic MCP | companion-cli | `companion_only_not_automatic` | N/A |

## LangGraph certification

### RUN9 — deterministic topology only (not live-model)
- Artifact: `CONTEXT_ENGINE_LANGGRAPH_RUN9_RECLASSIFIED_2026-08-02.md`
- Mode: `AGENTCORE_WORKER_MODE=deterministic`
- Must not be cited as cloud-worker certification

### RUN11 — live cloud worker (authoritative)
- File: `CONTEXT_ENGINE_LANGGRAPH_RUN11_LIVE_2026-08-02.json`
- `run_db_id`: `c376e23d-a2c5-4844-b8a9-f02cd905f690`
- `thread_uuid`: `034a28db-a7b4-4c9f-a967-a3ea00091130`
- Status: `completed` (DB `completed_at` still null — known metadata gap; status column is completed)
- Model: `gemini:gemini-3.6-flash` (OpenRouter transport)
- Checkpoints: **23**
- Evidence rows: **6** (builder/critic/micro for M1.1.1 and M1.2.1)
- Judge: `proceed`, critic scores `1.0`
- Deliverable: `CERTIFICATION_NOTE.md` in context-engine root
- Note: builder used project root path rather than `D:\agentcore-worktrees\…` — documented residual isolation hardening

## Device enforcement posture

- Policy mode remains `legacy_compat` for **unsigned reads** during migration.
- **Writes** require cryptographic assertions regardless of policy mode (Option B).
- Temporary `required` drill proven for Cursor path; restored afterward.
- Promoting full `required` (signed reads too) needs either signed MCP clients for all ordinary IDE tool calls or Option C Bifrost identity binding (authority decision).

## Independent review

- `audits/INDEPENDENT_REVIEW_CONTEXT_ENGINE_2026-08-02.md` — **PASS**

## Operator commands

```powershell
cd D:\github\agentcore-control-plane\scripts
python -m agentcore workflow status --run c376e23d-a2c5-4844-b8a9-f02cd905f690 --json
python -m agentcore workflow evidence --run c376e23d-a2c5-4844-b8a9-f02cd905f690 --json
python -m agentcore workflow topology
# Studio (dev only — not production checkpoints)
python -m agentcore workflow studio --port 2024 --no-browser
```

## Storage matrix (logical vs physical)

| Plane | Logical ownership | Physical (this PC) |
|---|---|---|
| AgentCore PG18 | AgentCore | `127.0.0.1:55433` / PostgreSQL 18 |
| Bifrost gateway | AgentCore | `127.0.0.1:8080` |
| Neutral SwarmRecall | Machine-level neutral | `127.0.0.1:3300`; hot data `H:\SwarmData\recall` |
| SwarmClaw SQLite/tasks | Swarm runtime | `H:\SwarmData\claw` |
| Source | Git | `D:\github\…` |

## True residuals (not false)

1. DB `wf_runs.completed_at` not set when status=`completed` (metadata bug; status is authoritative).
2. LangGraph DA builder path used project root instead of isolated worktree path in RUN11.
3. Full enforcement `required` for **reads** not enabled (Option B write-only; Option C needs Tony if desired).
4. Cursor IDE MCP discovery was intermittently unavailable during sessions (Bifrost itself healthy with auth-required).
