# Overnight Readiness Status — AgentCore / Swarm / Bifrost

**Timestamp:** 2026-08-09T05:35-04:00  
**Scope:** Read-only live checks from `@D:\github\agentcore-control-plane`, plus repo-only Bifrost hardening work in `@D:\github\agentcore-control-plane-bifrost-hardening`.  
**No live service, IDE, Swarm runtime, database, or scheduled-task mutation was performed by this report.**

**Update 2026-08-09T05:50-04:00:** Bifrost hardening branch `codex/bifrost-production-hardening` was merged into `main` as repo source only. Live Bifrost runtime, scheduled tasks, Cursor config, Swarm, and databases remain unmodified by the merge.

## Authority model retained

- AgentCore owns Bifrost, `agentcore-gateway`, `agentcore-memory`, PG18 exact evidence/recovery/policy, Context Engine, and LangGraph checkpoints.
- SwarmClaw/Sally owns Swarm runtime, agents, sessions, tasks, recovery, SwarmVault, and Swarm lifecycle.
- Neutral SwarmRecall is the shared PC-native semantic memory/context plane only through bounded server-side adapters.
- Ordinary IDEs must use a single `agentcore-gateway` MCP entry and must not receive raw SwarmRecall, SwarmVault, Meilisearch, PostgreSQL, or direct SQL credentials.

## Current live checks

| Area | Evidence | Result |
| --- | --- | --- |
| Bifrost health | `Invoke-WebRequest http://127.0.0.1:8080/health` | HTTP 200, `{"status":"ok","components":{"db_pings":"ok"}}` |
| Bifrost status | `ops\bifrost\Get-BifrostStatus.ps1` | `BIFROST_STATUS_OK`; memory tools 10; ordinary project-router tools 0; Skills Hub >= 3; total tools 34 |
| Full Bifrost validator | `ops\bifrost\Test-AgentCoreBifrostGateway.ps1` | Failed only because Cursor global MCP has extra entries |
| LangGraph topology | `scripts\.venv\Scripts\python.exe -m agentcore workflow topology --json` from `scripts\` | fingerprint `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32`; 15 nodes; production PostgresSaver |
| H-drive Swarm root | `Test-Path H:\SwarmData`; directory inventory | Present; expected top-level roots visible |
| Swarm loopback ports | `netstat` probe | `:3300`, `:7700`, `:3456`, and `:65432` listening |
| AgentCore PG18 port | `netstat` probe | `:55433` listening |
| Sally/SwarmClaw orchestrator | Operator-provided Sally result | `Canary passed cleanly... ORCHESTRATOR_OK` |

## Current blockers before production work

1. **Cursor global MCP is not clean.** `@C:\Users\ynotf\.cursor\mcp.json` currently has three servers: `agentcore-gateway`, `codegraph`, and `repomix`. This violates the single-gateway baseline and causes `Test-AgentCoreBifrostGateway.ps1` to fail.
2. **Sally evidence is health evidence, not full Swarm autonomous acceptance.** `ORCHESTRATOR_OK` proves the orchestrator canary is healthy, but full SwarmRecall/SwarmVault/autonomous-runtime acceptance still needs Sally's service table, Recall/Vault canaries, autonomous team canary, and no-cross-write evidence.
3. **Bifrost hardening is source-merged but not live-rolled-out.** `main` contains the hardening source changes, but live scheduled tasks/config have not been changed.
4. **H: dirty-bit proof was not repeated by this non-elevated shell.** `fsutil dirty query H:` returned access denied in this session. The operator's prior elevated check showed `H:` was not dirty and `chkdsk H: /scan` found no problems.

## Bifrost hardening branch progress

Worktree: `@D:\github\agentcore-control-plane-bifrost-hardening`  
Branch: `codex/bifrost-production-hardening`  
Latest branch commit: `6346557 fix bifrost installer transaction gaps`
Merged to `main`: `merge bifrost production hardening`

Closed in the branch:

- installer now writes both managed config projections:
  - `<RuntimeRoot>\config.json`
  - `<RuntimeRoot>\config\config.json`
- installer rollback now restores both config projections.
- staged config activation now requires basic semantic Bifrost shape, not just any JSON object.

Branch and merged-main validation:

- targeted RED tests failed before implementation for the second config projection and semantic config validation.
- targeted tests now pass.
- `python -m pytest scripts\bifrost -q` -> `49 passed` on the branch and on merged `main`.
- `python scripts\bifrost\acceptance_lifecycle_watchdog.py` -> `BIFROST_WATCHDOG_ACCEPTANCE_OK`.
- `python scripts\bifrost\validate_contracts.py` -> pass.
- `python scripts\bifrost\validate_output_schemas.py` -> pass.
- PowerShell parser check for `Install-AgentCoreBifrostGateway.ps1` -> pass.
- changed-content secret scan -> pass.

## Next required actions

1. Clean Cursor global MCP back to the single `agentcore-gateway` entry through approved live IDE config procedure or explicit operator approval.
2. Re-run `ops\bifrost\Test-AgentCoreBifrostGateway.ps1`; it should pass after Cursor global MCP cleanup.
3. Have Sally provide full Swarm service/Recall/Vault/autonomous canary acceptance, not just orchestrator health.
4. Perform governed live Bifrost rollout only after backup, rollback plan, and operator approval for scheduled-task/config mutation.
5. Run LangGraph production canary and SwarmClaw autonomous canary, then create the restore-point report.
