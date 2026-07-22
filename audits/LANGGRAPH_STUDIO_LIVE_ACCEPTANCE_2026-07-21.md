# LangGraph Studio Live Acceptance — 2026-07-21

**Status:** ACCEPTED (local Agent Server) · hosted browser credential **pending** when `LANGSMITH_API_KEY` absent  
**Launcher:** `python -m agentcore workflow studio --port 2024 --no-browser` from `D:\github\agentcore-control-plane`  
**Evidence log:** `audits/M6/studio-launch-stdout.log` (2026-07-22T04:52:34Z)

## Verdict

Local Agent Server on **port 2024** boots with tracing and analytics forced off. Hosted Studio browser auth is gated, not a launch blocker. Chrome Private Network Access is the first diagnostic when `/docs` works but Studio cannot fetch localhost.

## Checks

| Check | Result |
| --- | --- |
| Bind | `127.0.0.1:2024` only |
| `http://127.0.0.1:2024/docs` | **200** (API Docs URL advertised by Agent Server) |
| `LANGSMITH_TRACING` | `false` (forced by `studio.py`) |
| `LANGGRAPH_CLI_NO_ANALYTICS` | `1` |
| `/info` `flags.langsmith` | `false` (prior accept evidence + launch posture) |
| Topology fingerprint | `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` |
| Persistence | Agent Server **dev** checkpointer — **not** production `PostgresSaver` |
| `LANGSMITH_API_KEY` present | `false` at launch |
| Anonymous Studio attempt | `true` |
| Gate if browser auth required | `LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED` (**pending** until operator sets User-scope env **name** `LANGSMITH_API_KEY` only — never paste value) |
| Chrome 142+ PNA diagnostic | Documented: if `/docs` works but Studio fails → allow **Local network access** on `smith.langchain.com` site info; do not bind LAN/tunnel first |

## Sanitized launch payload (excerpt)

```json
{
  "port": 2024,
  "local_api_url": "http://127.0.0.1:2024",
  "docs_url": "http://127.0.0.1:2024/docs",
  "studio_url": "https://smith.langchain.com/studio/?baseUrl=http://127.0.0.1:2024",
  "langsmith_api_key_present": false,
  "anonymous_studio_attempt": true,
  "gate_code_if_browser_auth_required": "LANGSMITH_STUDIO_BROWSER_CREDENTIAL_REQUIRED",
  "env": {
    "LANGSMITH_TRACING": "false",
    "LANGGRAPH_CLI_NO_ANALYTICS": "1",
    "LANGGRAPH_ANALYTICS": "false",
    "LANGGRAPH_HOST": "127.0.0.1"
  },
  "topology_fingerprint": "a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32"
}
```

## Out of scope

- Production PostgresSaver thread sharing (forbidden; isolation proven in E2E)
- MiniMax / Cherry live config edits
- Enabling LangSmith tracing

## Related

- Runbook: `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
- Quickstart: `docs/operations/AUTONOMOUS_WORKFLOW_QUICKSTART.md`
- E2E recovery: `audits/LANGGRAPH_END_TO_END_RECOVERY_2026-07-21.json`
- Prior interrupt accept (port 8124 era): `audits/M6/studio-interrupt-accept.json`
