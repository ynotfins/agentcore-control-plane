# AgentCore Bifrost and Context Alignment Acceptance — 2026-08-02

**Approval:** `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`
**Capability:** `authority_maintainer`
**Status:** REMEDIATED — FINAL INDEPENDENT REVIEW PENDING
**Scope:** Authority/current-state reconciliation, Arabold official-doc indexing, Context Fabric committed-state baseline, and project-owned Cursor subagents
**Explicit exclusions:** No OmniRoute, Hindsight, Graphify, CrewAI, new MCP-upstream, inference-route, Swarm-runtime, database, credential, or live IDE configuration change. Live gateway changes are limited to the governed project-isolation remediation and profile correction described below.

## Preflight

- Repository: `D:\github\agentcore-control-plane`
- Branch: `main`
- Before HEAD: `da9f6ccd4e4b9f646f213a4faecf95ba1586a75c`
- Rollback root: `E:\AgentCore-Backups\agentcore-control-plane\context-alignment-20260802-232010`
- Pre-remediation live Bifrost rollback root: `E:\AgentCore-Backups\agentcore-control-plane\project-isolation-20260803-003135`
- Cursor/runtime-path remediation rollback root: `E:\AgentCore-Backups\agentcore-control-plane\cursor-runtime-path-20260803-0045`
- Project-enrollment/final-review remediation rollback root: `E:\AgentCore-Backups\agentcore-control-plane\project-enrollment-review-20260803-0145`
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
| Original builder discovery | REJECTED — 161 tools exposed shared implicit-project upstreams and four machine-global router controls |
| Forbidden gateway patterns | PASS — no Swarm, raw PostgreSQL/PSQL, whole-drive, or Bifrost-admin tools |
| Cursor MCP baseline | PASS — one `agentcore-gateway`; no `MCP_DOCKER`; environment placeholder retained |
| AgentCore memory | PASS — `agentcore-memory` `0.7.0`, PG18 reachable, neutral Recall health 200 |
| Known memory degradation | Accurate — Cognee `degraded_unavailable` / `ModuleNotFoundError` |
| Device identity | Accurate — `legacy_compat`; writes require signed assertion per final Context Engine acceptance |
| Context Fabric initial gateway probe | FAIL — direct upstream was bound to Bifrost cwd (`project=bifrost`, `HEAD unknown`, zero components); service health alone was a false project-binding signal |
| Context Fabric first repair | REJECTED — the router wrapper corrected cwd but one machine-global active-project state still could not isolate concurrent IDE sessions |
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

### Independent review failure and verified remediation

The first scoped implementation commit was `97c872cd98e887292e47b2574fcf236e4872fdde`. A fresh Cursor GPT-5.6 Sol review (`bc-fb3fe422-8f8b-4544-aa27-66ff1a5acce8`) returned **FAIL**. Each material finding was reproduced against source before remediation:

1. `project_activate` changed machine-global state before reconnect, while a failed reconnect could be nested under top-level success. The old shared STDIO child could remain bound to the previous project.
2. `filesystem` was described as project-scoped but launched directly with write access rooted at `D:\github`.
3. Non-operator profiles received machine-global project activation/clear controls.
4. The memory plan retained one stale `H:` artifact-spool path.
5. The child launcher rewrote shared process-registry JSON per byte without a cross-process lock.
6. Source renderers could retain a runtime `oauth_config_id`; the recovery runbook still described Stage A.

The corrected security model does not treat one Bifrost process-global project selection as a concurrent-session boundary:

- `serena`, `depwire`, `tentra`, `filesystem`, and `context-fabric` are dormant in shared Bifrost profiles because their tool calls lack trustworthy explicit caller/project identity.
- Context Fabric remains repo-local through its Git hook/CLI; filesystem/source work uses native IDE tools; Depwire/Tentra use explicit-cwd local launches; Serena remains catalogued for an explicit project-owned process.
- `agentcore-project-router` is operator-only maintenance. Ordinary profiles expose zero router controls.
- `project_activate` and `project_clear` now preserve/restore prior state and return top-level failure if required reconnect fails.
- The child registry uses atomic replacement plus a cross-process lock and updates only at lifecycle boundaries, with 64 KiB proxy chunks rather than per-byte writes.
- The stale spool path, committed runtime OAuth identifier, and Stage A runbook text were corrected.

TDD red evidence preceded implementation. The corrected focused suite passes 10/10 router/security tests and the Bifrost contract/renderer suite passes 129 checks.

A second fresh review of `01434d8f61dae057053e6198fa3baa68873108c9` (`bc-dcd759ab-79c7-4b91-bf9e-f0a04a5087dd`) also returned **FAIL** and exposed five additional end-to-end inconsistencies:

1. `swarm-ecosystem-control` was not an explicit rejection marker in the operator router/child launcher.
2. Cursor Stage B still called `project_list`/`project_activate` while the builder profile correctly exposed zero router tools.
3. Active Cursor spool/log/pointer defaults and the write allowlist still referenced `H:\AgentRuntime`.
4. `BufferedReader.read(64 KiB)` could wait for a full buffer or EOF and stall small MCP frames.
5. `contracts/global-agent-policy.yaml`, generated IDE rules, the new-project bootstrap, and Cursor staging policy still mandated the rejected shared-project model.

All five were reproduced before repair. The follow-up implementation:

- rejects `swarm-ecosystem-control` in both router layers;
- derives Cursor memory identity from the validated workspace root and sends the explicit project/root/worktree tuple without router calls;
- moves active Cursor defaults and runtime write allowance to environment-governed `F:\AgentCore\runtime`;
- uses `os.read(..., 64 KiB)` so a small available MCP message returns immediately, with a real open-pipe regression test;
- updates the canonical policy/new-project bootstrap/Cursor staging rule and regenerates all 27 IDE rule artifacts.

TDD proof now passes 12/12 router/security tests and 133 Bifrost contract/renderer checks. The complete Stage B suite passes 26/26 with `AGENTCORE_WORKER_MODE=deterministic`; without that explicit fixture setting, the embedded live LangGraph worker exceeded its independent 120-second test timeout. The hook protocol harness passes all event fixtures and special cases.

A third fresh review of `9ceab4e9aefe3a4785020e3bcd6d92264cc71dc5`
(`bc-41bbc2cb-fab6-4cd9-ac44-0be69db8882f`) correctly returned **FAIL**.
It proved that Cursor bootstrap and `agentcore-memory` could still create an
arbitrary/Swarm project because the boundary was deny-by-name rather than
positive enrollment. It also found incomplete renamed/relocated Swarm defense,
cross-process-unsafe router state writes, misleading Stage B assertions, and
current documentation conflicts around the dormant router/Tentra/Serena routes,
Context Fabric CRLF drift, and the retired H: Bifrost path.

The final remediation replaces directory discovery with one default-deny source
contract, `contracts/agentcore-project-enrollment.json`. Cursor bootstrap,
`agentcore-memory`, the operator router, and its child launcher all consume the
same exact project-key/path enrollment. This enforcement covers every project-key
read/write plus opaque session, event, artifact, and summary references—not only
`session_open`. `docs_search` now requires a project key. Boundary refusal performs
no write inside the rejected workspace. Router state writes use unique temporary
files plus thread and cross-process locks. Current policies/runbooks and all nine
generated IDE rule projections now agree that ordinary IDEs expose zero router
controls and use exact enrolled identity.

The live pre-rollout database contains one historical `swarm-ecosystem-control`
project row and one empty session created while the prior defect existed: zero
evidence events, artifacts, summaries, or fact proposals. It is not deleted in
this task; v0.8.0 makes it unreachable through every ordinary project/session/
reference tool path. Destructive cleanup remains a separately approved database
maintenance action and is not required to prove zero persisted Swarm context.

### Corrected live rollout

- The live Bifrost config and online SQLite database were backed up under `E:\AgentCore-Backups\agentcore-control-plane\project-isolation-20260803-003135`; `PRAGMA integrity_check=ok`.
- The generated runtime configuration now enables eight upstream clients and keeps all five implicit-project clients dormant.
- One governed scheduled-task recycle completed and `/health` recovered.
- Authenticated builder proof: 57 total tools; exact 10 memory; zero router; at least 3 skills-hub.
- Authenticated operator proof: 24 total tools; exact 10 memory; exact 4 router; zero skills-hub required.
- No IDE MCP entry changed; `agentcore-gateway` remains the sole front door.

### Arabold and Cursor subagents

- Retrieval-proven corpora: Context Fabric `1.0.7`, Cursor/subagents `3.14.7`, Hindsight/cookbook `0.7.0`, OmniRoute/RTK/compression `3.8.49`, Graphify `0.9.22`, and CrewAI `1.15.10`.
- Bifrost official documentation was refreshed; Arabold still reports it as unversioned. The installed binary pin remains `2.0.0-prerelease1`; no false documentation version was asserted.
- Seven project Cursor agents validate against the current official field set. Three new focused roles cover authority drift, Bifrost diagnosis, and MCP contract implementation; all inherit the parent model.
- CodeRabbit review was unavailable: its official CLI installer returned `Unsupported operating system: mingw64_nt-10.0-26200`. No manual result is represented as CodeRabbit output.

### Deterministic validation

| Check | Result |
| --- | --- |
| Project-router unit tests | PASS — 14/14, including default-deny enrollment, concurrent state writes, cross-platform paths, and small open-pipe proxy delivery |
| Project-boundary tests | PASS — Cursor 2/2; memory 30/30; renamed/unregistered paths and mismatched identities refused |
| Python compile | PASS |
| Authority lock | PASS |
| Cursor prompt format | PASS |
| Ecosystem separation | PASS |
| Bifrost contract validation | PASS |
| Bifrost contract/renderer suite | PASS — 136 checks |
| Cursor Stage B comprehensive suite | PASS — 26/26 with deterministic LangGraph fixture and real 100-iteration hook run |
| Cursor hook protocol harness | PASS — all seven event fixtures plus special cases |
| IDE rules renderer check | PASS |
| IDE enrollment scope | PASS |
| Runtime Bifrost builder status | PASS — task running, health ok, 57 tools, memory 10, router 0, skills-hub >=3 |
| Runtime Bifrost operator status | PASS — task running, health ok, 24 tools, memory 10, router 4 |
| Exact staged secret/junk scan | PASS — 38 intended files, zero secret-pattern hits, zero junk/runtime artifact paths |

Repository-wide reconciliation scanning also identified 12 unchanged secret-like credential-backup files under the inherited `langsmith-projects/alerts-sheets/global files` tree. They are outside this task's stage set and were neither printed nor modified. Their remediation requires a separate security-scoped decision; the finding does not weaken the exact staged-patch result.

### Context Fabric Windows drift residual

- Post-commit capture `#123` is healthy at `97c872cd98e8`, with DB integrity `ok`, no degraded mode, and zero pending captures.
- The raw `cf_drift` result remains `HIGH` (`709/820`, 86.5%) and must not be treated as an accurate Windows change count.
- Read-only hash classification proved that 683 of the 709 mismatches equal the stored Git-blob SHA-256 after CRLF-to-LF normalization. The remaining 26 are 15 inherited dirty task-external paths and 11 historical missing paths, an actionable upper bound of 3.2% before missing-path reconciliation.
- Cause is confirmed in the installed and [current upstream Context Fabric `1.0.7` source](https://github.com/VIKAS9793/context-fabric/blob/main/src/engines/anchor.ts): capture hashes Git blob bytes while `anchor.ts` hashes raw working-tree bytes. This conflicts with this Windows checkout's documented `core.autocrlf=true` behavior.
- Classification: `MEDIUM` dependency residual. Capture, query, decision logging, search, project identity, DB integrity, and hook readiness remain usable; the raw drift severity alone is not accepted as an operational gate on Windows.
- Smallest safe follow-up: upstream or forked Context Fabric must compare working-tree content through Git clean filters/object identity and reconcile historical tombstones. Do not rewrite this repository or globally change line-ending policy merely to silence the metric.
- Repo-local capture `#124` records remediation commit `01434d8f61dae057053e6198fa3baa68873108c9`; doctor reports schema/search-index 2, database integrity `ok`, hook installed/ready, zero pending captures, and six retained historical failures.
- A repo-local `cf_log_decision` call appended **Keep implicit-project tools out of shared Bifrost profiles**, explicitly superseding the earlier project-router decision. A bounded local query returns the superseding decision first and identifies `01434d8` as latest captured Git state.

### Pending closeout evidence

- Independent fresh-context Cursor review of the final remediation commit (the `01434d8` review correctly failed and its findings are repaired locally).
- Final accepted-HEAD repo-local Context Fabric capture/drift/query/health evidence.
- Final scoped push and after-hash table.

### Protected-file after hashes (pre-commit content)

| File | SHA-256 after remediation |
| --- | --- |
| `BLUEPRINT.md` | `63A57B6FAFF4050528005A2DFEF6621925D553500A4FAB89519AAD7335AC69C0` |
| `CONTEXT_BLOCK.md` | `2D12B792E72D97AD0F505ED97961F310FA01B825BCC48C6755F1D593451AEB68` |
| `DOC_AUTHORITY.md` | `94C50E90DCF09EF10AE618448E4B60D0995DF1BC3BFE2CFF7924C96E6265A5EE` |
| `MASTER_CONFIG_AND_PROMPT.md` | `B924C278397E98EA51D1AC01C9B87C14602F8B6083C8D30DA40DE6C13B76AD0E` |
| `AGENTS.md` | `22CCEF76B879935D04DBB7E8BB9B5C6A607608ABCD3F86CC63975B484CDFC57D` |
| `docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md` | `843FD76081120B3A297F519727F298E8FAF97E63E0DB8A7B14F7FDFBCF234BE8` |

## Rollback

Restore only a changed protected file from the matching file under the rollback root, rerun the complete validator set, create a separate rollback commit, and push under explicit operator approval.

For live rollback, restore `config.json` and `config-config.json` from `E:\AgentCore-Backups\agentcore-control-plane\project-isolation-20260803-003135` (or restore `config.db` with Bifrost stopped), then restart only `\AgentCore\AgentCore-Bifrost-Gateway` through the governed scheduled task. Confirm `/health` and the intended authenticated profile counts before reopening submissions. The database backup passed `PRAGMA integrity_check=ok`; no IDE config, database schema, credentials, or Swarm runtime require rollback.
