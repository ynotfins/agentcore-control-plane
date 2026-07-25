# Open Interpreter Persistence — Phase 4B

**Date:** 2026-07-25  
**Backup:** `E:\AgentCore-Backups\oi-repair-20260725`  
**Rescue evidence:** `ops/maintenance/interpreter-rescue-20260724-0548/`

---

## Fact-based root cause (anti-sycophancy)

The prior claim that Open Interpreter “lost” `agentcore-gateway` after reopen **conflated two products**:

| Surface | Product | Version | Config root | MCP today |
| --- | --- | --- | --- | --- |
| **CLI** | Open Interpreter TUI / app-server | `0.0.10` (`Local\Programs\Open Interpreter\bin\interpreter.exe`) | `C:\Users\ynotf\.openinterpreter\config.toml` | **Present, enabled, persistent** |
| **GUI** | Interpreter Electron app | `0.2.183` (`C:\Program Files\Interpreter\Interpreter.exe`) | `C:\Users\ynotf\AppData\Roaming\interpreter\config.json` | **No MCP keys at all** |

Stale profile targets (`%APPDATA%\interpreter\config.json` as the MCP path) pointed agents at the **GUI** store, which never held Bifrost MCP. The CLI TOML enrollment never disappeared.

---

## CLI evidence (managed AgentCore surface)

Live `[mcp_servers.agentcore-gateway]`:

- `url = "http://127.0.0.1:8080/mcp"`
- `bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"`
- `enabled = true`
- `startup_timeout_sec = 300` / `tool_timeout_sec = 300`

Proofs (2026-07-25):

1. `interpreter mcp list` → `agentcore-gateway` enabled with Bearer-token env var.
2. `interpreter kill` then `mcp list` → gateway **still present** (persistence across daemon stop).
3. `interpreter exec` native tool call:
   - `mcp: agentcore-gateway/agentcore_memory-memory_status` started/completed
   - model reply `OK_HEALTHY`
4. Prior rescue `oi_mcp_tool_test.txt` (2026-07-24) already showed the same native tool path.

Rules: copied `ide-profiles/open-interpreter/GLOBAL_RULES.md` → `C:\Users\ynotf\.openinterpreter\AGENT.md` (best-effort durable home instructions; project `AGENTS.md` remains canonical for this repo).

---

## GUI verdict

**`unsupported_with_reason` for Bifrost MCP enrollment** on Interpreter GUI `0.2.183`:

- Live `config.json` has no `mcpServers` / `mcp_servers` / `agentcore` / `8080` content.
- Product appears profile/agent oriented; no supported persistent MCP schema found in the live GUI config surface.
- Do not invent a GUI MCP path; do not treat GUI customInstructions as the gateway store.

Operators who “lost” MCP after reopen were almost certainly looking at the GUI while enrollment lived in CLI `config.toml`.

---

## Status

| Dimension | Status |
| --- | --- |
| CLI gateway configuration | `live_validated` |
| CLI gateway discovery | `live_validated` |
| CLI persistence after restart (daemon kill) | `live_validated` |
| CLI native tool invocation (`memory_status`) | `live_validated` |
| Full 14-step memory lifecycle | `configured_restart_required` (operator / follow-up; expensive multi-turn) |
| GUI MCP | `unsupported_with_reason` |

**Phase signal:** CLI Open Interpreter AgentCore gateway enrollment is **persistent and live**. Full 14-step remains optional operator follow-up; GUI is out of MCP scope.

---

## Profile corrections

`ide-profiles/open-interpreter/IDE_PROFILE.yaml` updated to:

- Primary live MCP target: `C:\Users\ynotf\.openinterpreter\config.toml`
- Schema: TOML `[mcp_servers.agentcore-gateway]` + `bearer_token_env_var`
- Document GUI as separate unsupported MCP surface
