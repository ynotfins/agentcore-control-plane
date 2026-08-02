# Context Engine LangGraph Live Builder Blocker — 2026-08-02

**Status:** M1 live-builder criterion **INCOMPLETE**  
**Authority:** RUN10 live certification attempt (post RUN9 deterministic reclassification)

## Summary

Two live `AGENTCORE_WORKER_MODE=llm` production runs were executed from `D:\github\agentcore-control-plane\scripts` with extended timeouts (`AGENTCORE_WORKER_TIMEOUT_SEC=900`, `AGENTCORE_OPENROUTER_TIMEOUT_SEC=300`). Both approved models failed in the DA builder with **HTTP ReadTimeout** at ~201s — well below the configured 900s worker ceiling and 300s OpenRouter read ceiling.

| Attempt | Provider / Model | run_db_id | thread_uuid | Builder outcome | wf_evidence rows |
|---|---|---|---|---|---|
| 1 (preferred) | gemini / gemini-3.6-flash | `d1e246ae-9ad1-4dec-9003-f7695fc75300` | `95164566-26eb-4e65-a7a5-ebad20c948af` | ReadTimeout ~209s | 0 (pre-fix) |
| 2 (alternate) | openrouter / deepseek/deepseek-v4-flash | `0cadc66e-de1e-4526-9ecc-c5fc7e9ab96f` | `0753e194-75fe-4fca-b735-7479c118d2bb` | ReadTimeout ~201s | 1 (`da_builder_result` failure) |

**Live builder succeeded:** **No**  
**CERTIFICATION_NOTE.md created in worktree:** **No**

## Timeout telemetry

### Gemini attempt (`d1e246ae-…`)

```text
Shell elapsed:     ~209573 ms
Worker timeout:    AGENTCORE_WORKER_TIMEOUT_SEC=900 (not reached)
OpenRouter timeout: AGENTCORE_OPENROUTER_TIMEOUT_SEC=300 (not reached)
Failure class:     ReadTimeout (HTTP read layer inside agent.invoke)
Graph result:      completed=true, judge_verdict=proceed, score=1.0
DB run status:     failed
completed_at:      null
checkpoint_count:  10
errors:
  - memory_gateway_bootstrap_degraded: URLError
  - DA builder failed: ReadTimeout: The read operation timed out
```

### Deepseek attempt (`0cadc66e-…`)

```text
Shell elapsed:     ~208274 ms
Builder elapsed_ms: 201536 (from wf_evidence.detail)
Worker timeout:    AGENTCORE_WORKER_TIMEOUT_SEC=900 (not reached)
OpenRouter timeout: AGENTCORE_OPENROUTER_TIMEOUT_SEC=300 (not reached)
Failure class:     ReadTimeout (HTTP read layer inside agent.invoke)
Graph result:      completed=true, judge_verdict=proceed, score=1.0
DB run status:     failed
completed_at:      null
checkpoint_count:  10
errors:
  - DA builder failed: ReadTimeout: The read operation timed out
```

### Interpretation

- Failures are **not** `WorkerTimeout` (the governed 900s thread guard never fired).
- Both models stall at **~200–209s**, suggesting an HTTP client read timeout below the operator-configured 300s (likely langchain-openrouter / httpx default interpretation before the `httpx.Timeout` patch in `deepagents_worker._chat_openrouter`).
- Bifrost gateway returned **401** on probe (`http://127.0.0.1:8080/mcp`); gemini run also logged `memory_gateway_bootstrap_degraded: URLError`. OpenRouter calls are direct (not via gateway), so builder failure is independent of gateway auth but memory bootstrap was degraded.

## Evidence persistence defect (fixed during RUN10)

RUN9 falsely reported `evidence_count: 1` while `wf_evidence` was empty. RUN10 gemini attempt also had 0 workflow-produced rows.

**Root cause (code):**

1. `workflow_cli.cmd_start` pre-registers `run_db_id` but did not pass it into `initial_state` / `run_workflow`.
2. `node_evidence_record` and `node_da_builder` swallowed `record_evidence` exceptions (`except Exception: pass`).

**Fix applied (uncommitted):**

- Pass `run_db_id` from CLI → `run_workflow` → `initial_state`.
- `_json_safe()` + `default=str` in `db.record_evidence`.
- Surface persistence failures in node errors instead of silent pass.

**Verification:** Deepseek run `0cadc66e-…` persisted `da_builder_result` evidence after fix (`evidence_count=1`).

## Worktree note

Evidence shows builder worktree `D:\github\agentcore-context-engine` (project `root_path`) rather than isolated `D:\agentcore-worktrees\agentcore-context-engine`. Init registered the isolated worktree, but `node_start` resolves `worktree_path` from `projects.root_path`. This does not explain ReadTimeout but should be aligned before a successful live cert.

## Operator commands (repro)

```powershell
cd D:\github\agentcore-control-plane\scripts
$env:AGENTCORE_WORKER_MODE = "llm"
$env:AGENTCORE_WORKER_TIMEOUT_SEC = "900"
$env:AGENTCORE_OPENROUTER_TIMEOUT_SEC = "300"

# Attempt 1
python -m agentcore workflow start --project-key agentcore-context-engine --milestone M1 --risk-profile medium --provider gemini --model gemini-3.6-flash --goal "Create CERTIFICATION_NOTE.md in the isolated worktree only." --json

# Attempt 2 (alternate)
python -m agentcore workflow start --project-key agentcore-context-engine --milestone M1 --risk-profile medium --provider openrouter --model deepseek/deepseek-v4-flash --goal "Create CERTIFICATION_NOTE.md in the isolated worktree only." --json
```

## Next steps (operator)

1. Re-run live cert after `httpx.Timeout` OpenRouter patch with `AGENTCORE_OPENROUTER_TIMEOUT_SEC=600` or higher.
2. Confirm OpenRouter API key and model availability for `google/gemini-3.6-flash` and `deepseek/deepseek-v4-flash`.
3. Repair Bifrost gateway / memory bootstrap (`memory_gateway_bootstrap_degraded`).
4. Align `worktree_path` to `D:\agentcore-worktrees\agentcore-context-engine` in `node_start`.
5. Re-attempt RUN10 live cert; do **not** treat RUN9 deterministic run as live-model proof.

## Related artifacts

- `audits/CONTEXT_ENGINE_LANGGRAPH_RUN9_RECLASSIFIED_2026-08-02.md`
- `audits/CONTEXT_ENGINE_LANGGRAPH_RUN10_LIVE_2026-08-02.json`
- `audits/CONTEXT_ENGINE_LANGGRAPH_RUN10_DEEPSEEK_START_2026-08-02.json`
- `audits/CONTEXT_ENGINE_LANGGRAPH_RUN10_START_2026-08-02.json` (gemini)
