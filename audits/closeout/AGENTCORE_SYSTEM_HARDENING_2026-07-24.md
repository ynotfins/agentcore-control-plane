# AgentCore System Hardening — Closeout (2026-07-24 / 2026-07-25)

**Repo:** `D:\github\agentcore-control-plane`  
**HEAD at closeout:** `0399b4d` (Phase 9) + this closeout commit  
**Health snapshot:** `AGENTCORE_HEALTH_OK` (memory=10, router=4, skills_hub=3, tool_total=161)

---

## Phase evidence index

| Phase | Status | Primary evidence |
| --- | --- | --- |
| 1 Source cleanup | DONE | commit `c06425b` |
| 2 Bifrost hardening | DONE | `audits/OPENROUTER_PROVIDER_REPAIR_2026-07-24.md`, commit `99d21f5` |
| 3 Cursor Stage B | DONE | `audits/cursor-context/CURSOR_CONTINUE_HARD_GATE_AND_STAGE_B_REGISTRATION_2026-07-24.md` |
| 4A MiniMax Code | DONE | `audits/MINIMAX_CODE_NATIVE_ACCEPTANCE_2026-07-24.md` |
| 4B Open Interpreter | DONE | `audits/OPEN_INTERPRETER_PERSISTENCE_2026-07-24.md` |
| 4C Cherry | DONE | `audits/CHERRY_TARGET_AGENT_REPAIR_2026-07-24.md` |
| 4D Codex | DONE | `audits/CODEX_DESKTOP_REPAIR_2026-07-24.md` |
| 4E MiniMax Classic | DONE (UI-gated) | `audits/MINIMAX_CLASSIC_ENROLLMENT_2026-07-24.md` |
| 5 MASTER_CONFIG | DONE | `audits/MASTER_CONFIG_REBUILD_2026-07-25.md` |
| 6 Foundation health | DONE | `audits/FOUNDATION_HEALTH_HARDENING_2026-07-24.md` |
| 7 Wildcard + Steward | DONE (baseline) | `audits/WILDCARD_AND_CONTEXT_STEWARD_2026-07-24.md` |
| 8 Docker + New API | DONE (audit) | `audits/DOCKER_AND_NEWAPI_2026-07-24.md` |
| 9 Studio + pilot | DONE (local gate) | `audits/LANGSMITH_STUDIO_AND_PILOT_2026-07-24.md` |

---

## Service health (closeout)

| Component | Result |
| --- | --- |
| PostgreSQL 18 `AgentCore-PostgreSQL18` | Running / Automatic; `:55433` open |
| Bifrost `\AgentCore\AgentCore-Bifrost-Gateway` | Running; `/health` ok |
| Tool groups | `agentcore_memory=10`, `agentcore_project_router=4`, `skills_hub=3` |
| Skills-Hub start script | present |
| LangGraph Studio env | `LANGSMITH_TRACING=false`, `LANGGRAPH_CLI_NO_ANALYTICS=1` |
| Backup `E:\DatabaseBackups` | present |
| Backup `G:\DatabaseBackups` | **MISSING** (WARN) |
| Latest restore-test artifact | `audits/M5/pg18-restore-test-20260724-033001.json` |
| OS reboot acceptance | **Not executed** (operator-gated) |

One-command owners:

- `ops/health-check.ps1`
- `ops/bifrost/Get-BifrostStatus.ps1`
- `ops/bifrost/Rotate-BifrostLogs.ps1`

---

## Wildcard remediation

| Server | Status |
| --- | --- |
| `filesystem` | Named 14-tool inventory (Phase 7) |
| `context-fabric` | Named 5-tool inventory (Phase 7) |
| `serena`, `sequential-thinking`, `depwire`, `playwright` | Deferred next pass |

Context Steward: policy + SQL tables + `context_steward.py` + `.agentcore/MILESTONE_DELTA.md` projection baseline live.

---

## Swarm boundary proof

`MASTER_CONFIG_AND_PROMPT.md` contains the verbatim **SWARM DEVELOPMENT AND RUNTIME BOUNDARY** section. Non-Swarm IDE baseline continues to use only `agentcore-gateway`. SwarmRecall/SwarmVault/SwarmClaw remain a separate ecosystem (PG16 `:55432`, SwarmRecall `:3300`).

---

## Docker / New API

- Docker VHDX remains on **C:** (~18.9 GB) → `DOCKER_DATA_ON_C_OPERATOR_RELOCATION_REQUIRED`
- New API already deployed (`agentcore-newapi` + app-owned Postgres/Redis); status API 200
- Localhost-only bind harden for New API compose is operator follow-up in `D:\github\new-api` (out-of-worktree edit blocked by Stage B)

---

## Operator-pending register

1. Fix User-scope `OPENAI_API_KEY` if it still holds an OpenRouter `sk-or-…` key (Phase 2 note).
2. MiniMax Classic Matrix UI enrollment (no public tunnel).
3. MiniMax Code / Cherry / Codex / OI CLI full 14-step native lifecycle in-product.
4. Set `LANGSMITH_API_KEY` (name only in chat) for hosted Studio browser; allow Local Network Access.
5. Select controlled LangGraph pilot repo (not AgentCore/EMU/Swarm).
6. Relocate Docker Desktop disk image to `H:\AgentRuntime\docker` in a maintenance window.
7. Create/sync `G:\DatabaseBackups` second copy.
8. Reboot once; confirm PG18 + Bifrost logon recovery.

---

## Signal

`AGENTCORE_SYSTEM_HARDENING_CLOSEOUT_2026-07-25`
