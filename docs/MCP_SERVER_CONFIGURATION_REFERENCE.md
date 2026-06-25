# MCP Server Configuration Reference

`D:\MCP-Control-Plane` is the source of truth for MCP server configuration on this PC.

Use this document when an IDE needs to be repaired, manually configured, or compared against the rendered control-plane outputs.

For drive layout and active/archive storage policy, see `D:\MCP-Control-Plane\docs\AGENTCORE_STORAGE_DESIGN.md`.

## Source Renderers

- Cursor: `D:\MCP-Control-Plane\renderers\cursor-global.mcp.json`
- OpenClaw: `D:\MCP-Control-Plane\renderers\openclaw.openclaw.fragment.json`
- MiniMax / Mavis legacy: `D:\MCP-Control-Plane\renderers\minimax.mcp.json`
- Open Interpreter: `D:\MCP-Control-Plane\renderers\open-interpreter.config.fragment.json`
- Android Studio: `D:\MCP-Control-Plane\renderers\android-studio.mcp.json`

## Live Config Paths

- Cursor global: `C:\Users\ynotf\.cursor\mcp.json`
- OpenClaw: `C:\Users\ynotf\.openclaw\openclaw.json`
- MiniMax new platform: `C:\Users\ynotf\.minimax\mcp\mcp.json`
- MiniMax / Mavis legacy: `C:\Users\ynotf\.mavis\mcp\mcp.json`
- Open Interpreter: `C:\Users\ynotf\AppData\Roaming\interpreter\config.json`
- Android Studio: no live MCP config found under `%APPDATA%\Google` as of this audit

## Default Memory Server

All IDEs should use `global-memory-gateway` for normal memory operations.

```json
{
  "global-memory-gateway": {
    "type": "stdio",
    "command": "D:\\Codex_Managed\\.venv\\Scripts\\python.exe",
    "args": [
      "-m",
      "autonomy_factory.global_memory_gateway",
      "--user-id",
      "master_developer_profile"
    ],
    "env": {
      "MEM0_DEFAULT_USER_ID": "master_developer_profile",
      "MEMORY_GATEWAY_BACKEND": "postgres",
      "AGENT_CORE_PGHOST": "127.0.0.1",
      "AGENT_CORE_PGPORT": "55432",
      "AGENT_CORE_PGDATABASE": "agent_core",
      "AGENT_CORE_PGUSER": "agent_ingest",
      "AGENT_CORE_PGPASSWORD": "${env:AGENT_CORE_AGENT_INGEST_PASSWORD}",
      "MEMORY_GATEWAY_EMBEDDING_PROVIDER": "auto",
      "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
      "MEMORY_GATEWAY_EMBEDDING_DIMENSIONS": "1536",
      "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
    }
  }
}
```

## Full JSON Shapes

## Prompt: MiniMax Configure Open Interpreter MCP And Global Rules

Use this prompt in MiniMax when you want MiniMax to configure Open Interpreter MCP and enforce the AgentCore drive rules.

````text
Act as a senior Windows MCP control-plane engineer.

Goal: Configure Open Interpreter to use the MCP server JSON I paste below and enforce the AgentCore drive write boundary for future agents.

Authority:
- `D:\MCP-Control-Plane` is the source of truth.
- Read `D:\MCP-Control-Plane\AGENT_DATABASE_BOOTSTRAP.md`.
- Read `D:\MCP-Control-Plane\docs\MCP_SERVER_CONFIGURATION_REFERENCE.md`.
- Read `D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
- Use `D:\MCP-Control-Plane\renderers\open-interpreter.config.fragment.json` as the reference shape.

Target:
- Open Interpreter live config: `C:\Users\ynotf\AppData\Roaming\interpreter\config.json`

Safety requirements:
- Do not print, summarize, or store secret values.
- If the pasted JSON contains literal secrets, stop and replace them with environment-variable placeholders such as `${env:OPENAI_API_KEY}`.
- Create a timestamped raw backup under `D:\Autonomy\secrets-backups\` before editing live config.
- Create a redacted or metadata-only rollout record under `D:\MCP-Control-Plane\artifacts\live-rollout\`.
- Preserve non-MCP Open Interpreter settings.
- Merge/update only the `mcpServers` section unless the app's schema requires otherwise.

Required memory server:
- Keep `global-memory-gateway`.
- It must use `MEMORY_GATEWAY_BACKEND=postgres`.
- It must point at `127.0.0.1:55432/agent_core`.
- It must use `MEMORY_GATEWAY_EMBEDDING_PROVIDER=auto`.
- It must use `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`.
- Do not add raw Mem0 as a normal-agent route.

Drive write boundary:
- Default writable roots: `F:\AgentCore` and `E:\AgentCoreArchive`.
- Do not write to `C:`, `D:`, `G:`, `H:`, or `I:` unless the user explicitly instructs that drive for the current task.
- If a write to `F:\AgentCore` or `E:\AgentCoreArchive` fails, stop immediately and notify the user.
- Never silently fall back to another drive.
- Raw secret-bearing backups remain restricted to `D:\Autonomy\secrets-backups`.

Tasks:
1. Inspect the current Open Interpreter config.
2. Back it up before editing.
3. Parse the pasted MCP JSON and identify whether it is a full config, an `mcpServers` fragment, or a single server block.
4. Merge it into Open Interpreter's config using the correct schema.
5. Ensure `global-memory-gateway` remains configured exactly as the PostgreSQL-backed default.
6. Add or update any Open Interpreter global instruction/rule file if the app supports one; if no global rule file exists, create a clearly named local MCP note beside the config that points to `D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
7. Validate JSON parsing.
8. Report only paths changed, server names added/updated, validation results, backup path, and restart requirement.

Here is the MCP JSON to add:

```json
PASTE_JSON_HERE
```
````

## Prompt: Add MCP Server To Codex

Use this prompt in Codex when you want to paste a new MCP server JSON block into the chat and have Codex apply it safely.

````text
Act as a senior Windows MCP control-plane engineer.

Goal: Add the MCP server JSON I paste below to the Codex MCP configuration on this PC and enforce the AgentCore drive write boundary while preserving existing working servers and secrets.

Authority:
- `D:\MCP-Control-Plane` is the source of truth.
- Read `D:\MCP-Control-Plane\AGENT_DATABASE_BOOTSTRAP.md`.
- Read `D:\MCP-Control-Plane\docs\MCP_SERVER_CONFIGURATION_REFERENCE.md`.
- Read `D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
- Use existing renderer/config patterns from `D:\MCP-Control-Plane\renderers\`.

Safety requirements:
- Do not print, summarize, or store secret values.
- If the pasted JSON contains literal secrets, stop and replace them with environment-variable placeholders such as `${env:OPENAI_API_KEY}`.
- Create a timestamped raw backup under `D:\Autonomy\secrets-backups\` before editing any live Codex config.
- Create a redacted or metadata-only rollout record under `D:\MCP-Control-Plane\artifacts\live-rollout\`.
- Preserve existing MCP servers unless they conflict with this control-plane policy.
- Keep `global-memory-gateway` as the default memory server.
- Do not add raw Mem0 as a normal-agent memory route.
- Enforce that normal writes go only to `F:\AgentCore` or `E:\AgentCoreArchive`.
- Do not write to `C:`, `D:`, `G:`, `H:`, or `I:` unless the user explicitly instructs that drive for the current task.
- If an approved drive write fails, stop immediately and notify the user; do not silently fall back.

Expected memory server default:
- server name: `global-memory-gateway`
- backend: PostgreSQL/pgvector
- database: `127.0.0.1:55432/agent_core`
- embedding provider mode: `auto`
- preferred model: `text-embedding-3-small`

Tasks:
1. Discover the live Codex MCP config path and current config shape.
2. Parse the pasted JSON and identify whether it is a full config, an `mcpServers` fragment, or a single server block.
3. Merge it into the Codex MCP config using the correct schema for Codex.
4. Validate JSON parsing.
5. Validate that `global-memory-gateway` still exists and still has `MEMORY_GATEWAY_BACKEND=postgres`.
6. Validate that no quarantined normal-agent routes were added.
7. Add or update Codex global rules/instructions so future Codex agents read `D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
8. Re-lock managed config files if this host uses read-only drift protection.
9. Report only paths changed, server names added/updated, validation results, backup path, and restart requirement.

Here is the MCP JSON to add:

```json
PASTE_JSON_HERE
```
````

### Cursor / MiniMax / Open Interpreter

These clients use a top-level `mcpServers` object.

```json
{
  "mcpServers": {
    "global-memory-gateway": {
      "type": "stdio",
      "command": "D:\\Codex_Managed\\.venv\\Scripts\\python.exe",
      "args": [
        "-m",
        "autonomy_factory.global_memory_gateway",
        "--user-id",
        "master_developer_profile"
      ],
      "env": {
        "MEMORY_GATEWAY_BACKEND": "postgres",
        "AGENT_CORE_PGHOST": "127.0.0.1",
        "AGENT_CORE_PGPORT": "55432",
        "AGENT_CORE_PGDATABASE": "agent_core",
        "AGENT_CORE_PGUSER": "agent_ingest",
        "AGENT_CORE_PGPASSWORD": "${env:AGENT_CORE_AGENT_INGEST_PASSWORD}",
        "MEMORY_GATEWAY_EMBEDDING_PROVIDER": "auto",
        "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
        "MEMORY_GATEWAY_EMBEDDING_DIMENSIONS": "1536",
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
      }
    }
  }
}
```

### OpenClaw

OpenClaw uses `mcp.servers`.

```json
{
  "mcp": {
    "servers": {
      "global-memory-gateway": {
        "type": "stdio",
        "command": "D:\\Codex_Managed\\.venv\\Scripts\\python.exe",
        "args": [
          "-m",
          "autonomy_factory.global_memory_gateway",
          "--user-id",
          "master_developer_profile"
        ],
        "env": {
          "MEMORY_GATEWAY_BACKEND": "postgres",
          "AGENT_CORE_PGHOST": "127.0.0.1",
          "AGENT_CORE_PGPORT": "55432",
          "AGENT_CORE_PGDATABASE": "agent_core",
          "AGENT_CORE_PGUSER": "agent_ingest",
          "AGENT_CORE_PGPASSWORD": "${env:AGENT_CORE_AGENT_INGEST_PASSWORD}",
          "MEMORY_GATEWAY_EMBEDDING_PROVIDER": "auto",
          "OPENAI_EMBEDDING_MODEL": "text-embedding-3-small",
          "MEMORY_GATEWAY_EMBEDDING_DIMENSIONS": "1536",
          "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
        }
      }
    }
  }
}
```

## Agent Behavior

After restart, agents can use the database when they call the memory tools exposed by `global-memory-gateway`:

- `memory_append`
- `memory_search`
- `memory_state`

The gateway writes to PostgreSQL `agent_core` and pgvector automatically. Agents do not need SQL for normal memory work.

Active agent workspaces belong under `F:\AgentCore\agents_workspace`.

Agents do not automatically save every chat token or every file they read. Durable database writes happen when:

- an agent calls `memory_append`
- a trusted ingest script writes investigation data
- a task rule explicitly tells the agent to persist compact durable findings

Do not store raw secrets, raw logs, full transcripts, or full source dumps in the vector store.

## MiniMax Notes

This PC has two MiniMax/Mavis MCP config trees:

- New platform: `C:\Users\ynotf\.minimax\mcp\mcp.json`
- Legacy Mavis platform: `C:\Users\ynotf\.mavis\mcp\mcp.json`

Both should be kept aligned with `D:\MCP-Control-Plane\renderers\minimax.mcp.json`.

The GUI app config at `C:\Users\ynotf\AppData\Roaming\MiniMax Agent\minimax-agent-config.json` may contain account tokens and must not be copied into reports, prompts, or normal artifacts.

## Validation Commands

Drive boundary authority:

`D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`

```powershell
D:\MCP-Control-Plane\validators\validate-control-plane.ps1 -Root D:\MCP-Control-Plane
```

```powershell
D:\MCP-Control-Plane\ops\Start-AgentCorePostgres.ps1
```

```powershell
$env:PGPASSWORD=[Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_READ_PASSWORD", "User")
$env:PGSSLMODE="require"
F:\AgentCore\postgres_runtime_engine\pgsql\bin\psql.exe -h 127.0.0.1 -p 55432 -U agent_read -d agent_core -c "SELECT COUNT(*) FROM global_vector_memory_store;"
```
