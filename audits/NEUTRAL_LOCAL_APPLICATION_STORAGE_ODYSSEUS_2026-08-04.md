# Neutral Local-Application Storage and Odysseus Migration — 2026-08-04

Approval: `AUTH-2026-08-04-NEUTRAL-LOCAL-APPLICATION-STORAGE`
AgentCore repository: `D:\github\agentcore-control-plane`, branch `main`
Odysseus repository: `D:\odysseus`, branch `dev`

## Preflight and inherited state

- AgentCore began with unrelated inherited dirty M6-M8 audit, registry/schema, IDE-profile, Langfuse, skill, and runtime files; task staging excludes those except renderer-owned global rules required by this decision.
- Odysseus began with inherited changes in `app.py`, `setup.py`, and `launch-windows.ps1`. The retained behavior is the smallest native boundary: process-scoped SQLite plus loopback Chroma startup.
- I: was live-corroborated as NTFS, label `AgentCore_Staging`, 982,292,299,776 bytes total and 974,204,436,480 bytes free. The operator-supplied 64 KB allocation-unit evidence remains the accepted value because non-elevated `fsutil` returned access denied.
- Before migration, Odysseus PID 61624 owned `127.0.0.1:7000` and Chroma PID 56756 owned `127.0.0.1:8100`; command lines resolved to `D:\odysseus` and `D:\odysseus\data\chroma`.
- No Odysseus/Chroma Windows service or scheduled task was found.

## Authority rollback

Protected-file rollback bundle: `E:\AgentCore\rollback\neutral-localapps-odysseus-20260804-174734`.
Manifest SHA-256: `2CC891F7CD8CFF8165E904C96D15C549A3AC676C121AC94EA5F64002CDCA17D4`.

The repository-local untracked `.agentcore\rollback` tree predated this task and is unrelated; it is excluded from staging. Protected files were not filesystem-read-only, so the logical unlock was a process-scoped `authority_maintainer` capability plus the approval ID during validation. Those variables were not persisted, which restores the normal locked posture after each command.

## Storage decision

- Neutral hot application data: `I:\LocalApps\<AppName>`.
- Neutral cold backups: `E:\LocalApps\Backups\<AppName>`.
- AgentCore staging: `F:\AgentCore\staging`.
- The live `F:\AgentCore\staging` directory was created and verified.
- D: remains source/projects/worktrees/build files; C: remains Windows/programs; H: remains Swarm/neutral-Recall hot storage under its existing boundary.
- Per-application databases, indexes, credentials, services, logs, backups, and recovery remain isolated.

## Odysseus migration evidence

- Final cold backup root: `E:\LocalApps\Backups\Odysseus\20260804-175039`.
- Final quiesced tree: 22 files, 92,139,029 bytes.
- Final manifest SHA-256: `E3B43B1CD11B72EFB768F4530E5A24B0059B984BEEE8E0D1C59B8E41E1C934D9`.
- Restore proof: all 22 files hash-matched under `E:\LocalApps\Backups\Odysseus\restore-tests\20260804-175039`.
- `D:\odysseus\data` is an NTFS junction targeting `I:\LocalApps\Odysseus\data`.
- `Path.resolve()` proved SQLite at `I:\LocalApps\Odysseus\data\app.db` and Chroma at `I:\LocalApps\Odysseus\data\chroma`.
- SQLite `PRAGMA integrity_check` returned `ok`.
- A no-reparse traversal found zero physical `.db`, `.sqlite`, or `.sqlite3` files under `D:\odysseus`.
- Startup loaded the existing auth configuration and one saved session from disk.
- Odysseus health returned HTTP 200; Chroma heartbeat returned HTTP 200; both listeners were loopback-only.
- Live Chroma command line uses `--path I:\LocalApps\Odysseus\data\chroma --host 127.0.0.1 --port 8100`; the launcher now refuses an unverified PID on 8100 and permits only `-BindHost 127.0.0.1`.
- A fresh-start exercise with 8100 initially unbound created Chroma, resolved the actual listener PID 62048, verified its executable and exact I:-drive/loopback command line, required heartbeat HTTP 200, and only then launched Uvicorn. The resulting listeners were PID 15996 on `127.0.0.1:7000` and PID 62048 on `127.0.0.1:8100`.
- A subprocess given a fake inherited PostgreSQL `DATABASE_URL` reported `PROCESS_DB_BOUNDARY=sqlite`.
- The 19-process Odysseus descendant tree had zero connections to ports 55433, 55432, or 65432.

## Validation

- `python scripts/validate_authority_lock.py`: PASS.
- `python scripts/render_ide_rules.py --check`: PASS.
- `python scripts/bifrost/validate_contracts.py`: PASS.
- `python scripts/validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md`: PASS.
- `python scripts/validate_ecosystem_separation.py`: PASS.
- Python compilation of changed AgentCore/Odysseus modules: PASS.
- PowerShell parsing of `launch-windows.ps1`: PASS; an explicit `-BindHost 0.0.0.0` invocation was rejected by the parameter contract.
- A launcher restart with the physical I: data root exposed and then passed a repaired Windows cross-drive setup path (`relpath(I:, D:)` now falls back to an absolute display path).
- Task-owned secret-value scan: 0 hits; junk/generated-file path scan: 0 hits; oversized task files over 1 MB: 0.
- Independent final review: APPROVE, with no actionable findings after the Chroma listener ownership and heartbeat gate was proven.
- Odysseus focused test selection: 2 passed, 2 skipped, 1 failed. The failure is `tests/test_app_db_permissions.py::test_sqlite_db_path_handles_file_uri_forms` in unchanged `core/database.py` handling of a `file://localhost` URI; it is outside the three-file migration patch and is retained as a pre-existing product defect.

## Residuals and stop gates

- PC-restart lifecycle ownership is not certified: no persistent Odysseus task/service exists. The repository launcher completed a full stop/start and live health proof, but installing a persistent owner requires a separate operator-approved design.
- The live process is owned by the current managed foreground launcher session. Closing that session stops Odysseus; Chroma is a launcher child.
- No claim is made that every user-facing session/settings workflow was manually exercised; retained files, startup load, database integrity, and health were verified.
- No AgentCore PG18, legacy PG16, neutral Recall, SwarmVault, or Swarm database was modified or used by Odysseus.
