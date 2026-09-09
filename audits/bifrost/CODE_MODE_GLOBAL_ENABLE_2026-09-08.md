# Bifrost Code Mode Global Enable — 2026-09-08

Operator authorization: `AUTH-2026-09-08-CODE-MODE-GLOBAL-ENABLE`  
Base branch: `setup/zoo-code-qdrant-nfa-20260820`  
Start HEAD: `46421fddcb96f09e9fe8c335e9fd13a3b4e58189`  
Primary commit: `207af02`  
Ownership follow-up: this completion pass

## Intent

Enable Bifrost Code Mode for `mcp-prompt-optimizer` and `openrouter`; pre-flag `github-mcp` for Code Mode without enabling the client; set global `code_mode_binding_level` to `tool`.

## Ownership rule (now in AGENTS.md)

> **Bifrost MCP contract ownership (operator decision 2026-09-08):** Cursor is the sole primary owner of the Bifrost MCP contract plane in this repository. Cursor owns `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json`, `scripts/bifrost/render_bifrost_config.py` and Bifrost validators/tests, `renderers/bifrost/*`, `ops/bifrost` live apply/restart/acceptance for the MCP gateway, and related Bifrost MCP commits on the AgentCore base branch. Codex's role for Bifrost MCP is independent reviewer / challenge only. Do not create dual-primary ownership of this plane.

## Results

| Item | Status |
| --- | --- |
| Rollback `.agentcore/rollback/20260908-210120-code-mode-global-enable/` | done |
| Registry `is_code_mode_client=true` for mcp-prompt-optimizer, openrouter, github-mcp | done |
| github-mcp remains `enabled=false` / `deferred` | done |
| `code_mode_binding_level=tool` in renderer + rendered configs | done |
| Classic servers unchanged | done |
| AGENTS.md / CLAUDE.md Bifrost ownership | done |
| nfa compare branches pushed @ `7882536f…` | done |
| User-scope `AGENTCORE_AUTHORITY_*` cleared after completion | done |

## Non-goals honored

Did not enable postgres/sqlite/sheets/drive/sendgrid/firebase/github.  
Did not finish-build nfa-platform from AgentCore.  
Did not touch H:\ Swarm.  
Did not permanently weaken Stage B hooks.

## IDE note

Fetch nfa compare work from `D:\github\nfa-platform` branches `compare/eigent-finish-build-20260908`, `compare/antigravity-finish-build-20260908`, `compare/zed-finish-build-20260908`. Bootstrap prompts remain owned by the nfa-platform agent.
