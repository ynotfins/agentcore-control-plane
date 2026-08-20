# Zoo-Code Skills and Morph/Cheap-Worker Smoke Evidence

Timestamp: 2026-08-20T17:58:40-04:00

## Scope

- Add Zoo-Code discoverable global skills for the operator's Cursor/Antigravity Zoo-Code workflow.
- Verify Morph GitHub search is callable from Codex.
- Verify the cheap-worker OpenRouter route can call DeepSeek V4 Flash and DeepSeek V4 Pro after environment repair.

## Zoo-Code Skill Root

Verified from upstream Zoo-Code source via Morph:

- Repository: `Zoo-Code-Org/Zoo-Code`
- File: `src/services/skills/SkillsManager.ts`
- Relevant behavior:
  - Global `.agents/skills` is scanned.
  - Global `.roo/skills` is scanned after `.agents/skills` and has higher same-source priority.
  - Project `.agents/skills` and project `.roo/skills` are also scanned when a workspace is open.
  - Valid skills require `<skill-name>/SKILL.md` with matching `name` frontmatter and a non-empty `description`.

Installed global Zoo-Code skills at:

- `C:\Users\ynotf\.roo\skills`

Installed count: 30

Installed skill names:

- `agentcore-project-lifecycle`
- `automate`
- `autopilot`
- `canvas`
- `code-research`
- `create-hook`
- `create-rule`
- `create-skill`
- `create-subagent`
- `cursor-subagent-creator`
- `explore`
- `feature-research`
- `goal`
- `loop`
- `migrate-to-skills`
- `morph-migrate`
- `new-repo`
- `onboard`
- `origin`
- `rename-chat`
- `review`
- `review-bugbot`
- `review-security`
- `sdk`
- `share`
- `shell`
- `split-to-prs`
- `statusline`
- `update-cli-config`
- `update-cursor-settings`

Validation:

- `SkillsCount: 30`
- `BadCount: 0`
- Secret-pattern scan result: no matches for obvious `sk-*`, `zoo_ext_*`, `MORPH_API_KEY=`, or `OPENROUTER_*KEY=` patterns under `C:\Users\ynotf\.roo\skills`.

No pre-existing `C:\Users\ynotf\.roo\skills` collision was found, so no skill collision backup folder was created.

## Morph Smoke

Codex Morph MCP call:

- Tool: `mcp__morph_mcp.github_codebase_search`
- Repository: `Zoo-Code-Org/Zoo-Code`
- Query: "Find where global and project skill directories are discovered for skills. Summarize the path logic and the relevant functions or files."
- Result: succeeded and returned `src/services/skills/SkillsManager.ts:1-718`.

This proves the Morph GitHub search path is currently callable from Codex.

Billing note: the Morph MCP output does not include account or cost information. This evidence proves the route works, but it does not prove which Morph billing ledger was charged.

## Cheap-Worker Repair and Smoke

Initial live MCP tool call failed with:

- `OPENROUTER_CODEX_API_KEY is not set in the environment.`

Environment check showed these variables are set in User and current Codex process scope:

- `MORPH_API_KEY`
- `OPENROUTER_CODEX_API_KEY`
- `OPENROUTER_API_KEY`

Root cause:

- `C:\Users\ynotf\.codex\config.toml` had `cheap-workers` env vars set to `["OPENROUTER_API_KEY", "MORPH_API_KEY"]`.
- `C:\Users\ynotf\.codex\mcp\cheap-workers\server.mjs` reads `process.env.OPENROUTER_CODEX_API_KEY`.

Repair:

- Backed up config to `C:\Users\ynotf\.codex\config.toml.agentcore-backup-20260820-175648`.
- Updated `cheap-workers` env vars to `["OPENROUTER_CODEX_API_KEY", "OPENROUTER_API_KEY", "MORPH_API_KEY"]`.

In-task MCP transport limitation:

- Existing `cheap-workers` MCP child processes were started before the config repair.
- They were exact children of `codex.exe` running `C:\Users\ynotf\.codex\mcp\cheap-workers\server.mjs`.
- After stopping those stale child processes, this already-open Codex task retained a closed MCP transport.
- A fresh Codex task/app restart is required for the lazy MCP tool channel to reconnect normally.

Direct stdio MCP smoke from the corrected environment succeeded:

DeepSeek V4 Flash:

- Tool: `deepseek_flash_worker`
- Route: `~deepseek/deepseek-v4-flash-latest`
- Provider response model: `deepseek/deepseek-v4-flash`
- Worker returned: `CHEAP_WORKER_OK`
- Usage reported by OpenRouter: 319 total tokens, cost `0.00003168`, `is_byok: false`

DeepSeek V4 Pro:

- Tool: `deepseek_pro_worker`
- Route: `deepseek/deepseek-v4-pro`
- Provider response model: `deepseek/deepseek-v4-pro`
- Worker returned: `DEEPSEEK_PRO_WORKER_OK`
- Usage reported by OpenRouter: 403 total tokens, cost `0.0002070396855`, `is_byok: false`

## Current Status

- Zoo-Code global skills are installed in the higher-priority Roo-compatible global skill root.
- Morph GitHub search works from Codex.
- Cheap-worker server works from Codex's corrected command environment.
- The current Codex task's already-open cheap-worker tool transport remains closed until a fresh task/app restart.
