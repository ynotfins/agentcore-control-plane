# Checklist Standard

**Authority:** `PROJECT_ANCHOR.md` §0.1 → this policy. Machine-readable: `contracts/project-execution-policy.json`.

## Canonical state

The canonical execution state is machine-readable: `<project>/.agentcore/checklists/state.json` during this pre-platform stage, migrating to PostgreSQL when the memory platform lands (M3+). **Markdown checkboxes are generated projections of that state — Markdown is never the only canonical execution database.**

## Status vocabulary

Exactly these values:

| Status | Meaning |
| -- | -- |
| `pending` | Not started |
| `in_progress` | Actively being worked |
| `passed` | Complete **with evidence recorded** |
| `blocked` | Cannot proceed; blocker recorded |
| `failed` | Attempted and failed; failure evidence recorded |
| `skipped_with_reason` | Intentionally not done; reason and approver recorded |

## State entry shape

Each checklist item in `state.json`:

```json
{
  "id": "M1.A2.m3",
  "type": "micro",
  "parent": "M1.A2",
  "action": "…",
  "expected_output": "…",
  "validation": "…",
  "status": "pending",
  "evidence_ref": null,
  "rollback": "…",
  "agent": null,
  "updated_at": null
}
```

## Evidence rules

- A Micro step may be marked `passed` **only** when `evidence_ref` points to real evidence: a file path, commit hash, test transcript, validator output, checkpoint ID, or artifact location.
- A Micro step may **not** be marked complete from partial implementation, intention, agent confidence, or narrative claims.
- `skipped_with_reason` requires a non-empty reason and the approving identity.
- A Macro step closes only when every child Micro step is `passed` or `skipped_with_reason`.
- A Milestone closes only when every required Macro step is closed and the exit gate passes (`MILESTONE_EXECUTION_STANDARD.md`).

## Markdown projection

Generated checklists render one line per item:

```markdown
- [x] M1.A2.m3 — action summary (passed — evidence: ops/evidence/…)
- [ ] M1.A2.m4 — action summary (blocked — waiting on …)
```

`[x]` renders only for `passed` and `skipped_with_reason`. If a Markdown projection disagrees with the machine-readable state, the machine-readable state wins and the projection must be regenerated; validators treat disagreement as a failure.
