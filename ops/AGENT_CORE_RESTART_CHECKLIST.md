# Agent Core Restart Checklist

Use this after installing or servicing the `Agent_Vector_4TB` Samsung 990 Pro NVMe drive.

## Goal

Keep the active AgentCore paths stable:

- Engine: `F:\AgentCore\postgres_runtime_engine\pgsql`
- Database cluster: `F:\AgentCore\database_cluster`
- Active workspaces: `F:\AgentCore\agents_workspace`
- Cold archive: `E:\AgentCoreArchive`

The MCP memory gateway and IDE configs do not launch PostgreSQL directly, but they depend on the database being available at:

`127.0.0.1:55432/agent_core`

## Environment Variable Policy

AgentCore does not use `.env` files. All secrets and runtime credentials are stored in Windows Environment Variables. Documentation may list variable names only, never values.

## Before Restart

- Confirm the current engine path exists: `F:\AgentCore\postgres_runtime_engine\pgsql`
- Confirm the data directory exists: `F:\AgentCore\database_cluster`
- Confirm the server is healthy:

```powershell
D:\MCP-Control-Plane\ops\Start-AgentCorePostgres.ps1
```

## After Reboot Or Drive Service

1. Confirm Windows kept `Agent_Vector_4TB` as drive letter `F:`.
2. If Windows assigns a different letter, use Disk Management to restore the original `F:` letter before starting agents.
3. Run:

```powershell
D:\MCP-Control-Plane\ops\Start-AgentCorePostgres.ps1 -StartIfStopped
```

1. Confirm the script reports:

- `engine root`: passed
- `pg_ctl`: passed
- `server status`: passed
- `pgvector extension`: passed
- `vector table query`: passed

## If F: Changes

Preferred fix: restore the drive letter to `F:`.

Temporary fix:

```powershell
D:\MCP-Control-Plane\ops\Start-AgentCorePostgres.ps1 -EngineRoot "X:\AgentCore\postgres_runtime_engine\pgsql" -DataDir "X:\AgentCore\database_cluster" -StartIfStopped
```

Then update the control-plane contract and docs if the new letter is permanent.

## IDE Restart Order

After PostgreSQL health passes:

1. Cursor
2. Codex
3. OpenClaw
4. Claude Code
5. MiniMax
6. Open Interpreter
7. Android Studio if/when an MCP config exists

Each non-Swarm IDE should load one MCP baseline entry:

- `agentcore-gateway`
- `http://127.0.0.1:8080/mcp`
- `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`

Before restarting IDEs, validate Bifrost with:

```powershell
D:\github\agentcore-control-plane\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
```

Use `docs\restart_after_env_changes.md` for the full restart and env-propagation checklist.
