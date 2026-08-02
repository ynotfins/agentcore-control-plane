# RUN9 Reclassification — Deterministic Topology/Checkpointer Only

**Date:** 2026-08-02  
**Authority:** Live-model LangGraph production certification (RUN10)  
**Prior artifact:** `audits/CONTEXT_ENGINE_LANGGRAPH_RUN9_DET_2026-08-02.json`

## Summary

RUN9 (`run_db_id=368634f7-5e5b-4fb3-a830-d5a478629d5b`, `thread_uuid=f5a8f47b-40d1-4d03-9468-095192a5a661`) is **reclassified** as a **deterministic-only** certification. It does **not** satisfy the live cloud-model builder criterion for M1.

## What RUN9 actually proved

| Criterion | Evidence |
|---|---|
| Governed LangGraph topology | 13 PostgresSaver checkpoints on thread `f5a8f47b-…` |
| PostgresSaver persistence | `checkpoint_count=13` in `RUN9_STATUS` and `RUN9_FULL` |
| Judge/scorer path (deterministic worker) | `judge_verdict=proceed`, `score=1.0` |
| Worker mode | `AGENTCORE_WORKER_MODE=deterministic` (explicit in `RUN9_FULL`) |
| Run duration | ~3.5s (`started_at` → `updated_at`), inconsistent with live LLM builder |

## What RUN9 did **not** prove

- Live OpenRouter/Gemini builder execution (`gemini:gemini-3.6-flash` was requested but bypassed by deterministic worker mode).
- Cloud-model file mutation in an isolated worktree.
- Durable `wf_evidence` persistence for the completed micro step.

## False `evidence_count` claim

`RUN9_DET` reported `evidence_count: 1` from in-graph state (`len(result["evidence"])` in `workflow.py`). Direct DB query contradicted this:

| Source | `evidence_count` | Notes |
|---|---|---|
| `RUN9_DET_2026-08-02.json` | **1** | In-memory graph state only |
| `RUN9_EVIDENCE_2026-08-02.json` | **0** | `SELECT … FROM agentcore.wf_evidence WHERE run_id = '368634f7-…'` |
| `RUN9_FULL_2026-08-02.json` | **0** (empty `evidence` array) | Same DB query |

Additional DB facts for RUN9:

- `completed_at` is **null** on `agentcore.wf_runs` despite `status=completed`.
- `wf_evidence` rows: **empty** for `run_id=368634f7-5e5b-4fb3-a830-d5a478629d5b`.

The inflated `evidence_count` in `RUN9_DET` came from LangGraph state accumulation in `node_evidence_record`, while `db.record_evidence()` failed silently (`except Exception: pass` in `nodes.py`). This is a known defect tracked for RUN10 remediation.

## Prior live attempts (RUN5–RUN7)

Live builder paths with `AGENTCORE_WORKER_MODE=llm` (default) timed out:

- RUN5/RUN6/RUN7: `WorkerTimeout: builder exceeded 180s` with `gemini:gemini-3.6-flash`
- RUN5 also hit: missing worktree / `da_enabled=False` execution-path error before timeout fixes

RUN9 was intentionally run with `AGENTCORE_WORKER_MODE=deterministic` to certify topology/checkpointer/judge under zero-cost fixture worker after live timeouts.

## Reclassification verdict

| Label | Value |
|---|---|
| **RUN9 classification** | `deterministic_topology_checkpointer_validation` |
| **Live-model cert?** | **No** |
| **Usable for M1 live-builder gate?** | **No** — superseded by RUN10 live attempt |
| **Usable for topology/PostgresSaver gate?** | **Yes** (with evidence-persistence caveat) |

## Operator command (for audit reproducibility)

```powershell
cd D:\github\agentcore-control-plane\scripts
$env:AGENTCORE_WORKER_MODE = "deterministic"
python -m agentcore workflow start `
  --project-key agentcore-context-engine `
  --milestone M1 `
  --risk-profile medium `
  --provider gemini `
  --model gemini-3.6-flash `
  --goal "M1 bootstrap validation (deterministic worker)" `
  --json
```

## Downstream impact

- `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md` item #5 must be read as **deterministic topology cert only**, not live-model cert.
- M1 **live-builder** criterion remains **incomplete** until RUN10 (or documented blocker).
