# Restart After Environment Changes

## Why Restart Is Required

Windows environment variable changes do not reliably apply to already-running IDE, terminal, or MCP processes. A process may keep its old environment until it is restarted.

## Restart Targets

After changing AgentCore environment variables, restart:

1. Cursor
2. Codex
3. OpenClaw
4. Claude Code
5. open terminals and fresh shells
6. MCP gateway processes and any IDE-hosted MCP sessions that were already running

## Safe Verification

- Verify variable presence by name only.
- Do not print or log secret values.
- Confirm that `AGENT_CORE_PGUSER` resolves to `agent_ingest`.
- Confirm that `AGENT_CORE_PGPASSWORD` resolves from `AGENT_CORE_AGENT_INGEST_PASSWORD` in the MCP config pattern rather than a literal credential.

Example PowerShell checks:

```powershell
[Environment]::GetEnvironmentVariable("AGENT_CORE_PGUSER", "User")
[Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_INGEST_PASSWORD", "User")
```

The checks above are presence checks. Do not echo secret values into transcripts, docs, or logs.

## If Authentication Fails

Before changing database authentication, verify these in order:

1. The required AgentCore environment variables exist in User or System scope.
2. The currently running IDE or MCP process has been restarted after the env-var change.
3. The rendered gateway config still references environment variables rather than literal credentials.
4. PostgreSQL is reachable with SSL/SCRAM using the governed AgentCore role contract.

Do not create a `.env` fallback to work around a stale process environment.
