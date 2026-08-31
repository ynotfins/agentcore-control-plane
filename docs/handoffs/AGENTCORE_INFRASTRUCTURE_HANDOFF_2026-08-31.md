# AgentCore Control Plane — Infrastructure Handoff
**Date:** 2026-08-31 | **Branch:** setup/zoo-code-qdrant-nfa-20260820 | **Auth:** AUTH-2026-08-30-GLOBAL-LOCAL-DOCS-INGEST

## Purpose
This handoff covers every infrastructure, policy, and governance change made to `D:\github\agentcore-control-plane` during the Aug 30–31 2026 session. Open a new Cursor chat scoped to this repo and read this doc first.

---

## 1. Mandatory Local Docs Ingest — Complete

### Arabold F: store (live)
- `DOCS_MCP_STORE_PATH` = `F:\AgentCore\runtime\docs-store\arabold`
- DB migrated from C: to F:; classic mode (`is_code_mode_client: false`)
- Launch: pnpm Node 24 (`C:\Users\ynotf\AppData\Local\pnpm\bin\node.EXE`, ABI 137) + `mcp` subcommand
  - Reason: system Node 26.8.1 (ABI 147) breaks better-sqlite3; pnpm Node 24 is correct
- `bifrost@2.0.0` scraped, catalogued, snapshotted: `F:\AgentCore\runtime\docs-store\official\bifrost\2.0.0\`
- CATALOG.json: `F:\AgentCore\runtime\docs-store\CATALOG.json`
- **PIN MISMATCH documented**: docs = `2.0.0`; live `bifrost-http.exe` reports `v2.0.0-prerelease1` — upgrade gated

### Context7 (live, gateway-only)
- Installed: `C:\Users\ynotf\.cursor\vendor\context7-mcp`; pnpm Node 24 launch
- Status: `active` in Bifrost registry; arabold-first; same-turn public-miss bridge only
- Removed from `forbidden_routes` in global-agent-policy; DORMANT catalog: `active_gateway`
- Skill: `C:\Users\ynotf\.claude\skills\context7-mcp\SKILL.md` (rewritten arabold-first)
- Rule: NEVER paste Context7 into IDE `mcp.json`

### global-agent-policy.yaml changes
- `policy_revision: "2026-08-30-local-docs-ingest"`
- New rules added: `arabold-docs` (mandatory ingest), `milestone-gateway-tool-inventory`, `session-tool-discovery`
- `git-safety` rule updated: commit after milestones/substantial changes, no permission ask needed
- `dormant-mcp-catalog` rule updated: Context7 gateway-only not forbidden

### Docs updated this session
- `docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md` — Arabold checkpoint = CATALOG.json row per used pin
- `docs/agent-policy/MILESTONE_EXECUTION_STANDARD.md` — gateway-tool-inventory in milestone gates
- `docs/operations/DORMANT_MCP_CAPABILITY_CATALOG.md` — Context7 status active_gateway
- `templates/project-governance/.agentcore/TOOL_MANIFEST.yaml` — annotated with docs-ingest and inventory notes
- `contracts/validate_contracts.py` — Context7 unblocked from authority check

### Generated artifacts (all committed)
- `.cursor/rules/docs-first-arabold.mdc` — alwaysApply: true; session-start tools/list + arabold ingest
- `.cursor/rules/architecture-critic.mdc` — requestable; macro-level strategic review subagent
- `scripts/generate_gateway_tool_inventory.py` — generates .agentcore/runtime/gateway-tool-inventory.md
- `.agentcore/runtime/gateway-tool-inventory.md` — 46 tools (current)
- `.agentcore/runtime/USER_RULES_DOCS_INGEST_PASTE.md` — paste text for IDE User Rules
- 42 IDE GLOBAL_RULES.md re-rendered (including new `devin` profile)

### Artiforge — completely removed
Scrubbed from: AGENTS.md, global-agent-policy, registry, project-tool-lifecycle, MCP matrix, DORMANT catalog, all GLOBAL_RULES.

### Devin IDE profile — created
- `ide-profiles/devin/IDE_PROFILE.yaml`
- `ide-profiles/devin/MCP_CONFIG_TEMPLATE.json` (filesystem+depwire+tentra+serena direct servers)
- `renderers/gateway-clients/devin.json`
- GLOBAL_RULES/INSTALL/VALIDATION rendered

### AGENTS.md changes
- Git policy: commit after milestones, no permission needed for routine post-task commits
- Tool routing Docs line: arabold-first with F: store path
- Stop policy: artiforge removed

---

## 2. Bifrost Semantic Caching — LIVE

**Status: Active since Aug 30.**

```
Vector store : Redis localhost:6379 (confirmed running; TCP 0.0.0.0:6379)
Mode         : direct-only (hash-based, no embedding cost)
TTL          : 30 minutes
Cache key    : agentcore-global (default — all requests auto-cached, no header needed)
Config file  : F:\AgentCore\runtime\bifrost\config.json (vector_store + plugins sections)
Renderer     : scripts/bifrost/render_bifrost_config.py — build_bifrost_config function
```

What it does: identical requests through agentcore-gateway within 30 min cost zero provider tokens — served from Redis.
To verify: Bifrost logs show `Direct Cache` badge; `cache_debug.cache_hit: true` in response extra_fields.

---

## 3. Gateway tool inventory (verified 2026-08-30)

46 tools through `http://127.0.0.1:8080/mcp` (BIFROST_MCP_VIRTUAL_KEY, 80 chars):
- arabold_docs (10 tools), context7 (2), sequential_thinking, agentcore_memory (10)
- agentcore_project_router (4), playwright, morph_mcp (7), mcp_prompt_optimizer (7)
- skills_hub (3), cursor_agent_mcp, openrouter (0 tools without M6 lease)

---

## 4. Runtime facts (proven, unchanged unless noted)

| Item | Value |
|---|---|
| Bifrost gateway | `http://127.0.0.1:8080/mcp` (scheduled task `\AgentCore\AgentCore-Bifrost-Gateway`) |
| Bifrost binary | `F:\AgentCore\runtime\bifrost\bin\bifrost-http.exe` v2.0.0-prerelease1 |
| PostgreSQL 18 | `127.0.0.1:55433` — `agent_core` + `cognee_core` (canonical AgentCore); `nfa_devin_dev` + `nfa_ingest_capture` (nfa-platform) |
| Redis | `localhost:6379` (used by Bifrost semantic cache) |
| BIFROST_MCP_VIRTUAL_KEY | Windows User env, 80 chars — never commit |
| CONTEXT7_API_KEY | Windows User env |
| OPENAI_API_KEY | Windows User env |
| MORPH_API_KEY | Windows User env, 51 chars |
| Node for arabold | `C:\Users\ynotf\AppData\Local\pnpm\bin\node.EXE` (Node 24, ABI 137) |
| Docs store | `F:\AgentCore\runtime\docs-store\` |

---

## 5. Pending items (priority order)

| Priority | ID | Task |
|---|---|---|
| HIGH | bifrost-version-upgrade | Audit live v2.0.0-prerelease1 vs latest; run `arabold_docs scrape_docs https://docs.getbifrost.ai` for latest version; upgrade if stable |
| MEDIUM | bifrost-semantic-cache-verify | Confirm Redis caching is hitting in Bifrost logs after a restart |
| DONE | global-docs-ingest-rule | Policy + M0 + Milestone docs updated |
| DONE | context7-gated-register | Context7 live behind Bifrost |
| DONE | milestone-tool-inventory | generator + inventory file created |
| DONE | render-global-policy | 42 IDE GLOBAL_RULES re-rendered; User Rules paste created |

---

## 6. Not wired predictably (read before starting new work)

- **minimax-classic context snapshots** committed in `e492302` contained OpenRouter API keys. Push-protection was manually bypassed. Keys ending in `...0600`, `...911a`, `...fef7`, `...c01f` should be rotated in OpenRouter dashboard. Those paths are now gitignored.
- **Node ABI**: arabold MUST use pnpm Node 24, not system Node 26 — this is wired in the renderer.
- **Bifrost docs version mismatch**: catalogued as 2.0.0, binary reports v2.0.0-prerelease1. Not a bug — upgrade is gated.
- **Semantic cache partition**: if Redis is flushed or `default_cache_key` changes, all cache entries are lost (non-destructive; just misses until re-populated).
- **Context7 must stay gateway-only** — never put it in any IDE `mcp.json`.

---

## 7. Cursor continuation prompt

```
@D:\github\agentcore-control-plane\docs\handoffs\AGENTCORE_INFRASTRUCTURE_HANDOFF_2026-08-31.md
@D:\github\agentcore-control-plane\AGENTS.md
@D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml

Read the handoff doc. Branch: setup/zoo-code-qdrant-nfa-20260820.
Priority: bifrost-version-upgrade — check if v2.0.0-prerelease1 is behind the latest 
stable Bifrost release. Use arabold_docs scrape_docs to ingest the latest docs, 
then evaluate whether to upgrade. Follow AGENTS.md commit policy.
```
