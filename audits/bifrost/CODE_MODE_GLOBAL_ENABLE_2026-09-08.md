# Bifrost Code Mode Global Enable — 2026-09-08

Operator authorization: `AUTH-2026-09-08-CODE-MODE-GLOBAL-ENABLE`  
Base branch: `setup/zoo-code-qdrant-nfa-20260820`  
HEAD at start: `46421fddcb96f09e9fe8c335e9fd13a3b4e58189`

## Intent

Enable Bifrost Code Mode for `mcp-prompt-optimizer` and `openrouter`; pre-flag `github-mcp` for Code Mode without enabling the client; set global `code_mode_binding_level` to `tool`.

## Ownership decision

Cursor is sole primary owner of the Bifrost MCP contract plane (operator decision 2026-09-08). Codex is independent reviewer / challenge only for that plane. **AGENTS.md / CLAUDE.md text update is blocked** until Cursor reloads process env with:

- `AGENTCORE_AUTHORITY_CAPABILITY=authority_maintainer`
- `AGENTCORE_AUTHORITY_APPROVAL_ID=AUTH-2026-09-08-CODE-MODE-GLOBAL-ENABLE`

(User-scope env vars were set this session; Cursor hook process has not inherited them yet.)

## Completed

| Item | Status |
| --- | --- |
| Re-verify AgentCore base branch HEAD | done (`setup/zoo-code-qdrant-nfa-20260820` @ `46421fd`) |
| Session-scope declared_files for this task | done |
| `scripts/bifrost/render_bifrost_config.py` → `code_mode_binding_level=tool` | done |
| `renderers/bifrost/config.json` binding_level=tool + Code Mode for mcp_prompt_optimizer + openrouter | done |
| `renderers/bifrost/config.sanitized.json` same | done |
| `docs/bifrost/BIFROST_CODE_MODE_RUNBOOK.md` updated | done |
| nfa-platform compare branches created from `origin/master` | done |
| nfa-platform compare branches pushed `-u` | done |
| `audits/bifrost/COMPARE_IDE_NFA_BRANCHES_2026-09-08.md` | done |

## Blocked (governed_mutable / Stage B)

| Item | Blocker |
| --- | --- |
| Rollback tree under `.agentcore/rollback/<ts>-code-mode-global-enable/` | subdirectory not declared; copying registry requires authority |
| `contracts/bifrost-upstream-mcp-registry.json` `is_code_mode_client=true` for three servers | requires authority_maintainer + approval id in Cursor process env |
| `AGENTS.md` / `CLAUDE.md` Bifrost ownership wording | same |
| Re-render from registry + `validate_contracts.py` green for this change | registry not updated; validate currently fails on unrelated dirty `ide-profiles/devin/MCP_CONFIG_TEMPLATE.json` |
| `Test-AgentCoreBifrostGateway.ps1` live apply | deferred until registry+authority path complete |
| Commit on AgentCore base branch | deferred until governed edits land |

## Pending registry edits (apply after Cursor reload)

### mcp-prompt-optimizer
- Set `is_code_mode_client: true`
- Keep `enabled: true`
- Note: Code Mode enabled 2026-09-08 with binding_level=tool

### openrouter
- Set `is_code_mode_client: true`
- Keep `enabled: true`, `status: dormant` (lease/JIT unchanged)
- Note: Code Mode enabled 2026-09-08; zero default exposure unchanged

### github-mcp
- Set `is_code_mode_client: true` (pre-flag only)
- Keep `enabled: false`, `status: deferred`, `deferred: true`

Classic unchanged (do not flip): agentcore-memory, sequential-thinking, cursor-agent-mcp, skills-hub, arabold-docs, context7, nia, agentcore-capability-catalog, agentcore-project-router.

Do not enable: postgres, sqlite, sheets, drive, sendgrid, firebase, github.

## nfa-platform compare lanes

| Branch | SHA | Pushed |
| --- | --- | --- |
| `compare/eigent-finish-build-20260908` | `7882536f575fb2b1a84ecbf44d560ed318a9dec3` | yes |
| `compare/antigravity-finish-build-20260908` | `7882536f575fb2b1a84ecbf44d560ed318a9dec3` | yes |
| `compare/zed-finish-build-20260908` | `7882536f575fb2b1a84ecbf44d560ed318a9dec3` | yes |

Base: `origin/master` @ `7882536f575fb2b1a84ecbf44d560ed318a9dec3`. Working checkout left on `feat/goal-mode-complete` (dirty files not carried into compare branches).

## Eigent / Zed gateway blockers

- Do not paste/materialize `BIFROST_MCP_VIRTUAL_KEY`
- If enrollment unverified, stop and propose credential-free path
- Antigravity: process-attested `http://127.0.0.1:18082/mcp` only

## Quoted ownership rule (target AGENTS.md text — not yet written to file)

> **Bifrost MCP contract ownership (operator decision 2026-09-08):** Cursor is the sole primary owner of the Bifrost MCP contract plane in this repository. Cursor owns `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-gateway-client.json`, `scripts/bifrost/render_bifrost_config.py` and Bifrost validators/tests, `renderers/bifrost/*`, `ops/bifrost` live apply/restart/acceptance for the MCP gateway, and related Bifrost MCP commits on the AgentCore base branch. Codex's role for Bifrost MCP is independent reviewer / challenge only. Do not create dual-primary ownership of this plane.

## CURSOR CONTINUATION PROMPT

```text
Resume AUTH-2026-09-08-CODE-MODE-GLOBAL-ENABLE on setup/zoo-code-qdrant-nfa-20260820.
Confirm process env has AGENTCORE_AUTHORITY_CAPABILITY=authority_maintainer and AGENTCORE_AUTHORITY_APPROVAL_ID=AUTH-2026-09-08-CODE-MODE-GLOBAL-ENABLE (User-scope already set; restart Cursor if missing).
Then: (1) rollback copies under .agentcore/rollback/<timestamp>-code-mode-global-enable/; (2) set is_code_mode_client=true on mcp-prompt-optimizer, openrouter, github-mcp in contracts/bifrost-upstream-mcp-registry.json (github stays enabled=false/deferred); (3) write Bifrost ownership rule into AGENTS.md and CLAUDE.md per audits/bifrost/CODE_MODE_GLOBAL_ENABLE_2026-09-08.md; (4) re-render Bifrost config; validate_contracts.py; (5) Test-AgentCoreBifrostGateway.ps1; (6) commit declared Code Mode files only on the AgentCore base branch.
Do not enable github/postgres/sqlite/sheets/drive/sendgrid/firebase. Do not finish-build nfa. Do not touch H:\.
nfa compare branches already pushed — see audits/bifrost/COMPARE_IDE_NFA_BRANCHES_2026-09-08.md.
```
