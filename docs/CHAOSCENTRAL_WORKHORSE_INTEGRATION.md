# ChaosCentral Workhorse Integration

Generated: 2026-06-26

ChaosCentral is an evidence collection and planning workhorse. AgentCore remains the authority for database, memory, MCP, runtime, and automation governance.

## Ownership

| Layer | Path | Role |
| --- | --- | --- |
| AgentCore authority | `D:\github\agentcore-control-plane` | Source-controlled contracts, renderers, validators, runtime scripts, and authoritative docs. |
| Live legacy ops | `D:\MCP-Control-Plane` | Existing live scripts and compatibility entrypoints. |
| ChaosCentral workhorse | `D:\ChaosCentral-Current-Build` | Machine inventory, current-state snapshots, evidence, planning docs, and security-surface observations. |

ChaosCentral may discover facts. AgentCore decides policy.

## Data Flow

1. ChaosCentral refresh writes `D:\ChaosCentral-Current-Build\MACHINE_STATE.manifest.json`.
2. Timestamped evidence is written under `D:\ChaosCentral-Current-Build\_evidence`.
3. If a finding affects AgentCore runtime or client behavior, update AgentCore docs/contracts/scripts.
4. AgentCore validators prove whether the authority layer still matches the live machine.

## Source-Of-Truth Rules

- MCP server requirements live in `contracts\master-mcp-server-config.json`.
- ChaosCentral integration rules live in `contracts\chaoscentral-workhorse-contract.json`.
- Runtime and automation ownership live in `docs\AGENTCORE_AUTOMATION_OPERATIONS.md`.
- Database and memory contracts live in `contracts\global-memory-database-contract.json` and memory docs.
- Do not use ChaosCentral docs as direct renderer inputs unless an AgentCore contract explicitly consumes them.

## Useful ChaosCentral Outputs

- hardware inventory and storage maps
- port and listener snapshots
- scheduled-task snapshots
- Codex automation inventories
- MCP and IDE current-state notes
- plugin and extension security-surface evidence
- unresolved setup or drift findings

## Validation

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File D:\ChaosCentral-Current-Build\scripts\Refresh-ChaosCentralInventory.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\ChaosCentral-Current-Build\scripts\Test-ChaosCentralInventory.ps1
powershell -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1 -DryRun
```

## Drift Policy

If ChaosCentral and AgentCore disagree:

1. Treat live evidence as current reality.
2. Treat AgentCore contracts as desired governed state.
3. Update AgentCore source docs/contracts/tests when desired state changes.
4. Update ChaosCentral current-state notes after validation.
