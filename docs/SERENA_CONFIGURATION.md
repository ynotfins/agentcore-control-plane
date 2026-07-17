# Serena MCP Configuration

This document is the AgentCore source-of-truth for Serena MCP setup on CHAOSCENTRAL.

## Current Authority

- Master prompt: `D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md`
- Machine contract: `D:\github\agentcore-control-plane\contracts\master-mcp-server-config.json`
- Renderers:
  - `D:\github\agentcore-control-plane\renderers\cursor-global.mcp.json`
  - `D:\github\agentcore-control-plane\renderers\openclaw.openclaw.fragment.json`
  - `D:\github\agentcore-control-plane\renderers\minimax.mcp.json`
  - `D:\github\agentcore-control-plane\renderers\open-interpreter.config.fragment.json`
  - `D:\github\agentcore-control-plane\renderers\antigravity.mcp_config.json`
- Serena upstream docs:
  - `https://oraios.github.io/serena/02-usage/020_running.html`
  - `https://oraios.github.io/serena/02-usage/030_clients.html`
  - `https://oraios.github.io/serena/02-usage/060_dashboard.html`

## Canonical Runtime

Use the installed Serena executable, not git `uvx`, in durable IDE configs:

```text
C:\Users\ynotf\AppData\Roaming\uv\tools\serena-agent\Scripts\serena.exe
```

Default JSON MCP shape:

```json
{
  "serena": {
    "type": "stdio",
    "command": "C:\\Users\\ynotf\\AppData\\Roaming\\uv\\tools\\serena-agent\\Scripts\\serena.exe",
    "args": [
      "start-mcp-server",
      "--transport",
      "stdio",
      "--context",
      "ide"
    ]
  }
}
```

Codex TOML shape:

```toml
[mcp_servers.serena]
command = "C:\\Users\\ynotf\\AppData\\Roaming\\uv\\tools\\serena-agent\\Scripts\\serena.exe"
args = ["start-mcp-server", "--transport", "stdio", "--context", "codex", "--project-from-cwd"]
startup_timeout_sec = 30.0
tool_timeout_sec = 300.0
```

## Forbidden Durable Launchers

Do not emit these as active launcher commands in managed renderers, live IDE configs, docs, or prompts:

```text
uvx --from git+https://github.com/oraios/serena
git+https://github.com/oraios/serena
--context ide-assistant
```

Git `uvx` is only acceptable for one-off upstream source-version testing. It is not a default AgentCore launcher.

## Lifecycle Policy

Default transport is `stdio`.

In `stdio` mode, the IDE/client starts Serena as a subprocess and owns that subprocess lifecycle. A client may keep one Serena subprocess alive for an active MCP session and reuse it for later Serena tool calls in that same session, or close it when the MCP session ends. It must not repeatedly spawn new permanent Serena processes while leaving old disconnected instances running.

`streamable-http` is allowed only for explicit same-project multi-client sessions. Serena is stateful and only one coding project can be active in one server instance, so one machine-wide HTTP Serena daemon is not valid for unrelated projects.

## Context Mapping

- Codex: `codex`, with `--project-from-cwd` when launched from the target repo root.
- Claude Code: `claude-code`, with `--project-from-cwd` when launched from the target repo root.
- Antigravity / Gemini: `antigravity`, without `--project-from-cwd`; prompt the agent to activate the current project with Serena after startup.
- Cursor, OpenClaw, MiniMax, Mavis, and Open Interpreter: `ide`, without `--project-from-cwd` unless the client launch root is proven.
- Claude Desktop and VS Code: no default Serena until a supported MCP surface and code-editing use case are confirmed.
- Trae: removed from this workstation on 2026-07-07 and is not a Serena rollout target.

## Dashboard Policy

Serena global config at `C:\Users\ynotf\.serena\serena_config.yml` should use:

```yaml
gui_log_window: false
web_dashboard: true
web_dashboard_open_on_launch: false
web_dashboard_interface: browser
```

Do not use `tray_manager` as the default. It is Windows-tested but experimental and can hide process fan-out during multi-IDE rollouts.

## Agent Usage Policy

Use Serena for project-scoped semantic code intelligence:

- Project activation and onboarding
- Symbol overviews
- Symbol lookup
- Reference discovery
- Diagnostics
- Symbol-aware edits
- Project-local Serena memory

Do not use Serena memory as the primary cross-project memory database. Durable cross-agent memory routes through the current AgentCore native memory baseline.

## Validation

Config scan:

```powershell
$paths = @(
  'C:\Users\ynotf\.codex\config.toml',
  'C:\Users\ynotf\.cursor\mcp.json',
  'C:\Users\ynotf\.openclaw\openclaw.json',
  'C:\Users\ynotf\.minimax\mcp\mcp.json',
  'C:\Users\ynotf\.mavis\mcp\mcp.json',
  'C:\Users\ynotf\.gemini\config\mcp_config.json',
  'C:\Users\ynotf\AppData\Roaming\Antigravity\User\mcp.json',
  'C:\Users\ynotf\.claude\config.json',
  'C:\Users\ynotf\AppData\Roaming\interpreter\config.json'
)
foreach ($path in $paths) {
  if (Test-Path -LiteralPath $path) {
    $text = Get-Content -LiteralPath $path -Raw
    if ($text -match 'git\+https://github.com/oraios/serena|ide-assistant') {
      Write-Output "STALE $path"
    }
  }
}
```

Process audit:

```powershell
Get-CimInstance Win32_Process |
  Where-Object { $_.CommandLine -match 'serena|oraios/serena|start-mcp-server' } |
  Select-Object ProcessId,Name,ParentProcessId,CommandLine
```

Pass criteria:

- No managed config contains the git `uvx` Serena launcher.
- No managed config uses `ide-assistant`.
- Live Serena launches use the installed `serena.exe` path.
- Active Serena process count matches active IDE/session use or documented same-project HTTP daemons.
- No Trae process or config is part of the active Serena rollout.
