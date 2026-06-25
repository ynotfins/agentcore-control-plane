# Rollout Runbook

Manual corrective one-liner for OpenClaw Artiforge while automated rollout is gated: set `mcp.servers.artiforge` to `{ "type": "http", "url": "https://tools.artiforge.ai/mcp?pat=${env:ARTIFORGE_PAT}" }`.

1. Fix any blockers in `D:\MCP-Control-Plane\artifacts\final-status.json`.
2. Run `D:\Codex_Managed\.venv\Scripts\python.exe D:\MCP-Control-Plane\scripts\mcp_control_plane.py --apply` from a fresh shell.
3. Confirm `D:\MCP-Control-Plane\artifacts\probe-results.json` has no `auth_failed` critical servers.
4. Restart Cursor, Open Interpreter, MiniMax Code, OpenClaw, and Android Studio after config changes.
5. Re-run probes and compare `D:\MCP-Control-Plane\artifacts\drift-report.json`.

Rollback copies are under the `rollback` location in `D:\MCP-Control-Plane\artifacts\backup-manifest.json`.
