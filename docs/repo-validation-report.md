# Repo Validation Report

Generated: 2026-06-29T02:23:30.4629323Z
Root: `D:\github\agentcore-control-plane`
Overall: FAIL

- PASS - core governance files: missing=none
- PASS - json parse: all json parsed
- PASS - no hard-coded secrets: no secret-like literals found
- PASS - correct env references only: all placeholder env vars are allowlisted
- PASS - Context7 retired from managed routing: context7 is not active or emitted
- PASS - correct Artiforge naming: artiforge is the only current managed name
- PASS - Composio quarantined: supervisor and registry lifecycle are quarantined; renderers do not emit composio
- PASS - global-memory-gateway primary: gateway is critical/active and raw Mem0 is quarantined
- PASS - critical tool set: missing=none
- PASS - live Codex routing set: missing=none; active=arabold-docs, artiforge, codex-security, filesystem, github, global-memory-gateway, node_repl, obsidian-vault, playwright, sequential-thinking, serena
- PASS - live Codex retired servers absent: no retired Codex servers are active
- PASS - live Codex server budget: count=11 limit=11
- FAIL - AgentCore PostgreSQL listener: no listener on 127.0.0.1:55432
- PASS - Postgres startup ownership: state=Ready; last_result=4294967295; action=powershell.exe -NoProfile -ExecutionPolicy Bypass -File "D:\github\agentcore-control-plane\ops\Start-AgentCorePostgres.ps1" -StartIfStopped
- PASS - approved renderer server sets: renderers\cursor-global.mcp.json count=8; renderers\openclaw.openclaw.fragment.json count=9; renderers\open-interpreter.config.fragment.json count=3; renderers\minimax.mcp.json count=7; renderers\antigravity.mcp_config.json count=8
- PASS - managed live client configs readable: Cursor count=8; OpenClaw count=9; Open Interpreter count=3; MiniMax Code count=10; MiniMax Code Legacy count=10; Antigravity count=8; Antigravity Roaming count=8
- PASS - gateway renderer args explicit: all rendered gateway configs include --project-id codex-managed and --platform
- PASS - no broad SwarmRecall MCP rollout: renderers do not expose SwarmRecall directly
- PASS - live managed MCP configs sanitized: no raw MCP secrets or retired hosted routes found
- PASS - vendored MCP installs: arabold-docs and context-fabric entrypoints exist
- PASS - managed files re-locked: all managed files are read-only
