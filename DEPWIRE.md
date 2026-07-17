# DEPWIRE.md

## Bifrost cutover note (2026-07-12)

After the AgentCore Bifrost MCP Gateway cutover, **normal IDE access to Depwire is through `agentcore-gateway`** (`http://127.0.0.1:8080/mcp`). See `docs/bifrost/DEPWIRE_RECONCILIATION.md` and `contracts/bifrost-upstream-mcp-registry.json` (`depwire`, `depwire-cloud`).

**Local Depwire CLI/MCP remains available for diagnostics**, offline work, and exact workspace graphs when the gateway path is down. Do not permanently re-paste a full direct Depwire + multi-server baseline into non-Swarm IDE configs as the normal architecture. Depwire Cloud stays deferred in the registry until enabled/healthy.

## Purpose

Depwire is the deterministic dependency-intelligence layer for AI coding tools. Use it to understand architecture, dependency impact, blast radius, health score, dead code, security risk, and multi-agent file coordination before agents modify code.

Depwire should be used beside the existing tool stack:

- **Depwire via agentcore-gateway** (primary after cutover): project-router wrapper → local `depwire mcp`.
- **Depwire local (diagnostic)**: exact current-workspace dependency graph / CLI.
- **Depwire cloud**: persistent Depwire Cloud graph/chat across sessions (deferred until registry-enabled).
- **Serena**: semantic repo navigation and editing context (also via gateway + project router).
- **arabold-docs**: latest external documentation (via gateway).
- **Git/tests**: final proof.

## Key decision: API key strategy

Depwire's docs/settings page show a single placeholder:

```json
"Authorization": "Bearer YOUR_API_KEY"
```

The docs do **not** explicitly say whether all IDEs should share one key or each IDE should have its own key.

Recommended setup:

1. **Use one shared desktop key first** if the goal is fastest reliable setup:
   - Windows environment variable: `DEPWIRE_API_KEY`
   - Use this for Cursor, Claude Desktop, MiniMax, Antigravity, and other desktop IDEs while validating.
2. **Use separate keys later** if better audit/revocation control is needed:
   - `DEPWIRE_API_KEY_CURSOR`
   - `DEPWIRE_API_KEY_CODEX`
   - `DEPWIRE_API_KEY_MINIMAX`
   - `DEPWIRE_API_KEY_CLAUDE`
3. **Always use separate keys for GitHub Actions / CI**:
   - Do not reuse a desktop IDE key in GitHub Actions.
   - Use repo-specific secrets when possible.

Using the same desktop key does not make the IDEs smarter. Using separate keys does not split the Depwire account graph. The key authenticates the client; the useful intelligence comes from the connected Depwire Cloud graph and/or the local dependency graph.

## Cursor install: Depwire Cloud MCP (rollback/diagnostic reference only)

> **Not the normal architecture.** Normal Depwire access is through `agentcore-gateway`; do not add
> direct `depwire-cloud` or `depwire-local` entries to non-Swarm IDE configs except as an
> operator-approved temporary diagnostic, and remove them afterward. Depwire Cloud remains
> deferred/`enabled=false` in the registry.

Use this only when the operator explicitly approves a temporary direct Cloud connection.

```json
{
  "mcpServers": {
    "depwire-cloud": {
      "url": "https://api.depwire.dev/mcp",
      "headers": {
        "Authorization": "Bearer ${env:DEPWIRE_API_KEY}"
      }
    }
  }
}
```

If Cursor does not resolve `${env:DEPWIRE_API_KEY}` in headers, use Cursor's MCP/secret/input-variable UI. Never paste a literal key into a config file or commit one to Git.

After changing Windows environment variables, fully restart Cursor.

## Local install: Depwire CLI/MCP (diagnostic fallback)

Depwire local is useful even with Pro because it gives exact current-workspace analysis without depending on cloud state.

Install globally:

```powershell
npm install -g depwire-cli
depwire --version
```

Recommended wrapper:

`D:\MCP-Control-Plane\wrappers\depwire-mcp.cmd`

```bat
@echo off
setlocal

where node >nul 2>nul
if errorlevel 1 (
  echo [depwire-mcp] Node.js was not found on PATH. 1>&2
  exit /b 1
)

where depwire >nul 2>nul
if errorlevel 1 (
  echo [depwire-mcp] depwire was not found. Run: npm install -g depwire-cli 1>&2
  exit /b 1
)

depwire mcp %*
```

Cursor local MCP config:

```json
{
  "mcpServers": {
    "depwire-local": {
      "command": "D:\\MCP-Control-Plane\\wrappers\\depwire-mcp.cmd",
      "args": []
    }
  }
}
```

## Combined Cursor config (rollback/diagnostic reference only)

> Not the normal architecture — normal access is via `agentcore-gateway`. Temporary diagnostic use only:

```json
{
  "mcpServers": {
    "depwire-local": {
      "command": "D:\\MCP-Control-Plane\\wrappers\\depwire-mcp.cmd",
      "args": []
    },
    "depwire-cloud": {
      "url": "https://api.depwire.dev/mcp",
      "headers": {
        "Authorization": "Bearer ${env:DEPWIRE_API_KEY}"
      }
    }
  }
}
```

## Telemetry policy

Telemetry should remain **on** unless there is a specific security reason to disable it.

To keep telemetry on:

- Do not set `DEPWIRE_NO_TELEMETRY=1`
- Do not set `DEPWIRE_NO_TELEMETRY=true`
- Do not set `DO_NOT_TRACK=1` if the goal is to allow telemetry

PowerShell check:

```powershell
[Environment]::GetEnvironmentVariable("DEPWIRE_NO_TELEMETRY","User")
[Environment]::GetEnvironmentVariable("DO_NOT_TRACK","User")
[Environment]::GetEnvironmentVariable("DEPWIRE_API_KEY","User")
```

If telemetry was previously disabled:

```powershell
[Environment]::SetEnvironmentVariable("DEPWIRE_NO_TELEMETRY", $null, "User")
[Environment]::SetEnvironmentVariable("DO_NOT_TRACK", $null, "User")
```

Then restart all IDEs and terminals.

## How IDE agents should use Depwire

Agents must use Depwire before risky structural edits.

Required before deleting, renaming, moving, splitting, merging, heavily refactoring, changing public APIs, changing routes, changing shared utilities, changing config loaders, changing database modules, or changing MCP/server entry points:

1. Prefer `depwire-local` for exact current workspace analysis.
2. Use `depwire-cloud` for persistent cloud graph context.
3. Use `get_file_context` before editing unfamiliar files.
4. Use `get_dependents` before deleting or renaming exported symbols.
5. Use `impact_analysis` or `simulate_change` before structural edits.
6. Use `verify_change` before applying large multi-file changes.
7. Use `security_scan` for security-sensitive files.
8. Use `claim_files` before multi-agent edits.
9. Use `release_files` after edits are complete.
10. Use `record_decision` for architecture decisions future agents must know.

If Depwire is unavailable, do not perform risky structural edits. Stop and report that deterministic architecture verification could not be completed.

When using `depwire-cloud`, always specify the current repository/project name. Do not assume the cloud graph refers to the active local workspace.

## Per-repo local routine

Before heavy coding in a repo:

```powershell
cd D:\github\your-repo
depwire parse .
depwire health .
depwire security .
```

For large repos, parsing first creates `depwire-output.json`, allowing the local MCP server to load faster.

## Git ignore

Add to project `.gitignore`:

```gitignore
.depwire/claims.jsonl
.depwire/decisions.jsonl
depwire-output.json
```

`claims.jsonl` and `decisions.jsonl` are runtime coordination state. `depwire-output.json` is a local graph cache; ignore it unless the project intentionally commits graph snapshots.

## Smoke test checklist

1. Confirm global install:
   ```powershell
   npm list -g depwire-cli
   depwire --version
   ```
2. Confirm environment variable:
   ```powershell
   [Environment]::GetEnvironmentVariable("DEPWIRE_API_KEY","User")
   ```
3. Confirm telemetry is not disabled:
   ```powershell
   [Environment]::GetEnvironmentVariable("DEPWIRE_NO_TELEMETRY","User")
   [Environment]::GetEnvironmentVariable("DO_NOT_TRACK","User")
   ```
4. Restart Cursor.
5. Confirm the `depwire` upstream is healthy through `agentcore-gateway` (Depwire Cloud remains deferred in the registry; only check `depwire-cloud` if the operator has enabled it).
6. Ask Cursor:
   ```text
   Use Depwire Cloud to identify the most critical files in the current repo. Do not edit files.
   ```
7. Test local:
   ```text
   Use depwire-local to connect to this workspace and summarize the architecture. Do not edit files.
   ```
8. Run a safe refactor simulation:
   ```text
   Use Depwire to simulate renaming or deleting a low-risk file and report affected files, broken imports, health-score effect, and whether the change is safe. Do not edit files.
   ```

## GitHub Actions

Use a separate Depwire API key for CI/CD. Do not reuse desktop IDE keys.

In GitHub repo secrets, use:

```text
DEPWIRE_API_KEY
DEPWIRE_REPO_ID
```

Use the workflow shown in the Depwire Cloud settings page for the specific repo.