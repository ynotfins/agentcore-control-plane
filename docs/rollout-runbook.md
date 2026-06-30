# Rollout Runbook

Manual corrective one-liner for OpenClaw Artiforge while automated rollout is gated: set `mcp.servers.artiforge` to `{ "type": "http", "url": "https://tools.artiforge.ai/mcp?pat=${env:ARTIFORGE_PAT}" }`.

1. Fix any blockers in `D:\github\agentcore-control-plane\artifacts\final-status.json` for source-repo validation.
2. Use `D:\github\agentcore-control-plane` as the canonical Git source for docs, renderers, contracts, and validators.
3. Treat `D:\MCP-Control-Plane` as the current live ops root for scheduled tasks, WAL archiving, and approved live rollout steps until migration is explicitly approved.
4. Restart Cursor, Open Interpreter, MiniMax Code, OpenClaw, and Android Studio after config changes.
5. Re-run probes and compare `D:\github\agentcore-control-plane\artifacts\drift-report.json`.

Rollback copies are under the `rollback` location in `D:\github\agentcore-control-plane\artifacts\backup-manifest.json`.
