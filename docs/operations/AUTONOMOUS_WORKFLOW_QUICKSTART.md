# Autonomous Workflow Quickstart

**Run from:** `D:\github\agentcore-control-plane\scripts` (operator cwd).  
**Not from:** repo root alone (`ModuleNotFoundError: No module named 'agentcore'`) or `D:\github\deepagents` (upstream Deep Agents checkout is not the operator CLI).

**Full runbook:** `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`

---

## Cursor Auto context posture

When the IDE routes via Cursor Auto (model not reliably observable), use AgentCore **`standard-context`** (conservative model-limit-aware ceiling). Durable history remains unbounded in PostgreSQL; only the active request budget is bounded. Do not invent a larger profile to “fit more” without an explicit operator decision.

---

## Exact commands

```powershell
cd D:\github\agentcore-control-plane\scripts

# If bare `python` is missing from PATH:
# $py = "C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe"

# One-time project registration
python -m agentcore workflow init `
  --project-key <project_key> `
  --project-name "<name>" `
  --target-path <repo_root> `
  --trust-class project_verified

# Start
python -m agentcore workflow start `
  --project-key <project_key> `
  --milestone M6 `
  --goal "<goal text>"

# Observe (production evidence)
python -m agentcore workflow status  --project-key <project_key>
python -m agentcore workflow logs    --project-key <project_key> --tail 50
python -m agentcore workflow topology

# Control
python -m agentcore workflow pause   --project-key <project_key> --reason "<why>"
python -m agentcore workflow approve --project-key <project_key> --decision approve --notes "<notes>"
python -m agentcore workflow reject  --project-key <project_key> --decision reject   --notes "<notes>"
python -m agentcore workflow resume  --project-key <project_key>
python -m agentcore workflow cancel  --project-key <project_key> --reason "<why>"

# Evidence
python -m agentcore workflow evidence --project-key <project_key> --run <run_db_id>

# Studio (dev-only Agent Server; NOT production PostgresSaver; cannot open production thread IDs)
python -m agentcore workflow studio --port 2024 --no-browser
```

**Repo-root alternative:** from `D:\github\agentcore-control-plane`, set `$env:PYTHONPATH = "D:\github\agentcore-control-plane\scripts"` then run the same commands. Prefer `cd …\scripts`.

Studio defaults: `127.0.0.1:2024`, `LANGSMITH_TRACING=false`, `LANGGRAPH_CLI_NO_ANALYTICS=1`, anonymous/local first. Topology fingerprint must be `a86e40e8ddd0a370…`.

---

## Production vs Studio (where to look)

| Question | Use |
|---|---|
| Run status, checkpoint summary, blockers | `workflow status` (production CLI) |
| Operator log tail | `workflow logs` |
| Run evidence artefact | `workflow evidence --run <run_db_id>` |
| PG18 checkpoint audit (admin) | `public.checkpoints*` on `127.0.0.1:55433` / `agent_core` |
| Graph topology parity | `workflow topology` (prod) or Studio local API |
| Disposable dev graph runs | Studio only — **not** production thread IDs |

Studio uses the Agent Server **dev** checkpointer (sqlite/in-memory). It **cannot** open, resume, or inspect production PostgresSaver threads.

---

## Preconditions

| Check | Expect |
|---|---|
| Operator cwd | `D:\github\agentcore-control-plane\scripts` |
| Bifrost | `http://127.0.0.1:8080` healthy |
| PG18 | `127.0.0.1:55433` accepting (`agent_core`) |
| Env names | `AGENT_CORE_POSTGRES_PASSWORD`, Bifrost VK(s) as User-scope vars |

---

## Evidence pointers

- E2E 17/17: `audits/M6/fixture-e2e-summary.json` · `audits/LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json`
- Studio live: `audits/LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md`
- Operator launch cwd: `audits/M6/WORKFLOW_OPERATOR_LAUNCH_ACCEPTANCE_2026-08-02.md`
- Memory gateway: `audits/MEMORY_GATEWAY_HEALTH_2026-07-22.md`
