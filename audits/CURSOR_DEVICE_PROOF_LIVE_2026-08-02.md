# Cursor device proof — live execution (2026-08-02)

Machine-readable companion: `audits/CURSOR_DEVICE_PROOF_LIVE_2026-08-02.json`

## Scope

Live proof that Cursor hooks are registered, `sessionStart` bootstraps `agentcore-context-engine`, and `agentcore_memory` device-identity enforcement behaves correctly under temporary `required` mode. No secrets (VK/passwords/private keys) were captured.

## Commits

| Repo | SHA |
|------|-----|
| agentcore-control-plane | `dbc32f1d4a1c8fd239a93db6632eb4ecc7edc3b9` |
| agentcore-context-engine | `57c32fe79a6bd20d45b535f00f101a8540603f9f` |

## Part 1 — Cursor hooks

**Config:** `.cursor/hooks.json`

**Registered events (7):**

1. `sessionStart`
2. `beforeSubmitPrompt`
3. `preToolUse`
4. `beforeShellExecution`
5. `afterFileEdit`
6. `postToolUse`
7. `stop`

**Smoke:** `sessionStart` via `.cursor/hooks/agentcore-hook.ps1` with workspace `D:\github\agentcore-context-engine`.

| Field | Value |
|-------|-------|
| Exit code | 0 |
| `AGENTCORE_BOOTSTRAP_OK` | `1` |
| `AGENTCORE_PROJECT_KEY` | `agentcore-context-engine` |
| `AGENTCORE_CONTEXT_ENGINE` | `1` |
| Session id (returned) | `adf011ef-00e6-40b0-80b1-ca2224e93f59` |

## Part 2 — Device identity enforcement (temporary `required`)

Executed with `PYTHONPATH=scripts;scripts/agentcore_memory` plus installed `agentcore-context-engine` packages. Device manifest from `EnginePaths.discover()` → `...\AgentCoreContextEngine\device.json`.

| Step | Result |
|------|--------|
| `set_enforcement("required")` | OK |
| Signed `session_open` | OK — `legacy_compat: false`, Ed25519 key bound |
| Unsigned `session_open` | `device_assertion_required` |
| Replay same assertion (identical args) | `device_assertion_replay` |
| Assertion `project_key` mismatch | `device_assertion_project_mismatch` |
| `set_enforcement("legacy_compat", window_hours=168)` | OK — restored |

**Enforcement after proof:** `legacy_compat` (migration window ends 2026-08-09).

## Residual note

Hook-mediated Cursor paths sign memory calls via `scripts/agentcore_cursor/gateway.py`. Direct IDE MCP tool calls to `agentcore-memory` through Bifrost still bypass hook signing — see `audits/BIFROST_DEVICE_IDENTITY_BINDING_OPTIONS_2026-08-02.md`.
