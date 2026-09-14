# Tool Routing

Use this matrix after the exact AgentCore project and task class are known. Tool availability does not authorize use; project identity, capability profile, and lease policy still apply.

| Task | Required or preferred route | Evidence | Never substitute |
| --- | --- | --- | --- |
| Startup, resume, recovery, handoff | `agentcore-memory` through `agentcore-gateway` | session identity, retrieved event IDs, expanded source, handoff | chat summary, raw SQL, raw Recall |
| Architecture, migration, concurrency, recovery, major refactor | `sequential-thinking` through gateway | bounded decision analysis | unsupported intuition-only decision |
| External dependency/API/protocol/version | `arabold-docs` through gateway, then current official primary docs | version and source citation | stale model memory |
| Symbol/reference-sensitive code work | host-native semantic tools; explicit project-owned Serena only when needed | symbols, references, implementations, diagnostics | shared implicit-project Serena or broad text search alone |
| Structural dependency change | local Depwire with exact cwd before and after | impact graph and post-change graph | shared implicit-project Depwire |
| Milestone bootstrap/entry/exit | repo-local Context Fabric capture, drift, health | checkpoint and normalized drift | Context Fabric as canonical memory |
| Architecture/code graph required by Milestone | local Tentra with explicit project root | bounded graph evidence | shared implicit-project Tentra |
| Browser/UI/E2E | Playwright | deterministic screenshots, traces, or assertions | unit tests alone |
| Cross-service hotspot/system map | Artiforge when admitted and available | bounded scan result | routine invocation for small edits |
| Procedural skill discovery | read-only Skills Hub | inspected source, provenance, license, hash | `install_skill` or blind trust |

## Progressive disclosure

- Start with the minimum profile for the task.
- Request a JIT lease only for the exact capability and time window needed.
- Do not expose every installed tool to every worker.
- Release or let expire task-scoped capabilities at the gate or task close.
- If a tool is dormant because it lacks trustworthy per-session identity, use its documented explicit-project local route or stop.

## Serena sequence

For unfamiliar structural edits, API changes, symbol moves, rename/delete operations, or reference-sensitive debugging:

1. Confirm an explicit project-owned Serena process exists for the exact root.
2. Read `D:\github\agentcore-control-plane\SERENA.md`.
3. Call `initial_instructions` once for that process/session.
4. Inspect symbol overview, target symbol, references, and implementations as needed.
5. Perform the surgical edit.
6. Run semantic diagnostics and Depwire post-change verification.

Do not require Serena for trivial prose edits or when the host's native semantic tools already provide sufficient evidence.
