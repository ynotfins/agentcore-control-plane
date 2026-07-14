# Milestone Execution Standard

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-execution-policy.json`.

## Definitions

- **Milestone** — an outcome boundary with acceptance criteria. Not a time box. Phases may exist *inside* a Milestone; do not use "phase" as a substitute when the work is an acceptance boundary.
- **Macro step** — a substantial workstream under a Milestone. Requires: unique ID, outcome, dependencies, responsible agent/role, a Micro checklist, and acceptance evidence.
- **Micro step** — an atomic, independently verifiable action. Requires: unique ID, action, expected output, validation, evidence location, rollback/repair instruction where relevant, and status.

## Milestone required fields

Every Milestone must define: unique ID, name, outcome, rationale, entry criteria, exit criteria, acceptance checks, required artifacts, rollback point, dependencies, risk classification, approved tool profile, Macro checklist, Micro checklists, Context Fabric checkpoint, Arabold documentation checkpoint, memory/handoff checkpoint, and tool-audit checkpoint.

## Refinement rule

Milestone purposes, exit criteria, and ordering are fixed once approved. Macro/Micro steps are implementation guidance: the executing agent may add, remove, split, or reorder steps inside a Milestone, and adapt implementation details from repository evidence — as long as the Milestone outcome, exit criteria, boundaries, and acceptance guarantees are preserved. Refine the current Milestone's checklists immediately before starting it, using repository state, Context Fabric, Arabold exact-version docs, Serena, Depwire, Tentra, and machine evidence. Do not pre-generate speculative Micro steps for distant Milestones.

## Entry gate (before beginning every Milestone)

1. Confirm the previous Milestone `passed` or has an approved exception recorded.
2. Load current global/project/session context (via `agentcore-memory` and project state).
3. Run Context Fabric capture and drift check.
4. Compare current state against: operator goal, Project Charter, definition of done, architecture, requirements, unresolved assumptions.
5. Review (and refine) the Milestone's Macro and Micro checklists.
6. Resolve exact dependency versions.
7. Query/index exact documentation through Arabold Docs.
8. Verify structural assumptions with Depwire/Tentra/Serena.
9. Select `core_active` tools, `milestone_active` tools, and likely JIT tools; record them in `TOOL_MANIFEST.yaml`.
10. Define the tool budget and expiry rules for the Milestone.
11. Record entry evidence (checklist state + checkpoint references).

**Do not start the Milestone** if context, requirements, dependencies, or acceptance criteria are materially ambiguous — resolve or escalate to the operator first.

## Exit gate (before closing every Milestone)

1. Verify every required Micro step has evidence (see `CHECKLIST_STANDARD.md`).
2. Verify every Macro outcome.
3. Run: tests, lint, type checks, secret scan, dependency/security checks, Depwire `verify_change`, Context Fabric drift check, Tentra architecture/spec alignment, Serena symbol/reference checks where relevant.
4. Compare the implementation with the Project Charter, operator goal, architecture, and acceptance criteria.
5. Run an early-refactor review (obvious debt addressed now, not deferred silently).
6. Update: project state, decisions, risk register, documentation index, memory/handoff, next Milestone.
7. Audit tool usage (see `TOOL_LIFECYCLE_POLICY.md`).
8. Disable: expired JIT tools, completed-Milestone tools, unused tools, failed optional upstreams, tools not required by the next Milestone.
9. Keep a tool `core_active` only when evidence shows frequent continued use.
10. Create a restore point.
11. Commit and push per `docs/GIT_PUSH_ONLY_POLICY.md`.
12. Generate the next Milestone's entry packet (context summary, refined checklist skeleton, tool plan).

**A Milestone is not complete until this gate passes.** Missing Context Fabric or Arabold checkpoints, missing tool audit, or incomplete Micro-step evidence block closure.
