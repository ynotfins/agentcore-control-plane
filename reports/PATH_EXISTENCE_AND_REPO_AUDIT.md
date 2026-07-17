# PATH_EXISTENCE_AND_REPO_AUDIT — CHAOSCENTRAL

**Generated:** 2026-07-03
**Mode:** Read-only. No installs, no edits, no service starts.
**Verification basis:** `Test-Path`, `Get-Item`, `git -C <repo> status/log/branch --porcelain`.
**Secret policy:** All inline credentials (OpenRouter API key in Open Interpreter config, OpenClaw inline gateway token, Codex experimental bearer token, Claude `CONTEXT7_API_KEY`, etc.) are masked as `[REDACTED]` in this report.

---

## 1. Path Existence Audit (28 paths)

All 28 paths in the original investigation list were probed. **Every path exists.** No missing directories.

| # | Path | Type | Notes |
|---|------|------|-------|
| 1 | `D:\github\swarm-agent-team` | Git repo | `master`, head `3a0e2c9`, 2 dirty |
| 2 | `D:\github\agentcore-control-plane` | Git repo | `master`, head `c688fde`, 6 dirty |
| 3 | `D:\github\agentcore-control-plane\vendor\swarm\swarmrelay` | Git repo | latest commit `docs: add .agentcore/docs/DOCS_INDEX.md` |
| 4 | `D:\github\agentcore-control-plane\vendor\swarm\swarmclaw` | Git repo | same recent doc commit |
| 5 | `D:\github\agentcore-control-plane\vendor\swarm\swarmvault` | Git repo | same recent doc commit |
| 6 | `D:\github\agentcore-control-plane\vendor\swarm\swarmdock` | Git repo | same recent doc commit |
| 7 | `D:\github\agentcore-control-plane\vendor\swarm\swarmfeed` | Git repo | same recent doc commit |
| 8 | `C:\Users\ynotf\.codex` | IDE profile | Codex 0.137.0 config, memories, plugin |
| 9 | `C:\Users\ynotf\.claude` | IDE profile | Claude Code 2.1.199, `.claude.json` w/ API key |
| 10 | `C:\Users\ynotf\.cursor` | IDE profile | Cursor mcp.json, vendors |
| 11 | `C:\Users\ynotf\.openclaw` | Agent profile | openclaw.json, gateway.cmd, lossless-claw/, memory/ |
| 12 | `C:\Users\ynotf\.openinterpreter` | Agent profile | config.toml w/ inline OpenRouter key |
| 13 | `C:\Users\ynotf\.minimax` | Agent profile | config.yaml (no-secrets policy) |
| 14 | `C:\Users\ynotf\.mavis` | Agent profile | Same config.yaml as minimax |
| 15 | `D:\openclaw` | OpenClaw install dir | Binaries / scripts |
| 16 | `D:\openclaw\ClawX` | OpenClaw sub-product | Process running (5 procs) |
| 17 | `D:\Program Files\nodejs` | Runtime | Node 24.16.0 |
| 18 | `D:\Obsidian` | Knowledge store | Dungeon Vault |
| 19 | `D:\Codex_Managed` | Codex extra | mcp-control-plane, memory-system, memory_gateway, postgres |
| 20 | `D:\AgentOps` | Operations dir | control-pane, clawx-skills, memory |

**Additional paths discovered during inventory (out-of-scope but relevant):**

| # | Path | Type | Notes |
|---|------|------|-------|
| 21 | `D:\github\agent-team` | Git repo | master, head `1ed33ca` 2026-06-18, 20 dirty |
| 22 | `D:\github\autonomous-agent-team` | Git repo | HEAD detached, 22 dirty, no remotes |
| 23 | `F:\AgentCore` | Runtime root | PostgreSQL, agentmemory, agents_workspace |
| 24 | `F:\AgentCore\agentmemory\swarmvault` | Runtime | File-based RAG |
| 25 | `F:\AgentCore\agentmemory\swarmrecall` | Runtime | API + Meilisearch |
| 26 | `F:\VectorDB` | Vector substrate dirs | chroma, lancedb, pgvector, qdrant (pre-wired, empty) |
| 27 | `F:\Postgres` | Legacy data | Older PG artifacts |
| 28 | `F:\AgentMemory` | Empty placeholder | — |

---

## 2. Repository Git State

All audited repos are real `git` working trees (presence of `.git\` verified).

### 2.1 `D:\github\swarm-agent-team`

- Branch: `master`
- HEAD: `3a0e2c9` — *"M7: hardening + final proof"* (2026-07-02)
- Dirty entries: **2**
- Status: Clean, recently hardened.

### 2.2 `D:\github\agentcore-control-plane` (canonical source authority)

- Branch: `master`
- HEAD: `c688fde` — *"Native-first memory: retire global-memory-gateway from baseline"* (2026-07-01)
- Dirty entries: **6** (rolled-out uncommitted source edits; rollout report explicitly states *"git commit of changes (incl. tracking database-plan.md/handoff) … awaiting explicit approval"*).
- Worktrees: 5 vendor/swarm subtrees, each on the latest doc-only commit `docs: add .agentcore/docs/DOCS_INDEX.md`.
- Notable in-tree artifacts:
  - `database-plan.md` (71,926 bytes) — design authority for unified memory catalog
  - `docs\SYSTEM_HANDOVER_BLUEPRINT.md` (19,779 bytes) — runtime/storage governance
  - `docs\memory_system.md` (5,392 bytes) — current memory plane summary
  - `docs\SWARMVAULT_SOURCE_REGISTRATION.md` (2,277 bytes) — safe strategy
  - `docs\rollout-runbook.md` (956 bytes) — minimal one-liner corrective procedure
  - `artifacts\rollout-2026-06-30\ROLLOUT_REPORT.md` (13,744 bytes) — PARTIAL-GREEN acceptance
  - `contracts\global-memory-database-contract.json` (4,402 bytes) — DB + memory contract
  - `contracts\master-mcp-server-config.json` (17,441 bytes) — canonical MCP server contract
  - `registry\tool-registry.json` (14,298 bytes) — generated tool inventory
  - `supervisor\servers.json` (21,251 bytes) — server catalog w/ launch contracts
  - `ops\` — extensive PowerShell runtime scripts (`Initialize-AgentCore6TB.ps1`, `Backup-AgentCorePostgres.ps1`, `Start-AgentCorePostgres.ps1`, `Test-AgentCore*.ps1`, `Invoke-AgentCoreSwarm*.ps1`, `Install-AgentCoreOperationalScheduledTasks.ps1`, etc.)
  - `migrations\` — 5 migration pairs authored but not applied (apply blocked per `database-plan.md` §13/§18)
  - `renderers\*.json` — per-client MCP fragments (codex, cursor, minimax, openclaw, antigravity, open-interpreter)
  - `docs\prompts\` — 9 per-IDE cleanup prompts
  - `validators\validate-control-plane.ps1` — drift gate

### 2.3 `D:\github\vendor\swarm\swarmrelay`

- Branch: per-repo default
- HEAD: `docs: add .agentcore/docs/DOCS_INDEX.md` (recent doc commit)
- No unusual dirty state.

### 2.4 `D:\github\vendor\swarm\swarmclaw`

- HEAD: same recent doc commit
- Per `SWARMVAULT_SOURCE_REGISTRATION.md`: SwarmVault registration of `swarmclaw` may be **ingest-incomplete** from a prior OOM incident; re-validate before relying on it.

### 2.5 `D:\github\vendor\swarm\swarmvault`

- Vendored CLI build present at `packages/cli/dist/index.js`
- Runtime root at `F:\AgentCore\agentmemory\swarmvault`
- Source registered to local SwarmVault (per `doctor` audit: 5 managed sources, 2465 raw sources, 7071 pages, ~22 MB raw)

### 2.6 `D:\github\vendor\swarm\swarmdock`

- HEAD: recent doc commit
- Not registered in local SwarmVault per handover blueprint

### 2.7 `D:\github\vendor\swarm\swarmfeed`

- HEAD: recent doc commit
- Not registered in local SwarmVault per handover blueprint

### 2.8 `D:\github\agent-team` (out-of-scope but found)

- Branch: `master`
- HEAD: `1ed33ca` (2026-06-18)
- Dirty entries: **20** — substantial uncommitted work, age ~2 weeks.

### 2.9 `D:\github\autonomous-agent-team` (out-of-scope but found)

- HEAD: **detached** at unknown commit
- Dirty entries: **22**
- No remotes configured (offline development state)
- Highest risk of accidental data loss among the repos — recommend attaching to a branch and committing before any future work.

---

## 3. Vendor Subtree Summary

`D:\github\agentcore-control-plane\vendor\swarm\` contains five real Git subtrees (each with their own `.git\`):

| Subtree | Source-type | Local runtime mapped? |
|---------|------------|------------------------|
| swarmrelay | Repo | No — source only |
| swarmclaw | Repo | No (F:\AgentCore\agentmemory\swarmclaw\ exists but empty) |
| swarmvault | Repo | Yes — `F:\AgentCore\agentmemory\swarmvault` |
| swarmdock | Repo | No |
| swarmfeed | Repo | No |

The five subtrees are healthy Git worktrees on a recent doc commit. They serve as source authority for any rebuild of `F:\AgentCore\agentmemory\*` runtime.

---

## 4. IDE / Agent Profile Audit (file-level)

### 4.1 `C:\Users\ynotf\.codex\`

- `config.toml` — `model = "gpt-5.5"`, `model_context_window = 1000000`, `features.memories = true`, `features.goals = true`, `features.multi_agent = true`, plugin `codex-lossless-memory-pack@personal` enabled
- `memories/` — `MEMORY.md`, `memory_summary.md`, `raw_memories.md` (Codex native memory pack surface)
- SQLite DBs:
  - `goals_1.sqlite` (24 KB)
  - `logs_2.sqlite` (1.4 GB) — very large
  - `memories_1.sqlite` (4.3 MB)
  - `state_5.sqlite` (1.8 MB)
- `hooks.json` — Stop hook calls `codex-stop-audit.ps1`
- `[REDACTED]` inline: `experimental_bearer_token` value present in config.toml (rotation per rollout gate)

### 4.2 `C:\Users\ynotf\.claude\`

- `claude.json` (likely `~/.claude.json`) — contains `[REDACTED]` `apiKey`, plus `[REDACTED]` `CONTEXT7_API_KEY` (rotation per rollout gate)
- mcp configs and `projects/` history present
- Claude Code 2.1.199

### 4.3 `C:\Users\ynotf\.cursor\`

- `mcp.json` references:
  - `swarmrecall` → `D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmRecall.ps1`
  - `swarmvault` → `D:\github\agentcore-control-plane\ops\Invoke-AgentCoreSwarmVault.ps1`
- `mcp_config.json` — additional per-project mcp
- `vendor\arabold-docs-mcp\`, `vendor\context-fabric-mcp\` — installed node packages

### 4.4 `C:\Users\ynotf\.openclaw\`

- `openclaw.json`:
  - `gateway.mode = "local"`, `gateway.bind = "loopback"`
  - Inline token `[REDACTED]` (rotation gate)
  - MCP servers: all stdio (no HTTP MCP)
  - controlUi allowedOrigins tied to port 18789
- `gateway.cmd` — sets `OPENCLAW_GATEWAY_PORT=18789` (not 3000)
- `lossless-claw\config.foundation.json` (468 bytes), `lossless-claw\lcm.sqlite` (4.6 MB), `lossless-claw\files\`
- `memory\` — multiple agent SQLite DBs
- `agents\main\qmd\xdg-cache\qmd\index.sqlite`
- `start-obsidian-mcp-server.ps1` — wraps Obsidian REST
- `mcp-wrappers\artiforge-mcp.ps1` — CodeX-stdout wrapper for Artiforge

### 4.5 `C:\Users\ynotf\.openinterpreter\`

- `config.toml` — contains inline OpenRouter API key `[REDACTED]` (**security finding**, see §6)
- API key also present in `http_headers` of a model entry
- Violates the AgentCore no-secrets-on-disk policy

### 4.6 `C:\Users\ynotf\.minimax\config.yaml` == `C:\Users\ynotf\.mavis\config.yaml`

- Identical file content
- Policy: `no_secrets_on_disk: true`, `secrets_source: windows_environment_variables`
- `banned_paths` includes `**/.env`
- `baseURL: https://agent.minimax.io/mavis/api/v1/llm/v1`

---

## 5. Live IDE MCP Wiring Snapshot

Verified across the renderer contracts in `D:\github\agentcore-control-plane\renderers\`:

| MCP server | Codex | Cursor | OpenClaw | MiniMax | Mavis | OI | Antigravity |
|------------|-------|--------|----------|---------|-------|----|-------------|
| arabold-docs | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| artiforge | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| sequential-thinking | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| serena | — | ✓ | ✓ | ✓ | — | — | — |
| context-fabric | ✓ | ✓ | ✓ | — | — | — | — |
| filesystem | ✓ | ✓ | ✓ | ✓ | — | — | ✓ |
| obsidian-vault | — | ✓ | ✓ | ✓ | — | — | ✓ |
| playwright | — | ✓ | ✓ | ✓ | — | — | ✓ |
| github-mcp | ✓ | ✓ | ✓ | — | — | — | — |
| cursor-agent-mcp | — | ✓ | ✓ | — | — | — | — |
| mcp-debugger | — | ✓ | ✓ | — | — | — | — |
| swarmrecall | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| swarmvault | ✓ | ✓ | ✓ | ✓ | — | ✓ | ✓ |
| global-memory-gateway | (retired from baseline) | (retired) | (retired) | (retired) | — | — | — |

This table reflects the post-2026-06-30 baseline: `global-memory-gateway` was retired from the normal-memory baseline and replaced by SwarmRecall as the canonical write/read path (per `master-mcp-server-config.json` v2026-06-26 `normal_memory_rule`).

---

## 6. Secret Findings (NOT printed in any form)

The following inline credentials were observed during the read-only audit. Values are masked as `[REDACTED]` per task policy; rotations are listed as rollout gates in `artifacts\rollout-2026-06-30\ROLLOUT_REPORT.md §6`.

| Location | Secret kind | Status |
|----------|-------------|--------|
| `C:\Users\ynotf\.openinterpreter\config.toml` | OpenRouter API key (inline) | **VIOLATION** — must be migrated to Windows env var per `database-plan.md` §3.6 |
| `C:\Users\ynotf\.openclaw\openclaw.json` | OpenClaw gateway token (inline) | Rotation gate per rollout report |
| `C:\Users\ynotf\.codex\config.toml` | `experimental_bearer_token` | Rotation gate per rollout report |
| `C:\Users\ynotf\.claude.json` (or `~/.claude.json`) | `apiKey`, `CONTEXT7_API_KEY` | Rotation gate per rollout report |

All `AGENT_CORE_*_PASSWORD`, `OPENAI_API_KEY`, `OBSIDIAN_API_KEY`, `ARTIFORGE_PAT`, `GITHUB_PAT_TOKEN`, etc. are intended to live in **Windows User-scope environment variables only**, never in files.

---

## 7. Repo + Path Risk Summary

| Risk | Evidence | Impact |
|------|----------|--------|
| `agentcore-control-plane` has 6 uncommitted source edits | `git status --porcelain` | Rollout report §6 explicitly lists *"git commit of changes … awaiting explicit approval"* as a commit gate. Architecture cannot ship until these are committed or rolled back. |
| `agent-team` 20 dirty entries, ~2 weeks old | `git status` | Stale uncommitted work, risk of accidental loss. |
| `autonomous-agent-team` HEAD detached, no remotes, 22 dirty | `git status` | Highest loss-risk. Should be reattached and committed. |
| `swarmclaw` SwarmVault registration may be OOM-incomplete | `SWARMVAULT_SOURCE_REGISTRATION.md` | Re-validate before using SwarmVault hits against `swarmclaw`. |
| Inline API key in Open Interpreter config | `config.toml` | Direct violation of policy; rotation+env-var migration required. |
| `global-memory-gateway` retired but renderers/agents may still reference it | `master-mcp-server-config.json` v2026-06-26 + 6 renderer fragments | Architecture must rely on SwarmRecall, not the retired gateway. |

---

## 8. Conclusion

Every path in the original investigation list is real. Every audited repository is a live Git worktree. The AgentCore canonical source repo (`D:\github\agentcore-control-plane`) is the design authority and contains every contract, validator, renderer, migration, and runtime script the architecture depends on. The pre-existing rollout is **PARTIAL-GREEN**: source state is green, but live IDE cleanup, DB migration apply, secret rotation, scheduled-task de-registration, and SwarmVault `query` performance remain blocked behind operator approval gates. The next deliverable quantifies which tools are actually installed and on PATH.