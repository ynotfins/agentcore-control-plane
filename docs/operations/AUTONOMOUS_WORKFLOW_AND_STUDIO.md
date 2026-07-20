# AgentCore Autonomous Workflow & LangGraph Studio Runbook

**Status:** READY — `python -m agentcore workflow {init,start,status,pause,approve,reject,resume,cancel,logs,evidence,topology,studio}` available. 17/17 E2E recovery scenarios PASS. Studio topology parity PASS. Production and Studio persistence are isolated.

**Authority:** `BLUEPRINT.md` M6 + `MEMORY_PLATFORM_EXECUTION_PLAN.md` M6 + `AGENTS.md` §Database Contract.

**See also:** `docs/operations/OPENROUTER_MCP.md` (JIT lease → VK bridge) · `audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md` · `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` · `CONTEXT_BLOCK.md` §0a

---

## 1. Folders

| Role | Path |
|---|---|
| Control plane (canonical repo) | `D:\github\agentcore-control-plane` |
| Operator CLI launcher | `scripts\agentcore\workflow_cli.py` |
| Studio adapter | `scripts\agentcore\studio.py` + `scripts\agentcore_workflow\studio\` |
| Workflow engine | `scripts\agentcore_workflow\` |
| Migration source | `migrations\m6\` (applied to PostgreSQL 18 at `127.0.0.1:55433`) |
| Studio acceptance runner | `scripts\agentcore\studio_accept.py` |
| E2E recovery suite | `scripts\agentcore_workflow\tests\fixture_e2e.py` |
| Fixture project (disposable) | `D:\agentcore-fixture\fixture-project` |
| Fixture bare remote | `D:\agentcore-fixture\fixture-remote.git` |
| Acceptance evidence | `audits\M6\` |

---

## 2. Environment variables (names only — never put values in source or docs)

| Variable | Required for | Default |
|---|---|---|
| `AGENT_CORE_POSTGRES_PASSWORD` | All production + E2E commands (PG18 superuser; not an agentcore_worker password) | _(User env var only)_ |
| `BIFROST_MCP_VIRTUAL_KEY` | Production + Studio MCP client (builder VK fallback) | _(User env var only)_ |
| `BIFROST_MCP_VK_WORKFLOW` | Optional dedicated workflow VK override | _(optional)_ |
| `BIFROST_ADMIN_KEY` | Automatic JIT lease → Bifrost VK bridge | _(User env var only)_ |
| `LANGSMITH_TRACING` | Studio only | `false` (forced by `studio.py`) |
| `LANGGRAPH_ANALYTICS` | Studio only | `false` (forced by `studio.py`) |
| `LANGGRAPH_HOST` | Studio only | `127.0.0.1` (forced by `studio.py`) |
| `LANGGRAPH_PORT` | Studio only | `2024` |
| `PYTHONIOENCODING` | PowerShell wrapper | `utf-8` (recommended) |

**Never** set `LANGSMITH_TRACING=true` for normal Studio runs. The `agentcore_workflow` graph is local-only by default and the `studio.py` launcher refuses to launch without `LANGSMITH_TRACING` defaulted to `false`.

There is **no** committed `.env` file. The repository has no Postgres connection strings in code, docs, or arguments. All secrets live as Windows User-scope environment variables (per `AGENTS.md` and `CLAUDE.md`).

---

## 3. Production launcher — operator commands

All commands run from `D:\github\agentcore-control-plane\` with the `scripts/` directory on `PYTHONPATH` (i.e. via `python -m agentcore`):

```powershell
# Initialise a target project (idempotent; one-time per repo)
python -m agentcore workflow init `
    --project-key fixture-project-a `
    --project-name "Fixture Project A" `
    --target-path D:\agentcore-fixture\fixture-project `
    --trust-class project_verified

# Start a workflow run; goal is either --goal "..." or --goal-file path
python -m agentcore workflow start `
    --project-key fixture-project-a `
    --milestone M6 `
    --goal "Diagnose the failing tests in calc.py and apply a minimal fix."

# Start a workflow run with OpenRouter explicit selection
# --provider openrouter requires an explicit --model from the OpenRouter model catalog.
python -m agentcore workflow start `
    --project-key fixture-project-a `
    --milestone M6 `
    --provider openrouter `
    --model minimax/minimax-m3 `
    --goal "Diagnose the failing tests in calc.py and apply a minimal fix."

# Display the sanitized available models catalog for OpenRouter
python -m agentcore workflow models --provider openrouter

# Observe state
python -m agentcore workflow status --project-key fixture-project-a

# Pause / approve / reject / resume / cancel — all reference the latest pending pause or active run
python -m agentcore workflow pause   --project-key fixture-project-a --reason "operator audit"
python -m agentcore workflow approve --project-key fixture-project-a --decision approve --notes "approved"
python -m agentcore workflow reject  --project-key fixture-project-a --decision reject   --notes "needs more"
python -m agentcore workflow resume  --project-key fixture-project-a
python -m agentcore workflow cancel  --project-key fixture-project-a --reason "abort"

# Logs / evidence / topology
python -m agentcore workflow logs     --project-key fixture-project-a --tail 50
python -m agentcore workflow evidence --project-key fixture-project-a --run <run_db_id>
python -m agentcore workflow topology  # shows prod + studio fingerprint + node list
```

JSON output is available via `--json`. Exit codes:
- `0` — success
- `2` — pre-flight / platform health failure
- `3` — runtime workflow error
- `4` — pause/decision conflict
- `5` — internal error (bug)

---

## 4. Lifecycle — goal → completion

1. **Operator invokes `workflow init`** with a project key + target path. The CLI:
   - validates platform health (Bifrost gateway reachable, PG18 reachable, M6 migrations applied);
   - inserts/upserts a row in `agentcore.projects` (`project_key`, `project_name`, `root_path`, `trust_class`);
   - registers the Git remote in `agentcore.repositories`;
   - creates an isolated Git worktree under `D:\github\<project_key>\wt\` if the `--worktree` flag is set (else uses the `root_path` directly).

2. **Operator invokes `workflow start`** with `--goal` (or `--goal-file`). The CLI:
   - opens a new thread (UUID) and inserts a `wf_runs` row + `wf_threads` row;
   - loads Project Charter, STATE, Milestones, checklists, and tool manifest;
   - opens an AgentCore memory session via `agentcore-memory`;
   - calls `agentcore_workflow.workflow.run_workflow(...)` against the **production** `PostgresSaver` (PG18, `public.checkpoints`);
   - returns the `thread_uuid` and `run_db_id`.

3. The graph executes against the registered project. It moves through:
   `start → gate_check → deterministic_checks → risk_assess → critics_and_score → judge_node → micro_execute | da_builder | human_pause | …`.

4. **Human pauses** surface as rows in `agentcore.wf_human_pauses`. The CLI surfaces them via `workflow status` and `workflow logs`. The operator uses `workflow approve` / `workflow reject` (or `resume` if not paused) to continue.

5. **Each successful micro-step** writes evidence rows to `agentcore.wf_evidence` through SECURITY DEFINER functions only.

6. **On terminal completion**, the CLI:
   - regenerates the project `STATE.md`, `DECISIONS.md`, `CONTEXT_INDEX.md` projections;
   - commits and pushes per `docs/GIT_PUSH_ONLY_POLICY.md` when the project policy allows;
   - closes the memory session;
   - prints a deterministic handoff JSON.

---

## 5. Pause / approve / resume / cancel

- `workflow pause` — sets the active run status to `paused` (preserves checkpoints). Idempotent.
- `workflow approve --decision approve --notes "..."` — resolves the most-recent pending pause as `approved` and queues a resume; the thread continues from the saved checkpoint.
- `workflow approve --decision reject --notes "..."` — resolves the pause as `rejected`; the run routes to `workflow_fail` and evidence is preserved.
- `workflow resume` — re-executes the thread from the latest checkpoint in PG18 (`public.checkpoints`). Safe to run after a process kill: no completed node is repeated, evidence is idempotent.
- `workflow cancel` — sets the run to `aborted` (the `wf_run_status` enum), resolves any pending pause as `cancelled`, preserves evidence. The thread is closed but checkpoints remain.

---

## 6. Restart recovery

The production runner is crash-safe by design. To verify after a kill:

```powershell
# Status reports thread, run, milestone, current node, checkpoint, blockers
python -m agentcore workflow status --project-key <project_key>

# Resume (no args needed; uses the most-recent run for the project)
python -m agentcore workflow resume  --project-key <project_key>
```

The runner reads the canonical thread UUID from `public.checkpoints` and continues execution. The 17/17 E2E suite (`scripts\agentcore_workflow\tests\fixture_e2e.py`) explicitly covers this in scenarios `03-kill_resume_partial` and `03-kill_resume`.

---

## 7. Logs / evidence locations

| Artefact | Path |
|---|---|
| Per-run logs (CLI output, captured to disk) | `audits\M6\<run_db_id>.log` (when `--log-file` is set) |
| Workflow evidence rows (canonical) | `agentcore.wf_evidence` (PG18) |
| Workflow abort / fail reasons | `agentcore.wf_run_status` enum + `agentcore.wf_human_pauses.resolution` |
| Acceptance summary | `audits\M6\fixture-e2e-summary.json` |
| Studio acceptance | `audits\M6\studio-acceptance.json` |
| LangGraph CLI dev log | `audits\M6\studio-dev.log` (when `studio` is run with `--log-file`) |

---

## 8. PostgreSQL checkpoint location

| Surface | Database / Schema / Table |
|---|---|
| **Production** checkpoints | PG18 `127.0.0.1:55433` → `agent_core` DB → `public.checkpoints`, `public.checkpoint_blobs`, `public.checkpoint_writes` (created by `PostgresSaver.setup()`) |
| **Studio** checkpoints | Agent Server dev checkpointer (sqlite/in-memory managed by `langgraph dev`); **separate** from production. |
| Project / thread / run registry | `agentcore.projects`, `agentcore.wf_runs`, `agentcore.wf_threads` |
| Workflow evidence | `agentcore.wf_evidence`, `agentcore.wf_gate_evals`, `agentcore.wf_critic_runs` |
| Human pauses | `agentcore.wf_human_pauses` |
| Capability leases | `agentcore.capability_leases`, `agentcore.capability_profiles` |

The production PostgresSaver and Studio dev checkpointer **never share a thread id**. E2E scenario `studio_sees_production_thread_status = 404` confirms this isolation.

---

## 9. LangGraph Studio start / stop

### Start

```powershell
cd D:\github\agentcore-control-plane
python -m agentcore workflow studio --port 8124 --no-browser
```

Output reports:
- local API URL: `http://127.0.0.1:8124`
- Studio connection hint: open https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:8124
- topology fingerprint (must match production `topology_fingerprint`)
- `LANGSMITH_TRACING=false`, `LANGGRAPH_ANALYTICS=false`, `LANGGRAPH_HOST=127.0.0.1`

### Stop

`Ctrl+C` in the terminal window. There is **no** persistent Windows service for Studio.

### One-shot acceptance

```powershell
python -m agentcore.studio_accept --port 8124
```

Writes `audits\M6\studio-acceptance.json` with `health_ok`, `assistant_id`, `thread_id`, `topology_fingerprint`, `tracing`, `host`.

---

## 10. Studio vs production persistence

| Aspect | Production (`python -m agentcore workflow ...`) | Studio (`langgraph dev`) |
|---|---|---|
| Checkpointer | `PostgresSaver` against `public.checkpoints` | Agent Server dev checkpointer (sqlite/in-memory) |
| Database | PG18 `127.0.0.1:55433`, `agent_core` | none / sqlite file in `.langgraph_api` |
| Project / run registry | `agentcore.wf_*` tables | none |
| Topology | `agentcore_workflow.workflow.build_topology()` | same module, same function |
| Topology fingerprint | `topology_fingerprint(build_topology())` | identical (deterministic SHA256) |
| Thread id format | UUID | UUID (separate namespace) |
| Resume after kill | yes, via `public.checkpoints` | yes, via dev checkpointer (sqlite) |
| Tracing to LangSmith | off by default, never enabled in production runs | off by default; operator may set `LANGSMITH_TRACING=true` (NOT recommended — would leak project data) |
| Localhost bind | N/A (CLI) | forced `127.0.0.1` |

**Do not run Studio against a real operator project for destructive testing.** Use the disposable fixture at `D:\agentcore-fixture\fixture-project`.

---

## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `langgraph dev` exits immediately with `ModuleNotFoundError: No module named 'agentcore_workflow'` | `scripts/` not installed editable | `pip install -e D:\github\agentcore-control-plane\scripts` |
| `langgraph dev` exits with `Required package 'langgraph-api' is not installed` | `langgraph-cli[inmem]` extra missing | `pip install -U "langgraph-cli[inmem]==0.4.29"` |
| Studio server boot reaches "Shutting down remote graphs" | graph import failed | check `audits\M6\studio-dev.log`; `agentcore_workflow` must be importable |
| `workflow status` reports `run_db_id` but no checkpoint | run was started in `--no-checkpointer` mode (Studio) | run via `python -m agentcore workflow start` (production) |
| `workflow approve` returns exit 4 | pause already resolved by a parallel process | re-run `workflow status` to see latest pause; do not retry the same pause |
| `workflow cancel` returns "no active run" | run already `aborted` or `completed` | idempotent; check `wf_run_status` row |
| E2E fails with `relation "agentcore.wf_*" does not exist` | M6 migrations not applied | re-run `psql -h 127.0.0.1 -p 55433 -U postgres -d agent_core -f migrations\m6\*.sql` |
| Studio thread UUID not visible to production | intentional; namespaces are separate | use the production thread UUID for production runs, a separate Studio UUID for Studio runs |

---

## 12. Rollback

| Surface | Rollback action |
|---|---|
| Production workflow CLI | revert commits touching `scripts\agentcore\workflow_cli.py` and `scripts\agentcore_workflow\`; restart gateway; do not migrate schema down on a populated DB |
| Studio adapter | revert commits touching `scripts\agentcore\studio.py`, `scripts\agentcore_workflow\studio\*`, and `scripts\pyproject.toml`; remove editable install with `pip uninstall agentcore_workflow` |
| Schema (M6) | only run the DOWN migrations from `migrations\m6\down_*.sql` against a verified-empty namespace; otherwise preserve historical runs and create a forward-only patch |
| Topology fingerprint drift | revert the change that touched `agentcore_workflow\workflow.py` (`NODE_ORDER`, `_AFTER_*`, `interrupt_before`); topology changes are a locked architecture decision and require explicit AGENTS.md revision |

---

## 13. Security and Swarm boundaries

- **No** `.env` file is committed. All secrets live as Windows User-scope environment variables.
- **No** PostgreSQL credentials appear in command arguments, documentation, logs, or Git history.
- **No** AgentCore application data is sent to LangSmith. `LANGSMITH_TRACING` is `false` by default in both production and Studio.
- **No** Docker / WSL is required for either production or Studio.
- **No** persistent Studio Windows service is created.
- The **Swarm** ecosystem (SwarmRecall, SwarmVault, SwarmClaw) is **separate** and **untouched** by this work. The Studio adapter and the production launcher do not import, depend on, or call any Swarm component.
- Bifrost gateway contract and the exact ten `agentcore-memory` tools are **unchanged**. Verified by E2E scenario `19-bifrost_memory_unchanged`.

---

## 14. Cross-references

- `AGENTS.md` — agent contract, Git policy, Swarm boundary
- `PROJECT_ANCHOR.md` — runtime endpoints, drive roles
- `BLUEPRINT.md` — locked M6 architecture
- `MASTER_CONFIG_AND_PROMPT.md` — Bifrost gateway + ten-tool memory surface
- `docs\AGENTCORE_AUTOMATION_OPERATIONS.md` — broader automation ops
- `docs\handoffs\AGENTCORE_BIFROST_GATEWAY_HANDOFF_2026-07-12.md` — gateway handoff
- `scripts\agentcore_workflow\README.md` — workflow package docs
- `scripts\agentcore_workflow\studio\README.md` — Studio adapter docs
- `audits\M6\fixture-e2e-summary.json` — 17/17 E2E result
- `audits\M6\studio-acceptance.json` — Studio acceptance result
- `audits\M6\m6-acceptance-summary.json` — M6 acceptance summary
