# AgentCore Cross-Project Master TODO

**Document type:** Mutable deferred-commitment ledger; not architecture authority

**Policy:** `docs/agent-policy/DEFERRED_COMMITMENT_POLICY.md`

**Last reviewed:** 2026-08-06

**Approval:** `AUTH-2026-08-06-DEFERRED-COMMITMENT-LEDGER`

Project Milestones, Micro checklists, acceptance contracts, and generated STATE take precedence. This file links to those artifacts instead of replacing or duplicating them.

## Active commitments

| ID | Priority | Status | Scope / owner | Commitment | Next action | Deferral reason | Authority / evidence | Recheck trigger | Last reviewed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| AC-TODO-001 | P0 | ready | Swarm ecosystem / Swarm operator (Sally) | Finish SwarmClaw, SwarmRecall, and SwarmVault production acceptance without entering LangGraph or AgentCore-owned runtime paths. | Resume Sally with a bounded final-acceptance goal; require current runtime, drive-boundary, adapter, skills, autonomous-canary, backup, restart, and Git evidence. | Sally halted for operator reconciliation; the local-only Recall-key finding is not a runtime blocker. | `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` sections 5, 6.8, and 8.4; Swarm authority remains `D:\github\swarm-ecosystem-control`. | Immediately after this worker/productivity audit. | 2026-08-06 |
| AC-TODO-002 | P0 | blocked | AgentCore LangGraph / Codex | Start the first governed production project through the certified LangGraph workflow. | Define the project goal and acceptance file, run Milestone 0, then execute through the repository-owned production runtime. | Blocker: AC-TODO-001 has not yet been dispatched. | `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` sections 3, 4, and 8.5. | After AC-TODO-001 is dispatched or the operator reprioritizes. | 2026-08-06 |
| AC-TODO-004 | P1 | ready | SwarmRecall secret hygiene / Swarm operator | Remove plaintext copies of the local-only Recall key and restore Windows-environment-only handling. | Replace two hard-coded script values with environment reads, sanitize three local log/archive copies with rollback, rotate once, and prove old-denied/new-accepted. | Low immediate exposure because Recall binds only to `127.0.0.1:3300`; progress work took priority. | Live listener proof on 2026-08-06; Windows environment-variable secret policy. | After Swarm acceptance unless a listener/network boundary changes. | 2026-08-06 |
| AC-TODO-005 | P1 | ready | AgentCore runtime / Codex | Reconcile PG18 to one governed lifecycle owner and prove reboot recovery. | Follow the current reconstruction completion sequence and create live lifecycle evidence. | Outside the current worker/productivity task. | `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` sections 6.1 and 8.1. | Before unattended commercial LangGraph operation. | 2026-08-06 |
| AC-TODO-006 | P1 | ready | Neutral Recall integration / Codex + Swarm operator | Prove global/project pool isolation and consistent server-side projection identity. | Run the existing isolation and projection acceptance path without adding direct IDE Recall access. | Current acceptance evidence is missing. | `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` sections 1, 6.2, and 8.2. | Before declaring PC-wide semantic-memory production close. | 2026-08-06 |
| AC-TODO-007 | P2 | ready | Documentation operations / Codex | Establish a versioned local official-document mirror/index policy for critical tools. | Define source, version, refresh cadence, integrity metadata, and authority classification; first correct the current `tools/caveman-docs` label because it contains Caveman, not Morph, sources. | Policy was discussed but never implemented. | Operator direction on 2026-08-06; Arabold remains the current official-doc cache authority. | After both P0 items are dispatched. | 2026-08-06 |
| AC-TODO-008 | P2 | ready | Prompt optimization / Codex | Benchmark Caveman on representative large prompts and define a quality/size trigger. | Compare intent fidelity and token reduction across at least five real prompts before considering automatic invocation. | A single prompt test is insufficient for transparent automation. | 2026-08-06 live test: 350 words -> 217 words, 38.0% reduction, validation passed. | After current production P0/P1 work or explicit operator reprioritization. | 2026-08-06 |
| AC-TODO-010 | P0 | blocked | Repository secret hygiene / Codex + operator | Triage 13 pre-existing secret-like artifacts reported by the repository-wide scan without exposing their values. | Obtain explicit security-remediation approval; classify tracked versus untracked artifacts, rotate any live credentials, create rollback evidence, then sanitize or remove only exact approved files. | Security remediation and deletion require operator approval; this checkpoint neither opened nor modified the flagged artifacts. | Sanitized path-only scan on 2026-08-06: 12 legacy credential artifacts under `langsmith-projects/.../.mcp*` and one inherited untracked MiniMax recovery artifact. | Immediately after operator approval; before treating the whole repository secret scan as clean. | 2026-08-06 |

## Closed commitments

Move an item here only with its closure evidence. Do not delete history.

| ID | Closed | Scope / owner | Outcome | Closure evidence |
| --- | --- | --- | --- | --- |
| AC-TODO-009 | 2026-08-06 | Cross-IDE documentation governance / Codex | Established a dedicated read-only documentation guard and sole bounded documentation-maintainer worker path; ordinary implementation workers are structurally blocked from documentation targets, generated projections remain projection-worker-only, and the global IDE policy carries the handoff rule. | `docs/agent-policy/DOCUMENTATION_GOVERNANCE.md`; `tools/cheap-workers`; `AUTH-2026-08-06-DOCUMENTATION-GUARD`; acceptance audit for this checkpoint. |
| AC-TODO-003 | 2026-08-06 | Codex worker stack / Codex | Promoted the cheap-worker stack to repository-owned v0.4.0 with structural secret and file-size preflight, crash-safe atomic replacement, guarded documentation roles, deterministic deployment/rollback, and controlled-production acceptance. | `tools/cheap-workers`; 32/32 canonical and deployed tests; zero npm vulnerabilities; live nine-tool schema; independent remediation review `ACCEPT`; acceptance audit for this checkpoint. |
