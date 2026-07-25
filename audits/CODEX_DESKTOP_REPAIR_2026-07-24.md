# Codex Desktop Repair — Phase 4D

**Date:** 2026-07-25  
**Backup:** `E:\AgentCore-Backups\codex-repair-20260725`  
**Rescue evidence:** `ops/maintenance/codex-rescue-20260724-0144/` (sessions quarantined earlier)

---

## Fact-based status

| Surface | Evidence |
| --- | --- |
| Unified Codex desktop (MSIX) | `OpenAI.Codex` `26.715.10079.0` Status=Ok; **ChatGPT processes running** from WindowsApps package |
| ChatGPT Classic desktop | `OpenAI.ChatGPT-Desktop` `1.2026.190.0` Status=Ok; processes running |
| Standalone CLI | `C:\Users\ynotf\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` → `codex-cli 0.137.0` |
| Config home | `C:\Users\ynotf\.codex\config.toml` |
| Global rules | `C:\Users\ynotf\.codex\AGENTS.md` present (48666 bytes) |

**Assessment of prior “desktop launch failure” claim:** **Stale / superseded.** As of 2026-07-25 the official MSIX Codex/ChatGPT desktop packages are installed healthy and running. No browser substitution was used for this verification.

---

## Gateway enrollment

`[mcp_servers.agentcore-gateway]` in live `config.toml`:

- `url = "http://127.0.0.1:8080/mcp"`
- `bearer_token_env_var = "BIFROST_MCP_VIRTUAL_KEY"`
- `enabled = true`
- timeouts 300/300

`codex mcp list` shows `agentcore-gateway` **enabled** with Bearer-token auth.

Codex also lists product/plugin MCP extras (`node_repl`, `codex-security`, `sites-design-picker`, and a plugin `github` URL entry). These are Codex-managed surfaces beside the AgentCore gateway (profile allows plugin extras). No SwarmRecall/SwarmVault MCP sections in `config.toml`. Project path references to OpenClaw directories are historical worktrees, not Swarm MCP enrollment.

---

## Lifecycle

Native 14-step memory lifecycle from inside the Codex desktop UI was **not** executed in this chat (UI operator gate). CLI proves gateway discovery.

| Dimension | Status |
| --- | --- |
| Application launch | `live_validated` |
| Gateway configuration | `live_validated` |
| Gateway discovery (`mcp list`) | `live_validated` |
| Native 14-step lifecycle | `configured_restart_required` |
| Fresh-chat Continue. | `configured_restart_required` |

---

## Status signal

`CODEX_DESKTOP_LAUNCH_REPAIRED` — desktop packages healthy/running; gateway configured; full native lifecycle still operator-gated.
