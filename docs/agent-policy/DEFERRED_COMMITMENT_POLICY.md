# Deferred Commitment Policy

**Authority:** `PROJECT_ANCHOR.md` section 0.1 -> this policy. Machine-readable registration: `contracts/project-execution-policy.json`.

## Purpose

Prevent explicit operator commitments from disappearing when they cannot be completed in the current task. The cross-project ledger is `docs/current/MASTER_TODO.md`.

## Authority boundary

- Active project Milestones, Micro checklists, acceptance contracts, and generated STATE remain authoritative for project execution.
- The master ledger is a working cross-project index, not architecture authority and not a replacement for project tracking.
- When a ledger item conflicts with an active project artifact, the project artifact wins. Reconcile the ledger entry immediately by linking to, revising, or superseding it.
- Do not duplicate work already tracked by an active Milestone, checklist, or generated STATE. Link to that authoritative item instead.

## Entry rule

Before leaving an explicit commitment unfinished, the active lead agent must either complete it or add/update one ledger item. An entry qualifies only when it is:

1. explicitly requested or approved by the operator;
2. concrete and actionable;
3. unable to finish safely inside the current task;
4. not already represented by an active authoritative tracker; and
5. assigned a priority, owner, next action, deferral reason, evidence link, and recheck trigger.

Ideas, speculative features, and unapproved wish-list items do not enter the ledger.

## Execution rule

- Review the ledger at session recovery, Milestone entry, and Milestone exit.
- "First opportunity" means immediately after the active safety-critical or operator-selected task, provided the item is ready and no higher-priority ready item exists.
- A ready P0 or P1 item may be bypassed only by an explicit operator priority change or a recorded dependency/blocker.
- `blocked` requires the exact blocker and a deterministic recheck trigger. Time alone is not a blocker.
- Close an item only with evidence: a commit and validation result, a dated acceptance artifact, a live probe, or explicit operator disposition.
- Superseded items remain visible with the replacement item or authority reference.

## Required ledger fields

`ID`, `priority`, `status`, `scope`, `owner`, `commitment`, `next action`, `deferral reason`, `authority/evidence`, `recheck trigger`, and `last reviewed`.

Allowed statuses: `ready`, `in_progress`, `blocked`, `done`, `superseded`.

## Review ownership

The active lead agent owns the review and update. Independent reviewers verify closure evidence but do not reprioritize or create architecture authority. Items that miss their recheck trigger are surfaced to the operator during the next task update; they are never silently aged out.
