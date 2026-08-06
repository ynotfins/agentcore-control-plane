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
| AC-TODO-003 | P1 | in_progress | Codex worker stack / Codex | Qualify and harden the cheap-worker routes and Morph apply boundary for routine production use. | Preserve the now-proven routes/tests; add repo-owned deployment authority, structural secret/file-size preflight, and an atomic-write decision before calling the stack production-closed. | The live stack works, but its canonical source is only under Codex home and prompt-only secret discipline is insufficient for unattended editing. | `C:\Users\ynotf\.codex\mcp\cheap-workers`; 11/11 tests; all five live routes proven on 2026-08-06; current DeepSeek, MiniMax, and Morph official docs. | Before unattended edit-worker use; controlled Codex-reviewed use may continue. | 2026-08-06 |
| AC-TODO-004 | P1 | ready | SwarmRecall secret hygiene / Swarm operator | Remove plaintext copies of the local-only Recall key and restore Windows-environment-only handling. | Replace two hard-coded script values with environment reads, sanitize three local log/archive copies with rollback, rotate once, and prove old-denied/new-accepted. | Low immediate exposure because Recall binds only to `127.0.0.1:3300`; progress work took priority. | Live listener proof on 2026-08-06; Windows environment-variable secret policy. | After Swarm acceptance unless a listener/network boundary changes. | 2026-08-06 |
| AC-TODO-005 | P1 | ready | AgentCore runtime / Codex | Reconcile PG18 to one governed lifecycle owner and prove reboot recovery. | Follow the current reconstruction completion sequence and create live lifecycle evidence. | Outside the current worker/productivity task. | `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` sections 6.1 and 8.1. | Before unattended commercial LangGraph operation. | 2026-08-06 |
| AC-TODO-006 | P1 | ready | Neutral Recall integration / Codex + Swarm operator | Prove global/project pool isolation and consistent server-side projection identity. | Run the existing isolation and projection acceptance path without adding direct IDE Recall access. | Current acceptance evidence is missing. | `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` sections 1, 6.2, and 8.2. | Before declaring PC-wide semantic-memory production close. | 2026-08-06 |
| AC-TODO-007 | P2 | ready | Documentation operations / Codex | Establish a versioned local official-document mirror/index policy for critical tools. | Define source, version, refresh cadence, integrity metadata, and authority classification; first correct the current `tools/caveman-docs` label because it contains Caveman, not Morph, sources. | Policy was discussed but never implemented. | Operator direction on 2026-08-06; Arabold remains the current official-doc cache authority. | After both P0 items are dispatched. | 2026-08-06 |
| AC-TODO-008 | P2 | ready | Prompt optimization / Codex | Benchmark Caveman on representative large prompts and define a quality/size trigger. | Compare intent fidelity and token reduction across at least five real prompts before considering automatic invocation. | A single prompt test is insufficient for transparent automation. | 2026-08-06 live test: 350 words -> 217 words, 38.0% reduction, validation passed. | After current production P0/P1 work or explicit operator reprioritization. | 2026-08-06 |

## Closed commitments

Move an item here only with its closure evidence. Do not delete history.
