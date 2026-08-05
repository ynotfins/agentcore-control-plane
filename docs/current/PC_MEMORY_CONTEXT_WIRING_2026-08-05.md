# PC memory/context wiring — current authority reconciliation

**Status:** current reconciliation aid  
**Approved alignment:** `AUTH-2026-08-05-MEMORY-CONTEXT-AUTHORITY-RECONCILIATION`  
**Scope:** CHAOSCENTRAL AgentCore + neutral SwarmRecall + SwarmClaw runtime boundaries

This file exists to prevent the recurring drift between “SwarmRecall is the PC native memory plane” and “AgentCore/LangGraph owns canonical workflow state.” Both are true, but they apply to different planes.

## Non-negotiable mental model

```text
All capable AgentCore/enrolled IDEs
  -> one MCP entry named agentcore-gateway
  -> Bifrost governance on 127.0.0.1:8080/mcp
  -> agentcore-memory ten-tool facade
  -> AgentCore PG18 for exact evidence/state
  -> bounded server-side projection to neutral SwarmRecall for semantic memory/context

SwarmClaw runtime
  -> Swarm-owned runtime/session/task state
  -> Swarm-owned adapter to the same neutral SwarmRecall semantic plane
  -> SwarmVault for Swarm-owned knowledge/RAG
  -> no AgentCore PG18, Bifrost, LangGraph checkpoint, or IDE profile ownership

LangGraph runtime
  -> AgentCore-owned autonomous workflow
  -> PG18 PostgresSaver checkpoints and workflow tables
  -> optional semantic memory through agentcore-memory -> neutral SwarmRecall
  -> no SwarmClaw SQLite/session ownership and no checkpoint storage in Recall
```

## Authorities by plane

| Plane | Authority | Current owner | Must not become |
| --- | --- | --- | --- |
| IDE MCP front door | `agentcore-gateway` | AgentCore/Bifrost | raw SwarmRecall/SwarmVault MCP in ordinary IDE configs |
| Exact recovery evidence | AgentCore PG18 `agent_core` | AgentCore | SwarmRecall-only, Meili-only, or SwarmVault-only truth |
| Rolling context lifecycle | Portable Context Engine | AgentCore host adapters | a second IDE gateway or raw database client |
| PC-native semantic memory/context | Neutral SwarmRecall | machine-level neutral service | AgentCore-owned exclusive DB or SwarmClaw-owned exclusive DB |
| LangGraph workflow/checkpoints | PG18 PostgresSaver | AgentCore/LangGraph | SwarmRecall, SwarmVault, or SwarmClaw SQLite |
| SwarmClaw runtime state | SwarmClaw local runtime | Swarm ecosystem | AgentCore memory/session authority |
| Swarm RAG/wiki/corpus | SwarmVault | Swarm ecosystem | AgentCore knowledge ingestion store |

## Drive and storage separation

| Root | Role |
| --- | --- |
| `D:\github\agentcore-control-plane` | AgentCore control-plane Git authority |
| `D:\github\agentcore-context-engine` | Portable Context Engine source/package authority |
| `D:\github\swarm-ecosystem-control` | Swarm control-plane Git authority |
| `F:\AgentCore\...` | AgentCore runtime and staging data |
| `H:\SwarmData\...` | Active native SwarmRecall/SwarmVault/SwarmClaw hot data |
| `E:\SwarmBackups` | Swarm backup root |
| `E:\AgentCore\...` | AgentCore cold/archive/backup roots where documented |
| `I:\LocalApps\...` | neutral local application storage; not AgentCore or Swarm runtime storage |

## Design decisions this resolves

1. **Do not reinstall SwarmClaw/SwarmRecall/SwarmVault by default.** The current native Swarm build is already authority-aligned around `H:\SwarmData`; a fresh wizard install may regress to vendor defaults, Docker assumptions, `.env.local`, broad listeners, or duplicate services unless run under a specific governed reinstall plan.
2. **Do not make LangGraph a SwarmClaw runtime.** LangGraph is already productized under AgentCore with PG18 checkpoints and Studio runbooks. Folding it into SwarmClaw would combine two runtime authorities and lose the completed workflow boundary.
3. **Do not make SwarmRecall the LangGraph checkpoint database.** SwarmRecall is the PC-wide semantic memory/context plane. LangGraph checkpoints, interrupts, retries, pending writes, and exact evidence stay in AgentCore PG18.
4. **Do use neutral SwarmRecall for shared semantic context.** AgentCore and SwarmClaw can both read/write curated semantic memories through their own bounded adapters, with project/session/pool identity, idempotency, provenance, and isolation.
5. **Do keep all ordinary IDEs on one MCP entry.** AgentCore/enrolled IDEs use `agentcore-gateway`; Swarm-owned work uses the Swarm control plane and Swarm-owned tooling, not AgentCore IDE continuity.

## Current hard gates before declaring complete

- Prove neutral SwarmRecall global/per-project pool provisioning and project-pool isolation live.
- Prove SwarmClaw autonomous canary with Swarm-owned adapter/skill and no AgentCore state writes.
- Prove LangGraph can still complete a production canary while Recall is available and while Recall is degraded, without checkpoint count/state corruption.
- Reconcile the PG18 Windows service/launcher ownership into one governed owner.
- Keep Context Engine and IDE lifecycle validation current per host; configuration presence alone is not live validation.

## Reinstall rule

A Swarm wizard reinstall is allowed only if a current audit proves the native `H:\SwarmData` system is unrecoverable or materially miswired. The reinstall plan must preserve backups, loopback-only binds, Windows environment variable secret handling, neutral Recall identity, AgentCore separation, and the single IDE `agentcore-gateway` contract.
