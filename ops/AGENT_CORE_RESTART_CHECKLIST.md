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

4. Confirm the script reports:

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
2. OpenClaw
3. MiniMax
4. Open Interpreter
5. Android Studio if/when an MCP config exists

Each IDE should load `global-memory-gateway` with:

- `MEMORY_GATEWAY_BACKEND=postgres`
- `AGENT_CORE_PGHOST=127.0.0.1`
- `AGENT_CORE_PGPORT=55432`
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `MEMORY_GATEWAY_EMBEDDING_PROVIDER=auto`
