# Workflow Operator Launch Acceptance — 2026-08-02

**Status:** STUB — operator cwd + production/Studio isolation corrections documented; full re-run optional.

**Docs updated:** `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md`

## Verified (2026-08-02, live machine)

| # | Check | Result | Notes |
|---|---|---|---|
| 1 | `python -m agentcore workflow topology` from repo root | **FAIL** | `ModuleNotFoundError: No module named 'agentcore'` |
| 2 | Same from `D:\github\agentcore-control-plane\scripts` | **PASS** | Fingerprint `a86e40e8ddd0a370…` |
| 3 | Repo root + `PYTHONPATH=…\scripts` | **PASS** | Equivalent; `scripts` cwd preferred |
| 4 | Full Python path when bare `python` missing | **PASS** | `C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe` |

## Optional follow-up (non-destructive)

- [ ] `workflow status --project-key <fixture>` against existing fixture run (no new `start`)
- [ ] Studio `--no-browser` launch smoke; confirm `/docs` 200
- [ ] Confirm production `thread_uuid` returns 404 in Studio (isolation)

## Isolation invariants (must remain true)

- Production: `PostgresSaver` → PG18 `public.checkpoints`
- Studio: Agent Server dev checkpointer only
- Production and Studio **never** share thread IDs
- Studio **cannot** inspect production PostgresSaver threads/checkpoints
