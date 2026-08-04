# AgentCore and LangGraph Authority Reconciliation — 2026-08-04

**Approval:** `AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION`
**Scope:** AgentCore authority/current-state documentation, LangGraph operator documentation, and the repository-owned Python runtime
**Architecture change:** None
**Pre-change AgentCore commit:** `4b4c507`
**Rollback bundle:** `E:\AgentCore-Backups\agentcore-control-plane\authority-reconciliation-20260804-0820`

## Outcome

The documentation surface is reconciled around the existing architecture. AgentCore remains canonical for exact evidence and recovery; Bifrost remains the MCP aggregation and governance boundary; the portable Context Engine remains the rolling-context orchestrator above `agentcore-memory`; neutral SwarmRecall remains a rebuildable semantic projection; LangGraph remains the AgentCore production workflow runtime on PG18.

Historical acceptance evidence is no longer allowed to imply current release readiness. The current launch gates are now explicit and machine-verifiable.

## Inherited working-tree boundary

The repository was dirty before this reconciliation. The following inherited work was preserved and excluded from this task's staging boundary:

- M6, M7, and M8 generated acceptance summaries
- Bifrost registry and MCP output-schema changes
- generated IDE profile changes
- Langfuse dependency, bootstrap, runbook, and skill work
- Reasonix profile work, skill lock, restore evidence, start logs, and archive artifacts

No inherited file was reverted, absorbed into this reconciliation, or used as current authority without explicit classification.

The repository-wide reconciliation scanner also identified pre-existing tracked credential-backup files under a legacy LangSmith project tree. Their contents were not printed, edited, staged, or deleted. They require a separate explicitly approved security-remediation task; this reconciliation uses a task-owned-file secret scan for its release gate.

## Verified live state

### Repository runtime

- `scripts\.venv` was the documented operator runtime but lacked `pip` and production dependencies.
- `scripts\bootstrap-runtime.ps1` now repairs an existing venv that lacks `pip`, installs the declared runtime requirements, verifies package compatibility, and executes the workflow unit/boundary suite with the same venv.
- Verified runtime: Python 3.13.14, LangGraph 1.2.5, `langgraph-checkpoint-postgres` 3.1.0, psycopg 3.3.4, psycopg-pool 3.3.1, Deep Agents 0.6.12.
- `pip check` reported no broken requirements.
- The production topology command returned 15 nodes and fingerprint `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32`.
- Workflow unit and boundary tests passed: 88/88.

### Memory and workflow services

- `agentcore-memory` reported healthy at version 0.9.1.
- AgentCore PG18 was reachable at `127.0.0.1:55433`.
- Neutral SwarmRecall reported healthy behind the memory facade.
- Cognee reported available at version 1.3.0.
- LangGraph integration reported `m6_integrated`.
- RUN11 remains completed with 23 PostgreSQL checkpoints; it is point-in-time baseline evidence, not proof of a post-v0.2.1 release canary.

### Current release blockers

1. Context Engine source is v0.2.1 at `2faa91a9fff6dc82fb9e3862c5ceb811a5cb4bd3`, while installed package metadata remains v0.2.0. `agentcore-context validate --live` correctly fails `engine_version`.
2. Windows service `AgentCore-PostgreSQL18` is configured Automatic but stopped while a separately launched PG18 process owns the live cluster. The service account ACL is not yet proven compatible with the data directory. Lifecycle repair must wait for active workflow/canary writes to stop, then use a fresh backup and single-owner restart proof.
3. Neutral Recall project/global pool identity and concurrent isolation still require current end-to-end proof through `agentcore-memory`.
4. A fresh LangGraph canary is required after Context Engine v0.2.1 installation and live validation pass.

## Documentation corrections

- `DOC_AUTHORITY.md` now distinguishes current authority, point-in-time acceptance, superseded evidence, and inherited WIP.
- `CONTEXT_BLOCK.md` now reports the live version mismatch, PG18 ownership issue, repository runtime repair, and release gates.
- `MASTER_CONFIG_AND_PROMPT.md`, `AGENTS.md`, and `MILESTONES.md` now require the repository venv and current release evidence.
- The current reconstruction was reduced to a current-state synthesis rather than a second mutable authority.
- LangGraph production, Studio, quickstart, and recovery runbooks now use the repository-owned Python executable from `scripts`.
- Old OpenRouter, dual-ecosystem, autonomous-workflow, and system-handover documents are explicitly labeled historical, point-in-time, or superseded.
- The stale static ChatGPT project-source manifest/exporter is formally retired; current context comes from the live authority chain plus `agentcore-memory` recovery.
- `scripts\validate_current_documentation.py` prevents the known stale Context Engine claims, wrong Python launch path, unconditional readiness claim, and missing evidence classification from returning.

## Cross-reference result

The active documentation surface contains one coherent launch contract:

1. Bootstrap or repair `scripts\.venv`.
2. Install and live-validate the exact Context Engine release.
3. Prove memory pool/project isolation through the gateway facade.
4. Normalize PG18 to one governed process owner after active work is quiescent.
5. Run a fresh LangGraph canary and capture checkpoints, judge/score, memory, gateway, and rollback evidence.
6. Promote readiness only after an independent review of the exact release state.

## Validation record

| Gate | Result |
| --- | --- |
| Authority lock + foreign boundary | PASS |
| Bifrost registry/gateway schemas and policy contracts | PASS |
| Bifrost contract/renderer suite | PASS — 144 checks |
| Ecosystem separation | PASS — 4 files |
| IDE enrollment scope | PASS — 12 prompts / 13 live paths |
| Cursor prompt format | PASS |
| Generated IDE rules | PASS |
| Current-document validator | PASS — 11 current documents + 5 classified historical/retired documents |
| Current-document validator tests | PASS — 8/8 |
| Repository runtime bootstrap | PASS |
| Python dependency consistency | PASS — no broken requirements |
| LangGraph topology | PASS — 15 nodes; locked fingerprint matched |
| Workflow unit/boundary suite | PASS — 88/88 |
| RUN11 read-only status | PASS — completed; 23 checkpoints; zero blockers |
| Live `agentcore-memory` status | PASS — v0.9.1 healthy; PG18, Cognee, neutral Recall, and LangGraph reported available/integrated |
| Task-owned secret/junk/whitespace scan | PASS |
| Repository-wide reconciliation scan | PARTIAL — authority, Stage A, ports, classification, and Markdown links pass; pre-existing legacy credential-backup files require separate approved remediation |
| Context Engine v0.2.1 live validation | BLOCKED — installed metadata remains v0.2.0; `engine_version` mismatch |
| Independent review | Review 1: FAIL on bare pip and handoff-recency authority; repaired. Review 2: FAIL because the validator missed Markdown-table pip and repo-root launch forms; repaired with realistic regression tests. Final exact-commit re-review pending. |

The exact review result and final Git commit are appended after independent review completes.
