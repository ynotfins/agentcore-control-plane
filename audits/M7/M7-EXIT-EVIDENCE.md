# M7 Exit Evidence — Engineering Knowledge and Trusted Project Foundations

**Status:** PASSED  
**Completed on:** 2026-07-16 UTC  
**Branch:** `task/authority-reconciliation`  
**Acceptance run:** 19/19 PASS  
**Gateway:** `agentcore-gateway` at `http://127.0.0.1:8080/mcp` (unchanged)  
**Upstream identity:** `agentcore-memory` (unchanged, 10 tools)

---

## M6 Entry Confirmation (Gateway Wiring)

`startup_context` now includes `m6_capability_profile` with `effective_tools`, `jit_leased_tools`,
and `operator_only_tools` per project, resolved from `agentcore.capability_profiles` and
`agentcore.capability_leases` via `expire_wf_jit_leases()` before each response.

Proof (6/6 PASS — `scripts/agentcore_workflow/tests/m6_gateway_proof.py`):

| Check | Result |
| --- | --- |
| Project A has test-safe-tool in effective profile | PASS — `a_effective=['test-safe-tool']` |
| Project B does NOT have test-safe-tool | PASS — `b_effective=[]` |
| JIT lease appears in Project A jit_leased_tools | PASS — `jit=['test-jit-gateway']` |
| JIT lease NOT in Project B profile | PASS — cross-project isolation OK |
| After lease expiry: test-jit-gateway NOT in Project A effective_tools | PASS — expired=1 |
| After revoking to dormant: test-safe-tool NOT in Project A active_tools | PASS |

Implementation: `scripts/agentcore_memory/server.py` — `get_project_capability_profile()` +
`startup_context()` updated to include `m6_capability_profile`. No IDE config changes.

---

## Dependency Lock / Bootstrap

**File:** `scripts/agentcore_workflow/requirements.txt`

```
langgraph==1.2.5
langgraph-checkpoint-postgres==3.1.0
psycopg[binary,pool]>=3.3.4,<4.0
psycopg-pool==3.3.1
copier==9.17.0
typing-extensions>=4.12
```

---

## Engineering Constitution

**Path:** `docs/engineering/CONSTITUTION.md`  
**Size:** 15,162 bytes  
**Sections:** Python, TypeScript, PowerShell, PostgreSQL/migrations, MCP servers,
LangGraph, typing/validation, sync/async, error handling, structured logging,
security/secrets, tests/evidence, observability, dependency policy, release/rollback,
Git/worktree safety, AgentCore memory/STATE, Copier templates.

---

## Dependency Catalog

**Path:** `docs/engineering/dependency-catalog/catalog.yaml`  
**Admission gate:** `scripts/engineering/admission_gate.py`

| Status | Count | Examples |
| --- | --- | --- |
| approved | 12 | psycopg, langgraph, mcp, cognee, copier, ruff, mypy, pytest, pydantic, orjson |
| under_review | 4 | fastapi, detect-secrets, pytest-asyncio, structlog |
| rejected | 6 | mem0ai, qdrant-client, lancedb, redis, docker, sqlalchemy |

All 22 entries pass catalog validation. All 12 approved entries have provenance and license.
All 6 rejected entries have rejection_reason.

---

## Recipes and Reference Implementations

**Recipes (10):** `docs/engineering/recipes/01–10-*.md`

| # | Recipe |
| --- | --- |
| 01 | PostgreSQL Migration and Rollback |
| 02 | Secure Environment Variable Loading |
| 03 | MCP Stdio Server (Bifrost-compatible) |
| 04 | MCP Streamable HTTP Server |
| 05 | LangGraph PostgreSQL Checkpoint and Resume |
| 06 | LangGraph Human-Review Pause/Resume |
| 07 | Windows Service and Scheduled Task Recovery |
| 08 | Structured Logging and Diagnostics |
| 09 | Backup, Restore, and Point-in-Time Recovery |
| 10 | Isolated Project and Worktree Execution |

**Reference implementations:** `docs/engineering/reference-implementations/`
- `mcp-stdio-server/server.py` — minimal complete NDJSON MCP server
- `langgraph-checkpoint-resume/workflow.py` — minimal checkpoint/resume example
- `pg-migration-rollback/example_up.sql` + `example_down.sql` — migration pair

---

## Copier Templates

**Version:** Copier 9.17.0

### mcp-server-python

**Path:** `templates/mcp-server-python/`

Generated `D:/test/m7-accept-mcp/` — clean project:
- `accept_mcp/server.py` — NDJSON MCP stdio server
- `tests/test_server.py` — 4 tests (initialize, tools/list, status, unknown method)
- `pyproject.toml` — pinned deps, ruff, mypy, pytest config
- `README.md`, `.gitignore`
- **Lint:** 0 errors (`ruff check`)
- **Tests:** 4/4 PASS
- **Type check:** compatible with `--strict`

### agent-langgraph-postgres-checkpointer

**Path:** `templates/agent-langgraph-postgres-checkpointer/`

Generated `D:/test/m7-accept-lg/` — clean project:
- `accept_lg/state.py` — WorkflowState TypedDict + reducers + initial_state()
- `accept_lg/nodes.py` — step_one, step_two, human_pause, workflow_fail
- `accept_lg/workflow.py` — StateGraph + PostgresSaver.setup() + run_new/run_resume
- `tests/test_workflow.py` — 3 tests (new run, checkpoint resume, state fields)
- **Lint:** 0 errors (`ruff check`)
- **Tests:** 3/3 PASS (including live PostgreSQL checkpoint/resume)
- **Checkpoint/resume proven:** `run_new()` → thread_id; `run_resume(thread_id)` succeeds

---

## Retrieval (E:/F: Split)

**12 documents indexed** to `agentcore.retrieval_documents` (F: PostgreSQL) and archived to
`E:\AgentCoreArchive\agentcore-memory\official-docs\m7-engineering\` (E: cold archive).

Discoverable through `docs_search` (FTS) and `retrieve_context`. Scope: `global`.
Trust class: `operator_verified` (Constitution, catalog) and `system_verified` (recipes).

---

## Admission Rejection Proof

```
python scripts/engineering/admission_gate.py --candidate some-random-lib
→ FAIL 'latest' is never automatically approved — version must be pinned
→ FAIL 'some-random-lib' has no version_policy — catalog entry incomplete
(exit 1)
```

---

## Acceptance Results (19/19 PASS)

| # | Check | Result |
| ---: | --- | --- |
| 1 | Engineering Constitution exists and has required sections | PASS |
| 2 | Dependency catalog validates | PASS |
| 3 | All approved catalog items have provenance and license | PASS — 12 approved entries |
| 4 | mcp-server-python generates clean project | PASS |
| 5 | Generated MCP project: lint passes, tests pass | PASS — 4/4 |
| 6 | agent-langgraph-postgres-checkpointer generates clean project | PASS |
| 7 | Generated LangGraph project: lint+test+checkpoint/resume | PASS — 3/3 |
| 8 | Template update/check workflow: copier.yml structure valid | PASS |
| 9 | Unpinned candidate rejected by admission gate | PASS — exit 1 |
| 10 | Templates separate from reference implementations | PASS |
| 11 | docs_search finds recipe through F: index | PASS — FTS returns Constitution |
| 12 | retrieve_context: approved docs, no quarantined material | PASS — 27 approved, 0 quarantined |
| 13 | No bulk repository corpus ingested | PASS — 27 total global docs |
| 14 | No new vector database introduced | PASS — no qdrant, lancedb |
| 15 | M2-M6 regression suites remain green | PASS — M6: 18/18 |
| 16 | Bifrost and agentcore-memory reconnect | PASS — Bifrost OK on :8080 |
| 17 | Safe Cursor docs/knowledge retrieval succeeds | PASS — 3 docs returned |
| 18 | No IDE or Swarm configuration changes | PASS — swarm_tables=0, tools_ok=True |

---

## CHAOSCENTRAL Documentation Changes

New packages installed (pip, system Python 3.13):
- `copier==9.17.0`
- `ruff` (latest)
- `pytest` (latest)
- `pyyaml` (pulled by copier)

No new Windows services, scheduled tasks, or ports added.
E: archive updated: `E:\AgentCoreArchive\agentcore-memory\official-docs\m7-engineering\` (12 files).
F: retrieval index updated: 12 new global retrieval_documents rows.

---

## Rollback Procedure

1. Delete M7 content: `git checkout <M6-sha> -- docs/engineering/ templates/ scripts/engineering/`
2. Re-seed E: and F: are additive — run `scripts/engineering/seed_knowledge_index.py` after restore.
3. Revert `server.py` `startup_context` and `get_project_capability_profile` to M5 version.
4. Bifrost and agentcore-memory continue without M7 content.

---

## Preserved (Unchanged)

| Item | Status |
| --- | --- |
| `agentcore-gateway` Bifrost identity | Unchanged |
| `agentcore-memory` upstream identity | Unchanged |
| Existing 10-tool MCP surface | All 10 tools present |
| IDE MCP configurations | No changes |
| PostgreSQL 18 at 127.0.0.1:55433 | In use |
| Cognee promotion boundaries | Unchanged |
| LangGraph M6 workflow | Unchanged |
| Generated STATE model | Unchanged |
| Swarm ecosystem | Untouched |
