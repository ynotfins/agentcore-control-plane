# AgentCore Autonomous Workflow & LangGraph Studio Runbook

**Status:** READY — `python -m agentcore workflow {init,start,status,pause,approve,reject,resume,cancel,logs,evidence,topology,studio}` from `D:\github\agentcore-control-plane`. Fixture E2E **17/17 PASS**. Topology fingerprint `a86e40e8ddd0a370…`. Production and Studio persistence are isolated.

**Authority:** `BLUEPRINT.md` M6 + `MEMORY_PLATFORM_EXECUTION_PLAN.md` M6 + `AGENTS.md`.

**Quickstart:** `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md`  
**See also:** `docs/operations/OPENROUTER_MCP.md` · `audits/LANGGRAPH_GATEWAY_ENROLLMENT_2026-07-20.md` · `audits/LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md` · `audits/LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json`

---

## 1. Folders

| Role | Path |
|---|---|
| Control plane (canonical; run all commands here) | `D:\github\agentcore-control-plane` |
| Operator CLI | `scripts\agentcore\workflow_cli.py` |
| Studio adapter | `scripts\agentcore\studio.py` + `scripts\agentcore_workflow\studio\` |
| Workflow engine | `scripts\agentcore_workflow\` |
| Migrations | `migrations\m6\` → PG18 `127.0.0.1:55433` |
| E2E suite | `scripts\agentcore_workflow\tests\fixture_e2e.py` |
| Fixture project | `D:\agentcore-fixture\fixture-project` |
| Evidence | `audits\M6\` |

Do **not** run production workflow commands from `D:\github\deepagents`. Deep Agents is a PyPI worker pin only (`deepagents==0.6.12`).

---

## 2. Environment variables (names only)

| Variable | Required for | Default / posture |
|---|---|---|
| `AGENT_CORE_POSTGRES_PASSWORD` | Production + E2E (PG18) | User env only |
| `BIFROST_MCP_VIRTUAL_KEY` | MCP client (builder VK fallback) | User env only |
| `BIFROST_MCP_VK_WORKFLOW` | Optional workflow VK override | optional |
| `BIFROST_ADMIN_KEY` | JIT lease → Bifrost VK bridge | User env only |
| `LANGSMITH_TRACING` | Studio | forced `false` by `studio.py` |
| `LANGGRAPH_CLI_NO_ANALYTICS` | Studio | forced `1` by `studio.py` |
| `LANGGRAPH_ANALYTICS` | Studio (legacy alias) | forced `false` |
| `LANGGRAPH_HOST` | Studio | forced `127.0.0.1` |
| `LANGGRAPH_PORT` | Studio | `2024` (abort on collision) |
| `LANGSMITH_API_KEY` | Hosted Studio browser auth only | optional; missing ≠ stop |

No committed `.env`. Never print secret values. Never paste `LANGSMITH_API_KEY` into chat.

---

## 3. Production launcher

From `D:\github\agentcore-control-plane` (via `python -m agentcore`):

```powershell
cd D:\github\agentcore-control-plane

python -m agentcore workflow init `
  --project-key fixture-project-a `
  --project-name "Fixture Project A" `
  --target-path D:\agentcore-fixture\fixture-project `
  --trust-class project_verified

python -m agentcore workflow start `
  --project-key fixture-project-a `
  --milestone M6 `
  --goal "Diagnose the failing tests in calc.py and apply a minimal fix."

python -m agentcore workflow status  --project-key fixture-project-a
python -m agentcore workflow pause   --project-key fixture-project-a --reason "operator audit"
python -m agentcore workflow approve --project-key fixture-project-a --decision approve --notes "approved"
python -m agentcore workflow reject  --project-key fixture-project-a --decision reject   --notes "needs more"
python -m agentcore workflow resume  --project-key fixture-project-a
python -m agentcore workflow cancel  --project-key fixture-project-a --reason "abort"
python -m agentcore workflow logs     --project-key fixture-project-a --tail 50
python -m agentcore workflow evidence --project-key fixture-project-a --run <run_db_id>
python -m agentcore workflow topology
```

Exit codes: `0` ok · `2` pre-flight · `3` runtime · `4` pause conflict · `5` internal.

---

## 4. Lifecycle (goal → completion)

1. `workflow init` — platform health, project/repo rows, optional worktree.
2. `workflow start` — thread + `wf_runs` / `wf_threads`, memory session, production `PostgresSaver` (PG18 `public.checkpoints`).
3. Graph: `start → gate_check → deterministic_checks → risk_assess → critics_and_score → judge_node → micro_execute | da_builder | human_pause | …`.
4. Human pauses → `wf_human_pauses`; resolve via `approve` / `reject` / `resume`.
5. Evidence → `wf_evidence` (SECURITY DEFINER only).
6. Terminal → projections, optional push per Git policy, memory session close.

---

## 5. Pause / approve / resume / cancel

| Command | Effect |
|---|---|
| `pause` | Active run → `paused`; checkpoints kept |
| `approve --decision approve` | Resolve pending pause; resume from checkpoint |
| `approve --decision reject` / `reject` | Pause → rejected; route toward fail; evidence kept |
| `resume` | Continue from latest PG18 checkpoint (safe after kill) |
| `cancel` | Run → `aborted`; pending pause cancelled; evidence kept |

---

## 6. Restart recovery

```powershell
python -m agentcore workflow status --project-key <project_key>
python -m agentcore workflow resume  --project-key <project_key>
```

Covered by fixture scenarios `03-kill_resume_partial` and `03-kill_resume` (17/17 suite).

---

## 7. Logs / evidence

| Artefact | Location |
|---|---|
| CLI logs | `audits\M6\` when `--log-file` set |
| Evidence rows | `agentcore.wf_evidence` |
| E2E summary | `audits\M6\fixture-e2e-summary.json` |
| Studio launch | `audits\M6\studio-launch-stdout.log` |
| Studio interrupt accept | `audits\M6\studio-interrupt-accept.json` |

---

## 8. PostgreSQL vs Studio checkpointers

| Surface | Persistence |
|---|---|
| **Production** | PG18 `127.0.0.1:55433` / `agent_core` / `public.checkpoints` (+ blobs/writes) via `PostgresSaver` |
| **Studio** | Agent Server **dev** checkpointer (sqlite/in-memory). **Not** production PostgresSaver |
| Registry / evidence | `agentcore.wf_*`, leases, pauses — production only |

Production and Studio **never share thread IDs**. Isolation proven (`studio_sees_production_thread_status = 404`).

Topology fingerprint (prod = studio):

```text
a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32
```

---

## 9. LangGraph Studio (Option A)

### Posture

- Default port **2024** on `127.0.0.1` only; abort on collision (no silent rebind).
- Force `LANGSMITH_TRACING=false` and `LANGGRAPH_CLI_NO_ANALYTICS=1` (refuse launch if tracing already truthy unless `--allow-dangerous-langsmith-tracing`).
- **Anonymous / local Studio first.** Missing `LANGSMITH_API_KEY` is **not** a global stop.
- If the hosted Studio browser requires auth, emit gate `LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED` and ask the operator to set User-scope env var **name** `LANGSMITH_API_KEY` only (never print the value).
- Complete non-browser work first (`--no-browser`).
- No persistent Windows service. Stop with Ctrl+C.

### Start / stop

```powershell
cd D:\github\agentcore-control-plane
python -m agentcore workflow studio --port 2024 --no-browser
# Ctrl+C to stop
```

URLs (sanitized):

- Local API: `http://127.0.0.1:2024`
- Docs: `http://127.0.0.1:2024/docs`
- Hosted Studio: `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`

### Chrome 142+ Private Network Access

If `http://127.0.0.1:2024/docs` returns **200** but hosted Studio cannot fetch the local Agent Server: open site info for `https://smith.langchain.com` and allow **Local network access**. Do **not** bind LAN or open a tunnel as the first fix.

### Live acceptance (2026-07-21/22)

See `audits/LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md`: local `/docs` 200, tracing false, `/info` `langsmith: false`, browser credential gate pending when key absent, PNA diagnostic documented.

---

## 10. Studio vs production

| Aspect | Production | Studio |
|---|---|---|
| Checkpointer | `PostgresSaver` → `public.checkpoints` | Agent Server dev (sqlite/memory) |
| Bind | N/A (CLI) | `127.0.0.1:2024` |
| Topology module | `build_topology()` | same |
| Fingerprint | `a86e40e8…` | must match (parity abort) |
| Tracing | off | forced off |
| Analytics | N/A | `LANGGRAPH_CLI_NO_ANALYTICS=1` |

Use the disposable fixture for Studio destructive tests — not a live operator project.

---

## 11. Troubleshooting

| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: agentcore_workflow` | `pip install -e D:\github\agentcore-control-plane\scripts` |
| Missing `langgraph-api` | `pip install -U "langgraph-cli[inmem]==0.4.29"` |
| Port 2024 in use | Stop the other listener or choose another free port explicitly |
| Hosted Studio blank; `/docs` OK | Chrome PNA → allow Local network access on smith.langchain.com |
| Browser asks for LangSmith auth | Gate `LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED` — set User env name `LANGSMITH_API_KEY` (value never in chat) |
| Exit 4 on approve | Pause already resolved; re-check `status` |
| Studio thread invisible to production | Intentional namespace isolation |

---

## 12. Rollback

| Surface | Action |
|---|---|
| Production CLI / engine | Revert `workflow_cli.py` / `agentcore_workflow/`; do not DOWN-migrate populated DB |
| Studio adapter | Revert `studio.py` + `studio/`; uninstall editable if needed |
| Fingerprint drift | Revert topology changes in `workflow.py`; fingerprint is locked architecture |

---

## 13. Security / Swarm

- No `.env`; no Postgres credentials in docs/args/logs.
- No AgentCore data to LangSmith by default (`LANGSMITH_TRACING=false`).
- SwarmRecall / SwarmVault / SwarmClaw untouched.
- Ten-tool `agentcore-memory` surface unchanged (E2E `19-bifrost_memory_unchanged`).

---

## 14. Cross-references

- Quickstart: `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md`
- ADR: `docs/decisions/ADR-DEEP-AGENTS-WORKER-HARNESS.md`
- Audits: `audits/LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md`, `audits/LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json`, `audits/DEEP_AGENTS_WORKER_ACCEPTANCE_2026-07-21.md`, `audits/MEMORY_GATEWAY_HEALTH_2026-07-22.md`
- Memory health: `audits/MEMORY_GATEWAY_HEALTH_2026-07-22.md`
