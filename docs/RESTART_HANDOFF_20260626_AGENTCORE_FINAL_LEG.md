> **HISTORICAL — SUPERSEDED (2026-07-14). DO NOT FOLLOW AS CURRENT INSTRUCTIONS.**
> Pre-Bifrost memory routing snapshot (`global-memory-gateway`, SwarmRecall/SwarmVault substrate).
> Current route: `agentcore-gateway` → `agentcore-memory`. Current memory authority:
> `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`.

# AgentCore Restart Handoff - Final Leg

Generated: 2026-06-26T22:29:49-04:00

This handoff is for the next Codex session after restart. AgentCore remains the authority repo.

## Project Goal

Finish the AgentCore unified local memory/database runtime so every supported IDE and agent uses the same governed system automatically:

- native PostgreSQL/pgvector on the new 4 TB NVMe drive
- `global-memory-gateway` as the only normal memory write path
- SwarmRecall as the local-only lossless memory/runtime backend
- SwarmVault as the local RAG/wiki/knowledge substrate
- governed projection from canonical PostgreSQL into SwarmRecall and curated SwarmVault material
- consistent MCP/rules rollout across Codex, Cursor, Open Interpreter, OpenClaw, MiniMax, and Mavis

## Authority And Workhorse Paths

- AgentCore authority: `D:\github\agentcore-control-plane`
- Live legacy ops root: `D:\MCP-Control-Plane`
- Machine evidence workhorse: `D:\ChaosCentral-Current-Build`
- SwarmRecall root: `F:\AgentCore\agentmemory\swarmrecall`
- SwarmVault root: `F:\AgentCore\agentmemory\swarmvault`
- Projection state: `F:\AgentCore\agentmemory\projection-state`
- Archive root observed: `E:\AgentCoreArchive`

Do not make ChaosCentral a second authority. Use it for evidence refresh and spec sync into AgentCore docs/contracts only.

## Current Validation Snapshot

Last checked before restart:

- AgentCore source validator: PASS
  - command: `powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1 -DryRun`
  - PostgreSQL listener: `127.0.0.1:55432`
  - `\AgentCore\PostgresRuntime`: Ready, last result `0`
  - no broad SwarmRecall MCP rollout
  - live Codex budget: `11/11`
- Context policy validator: PASS
  - command: `powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreContextWindowPolicy.ps1`
  - live client counts:
    - Codex `11/11`
    - Cursor `12/12`
    - OpenClaw `13/13`
    - Open Interpreter `3/3`
    - MiniMax Code `7/7`
    - Mavis `7/7`
- ChaosCentral inventory validator: PASS
  - command: `powershell -NoProfile -ExecutionPolicy Bypass -File D:\ChaosCentral-Current-Build\scripts\Test-ChaosCentralInventory.ps1`
- Retired website-hosting route: no source references found in AgentCore or ChaosCentral.

## Recent Additions

ChaosCentral workhorse files:

- `D:\ChaosCentral-Current-Build\AGENTS.md`
- `D:\ChaosCentral-Current-Build\CURRENT_STATE.md`
- `D:\ChaosCentral-Current-Build\REFRESH_RUNBOOK.md`
- `D:\ChaosCentral-Current-Build\AUTOMATION_BACKLOG.md`
- `D:\ChaosCentral-Current-Build\SECURITY_REMEDIATION_TRACKER.md`
- `D:\ChaosCentral-Current-Build\MACHINE_STATE.manifest.json`
- `D:\ChaosCentral-Current-Build\scripts\Refresh-ChaosCentralInventory.ps1`
- `D:\ChaosCentral-Current-Build\scripts\Test-ChaosCentralInventory.ps1`

AgentCore authority additions:

- `docs\CHAOSCENTRAL_WORKHORSE_INTEGRATION.md`
- `docs\CONTEXT_WINDOW_OPTIMIZATION_POLICY.md`
- `docs\PLUGIN_EXTENSION_SECURITY_MONITORING.md`
- `contracts\chaoscentral-workhorse-contract.json`
- `ops\Test-AgentCoreContextWindowPolicy.ps1`
- `ops\Test-AgentCorePluginExtensionSecurity.ps1`

Codex automations added or updated:

- updated `agentcore-context-window-optimizer`
- created `agentcore-plugin-and-extension-security-monitor`
- created `agentcore-chaoscentral-spec-sync`

## Important OpenClaw Note

OpenClaw send failure was investigated immediately before this handoff.

Finding:

- `C:\Users\ynotf\.openclaw\openclaw.json` and `openclaw.json.last-good` are byte-identical.
- Both were written around `2026-06-26 20:12`, before the ChaosCentral/AgentCore handoff work.
- `eye2byte` remains present and user-approved in OpenClaw only.
- Gateway/node auth was not the failure. The log showed:
  - `chat.send failed: Agent "main" no longer exists in configuration`
- `C:\Users\ynotf\.openclaw\agents\main` exists on disk, but `main` is not listed in `openclaw.json` `agents.list`.
- Current approved OpenClaw MCP set is 13 servers.

Do not repair OpenClaw silently. If repairing, first back up `openclaw.json`, then either restore `main` to `agents.list` or repoint the active/default send target to `manager`, and validate with OpenClaw launch/send proof.

## Final-Leg Execution Order

After restart, execute in this order:

1. Cold-boot runtime proof
   - verify PostgreSQL auto-start on `127.0.0.1:55432`
   - verify SwarmRecall API on `127.0.0.1:3300`
   - verify Meilisearch on `127.0.0.1:7700`
   - verify SwarmVault runtime root and ingest/query validator

2. Run deterministic runtime gates
   - `ops\Test-AgentCoreRuntimeSuite.ps1`
   - `ops\Test-AgentCoreSwarmRecall.ps1`
   - `ops\Test-AgentCoreSwarmVault.ps1`
   - `ops\Test-AgentCoreMemoryProjection.ps1`
   - `ops\Test-AgentCoreContextWindowPolicy.ps1`
   - `ops\Test-AgentCorePluginExtensionSecurity.ps1`

3. Prove memory chain end to end
   - governed write through `global-memory-gateway`
   - row lands in canonical PostgreSQL `agent_core`
   - projector moves approved memory into SwarmRecall
   - curated knowledge lands in SwarmVault
   - no normal IDE flow uses direct SQL

4. Prove all IDE adoption
   - Codex
   - Cursor
   - Open Interpreter
   - OpenClaw
   - MiniMax
   - Mavis
   - run `ops\Test-AgentCoreLiveClientAdoption.ps1`
   - final gate: `ops\Test-AgentCoreRuntimeSuite.ps1 -IncludeLiveClientAdoption`

5. Polish and harden
   - approve or refine plugin/extension security baseline
   - resolve MiniMax/Mavis `mavis-trash.js` high-review warning or baseline it explicitly
   - formalize any remaining service/startup gaps
   - update docs and handoff
   - commit only after all validation is green and the user approves or repo policy allows

## Known Review Items

- Plugin/security scanner currently returns WARN, not FAIL:
  - high review: `C:\Users\ynotf\.mavis\bin\mavis-trash.js`
  - high review: `C:\Users\ynotf\.minimax\bin\mavis-trash.js`
  - reason: PowerShell encoded command usage for Windows file/trash helper behavior
  - no critical findings after tuning
- `D:\github\agentcore-control-plane` has substantial pre-existing uncommitted rollout work. Do not assume all dirty files are from Codex.
- `D:\ChaosCentral-Current-Build` is not a Git repo.
- OpenClaw config mutation should be deliberate because `main` is missing from config while its agent folder still exists.

## Do Not Drift

- Keep `global-memory-gateway` as the normal write path.
- Keep direct broad SwarmRecall MCP exposure out of default clients.
- Keep raw Mem0 out of normal routing.
- Keep context7 retired in favor of `arabold-docs`.
- Keep Composio quarantined until explicitly re-enabled through a stable MCP/OAuth path.
- Keep `eye2byte` as an OpenClaw-only user-approved exception.
- Do not restore retired website-hosting routes.
- Do not print or store secrets in reports, docs, logs, memory, or manifests.

## Restart Resume Commands

Start with:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1 -DryRun
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreContextWindowPolicy.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\ChaosCentral-Current-Build\scripts\Refresh-ChaosCentralInventory.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\ChaosCentral-Current-Build\scripts\Test-ChaosCentralInventory.ps1
```

Then continue with final-leg execution order above.

## 2026-06-26 Late Runtime And MCP Rollout Addendum

Current runtime proof:

- PostgreSQL is listening on `127.0.0.1:55432` with process `postgres.exe` rooted at `F:\AgentCore\postgres_runtime_engine\pgsql`.
- SwarmRecall API is listening on `127.0.0.1:3300` with Node API from `D:\github\vendor\swarm\swarmrecall\packages\api\dist\index.js`.
- Meilisearch is listening on `127.0.0.1:7700` with data path `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data` and `--no-analytics`.
- `ops\Test-AgentCoreRuntimeSuite.ps1` passes.
- `ops\Test-AgentCoreSwarmRecall.ps1` passes: 25 checks, 0 failures.
- `ops\Test-AgentCoreSwarmVault.ps1` passes: 15 checks, 0 failures.
- `ops\Test-AgentCoreMemoryProjection.ps1` passes: 14 checks, 0 failures.
- `validators\validate-control-plane.ps1 -DryRun` reports `Overall: PASS`.

Live MCP rollout completed:

- Cursor live config now has 8 approved default servers.
- OpenClaw live config now has 9 approved default servers, preserving the user-approved `eye2byte` exception and preserving non-MCP OpenClaw config sections.
- MiniMax live config now has 7 approved default servers.
- Mavis live config now has 7 approved default servers.
- Codex and Open Interpreter were already aligned.
- `ops\Test-AgentCoreContextWindowPolicy.ps1` now reports `status: pass`, 0 failed, 0 warnings across Codex, Cursor, OpenClaw, Open Interpreter, MiniMax, and Mavis.

Rollback and artifacts:

- Runtime-hardening script/task backup: `E:\AgentCoreArchive\backups_cold\agentcore-control-plane\runtime-hardening-20260626-234952`.
- Live MCP raw config backup: `D:\Autonomy\secrets-backups\agentcore-live-mcp-rollout-20260626-235706\raw`.
- Live MCP rollout manifest: `D:\github\agentcore-control-plane\artifacts\live-rollout\20260626-235706\live-mcp-rollout-manifest.json`.

Still pending:

- Restart affected IDEs after the live MCP config timestamps, then rerun `ops\Test-AgentCoreLiveClientAdoption.ps1`.
- Codex itself also needs restart before its own adoption proof can pass because the current Codex process predates the config timestamp.
- Scheduled task re-registration is still blocked from this Codex session because the process token is not elevated (`IsAdmin=false`). The startup scripts were hardened, but `\AgentCore\PostgresRuntime`, `\AgentCore\SwarmRecallApi`, and `\AgentCore\SwarmRecallMeilisearch` still show the old task metadata and `LastTaskResult=3221225786` until an elevated PowerShell re-registers them.
- `docs\rollout-runbook.md` is read-only, which blocks full `scripts\mcp_control_plane.py --apply` regeneration until the managed-doc unlock path is used.

Elevated follow-up command:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Install-AgentCoreOperationalScheduledTasks.ps1 -UseHighestRunLevel
```

After running it elevated, start or restart the AgentCore scheduled tasks and verify:

```powershell
Get-ScheduledTask -TaskPath \AgentCore\ | ? TaskName -in PostgresRuntime,SwarmRecallMeilisearch,SwarmRecallApi | Get-ScheduledTaskInfo
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1
```
