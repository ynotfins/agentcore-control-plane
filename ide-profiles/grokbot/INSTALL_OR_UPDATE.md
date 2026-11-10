# Install / Update — Grok Bot

Installation mode: **UI_only** for MCP; **manual_import** for primary-Bot custom rules.

1. Keep Grok Bot updated via WinGet `xAI.GrokBot` or the desktop updater.
2. Set Windows User env `BIFROST_MCP_VK_GROKBOT` (never commit the value).
3. Confirm Cloudflare connector task `\AgentCore-Grokbot-Cloudflare-Tunnel` is Running / Hidden (do not recreate the tunnel routinely).
4. Follow `MCP_ENROLLMENT_UI.md` for the custom connector — canonical cloud URL `https://agentcore-grokbot.4axe.com/mcp`, header `x-bf-vk` = raw key.
5. Import `GLOBAL_RULES.md` into the primary Bot custom rules / memory as operator policy.
6. Restart Grok Bot fully after env or connector changes.
7. Run checks in `VALIDATION.md`.
8. When Cursor is unavailable for Bifrost/control-plane work, follow `BIFROST_STANDING_BACKUP.md` (standing backup 1B) and use `ops/bifrost/Invoke-AgentCoreBifrostLifecycleForGrokbot.ps1` for gateway Start/Stop/Status/Test on ChaosCentral.
