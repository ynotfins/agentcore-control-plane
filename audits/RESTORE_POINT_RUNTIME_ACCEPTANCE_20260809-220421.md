# AgentCore Runtime Restore-Point Report

**Timestamp:** 2026-08-09T22:04:21-04:00
**Repository:** `@D:\github\agentcore-control-plane`
**Git branch:** `main`
**Git HEAD:** `04a7dee467967197f85e2c8d5f5b07d0bbfb7fec`
**Morning readiness status:** `READY`

## Git state

```text
## main...origin/main
 M audits/M6/fixture-e2e-summary.json
 M audits/M6/m6-acceptance-summary.json
 M audits/M6/m6-acceptance-summary.txt
 M audits/M7/m7-acceptance-summary.json
 M audits/M7/m7-acceptance-summary.txt
 M audits/M8/m8-acceptance-summary.json
 M audits/M8/m8-acceptance-summary.txt
 M docs/templates/SALLY_FULL_SWARM_ACCEPTANCE_REPORT_TEMPLATE_2026-08-09.md
 M scripts/agentcore_workflow/requirements.txt
?? .agentcore/rollback/
?? .agents/skills/
?? audits/CONTEXT_ENGINE_LANGGRAPH_START_2026-08-01.jsonl
?? audits/M5/pg18-restore-test-20260729-033002.json
?? audits/M5/pg18-restore-test-20260730-033001.json
?? audits/M5/pg18-restore-test-20260731-033002.json
?? audits/M5/pg18-restore-test-20260801-033001.json
?? audits/M5/pg18-restore-test-20260802-033001.json
?? audits/M5/pg18-restore-test-20260803-033002.json
?? audits/M5/pg18-restore-test-20260804-033001.json
?? audits/M5/pg18-restore-test-20260805-033001.json
?? audits/M5/pg18-restore-test-20260806-033001.json
?? audits/M5/pg18-restore-test-20260807-033001.json
?? audits/M5/pg18-restore-test-20260808-033001.json
?? audits/M5/pg18-restore-test-20260809-033002.json
?? docs/operations/LANGFUSE_TRACING_AND_PROMPTS.md
?? ide-profiles/minimax-classic/.trash/
?? ide-profiles/minimax-classic/deepseek-v4-pro-openrouter.PASTE-INTO-EIGENT.json
?? ide-profiles/minimax-classic/deepseek-v4-pro-openrouter.json
?? ide-profiles/minimax-classic/minimax-m3-direct-minimax.PASTE-INTO-EIGENT.json
?? ide-profiles/minimax-classic/minimax-m3-direct-minimax.json
?? ide-profiles/minimax-classic/minimax-m3-eigent-README.md
?? ide-profiles/minimax-classic/recovered-from-minimax-code/
?? ide-profiles/reasonix/
?? scripts/agentcore_workflow/langfuse_bootstrap_prompts.py
?? scripts/icon/
?? skills-lock.json
?? tools/caveman-docs/
```

## Bifrost config hashes

| Path | Exists | SHA-256 | Bytes |
| --- | --- | --- | --- |
| `@D:\github\agentcore-control-plane\renderers\bifrost\config.json` | True | `062EF7694DF7316D60379E020328696A6D861BF699AB01113508274F8089D3E0` | 24485 |
| `F:\AgentCore\runtime\bifrost\config.json` | True | `41BB78234E659472C7A88AC1746E87A3E673460E3FCF5B0D4C470F19CD3B2106` | 21636 |
| `F:\AgentCore\runtime\bifrost\config\config.json` | True | `41BB78234E659472C7A88AC1746E87A3E673460E3FCF5B0D4C470F19CD3B2106` | 21636 |

## Scheduled tasks

| Task | Exists | State | Last result | Last run |
| --- | --- | --- | --- | --- |
| `AgentCore-Bifrost-Gateway` | True | Running | `2147946720` | `08/09/2026 17:58:33` |
| `AgentCore-Bifrost-Watchdog` | True | Ready | `0` | `08/09/2026 22:03:33` |

## Acceptance evidence paths

| Evidence | Status | Path |
| --- | --- | --- |
| Sally full Swarm acceptance | present | `H:\SwarmData\claw\workspace\sally\SALLY_FULL_SWARM_ACCEPTANCE_2026-08-09.md` |
| LangGraph production canary | present | `@D:\github\agentcore-control-plane\audits\LANGGRAPH_TOPOLOGY_CANARY_2026-08-09_1951.md` |
| SwarmClaw autonomous canary | present | `H:\SwarmData\claw\workspace\sally\SWARMCLAW_AUTONOMOUS_CANARY_2026-08-09.md` |

## Morning readiness JSON

```json
{
  "status": "READY",
  "pass": 23,
  "warn": 0,
  "fail": 0,
  "results": [
    {
      "status": "PASS",
      "name": "cursor_global_mcp",
      "detail": "exactly one server: agentcore-gateway",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "cursor_global_mcp_secret_scan",
      "detail": "no obvious secret literal pattern",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "bifrost_status_script",
      "detail": "BIFROST_STATUS_OK",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "bifrost_health",
      "detail": "HTTP 200",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "bifrost_config_drift",
      "detail": "source-rendered candidate/live/projection match: 41BB78234E659472C7A88AC1746E87A3E673460E3FCF5B0D4C470F19CD3B2106",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "task_AgentCore-Bifrost-Gateway",
      "detail": "state=Running; lastResult=2147946720; lastRun=8/9/2026 5:58:33 PM",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "task_AgentCore-Bifrost-Watchdog",
      "detail": "state=Ready; lastResult=0; lastRun=8/9/2026 10:03:33 PM",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "swarmrecall_api_health",
      "detail": "HTTP 200",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "meilisearch_health",
      "detail": "HTTP 200",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "swarmclaw_health",
      "detail": "HTTP 200",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "swarmrecall_web",
      "detail": "HTTP 200",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "swarm_data_root",
      "detail": "exists: H:\\SwarmData",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "swarm_runtime_root",
      "detail": "exists: H:\\SwarmRuntime",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "swarm_backup_root",
      "detail": "exists: E:\\SwarmBackups",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "agentcore_runtime_root",
      "detail": "exists: F:\\AgentCore",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "postgres18_root",
      "detail": "exists: F:\\PostgreSQL18",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "port_3300",
      "detail": "listening on 127.0.0.1",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "port_3456",
      "detail": "listening on 127.0.0.1",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "port_7700",
      "detail": "listening on 127.0.0.1",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "port_8080",
      "detail": "listening on 127.0.0.1",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "port_55433",
      "detail": "listening on 127.0.0.1",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "port_65432",
      "detail": "listening on 127.0.0.1",
      "remediation": ""
    },
    {
      "status": "PASS",
      "name": "langgraph_topology",
      "detail": "fingerprint=a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32; nodes=15",
      "remediation": ""
    }
  ]
}
```

## Closeout rule

Do not treat this restore point as production-ready unless morning readiness is `READY` and all three acceptance evidence paths are present.
