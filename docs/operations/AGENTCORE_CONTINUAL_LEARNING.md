# AgentCore Continual Learning Boundary

**Status:** Binding operating policy (2026-07-20)  
**Related:** `audits/CONTINUAL_LEARNING_AUTOMATION_2026-07-20.md` · `BLUEPRINT.md` · `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`

## Decision

Cursor’s marketplace **continual-learning** plugin (stop-hook `followup_message` → user-role prompt → `agents-memory-updater` → `AGENTS.md`) is a **parallel memory path**. It is **not** AgentCore memory.

Automatic trigger is **disabled** on this workstation until an AgentCore-aligned capture job exists.

## Approved target flow

```text
Cursor lifecycle event (bounded)
  -> local capture job (single-run lock, idempotent)
  -> agentcore-gateway -> agentcore-memory.append_event
  -> propose_fact for durable high-signal candidates
  -> AgentCore trust / provenance review
  -> governed promotion
  -> generated projections only (never hand-edit STATE.md / GLOBAL_STATE.md / DECISIONS.md / CONTEXT_INDEX.md)
```

## Hard rules

1. Never silently impersonate the operator with an injected user-role prompt.
2. Never auto-edit `AGENTS.md` with inferred personal facts or transcript summaries.
3. Never write `GLOBAL_STATE.md`, `STATE.md`, `DECISIONS.md`, or `CONTEXT_INDEX.md` directly.
4. Never store secrets; quarantine secret-bearing transcripts.
5. Never process Swarm transcripts into AgentCore memory.
6. Never run recursively; never reprocess the same generation/transcript mtime without advance.
7. Use a single-run lock and deterministic idempotency keys.
8. Limit processing to newly changed transcripts.
9. Record a sanitized audit event per run.
10. Use a registered AgentCore client/agent identity and respect project boundaries.
11. Quarantine uncertain facts; require operator approval before promoting to operating rules.
12. No model call when no changed transcript exists; no update when no high-signal fact exists.

## What may change `AGENTS.md`

Only:

- Explicit operating-contract changes
- Source-controlled tool/rule changes
- Operator-approved durable project governance

User preferences and recurring corrections belong in **AgentCore facts**, not `AGENTS.md` “Learned” bullets.

## Current machine controls

| Control | Location |
| --- | --- |
| Auto-trigger disabled | Plugin `hooks/continual-learning-stop.ts` no-op (originals preserved under `E:\AgentCore-Backups\…` and `audits/_preserved/…`) |
| Marker | `.cursor/hooks/CONTINUAL_LEARNING_AUTO_TRIGGER_DISABLED.md` |
| Index helper (manual) | `.cursor/hooks/update-continual-learning-index.ps1` |

## Re-enable criteria

Do not re-enable marketplace auto-followup until:

1. Capture job writes only via `agentcore-memory`
2. No user-role prompt injection
3. No AGENTS.md auto-edits
4. Lock + idempotency + sanitized audit exist
5. Operator sign-off recorded in an audit under `audits/`
