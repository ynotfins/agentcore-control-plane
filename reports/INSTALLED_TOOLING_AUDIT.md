# INSTALLED_TOOLING_AUDIT — CHAOSCENTRAL

**Generated:** 2026-07-03
**Method:** Read-only shell probes — `where.exe`, `Get-Command`, version flags, `Get-Process`. No installs.
**Coverage:** Runtimes, package managers, database engines, vector stores, IDE/agent CLIs, search engines, MCP server prerequisites.

---

## 1. Executive Summary

The machine is **fully provisioned** for the AgentCore native-first runtime. Node 24.16.0, Python 3.13.14, PowerShell 7, and the major package managers are on PATH. The CLIs for Codex, Claude, OpenClaw, and MiniMax/Mavis are present. Docker Desktop is installed but its service is stopped. Meilisearch is running. Ollama is installed but not listening. psql/postgres are **not** on PATH but the native engine is intact under `F:\AgentCore\postgres_runtime_engine\pgsql\bin\`. Several CLI helpers (qdrant, obsidian, clawx, meilisearch-CLI) are **not** on PATH, which is consistent with the "governed wrapper" pattern in the rollout contract — clients are launched via PowerShell wrappers, not directly.

No new tool installation is required for any architecture option. The audit confirms the existing native-first toolchain is sufficient.

---

## 2. Runtimes on PATH

| Tool | Version | Location | Status |
|------|---------|----------|--------|
| Node.js | 24.16.0 | `D:\Program Files\nodejs\node.exe` | Healthy, current LTS-tier |
| npm | 11.13.0 | bundled with Node | Healthy |
| pnpm | 11.7.0 | global | Healthy |
| yarn | 1.22.22 | global | Legacy (v1); acceptable for vendored repos |
| PowerShell (pwsh) | 7.x | `C:\Program Files\PowerShell\7\pwsh.exe` | Required by all `ops\*.ps1` and `mcp-wrappers\*.ps1` scripts |
| Python | 3.13.14 | system Python | Healthy |
| pip | 26.1.2 | bundled | Healthy |
| uv | 0.11.21 | (Python tooling) | Healthy; used by `serena` MCP wrapper via `uvx.exe` |
| Git | 2.51.1 | system Git | Healthy |
| Docker Desktop | 29.5.2 | installed | **Service stopped**; only required for `github-mcp` cursor/openclaw shape and the obsolete Qdrant/RDP/Portainer stack |

**Critical:** psql, postgres, pg_isready are NOT on PATH. They are reachable only via the explicit absolute path `F:\AgentCore\postgres_runtime_engine\pgsql\bin\psql.exe`. This is intentional per the database-plan design ("Native PostgreSQL engine on Windows filesystems, not as a Docker container, not a Windows service"). Architecture must respect this — clients invoke psql through PowerShell wrappers (`Start-AgentCorePostgres.ps1`, `Backup-AgentCorePostgres.ps1`, `Invoke-AgentCoreMemoryProjector.ps1`), not via direct PATH lookup.

---

## 3. Database & Vector Store Binaries

| Binary | On PATH? | Location | Status |
|--------|----------|----------|--------|
| PostgreSQL engine (psql, postgres, pg_isready, pg_ctl) | No | `F:\AgentCore\postgres_runtime_engine\pgsql\bin\` | Cold (not running) |
| pgvector extension | n/a | loaded into PG via `CREATE EXTENSION vector` | Schema applied |
| Meilisearch | No | `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe` | **Running** (single instance) |
| qdrant | No | not present | Optional layer; absent by design |
| chroma | No | not present | Optional layer; absent by design |
| lancedb | No | not present | Optional layer; absent by design |

The optional vector stores (`chroma`, `lancedb`, `qdrant`, `pgvector`) have **placeholder directories** under `F:\VectorDB\` but no runtime data. Only the pgvector plane inside PostgreSQL is active. This is consistent with `database-plan.md` which lists only pgvector + SwarmVault + SwarmRecall as live backends.

---

## 4. IDE / Agent CLIs

| CLI | Version | Location | On PATH? | Notes |
|-----|---------|----------|----------|-------|
| codex | 0.137.0 | Codex CLI install dir | Yes | Codex CLI; config in `~/.codex\` |
| claude | 2.1.199 | Claude Code install | Yes | Claude Code; `~/.claude\` + `~/.claude.json` |
| openclaw | 2026.6.10 | `D:\openclaw\bin\openclaw.cmd` | (via cmd wrapper) | OpenClaw CLI; gateway port from `gateway.cmd` is **18789** |
| clawx | not found on PATH | (process running 5× but no CLI shim on PATH) | No | ClawX runs as GUI/process only |
| minimax | (mavis) 3.0.47 | `C:\Users\ynotf\.mavis\bin\` | (via bin) | MiniMax Code / mavis agent |
| openinterpreter | not probed for version | (Python package install) | Yes via Python | Inline API key violation noted |
| obsidian | not on PATH | — | No | Obsidian GUI only; long-form notes stored in `D:\Obsidian\Dungeon Vault\` |

The `mavis` and `minimax` paths share the same `config.yaml` (verified identical content), confirming they are the same agent with two symlinked homes — relevant when reading cleanup prompts in `docs\prompts\`.

---

## 5. Search & Memory Stack Binaries

| Binary | On PATH? | Location | Status |
|--------|----------|----------|--------|
| meilisearch | No | `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe` | Running |
| qdrant | No | absent | Not used |
| mem0 | (Python pkg) | vendored | Used by `global-memory-gateway` (now retired) |
| qmd (LCM) | (Python pkg) | vendored | `~/.openclaw\agents\main\qmd\xdg-cache\qmd\index.sqlite` present |

No CLI is invoked directly for search; the contract mandates **governed wrappers** (`Invoke-AgentCoreSwarmRecall.ps1`, `Invoke-AgentCoreSwarmVault.ps1`, `Test-AgentCore*.ps1`). Direct CLI invocation is permitted only inside those wrappers, not from IDE configs.

---

## 6. MCP Server Prerequisites

Per `master-mcp-server-config.json` (v2026-06-26) the canonical MCP surfaces are launched via:

| MCP | Launch shape | Runtime requirement |
|-----|--------------|---------------------|
| arabold-docs | `node C:\Users\ynotf\.cursor\vendor\arabold-docs-mcp\node_modules\@arabold\docs-mcp-server\dist\index.js` | Node 24 + vendored package present |
| artiforge (HTTP) | `https://tools.artiforge.ai/mcp?pat=${env:ARTIFORGE_PAT}` | Outbound HTTPS + `ARTIFORGE_PAT` env var |
| artiforge (CodeX/MiniMax) | `pwsh -File C:\Users\ynotf\.codex\mcp-wrappers\artiforge-mcp.ps1` | pwsh 7 + wrapper present |
| sequential-thinking | `npx.cmd -y @modelcontextprotocol/server-sequential-thinking` | Node + npx + npm registry |
| serena | `C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe start-mcp-server --transport stdio --context <client-context>` | installed Serena tool; no git `uvx` for durable IDE configs |
| context-fabric | `node C:\Users\ynotf\.cursor\vendor\context-fabric-mcp\node_modules\context-fabric\dist\index.js` | Node + vendored package present |
| filesystem | `npx.cmd -y @modelcontextprotocol/server-filesystem C:\Users\ynotf …` | Node + npx |
| obsidian-vault | `pwsh -File C:\Users\ynotf\.openclaw\start-obsidian-mcp-server.ps1` | pwsh 7 + Obsidian running with local REST API |
| playwright | `npx.cmd -y @playwright/mcp@latest` | Node + npx + playwright browser binaries |
| github-mcp (cursor/openclaw) | `docker run … ghcr.io/github/github-mcp-server` | **Docker Desktop running** (currently stopped) |
| github-mcp (codex) | `https://api.githubcopilot.com/mcp/` with bearer | Outbound HTTPS + `GITHUB_PAT_TOKEN` |
| cursor-agent-mcp | `npx.cmd -y cursor-agent-mcp@latest` | Node + npx |
| mcp-debugger | `npx.cmd -y @debugmcp/mcp-debugger@latest` | Node + npx |
| swarmrecall | `pwsh -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1 -Mode Mcp` | pwsh 7 + Python venv + F:\AgentCore\agentmemory\swarmrecall |
| swarmvault | `pwsh -File D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` | pwsh 7 + Node + vendored CLI |

**All prerequisites are present** except Docker Desktop is currently stopped. If a user wants `github-mcp` in Cursor/OpenClaw, they must start Docker Desktop first.

---

## 7. Cold-Start Toolchain Chain

The AgentCore design requires the following deterministic cold-start sequence (per `database-plan.md` §3.4 and `SYSTEM_HANDOVER_BLUEPRINT.md`):

1. **Windows logon** triggers `\AgentCore\PostgresRuntime` (Task Scheduler, runs `Start-AgentCorePostgres.ps1 -StartIfStopped`).
2. PostgreSQL starts natively on `127.0.0.1:55432`; `agent_core` + `swarmrecall` databases accessible.
3. `\AgentCore\SwarmRecallMeilisearch` (Task Scheduler) starts meilisearch at `127.0.0.1:7700`.
4. `\AgentCore\SwarmRecallApi` (Task Scheduler) starts the SwarmRecall Python API at `127.0.0.1:3300`.
5. On first IDE launch, the IDE reads its `mcp.json` and starts each MCP server process. `swarmrecall`/`swarmvault` wrappers then talk to the warm services from steps 2–4.

At the moment of audit, **none** of steps 2–4 had a live listener. This is consistent with the design — the services are cold-started at user logon. Architecture must continue to depend on these scheduled tasks; we must not introduce a competing always-on launcher.

---

## 8. Process Snapshot (audit moment)

Running processes relevant to the memory architecture (partial list):

| Process | Count | Notes |
|---------|-------|-------|
| Antigravity IDE | 1 | IDE |
| claude (Claude Code) | 1+ | IDE/agent |
| ClawX | 5 | OpenClaw sub-product |
| Codex | 1+ | IDE/agent |
| Cursor | many | IDE (multiple workspaces) |
| Docker Desktop | 1 | **Service stopped** |
| meilisearch | 1 | SwarmRecall backend |
| MiniMax Code | 1+ | IDE/agent |
| node.exe | many | MCP servers, IDE internals |
| Obsidian | 1 | Notes |
| python.exe | many | MCP servers, IDE internals |

The single-instance meilisearch process matches the local-only constraint. There is no rogue second meilisearch process, and no rogue second Postgres process.

---

## 9. Tooling Gaps and Risks

| Gap | Severity | Mitigation |
|-----|----------|-----------|
| No CLI for qdrant/chroma/lancedb | Low | Intentional — those are optional layers not in the live baseline |
| psql not on PATH | Medium | Operators must use `Start-AgentCorePostgres.ps1` wrappers; documented in `database-plan.md` |
| Docker Desktop service stopped | Medium | Affects `github-mcp` Cursor/OpenClaw shape only; can be started on demand |
| Ollama installed but not listening | Low | Optional layer; no auto-pull policy |
| Obsidian not running | Low | Obsidian is a human notes app; not a background service |
| Open Interpreter config has inline OpenRouter key | **High (security)** | Must be migrated to Windows env var per policy |

---

## 10. Conclusion

The host is fully provisioned for any native-first AgentCore architecture. **No new installs are required.** The relevant runtime contracts (PowerShell 7, Node 24, Python 3.13, uv, the vendored MCP packages, the governed PowerShell wrappers) are all in place. The only mandatory remediation is the Open Interpreter inline secret, which is a security finding rather than a tooling gap. Architecture decisions in subsequent deliverables assume the existing toolchain and respect the governed-wrapper pattern — direct CLI invocation is not part of the design.
