# Documentation Governance and Drift Guard

**Approval:** `AUTH-2026-08-06-DOCUMENTATION-GUARD`

**Applies to:** every AgentCore-managed project, IDE, runtime, and delegated worker. Swarm-owned documentation remains under the Swarm control plane and is not modified by this policy.

## Purpose

Documentation records operator intent, accepted architecture, current Milestone state, and verified evidence. It must not become an ungoverned second implementation surface. A dedicated documentation guard and maintainer workflow owns documentation mutation so ordinary implementation agents cannot silently rewrite the facts that orient later agents.

The documentation worker is a maintainer, not an authority. Authority remains with the operator, the repository authority chain, accepted contracts, current code/test evidence, and the applicable writer capability. Model identity never grants permission.

## Roles

- **Ordinary agents and implementation workers:** may read documentation, cite it, detect a likely mismatch, and submit a bounded change proposal. They do not directly edit documentation.
- **Documentation guard:** read-only and independent from the proposed edit. It compares the proposal with the operator goal, authority chain, current Milestone, implementation, tests, and live evidence. It returns `BLOCK`, `REVISE`, or `ACCEPT` and never writes files.
- **Documentation maintainer:** the sole ordinary-agent path for editing an existing documentation file. It receives one file, a bounded instruction, and relevant authority/evidence; after producing the proposed diff, it calls the guard internally and writes only when that actual diff receives `ACCEPT`. A caller-supplied verdict is never trusted. It cannot create architecture authority by assertion.
- **Authority maintainer:** supplies the required capability and approval reference for governed or operator-locked documents. The documentation worker does not replace this authorization.
- **Projection worker:** remains the only writer for generated `STATE.md`, `DECISIONS.md`, `CONTEXT_INDEX.md`, and global-state projections.

## Required workflow

1. Classify the target through `DOC_AUTHORITY.md`, `AUTHORITY_LOCK.md`, and the project’s local governance files.
2. Gather the smallest sufficient authority/evidence packet. Historical documents are evidence only unless currently classified as authority.
3. A preliminary read-only guard review may assess the proposed factual change. `BLOCK` stops and `REVISE` requires correction. This preliminary review is advisory; it cannot authorize a write.
4. For governed or locked targets, obtain an `AUTH-YYYY-MM-DD-*` approval, create an external rollback copy, record before hashes, and unlock only the named files.
5. Use the documentation maintainer for one existing documentation file at a time. Preview first when the change is non-trivial. On write, the maintainer submits the actual generated diff to the guard internally and proceeds only on the directly returned `ACCEPT`; callers cannot supply or forge the verdict.
6. Run syntax, schema, renderer-parity, cross-reference, authority-lock, and project validators appropriate to the changed file.
7. Obtain an independent review for protected changes, record after hashes and evidence, restore read-only attributes, then commit and push the bounded documentation checkpoint.

## Milestone lock

Accepted Milestone outcomes, operator goals, architecture decisions, and authority classifications are stable. A later agent may not “clean up,” reinterpret, broaden, or silently modernize them. Change requires a cited reason, impact analysis, explicit approval when governed, updated acceptance evidence, and a new recorded decision. Routine wording fixes must preserve semantics.

Documentation must be updated in the same Milestone as the verified behavior it describes. When implementation finishes but documentation evidence is incomplete, the Milestone remains open or records an explicit deferred commitment; agents must not fabricate a completed state.

## Structural enforcement in the Codex worker stack

The repository-owned package at `tools/cheap-workers` provides:

- `documentation_guard_worker` — read-only DeepSeek V4 Pro review;
- `documentation_maintainer_edit_worker` — bounded one-file documentation editing, dry-run by default;
- secret and credential preflight before external model calls (active Windows secret values of at least 8 characters plus high-confidence credential formats; shorter values are not acceptable secret material);
- default 2 MiB target limit, workspace containment, binary rejection, same-file serialization, double hash checks, rollback backup, crash-safe same-directory replacement, and post-write verification;
- rejection of documentation targets by ordinary code-edit workers;
- rejection of source targets and generated projections by the documentation maintainer;
- internally obtained guard acceptance for the actual proposed diff, plus live authority-capability and matching approval-environment enforcement for protected anchor filenames.

This worker-level enforcement supplements Git, authority-lock validators, IDE rules, and human review. It does not make an external model a security principal and cannot prevent a separate unmanaged process from writing files. Managed agents therefore treat direct documentation mutation as denied even if their host technically exposes a generic file-edit tool.

## Cross-IDE rule

Every rendered AgentCore IDE policy carries this governance rule. IDEs that do not host the Codex documentation workers must leave documentation unchanged and hand the proposed patch, evidence, and target path to the AgentCore authority maintainer. Do not register the Codex worker MCP as a second IDE MCP entry and do not expose it through Bifrost merely to bypass this handoff.
