# M0 — Project Bootstrap and Alignment

**Standard:** `docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md`
**Risk classification:** low (read/discovery + bounded governance-file writes)
**Approved tool profile:** bootstrap
**Rollback point:** {{restore_point_ref — clean commit/tag before M0 work}}
**Dependencies:** none

## Outcome

The project has one accurate charter, Milestone plan, checklist state, tool manifest, and safe initial tool surface. No broad implementation has begun.

## Entry criteria

- Repository/worktree exists and is registered via `agentcore-project-router`.
- Operator's original project prompt is available.

## Exit criteria

- `PROJECT_CHARTER.md` exists with the operator prompt preserved verbatim.
- `MILESTONES.md`, `TOOL_MANIFEST.yaml`, `PROJECT_STATE.json`, `RISK_REGISTER.md`, `ACCEPTANCE_TESTS.md`, and `checklists/state.json` exist and validate.
- Context Fabric capture + drift check recorded.
- Arabold exact-version documentation checkpoint recorded for declared dependencies.
- Architecture discovery notes recorded (Serena/Depwire/Tentra).
- First tool audit completed; Bootstrap-only tools marked dormant if not needed for M1.
- Restore point created.

## Macro steps

### M0.A1 — Identity and context

| ID | Micro step | Expected output | Validation | Status |
| -- | -- | -- | -- | -- |
| M0.A1.m1 | Activate project via project router | active-project state | `project_status` | pending |
| M0.A1.m2 | Load global context via agentcore-memory | startup context (or recorded degraded state) | tool response captured | pending |
| M0.A1.m3 | Read global + project rules per read order | reading log in PROJECT_STATE | list of files read | pending |
| M0.A1.m4 | Preserve operator prompt verbatim in charter | charter section populated | diff vs original | pending |

### M0.A2 — Repository reality

| ID | Micro step | Expected output | Validation | Status |
| -- | -- | -- | -- | -- |
| M0.A2.m1 | Inspect manifests/lockfiles/git history | inventory notes | evidence file | pending |
| M0.A2.m2 | Context Fabric capture + drift check | checkpoint ID | cf_health/cf_drift output | pending |
| M0.A2.m3 | Architecture discovery (Serena/Depwire/Tentra) | architecture notes | evidence file | pending |
| M0.A2.m4 | Resolve exact dependency versions via Arabold | version table | docs index entry | pending |

### M0.A3 — Governance files and tool surface

| ID | Micro step | Expected output | Validation | Status |
| -- | -- | -- | -- | -- |
| M0.A3.m1 | Create governance files from templates | all 8 files present | validator pass | pending |
| M0.A3.m2 | Select core/M1 tools in TOOL_MANIFEST.yaml | populated manifest | schema validation | pending |
| M0.A3.m3 | Create restore point | commit/tag ref | git log | pending |
| M0.A3.m4 | Run M0 acceptance checks | all exit criteria evidenced | checklist state all passed | pending |
| M0.A3.m5 | First tool audit; dormant unused Bootstrap tools | updated manifest audit fields | manifest diff | pending |

## Checkpoints

- Context Fabric: {{checkpoint_ref}}
- Arabold docs: {{docs_index_ref}}
- Memory/handoff: {{handoff_ref}}
- Tool audit: {{audit_ref}}
