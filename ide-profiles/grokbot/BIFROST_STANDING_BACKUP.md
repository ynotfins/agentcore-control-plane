# Bifrost standing backup — Grok Bot (operator decision 1B)

Use when **Devin is unavailable** (operator says so or Devin is not usable) and Bifrost / control-plane recovery is needed. Devin remains **primary** when healthy (operator decision 2026-11-19; Cursor no longer holds this role).

## Authority

- Governance: `governance/proposals/2026-11-09-grokbot-standing-bifrost-backup.md`
- Policy: `GLOBAL_RULES.md` (Bifrost ownership rule)
- Stage B stays **Cursor-only** — do not disable hooks; use Morph/Code Mode if a write is blocked.

## Enrolled write roots

| project_key | Path |
| --- | --- |
| `agentcore-control-plane` | `D:\github\agentcore-control-plane` |
| `postgresql18-control-plane` | `D:\postgreSQL18-control-plane` |

## MCP (unchanged)

One connector: `agentcore-gateway` at `https://agentcore-grokbot.4axe.com/mcp` with `x-bf-vk` = raw `BIFROST_MCP_VK_GROKBOT`. Do not add operator-router or project-router to the Grokbot profile.

## Workstation lifecycle

```powershell
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1 -Action Status
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1 -Action Test
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1 -Action Start
pwsh -NoProfile -File D:\github\agentcore-control-plane\ops\bifrost\Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1 -Action Stop
```

Log: `F:\AgentCore\runtime\bifrost\logs\grokbot-lifecycle.log`.

When Devin returns, hand off to Devin for primary acceptance per `AGENTS.md`.

## Cloud connector

Task `\AgentCore-Grokbot-Cloudflare-Tunnel` must be Running and Hidden. See `INSTALL_OR_UPDATE.md` and `VALIDATION.md`.
