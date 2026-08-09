# Sally Full Swarm Acceptance Report Template

Use this template for Sally/SwarmClaw's final acceptance report. Replace every bracketed placeholder with current live evidence. Do not include secrets, bearer tokens, API keys, raw database credentials, raw SwarmRecall credentials, or raw SwarmVault credentials.

## Final status

- Final status: [PASS | PARTIAL | FAIL]
- Timestamp: [YYYY-MM-DDTHH:MM:SS-04:00]
- Timestamp format example: 2026-08-09T08:00:00-04:00
- Machine: [machine name]
- Operator-visible summary: [one paragraph]

## Version evidence

- SwarmClaw version: [version]
- SwarmRecall version: [version]
- SwarmVault version: [version]
- Meilisearch version: [version if available]
- PostgreSQL/listener version: [version if available]

## Storage roots

- Swarm hot data root: H:\SwarmData
- Swarm runtime root: H:\SwarmRuntime
- Swarm backup/archive root: E:\SwarmBackups
- Evidence that no LangGraph-owned runtime path was used: [evidence]
- Evidence that no AgentCore-owned runtime path was used for Swarm state: [evidence]

## Service table and endpoints

| Service | Endpoint/path | Status | Timestamp | Evidence |
| --- | --- | --- | --- | --- |
| SwarmClaw | [endpoint] | [PASS/PARTIAL/FAIL] | [timestamp] | [sanitized evidence] |
| SwarmRecall | [endpoint] | [PASS/PARTIAL/FAIL] | [timestamp] | [sanitized evidence] |
| SwarmVault | [endpoint/path] | [PASS/PARTIAL/FAIL] | [timestamp] | [sanitized evidence] |
| Meilisearch | [endpoint] | [PASS/PARTIAL/FAIL] | [timestamp] | [sanitized evidence] |
| PostgreSQL/listener 65432 | [endpoint/path] | [PASS/PARTIAL/FAIL] | [timestamp] | [sanitized evidence] |

## SwarmRecall canary

- Canary ID: [sanitized id]
- Write/POST/create result: [status and sanitized evidence]
- Read/GET/retrieve result: [status and sanitized evidence]
- Search result: [status and sanitized evidence]
- Exact match proof: [what matched, without secrets]
- Credential handling proof: [confirm no raw credentials exposed]

## SwarmVault canary

- Corpus/source count: [count/status]
- Search query: [safe query]
- Search result: [status and sanitized evidence]
- Context-pack result: [status and sanitized evidence]
- Context-pack token size: [token count if available]

## Autonomous team canary

- Canary task ID: [sanitized id]
- Team path: Sally -> [Builder/equivalent] -> [QA/equivalent] -> [Reviewer/equivalent]
- Task created: [status and sanitized evidence]
- Delegation: [status and sanitized evidence]
- Result: [status and sanitized evidence]
- Review: [status and sanitized evidence]
- Completed: [status and sanitized evidence]

## No-cross-write boundary

- No writes to AgentCore: [evidence]
- No writes to Bifrost: [evidence]
- No writes to LangGraph: [evidence]
- No writes to IDE configs: [evidence]
- Swarm runtime paths stayed under approved Swarm roots: [evidence]

## Exact files changed

- [path or "none"]

## Files intentionally not touched

- AgentCore: [evidence]
- Bifrost: [evidence]
- LangGraph: [evidence]
- IDE configs: [evidence]
- Non-Swarm project folders: [evidence]

## Backup / restore point

- Backup or restore point path: [path under E:\SwarmBackups or current Swarm-approved backup root]
- Files included: [sanitized list/count]
- Readability verification: [status]
- Restore note: [how Sally would restore, without secrets]

## Residuals and operator actions

- Residual risks: [none or list]
- Required restart: [yes/no and reason]
- New Sally chat required: [yes/no and reason]
- Next safe action: [action]
