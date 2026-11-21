# Independent review: AUTH-2026-11-20-AGENT-DISPATCH-LIVE

**Verdict:** ACCEPT (second pass, after blocking findings were fixed)
**Reviewer role:** independent_reviewer. This was a fresh-context, read-only review agent; the first pass returned REJECT with four blocking findings.
**Scope:** register `agent-dispatch` in Bifrost for builder/ide/grokbot (P1), retire `pi-agents` (P2), start the dispatcher with the gateway (P3), move the bounded-implementation role from Cursor to Devin, and add a silent watchdog.

## First pass: REJECT

| # | Blocking finding | Resolution |
| --- | --- | --- |
| 1 | `contracts/global-agent-policy.yaml` still named the retired `pi-agents` shim as the only governed Pi path | Both Pi routing rules now name `agent-dispatch`; `pi-agents` is rollback-only |
| 2 | `CONTEXT_BLOCK.md` still assigned bounded implementation to Cursor | Row and two bullets now name Devin; Stage B rows untouched |
| 3 | `WORKSTATION_PARALLEL_SUBAGENT_INFRASTRUCTURE.md` still described `pi-agents` as current | Status, access path, tools, delegation law and rollback now describe `agent-dispatch` |
| 4 | `DORMANT_MCP_CAPABILITY_CATALOG.md` still listed `pi-agents` as active | Row now reads disabled/retired |

## Second pass: ACCEPT

- Findings 1-4 verified resolved; no new contradictions introduced.
- Watchdog hardening verified: corrupt cooldown stamp tolerated, cooldown also written on failure, and a spawned-but-unready process is stopped before the throw.
- Remaining non-blocking items were fixed in the same commit (policy rule-id pointer, rollback path, historical note tail).

## Evidence recorded here

- Rollback copies of every edited file (`*` at this level, in the timestamped subdirectory).
- `before-hashes.json` / `after-hashes.json` (10 files).
- `bifrost-runtime-config.json` (pre-change runtime config).

## Checks run by the author

| Check | Result |
| --- | --- |
| `scripts/validate_authority_lock.py` | PASS |
| `scripts/bifrost/validate_contracts.py` | PASS |
| `scripts/validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md` | PASS |
| `ops/bifrost/Test-AgentCoreSilentAutomationTasks.ps1` | PASS, 21 tasks |
| Live gateway: Code Mode files show `agent_dispatch/`, no `pi_agents/` | PASS |
| Live gateway: `agents_list`, `agent_run(pi)`, 3-way `agents_parallel` | PASS |
| Watchdog: killed dispatcher, task run, healthy again | PASS |
