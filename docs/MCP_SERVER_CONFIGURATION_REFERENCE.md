# MCP Server Configuration Reference

> **HISTORICAL / ROLLBACK REFERENCE ONLY — SUPERSEDED (2026-07-14).**
> This is the pre-Bifrost direct-per-IDE configuration reference. Its per-client server lists
> (including `swarmrecall`/`swarmvault` in non-Swarm IDE surfaces) are **not** current policy.
> **Current architecture:** every non-Swarm IDE has exactly one MCP entry — `agentcore-gateway`
> at `http://127.0.0.1:8080/mcp` — with upstreams registered once in
> `contracts/bifrost-upstream-mcp-registry.json`.
> Current setup authority: `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` and
> `docs/prompts/install-agentcore-gateway-in-ide.md`. Per-IDE profiles: `ide-profiles/`.
> Use this file only for rollback comparison or live-config forensics.

`D:\github\agentcore-control-plane` is the canonical Git source repo for MCP server configuration policy on this PC.

`D:\MCP-Control-Plane` is compatibility/live-ops evidence only.

Machine-readable master contract (historical direct-mode):

- `D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json` — superseded by the Bifrost registry for non-Swarm IDE setup.
- The legacy renderer files remain rollback-only outputs; current per-IDE outputs live in `renderers/gateway-clients/`.

For drive layout and active/archive storage policy, see `D:\github\agentcore-control-plane\docs\AGENTCORE_STORAGE_DESIGN.md`.

## Source Renderers

- Cursor: `D:\github\agentcore-control-plane\renderers\cursor-global.mcp.json`
- OpenClaw: `D:\github\agentcore-control-plane\renderers\openclaw.openclaw.fragment.json`
- MiniMax / Mavis legacy: `D:\github\agentcore-control-plane\renderers\minimax.mcp.json`
- Open Interpreter: `D:\github\agentcore-control-plane\renderers\open-interpreter.config.fragment.json`
- Antigravity / Gemini: `D:\github\agentcore-control-plane\renderers\antigravity.mcp_config.json`
- Android Studio: `D:\github\agentcore-control-plane\renderers\android-studio.mcp.json`

## Live Config Paths

- Codex: `C:\Users\ynotf\.codex\config.toml`
- Cursor global: `C:\Users\ynotf\.cursor\mcp.json`
- OpenClaw: `C:\Users\ynotf\.openclaw\openclaw.json`
- MiniMax new platform: `C:\Users\ynotf\.minimax\mcp\mcp.json`
- MiniMax / Mavis legacy: `C:\Users\ynotf\.mavis\mcp\mcp.json`
- Antigravity / Gemini primary: `C:\Users\ynotf\.gemini\config\mcp_config.json`
- Antigravity secondary: `C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json`
- Claude Code: `C:\Users\ynotf\.claude\config.json`
- Claude Desktop: `C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json`
- Open Interpreter: `C:\Users\ynotf\AppData\Roaming\interpreter\config.json`
- VS Code: `C:\Users\ynotf\AppData\Roaming\Code\User\settings.json`
- Android Studio: no live MCP config found under `%APPDATA%\Google` as of this audit

Removed clients:

- Trae: removed from this workstation on 2026-07-07; do not configure Serena for Trae unless the IDE is explicitly reinstalled and promoted.

## Core vs Optional MCP Exposure

Use the smallest approved MCP surface that still preserves the governed routing contract.

Core governed routes:

- Native SwarmRecall and SwarmVault are the governed local memory/RAG baseline where exposed by the current renderers; `global-memory-gateway` is retired from the default renderer baseline.
- `arabold-docs` is the current-docs path.
- `artiforge` remains the approved architecture/codebase scan path.
- `sequential-thinking` remains the approved planning/debugging MCP where reasoning MCP exposure is needed.
- `serena` remains the repo-code navigation/refactor MCP for the clients that perform code-aware editing.
- `depwire` is the deterministic dependency/impact/simulation/verification MCP for code-editing clients.

Optional high-surface routes:

- `context-fabric`, `filesystem`, `github-mcp`, `obsidian-vault`, `playwright`, `cursor-agent-mcp`, and `mcp-debugger` are useful, but each adds more tools and more context-window pressure.
- Keep them only on the clients that actually need them, and treat additions beyond the approved renderer sets as drift unless the exception is promoted into the source renderer and master contract.
- `context-fabric`, `cursor-agent-mcp`, `github-mcp`, and `mcp-debugger` are task-specific opt-ins for Cursor/OpenClaw rather than part of the bounded default surface.

Current approved renderer surfaces:

- Codex: bounded to 18 or fewer live MCP servers; `arabold-docs`, `artiforge`, `depwire`, `filesystem`, `github`, `node_repl`, `obsidian-vault`, `playwright`, `sequential-thinking`, and `serena` remain expected, with Codex-managed/plugin MCP surfaces allowed. Do not copy Codex-only servers into JSON IDE renderers.
- Cursor: 13 servers (`arabold-docs`, `artiforge`, `context-fabric`, `cursor-agent-mcp`, `depwire`, `filesystem`, `mcp-debugger`, `obsidian-vault`, `playwright`, `sequential-thinking`, `serena`, `swarmrecall`, `swarmvault`)
- OpenClaw: 11 servers (`arabold-docs`, `artiforge`, `depwire`, `eye2byte`, `filesystem`, `obsidian-vault`, `playwright`, `sequential-thinking`, `serena`, `swarmrecall`, `swarmvault`)
- MiniMax Code / Mavis: 10 servers (`arabold-docs`, `artiforge`, `depwire`, `filesystem`, `obsidian-vault`, `playwright`, `sequential-thinking`, `serena`, `swarmrecall`, `swarmvault`)
- Open Interpreter: 6 servers (`arabold-docs`, `artiforge`, `depwire`, `serena`, `swarmrecall`, `swarmvault`)
- Antigravity / Gemini: 10 servers (`arabold-docs`, `artiforge`, `depwire`, `filesystem`, `obsidian-vault`, `playwright`, `sequential-thinking`, `serena`, `swarmrecall`, `swarmvault`)
- Android Studio: `depwire` only until a broader client surface is explicitly promoted.

Validation note:

- `validators\validate-control-plane.ps1` enforces the approved source renderer server sets and keeps repo validation separate from live rollout timing.
- `ops\Test-AgentCoreLiveClientAdoption.ps1` is the live-state proof after restart; it verifies that the running clients actually adopted the governed config set.
- `eye2byte` is intentionally approved only for OpenClaw and must not be copied into Codex, Cursor, MiniMax, Mavis, or Open Interpreter.

## DepWire Default Server

DepWire provides the deterministic dependency graph and structural change-safety layer for code-editing clients. It complements Serena; it does not replace semantic symbol navigation or native project tests.

Canonical launcher:

```text
C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd mcp
```

Governed package version: `depwire-cli@1.8.2`. Set `DEPWIRE_NO_TELEMETRY=1`. The local CLI/MCP server requires no DepWire API/license key. DepWire Pro activation is separate and belongs only to the VS Code/Cursor extension setting `depwire.licenseKey`, entered through `Depwire: Enter License Key` without exposing the value.

```json
{
  "depwire": {
    "type": "stdio",
    "command": "C:\\Users\\ynotf\\AppData\\Roaming\\npm\\depwire.cmd",
    "args": ["mcp"],
    "env": {
      "DEPWIRE_NO_TELEMETRY": "1"
    }
  }
}
```

Use verified local repository paths by default. `connect_repo` creates `.depwire/cache.db`; keep `.depwire/` and `depwire-output.json` in the configured global Git excludes file and never commit them. Run `impact_analysis` and `simulate_change` before risky structural changes and `verify_change` before completion. Side-effect-capable tools stay on approval. The reusable setup contract is `docs\prompts\depwire-global-setup-prompt.md`.

## Serena Default Server

Serena is project-scoped semantic code intelligence. It is not the cross-project durable memory layer and it is not a machine-wide singleton for unrelated repositories.

Canonical AgentCore launcher:

```text
C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe
```

Default JSON shape:

```json
{
  "serena": {
    "type": "stdio",
    "command": "C:\\Users\\ynotf\\AppData\\Roaming\\uv\\tools\\serena-agent\\Scripts\\serena.exe",
    "args": [
      "start-mcp-server",
      "--transport",
      "stdio",
      "--context",
      "ide"
    ]
  }
}
```

Codex TOML shape:

```toml
[mcp_servers.serena]
command = "C:\\Users\\ynotf\\AppData\\Roaming\\uv\\tools\\serena-agent\\Scripts\\serena.exe"
args = ["start-mcp-server", "--transport", "stdio", "--context", "codex", "--project-from-cwd"]
```

Context mapping:

- Codex: `codex`, with `--project-from-cwd` when launched from the target repo root.
- Claude Code: `claude-code`, with `--project-from-cwd` when launched from the target repo root.
- Antigravity / Gemini: `antigravity`, with `--project-from-cwd`.
- Cursor, OpenClaw, MiniMax, Mavis, and Open Interpreter: `ide`, without `--project-from-cwd` unless the client launch root is proven.
- Claude Desktop and VS Code: do not add Serena unless a supported MCP surface and code-editing use case are confirmed.
- Trae: removed from this workstation on 2026-07-07; do not configure Serena for Trae unless explicitly reinstalled and promoted.

Forbidden durable Serena launch patterns:

```text
uvx --from git+https://github.com/oraios/serena
git+https://github.com/oraios/serena
--context ide-assistant
```

See `docs\SERENA_CONFIGURATION.md` for full lifecycle, dashboard, and validation policy.

## Native Memory And RAG Servers

Managed IDE renderer defaults now use native local SwarmRecall and SwarmVault where those clients need memory/RAG. `global-memory-gateway` remains a governed memory component for approved AgentCore workflows, but it is retired from the default IDE renderer baseline and must not be reintroduced into managed IDE configs unless the source renderer and validator are intentionally updated first.

Unified rollout rules:

- `swarmrecall` and `swarmvault` use the governed wrapper scripts below, not raw vendored CLIs.
- `SwarmRecall` stays local-only and must not fall back to hosted endpoints.
- `SwarmVault` stays local-first under `F:\AgentCore\agentmemory\swarmvault`.
- Do not add raw Mem0, OpenMemory, hosted Swarm endpoints, direct SQL, or `:65432` as normal-agent MCP routes.
- Do not dual-write memory across tools. Follow the current renderer set and app-specific rule file.

SwarmRecall stdio shape:

```json
{
  "swarmrecall": {
    "type": "stdio",
    "command": "pwsh",
    "args": [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      "D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreSwarmRecall.ps1",
      "-Mode",
      "Mcp"
    ]
  }
}
```

SwarmVault stdio shape:

```json
{
  "swarmvault": {
    "type": "stdio",
    "command": "pwsh",
    "args": [
      "-NoProfile",
      "-ExecutionPolicy",
      "Bypass",
      "-File",
      "D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreSwarmVault.ps1",
      "-Mode",
      "Mcp"
    ]
  }
}
```

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

Required native memory/RAG servers:
- Keep `swarmrecall` and `swarmvault` exactly as defined by `renderers\open-interpreter.config.fragment.json`.
- Use the governed wrapper scripts under `D:\github\agentcore-control-plane\ops\`.
- Do not add `global-memory-gateway` unless the current source renderer explicitly contains it.
- Do not add raw Mem0, OpenMemory, hosted Swarm endpoints, direct SQL, or `:65432` as normal-agent routes.

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
5. Ensure `swarmrecall` and `swarmvault` remain configured from the source renderer and governed wrappers.
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
- Keep the current native memory/RAG baseline from the source authority.
- Do not add `global-memory-gateway` unless the current Codex source authority explicitly contains it.
- Do not add raw Mem0 as a normal-agent memory route.
- Enforce that normal writes go only to `F:\AgentCore` or `E:\AgentCoreArchive`.
- Do not write to `C:`, `D:`, `G:`, `H:`, or `I:` unless the user explicitly instructs that drive for the current task.
- If an approved drive write fails, stop immediately and notify the user; do not silently fall back.

Expected memory/RAG default:
- Preserve source-authorized `swarmrecall` and `swarmvault` entries when present.
- Use governed wrapper scripts, not raw vendored CLIs.
- Keep direct PostgreSQL, raw Mem0, OpenMemory, and hosted Swarm endpoints out of normal-agent MCP routes.

Tasks:
1. Discover the live Codex MCP config path and current config shape.
2. Parse the pasted JSON and identify whether it is a full config, an `mcpServers` fragment, or a single server block.
3. Merge it into the Codex MCP config using the correct schema for Codex.
4. Validate JSON parsing.
5. Validate that the source-authorized native memory/RAG servers still use governed wrapper scripts.
6. Validate that no quarantined normal-agent routes were added.
7. Add or update Codex global rules/instructions so future Codex agents read `D:\MCP-Control-Plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
8. Re-lock managed config files if this host uses read-only drift protection.
9. Report only paths changed, server names added/updated, validation results, backup path, and restart requirement.

Here is the MCP JSON to add:

```json
PASTE_JSON_HERE
```
````

### Cursor / MiniMax / Open Interpreter / Antigravity

These clients use a top-level `mcpServers` object. Copy from the client-specific renderer instead of reconstructing entries by hand.

### OpenClaw

OpenClaw uses `mcp.servers`. Copy from `renderers\openclaw.openclaw.fragment.json`.

## Agent Behavior

After restart, agents can use the currently exposed native memory/RAG tools from `swarmrecall` and `swarmvault`. Agents must not connect directly to PostgreSQL for normal memory work.

Active agent workspaces belong under `F:\AgentCore\agents_workspace`.

Agents do not automatically save every chat token or every file they read. Durable database writes happen when:

- an agent calls an approved memory/RAG MCP tool
- a trusted ingest script writes investigation data
- a task rule explicitly tells the agent to persist compact durable findings

Do not store raw secrets, raw logs, full transcripts, or full source dumps in the vector store.

## Local-Only Native MCPs

These are validated local-only MCPs. SwarmRecall's API and Meilisearch runtime are owned by AgentCore scheduled tasks, and live IDE MCP configs are governed by the source renderers rather than ad hoc per-client edits.

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
- Default IDE exposure: use when present in the client source renderer

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
- Default IDE exposure: use when present in the client source renderer

## MiniMax Notes

This PC has two MiniMax/Mavis MCP config trees:

- New platform: `C:\Users\ynotf\.minimax\mcp\mcp.json`
- Legacy Mavis platform: `C:\Users\ynotf\.mavis\mcp\mcp.json`

Both should be kept aligned with `D:\github\agentcore-control-plane\renderers\minimax.mcp.json`.

The GUI app config at `C:\Users\ynotf\AppData\Roaming\MiniMax Agent\minimax-agent-config.json` may contain account tokens and must not be copied into reports, prompts, or normal artifacts.

## Validation Commands

Drive boundary authority:

`D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`

Source-repo dry-run validation:

```powershell
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\validators\validate-control-plane.ps1
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreEnvPolicy.ps1
powershell -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Test-AgentCoreDepwireIntegration.ps1 -IncludeLiveCodex
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
