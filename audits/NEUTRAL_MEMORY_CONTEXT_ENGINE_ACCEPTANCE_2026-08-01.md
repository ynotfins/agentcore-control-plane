# Neutral Shared SwarmRecall + Context Engine — Acceptance Evidence

**Approval:** `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`  
**ADR:** `docs/adr/ADR-2026-08-01-neutral-shared-swarmrecall-context-engine.md`  
**Timestamp:** 2026-08-01T21:45:00Z

## Decisions executed

- One neutral shared SwarmRecall semantic plane (dual-Recall rejected).
- Portable Context Engine at `D:\github\agentcore-context-engine` (dedicated repo).
- AgentCore keeps gateway, ten-tool facade, PG18 evidence/checkpoints, Cognee.
- Swarm keeps Claw SQLite + Vault; bounded Recall adapter only.

## Live baseline (loopback)

| Service | Bind | Status |
|---|---|---|
| Bifrost / agentcore-gateway | 127.0.0.1:8080 | healthy |
| PG18 AgentCore | 127.0.0.1:55433 | accepting |
| Neutral Recall API | 127.0.0.1:3300 | healthy after reload |
| Neutral PG16 | 127.0.0.1:65432 | listening |
| Meilisearch | 127.0.0.1:7700 | available |
| SwarmClaw | 127.0.0.1:3456 | listening |

## Proofs

1. **Idempotent Recall writes:** same `idempotencyKey` → same memory id `12d936ce-5efd-49ea-86e7-a6cd00da2d8c`.
2. **Meili outage → PG write → outbox/rebuild:** wrote `c59d91f6-01da-4419-a33e-be60dd22e56d` while Meili down; `processSearchOutbox` 1 success; `rebuildMemoriesIndex` 7 rows; search recovered hit.
3. **Gateway tools/list:** 161 tools; **exactly 10** `agentcore_memory-*` tools; **zero** swarm/recall MCP tools.
4. **PG18 backup:** `E:\AgentCoreArchive\agentcore-memory\backups\pg18\20260801-173638` (+ G: copy).
5. **Authority unlock rollback copies:** `E:\AgentCore-Backups\authority-unlock-AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE\20260801-172118` and Swarm twin under `E:\SwarmBackups\...`.
6. **LangGraph production run:** project `agentcore-context-engine`, run `5ed18346-0727-4932-b6a5-3fbfb5c84d70`, thread `9d09cc48-3ef8-4f03-93be-772c59fe7d5a`, milestone M1, `judge_verdict=proceed`, `score=1.0`, **13 PostgresSaver checkpoints**, status completed. Evidence file: `audits/CONTEXT_ENGINE_LANGGRAPH_RUN4_2026-08-01.json`.
7. **Checkpoint survival while Recall stopped:** checkpoint_count remained **13** before/after Recall stop.
8. **Exact-evidence continuity while Recall down:** `propose_fact` returned `ok=true` with `neutral_recall_projection.degraded=true`; `startup_context` still `ok=true`.
9. **Context Engine repo:** local commit `cc21747…`, **75/75 pytest pass**.
10. **SwarmRecall hardening:** fork commit `b272130…` pushed to `origin` ynotfins (not upstream).
11. **Validators:** `validate_authority_lock.py` OK; `validate_contracts.py` OK.
12. **Independent review:** code-reviewer CONDITIONAL PASS; addressed `FORBIDDEN_DEPENDENCY_HINTS` swarmrecall false-positive.

## Physical roots selected

- AgentCore LangGraph / PG18: F: (`F:\PostgreSQL18`, Bifrost runtime as currently wired).
- Neutral Recall / Meili / PG16: in-place reclassify of live H: SwarmData stack (`H:\SwarmData\meilisearch`, PG16 `:65432`).
- SwarmClaw operational: H: / `:3456`.
- Cold backups: E: (AgentCoreArchive + SwarmBackups namespaces).

## Residual risks / follow-ups

- Neutral PG16 `pg_dump` binary not found on PATH during this window — schedule dump via Swarm ops once `pg_dump` for PG16 is located; Meili rebuild-from-PG remains the lexical recovery path.
- `human_pause` interrupt was not entered on the successful M1 auto path; interrupt node remains in topology (`interrupt_before: human_pause`). Checkpoint durability proven instead.
- Cognee reports `degraded_unavailable` (`ModuleNotFoundError`) — pre-existing; not introduced by this change; PG FTS/pgvector still serve retrieval.
- Context Engine GitHub remote not created (operator stop condition); local git only until Tony approves `gh repo create`.
- SwarmClaw plugin added; full Claw packaging/test suite not re-run in this window.
- Meili historically launched with master key on command line (pre-existing); restarted with env-based key where possible — harden Swarm launcher separately.

## Commits / artifacts expected

- AgentCore control plane: ADR + authority + adapters + gate fixes + audits (this push).
- SwarmRecall fork: `b272130` already on origin.
- Context Engine: local `cc21747` (no remote).
- Swarm ecosystem-control: memory-ownership + SWARM_PROJECT_ANCHOR.
- SwarmClaw: `context-engine-plugin.ts`.
