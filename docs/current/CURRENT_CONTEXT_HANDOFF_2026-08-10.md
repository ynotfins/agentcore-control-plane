# Current Context Handoff — 2026-08-10

**Repository:** `@D:\github\agentcore-control-plane`
**Purpose:** compact restart/new-chat anchor for the post-restore-point state before running the first real project through LangGraph and SwarmClaw.

## Stable facts

- Runtime restore point exists: `@D:\github\agentcore-control-plane\audits\RESTORE_POINT_RUNTIME_ACCEPTANCE_20260809-220421.md`.
- Current goal-completion checklist exists: `@D:\github\agentcore-control-plane\docs\current\GOAL_COMPLETION_CHECKLIST_2026-08-09.md`.
- Active doc-alignment checklist: `@D:\github\agentcore-control-plane\docs\current\MEMORY_CONTEXT_DOC_ALIGNMENT_CHECKLIST_2026-08-10.md`.
- SwarmRecall is the PC-native semantic memory/context plane.
- AgentCore PG18 is canonical for exact evidence, recovery, policy, leases, generated projections, and LangGraph checkpoints.
- `agentcore-memory` is the AgentCore-governed access facade behind `agentcore-gateway`; it is not the top semantic-memory authority.
- Ordinary IDEs use one MCP entry: `agentcore-gateway` at `http://127.0.0.1:8080/mcp`.
- Ordinary IDEs must not receive raw SwarmRecall, SwarmVault, PostgreSQL, Meilisearch, or direct SQL credentials.
- LangGraph production checkpoints remain PG18 PostgresSaver. LangGraph may consume semantic context through the AgentCore facade, but SwarmRecall is not its checkpoint database.
- SwarmClaw/Sally owns Swarm runtime operation and reaches neutral SwarmRecall through Swarm-owned bounded adapters.

## Latest accepted evidence

- Bifrost readiness: `Test-AgentCoreMorningReadiness.ps1` returned `SUMMARY status=READY pass=23 warn=0 fail=0` during the restore-point pass.
- Sally full Swarm acceptance: `@H:\SwarmData\claw\workspace\sally\SALLY_FULL_SWARM_ACCEPTANCE_2026-08-09.md`; AgentCore validator returned `SUMMARY status=READY pass=16 fail=0`.
- LangGraph canary: `@D:\github\agentcore-control-plane\audits\LANGGRAPH_TOPOLOGY_CANARY_2026-08-09_1951.md`.
- SwarmClaw autonomous canary: `@H:\SwarmData\claw\workspace\sally\SWARMCLAW_AUTONOMOUS_CANARY_2026-08-09.md`.
- Final evidence preflight: `Test-AgentCoreFinalAcceptanceEvidence.ps1` returned `SUMMARY status=READY pass=7 fail=0`.

## Active issues

1. Documentation wording/diagrams must not imply AgentCore owns the PC-native semantic memory plane.
2. Full Codex/Cursor automatic rolling-context behavior should be re-audited before the first real project run.
3. Neutral Recall global/per-project pool isolation remains a tracked proof item until fresh evidence is recorded.
4. The next real project should use one shared goal and acceptance criteria on isolated copies/worktrees so LangGraph and SwarmClaw can be compared fairly.

## Next run plan

1. Finish the 2026-08-10 doc-alignment checklist.
2. Run a fast memory/rolling-context audit for Codex and Cursor through `agentcore-gateway` / `agentcore-memory`.
3. Ask Sally for a read-only Swarm-side memory/context audit without touching AgentCore/LangGraph/IDE configs.
4. Create a second restore point after the rolling-context audit passes.
5. Run the same nearly-finished Android notification app through LangGraph and SwarmClaw using identical natural-language goals, identical acceptance criteria, and isolated workspaces.
