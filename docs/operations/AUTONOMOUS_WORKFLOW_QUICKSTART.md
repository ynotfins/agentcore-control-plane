# Autonomous Workflow Quickstart

**Run from:** `D:\github\agentcore-control-plane` only.  
**Not from:** `D:\github\deepagents` (upstream / local Deep Agents checkout is not the operator CLI).

**Full runbook:** `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`

---

## Cursor Auto context posture

When the IDE routes via Cursor Auto (model not reliably observable), use AgentCore **`standard-context`** (conservative model-limit-aware ceiling). Durable history remains unbounded in PostgreSQL; only the active request budget is bounded. Do not invent a larger profile to “fit more” without an explicit operator decision.

---

## Exact commands

```powershell
cd D:\github\agentcore-control-plane

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

# Observe
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

# Studio (dev-only Agent Server; NOT production PostgresSaver)
python -m agentcore workflow studio --port 2024 --no-browser
```

Studio defaults: `127.0.0.1:2024`, `LANGSMITH_TRACING=false`, `LANGGRAPH_CLI_NO_ANALYTICS=1`, anonymous/local first. Topology fingerprint must be `a86e40e8ddd0a370…`.

---

## Preconditions

| Check | Expect |
|---|---|
| Bifrost | `http://127.0.0.1:8080` healthy |
| PG18 | `127.0.0.1:55433` accepting (`agent_core`) |
| Env names | `AGENT_CORE_POSTGRES_PASSWORD`, Bifrost VK(s) as User-scope vars |

---

## Evidence pointers

- E2E 17/17: `audits/M6/fixture-e2e-summary.json` · `audits/LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json`
- Studio live: `audits/LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md`
- Memory gateway: `audits/MEMORY_GATEWAY_HEALTH_2026-07-22.md`
