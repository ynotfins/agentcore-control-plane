# AgentCore Bifrost Runtime Repair Evidence — 2026-07-14

## Scope

Repair the actual runtime cause of Cursor `agentcore-gateway` connection refusal and complete the global Cursor MCP cutover.

## Preserved State

| Item | Value |
| -- | -- |
| Repo | `D:\github\agentcore-control-plane` |
| Branch | `feature/bifrost-mcp-gateway-cutover` |
| Starting HEAD | `f4298019f045c0fd63525a7251c5c6d1322c3368` |
| Cursor global MCP | `C:\Users\ynotf\.cursor\mcp.json` |
| Original Cursor MCP SHA-256 | `36C7C42D38F7E0A31627F9522A520CAED96E30978AC119C5E005B4C33F33F358` |
| Cursor MCP backup | `E:\AgentCore-Backups\cursor-bifrost-runtime-repair\mcp.json.20260714-020459.bak` |
| Backup SHA-256 | `36C7C42D38F7E0A31627F9522A520CAED96E30978AC119C5E005B4C33F33F358` |
| Final Cursor MCP SHA-256 | `55498B4E009C7A82BBB7619034490FB94D971BD0C2AEA1B9BB779EE1C1A8A9DA` |

No secret values were printed or written to evidence.

## Root Cause

Cursor showed `net::ERR_CONNECTION_REFUSED` because nothing was accepting connections on `127.0.0.1:8080`.

Investigation showed:

- No listener on TCP 8080 by `Get-NetTCPConnection`, `netstat`, `Test-NetConnection`, or direct `/health`.
- No durable `bifrost-http.exe` process was running.
- The scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` existed but was not the active runtime owner.
- Foreground launch of the pinned binary with `-app-dir H:\AgentRuntime\bifrost -host 127.0.0.1 -port 8080` succeeded, proving config/schema/VK loading were not the cause.
- The previous start wrapper could start the scheduled task, but failed to recognize health, timed out, and launched a direct fallback. That fallback killed the working task-owned listener, recreating the connection-refused state.

## Runtime Fix

Changed the native Windows startup owner to keep Bifrost in the scheduled task foreground:

- `ops\bifrost\Launch-AgentCoreBifrostGateway.ps1` now runs `bifrost-http.exe` in the foreground and exits with the Bifrost exit code.
- Task Scheduler can restart the launcher on unexpected failure.
- `ops\bifrost\Start-AgentCoreBifrostGateway.ps1` no longer hides failures by falling back after a healthy scheduled task start.
- `ops\bifrost\Install-AgentCoreBifrostGateway.ps1` registers the task with full PowerShell path, working directory, runtime root, host, and port.

## Runtime Owner

| Item | Value |
| -- | -- |
| Startup owner | Windows Scheduled Task |
| Task | `\AgentCore\AgentCore-Bifrost-Gateway` |
| Executable | `C:\Program Files\PowerShell\7\pwsh.exe` |
| Launcher | `D:\github\agentcore-control-plane\ops\bifrost\Launch-AgentCoreBifrostGateway.ps1` |
| Bifrost binary | `H:\AgentRuntime\bifrost\bin\bifrost-http.exe` |
| Version | `v2.0.0-prerelease1` |
| App dir | `H:\AgentRuntime\bifrost` |
| Config | `H:\AgentRuntime\bifrost\config.json` |
| Config DB | `H:\AgentRuntime\bifrost\data\config.db` |
| Logs DB | `H:\AgentRuntime\bifrost\logs\logs.db` |
| Bind | `127.0.0.1:8080` |

Commands:

```powershell
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Start-AgentCoreBifrostGateway.ps1
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Stop-AgentCoreBifrostGateway.ps1
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Test-AgentCoreBifrostGateway.ps1
Get-ScheduledTask -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
Get-ScheduledTaskInfo -TaskPath '\AgentCore\' -TaskName 'AgentCore-Bifrost-Gateway'
```

Logs:

```text
H:\AgentRuntime\bifrost\logs\bifrost-gateway.stdout.log
H:\AgentRuntime\bifrost\logs\bifrost-gateway.stderr.log
H:\AgentRuntime\bifrost\logs\logs.db
```

Managed restart evidence:

- Before restart: task `Running`, Bifrost PID `38584`, `/health` 200.
- Managed restart command path: `Stop-AgentCoreBifrostGateway.ps1` then `Start-AgentCoreBifrostGateway.ps1`.
- After restart: task `Running`, Bifrost PID `36816`, `/health` 200.
- Five-minute stability gate: after 322 seconds, same PID `36816`, task `Running`, `/health` 200.

## Direct MCP Validation

After managed restart:

- `/health` returned `200`.
- MCP `initialize` accepted protocol version `2025-06-18`.
- `notifications/initialized` was accepted.
- `tools/list` returned `127` visible tools for the builder VK.
- Safe read-only call `arabold_docs-list_libraries` succeeded.

Visible prefix counts:

| Prefix | Count |
| -- | --: |
| `arabold_docs` | 10 |
| `depwire` | 23 |
| `tentra` | 35 |
| `sequential_thinking` | 1 |
| `context_fabric` | 5 |
| `filesystem` | 14 |
| `playwright` | 24 |
| `cursor_agent_mcp` | 9 |
| `agentcore_memory` | 2 |
| `agentcore_project_router` | 4 |
| `swarm` | 0 |

Connected clients:

- `agentcore_memory`
- `agentcore_project_router`
- `arabold_docs`
- `context_fabric`
- `cursor_agent_mcp`
- `depwire`
- `filesystem`
- `playwright`
- `sequential_thinking`
- `tentra`

Disconnected upstream caveats:

- `obsidian_vault`: Bifrost upstream reconnect timed out.
- `serena`: Bifrost upstream reconnect timed out.

The gateway itself is healthy; these are separate upstream health issues.

## MCP_DOCKER Disposition

The Cursor `MCP_DOCKER` profile `r3lentless_grind` included:

- `playwright` — already behind Bifrost.
- `sequentialthinking` — already behind Bifrost.
- `context7` — superseded by Arabold Docs in AgentCore.
- `obsidian` — overlaps the AgentCore Obsidian upstream.
- `desktop-commander` — broken in Cursor logs due missing `desktop-commander.paths`; overlaps filesystem/process capabilities and is not approved as a second baseline gateway.

No unique required capability justified keeping `MCP_DOCKER` active. It was removed from global Cursor MCP. Backup is the rollback path.

## Final Cursor Global MCP

`C:\Users\ynotf\.cursor\mcp.json` now contains exactly one MCP server:

```json
{
  "mcpServers": {
    "agentcore-gateway": {
      "type": "http",
      "url": "http://127.0.0.1:8080/mcp",
      "headers": {
        "Authorization": "Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}"
      },
      "timeout": 300
    }
  }
}
```

Validation:

- JSON parse OK.
- One `mcpServers` entry.
- One `agentcore-gateway` key.
- No `MCP_DOCKER`.
- No embedded secret literal.
- No active project-level duplicate found under `D:\github`.
- Cursor MCP registry observed `user-agentcore-gateway` as ready after the edit.
- Safe Cursor-layer tool call `agentcore_memory-memory_status` succeeded through `agentcore-gateway`.

## Swarm Boundary

SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, and ClawX were not modified.
