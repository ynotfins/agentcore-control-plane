# Tool Lifecycle Policy — Progressive Tool Disclosure with Milestone-Gated Capability Leases

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-tool-lifecycle.json`.

## Core principle

Distinguish **full tool availability** from **active exposure to the model**:

- Every approved tool remains available for immediate activation (catalogued in `contracts/bifrost-upstream-mcp-registry.json`).
- Dormant / deferred / future capabilities are indexed in `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md` with **zero default exposure**.
- Only tools needed for the current project and current Milestone are actively exposed to the model.
- The full builder catalog (~127 tools) must not remain permanently loaded into every model turn.
- A project begins with the safe **Bootstrap** profile (`NEW_PROJECT_BOOTSTRAP.md`), never unrestricted administrative or destructive authority.

## Implementation status (important)

**This policy currently governs desired state and audits only.** Runtime lease activation/expiry, per-project capability isolation, usage ledgers, and concurrency enforcement are implemented by the memory platform (PostgreSQL-backed) at Milestone **M6** of `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` — after the identity and policy schema exists. Until M6 passes:

- `TOOL_MANIFEST.yaml` records policy and desired state; agents honor it behaviorally.
- The Bifrost registry's `permitted_tools: ["*"]` wildcard grants are a **documented transitional state**.
- No temporary YAML/JSON lease database or runtime Tool Lifecycle Manager is created — that would be a competing authority requiring later migration.

## Tool states

| State | Meaning |
| -- | -- |
| `catalogued` | Approved and available for immediate activation, but not currently exposed |
| `core_active` | Used frequently throughout the project |
| `milestone_active` | Needed throughout the current Milestone |
| `jit_leased` | Temporarily exposed for a Macro or Micro step (runtime enforcement from memory-platform M6) |
| `dormant` | Not currently needed but may be reactivated |
| `operator_only` | Requires explicit operator approval per activation |
| `forbidden` | Never permitted for this project |

## JIT capability leases

A tool not active for the current Milestone may be activated through a JIT lease. Every lease records: project, Milestone, Macro/Micro step, requested tool or tool group, justification, risk class, permitted operations, expiry, requesting agent, approval class, and audit ID.

A lease expires on the earliest of: Micro step completion, Macro step completion, defined timeout, session close, project change, Milestone close, or explicit revocation. High-risk tools default to task-scoped leases. **No tool remains active merely because it may be useful later.**

## Tool audits

Audits run at every Milestone entry and exit (and at M0 completion). Decision rules:

**Keep active when:** used repeatedly; required by the next Milestone; foundational for continuous context, memory, validation, or safe editing; its context cost is justified.

**Make dormant when:** not used in the current Milestone; not required by the next Milestone; useful only in a future uncertain stage.

**Expire when:** its Micro/Macro step is complete; it was activated as a JIT lease; its upstream is unhealthy and nonessential.

**Make operator_only when it can:** modify gateway configuration; access secrets; execute destructive database operations; modify live IDE configuration; write outside the assigned worktree; upload private code or data; perform broad browser or arbitrary-code execution.

**Forbid when it:** crosses Swarm boundaries; bypasses AgentCore memory/database policy; exposes whole drives; creates a duplicate canonical system; violates the project's security classification.

Every audit updates `TOOL_MANIFEST.yaml` (`last_audit`, `next_required_audit`) and disables Bootstrap-only and completed-Milestone tools not needed next.

## Future capability profiles (defined now, enforced from memory-platform M6)

| Profile | Intent |
| -- | -- |
| `bootstrap` | Broad safe discovery and project setup (see `NEW_PROJECT_BOOTSTRAP.md`) |
| `builder-core` | Minimal continuous build set: agentcore-memory, agentcore-project-router, arabold-docs, context-fabric core, Serena navigation, Depwire read/impact/verify, sequential-thinking where necessary, bounded project filesystem — **not** every mutation tool |
| `milestone-builder` | builder-core plus the current Milestone's tools |
| `reviewer` | Read-focused validation tools |
| `database-validator` | Migration and disposable-database validation only |
| `docs-knowledge` | Documentation and project knowledge tools |
| `operator` | Administrative capability, explicit use only |
| `emergency-recovery` | Minimal recovery/diagnostic operations, explicit operator activation |

Profiles must define named tools, not broad wildcards, except where a server's entire small read-only surface is reviewed and explicitly justified in the registry. Wildcard grants without a documented transitional exception fail validation.

## Bifrost treatment

The current Bifrost registry/VK wildcard exposure is transitional. The memory platform (M6) implements concurrency-safe per-project runtime exposure on PostgreSQL identity/policy state, preserving: one `agentcore-gateway` entry per IDE, no IDE config changes for tool activation, no shared-VK mutation that breaks another active project, no secret exposure, and rollback via the rendered `config.json` + scheduled-task restart.
