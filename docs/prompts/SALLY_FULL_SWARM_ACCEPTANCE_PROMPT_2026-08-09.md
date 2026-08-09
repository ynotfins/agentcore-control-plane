# Sally Full Swarm Acceptance Prompt — 2026-08-09

Paste this into Sally/SwarmClaw when the operator is ready to replace the current `ORCHESTRATOR_OK` health-only evidence with full SwarmRecall, SwarmVault, and autonomous-team acceptance evidence.

```text
GOAL MODE — SWARMCLAW FULL SWARM ACCEPTANCE AND AUTONOMOUS RUNTIME READINESS

Complexity: 7/10
Context size: 6/10

Sally, resume as the SwarmClaw Orchestrator and authority for the Swarm ecosystem on this PC.

Current evidence:
- The latest health prompt returned: "Canary passed cleanly. No tasks queued, no active schedules, all agents idle. System is healthy. ORCHESTRATOR_OK"
- Treat that as SwarmClaw orchestrator health only.
- It is not full SwarmRecall, SwarmVault, or autonomous-runtime acceptance.

Primary goal:
Certify the SwarmClaw ecosystem as production-ready for autonomous development work, with SwarmRecall and SwarmVault healthy, correctly located, backed up, and usable through Swarm's supported best-practice boundaries.

Authority boundaries:
- SwarmClaw/Sally owns Swarm runtime orchestration, agents, sessions, tasks, recovery, lifecycle, SwarmRecall operational use, and SwarmVault operational use.
- AgentCore owns Bifrost, agentcore-gateway, LangGraph, exact IDE evidence, project identity, recovery, and PG18 checkpoints.
- Do not edit AgentCore, Bifrost, LangGraph, Cursor, Codex, or IDE configs.
- Do not expose raw SwarmRecall, SwarmVault, PostgreSQL, Meilisearch, or secrets to ordinary IDEs.
- Use Windows environment variables for secrets only. Do not write secrets to files.

Required storage boundary:
- Current Swarm hot/runtime storage must stay under H:\SwarmData and H:\SwarmRuntime.
- Swarm backups/archive should use E:\SwarmBackups unless current Swarm authority requires another Swarm-approved backup path.
- Do not use LangGraph-owned or AgentCore-owned runtime paths for Swarm state.

Required acceptance evidence:
1. Current service table:
   - SwarmClaw UI/API health
   - SwarmRecall health
   - SwarmVault health
   - Meilisearch health
   - Swarm PostgreSQL/listener health
   Include endpoint, status, and timestamp.

2. SwarmRecall canary:
   - Write one harmless test fact/event through the supported Swarm path.
   - Read it back.
   - Search for it.
   - Prove exact match.
   - Do not expose raw credentials.

3. SwarmVault canary:
   - Confirm source count or corpus status.
   - Run a small search/context-pack test.
   - Report token/context-pack size if available.

4. Autonomous team canary:
   - Run a harmless bounded delegated Swarm team task using Sally -> Builder -> QA/Reviewer or the installed recommended equivalent.
   - Prove task creation, delegation, result, review, and completion.

5. Drift and boundary proof:
   - Prove no writes were made to AgentCore, Bifrost, LangGraph, or IDE configs.
   - Prove Swarm runtime paths stayed under the approved Swarm roots.
   - List exact files changed.
   - List files intentionally not touched.

6. Restore point:
   - Create or identify a Swarm-side restore/backup evidence point using the installed Swarm best-practice mechanism.
   - Report exact backup/restore-point path and files, without secrets.

Final report:
- Write the final acceptance report using this template:
  @D:\github\agentcore-control-plane\docs\templates\SALLY_FULL_SWARM_ACCEPTANCE_REPORT_TEMPLATE_2026-08-09.md
- Return the final report path.
- Return PASS / PARTIAL / FAIL.
- State whether a SwarmClaw restart is required.
- State whether a new Sally chat is required or this chat can continue safely.

Stop gates:
- Stop before destructive action.
- Stop before deleting, migrating, reinitializing, or compacting databases.
- Stop before changing AgentCore/Bifrost/LangGraph/IDE configs.
- Stop if H-drive Swarm data appears missing, stale, or inconsistent.
- Stop if any secret would need to be written outside Windows environment variables.
```

After Sally returns the final report path, validate the report from `@D:\github\agentcore-control-plane`:

```powershell
.\ops\bifrost\Test-SallyAcceptanceEvidence.ps1 -Path '<path from Sally final acceptance>'
```

Continue to runtime canaries only if the validator returns `SUMMARY status=READY`.
