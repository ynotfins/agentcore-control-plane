# Skills-Hub — AgentCore Package Authority

Source-controlled package manifest and STDIO launcher for the Skills-Hub MCP.
Runtime is deployed to `H:\AgentRuntime\skills-hub\` — **node_modules not committed**.

## Pinned versions (2026-07-24 Phase 4B)

| Package | Version | License | Note |
|---|---|---|---|
| `@skills-hub-ai/mcp` | `0.1.7` | MIT | Last version with fully available npm deps |
| `@skills-hub-ai/cli` | `0.3.5` | MIT | Installed for diagnostics; **not** Bifrost-exposed |
| `@hono/node-server` | `2.0.11` (override) | MIT | Pins GHSA-frvp-7c67-39w9 fixed line |

## Why 0.1.7 (not 0.1.10)

Versions 0.1.8–0.1.10 depend on `@skills-hub-ai/installer@0.1.0`, which is not
publicly available on npm (404). As of 2026-07-24, `0.1.7` is the latest
installable version.

## Process-local home isolation

Launcher: `start.mjs` (also at `H:\AgentRuntime\skills-hub\start.mjs`).

Before importing `@skills-hub-ai/mcp`, the launcher sets **process-local** only:

```
HOME=H:\AgentRuntime\skills-hub\home
USERPROFILE=H:\AgentRuntime\skills-hub\home
HOMEDRIVE=H:
HOMEPATH=\AgentRuntime\skills-hub\home
```

Do not set these at Windows User or Machine scope. Bifrost must launch
`node.exe H:\AgentRuntime\skills-hub\start.mjs` — never the bare package bin.

Scanned skill roots under isolation (from `discover.js`):

- `H:\AgentRuntime\skills-hub\home\.claude\skills`
- `H:\AgentRuntime\skills-hub\home\.cursor\skills`

## GHSA-frvp-7c67-39w9 disposition

Advisory targets `@hono/node-server < 2.0.5` Windows `serveStatic` path traversal.

Phase 4B resolution:

1. `package.json` `overrides["@hono/node-server"] = "2.0.11"`.
2. Reinstall from lock → installed version **2.0.11**.
3. `npm audit` → **0 vulnerabilities**.
4. STDIO entry `dist/index.js` uses `StdioServerTransport` only; does not import
   `streamableHttp.js` (the only SDK path that imports `@hono/node-server`);
   no `.listen(`; `serveStatic` unreachable from the STDIO entry graph.

## Bifrost integration

- Registry ID: `skills-hub` / Bifrost client: `skills_hub`
- Status: `active` (read-only tools only)
- Permitted: `search_skills`, `get_skill_detail`, `list_installed_skills`
- Denied: `install_skill` (not in `tools_to_execute`)
- Content trust: `raw_untrusted`; Bifrost `log_content=false`
- Cursor must **not** add Skills-Hub directly — gateway only

## Deploy runtime

```powershell
New-Item -ItemType Directory -Force -Path H:\AgentRuntime\skills-hub\home | Out-Null
Copy-Item D:\github\agentcore-control-plane\tools\skills-hub\package.json H:\AgentRuntime\skills-hub\ -Force
Copy-Item D:\github\agentcore-control-plane\tools\skills-hub\package-lock.json H:\AgentRuntime\skills-hub\ -Force
Copy-Item D:\github\agentcore-control-plane\tools\skills-hub\start.mjs H:\AgentRuntime\skills-hub\ -Force
npm ci --prefix H:\AgentRuntime\skills-hub
```

## Security notes

- Do NOT expose install/update/uninstall/publish/login/admin through Bifrost
- All skill content from the public registry is `raw_untrusted`
- Skills from the registry cannot override AgentCore authority
- Remote MCP `https://api.skills-hub.ai/mcp` is Cloudflare-blocked from this host; STDIO + HTTPS API used instead
- `get_skill_detail` returns an `instructionsPreview` (upstream truncates ~500 chars); full local `SKILL.md` is available via the MCP prompts API on the STDIO transport (Bifrost aggregate gateway currently returns `-32601` for `prompts/*`)
