# MCP Server Configuration Reference

`D:\github\agentcore-control-plane` is the canonical Git source repo for MCP server configuration policy on this PC.

`D:\MCP-Control-Plane` remains the current live deployed ops root used by scheduled tasks, inherited rollout scripts, and live archive hooks until a separate migration is approved.

Use this document when an IDE needs to be repaired, manually configured, or compared against the rendered control-plane outputs.

Machine-readable master contract:

- `D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json`
- Use this first when another IDE agent needs to install or verify the mandatory/essential AgentCore MCP surface.
- The renderer files remain the executable per-client outputs; the master contract records the shared policy, per-client server sets, unique client setup notes, and default exclusions in one place.

For drive layout and active/archive storage policy, see `D:\github\agentcore-control-plane\docs\AGENTCORE_STORAGE_DESIGN.md`.

## Source Renderers

- Cursor: `D:\github\agentcore-control-plane\renderers\cursor-global.mcp.json`
- OpenClaw: `D:\github\agentcore-control-plane\renderers\openclaw.openclaw.fragment.json`
- MiniMax / Mavis legacy: `D:\github\agentcore-control-plane\renderers\minimax.mcp.json`
- Open Interpreter: `D:\github\agentcore-control-plane\renderers\open-interpreter.config.fragment.json`
- Android Studio: `D:\github\agentcore-control-plane\renderers\android-studio.mcp.json`

## Live Config Paths

- Cursor global: `C:\Users\ynotf\.cursor\mcp.json`
- OpenClaw: `C:\Users\ynotf\.openclaw\openclaw.json`
- MiniMax new platform: `C:\Users\ynotf\.minimax\mcp\mcp.json`
- MiniMax / Mavis legacy: `C:\Users\ynotf\.mavis\mcp\mcp.json`
- Open Interpreter: `C:\Users\ynotf\AppData\Roaming\interpreter\config.json`
- Android Studio: no live MCP config found under `%APPDATA%\Google` as of this audit

## Core vs Optional MCP Exposure

Use the smallest approved MCP surface that still preserves the governed routing contract.

Core governed routes:

- `global-memory-gateway` is the governed memory path and must remain the default memory server.
- `arabold-docs` is the current-docs path.
- `artiforge` remains the approved architecture/codebase scan path.
- `sequential-thinking` remains the approved planning/debugging MCP where reasoning MCP exposure is needed.
- `serena` remains the repo-code navigation/refactor MCP for the clients that perform code-aware editing.

Optional high-surface routes:

- `context-fabric`, `filesystem`, `github-mcp`, `obsidian-vault`, `playwright`, `cursor-agent-mcp`, and `mcp-debugger` are useful, but each adds more tools and more context-window pressure.
- Keep them only on the clients that actually need them, and treat additions beyond the approved renderer sets as drift unless the exception is promoted into the source renderer and master contract.
- `context-fabric`, `cursor-agent-mcp`, `github-mcp`, and `mcp-debugger` are task-specific opt-ins for Cursor/OpenClaw rather than part of the bounded default surface.

Current approved renderer surfaces:

- Codex: bounded to 11 or fewer live MCP servers; `global-memory-gateway`, `arabold-docs`, `artiforge`, `sequential-thinking`, and `serena` must remain present, while direct Firecrawl routes are not part of the default AgentCore memory rollout surface.
- Cursor: 8 servers (`arabold-docs`, `artiforge`, `filesystem`, `global-memory-gateway`, `obsidian-vault`, `playwright`, `sequential-thinking`, `serena`)
- OpenClaw: 9 servers (same reduced approved set as Cursor plus the user-approved `eye2byte` OpenClaw-only MCP)
- MiniMax Code: 7 servers (`arabold-docs`, `artiforge`, `filesystem`, `global-memory-gateway`, `obsidian-vault`, `playwright`, `sequential-thinking`)
- Open Interpreter: 3 servers (`arabold-docs`, `artiforge`, `global-memory-gateway`)

Validation note:

- `validators\validate-control-plane.ps1` enforces the approved source renderer server sets and keeps repo validation separate from live rollout timing.
- `ops\Test-AgentCoreLiveClientAdoption.ps1` is the live-state proof after restart; it verifies that the running clients actually adopted the governed config set.
- `eye2byte` is intentionally approved only for OpenClaw and must not be copied into Codex, Cursor, MiniMax, Mavis, or Open Interpreter.

## Default Memory Server

All IDEs should use `global-memory-gateway` for normal memory operations.

Unified memory rollout rules:

- `global-memory-gateway` is the only normal agent write path.
- `agent_core` on `127.0.0.1:55432` is the canonical governed memory database.
- `SwarmRecall` stays local-only as a backend runtime and retrieval service, not a default broad MCP surface for every IDE.
- `SwarmVault` stays local-first under `F:\AgentCore\agentmemory\swarmvault` as the shared RAG/wiki substrate.
- Projection into `SwarmRecall` and `SwarmVault` is handled by control-plane jobs, not client-side dual writes.
- Direct `SwarmRecall` MCP exposure is intentionally absent from the default renderer set.

```json
{
  "global-memory-gateway": {
    "type": "stdio",
    "command": "D:\\Codex_Managed\\.venv\\Scripts\\python.exe",
    "args": [
      "-m",
      "autonomy_factory.global_memory_gateway",
      "--user-id",
      "master_developer_profile",
      "--project-id",
      "codex-managed",
      "--platform",
      "cursor"
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

The rendered client fragments use the same governed contract but set `--platform` per client:

- Codex: `codex`
- Cursor: `cursor`
- OpenClaw: `openclaw`
- Open Interpreter: `open-interpreter`
- MiniMax Code: `minimax-code`

After a live apply:

1. Restart the affected client.
2. Run `D:\github\agentcore-control-plane\ops\Test-AgentCoreLiveClientAdoption.ps1`.
3. Do not claim live rollout completion until that verifier passes for the clients in scope.

## Environment Variable Policy

AgentCore does not use `.env` files. All secrets and runtime credentials are stored in Windows Environment Variables. Documentation may list variable names only, never values.

If a variable is missing, stop and report the variable name rather than creating a local fallback. See `docs\restart_after_env_changes.md` after any env-var update.

## Full JSON Shapes

## Prompt: MiniMax Configure Open Interpreter MCP And Global Rules

Use this prompt in MiniMax when you want MiniMax to configure Open Interpreter MCP and enforce the AgentCore drive rules.

````text
Act as a senior Windows MCP control-plane engineer.

Goal: Configure Open Interpreter to use the MCP server JSON I paste below and enforce the AgentCore drive write boundary for future agents.

Authority:
- `D:\github\agentcore-control-plane` is the canonical Git source repo.
- `D:\MCP-Control-Plane` remains the live ops root until migration is approved.
- Read `D:\github\agentcore-control-plane\AGENT_DATABASE_BOOTSTRAP.md`.
- Read `D:\github\agentcore-control-plane\docs\MCP_SERVER_CONFIGURATION_REFERENCE.md`.
- Read `D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
- Use `D:\github\agentcore-control-plane\renderers\open-interpreter.config.fragment.json` as the reference shape.

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
- `D:\github\agentcore-control-plane` is the canonical Git source repo.
- `D:\MCP-Control-Plane` remains the live ops root until migration is approved.
- Read `D:\github\agentcore-control-plane\AGENT_DATABASE_BOOTSTRAP.md`.
- Read `D:\github\agentcore-control-plane\docs\MCP_SERVER_CONFIGURATION_REFERENCE.md`.
- Read `D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
- Use existing renderer/config patterns from `D:\github\agentcore-control-plane\renderers\`.

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

## Local-Only Candidate MCPs

These are validated local-only candidates. SwarmRecall's API and Meilisearch runtime are now owned by AgentCore scheduled tasks, but live IDE MCP configs are still governed rollout targets rather than ad hoc per-client edits.

### SwarmVault candidate

- Source: `D:\github\vendor\swarm\swarmvault`
- Runtime root: `F:\AgentCore\agentmemory\swarmvault`
- Wrapper: `D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1`
- Validator: `D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmVault.ps1`
- MCP command shape:

```json
{
  "command": "node",
  "args": [
    "D:\\github\\vendor\\swarm\\swarmvault\\packages\\cli\\dist\\index.js",
    "mcp"
  ]
}
```

- Role: local retrieval/wiki/context only
- Not a replacement for `global-memory-gateway`

### SwarmRecall candidate

- Source: `D:\github\vendor\swarm\swarmrecall`
- Runtime root: `F:\AgentCore\agentmemory\swarmrecall`
- Wrapper: `D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1`
- Validator: `D:\github\agentcore-control-plane\ops\Test-AgentCoreSwarmRecall.ps1`
- Runtime tasks:
  - `\AgentCore\SwarmRecallApi`
  - `\AgentCore\SwarmRecallMeilisearch`
- Aggregate runtime validator: `D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1`
- Required local override:
  - `SWARMRECALL_API_URL=http://127.0.0.1:3300`
- Required local auth:
  - `SWARMRECALL_API_KEY` from the Windows environment
- Verified local listener posture:
  - API binds only to `127.0.0.1:3300`
  - exactly one Meilisearch instance binds to `127.0.0.1:7700`
- MCP command shape:

```json
{
  "command": "node",
  "args": [
    "D:\\github\\vendor\\swarm\\swarmrecall\\packages\\cli\\dist\\index.js",
    "mcp"
  ],
  "env": {
    "SWARMRECALL_API_URL": "http://127.0.0.1:3300",
    "SWARMRECALL_API_KEY": "${env:AGENT_CORE_SWARMRECALL_API_KEY}"
  }
}
```

- Local-only rules:
  - no hosted `swarmrecall-api.onrender.com`
  - no Upstash
  - no Firebase cloud dependency for the agent API path
  - no Docker-backed persistent storage
  - no `--master-key` in the Meilisearch process command line
- Not a replacement for `global-memory-gateway`

## MiniMax Notes

This PC has two MiniMax/Mavis MCP config trees:

- New platform: `C:\Users\ynotf\.minimax\mcp\mcp.json`
- Legacy Mavis platform: `C:\Users\ynotf\.mavis\mcp\mcp.json`

Both should be kept aligned with `D:\MCP-Control-Plane\renderers\minimax.mcp.json`.

The GUI app config at `C:\Users\ynotf\AppData\Roaming\MiniMax Agent\minimax-agent-config.json` may contain account tokens and must not be copied into reports, prompts, or normal artifacts.

## Validation Commands

Drive boundary authority:

`D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`

Source-repo dry-run validation:

```powershell
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreEnvPolicy.ps1
```

Source-repo report-writing validation:

```powershell
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1 -WriteReport
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreEnvPolicy.ps1 -WriteReport
```

Live runtime validation:

```powershell
D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1
```

```powershell
$env:PGPASSWORD=[Environment]::GetEnvironmentVariable("AGENT_CORE_AGENT_READ_PASSWORD", "User")
$env:PGSSLMODE="require"
F:\AgentCore\postgres_runtime_engine\pgsql\bin\psql.exe -h 127.0.0.1 -p 55432 -U agent_read -d agent_core -c "SELECT COUNT(*) FROM global_vector_memory_store;"
```
