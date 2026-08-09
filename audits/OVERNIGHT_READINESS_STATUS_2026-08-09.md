# Overnight Readiness Status — AgentCore / Swarm / Bifrost

**Timestamp:** 2026-08-09T05:35-04:00  
**Scope:** Read-only live checks from `@D:\github\agentcore-control-plane`, plus repo-only Bifrost hardening work in `@D:\github\agentcore-control-plane-bifrost-hardening`.  
**No live service, IDE, Swarm runtime, database, or scheduled-task mutation was performed by this report.**

**Update 2026-08-09T05:50-04:00:** Bifrost hardening branch `codex/bifrost-production-hardening` was merged into `main` as repo source only. Live Bifrost runtime, scheduled tasks, Cursor config, Swarm, and databases remain unmodified by the merge.

**Update 2026-08-09T05:45-04:00:** additional read-only probes confirmed the current live Bifrost runtime has not yet been rolled forward to the merged source config, and current Swarm service health endpoints are reachable.

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
| Current SwarmRecall API | `GET http://127.0.0.1:3300/api/v1/health` | HTTP 200, `status:ok`, `services.database:true` |
| Current Meilisearch | `GET http://127.0.0.1:7700/health` | HTTP 200, `status:available` |
| Current SwarmClaw | `GET http://127.0.0.1:3456/api/healthz` | HTTP 200, `ok:true` |
| Current SwarmRecall web | `GET http://127.0.0.1:3400` | HTTP 200, HTML served |
| Current Swarm PG listener | `netstat` | `127.0.0.1:65432` listening |
| Latest Swarm acceptance report | `@D:\github\swarm-ecosystem-control\audits\SALLY_SWARM_PRODUCTION_ACCEPTANCE_20260806.md` | Accepted for local Swarm operation with residuals |

## Current blockers before production work

1. **Cursor global MCP is not clean.** `@C:\Users\ynotf\.cursor\mcp.json` currently has three servers: `agentcore-gateway`, `codegraph`, and `repomix`. This violates the single-gateway baseline and causes `Test-AgentCoreBifrostGateway.ps1` to fail.
2. **Sally evidence is health evidence, not full Swarm autonomous acceptance.** `ORCHESTRATOR_OK` proves the orchestrator canary is healthy, but full SwarmRecall/SwarmVault/autonomous-runtime acceptance still needs Sally's service table, Recall/Vault canaries, autonomous team canary, and no-cross-write evidence.
3. **Bifrost hardening is source-merged but not live-rolled-out.** `main` contains the hardening source changes, but live scheduled tasks/config have not been changed.
4. **H: dirty-bit proof was not repeated by this non-elevated shell.** `fsutil dirty query H:` returned access denied in this session. The operator's prior elevated check showed `H:` was not dirty and `chkdsk H: /scan` found no problems.

## Source-to-live drift that requires rollout approval

| Item | Source state | Live state | Required action |
| --- | --- | --- | --- |
| Bifrost rendered config | `renderers\bifrost\config.json` SHA-256 `062EF7694DF7316D60379E020328696A6D861BF699AB01113508274F8089D3E0` | `F:\AgentCore\runtime\bifrost\config.json` SHA-256 `AF5797CF0E62922AAABD5E8C9259C48452B9213622E21603A9FA1795626717F5` | governed Bifrost install/render rollout |
| Bifrost second config projection | source renderer expects both projections managed | `F:\AgentCore\runtime\bifrost\config\config.json` matches old live config hash | governed Bifrost install/render rollout |
| Bifrost watchdog task | source installer defines `\AgentCore\AgentCore-Bifrost-Watchdog` | task is not installed | approved scheduled-task rollout |
| Gateway task | source launcher path remains repo-owned | live task exists and is running | preserve; update only through governed installer |

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

1. Approve cleanup of `@C:\Users\ynotf\.cursor\mcp.json` back to the single `agentcore-gateway` entry, preserving a timestamped backup.
2. Re-run `ops\bifrost\Test-AgentCoreBifrostGateway.ps1`; it should pass after Cursor global MCP cleanup.
3. Approve governed live Bifrost rollout using the merged installer, including backup, config render, watchdog task install, Task Scheduler Operational logging, and rollback proof.
4. Ask Sally for current full Swarm service/Recall/Vault/autonomous team canary acceptance against the already accepted Swarm production configuration.
5. Run LangGraph production canary and SwarmClaw autonomous canary, then create the restore-point report.

## Morning operator packet

Use this order when the operator returns:

```text
1. Approve live Cursor global MCP cleanup:
   - backup @C:\Users\ynotf\.cursor\mcp.json
   - remove codegraph and repomix from global Cursor MCP
   - keep only agentcore-gateway

2. Validate gateway:
   @D:\github\agentcore-control-plane\ops\bifrost\Test-AgentCoreBifrostGateway.ps1

3. Approve governed Bifrost live rollout:
   - use source already merged to main
   - render/activate both Bifrost config projections
   - install AgentCore-Bifrost-Watchdog
   - enable Task Scheduler Operational logging
   - prove rollback artifacts exist
   - prove BIFROST_STATUS_OK after restart

4. Ask Sally for current full Swarm acceptance:
   - services table
   - Recall write/read/search canary
   - SwarmVault query/context-pack canary
   - autonomous team canary
   - no AgentCore/Bifrost/LangGraph writes

5. Run runtime canaries:
   - LangGraph production canary from @D:\github\agentcore-control-plane\scripts
   - SwarmClaw canary through Sally
   - create final restore-point report
```
