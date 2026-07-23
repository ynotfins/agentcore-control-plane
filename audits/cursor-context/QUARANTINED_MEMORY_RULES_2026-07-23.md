# Quarantined Contradictory Memory Rules — 2026-07-23

## Action

Three proven contradictory always-on memory rules were quarantined during the Cursor Context Integrity Repair (Phase 6).

## Quarantine method

Each rule was first copied to a timestamped rollback backup under `E:\AgentCore-Backups\cursor-rules-quarantine-2026-07-23-0137`, then renamed in place by appending `.mdc.quarantined`. This makes the quarantine reversible while immediately removing the rules from Cursor's active rule load.

## Quarantined rules

| Rule | Original path | Backup path | Why it was quarantined |
| ---- | ------------- | ----------- | ---------------------- |
| `openmemory.mdc` | `D:\.cursor\rules\openmemory.mdc` | `E:\AgentCore-Backups\cursor-rules-quarantine-2026-07-23-0137\openmemory.mdc` | Mandates OpenMemory/MCP memory-first phases and project/user-preference searches that conflict with the AgentCore `agentcore-memory` gateway contract and the canonical PostgreSQL memory path. |
| `00-memory-autopilot.mdc` | `D:\github\.cursor\rules\00-memory-autopilot.mdc` | `E:\AgentCore-Backups\cursor-rules-quarantine-2026-07-23-0137\00-memory-autopilot.mdc` | Requires `mem0` / `Memory Tool` at session start and autonomous memory writes, which conflicts with the AgentCore memory surface and the `agentcore-memory` ten-tool gateway contract. |
| `30-memory-usage.mdc` | `C:\Users\ynotf\.cursor\rules\30-memory-usage.mdc` | `E:\AgentCore-Backups\cursor-rules-quarantine-2026-07-23-0137\30-memory-usage.mdc` | Reinstates the retired `global-memory-gateway` as the primary memory path and references the pre-Bifrost `D:\MCP-Control-Plane` / PG `:55432` baseline, which contradicts current AgentCore authority (`PROJECT_ANCHOR.md`, `BLUEPRINT.md`, `AGENTS.md`). |

## Superseding authority

The quarantined rules are superseded by the current AgentCore authority chain:

1. `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`
2. `D:\github\agentcore-control-plane\DOC_AUTHORITY.md`
3. `D:\github\agentcore-control-plane\BLUEPRINT.md`
4. `D:\github\agentcore-control-plane\AGENTS.md`
5. `D:\github\agentcore-control-plane\CONTEXT_BLOCK.md`
6. `D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md`
7. `D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json`
8. `D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`

Key superseding facts:

- Normal non-Swarm IDE memory is `agentcore-memory` via the single `agentcore-gateway` entry (`http://127.0.0.1:8080/mcp`).
- `global-memory-gateway` is retired from the mandatory baseline.
- Direct PostgreSQL credentials, SQL, DDL, and raw Mem0/OpenMemory are not normal IDE routes.
- Persistent memory writes go through `agentcore-gateway` -> `agentcore-memory` only.

## Rollback

To restore the quarantined rules, rename each `.mdc.quarantined` file back to `.mdc` from the original paths. The backup directory above contains the pre-quarantine copies.

## Verification

After quarantine, a fresh Cursor session should load only the AgentCore-aligned rules under:

- `D:\github\agentcore-control-plane\.cursor\rules\`
- `C:\Users\ynotf\.cursor\rules\agentcore-memory.mdc` and other non-conflicting rules

No `openmemory.mdc`, `00-memory-autopilot.mdc`, or `30-memory-usage.mdc` should be active in Cursor's rule list.
