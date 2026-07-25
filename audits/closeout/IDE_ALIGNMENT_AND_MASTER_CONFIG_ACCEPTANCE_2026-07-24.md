# IDE Alignment and MASTER_CONFIG Acceptance — Closeout (2026-07-24 / 2026-07-25)

**Repo:** `D:\github\agentcore-control-plane`  
**Master:** `MASTER_CONFIG_AND_PROMPT.md` (Phase 5 rebuild)  
**Companion:** `audits/closeout/AGENTCORE_SYSTEM_HARDENING_2026-07-24.md`

---

## Per-IDE final status

| IDE | Enrollment / native status | Evidence |
| --- | --- | --- |
| **Cursor** | **live_validated** — Stage B hooks live; Continue. hard gate proven; 26/26 suite | `audits/cursor-context/CURSOR_CONTINUE_HARD_GATE_AND_STAGE_B_REGISTRATION_2026-07-24.md` |
| **Codex** | configured_restart_required — desktop packages healthy; gateway in `config.toml`; UI 14-step pending | `audits/CODEX_DESKTOP_REPAIR_2026-07-24.md` |
| **MiniMax Code** | configured_restart_required — in-app MCP repaired (VK materialize + streamable-http); CLI `daemon\cli.js` unsupported | `audits/MINIMAX_CODE_NATIVE_ACCEPTANCE_2026-07-24.md` |
| **MiniMax Classic** | awaiting_operator_cloud_mcp_enrollment — Matrix UI only; no tunnel | `audits/MINIMAX_CLASSIC_ENROLLMENT_2026-07-24.md` |
| **Open Interpreter CLI** | configured_restart_required — gateway persistent; `memory_status` native call proven; full 14-step pending | `audits/OPEN_INTERPRETER_PERSISTENCE_2026-07-24.md` |
| **Open Interpreter GUI** | unsupported_with_reason — no MCP schema | same audit |
| **Cherry Studio** | configured_restart_required — DRIFT-01 reconciled (agent/model/gateway + session schema proven); UI 14-step pending | `audits/CHERRY_TARGET_AGENT_REPAIR_2026-07-24.md` |
| **Claude Code / Desktop / Antigravity** | unchanged awaiting / configured states in matrix | `ide-profiles/IDE_CAPABILITY_MATRIX.yaml` |

---

## MASTER_CONFIG validator matrix (Phase 5)

| Validator | Result |
| --- | --- |
| `scripts/bifrost/validate_contracts.py` | OK |
| `scripts/bifrost/test_contracts.py` | PASS 124 checks |
| `scripts/render_ide_rules.py --check` | OK |
| `scripts/bifrost/validate_ide_enrollment_scope.py` | OK |
| `scripts/validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md` | PASS |
| `scripts/bifrost/validate_client_status.py` | OK |

Evidence: `audits/MASTER_CONFIG_REBUILD_2026-07-25.md`

---

## Swarm boundary section proof

`MASTER_CONFIG_AND_PROMPT.md` includes the required **SWARM DEVELOPMENT AND RUNTIME BOUNDARY** section stating that Swarm runtime processes do not use AgentCore memory/Bifrost/projections/VKs; SwarmDock/Relay/Feed remain deferred.

---

## Fresh-chat recovery proof

| IDE | Proof |
| --- | --- |
| Cursor | Continue. exact-once capture + Stage B suite (Phase 3) |
| Others | Operator-gated native Continue./lifecycle still required where status ≠ full live_validated |

---

## Cursor absolute-path rule

MASTER_CONFIG and embedded prompts require `@` + full absolute Windows paths for Cursor file/folder references.

---

## Signal

`IDE_ALIGNMENT_AND_MASTER_CONFIG_ACCEPTANCE_2026-07-25`

---

## CURSOR CONTINUATION PROMPT

```text
Continue AgentCore operator-pending gates only.
Authority: @D:\github\agentcore-control-plane\PROJECT_ANCHOR.md, @D:\github\agentcore-control-plane\DOC_AUTHORITY.md, @D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md, @D:\github\agentcore-control-plane\audits\closeout\AGENTCORE_SYSTEM_HARDENING_2026-07-24.md, @D:\github\agentcore-control-plane\audits\closeout\IDE_ALIGNMENT_AND_MASTER_CONFIG_ACCEPTANCE_2026-07-24.md.
Pick ONE pending item: MiniMax Classic Matrix enrollment, MiniMax/Cherry/Codex/OI native 14-step, LANGSMITH_API_KEY Studio browser gate, Docker disk relocation to H:\AgentRuntime\docker, G:\DatabaseBackups second copy, or controlled LangGraph pilot selection.
Do not edit PROJECT_ANCHOR.md, BLUEPRINT.md, or MILESTONES.md. Push-only git policy. No public tunnels.
```
