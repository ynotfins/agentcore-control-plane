# LangSmith Studio Gate + Controlled Pilot — Phase 9

**Date:** 2026-07-25

## Studio gate (re-verified)

| Check | Result |
| --- | --- |
| Launch | `PYTHONPATH=scripts python -m agentcore workflow studio --port 2024 --no-browser` |
| Bind | `127.0.0.1:2024` |
| `/docs` | **200** |
| `/info` | **200**; `flags.langsmith=false` |
| Topology fingerprint | `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` |
| `LANGSMITH_TRACING` | `false` (User-scope set Phase 6 + forced by launcher) |
| `LANGGRAPH_CLI_NO_ANALYTICS` | `1` |
| `LANGSMITH_API_KEY` User-scope | **absent** |
| Hosted browser Studio | `LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED` (unchanged gate) |
| Persistence | Agent Server **dev** in-memory checkpointer — not production PostgresSaver |
| Server stopped after verify | yes (dev-only; never a Windows service) |

Studio URL (operator): `https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024`  
If `/docs` works but Studio cannot fetch localhost: allow **Local network access** for `smith.langchain.com` (Chrome PNA). Do not open a public tunnel.

## Controlled pilot project

**Not started this phase** (operator selection required).

Constraints from plan:

- Not AgentCore control-plane, not EMU, not Swarm product repos
- Register project → `AGENTS.md` + `CLAUDE.md` → Milestone 0 → one clear goal → pause/resume + kill/resume → accept only after deterministic tests

**Pilot:** `LANGGRAPH_STUDIO_LOCAL_GATE_PASS` · `LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED` · `CONTROLLED_PILOT_OPERATOR_SELECTION_PENDING`

## Related

- Prior accept: `audits/LANGGRAPH_STUDIO_LIVE_ACCEPTANCE_2026-07-21.md`
- Runbook: `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
