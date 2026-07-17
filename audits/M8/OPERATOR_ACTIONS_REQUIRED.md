# Operator Actions Required — Final IDE Enrollment

**Date:** 2026-07-16  
**Status:** Cursor live_validated. The following IDEs require operator action to complete enrollment.

---

## IMMEDIATE — Requires Only a Restart

### Codex
Config **already written** to `C:\Users\ynotf\.codex\config.toml`:
```toml
[mcp_servers.agentcore-gateway]
url = "http://127.0.0.1:8080/mcp"
bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"
enabled = true
startup_timeout_sec = 300
tool_timeout_sec = 300
```
**Action required:** Start a new Codex session.  
**Validation:** In a new session, run `memory_status` → confirm `"status": "healthy"` and 10 tools listed.

---

### Claude Desktop
Config **already written** to `C:\Users\ynotf\AppData\Roaming\Claude\claude_desktop_config.json`:
- Entry `agentcore-gateway` present in `mcpServers` with `type: http`, correct URL, and materialized bearer token.
**Action required:** Quit and restart the Claude Desktop application.  
**Validation:** Open Claude Desktop → Settings → MCP → confirm `agentcore-gateway` shows as connected → run `memory_status`.

---

## IMPORT REQUIRED — Artifacts Available in `ide-profiles/`

### Claude Code
- Artifact: `ide-profiles/claude-code/MCP_CONFIG_TEMPLATE.json`
- Instructions: `ide-profiles/claude-code/INSTALL_OR_UPDATE.md`
- **Action:** Run `claude mcp add agentcore-gateway http://127.0.0.1:8080/mcp` with the bearer token header from the artifact. Restart session. Validate 10 tools.

### MiniMax
- Artifact: `ide-profiles/minimax/MCP_CONFIG_TEMPLATE.json`
- Instructions: `ide-profiles/minimax/INSTALL_OR_UPDATE.md`
- **Action:** Follow INSTALL_OR_UPDATE.md. Import artifact to live MiniMax config. Restart client. Validate 10 tools.

### Antigravity
- Artifact: `ide-profiles/antigravity/MCP_CONFIG_TEMPLATE.json`
- Instructions: `ide-profiles/antigravity/INSTALL_OR_UPDATE.md`
- **Action:** Follow INSTALL_OR_UPDATE.md. Import artifact. Restart client. Validate 10 tools.

### Mavis
- Artifact: `ide-profiles/mavis/MCP_CONFIG_TEMPLATE.json`
- Instructions: `ide-profiles/mavis/INSTALL_OR_UPDATE.md`
- **Action:** Follow INSTALL_OR_UPDATE.md. Import artifact. Restart client. Validate 10 tools.

### Open Interpreter
- Artifact: `ide-profiles/open-interpreter/MCP_CONFIG_TEMPLATE.json`
- Instructions: `ide-profiles/open-interpreter/INSTALL_OR_UPDATE.md`
- **Action:** Follow INSTALL_OR_UPDATE.md. Apply profile system message. Restart session. Validate 10 tools.

---

## Validation Steps (for all IDEs once restarted)

1. `memory_status` → `{"ok": true, "status": "healthy"}`
2. `tools/list` → exactly 10 agentcore-memory tools
3. `session_open(project_key=..., client_key=..., agent_key=...)` → session_id returned
4. `append_event(session_id=..., event_kind="test_result", idempotency_key=..., payload={})` → event_id returned
5. `startup_context(project_key=..., token_budget=500)` → L0 raw tail includes appended event
6. `retrieve_context(project_key=..., query="...")` → ok=true
7. `session_close(session_id=...)` → ok=true
8. Confirm Swarm tools absent from tool list

After each validation, update `ide-profiles/IDE_CAPABILITY_MATRIX.yaml`:
- Change `m8_enrollment: configured_restart_required` or `awaiting_operator_import` → `live_validated`
- Add `m8_validation_evidence` block with session_id, tool count, and timestamps

---

## Platform Declaration

After Codex + Claude Desktop restarts:
**GLOBAL MEMORY AND ROLLING CONTEXT FULLY DEPLOYED** (2 of 8 IDEs pending easy restarts)

After all 8 IDE validations complete:
**GLOBAL ROLLOUT COMPLETE**
