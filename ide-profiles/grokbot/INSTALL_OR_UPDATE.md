# Install / Update — Grok Bot

Installation mode: **UI_only** for MCP; **manual_import** for primary-Bot custom rules.

1. Keep Grok Bot updated via WinGet `xAI.GrokBot` or the desktop updater.
2. Set Windows User env `BIFROST_MCP_VK_GROKBOT` (never commit the value).
3. Follow `MCP_ENROLLMENT_UI.md` for the custom connector.
4. Import `GLOBAL_RULES.md` into the primary Bot custom rules / memory as operator policy.
5. Restart Grok Bot fully after env or connector changes.
6. Run checks in `VALIDATION.md`.
