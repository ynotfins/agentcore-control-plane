# Memory / Context Documentation Alignment Audit — 2026-08-10

**Approval:** `AUTH-2026-08-10-SWARMRECALL-NATIVE-CONTEXT-DOC-ALIGNMENT`
**Scope:** AgentCore current authority docs, generated IDE rule docs, current control-plane docs, contracts, and known historical/rollback surfaces.

## Target ownership model

- SwarmRecall is the PC-native semantic memory/context plane.
- `agentcore-memory` is the AgentCore-governed access facade and lifecycle surface behind `agentcore-gateway`.
- AgentCore PG18 remains canonical for exact evidence, recovery, policy, leases, generated projections, and LangGraph checkpoints.
- LangGraph may consume semantic memory through the AgentCore facade, but its production checkpoints remain PG18 PostgresSaver.
- SwarmClaw/Sally owns Swarm runtime operation and reaches neutral SwarmRecall through Swarm-owned bounded adapters.
- Ordinary IDEs use one MCP entry, `agentcore-gateway`, and do not receive raw SwarmRecall, SwarmVault, PostgreSQL, or Meilisearch credentials.

## Files corrected in this pass

- `PROJECT_ANCHOR.md`
- `BLUEPRINT.md`
- `CONTEXT_BLOCK.md`
- `DOC_AUTHORITY.md`
- `MASTER_CONFIG_AND_PROMPT.md`
- `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`
- `docs/current/MASTER_TODO.md`
- `docs/current/MEMORY_CONTEXT_DOC_ALIGNMENT_CHECKLIST_2026-08-10.md`
- `docs/current/CURRENT_CONTEXT_HANDOFF_2026-08-10.md`
- `contracts/global-agent-policy.yaml`
- generated IDE rule files under `ide-profiles/*/`
- `CLAUDE.md`
- `rules/canonical/GLOBAL_AGENT_RULES.md`
- historical/superseded warning updates: `VALIDATION_REPORT.md`, `docs/CONTEXT_WINDOW_OPTIMIZATION_POLICY.md`, `docs/CHAOSCENTRAL_WORKHORSE_INTEGRATION.md`, `docs/SERENA_CONFIGURATION.md`, `docs/memory_system.md`, `reports/UNIVERSAL_GATEWAY_VERIFICATION.md`, `reports/MEMORY_STACK_AUDIT.md`, `contracts/master-mcp-server-config.json`, `contracts/chaoscentral-workhorse-contract.json`

## Cross-reference result

Current anchored docs now agree on the key distinction:

```text
ordinary IDE / AgentCore-enrolled agent
  -> agentcore-gateway
  -> agentcore-memory access facade
     -> neutral SwarmRecall: PC-native semantic memory/context
     -> AgentCore PG18: exact evidence, recovery, policy, LangGraph checkpoints
```

No current authority file is allowed to interpret this as direct IDE access to raw SwarmRecall, SwarmVault, PostgreSQL, or Meilisearch.

## Stale string disposition

Searches still find stale strings such as `global-memory-gateway`, `127.0.0.1:55432`, `F:\AgentCore\agentmemory`, and direct SwarmRecall/SwarmVault examples in historical reports, rollback artifacts, backups, inventory snapshots, and migration evidence. Those are intentionally retained as evidence and are controlled by the warning added to `DOC_AUTHORITY.md`.

The risky current/superseded ambiguity found during this pass was corrected in:

- `contracts/master-mcp-server-config.json` — now carries a machine-readable `historical_superseded_pre_bifrost` marker and current-memory authority note.
- `docs/CONTEXT_WINDOW_OPTIMIZATION_POLICY.md` — historical body now names the current path.
- `docs/CHAOSCENTRAL_WORKHORSE_INTEGRATION.md` — current MCP source-of-truth no longer points at the superseded master MCP contract.
- `docs/SERENA_CONFIGURATION.md` — body no longer claims current source-of-truth status.
- `VALIDATION_REPORT.md`, `reports/UNIVERSAL_GATEWAY_VERIFICATION.md`, and `reports/MEMORY_STACK_AUDIT.md` — strengthened historical warnings.

## Remaining proof gate before first real project

This pass aligns documentation. It does not by itself prove every IDE's live automatic rolling-context hooks. Before the Android notification app comparison run, execute:

1. Codex/Cursor AgentCore memory lifecycle check through `agentcore-gateway` / `agentcore-memory`.
2. Sally read-only Swarm-side audit of SwarmRecall/SwarmVault/SwarmClaw memory/context readiness.
3. If both pass, create a new restore point that explicitly says rolling context is live-proven for the selected hosts.
