# Skills-Hub — AgentCore Package Authority

Source-controlled package manifest for the Skills-Hub MCP and CLI packages.
Runtime is deployed to `H:\AgentRuntime\skills-hub\` — **not committed to Git**.

## Pinned versions (2026-07-24)

| Package | Version | License | Note |
|---|---|---|---|
| `@skills-hub-ai/mcp` | `0.1.7` | MIT | Last version with fully available npm deps |
| `@skills-hub-ai/cli` | `0.3.5` | MIT | Last version with fully available npm deps |

## Why 0.1.7 (not 0.1.10)

Versions 0.1.8–0.1.10 added a dependency on `@skills-hub-ai/installer@0.1.0` which is
not publicly available on npm (returns 404). As of 2026-07-24, `0.1.7` is the latest
installable version.

## Known vulnerability

`@hono/node-server <2.0.5` — Path traversal on Windows via encoded backslash (`%5C`).  
GHSA: `GHSA-frvp-7c67-39w9` | Severity: moderate | No upstream fix available.

**Mitigation**: Skills-Hub runs STDIO-only under Bifrost (not as an HTTP server). The
vulnerable `@hono/node-server` `serve-static` middleware is not invoked in STDIO mode.

## Bifrost integration

- Status: `dormant` (disabled by default)
- Upstream ID: `skills-hub`
- Bifrost client name: `skills_hub`
- Enable only after verifying skill-scan directory scope (see registry notes)
- Content trust class: `raw_untrusted`

## Deploy runtime

```powershell
# Deploy to AgentRuntime (from this directory)
npm install --prefix H:\AgentRuntime\skills-hub
```

## Security notes

- Do NOT expose Skills-Hub's install/publish capabilities through Bifrost
- All skill content from the public registry is `raw_untrusted`
- Skills from the registry cannot override AgentCore authority
- `~/.cursor/skills/` has been quarantined (empty); `~/.claude/skills/` contains Codex skills
