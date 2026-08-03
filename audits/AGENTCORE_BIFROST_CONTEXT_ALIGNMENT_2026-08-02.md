# AgentCore Bifrost and Context Alignment Acceptance — 2026-08-02

**Approval:** `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`
**Capability:** `authority_maintainer`
**Status:** IN PROGRESS
**Scope:** Authority/current-state reconciliation, Arabold official-doc indexing, Context Fabric committed-state baseline, and project-owned Cursor subagents
**Explicit exclusions:** No OmniRoute, Hindsight, Graphify, CrewAI, new MCP-upstream, inference-route, Swarm-runtime, database, credential, or live IDE configuration change. The only live gateway mutation is the governed Context Fabric client rewire described below.

## Preflight

- Repository: `D:\github\agentcore-control-plane`
- Branch: `main`
- Before HEAD: `da9f6ccd4e4b9f646f213a4faecf95ba1586a75c`
- Rollback root: `E:\AgentCore-Backups\agentcore-control-plane\context-alignment-20260802-232010`
- Inherited dirty state was inventoried before editing and remains excluded from this task's stage set.
- Protected-file attributes were writable before the pass; authority is enforced by approval identity, rollback, validation, review, and recorded hashes rather than an NTFS read-only bit.

### Before hashes and rollback proof

| File | SHA-256 before | Backup match |
| --- | --- | --- |
| `BLUEPRINT.md` | `D0C27C90A25C62C65BEB0068A193811FD4F617B9BD1362DCEB84C26B167943CB` | PASS |
| `CONTEXT_BLOCK.md` | `34CE4317D1CF6E28DFE663FE14DD41F0169DCD78D5E2E0209F13491932E1BDF9` | PASS |
| `DOC_AUTHORITY.md` | `76D6CE8764F7E2A09733713FACB47E094AF6CD6FDCFB854A5ECD5DC40336F47F` | PASS |
| `MASTER_CONFIG_AND_PROMPT.md` | `768F73724E557F5DFEC72620253093673976BEB9286DA6E6E2E971FCD55514F3` | PASS |
| `MILESTONES.md` | `3E0FA5F320FBDC40F5E1683BDFF2982B76B4FC98E7D3953D335965ED51C01B2D` | PASS |
| `AGENTS.md` | `4695A045188F7AFBA8E4CFD551E63DA9BFEC6CE787A95471528FF7AF9ECED89E` | PASS |
| `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` | `373E092B51B84C4FE07BE9D9064E5E58D9C7BB2D6ACFE6A15426BAF9F8EAF723` | PASS |

Additional exact rollback copies were captured before mutation for the Bifrost upstream registry, project-router server/child launcher, current Bifrost/Context-Fabric runbooks, OpenRouter/recovery runbooks, and generated runtime inputs. Live `F:\AgentCore\runtime\bifrost\config.json`, `config\config.json`, and the online SQLite backup of `data\config.db` are under `live-bifrost\`; SQLite `PRAGMA integrity_check` returned `ok`.

## Live preflight evidence

| Check | Result |
| --- | --- |
| Bifrost scheduled owner | PASS — `\AgentCore\AgentCore-Bifrost-Gateway` running |
| Bifrost HTTP health | PASS — `status=ok` |
| Gateway discovery | PASS — 161 tools; 10 `agentcore_memory-*`; 4 `agentcore_project_router-*`; 3 `skills_hub-*` |
| Forbidden gateway patterns | PASS — no Swarm, raw PostgreSQL/PSQL, whole-drive, or Bifrost-admin tools |
| Cursor MCP baseline | PASS — one `agentcore-gateway`; no `MCP_DOCKER`; environment placeholder retained |
| AgentCore memory | PASS — `agentcore-memory` `0.7.0`, PG18 reachable, neutral Recall health 200 |
| Known memory degradation | Accurate — Cognee `degraded_unavailable` / `ModuleNotFoundError` |
| Device identity | Accurate — `legacy_compat`; writes require signed assertion per final Context Engine acceptance |
| Context Fabric initial gateway probe | FAIL — direct upstream was bound to Bifrost cwd (`project=bifrost`, `HEAD unknown`, zero components); service health alone was a false project-binding signal |
| Context Fabric repaired binding | PASS — router wrapper uses `F:\AgentCore\runtime` active-project state; `project_activate` returned `reconnected` for `context_fabric`; `cf_query` identifies `agentcore-control-plane` |
| Context Fabric local DB | PASS — schema 2, search index 2, integrity ok, hook installed/ready, latest successful capture `#122` at `da9f6ccd4e4b`; six historical failed-capture records retained |

## Inherited dirty state exclusion

The following pre-existing modified/untracked paths are not owned by this change and must not be staged: M6/M7/M8 acceptance summaries, `scripts/agentcore_workflow/requirements.txt`, Langfuse WIP, M5 restore-test outputs, the LangGraph start JSONL, `.agents/skills/`, `skills-lock.json`, and `agent-control-plane-md-files.zip`.

## Acceptance results

### Authority and architecture

- `BLUEPRINT.md`, `CONTEXT_BLOCK.md`, `DOC_AUTHORITY.md`, `MASTER_CONFIG_AND_PROMPT.md`, `MILESTONES.md`, `AGENTS.md`, the locked memory execution plan, the ADR, and current Bifrost/runbook paths now agree on:
  - AgentCore canonical truth/recovery;
  - Bifrost MCP aggregation/governance;
  - Context Engine rolling context;
  - neutral Recall semantic projection;
  - Context Fabric project-local committed-state/drift;
  - Arabold current official documentation;
  - LangGraph production autonomy;
  - Codex/authority-maintainer ownership with Cursor as a bounded specialist/reviewer.
- MCP and model-inference transport are explicitly separate. OmniRoute, Graphify, Hindsight, and CrewAI remain disabled, benchmark-gated candidates.

### Context Fabric runtime repair

- Root cause: `context-fabric` was marked project-scoped but rendered as direct STDIO, so the child inherited Bifrost's runtime cwd and ignored project-router activation.
- Contract fix: `connection_type=router` plus `scripts/project_router/wrappers/context-fabric.cmd`.
- Launcher fix: stale `H:\AgentRuntime` state/process/Tentra defaults replaced by environment-governed `F:\AgentCore\runtime`; filesystem wrapper roots are reduced to the active project.
- Activation fix: state writes are atomic and `project_activate` reconnects only enabled router-backed Bifrost clients through the documented management endpoint, returning explicit success/missing/failure evidence.
- TDD evidence: six focused unit tests pass, including preservation of the previous active project on a failed state write and fail-closed router-client reconnect on project clear.
- Framing evidence: wrapped Context Fabric `1.0.7` initialized, exposed exactly five tools, and all five had `outputSchema`.
- Rollout: generated config deployed; one scheduled-task recycle completed; gateway health recovered; builder surface remained 161 tools with exact 10 memory, 4 router, and at least 3 skills-hub tools.

### Arabold and Cursor subagents

- Retrieval-proven corpora: Context Fabric `1.0.7`, Cursor/subagents `3.14.7`, Hindsight/cookbook `0.7.0`, OmniRoute/RTK/compression `3.8.49`, Graphify `0.9.22`, and CrewAI `1.15.10`.
- Bifrost official documentation was refreshed; Arabold still reports it as unversioned. The installed binary pin remains `2.0.0-prerelease1`; no false documentation version was asserted.
- Seven project Cursor agents validate against the current official field set. Three new focused roles cover authority drift, Bifrost diagnosis, and MCP contract implementation; all inherit the parent model.
- CodeRabbit review was unavailable: its official CLI installer returned `Unsupported operating system: mingw64_nt-10.0-26200`. No manual result is represented as CodeRabbit output.

### Deterministic validation

| Check | Result |
| --- | --- |
| Project-router unit tests | PASS — 6/6 |
| Python compile | PASS |
| Authority lock | PASS |
| Cursor prompt format | PASS |
| Ecosystem separation | PASS |
| Bifrost contract validation | PASS |
| Bifrost contract/renderer suite | PASS — 124 checks |
| IDE rules renderer check | PASS |
| IDE enrollment scope | PASS |
| Runtime Bifrost status | PASS — task running, health ok, 161 tools |
| Context Fabric active-project reconnect | PASS |
| Exact staged secret/junk scan | PASS — 32 intended files, zero secret-pattern hits, zero junk/runtime artifact paths |

Repository-wide reconciliation scanning also identified 12 unchanged secret-like credential-backup files under the inherited `langsmith-projects/alerts-sheets/global files` tree. They are outside this task's stage set and were neither printed nor modified. Their remediation requires a separate security-scoped decision; the finding does not weaken the exact staged-patch result.

### Pending closeout evidence

- Independent fresh-context Cursor review after the scoped implementation commit.
- Post-commit Context Fabric capture/decision/drift/query/health evidence.
- Final scoped push and after-hash table.

## Rollback

Restore only a changed protected file from the matching file under the rollback root, rerun the complete validator set, create a separate rollback commit, and push under explicit operator approval.

For live rollback, restore `live-bifrost\config.json` and `live-bifrost\config-config.json` from the rollback root (or restore `live-bifrost\config.db` with Bifrost stopped), then restart only `\AgentCore\AgentCore-Bifrost-Gateway` through the governed scheduled task. Confirm `/health`, the 161-tool gateway baseline, and Context Fabric client state before reopening submissions. The database backup passed `PRAGMA integrity_check=ok`; no IDE config, database schema, credentials, or Swarm runtime require rollback.
