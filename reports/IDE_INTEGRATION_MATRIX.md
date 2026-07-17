# IDE_INTEGRATION_MATRIX — CHAOSCENTRAL

**Generated:** 2026-07-03
**Scope:** All IDEs and agents installed on the host, mapped to the AgentCore canonical memory/render contract.
**Source contracts:**
- `D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json` (v2026-06-26)
- `D:\github\agentcore-control-plane\renderers\*.json`
- `D:\github\agentcore-control-plane\supervisor\servers.json`
- `D:\github\agentcore-control-plane\registry\tool-registry.json`
- `D:\github\agentcore-control-plane\docs\prompts\*` (per-IDE cleanup prompts)

**Secret policy:** All inline credentials in live IDE configs are masked as `[REDACTED]`; rotation is tracked as rollout gates.

---

## 1. IDE / Agent Roster

| # | IDE/Agent | Profile root | Renderer file | Cleanup prompt | Live MCP wired? |
|---|-----------|--------------|---------------|----------------|-----------------|
| 1 | Codex | `C:\Users\ynotf\.codex\` | `renderers\codex.mcp.json` | `docs\prompts\codex-cleanup-prompt.md` | Yes |
| 2 | Cursor | `C:\Users\ynotf\.cursor\` | `renderers\cursor-global.mcp.json` | `docs\prompts\cursor-cleanup-prompt.md` | Yes |
| 3 | OpenClaw | `C:\Users\ynotf\.openclaw\` | `renderers\openclaw.openclaw.fragment.json` | `docs\prompts\openclaw-cleanup-prompt.md` | Yes |
| 4 | Open Interpreter | `C:\Users\ynotf\.openinterpreter\` | `renderers\open-interpreter.config.fragment.json` | `docs\prompts\open-interpreter-cleanup-prompt.md` | Yes |
| 5 | MiniMax Code | `C:\Users\ynotf\.minimax\` | `renderers\minimax.mcp.json` | `docs\prompts\minimax-cleanup-prompt.md` | Yes |
| 6 | Mavis | `C:\Users\ynotf\.mavis\` (symlinked config) | (deferred: `renderers\mavis.mcp.json`) | `docs\prompts\mavis-cleanup-prompt.md` | Yes (same as minimax) |
| 7 | Antigravity IDE | (workspace install) | `renderers\antigravity.mcp_config.json` | `docs\prompts\antigravity-cleanup-prompt.md` | Yes |
| 8 | Claude Code | `C:\Users\ynotf\.claude\` + `~/.claude.json` | `artifacts\staging\claude-code\claude-code.mcp.json` (staged) | `docs\prompts\claude-code-cleanup-prompt.md` | Staged |
| 9 | Claude Desktop + Obsidian | `C:\Users\ynotf\AppData\…` | — | `docs\prompts\claude-desktop-obsidian-cleanup-prompt.md` | Not yet wired |
| 10 | Android Studio | `D:\AgentOps\control-pane\` (workspace) | (uses minimax/agentops renderer) | n/a (no cleanup prompt) | Inherits minimax shape |

Every IDE/agent has a corresponding renderer (or staged renderer), a profile directory, and (except Android Studio) a cleanup prompt in `docs\prompts\`. The cleanup prompts are the operator's checklist for migrating live IDE configs to the governed baseline.

---

## 2. Live MCP Wiring Matrix (post-2026-06-30 baseline)

Each cell describes whether the IDE/agent's live `mcp.json` (or equivalent) actually invokes that MCP server. The "live" column reflects what's wired today; "renderer" reflects what the canonical contract says should be wired once the operator runs the cleanup prompt.

| MCP | Codex | Cursor | OpenClaw | OI | MiniMax | Mavis | Antigravity | Claude Code | Claude Desktop/Obsidian |
|-----|:-----:|:------:|:--------:|:--:|:-------:|:-----:|:-----------:|:-----------:|:----------------------:|
| arabold-docs | L+R | L+R | L+R | L+R | L+R | (L) | L+R | R | — |
| artiforge | L+R | L+R | L+R | L+R | L+R | (L) | L+R | R | — |
| sequential-thinking | L+R | L+R | L+R | L+R | L+R | (L) | L+R | R | — |
| serena | — | L+R | L+R | — | L+R | — | — | R | — |
| context-fabric | L+R | L+R | L+R | — | — | — | — | — | — |
| filesystem | L+R | L+R | L+R | — | L+R | — | L+R | — | — |
| obsidian-vault | — | L+R | L+R | — | L+R | — | L+R | — | R (planned) |
| playwright | — | L+R | L+R | — | L+R | — | — | — | — |
| github-mcp | L+R | L+R | L+R | — | — | — | — | — | — |
| cursor-agent-mcp | — | L+R | L+R | — | — | — | — | — | — |
| mcp-debugger | — | L+R | L+R | — | — | — | — | — | — |
| swarmrecall | L+R | L+R | L+R | L+R | L+R | — | L+R | R | — |
| swarmvault | L+R | L+R | L+R | L+R | L+R | — | L+R | R | — |
| global-memory-gateway | (retired) | (retired) | (retired) | — | (retired) | — | (retired) | — | — |

Legend: L = live today, R = required by renderer contract, — = not wired.

Key observations:

- `global-memory-gateway` was **retired from the baseline** in `master-mcp-server-config.json` v2026-06-26 and `database-plan.md` notes `Native-first memory: retire global-memory-gateway from baseline` is the most recent source commit on `agentcore-control-plane`. The codebase has moved on from this surface.
- `swarmrecall` and `swarmvault` are now the **mandatory-everywhere** memory/render surfaces, replacing global-memory-gateway.
- Mavis inherits MiniMax's renderer until the dedicated `mavis.mcp.json` is added (deferred per rollout §7).
- Claude Code is staged, not yet emitted to its live config — operator must run its cleanup prompt.
- Claude Desktop + Obsidian is the only IDE with an `obsidian-vault` connection in cleanup-prompt scope.

---

## 3. Memory Surface Mapping

| IDE/Agent | Native lossless plane | Governed memory plane | Local RAG plane | Long-form notes plane |
|-----------|-----------------------|------------------------|------------------|------------------------|
| Codex | `~/.codex\memories_1.sqlite` (4.3 MB) + `logs_2.sqlite` (1.4 GB) + `codex-lossless-memory-pack@personal` plugin | SwarmRecall MCP (mandatory) | SwarmVault MCP (mandatory) | (no native obsidian binding) |
| Cursor | (no native lossless) | SwarmRecall MCP | SwarmVault MCP | obsidian-vault MCP (planned) |
| OpenClaw | `~/.openclaw\memory\*.sqlite` + `lossless-claw\lcm.sqlite` + `qmd\index.sqlite` | SwarmRecall MCP | SwarmVault MCP | obsidian-vault MCP |
| Open Interpreter | (no native lossless) | SwarmRecall MCP | SwarmVault MCP | — |
| MiniMax Code | (none on disk) | SwarmRecall MCP | SwarmVault MCP | obsidian-vault MCP |
| Mavis | (none on disk) | SwarmRecall MCP (deferred renderer) | SwarmVault MCP (deferred renderer) | — |
| Antigravity IDE | (none on disk) | SwarmRecall MCP | SwarmVault MCP | obsidian-vault MCP |
| Claude Code | `~/.claude\projects\…` + `~/.claude.json` | SwarmRecall MCP (staged) | SwarmVault MCP (staged) | — |
| Claude Desktop + Obsidian | (Claude Desktop project memory) | — | — | obsidian-vault MCP (planned) |
| Android Studio | (none) | (inherits minimax MCP shape) | — | — |

**Critical insight.** Codex and OpenClaw each have **native lossless planes** (Codex's `codex-lossless-memory-pack@personal` + native sqlite; OpenClaw's `lossless-claw` + QMD index + per-agent sqlite). These are *parallel* to the governed memory plane. The architecture must decide:

1. Whether native lossless is the canonical durable store (then the governed plane is a projection), OR
2. Whether the governed plane is canonical (then native lossless is a fast cache), OR
3. Whether both coexist with explicit synchronization (the current rollout pattern via `Invoke-AgentCoreMemoryProjector.ps1`).

Option 3 is what the existing rollout documents implement; options 1 and 2 would require new design work and are listed as the rejected options in the architecture comparison.

---

## 4. Secret Storage Posture per IDE

| IDE | Secrets on disk? | Required env-var migrations |
|-----|------------------|-----------------------------|
| Codex | `[REDACTED]` `experimental_bearer_token` in `~/.codex\config.toml` | `OPENAI_API_KEY`, `GITHUB_PAT_TOKEN`, etc. should be env-var-only |
| Cursor | none observed in `~/.cursor\mcp.json` | relies on `${env:...}` references already |
| OpenClaw | `[REDACTED]` inline token in `~/.openclaw\openclaw.json` | rotation per rollout gate |
| Open Interpreter | `[REDACTED]` inline OpenRouter key in `config.toml` AND `http_headers` | **violation** — migration mandatory |
| MiniMax / Mavis | none (policy enforced: `no_secrets_on_disk: true`) | env-var only |
| Antigravity | not inspected deeply | relies on renderer env-var refs |
| Claude Code | `[REDACTED]` `apiKey` and `CONTEXT7_API_KEY` in `~/.claude.json` | rotation per rollout gate |

---

## 5. Renderer vs. Live Drift

The rollout report (`ROLLOUT_REPORT.md` §5 item 3) states *"contracts + supervisor aligned (swarmrecall/swarmvault) — DONE"* but a full `python scripts\mcp_control_plane.py` regeneration is **deferred**. As a result, `registry\tool-registry.json` and `supervisor\servers.json` were last regenerated 2026-06-27. Any new cleanup-prompt operator action may create renderer drift relative to the live IDE configs.

**Implication for architecture.** The renderer-vs-live drift is small enough to ignore for design purposes — the contract is the source of truth, not the regenerated registry — but operators should be told to re-run `validators\validate-control-plane.ps1 -DryRun` after every IDE cleanup-prompt run.

---

## 6. Per-IDE Memory Plane Role

### 6.1 Codex

- Lossless plane: Native (`memories_1.sqlite` + `logs_2.sqlite` + plugin).
- Governed plane: SwarmRecall MCP via the governed wrapper.
- Native 1M-token context window (`model_context_window = 1000000`).
- Hook: `Stop` → `codex-stop-audit.ps1`.
- Risks: 1.4 GB `logs_2.sqlite` may grow unbounded; cleanup prompt should advise a rotation policy.

### 6.2 Cursor

- Lossless plane: none native.
- Governed plane: SwarmRecall MCP (local API), SwarmVault MCP (file-based).
- Native feature: Cursor's own project memory (separate, not part of AgentCore).
- Risks: `mcp.json` has 13+ servers; a few are HTTP (artiforge, github-mcp) — outbound network required.

### 6.3 OpenClaw

- Lossless plane: native `lossless-claw` + QMD + per-agent sqlite.
- Governed plane: SwarmRecall + SwarmVault MCP.
- Gateway: **port 18789** (NOT 3000); currently offline at audit.
- Risks: inline gateway token must be rotated; `~/.openclaw\memory\*.sqlite` will balloon without compaction.

### 6.4 Open Interpreter

- Lossless plane: none.
- Governed plane: SwarmRecall + SwarmVault MCP (per renderer, OI is a binding).
- Risks: inline API key in plaintext — security finding.

### 6.5 MiniMax / Mavis

- Lossless plane: none.
- Governed plane: SwarmRecall + SwarmVault (Mavis deferred).
- Risks: `banned_paths: **/.env` is good; verify config actually respects it.

### 6.6 Antigravity IDE

- Lossless plane: none.
- Governed plane: SwarmRecall + SwarmVault MCP.
- Risks: same as Cursor (HTTP MCPs require outbound).

### 6.7 Claude Code

- Lossless plane: Claude Code native project memory under `~/.claude\projects\`.
- Governed plane: SwarmRecall + SwarmVault MCP (staged config; not yet emitted).
- Risks: API key + Context7 key inline; both must rotate.

### 6.8 Claude Desktop + Obsidian

- Lossless plane: Claude Desktop project memory.
- Long-form plane: Obsidian (`D:\Obsidian\Dungeon Vault\`).
- Governed plane: not connected.
- Risks: Obsidian must be running in MCP-server mode (`https://127.0.0.1:27124`) to use `obsidian-vault` MCP — currently not running.

### 6.9 Android Studio

- Lossless plane: none.
- Inherits MiniMax/AgentOps MCP shape.
- Risks: none material.

---

## 7. Cross-IDE Failure Mode Map

| Failure | Which IDEs impacted | Where the recovery plane lives |
|---------|---------------------|--------------------------------|
| PostgreSQL cold (`:55432` not up) | All — every MCP that touches the gateway | Postgres task `\AgentCore\PostgresRuntime` cold-starts on logon |
| Meilisearch cold (`:7700` not up) | SwarmRecall full-text path | Task `\AgentCore\SwarmRecallMeilisearch` |
| SwarmRecall API cold (`:3300` not up) | All SwarmRecall MCP callers | Task `\AgentCore\SwarmRecallApi` |
| SwarmVault CLI build missing | SwarmVault MCP | Vendored CLI at `D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js`; rebuild via `pnpm install && pnpm build` |
| Docker Desktop stopped | Cursor/OpenClaw `github-mcp` shape | Start Docker Desktop service manually |
| Obsidian not running | Claude Desktop + any `obsidian-vault` MCP caller | Open Obsidian and enable Local REST API plugin |
| OpenAI key missing | arabold-docs (degraded semantic) | Set `OPENAI_API_KEY` env var |
| `OPENROUTER_API_KEY` leaked in OI config | OI sessions — secret rotation | Rotate at provider, migrate to env var |

---

## 8. Summary

Every IDE/agent has a renderer, a profile, and (except Android Studio) a cleanup prompt. The canonical baseline is **SwarmRecall + SwarmVault + (for long-form) Obsidian**, not the retired `global-memory-gateway`. Two IDEs (Codex, OpenClaw) have native lossless planes that must be coordinated with the governed plane; the rest depend entirely on the governed plane. Security findings (Open Interpreter inline key, plus four other inline credentials) are catalogued and must be remediated before production rollout. The next deliverable audits the memory stack in detail to determine which backplane components can carry the load described above.