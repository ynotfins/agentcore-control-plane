# MASTER_CONFIG_AND_PROMPT.md

## Purpose

Reusable root-level master setup guide for AgentCore MCP configuration, IDE rules, memory routing, SwarmRecall, SwarmVault, Postgres/pgvector, Artiforge, Arabold/Grounded Docs, context-fabric, Serena, sequential-thinking, Obsidian, cursor-agent-mcp, and mcp-debugger.

Use this file in every project root and every IDE setup pass.

Core architecture:

```text
Native SwarmRecall works first.
Native SwarmVault works first.
AgentCore governance wraps proven native behavior.
All IDEs use the same MCP baseline, memory rules, drive policy, and database rules.
Secrets live only in Windows User-scope environment variables.
```

---

## 1. Authority and Runtime Facts

Source authority:

```text
D:\github\agentcore-control-plane
```

Compatibility/live-ops evidence only:

```text
D:\MCP-Control-Plane
```

Drive policy:

```text
C: = OS/apps/live IDE configs only
D: = source repos, project folders, worktrees, evidence
F: = hot local memory/database/RAG/search runtime
E: = archive/cold/backups/exports/spool only
G: = backup only
```

F: allocation policy:

```text
F: is the 3.63 TB hot runtime drive.
Reserve roughly 2 TB logical budget for SwarmVault, SwarmRecall, Meilisearch, and local memory/RAG artifacts.
Use remaining F: capacity for PostgreSQL/pgvector, agent_core, native vector/runtime support, and future Docker bind mounts.
Prefer logical directory budgets over repartitioning.
Do not put primary SQL on E:.
Do not put hot runtime data on C:.
```

Runtime facts:

```text
PostgreSQL:       127.0.0.1:55432
SwarmRecall API:  http://127.0.0.1:3300
SwarmRecall health: http://127.0.0.1:3300/api/v1/health
Meilisearch:      http://127.0.0.1:7700
SwarmVault root:  F:\AgentCore\agentmemory\swarmvault
Projection state: F:\AgentCore\agentmemory\projection-state
Obsidian REST:    https://127.0.0.1:27124
OpenClaw gateway: http://127.0.0.1:18789
```

Forbidden runtime route:

```text
:65432 is retired/stale. Do not use it except in archived/historical evidence.
```

---

## 2. Windows Environment Variables

All API keys, tokens, and secrets must be Windows User-scope environment variables.

Never:

```text
print secret values
create .env files
commit rendered live configs containing secret values
store secrets in docs, reports, logs, or Git
```

Expected variables:


| Variable                         | Purpose                             | Status                       |
| -------------------------------- | ----------------------------------- | ---------------------------- |
| `AGENT_CORE_SWARMRECALL_API_KEY` | Canonical AgentCore SwarmRecall key | Required                     |
| `SWARMRECALL_API_KEY`            | Native SwarmRecall alias            | Required for native clients  |
| `SWARMRECALL_API_URL`            | Native SwarmRecall API URL          | Required                     |
| `ARTIFORGE_PAT`                  | Artiforge Personal Access Token     | Required if Artiforge active |
| `OBSIDIAN_BASE_URL`              | Obsidian REST URL                   | Required if Obsidian active  |
| `OBSIDIAN_VAULT_PATH`            | Obsidian vault path                 | Required if Obsidian active  |
| `GITHUB_PERSONAL_ACCESS_TOKEN`   | GitHub MCP token                    | Optional approved add-on     |
| repo-defined DB env              | AgentCore DB connection             | Governed scripts only        |


Set Artiforge PAT:

```powershell
[Environment]::SetEnvironmentVariable("ARTIFORGE_PAT", "<PASTE_ARTIFORGE_PAT_HERE>", "User")
```

Set native SwarmRecall alias from canonical AgentCore key:

```powershell
$CanonicalName = "AGENT_CORE_SWARMRECALL_API_KEY"
$AliasName = "SWARMRECALL_API_KEY"

$Value = [Environment]::GetEnvironmentVariable($CanonicalName, "User")
if ([string]::IsNullOrWhiteSpace($Value)) { $Value = [Environment]::GetEnvironmentVariable($CanonicalName, "Machine") }
if ([string]::IsNullOrWhiteSpace($Value)) { $Value = $env:AGENT_CORE_SWARMRECALL_API_KEY }
if ([string]::IsNullOrWhiteSpace($Value)) { throw "$CanonicalName is not set in User, Machine, or current process environment." }

[Environment]::SetEnvironmentVariable($AliasName, $Value, "User")
$env:SWARMRECALL_API_KEY = $Value
[Environment]::SetEnvironmentVariable("SWARMRECALL_API_URL", "http://127.0.0.1:3300", "User")
$env:SWARMRECALL_API_URL = "http://127.0.0.1:3300"

Write-Host "$AliasName set from $CanonicalName. Value not printed. Length: $($Value.Length)"
```

Verify without printing secrets:

```powershell
$k = [Environment]::GetEnvironmentVariable("SWARMRECALL_API_KEY", "User")
if ([string]::IsNullOrWhiteSpace($k)) { "SWARMRECALL_API_KEY missing" } else { "SWARMRECALL_API_KEY present. Length: $($k.Length)" }
[Environment]::GetEnvironmentVariable("SWARMRECALL_API_URL", "User")
Invoke-RestMethod -Uri "http://127.0.0.1:3300/api/v1/health" -Method Get
```

---

## 3. Mandatory MCP Baseline

Every managed IDE must converge on this baseline where supported:

```text
arabold-docs
serena
sequential-thinking
cursor-agent-mcp
context-fabric
mcp-debugger
artiforge
global-memory-gateway
obsidian-vault
swarmrecall
swarmvault
```

Optional approved add-ons:

```text
github-mcp
playwright
filesystem only when sandboxed to the intended project roots
```

eye2byte 

Forbidden active MCP routes:

```text
context7
raw mem0
direct composio
Hostinger
hosted SwarmRecall
hosted SwarmVault
direct SQL normal-memory route
:65432 active runtime route
D:\MCP-Control-Plane as design authority
SwarmVault-as-Postgres
SwarmRecall auto-using-SwarmVault-DB
```

---

## 4. Master MCP Config Template for JSON-Based IDEs

Use this as a template, not a blind paste. Agents must inspect the IDE schema first, remove unsupported fields such as `notes`, and merge correctly.

For any server already defined in `D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json`, source-controlled renderers, or validated live configs, prefer the canonical local definition. Do not invent paths.

```json
{
  "mcpServers": {
    "arabold-docs": {
      "type": "sse",
      "url": "http://localhost:6280/sse",
      "notes": "Start local Arabold/Grounded Docs first with: npx @arabold/docs-mcp-server@latest. If the IDE supports only stdio, use a verified wrapper or client-specific setup."
    },
    "serena": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/oraios/serena",
        "serena",
        "start-mcp-server",
        "--context",
        "ide-assistant"
      ],
      "notes": "If workspace substitution is supported, add --project <workspace-root>. Otherwise activate/onboard the project through Serena tools at session start."
    },
    "sequential-thinking": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sequential-thinking"]
    },
    "cursor-agent-mcp": {
      "command": "npx",
      "args": ["-y", "cursor-agent-mcp"]
    },
    "context-fabric": {
      "command": "context-fabric-mcp",
      "args": []
    },
    "mcp-debugger": {
      "command": "npx",
      "args": ["-y", "@debugmcp/mcp-debugger@latest"]
    },
    "artiforge": {
      "type": "http",
      "url": "https://tools.artiforge.ai/mcp?pat=${ARTIFORGE_PAT}",
      "notes": "If this IDE cannot expand env vars in HTTP URLs, render the live app-owned config from ARTIFORGE_PAT without printing the PAT. Never commit the rendered config."
    },
    "global-memory-gateway": {
      "command": "pwsh",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreGlobalMemoryGateway.ps1",
        "-Mode",
        "Mcp"
      ],
      "notes": "VERIFY THIS PATH AGAINST SOURCE AUTHORITY BEFORE WRITING. If missing, resolve from contracts/master-mcp-server-config.json or renderers."
    },
    "obsidian-vault": {
      "command": "pwsh",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "C:\\Users\\ynotf\\.openclaw\\start-obsidian-mcp-server.ps1"
      ],
      "env": {
        "OBSIDIAN_BASE_URL": "${OBSIDIAN_BASE_URL}",
        "OBSIDIAN_VAULT_PATH": "${OBSIDIAN_VAULT_PATH}"
      },
      "notes": "VERIFY wrapper exists. If missing, resolve canonical Obsidian MCP launcher from source-controlled renderers or validated live config."
    },
    "swarmrecall": {
      "command": "pwsh",
      "args": [
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        "D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreSwarmRecall.ps1",
        "-Mode",
        "Mcp"
      ],
      "env": {
        "SWARMRECALL_API_URL": "${SWARMRECALL_API_URL}",
        "SWARMRECALL_API_KEY": "${SWARMRECALL_API_KEY}"
      }
    },
    "swarmvault": {
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
}
```

### Required cleanup during config merge

Remove any active entry pointing to:

```text
C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1
```

That was a broken rogue wrapper path and must not remain active. As of 2026-06-30 the shim at that path has been removed; the canonical launcher is the source-authority `ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` below.

---

## 4a. Verified Canonical Launchers (source authority, 2026-06-30)

These are the launch commands VERIFIED to exist against source authority. They OVERRIDE any divergent entry in the template above. Do not invent paths; use these.

```text
global-memory-gateway  pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreGlobalMemoryGateway.ps1 -Mode Mcp -Platform <ide>
                       (uniform wrapper; sets cwd D:\Codex_Managed and runs the python module; inherits AGENT_CORE_*/OPENAI_API_KEY from Windows env; no env block or cwd needed in the IDE config)
swarmrecall            pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp
swarmvault             pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp
arabold-docs           stdio: node "C:\Users\ynotf\.cursor\vendor\arabold-docs-mcp\node_modules\@arabold\docs-mcp-server\dist\index.js"  (env OPENAI_API_KEY)   [SSE http://localhost:6280/sse only if a client requires SSE]
context-fabric         stdio: node "C:\Users\ynotf\.cursor\vendor\context-fabric-mcp\node_modules\context-fabric\dist\index.js"
serena                 uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant   (or --transport stdio --project-from-cwd)
sequential-thinking    npx.cmd -y @modelcontextprotocol/server-sequential-thinking   (env DISABLE_THOUGHT_LOGGING=true)
cursor-agent-mcp       npx.cmd -y cursor-agent-mcp@latest   (env CURSOR_API_KEY, CURSOR_API_URL=https://api.cursor.com)
mcp-debugger           npx.cmd -y @debugmcp/mcp-debugger@latest
artiforge              http url https://tools.artiforge.ai/mcp?pat=${env:ARTIFORGE_PAT}  (if the IDE cannot expand env in URLs, render live from ARTIFORGE_PAT without printing/committing)
obsidian-vault         pwsh -NoProfile -NonInteractive -File C:\Users\ynotf\.openclaw\start-obsidian-mcp-server.ps1  (env OBSIDIAN_API_KEY, OBSIDIAN_LOCAL_REST_API, OBSIDIAN_BASE_URL=https://127.0.0.1:27124, OBSIDIAN_VERIFY_SSL=false)
```

Servers whose canonical launcher could NOT be verified from source authority: none as of 2026-06-30 (the previously-missing `Invoke-AgentCoreGlobalMemoryGateway.ps1` has been created in `ops\`).

### System state note (2026-06-30)

```text
- Native Postgres agent_core on F: 127.0.0.1:55432 is canonical (F:\AgentCore\database_cluster).
- Docker legacy n8n stack RETIRED: containers local-agent-stack-n8n-1 + local-agent-stack-postgres-1 and their
  volumes (local-agent-stack_n8n_data, local-agent-stack_postgres_data) removed after verified tar backup to
  G:\DockerLegacyRetire-<stamp>\ (rollback manifest included). n8n/Qdrant/n8n-Postgres are NOT canonical AgentCore.
- agentops-qdrant is not present. Exited devcontainer-* (Frappe/redis/mariadb) left untouched (out of scope).
- E: (external archive USB) is currently UNMOUNTED. Backup/WAL targets that point at E:\AgentCoreArchive will fail
  until E: is reconnected. Use G: as the available backup tier meanwhile.
```

---

## 5. Codex TOML Baseline

Codex usually uses:

```text
C:\Users\ynotf\.codex\config.toml
```

Do not paste JSON into Codex. Merge TOML correctly and preserve existing Codex model/sandbox/profile settings.

```toml
[mcp_servers.swarmrecall]
command = "pwsh"
args = [
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  "D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreSwarmRecall.ps1",
  "-Mode",
  "Mcp"
]

[mcp_servers.swarmvault]
command = "pwsh"
args = [
  "-NoProfile",
  "-ExecutionPolicy",
  "Bypass",
  "-File",
  "D:\\github\\agentcore-control-plane\\ops\\Invoke-AgentCoreSwarmVault.ps1",
  "-Mode",
  "Mcp"
]

[mcp_servers.sequential-thinking]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-sequential-thinking"]

[mcp_servers.cursor-agent-mcp]
command = "npx"
args = ["-y", "cursor-agent-mcp"]

[mcp_servers.context-fabric]
command = "context-fabric-mcp"
args = []

[mcp_servers.mcp-debugger]
command = "npx"
args = ["-y", "@debugmcp/mcp-debugger@latest"]

[mcp_servers.serena]
command = "uvx"
args = [
  "--from",
  "git+https://github.com/oraios/serena",
  "serena",
  "start-mcp-server",
  "--context",
  "ide-assistant"
]
```

Artiforge and Arabold/Grounded Docs are HTTP/SSE servers. Add them to Codex only if the installed Codex MCP client supports HTTP/SSE server definitions. If not, mark them unsupported for Codex rather than inventing a fake stdio command.

---

## 6. Master Prompt for IDE Agents

Paste this into the local IDE agent when setting up or repairing any IDE MCP config.

```text
You are configuring this IDE for the AgentCore native-first MCP baseline on CHAOSCENTRAL.

Use MASTER_CONFIG_AND_PROMPT.md as the controlling setup guide.

Source authority:
D:\github\agentcore-control-plane

Do not blindly paste config. Inspect this IDE's actual MCP config schema, active config path, and existing working servers. Merge the baseline correctly.

Back up the live config before editing.
Preserve auth/session/profile state.
Never print secrets.
Use Windows User-scope environment variables for all API keys and tokens.
Do not create .env files.
Do not commit rendered live configs containing secrets.
Validate syntax after editing.
Restart/reload the IDE after editing.

Required MCP baseline:
- arabold-docs
- serena
- sequential-thinking
- cursor-agent-mcp
- context-fabric
- mcp-debugger
- artiforge
- global-memory-gateway
- obsidian-vault
- swarmrecall
- swarmvault

Required Swarm launchers:
swarmrecall:
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp

swarmvault:
pwsh -NoProfile -ExecutionPolicy Bypass -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp

Remove broken rogue SwarmVault wrapper path if present:
C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1

Artiforge:
Use official HTTP MCP endpoint:
https://tools.artiforge.ai/mcp?pat=<ARTIFORGE_PAT>
Use ARTIFORGE_PAT from Windows User env. If the IDE supports env expansion, use ${ARTIFORGE_PAT}. If not, render the live app-owned config from Windows env without printing the PAT and never commit that rendered config.

Arabold/Grounded Docs:
Use local Arabold/Grounded Docs for version-matched docs. Preferred server mode:
npx @arabold/docs-mcp-server@latest
SSE URL:
http://localhost:6280/sse
If this IDE only supports stdio and no verified wrapper exists, report unsupported instead of inventing a fake command.

Forbidden active routes:
- context7
- raw mem0
- direct composio
- Hostinger
- hosted SwarmRecall
- hosted SwarmVault
- direct SQL normal-memory route
- :65432 active runtime route
- D:\MCP-Control-Plane as design authority
- SwarmVault-as-Postgres
- SwarmRecall auto-using-SwarmVault-DB

Drive policy:
- C: live app configs only
- D: source/repos/projects/worktrees/evidence
- F: hot local memory/database/RAG/search runtime
- E: archive/cold/backups/exports/spool only
- G: backup only

Database policy:
- PostgreSQL is 127.0.0.1:55432
- agent_core and swarmrecall are separate DBs
- pgvector belongs on the F: hot tier through the local Postgres cluster
- normal agents must not raw-SQL into agent_core or swarmrecall
- current gateway tools are memory_append, memory_search, memory_state
- agentcore_* tools are future/target unless implemented and validated
- memory_catalog is future/post-migration unless DB and repo prove it exists

Memory policy:
- At session start, load PROJECT_ANCHOR.md and DOC_AUTHORITY.md if present.
- Identify the project root on D:.
- Use global-memory-gateway memory_state and memory_search for governed AgentCore memory context.
- Use native SwarmRecall for memory recall, semantic search, knowledge graph, learnings, skills, pools, and current memory.
- Use native SwarmVault for project RAG/wiki/graph/context packs/source retrieval/task ledger.
- Use Obsidian only through MCP/REST for durable human-readable notes, decisions, and project docs.
- Do not dual-write memory.
- Do not direct-write F:\AgentCore\agentmemory except through approved SwarmRecall/SwarmVault/AgentCore tools.
- Store durable machine memory through global-memory-gateway unless the task explicitly requires native SwarmRecall/SwarmVault storage.

Documentation policy:
- Before adding/changing a third-party package/API/framework, inspect manifests and lockfiles.
- Use arabold-docs/Grounded Docs to fetch and index exact version-matched documentation.
- Save a project-local docs manifest at .agentcore/docs/DOCS_INDEX.md.
- The manifest must list package/API name, version, docs source, local index status, date/time, and query used.
- Do not rely on model memory for current APIs.

Serena policy:
- Use Serena for semantic code navigation before broad edits.
- Perform Serena onboarding/activation at project start if needed.
- Prefer get_symbols_overview/find_symbol/find_referencing_symbols over raw grep for code structure.
- Use Serena memory only for project-scoped code intelligence, not primary cross-project memory.

Sequential-thinking policy:
- Use sequential-thinking before architecture changes, multi-file refactors, DB schema decisions, migrations, and complex debugging.
- Keep it concise and tied to acceptance checks.

Context-fabric policy:
- Initialize context-fabric for each project if missing.
- Use context-fabric at session start, before high-risk multi-file edits, after large changes, after repair/bootstrap, and whenever drift is suspected.
- If context-fabric reports drift, stop edits, resync with physical repo state, then continue.

MCP-debugger policy:
- On runtime exceptions, test failures, or unexplained behavior, do not guess.
- Use mcp-debugger to attach/inspect where supported, set breakpoints before failure path, inspect state, then edit.

Artiforge policy:
- Use Artiforge for complex implementation, refactors, module creation, docs generation, and multi-file coordination.
- Start Artiforge tasks with:
  use Artiforge tool to do this task:
- Include integrations, technical requirements, constraints, acceptance checks, and expected outcome.
- Review the Artiforge execution plan before allowing broad changes.
- Use high-reasoning/thinking models where available.
- Trust Artiforge to load codebase context; do not manually dump huge files unless it asks for a missing artifact.

cursor-agent-mcp policy:
- Use cursor-agent-mcp to coordinate Cursor agent capabilities and cross-agent orchestration where supported.
- Do not let it bypass memory, drive, DB, secret, or Git rules.

Obsidian policy:
- Use Obsidian for durable human-readable notes, architecture decisions, handoffs, and high-level knowledge.
- Do not use Obsidian as raw runtime memory DB.
- Prefer storing machine-retrievable memory through global-memory-gateway/SwarmRecall/SwarmVault.

Git policy:
- Normal GitHub origins are allowed.
- Do not pull/fetch/merge/rebase unless the user explicitly asks.
- Commit/push only after validation and secret/junk scan.
- Never commit live secret-bearing configs, rendered PAT URLs, DB dumps, caches, node_modules, or runtime artifacts.

Validation after setup:
- Config syntax valid.
- MCP discovery shows all required servers or exact unsupported blockers.
- swarmrecall, swarmvault, artiforge, arabold-docs, serena, sequential-thinking, context-fabric, mcp-debugger, cursor-agent-mcp, obsidian-vault, and global-memory-gateway discoverable where supported.
- No broken swarmvault wrapper path remains.
- No forbidden active route remains.

Final report:
- active config path
- backup path
- servers added/updated/removed
- env vars required/missing, names only
- syntax validation result
- MCP discovery result
- restart/reload requirement
- unresolved blockers
```

---

## 7. IDE Config Paths

Cursor:

```text
C:\Users\ynotf\.cursor\mcp.json
```

Codex:

```text
C:\Users\ynotf\.codex\config.toml
```

Claude Code:

```text
C:\Users\ynotf\.claude.json
C:\Users\ynotf\.claude\config.json
```

OpenClaw:

```text
C:\Users\ynotf\.openclaw\openclaw.json
```

MiniMax:

```text
C:\Users\ynotf\.minimax\mcp\mcp.json
```

Mavis:

```text
C:\Users\ynotf\.mavis\mcp\mcp.json
```

Antigravity:

```text
C:\Users\ynotf\.gemini\config\mcp_config.json
C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json
```

Open Interpreter:

```text
C:\Users\ynotf\AppData\Roaming\interpreter\config.json
```

Claude Desktop / Obsidian remediation:

```text
C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json
```

---

## 8. Project Startup Ritual

At the start of every project session:

```text
1. Identify the project root, usually D:\github\<repo>.
2. Read PROJECT_ANCHOR.md and DOC_AUTHORITY.md if present.
3. Read AGENTS.md, CLAUDE.md, .cursorrules, and .cursor/rules if present. If AGENTS.md or CLAUDE.md is MISSING at the project root, CREATE it (seed from the Root Agent Rules Template in section 19) before proceeding, and re-verify/update both regularly as project rules or wiring change.
4. Inspect manifests and lockfiles.
5. Query global-memory-gateway memory_state and memory_search for project/task context.
6. Query SwarmRecall native memory/search/learnings/skills/current memory.
7. Query SwarmVault context pack/wiki/graph/source retrieval/task ledger.
8. Check Obsidian for project handoff/architecture notes if relevant.
9. Use Serena onboarding/activation for project code intelligence.
10. Use context-fabric before multi-file changes or whenever drift is suspected.
11. Use arabold-docs/Grounded Docs for exact version docs before API/framework work.
12. Build a short plan with acceptance checks.
13. Execute, validate, and store durable memory through approved routes.
```

Manifests/lockfiles to inspect when present:

```text
package.json
pnpm-lock.yaml
package-lock.json
yarn.lock
pyproject.toml
uv.lock
poetry.lock
requirements.txt
Cargo.toml
go.mod
pom.xml
build.gradle
Dockerfile
compose files
```

---

## 9. Local Documentation Lifecycle

Fetch/index docs when:

```text
adding a dependency
upgrading a package
using a framework feature that may have changed
integrating a third-party API
debugging an API behavior mismatch
writing generated code against unfamiliar libraries
```

Preferred tool:

```text
arabold-docs / Grounded Docs
```

Fallback:

```text
official vendor docs only
```

Forbidden:

```text
guessing from model memory for APIs that could have changed
```

Required per-project docs manifest:

```text
.agentcore/docs/DOCS_INDEX.md
```

Template:

```markdown
# Project Docs Index

| Name | Type | Version | Source | Local index status | Last refreshed | Notes |
|---|---|---:|---|---|---|---|
| example-lib | npm | 1.2.3 | official docs URL | indexed in arabold-docs | 2026-06-30 | used for feature X |
```

---

## 10. Memory and Context Routing


| System                | Purpose                                                  | Write route                      |
| --------------------- | -------------------------------------------------------- | -------------------------------- |
| global-memory-gateway | Governed AgentCore memory broker                         | `memory_append`                  |
| agent_core DB         | AgentCore governance/catalog/policy state                | governed scripts/migrations only |
| swarmrecall DB        | Native SwarmRecall state                                 | native SwarmRecall service/tools |
| SwarmRecall MCP/API   | semantic recall, memory, graph, learnings, skills, pools | native tools                     |
| SwarmVault            | local-first project RAG/wiki/graph/context/task ledger   | native tools                     |
| Obsidian              | human-readable durable notes/handoffs                    | Obsidian MCP/REST only           |
| Postgres/pgvector     | local vector persistence for approved systems            | service-owned only               |


Normal agents may read through:

```text
global-memory-gateway.memory_search
global-memory-gateway.memory_state
SwarmRecall search/current memory/learnings/skills/pools
SwarmVault context packs/wiki/graph/source retrieval
Obsidian notes when relevant
```

Normal agents must not:

```text
raw-SQL into agent_core
raw-SQL into swarmrecall
dual-write the same memory to multiple stores
write directly to F:\AgentCore\agentmemory
write directly to active Obsidian vault files
treat SwarmVault as Postgres
treat SwarmRecall as auto-using SwarmVault DB
```

Saving guidance:

```text
Project-specific code fact -> SwarmVault task/context or project docs
User/system preference -> global-memory-gateway memory_append
Architecture decision -> Obsidian note plus gateway summary if it affects agent behavior
Dependency/API docs -> arabold-docs local index plus .agentcore/docs/DOCS_INDEX.md
Debugging lesson/failure pattern -> gateway memory_append and SwarmRecall learning if appropriate
```

---

## 11. Postgres / pgvector Rules

Database topology:

```text
PostgreSQL cluster: 127.0.0.1:55432
agent_core DB: governed AgentCore metadata/policy/catalog
swarmrecall DB: native SwarmRecall state
pgvector: local vector support on F: hot tier
```

Normal IDE agents must not:

```text
connect directly to Postgres for memory work
create ad hoc memory tables
apply migrations without migration protocol
point anything at :65432
move primary SQL to E:
```

Migration protocol:

```text
1. Backup.
2. Restore verification.
3. Dry-run with ROLLBACK.
4. Down migration verification.
5. Apply.
6. Post-checks.
7. Rollback plan.
8. Report.
```

`memory_catalog` and `agentcore_*` tools are target/post-migration unless live DB and source prove they exist.

---

## 12. SwarmRecall Rules

SwarmRecall is native-first.

Proof of health:

```text
http://127.0.0.1:3300/api/v1/health
MCP tool discovery
memory/search/list
knowledge graph
learnings
skills
pools
current/session memory where supported
```

Policy:

```text
AGENT_CORE_SWARMRECALL_API_KEY remains canonical.
SWARMRECALL_API_KEY is native compatibility alias.
SWARMRECALL_API_URL=http://127.0.0.1:3300.
Keep swarmrecall DB separate from agent_core.
No hosted fallback.
Do not collapse SwarmRecall into SwarmVault.
```

---

## 13. SwarmVault Rules

SwarmVault is native-first and file-based.

Proof of health:

```text
doctor
status
retrieval status
graph stats
context build
query with timeout
task ledger
MCP discovery
```

Always exclude from source registration:

```text
node_modules
.next
dist
build
coverage
.git
generated artifacts
caches
venv
.venv
__pycache__
large binary dumps
DB backups
```

Policy:

```text
SwarmVault root stays at F:\AgentCore\agentmemory\swarmvault.
Do not force SwarmVault into Postgres.
Do not delete valid sources without approval or proof of corruption.
Full query must be timeout-bounded.
If full query is slow, report BLOCKED with evidence, not a hang.
```

---

## 14. Artiforge Rules

Artiforge official HTTP MCP pattern:

```json
{
  "mcpServers": {
    "artiforge": {
      "type": "http",
      "url": "https://tools.artiforge.ai/mcp?pat=${ARTIFORGE_PAT}"
    }
  }
}
```

If the IDE cannot expand `${ARTIFORGE_PAT}`:

```text
Read ARTIFORGE_PAT from Windows User env.
Render the live app-owned config without printing the value.
Do not commit that rendered config.
```

Use Artiforge for:

```text
complex implementation
multi-file refactors
module creation
architecture changes
documentation generation
large test harness creation
cross-service integrations
```

Required task prefix:

```text
use Artiforge tool to do this task:
```

Required prompt structure:

```text
use Artiforge tool to do this task:

Goal:
<final end state>

Project context:
<project root, stack, relevant services>

Integrations:
<existing services/modules this must use>

Technical requirements:
<frameworks, protocols, DBs, APIs>

Constraints:
<memory/drive/security/git rules>

Acceptance checks:
<tests, validations, runtime checks>

Output:
<what to change/report>
```

Operating rules:

```text
Use Agent mode.
Use high-reasoning/thinking models where available.
Review the execution plan before broad edits.
Be specific about integrations and technical requirements.
Trust Artiforge to load codebase context; do not manually paste huge context unless it asks for a missing artifact.
```

---

## 15. Arabold / Grounded Docs Rules

Arabold/Grounded Docs replaces Context7 for local, version-matched documentation.

Preferred setup:

```powershell
npx @arabold/docs-mcp-server@latest
```

Local UI:

```text
http://localhost:6280
```

SSE client config:

```json
{
  "mcpServers": {
    "arabold-docs": {
      "type": "sse",
      "url": "http://localhost:6280/sse"
    }
  }
}
```

Documentation rule:

```text
1. Inspect manifest and lockfile.
2. Resolve exact version.
3. Fetch/index official docs with arabold-docs/Grounded Docs.
4. Save/update .agentcore/docs/DOCS_INDEX.md.
5. Use indexed docs before writing code.
```

---

## 16. Tool Use Rules

### Serena

Preferred command:

```text
uvx --from git+https://github.com/oraios/serena serena start-mcp-server --context ide-assistant
```

Use Serena for onboarding/activation, symbol overview, symbol references, code architecture, and safe symbol-level edits.

### Sequential-thinking

Use before architecture decisions, multi-file changes, DB/migration decisions, tooling changes, debugging strategy, and risk analysis.

### Context-fabric

Setup:

```powershell
pip install context-fabric
context-fabric init
```

MCP command:

```text
context-fabric-mcp
```

Use at session start, before high-risk multi-file changes, after repair/bootstrap, after large changes, when drift is suspected, and before handoff if context is high.

### MCP-debugger

Setup:

```text
npx -y @debugmcp/mcp-debugger@latest
```

On runtime/test failures, do not guess. Attach/inspect where supported, set breakpoints, inspect state, patch root cause, rerun narrow test.

### cursor-agent-mcp

Setup:

```text
npx -y cursor-agent-mcp
```

Use for Cursor agent orchestration, repo analysis, planning, code search, and delegated Cursor tasks. It cannot bypass this file's memory/drive/DB/secret/Git rules.

### Obsidian

Use Obsidian for human-readable architecture decisions, handoffs, runbooks, and durable project knowledge. Do not use it as raw runtime memory storage.

---

## 17. MCP Verification Prompt

Run this after setup in each IDE:

```text
Run MCP discovery and baseline validation.

Check these servers:
- arabold-docs
- serena
- sequential-thinking
- cursor-agent-mcp
- context-fabric
- mcp-debugger
- artiforge
- global-memory-gateway
- obsidian-vault
- swarmrecall
- swarmvault

For each, report:
- connected yes/no
- transport type
- tool count if available
- first useful tool name if available
- exact error if failed

Then verify:
- no context7 active
- no raw mem0 active
- no direct composio active
- no Hostinger active
- no hosted SwarmRecall/SwarmVault
- no :65432 active route
- no broken SwarmVault wrapper path

Do not print secrets.
Do not create .env files.
Report exact config path and restart requirement.
```

---

## 18. Cursor Prompt to Configure Claude Code Locally

Use this in Cursor when Claude chat cannot edit local Windows files:

```text
Configure Claude Code MCP baseline locally.

Candidate files:
C:\Users\ynotf\.claude.json
C:\Users\ynotf\.claude\config.json

Use MASTER_CONFIG_AND_PROMPT.md as controlling setup guide.

Tasks:
1. Discover which Claude Code config is active.
2. Back up both files if present.
3. Preserve auth/session/profile state.
4. Merge mandatory MCP baseline.
5. Use exact Swarm launchers from MASTER_CONFIG_AND_PROMPT.md.
6. Remove active context7 and Hostinger unless explicitly quarantined/disabled.
7. If CONTEXT7_API_KEY or any plaintext secret is present, do not print it. Replace with env reference where supported or report only field path.
8. Validate JSON.
9. Report backup path, changed file, MCP servers changed, and restart requirement.
```

---

## 19. Root Agent Rules Template

Copy into `AGENTS.md`, `.cursorrules`, `CLAUDE.md`, or IDE-specific rule files when needed:

```markdown
# AgentCore Native-First Operating Rules

D:\github\agentcore-control-plane is source authority.
D:\MCP-Control-Plane is compatibility/live-ops evidence only.

On every new project/repo, create AGENTS.md and CLAUDE.md at the project root if missing (seed from this template), read/verify both at session start, and keep them updated as rules or wiring change.

SwarmRecall and SwarmVault must work natively first.
AgentCore governance wrappers, renderers, projectors, validators, memory_catalog, and cross-IDE enforcement wrap proven native behavior.

Use global-memory-gateway for governed memory: memory_append, memory_search, memory_state.
Use SwarmRecall for native memory/search/graph/learnings/skills/pools.
Use SwarmVault for native RAG/wiki/graph/context-pack/task-ledger/source retrieval.
Use Obsidian for human-readable notes/handoffs only.
Do not raw-SQL memory DBs.
Do not dual-write.
Do not direct-write F:\AgentCore\agentmemory.

Use arabold-docs/Grounded Docs for exact version docs.
Save docs manifest to .agentcore/docs/DOCS_INDEX.md.
Do not use model memory for current APIs.

Use Serena before broad code edits.
Use sequential-thinking before architecture/migration/refactor decisions.
Use context-fabric at session start, before high-risk multi-file changes, after repairs, and when drift is suspected.
Use mcp-debugger for runtime/test failures instead of guessing.
Use Artiforge for complex multi-file work with: use Artiforge tool to do this task:

C: app/live config only.
D: repos/projects/evidence.
F: hot memory/database/RAG/search.
E: archive/cold/spool only.
G: backup only.

Postgres: 127.0.0.1:55432.
agent_core and swarmrecall remain separate DBs.
pgvector stays on local F: hot tier.
Migrations require backup, restore verification, rollback dry-run, down verification, apply, post-checks, and rollback plan.
memory_catalog and agentcore_* are target/post-migration unless proven.

No pull/fetch/merge/rebase unless user explicitly asks.
Commit/push only after validation and secret/junk scan.
Never commit secrets, rendered PAT URLs, DB dumps, caches, node_modules, runtime artifacts.
```

---

## 20. Docker to F: Policy

Docker hot data should move to F: bind mounts only after safe inventory and backup.

Required sequence:

```text
1. Confirm Docker daemon running.
2. Inventory containers, volumes, compose files.
3. Identify hot data: n8n, Qdrant, Postgres-like volumes, caches.
4. Export/backup current volumes.
5. Stop only affected containers.
6. Create F: bind-mount directories.
7. Update compose files.
8. Start and verify.
9. Document rollback.
```

Do not move Docker blindly. Do not lose n8n or Qdrant data.

---

## 21. Final Setup Checklist

```text
[ ] Config backed up.
[ ] Config syntax valid.
[ ] Required MCP baseline present or exact unsupported blockers documented.
[ ] swarmrecall points to canonical AgentCore launcher.
[ ] swarmvault points to canonical AgentCore launcher.
[ ] broken rogue swarmvault wrapper path absent.
[ ] Artiforge configured with env-backed PAT or documented unsupported.
[ ] Arabold/Grounded Docs configured as local SSE or documented unsupported.
[ ] Serena configured and project onboarding rule installed.
[ ] Sequential-thinking configured.
[ ] Context-fabric configured and drift rules installed.
[ ] MCP-debugger configured.
[ ] cursor-agent-mcp configured.
[ ] Obsidian configured through MCP/REST only.
[ ] global-memory-gateway configured from source authority.
[ ] no forbidden active routes remain.
[ ] no secrets printed or committed.
[ ] IDE restarted/reloaded.
[ ] MCP discovery verified.
```

---

## 22. Local Source Files Agents Must Verify

```text
D:\github\agentcore-control-plane\PROJECT_ANCHOR.md
D:\github\agentcore-control-plane\DOC_AUTHORITY.md
D:\github\agentcore-control-plane\database-plan.md
D:\github\agentcore-control-plane\CONTEXT_BLOCK_AGENTCORE_SWARM_2026-06-30.md
D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json
D:\github\agentcore-control-plane\renderers\
D:\github\agentcore-control-plane\ops\
```

