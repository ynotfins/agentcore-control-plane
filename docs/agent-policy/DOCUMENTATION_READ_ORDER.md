# Documentation Read Order (Task-Scoped)

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-execution-policy.json`.

## Mandatory authority baseline

Every managed task reads exactly these authority files first, in order:

1. `PROJECT_ANCHOR.md`
2. `DOC_AUTHORITY.md`

Discovering applicable instruction files and performing the mandatory self-checks below happens before task work. Beyond the baseline, load only documents selected by matching task triggers.

## Mandatory self-checks

- `SC-01` — Discover and read every applicable `AGENTS.md` and `CLAUDE.md` before task work.
- `SC-02` — Verify the exact repository, worktree, branch, HEAD, approved base, and dirty state.
- `SC-03` — Determine task mode, project ownership and enrollment, and the AgentCore or Swarm boundary.
- `SC-04` — Classify every target's authority and protection class and confirm matching authorization before writes.
- `SC-05` — Run the Ask-mode Foundation Report when this is the first task in the repository.
- `SC-06` — Compare requested scope, authority, current state, and evidence and stop on unresolved drift or conflict.

## Task triggers

Matching triggers may be combined, but each trigger's document order remains fixed and current authority always wins.

| Trigger | When | Ordered documents after the baseline |
| --- | --- | --- |
| `architecture_governance` | Architecture, milestones, governance, or protected authority changes. | `BLUEPRINT.md` → `CONTEXT_BLOCK.md` → `docs/agent-policy/` |
| `bifrost_gateway` | Bifrost, MCP registry, gateway client, client enrollment, Code Mode, capability-profile, or Bifrost runtime work. | `contracts/bifrost-upstream-mcp-registry.json` → `contracts/agentcore-gateway-client.json` → `GATEWAY_AND_BIFROST_DEVELOPER_GUIDE.md` |
| `memory_database` | AgentCore memory or database implementation work. | `CONTEXT_BLOCK.md` → `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` |
| `new_project_bootstrap` | New managed project bootstrap or the first repository task. | `docs/agent-policy/` → `docs/current/MASTER_TODO.md` → project `AGENTS.md` and `CLAUDE.md` → `.agentcore` project governance files |
| `documentation_mutation` | Documentation is proposed or changed. | `docs/agent-policy/DOCUMENTATION_GOVERNANCE.md` → `AUTHORITY_LOCK.md` → `contracts/authority-lock.yaml` |
| `dependency_external_api` | External library, API, CLI, schema, or protocol facts are needed. | Project manifests and lockfiles → Arabold exact-version documentation index |
| `ui_scaffolding` | Flutter, Android Compose, Refine, Next.js, React/shadcn, or FastAPI structure is scaffolded. | `docs/knowledge-library/` → knowledge library query for `framework` and `asset_type` |
| `implementation` | Source implementation is required after applicable authority is loaded. | Project state and decisions → relevant manifests and lockfiles → relevant implementation files |
| `historical_evidence` | A specific current fact question cannot be answered from current authority. | Specifically cited historical or superseded evidence required for the current fact question |

## Safeguards

- `SG-01` — Load only the matching task-triggered documents beyond the mandatory authority baseline; never load the full corpus automatically.
- `SG-02` — Historical or superseded evidence is never automatic and never overrides current authority.
- `SG-03` — Documentation mutation requires documentation governance, matching approval, rollback evidence, guard acceptance, and the documentation maintainer.
- `SG-04` — Generated state and decision projections remain projection-worker-only.
- `SG-05` — Do not expand task scope or claim merge, deployment, or adoption without the required new approval and evidence.

## Preserved rules

- Historical and superseded documents are read only for a specifically cited fact question and never by recency alone.
- Add deferred commitments to `docs/current/MASTER_TODO.md` only under `DEFERRED_COMMITMENT_POLICY.md`; active project Milestones and checklists take precedence.
- Machine facts come from `D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`, never ad-hoc memory.
- A knowledge-library miss is `LIBRARY MISS`; do not invent framework structure from training memory.
- When authoring Cursor prompts that list authority or evidence files, use `@` plus each full absolute Windows path. If more Cursor work remains, end with a ready-to-paste `CURSOR CONTINUATION PROMPT` section.
