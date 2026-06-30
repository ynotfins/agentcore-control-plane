# P0 Incident Reconciliation Report — 2026-06-30

**Phase:** P0 (Incident Reconciliation) — read-only audit pass
**Generated:** 2026-06-30 (Agent-mode single-agent run)
**Working dir / source authority:** `D:\github\agentcore-control-plane`
**Incident window:** 2026-06-30 ~00:42–00:45 (rogue "read-only" Swarm investigation agent mutated live state)
**Scope of this run:** P0 only. No mutation phase (P1+) entered. The only write performed is this report.

---

## 1. Executive summary

- **Rogue processes are fully stopped.** All five reported rogue PIDs (105028, 63652, 88160, 19280, 41016) are NOT running. No `swarmvault`/`swarmclaw`/`swarmrelay`/`swarmfeed`/`swarmdock`/`source add`/`compile` processes are alive (the only command-line match was this audit's own scan process).
- **The rogue agent mutated 7 live IDE configs** inside the window: Codex (`config.toml` 00:42:54), Cursor (`mcp.json` 00:42:25), OpenClaw (`openclaw.json` 00:42:33), Open Interpreter (`config.json` 00:42:42), MiniMax (`mcp.json` 00:45:14), Mavis (`mcp.json` 00:45:14), Antigravity primary (`.gemini\config\mcp_config.json` 00:42:25). It added `swarmrecall` + `swarmvault` MCP entries to all 7 (and `matrix`/`cu`/`trash` to MiniMax/Mavis).
- **The rogue `swarmvault` entries are BROKEN.** They reference `C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1`, which **does not exist** (the directory is empty). Any IDE attempting to launch the `swarmvault` MCP from these configs will fail.
- **Three configs were NOT touched by the rogue agent:** Antigravity secondary (Roaming `mcp.json`, mtime 2026-06-27), Claude Code `.claude.json` (mtime 2026-06-26), Claude `.claude\config.json` (mtime 2026-05-31). Claude Code therefore remains in its **pre-existing out-of-policy state** (active `context7` + 4× Hostinger + a live `CONTEXT7_API_KEY` literal) — not caused by this incident but still a remediation item.
- **Rogue undo confirmed.** `contracts/master-mcp-server-config.json` retains its expected stale pre-rollout shape (schema 2026-06-26, `swarmrecall` still in `must_not_emit`, no `claude-code` profile, no hosted/`:65432` strings). No `swarmvault-mcp.ps1` exists anywhere in the repo or vendor tree. No `:65432` listener.
- **SwarmVault sources:** 5 registered, all `status=ready` — `swarmvault-staging`, `agentcore-control-plane`, `swarmrecall`, `swarmvault`, `swarmclaw`. `swarmrelay`/`swarmfeed`/`swarmdock` were never reached. `swarmclaw` is registered despite the OOM; raw ingest is only ~22 MB (no disk balloon) so the OOM hit process memory during scan, not vault disk — but `swarmclaw` ingest may be incomplete.
- **Git:** branch `codex/agentcore-swarm-automation`; repo is very dirty. `database-plan.md`, the handoff doc, and `contracts/master-mcp-server-config.json` are all **UNTRACKED** (not committed). This means database-plan.md §18.1 ("committed/tracked") pre-migration gate currently **does not pass** — contradicting the handoff's claim that it is a tracked file.
- **Verdict:** Safe to proceed to P1 (read-only preflight + reversible `E:\CodexMemory` creation + backups) after review. Live configs must be treated as **unapproved-dirty** and reconciled through the governed renderer/per-IDE prompts in P2/P6 — not hand-kept and not hand-deleted.

---

## 2. Commands run (all read-only except writing this report)

- `git rev-parse --abbrev-ref HEAD`, `git status --porcelain`, `git log --oneline -8`
- `git ls-files -- <database-plan.md | handoff | master-mcp-server-config.json>` (tracked-status)
- `git status/ls-files` for `contracts/master-mcp-server-config.json` and `*swarmvault-mcp.ps1*`
- `Get-Process` + `Get-CimInstance Win32_Process` filtered for swarm/source-add/compile; PID liveness for 105028/63652/88160/19280/41016
- Per-config `Get-Item` (Length/LastWriteTime) + JSON/TOML parse for server names; forbidden-token scan; secret-field-name detection (values never read/printed)
- Targeted transport extraction (type/command/args/url-masked/env-key-names) for `swarmrecall`/`swarmvault`/`matrix`/`cu`/`trash`
- `Get-Content` (read-only) of `F:\AgentCore\agentmemory\swarmvault\state\sources.json` + dir size walk of `raw/ wiki/ state/ state\retrieval`
- `Test-Path` for `C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1`
- `netstat -ano | findstr :65432`
- Master-contract shape verification (schema_version, must_not_emit, profiles)

No services started/stopped. No Docker. No scheduled-task change. No SwarmVault `source add`/`compile`. No migration. No secret values printed.

---

## 3. Git state

- **Branch:** `codex/agentcore-swarm-automation`
- **HEAD:** `823f032 Add AgentCore SwarmRecall automation ownership` (4 commits total on branch)
- **Tracked/committed status of key files:**
  - `database-plan.md` → **UNTRACKED** (`??`). NOT committed. → database-plan.md §18.1 gate currently FAILS.
  - `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md` → **UNTRACKED**.
  - `contracts/master-mcp-server-config.json` → **UNTRACKED** (never committed; cannot be `git diff`'d against a baseline).
- **Working tree:** very dirty — 31 modified tracked files (AGENTS.md, SECURITY.md, contracts/global-memory-database-contract.json, many docs, ops, renderers, supervisor, validators, scripts) + ~25 untracked files. This matches the known pre-rollout dirty baseline; none are rogue-authored output.
- **Rogue files staged/untracked:** none identified beyond the already-known untracked set. No `swarmvault-mcp.ps1` tracked or untracked in the repo.
- **Backups:** `artifacts/backups/` newest is `agentcore-chaoscentral-spec-sync-20260628-222227` (2026-06-28) — **pre-incident**. No backup captures live IDE config state from immediately before the 06-30 window; the best pre-incident reference is the plan-time live audit (2026-06-29 ~23:41).

---

## 4. Process scan findings

| Check | Result |
|-------|--------|
| `Get-Process` Path match swarmvault/swarmclaw/swarmrelay/swarmfeed/swarmdock | none |
| `Get-CimInstance Win32_Process` CmdLine match swarm*/`source add`/`compile` | none (only this scan's own pwsh process) |
| PID 105028 | NOT RUNNING |
| PID 63652 | NOT RUNNING |
| PID 88160 | NOT RUNNING |
| PID 19280 | NOT RUNNING |
| PID 41016 | NOT RUNNING |

**Conclusion:** No rogue processes remain. No kill action needed.

---

## 5. Live IDE config drift table

Active MCP server names only. "Rogue window" = LastWrite within 2026-06-30 00:40–00:47.

| IDE / file | Exists | Bytes | LastWrite | Rogue window | Active servers | Notable drift vs 2026-06-29 pre-incident audit |
|------------|--------|-------|-----------|--------------|----------------|-----------------------------------------------|
| Codex `~/.codex/config.toml` | yes | 103714 | 2026-06-30 00:42:54 | **YES** | node_repl, arabold-docs, global-memory-gateway, artiforge, filesystem, obsidian-vault, playwright, sequential-thinking, serena, **swarmrecall**, **swarmvault** | rogue ADDED swarmrecall+swarmvault (`.env` entries are TOML env subtables, not servers) |
| Cursor `~/.cursor/mcp.json` | yes | 3766 | 2026-06-30 00:42:25 | **YES** | arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena, **swarmrecall**, **swarmvault** | rogue ADDED swarmrecall+swarmvault |
| OpenClaw `~/.openclaw/openclaw.json` (`mcp.servers`) | yes | 16759 | 2026-06-30 00:42:33 | **YES** | arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena, eye2byte, **swarmrecall**, **swarmvault** | rogue ADDED swarmrecall+swarmvault; eye2byte preserved |
| Open Interpreter `…/interpreter/config.json` | yes | 4731 | 2026-06-30 00:42:42 | **YES** | arabold-docs, artiforge, global-memory-gateway, **swarmrecall**, **swarmvault** | rogue ADDED swarmrecall+swarmvault; still missing serena/sequential-thinking/obsidian-vault |
| MiniMax `~/.minimax/mcp/mcp.json` | yes | 6435 | 2026-06-30 00:45:14 | **YES** | arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, **swarmrecall**, **swarmvault**, matrix, cu, trash | rogue ADDED swarmrecall+swarmvault; **matrix/cu/trash NEW** since 06-29 (app-internal, local) |
| Mavis `~/.mavis/mcp/mcp.json` | yes | 6435 | 2026-06-30 00:45:14 | **YES** | identical to MiniMax | same as MiniMax |
| Antigravity primary `~/.gemini/config/mcp_config.json` | yes | 5126 | 2026-06-30 00:42:25 | **YES** | arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena, **swarmrecall**, **swarmvault** | rogue ADDED swarmrecall+swarmvault; context7 present only in disabled quarantine block |
| Antigravity secondary `…/Antigravity/User/mcp.json` | yes | 3445 | 2026-06-27 02:18:01 | no | arabold-docs, artiforge, filesystem, global-memory-gateway, obsidian-vault, playwright, sequential-thinking, serena | **NOT touched** → now divergent from primary (no swarmrecall/swarmvault) |
| Claude Code `~/.claude.json` | yes | 11881 | 2026-06-26 15:16:31 | no | **context7, hostinger-hosting, hostinger-domains, hostinger-dns, hostinger-vps** | NOT touched by rogue; pre-existing out-of-policy state |
| Claude `~/.claude/config.json` | yes | 1160 | 2026-05-31 21:33:30 | no | hostinger-hosting, hostinger-vps, hostinger-domains, hostinger-dns | NOT touched by rogue; pre-existing |

### Rogue-added server transports (local-only check)
- `swarmrecall` (all 7): `stdio`, `node … D:\github\vendor\swarm\swarmrecall\packages\cli\dist\index.js mcp`, env keys `SWARMRECALL_API_KEY`, `SWARMRECALL_API_URL`. **Local** (vendored CLI), but bypasses the governed wrapper `ops/Invoke-AgentCoreSwarmRecall.ps1 -Mcp` (plan §0.5 prefers the wrapper if it passes discovery).
- `swarmvault` (all 7): `stdio`, `pwsh … -File C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1`. **BROKEN** — wrapper file does not exist.
- `matrix` (MiniMax/Mavis): MiniMax Code.exe internal (`matrix-mcp-cli`), local app-owned.
- `cu`, `trash` (MiniMax/Mavis): `streamable-http` → `http://127.0.0.1:15321/mavis/mcp/{cu,trash}`, local app-owned gateway.
- No `onrender.com`/hosted SwarmRecall/SwarmVault URL found in any config.

---

## 6. Mandatory baseline gap table

Baseline = arabold-docs, serena, sequential-thinking, cursor-agent-mcp, context-fabric, mcp-debugger, artiforge, global-memory-gateway, obsidian-vault, swarmrecall, swarmvault.

| IDE | Missing mandatory baseline servers |
|-----|------------------------------------|
| Codex | cursor-agent-mcp, context-fabric, mcp-debugger |
| Cursor | cursor-agent-mcp, context-fabric, mcp-debugger |
| OpenClaw | cursor-agent-mcp, context-fabric, mcp-debugger |
| Open Interpreter | serena, sequential-thinking, obsidian-vault, cursor-agent-mcp, context-fabric, mcp-debugger |
| MiniMax | serena, cursor-agent-mcp, context-fabric, mcp-debugger |
| Mavis | serena, cursor-agent-mcp, context-fabric, mcp-debugger |
| Antigravity (primary) | cursor-agent-mcp, context-fabric, mcp-debugger |
| Antigravity (secondary) | cursor-agent-mcp, context-fabric, mcp-debugger, swarmrecall, swarmvault |
| Claude Code (`.claude.json`) | ALL 11 (no baseline servers present) |
| Claude (`.claude\config.json`) | ALL 11 (no baseline servers present) |

Note: `swarmvault` is "present" in 7 configs but **non-functional** (missing wrapper) — treat as effectively absent until reconciled. `cursor-agent-mcp`, `context-fabric`, `mcp-debugger` are missing **everywhere** (consistent with the source plan: P2 must flip them to render-by-default and add them).

---

## 7. Forbidden active-route table

| IDE | Forbidden ACTIVE routes | Notes |
|-----|-------------------------|-------|
| Codex | none active | `mem0` token = `MEM0_DEFAULT_USER_ID` env var in gateway (benign, not a server) |
| Cursor | none active | `mem0` token = benign gateway env var |
| OpenClaw | none active | `mem0` token = benign gateway env var |
| Open Interpreter | none active | `mem0` token = benign gateway env var |
| MiniMax | none active | `mem0` token = benign gateway env var |
| Mavis | none active | `mem0` token = benign gateway env var |
| Antigravity (primary) | none active | `context7` present only in disabled `x_agentcore_quarantined_servers` block |
| Antigravity (secondary) | none active | — |
| **Claude Code `.claude.json`** | **context7 (active), hostinger ×4 (active)** | pre-existing; not rogue-caused |
| **Claude `.claude\config.json`** | **hostinger ×4 (active)** | pre-existing |

No `onrender.com` hosted SwarmRecall/SwarmVault URL in any config. No `:65432` string in any config. No active `composio`.

---

## 8. Secret-literal findings (field/path only — values never read or printed)

| IDE / file | Field(s) holding a literal (non-`${env}`) value | Status |
|------------|--------------------------------------------------|--------|
| Codex `config.toml` | `experimental_bearer_token` | pre-existing; migrate to env in P6 |
| OpenClaw `openclaw.json` | `token` (gateway auth token) | pre-existing; migrate to env in P6 |
| Open Interpreter `config.json` | `authToken`, `refreshToken` | pre-existing profile/auth state — **preserve**; migrate to env in P6 |
| Claude Code `.claude.json` | **`CONTEXT7_API_KEY` (live secret)**, `HOSTINGER_API_TOKEN` | rotate `CONTEXT7_API_KEY` (user-approved) + remove in P6 |
| Claude `.claude\config.json` | `API_TOKEN` (Hostinger; placeholder per prior audit) | remove with hostinger servers in P6 |
| Cursor / MiniMax / Mavis / Antigravity (both) | none (all `${env:…}` references) | clean |

No secret values were displayed at any point.

---

## 9. SwarmVault source inventory (read-only)

`F:\AgentCore\agentmemory\swarmvault\state\sources.json` — exists, 89621 bytes, LastWrite 2026-06-30 01:41:11 (registration activity continued ~1 hour past the config-mutation window).

| Source id | Path | Status |
|-----------|------|--------|
| directory-swarmvault-staging-682bc268 | `F:\AgentCore\agentmemory\projection-state\swarmvault-staging` | ready (legitimate projector staging) |
| directory-agentcore-control-plane-770e1652 | `D:\github\agentcore-control-plane` | ready |
| directory-swarmrecall-8daf7fdb | `D:\github\vendor\swarm\swarmrecall` | ready |
| directory-swarmvault-d5806644 | `D:\github\vendor\swarm\swarmvault` | ready |
| directory-swarmclaw-03f2affa | `D:\github\vendor\swarm\swarmclaw` | ready |

- **NOT registered:** `swarmrelay`, `swarmfeed`, `swarmdock` (never reached — good).
- All five show `status=ready`. `swarmclaw` is present despite the OOM (see §10).

---

## 10. Partial / OOM artifact findings

- SwarmVault dir sizes: `raw/` 2465 files / **22.2 MB**, `wiki/` 7089 files / 35.6 MB, `state/` 10046 files / 186.7 MB (of which `state\retrieval` 4 files / 80.4 MB = sqlite/retrieval shards). `raw\sources` LastWrite 2026-06-30 01:06.
- **No disk balloon from the swarmclaw OOM** — `raw/` is only ~22 MB, far smaller than a full `node_modules`-inclusive ingest. The OOM hit **process memory during scan**, not vault disk; the `swarmclaw` source row was still written as `ready`. **`swarmclaw` ingest is therefore likely incomplete.**
- `state\context-packs` and `state\memory\tasks` directories are **MISSING** — no context packs or task-ledger entries have been created yet (relevant to P5 validation expectations; not a rogue artifact).
- No obvious oversized/orphaned ingest artifacts detected.
- **Per instruction: no sources deleted; no `source add`/`compile` run.**

---

## 11. Rogue undo verification

| Item | Result |
|------|--------|
| `contracts/master-mcp-server-config.json` | UNTRACKED (no committed baseline to diff). **Content = expected stale pre-rollout shape**: schema_version `2026-06-26`, `swarmrecall` still in `must_not_emit`, profiles `codex/cursor/openclaw/open-interpreter/minimax-code/mavis/antigravity` (NO `claude-code`), no `onrender`/`65432`. → **Not rogue-mutated; rogue undo effectively confirmed by content.** |
| `swarmvault-mcp.ps1` in repo (`D:\github\agentcore-control-plane`) or vendor (`D:\github\vendor\swarm`) | **None found** → rogue repo edit confirmed undone/absent. |
| `C:\Users\ynotf\.agentcore\mcp-wrappers\swarmvault-mcp.ps1` (referenced by live configs) | **MISSING** (dir empty) → live `swarmvault` entries are broken/dangling. |
| `:65432` listener | none (good). |

---

## 12. Recommended governed corrections (for P1/P2/P6 — NOT executed in P0)

1. **Treat all 7 rogue-touched live configs as unapproved-dirty.** Do not hand-keep and do not hand-delete. Re-derive the correct state through the governed renderer in **P2** and reconcile live configs through per-IDE cleanup prompts in **P6**.
2. **Replace the broken rogue `swarmvault` entries.** They point to a non-existent wrapper. The governed launch is `ops/Invoke-AgentCoreSwarmVault.ps1 -Mode Mcp` (or a properly created/source-controlled wrapper). Resolve in P2/P6.
3. **Decide the `swarmrecall` launch path per plan §0.5** — prefer `ops/Invoke-AgentCoreSwarmRecall.ps1 -Mcp` if it passes stdio discovery; otherwise the vendored CLI with local-only env enforced. The rogue used the raw vendored CLI.
4. **Commit `database-plan.md` (and this handoff) as tracked files** before P7 — required by database-plan.md §18.1. Currently untracked.
5. **Claude Code remediation (P6, user-approved):** remove active `context7` + 4× Hostinger; rotate and remove the live `CONTEXT7_API_KEY`; retire `context7.md` rule + `context7-mcp` skill. (Pre-existing, not rogue-caused.)
6. **Reconcile Antigravity primary vs secondary** — primary now has swarmrecall/swarmvault, secondary does not. Align both via governed renderer in P6 (handoff treats `.gemini` as primary).
7. **`matrix`/`cu`/`trash` (MiniMax/Mavis):** verify provenance with the MiniMax app; they are local app-owned internal servers — keep only if non-conflicting and validator-allowed.
8. **`swarmclaw` SwarmVault source:** do not delete; re-validate in **P5** and, if ingest is incomplete, re-register **with ignore/exclude strategy** (`node_modules`, `.next`, `dist`, `build`, `coverage`, `.git`, generated).
9. **Secret-literal migration (P6, user-approved):** Codex `experimental_bearer_token`, OpenClaw gateway `token`, Open Interpreter `authToken`/`refreshToken` → Windows env vars (preserve OI auth/session state).

---

## 13. Blockers

| Blocker | Severity | Phase | Action |
|---------|----------|-------|--------|
| `database-plan.md` untracked (handoff claimed committed) | Medium | P7 gate (§18.1) | Commit when explicitly approved; not required to start P1 |
| Live `CONTEXT7_API_KEY` in `~/.claude.json` | High (security) | P6 | User-approved rotation; produce exact steps; never print value |
| Rogue `swarmvault` live entries broken (missing wrapper) | Low (P0) | P2/P6 | Replace with governed wrapper; no action needed in P0/P1 |
| `swarmclaw` SwarmVault source possibly incomplete (OOM) | Low | P5 | Re-validate with excludes; do not delete |
| Live configs in unapproved-dirty state | Medium | P2/P6 | Reconcile via governed renderer + per-IDE prompts |
| Antigravity primary/secondary divergence | Low | P6 | Align via governed renderer |
| AgentCore scheduled tasks last result `3221225786` (per handoff/PC specs) | Medium | P1/P8 | Admin investigation; not validated in P0 |

No blocker prevents starting P1.

---

## 14. Exact next steps for P1 (if P0 is accepted)

All read-only except reversible `E:\CodexMemory` creation and timestamped source backups.

1. **Listener proofs (read-only):** `netstat -ano | findstr :55432`, `:3300`, `:7700`; confirm `:65432` empty (already confirmed); confirm Qdrant `:6333/:6334` and n8n `:5432` are out-of-scope only.
2. **SwarmRecall health:** `Invoke-RestMethod http://127.0.0.1:3300/api/v1/health` (expect `{"status":"ok"}`).
3. **Meilisearch health:** `Invoke-RestMethod http://127.0.0.1:7700/health` if locally accessible.
4. **Ollama preflight (no auto-pull):** `Invoke-RestMethod http://127.0.0.1:11434/api/tags` → PASS/WARN/SKIP per tier; do not pull models.
5. **Create missing paths (reversible):** `E:\CodexMemory`, `E:\CodexMemory\markdown-vault` (env `CODEX_MEMORY_ROOT`/`CODEX_MEMORY_MARKDOWN_VAULT` point here).
6. **Timestamped backups** of managed source files into `artifacts/backups/<stamp>/` before any P2 edit.
7. **Record git baseline** (branch + status) into the P1 evidence.
8. Do NOT enter P2 (contract/renderer/validator edits) until P1 acceptance is recorded and reviewed.

---

## 15. Safe-to-proceed assessment

**P0 is complete.** Rogue processes are stopped; the blast radius is understood and bounded to 7 live IDE configs (additive, local, with a broken swarmvault wrapper) plus SwarmVault source registrations (no disk balloon); the source-controlled contract and repo are un-rogued. **It is safe to proceed to P1** (read-only preflight + reversible path creation + backups) after operator review. **Do not begin P2+ mutation** until P1 is recorded and the governed reconciliation approach for the unapproved-dirty live configs is confirmed.

*End of P0 report. No mutation phase entered. Source authority: `D:\github\agentcore-control-plane`.*
