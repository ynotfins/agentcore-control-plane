# MASTER_CONFIG_AND_PROMPT Rebuild — Phase 5

**Date:** 2026-07-25  
**File:** `MASTER_CONFIG_AND_PROMPT.md`

## Changes

- Updated client status table from Phase 4A–4E evidence (Cursor Stage B live; Codex desktop healthy; MiniMax Code/Classic separated; OI CLI persistence; Cherry DRIFT-01 reconciled; GUI OI unsupported).
- Inserted verbatim **SWARM DEVELOPMENT AND RUNTIME BOUNDARY** section.
- Strengthened Cursor `@` + absolute-path rule; removed July-12-as-baseline language.
- Synced `ide-profiles/IDE_CAPABILITY_MATRIX.yaml` `managed_ides` enrollment/dimensions with IDE profiles (`matrix_revision: 2026-07-25`).
- Re-rendered IDE `GLOBAL_RULES.md` / install / validation files.

## Validators (PASS)

```text
validate_contracts.py              OK
test_contracts.py                  PASS 124 checks
render_ide_rules.py --check        OK
validate_ide_enrollment_scope.py   OK
validate_cursor_prompt_format.py   PASS
validate_client_status.py          OK
```

## Status signal

`MASTER_CONFIG_REBUILD_2026-07-25_PASS`
