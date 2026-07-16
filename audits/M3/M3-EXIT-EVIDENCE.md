# M3 Exit Evidence — Lossless Context and STATE Projections

**Status:** PASSED  
**Completed on:** 2026-07-15 / 2026-07-16 UTC  
**Database:** PostgreSQL 18.4 at `127.0.0.1:55433/agent_core`  
**Migration:** `m3.001` (`migrations/m3/001_up_lossless_context_state_projections.sql`)  
**Harness:** `scripts/memory_platform/Test-M3LosslessContext.ps1`  
**Acceptance summary:** `audits/M3/m3-acceptance-summary.json` (run `20260715210053`)

## Exit Criteria

| BLUEPRINT.md M3 exit criterion | Result | Evidence |
| -- | -- | -- |
| L0/L1/L2/L3 context hierarchy works | PASS | `m3-acceptance-summary.json` check `L0 L1 L2 L3 compaction and exact source edges` |
| Original long prompts preserved verbatim | PASS | `verbatim preservation, secret redaction, write-time dedupe` |
| Requirements/constraints/assumptions/acceptance/unresolved questions link to exact source spans | PASS | `agentcore.context_source_edges`; 12 exact source edges across L1/L2/L3 |
| Write-time deduplication without deleting originals | PASS | `agentcore.event_dedupe_links` links duplicate to canonical; both original evidence rows remain |
| Token-budgeted and importance-aware context windows | PASS | `agentcore.assemble_context_window(project, 'small')` returned 7 items at 281 tokens <= 512-token budget |
| Hierarchical, versioned, idempotent, restart-safe compaction | PASS | `agentcore.compaction_runs`, `start_compaction_run`, `complete_compaction_run`, `recover_interrupted_compactions` |
| Exact expansion works after compaction | PASS | `agentcore.expand_summary(L3)` returned original source payloads from both sessions |
| Exact expansion works after archival to E: | PASS | artifact copied H: -> E:, hot copy removed, `expand_summary(L1)` returned E: cold path |
| Context assembly obeys model-specific token budgets | PASS | `agentcore.model_context_budgets` + acceptance check above |
| GLOBAL_STATE.md and project STATE.md regenerate deterministically using COMB-style projection | PASS | `Invoke-M3ProjectionWorker.ps1` ran twice; project state hash stable |
| Static/stable context separated from active/dynamic context | PASS | `agentcore.context_bucket` (`static_stable`, `active_dynamic`, `archived`) in summaries and context assembly |
| Projection writes atomic and versioned | PASS | projection worker writes temp then rename; failure simulation preserved previous valid file; `agentcore.projection_revisions` records revision/hash |
| Process interruption during compaction causes no loss/corruption | PASS | controlled PG18 restart with in-progress compaction; recovered as `interrupted_recovered` |
| Multi-session project chronology coherent | PASS | L3 summary includes source events from two sessions |
| Contradictory facts follow proposal/review path | PASS | `agentcore.fact_proposals` status `proposed` |
| Distill decision recorded | PASS | `audits/M2/distill-pre-m3-identification.md` identifies `Siddhant-K-code/distill`; default decision is native implementation first unless sidecar benchmarks prove value |

## Projection Paths and Hashes

| Projection | Path | SHA-256 |
| -- | -- | -- |
| Global state | `C:\Users\ynotf\.agentcore\GLOBAL_STATE.md` | `4A09F9BAA50FBACED6DEBD1453839144BDFF02E829B39F4189D59EFA33FFA9A5` |
| Project state | `.agentcore\STATE.md` | `041079ECE95A97805A2EAC3ED0D5FCB88471274089866D103A59BBC94425D585` |
| Decisions | `.agentcore\DECISIONS.md` | `355283EF5F2ABB99FFD4717649B6F220A5D93C0D29635089B461BEE3BDFD139E` |
| Context index | `.agentcore\CONTEXT_INDEX.md` | `672AA725111D72A7AE2D16367B3B2001861A37CB039C01995DA2F7484FAC21AC` |

## Performance Measurements

- Harness runtime (including one controlled PG18 restart and two projection generations): ~16 seconds.
- Token-budget assembly: 7 selected items, 285 tokens under the 512-token `small` budget.
- Projection file sizes: GLOBAL_STATE 822 bytes, STATE 1253 bytes, DECISIONS 357 bytes, CONTEXT_INDEX 605 bytes.

## Rollback Procedure

M3 rollback is versioned and reversible at the migration boundary:

1. Confirm operator approval.
2. Run `migrations/m3/001_down_lossless_context_state_projections.sql` against PG18 `agent_core`.
3. Restore projection files from `.previous` copies if needed:
   - `.agentcore\STATE.md.previous`
   - `.agentcore\DECISIONS.md.previous`
   - `.agentcore\CONTEXT_INDEX.md.previous`
   - `C:\Users\ynotf\.agentcore\GLOBAL_STATE.md.previous`
4. M2 identities/evidence/queue primitives remain intact because the M3 down migration does not drop M2 tables.

## Out of Scope Confirmed

- No M4 `agentcore-memory` gateway tool expansion.
- No Cognee integration or `cognee_core` schema changes.
- No LangGraph checkpoint tables.
- No dynamic Bifrost leases or IDE config changes.
