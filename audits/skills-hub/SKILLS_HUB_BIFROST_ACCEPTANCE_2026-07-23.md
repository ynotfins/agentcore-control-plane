# Skills-Hub Bifrost Acceptance — Phase 4B

Date: 2026-07-24 (EDT)  
Task: PHASE_4B_SKILLS_HUB  
Canonical repo: `D:\github\agentcore-control-plane`  
Runtime: `H:\AgentRuntime\skills-hub`  
Gateway: `http://127.0.0.1:8080/mcp` (Cursor one-entry `agentcore-gateway` unchanged)

---

## Verdict

**PHASE_4B_SKILLS_HUB_COMPLETE_READY_FOR_PHASE_5**

Phase 4 dynamic read/search/get through Bifrost is proven. Isolation and GHSA
gates passed. Firebase normalized to dormant project-scoped. Google Sheets kept
OAuth-pending / zero exposure. Apps Script remains deferred. Phase 5 was **not**
started.

---

## 1. Entry gate (lean AgentCore baseline)

| Check | Result |
|---|---|
| Exactly one live Cursor rule `agentcore-foundation.mdc` | PASS |
| Exactly one Cursor MCP entry `agentcore-gateway` | PASS |
| Third-party discovery remains OFF | PASS (no discovery enablement; Cursor `mcp.json` unchanged) |
| Bifrost `/health` 200 | PASS |
| PostgreSQL `AgentCore-PostgreSQL18` Running + Automatic | PASS |
| Exactly ten `agentcore_memory-*` tools | PASS (10/10) |
| Exactly four `agentcore_project_router-*` tools | PASS (4/4) |
| Zero Swarm tools | PASS |
| Zero Obsidian tools | PASS |
| Full memory lifecycle | PASS (open → startup → append → idempotent replay → retrieve → expand → handoff → close → reopen → project isolation) |
| Projections current | PASS (`Invoke-M3ProjectionWorker.ps1` revision timestamp `2026-07-24 00:45:10`) |
| LangGraph topology fixture green | PASS fingerprint `a86e40e8ddd0a370…` |

Note: Cursor IDE MCP discovery briefly reported `Not connected` during this
session; all proofs used Bifrost HTTP MCP with the User-scope virtual key
(secret not logged).

---

## 2. Skills-Hub process-local HOME isolation

### Launcher

`H:\AgentRuntime\skills-hub\start.mjs` (source: `tools/skills-hub/start.mjs`)
sets process-local env **before** dynamic import of `@skills-hub-ai/mcp`:

- `HOME=H:\AgentRuntime\skills-hub\home`
- `USERPROFILE=H:\AgentRuntime\skills-hub\home`
- `HOMEDRIVE=H:`
- `HOMEPATH=\AgentRuntime\skills-hub\home`

Windows User/Machine scope were **not** modified for these variables.

### Proof method

1. Created harmless sentinel only at  
   `H:\AgentRuntime\skills-hub\home\.cursor\skills\agentcore-isolation-sentinel\SKILL.md`  
   (valid Skills-Hub frontmatter: name, description ≥10 chars, semver `version`).
2. Child-process `os.homedir()` under the same env →  
   `H:\AgentRuntime\skills-hub\home`.
3. `discoverSkills()` returned only `agentcore-isolation-sentinel`.
4. FS access audit (patched `fs.existsSync` / `readdirSync` / `readFileSync` via
   `createRequire`) showed skill-related access only under  
   `H:\AgentRuntime\skills-hub\home\...` — **zero** access to:
   - `C:\Users\ynotf\.cursor\skills`
   - `C:\Users\ynotf\.cursor\skills-cursor`
   - `C:\Users\ynotf\.claude\skills`
   - `C:\Users\ynotf\.codex\skills`
   - `C:\Users\ynotf\.agents\skills`
5. Control: TEMP redirected fake user profile containing
   `user-profile-sentinel` **was** discovered when `USERPROFILE` pointed there —
   proving discovery works, and isolation is env-driven.
6. Through Bifrost after cache TTL: `skills_hub-list_installed_skills` returned
   the isolation sentinel only.
7. STDIO MCP client against the same `start.mjs` Bifrost launches:
   - `prompts/list` → `[agentcore-isolation-sentinel]`
   - `prompts/get` → full `SKILL.md` body (complete local retrieval)
8. Sentinel removed; after TTL, gateway list returned `[]`. Home retained only
   empty `.claude\skills` scaffolding (no installed skills).

Active Codex/Claude/agents skill roots were **not** written to.

---

## 3. GHSA-frvp-7c67-39w9 disposition

| Fact | Evidence |
|---|---|
| Why present | Transitive via `@skills-hub-ai/mcp@0.1.7` → `@modelcontextprotocol/sdk@1.29.0` → `@hono/node-server` |
| Unpinned would be vulnerable | Advisory: `@hono/node-server < 2.0.5` Windows `serveStatic` traversal |
| Preferred fix applied | `tools/skills-hub/package.json` `overrides["@hono/node-server"]="2.0.11"` + lockfile |
| Installed version | **2.0.11** (`npm ls` shows `overridden`) |
| `npm audit` | **0 vulnerabilities** |
| STDIO imports `@hono/node-server`? | **No** — `dist/index.js` uses `StdioServerTransport` only |
| `streamableHttp.js` reachable from STDIO entry? | **No** (static import walk) |
| HTTP listener / `serveStatic` in STDIO entry? | **No** (`listen=false`, `serveStatic=false`) |

Resolution path used: override → reinstall from lock → audit clean → keep override.
Reachability proof retained as defense-in-depth (not a substitute for the pin).

---

## 4. Dynamic retrieval through Bifrost

Path: Cursor/operator → `agentcore-gateway` → Bifrost → `skills_hub` STDIO child.

| Step | Result |
|---|---|
| 1. initialize / tools available | PASS — 3 skills_hub tools present after restart |
| 2. notifications/initialized | Implicit in healthy MCP session (tools/list 200) |
| 3. upstream connected | PASS — live child `node.exe …\skills-hub\start.mjs` observed |
| 4. prompts/list | Upstream STDIO PASS; Bifrost aggregate gateway returns `-32601 prompts not supported` |
| 5. prompts/get | Upstream STDIO PASS (full local SKILL.md); gateway aggregate N/A |
| 6. registry search | PASS — `skills_hub-search_skills` query `security audit` |
| 7. metadata retrieval | PASS — `skills_hub-get_skill_detail` for `security-audit` |
| 8. complete SKILL.md retrieval | PASS for **local** skill via STDIO `prompts/get`; remote via gateway returns upstream `instructionsPreview` (~500 chars truncated by `@skills-hub-ai/mcp`) |
| 9. query `security audit` | PASS — results include `security-audit` and related skills |
| 10. no skill installed | PASS — post-cleanup `list_installed_skills` = `[]` |
| 11. isolated home empty of skills | PASS — no skill packages under isolated home |
| 12. no real user-profile skill path accessed | PASS — FS audit |
| 13. Bifrost restart recovery | PASS — scheduled task restart; `/health` 200; search still works |
| 14. no direct IDE MCP change | PASS — still only `agentcore-gateway` |

Denied write surface:

- `skills_hub-install_skill` **not** in gateway `tools/list` (0 matches)
- Live Bifrost `tools_to_execute` = `search_skills,get_skill_detail,list_installed_skills` only
- `log_content=false` in registry logging policy

Content trust: all remote skill bodies classified **raw_untrusted**.

---

## 5. Source / runtime parity

| Artifact | Path |
|---|---|
| Registry | `contracts/bifrost-upstream-mcp-registry.json` (`skills-hub` enabled, read-only) |
| Schema | `contracts/schemas/bifrost-upstream-mcp-registry.schema.json` (extended status enum) |
| Package authority | `tools/skills-hub/{package.json,package-lock.json,start.mjs,README.md}` |
| Sanitized renderer | `renderers/bifrost/config.json` + `config.sanitized.json` |
| Live Bifrost | `H:\AgentRuntime\bifrost\config.json` — `skills_hub` present; **no** `firebase_mcp`; **no** `google_sheets_mcp` |
| Validators | `python scripts/bifrost/validate_contracts.py` → OK |

---

## 6. Tests / commands executed

- Bifrost HTTP `tools/list` / `tools/call` (memory lifecycle + skills-hub)
- Node isolation + FS access diagnostics (ephemeral `_*.mjs`, deleted)
- STDIO MCP prompt probe against `start.mjs`
- `npm ls @hono/node-server`, `npm audit`
- `Invoke-M3ProjectionWorker.ps1 -ProjectKey agentcore-control-plane`
- `python -m agentcore workflow topology` (PYTHONPATH=`scripts`)
- `validate_contracts.py` + `render_bifrost_config.py`
- Bifrost scheduled-task restart recovery (×2)

---

## 7. Files changed (this phase)

- `contracts/bifrost-upstream-mcp-registry.json`
- `contracts/schemas/bifrost-upstream-mcp-registry.schema.json`
- `tools/skills-hub/package.json` (override retained)
- `tools/skills-hub/package-lock.json`
- `tools/skills-hub/start.mjs` (source-controlled launcher)
- `tools/skills-hub/README.md`
- `renderers/bifrost/config.json`
- `renderers/bifrost/config.sanitized.json`
- `audits/skills-hub/SKILLS_HUB_BIFROST_ACCEPTANCE_2026-07-23.md`
- `audits/google-integrations/GOOGLE_INTEGRATIONS_DISPOSITION_2026-07-24.md`

Runtime-only (not git): `H:\AgentRuntime\skills-hub\*`, User env `FIREBASE_PROJECT_ID` cleared.

---

## 8. Rollback path

1. Set registry `servers.skills-hub.enabled=false` (and/or remove from builder `allowed_server_ids`).
2. `python scripts/bifrost/render_bifrost_config.py`
3. Restart `\AgentCore\AgentCore-Bifrost-Gateway`.
4. Optional: restore `H:\AgentRuntime\bifrost\backups\config.json.pre-phase4b-*`.
5. Isolated home at `H:\AgentRuntime\skills-hub\home` can remain; contains no secrets.

Skills-Hub content cannot override AgentCore authority even while enabled.

---

## 9. Known limitations (documented, non-blocking)

1. Bifrost aggregate MCP surface does not expose `prompts/*` (`-32601`). Local full
   SKILL.md retrieval proven on the same STDIO upstream Bifrost launches.
2. Remote `get_skill_detail` returns truncated `instructionsPreview` by upstream
   package design; install remains denied so full remote bodies are not materialised
   into the isolated home.
3. Remote Skills-Hub HTTP MCP (`https://api.skills-hub.ai/mcp`) remains Cloudflare
   blocked; HTTPS REST API used by the STDIO package for search/detail.
