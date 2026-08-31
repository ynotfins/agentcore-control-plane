# PC Infrastructure Reconstruction Handoff — 2026-08-25

## Document addresses (canonical paths)

- **Primary:** `D:\github\agentcore-control-plane\docs\handoffs\PC_INFRASTRUCTURE_RECONSTRUCTION_HANDOFF_2026-08-25.md`
- **Operator backup:** `D:\launchers\handoffs\PC_INFRASTRUCTURE_RECONSTRUCTION_HANDOFF_2026-08-25.md`
- **Restart packet:** `C:\Users\ynotf\OneDrive\Desktop\Temp\restart.txt` and `D:\launchers\handoffs\RESTART_PACKET_2026-08-25.txt`

This document is the operator-approved continuity artifact for post-restart PC infrastructure reconstruction. It binds Phase A (read-only audit), Phase B (reconstruction design requiring explicit operator ACCEPT), and Phase C (execution). Treat both handoff paths as carrying identical content; the repository copy is canonical for Git history and validators, while the launcher backup survives repo-only recovery scenarios.

---

## 0. Operator intent

The operator has requested a disciplined, three-phase reconstruction of the local PC infrastructure after a full system restart, without jeopardizing production-adjacent runtimes that already work.

**Phase A** is a read-only, full-system audit. No mutations to live services, enrolled paths, or authority documents unless a separate emergency ticket exists. The audit produces a machine-readable inventory and health evidence under the repository audits tree.

**Phase B** is reconstruction *design* only. No execution of structural changes (database moves, Docker pilots, new gateway enrollments, automation edits) proceeds until the operator reviews the design and issues an explicit **ACCEPT** (recorded in memory or an approval packet).

**Phase C** is execution, milestone-gated per Section 9, with rollback copies and validators before claiming completion.

**Protection priorities** (non-negotiable during this program):

- **AgentCore + LangGraph** on `F:` with PostgreSQL 18 at `127.0.0.1:55433`, including LangGraph `PostgresSaver` checkpoint tables in `agent_core`.
- **Swarm ecosystem** on `H:` and authority in `D:\github\swarm-ecosystem-control` (read-only from AgentCore agents unless explicitly delegated).
- **Neutral shared SwarmRecall** as the semantic memory/context plane reachable only through server-side `agentcore-memory` — not direct IDE SQL or raw Recall MCP in non-Swarm baselines.
- **Add Devin** as a *third*, isolated runtime namespace — not merged into AgentCore or Swarm ownership.

**Friction reduction:** Fewer duplicate MCP entries, fewer conflicting automations, clearer launcher ownership under `D:\launchers\`, and IDE defaults aligned to OpenRouter with **deepseek/deepseek-v4-pro** as the primary coding model where applicable.

**Explicit non-goal:** A blind “Docker all databases” migration. Containerization is evaluated per workload with ownership, backup, and point-in-time recovery (PITR) stories preserved (Section 5).

---

## 1. Authority chain

All agents and operators must resolve conflicts in this order (higher wins):

1. **`PROJECT_ANCHOR.md`** — repository root; non-Swarm gateway baseline, drive roles, enrollment default-deny.
2. **`DOC_AUTHORITY.md`** — classification of which documents are design authority vs. evidence vs. projections.
3. **`BLUEPRINT.md`** — locked implementation authority for memory-platform milestones and structural decisions.
4. **`CONTEXT_BLOCK.md`** — session continuity and current program context.
5. **`docs/boundaries/SWARM_FOREIGN_BOUNDARY.md`** — foreign ecosystem separation; Swarm mutable facts live in swarm-ecosystem-control.
6. **`docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`** — memory/database implementation authority for AgentCore.
7. **`D:\github\swarm-ecosystem-control`** — read-only for AgentCore workers unless the operator assigns Swarm-side work; SwarmClaw, SwarmVault, and Swarm runtime paths are not AgentCore design authority.
8. **`D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`** (and linked generated STATE projections) — **machine facts** and live milestone/runtime status; do not duplicate mutable runtime facts into `AGENTS.md` as permanent rules.

**`AGENTS.md` / `CLAUDE.md`** are agent contracts for this repository; they do not override `PROJECT_ANCHOR.md`. Codex remains the authority-maintainer for protected contracts and live rollout; Cursor is bounded implementation and independent review (Section 7).

---

## 2. Ecosystem and drive map

| Zone | Drive / path | Role | Notes |
|------|----------------|------|--------|
| AgentCore hot runtime | `F:` | Bifrost runtime, PG18 data dir, RAG/search hot paths | Production authority for `agent_core`, `cognee_core`, LangGraph checkpoints |
| AgentCore Git source | `D:` | `D:\github\agentcore-control-plane` | Canonical contracts, renderers, validators |
| Swarm hot runtime | `H:` | Swarm execution data, SwarmClaw SQLite, Swarm-local state | Operationally independent from `F:` |
| Swarm Git authority | `D:` | `D:\github\swarm-ecosystem-control` | Mutable Swarm facts; AgentCore read-only by default |
| Neutral SwarmRecall | Loopback | PostgreSQL **65432**, API **3300**, auxiliary **7700** (verify live) | No direct AgentCore/IDE SQL; reach via `agentcore-gateway` → `agentcore-memory` only |
| Devin (planned) | `I:\LocalApps\Devin` and/or `D:\devin-workspace` | Third isolated runtime | Gateway enrollment only; no cross-write into AgentCore/Swarm roots |
| OS / config | `C:` | Windows, user profiles, IDE global configs | Secrets via User-scope env vars only; no `.env` in AgentCore |
| Projects / worktrees | `D:` | Repos, worktrees | Enrollment must match `contracts/agentcore-project-enrollment.json` exactly |
| Archive / cold | `E:` | Neutral app backups (`E:\LocalApps\Backups`) | Not hot runtime |
| Backup | `G:` | Backup targets | Not active authority |
| Reserved Swarm | `H:` | (see above) | Do not store AgentCore PG data here |
| Neutral local apps | `I:` | `I:\LocalApps` hot data for non-AgentCore apps | Devin candidate namespace |
| Portable media | `J:` | Removable / portable | Not part of reconstruction authority |

**Forbidden cross-contamination (default-deny):**

- AgentCore processes, configs, or databases must not be relocated into Swarm roots on `H:` without an approved ADR and Swarm + AgentCore maintainer sign-off.
- Swarm Recall backend (`65432`) must not be added to IDE MCP baselines or AgentCore direct SQL routes.
- IDE global MCP must not duplicate the full upstream registry; non-Swarm entry is **`agentcore-gateway`** at `http://127.0.0.1:8080/mcp`.
- Context Fabric (`cf.db`) is repo-local rebuildable state — not a substitute for `agentcore-memory`.
- Writing to operator profile paths (`~\.openinterpreter`, `~\.codex`) from in-repo Cursor hooks is blocked by design; use **`D:\launchers\`** external PowerShell for profile mutations.

---

## 3. Known-good baseline (verify after reboot)

After every full reboot, verify the following before Phase A mutations or Phase C execution. Record results in the Phase A audit JSON.

### Gateway and databases

- **Bifrost / `agentcore-gateway`:** `http://127.0.0.1:8080/mcp` — Windows scheduled task `\AgentCore\AgentCore-Bifrost-Gateway`, runtime under `F:\AgentCore\runtime\bifrost`.
- **PostgreSQL 18 (production):** `127.0.0.1:55433`, data under `F:\PostgreSQL18\data` — databases `agent_core`, `cognee_core`; LangGraph `PostgresSaver` tables in `public` (`checkpoints`, `checkpoint_blobs`, `checkpoint_writes`).
- **PostgreSQL 16 (legacy rollback only):** `127.0.0.1:55432` — offline evidence; never an active production route.
- **Neutral SwarmRecall:** service-owned backend `127.0.0.1:65432` — no direct AgentCore connection.

### LangGraph / workflow

- Production workflow uses **PostgresSaver** at PG18; LangGraph Studio dev-only on `127.0.0.1:2024` with dev checkpointer — never share thread IDs with production.

### Open Interpreter Desktop (`~\.openinterpreter`)

- **Primary model:** OpenRouter **deepseek/deepseek-v4-pro**.
- **Profiles:** image/video via **minimax/minimax-m3** on OpenRouter as configured.
- **MCP:** `agentcore-gateway` plus `morph-mcp`, **danger-full-access**, browser/computer use as operator configured.
- **Launcher reference:** `D:\launchers\open-interpreter\` and `scripts/open-interpreter-desktop/` — commit **91b918e**.
- **Missing:** named fast profile for **deepseek/deepseek-v4-flash-vision-exp**.

### Open Interpreter CLI (`~\.openinterpreter-cli`)

- Separate home from Desktop. Launch via `scripts/open-interpreter-desktop/Start-OpenInterpreter-CLI.ps1`.
- That script sets process-scoped `CODEX_HOME` to `~\.openinterpreter-cli`. Do not set `CODEX_HOME` as a User environment variable.
- **Not done as of 2026-08-25:** still `openai/gpt-4.1-mini`, 16k context, `windows.sandbox = standard`, no gateway MCP. Update after restart.

### Codex

- Do not mutate `C:\Users\ynotf\.codex` during Phase A.
- Older note cited hash prefix `4F336B55`. Live `config.toml` SHA256 prefix at 2026-08-25 check: `B754A8AC7B519051`. Record the full current hash in the Phase A audit and use that as the do-not-mutate baseline.

### Context Fabric

- **Post-commit only** — hooks update committed-state evidence after Git commit; **not** pre-commit blocking for ordinary flows. Post-commit CF behavior is expected; absence of pre-commit CF is not a defect.

### Cursor

- Global MCP: `C:\Users\ynotf\.cursor\mcp.json` — single gateway entry per `PROJECT_ANCHOR.md`.
- Morph stays out of Cursor.
- Stage B: operator seeded `.agentcore/runtime/session-scope.json` on 2026-08-25. Same-turn writes can still deny with `current operator prompt is not durably captured`. That is C0, not empty Step 0.

---

## 4. Phase A — Full system audit checklist

Phase A is **read-only**. Collect evidence; do not “fix forward” during audit except documenting blockers.

### 4.1 Drives and paths

- Enumerate `C:` through `J:` usage against the drive map (Section 2).
- Flag any AgentCore data on `H:` or Swarm data on `F:`.
- Verify `F:\AgentCore`, `F:\PostgreSQL18`, and enrolled repo paths exist and match enrollment JSON.

### 4.2 Databases and ports

- Probe `55433` (PG18), `55432` (PG16 legacy), `65432` (Recall), `8080` (Bifrost), `2024` (Studio dev if running).
- Document database names, sizes, backup/PITR tooling paths (no credential output).

### 4.3 Automations

- Scheduled tasks: AgentCore Bifrost gateway/watchdog, OpenClaw remnants (should be disabled per rollback evidence), Swarm tasks on `H:`.
- Startup folder entries, HKCU Run keys — cross-check against operator-approved launcher list.

### 4.4 IDE rules, hooks, and MCP per client

- **Cursor:** `.cursor/hooks.json`, Stage B scripts, global `mcp.json`, project enrollment.
- **Codex:** `.codex/hooks`, agents, MCP — read-only inventory; hash Codex home.
- **Claude / MiniMax / Mavis / Antigravity / Open Interpreter:** profile MCP lists — gateway-only baseline vs. exceptions.
- **Open Interpreter Desktop vs CLI:** separate homes, model defaults, morph routing.

### 4.5 Installed software conflicts

- Duplicate PostgreSQL versions, competing Docker stacks, old MCP servers, conflicting Python runtimes on PATH.
- Cherry Studio / other agent hosts — tool surface vs. gateway policy.

### 4.6 Post-reboot health probes

- Bifrost MCP `list_tools` or contract validator: `scripts/bifrost/validate_contracts.py`.
- PG18 connect + `agent_core` checkpoint table presence.
- `agentcore-memory` ten-tool surface via gateway (enrolled project).
- OI Desktop launch smoke (operator optional): model list shows deepseek-v4-pro default.

### 4.7 Deliverable

Write **`audits/PC_INFRASTRUCTURE_AUDIT_2026-08-25.json`** in `D:\github\agentcore-control-plane` with structured sections mirroring this checklist, timestamps, pass/fail per probe, and pointers to evidence files (no secrets).

---

## 5. Database inventory and Docker migration assessment

**IMPORTANT:** Docker is **not** automatically better for all databases on this machine. The reconstruction program evaluates containerization per workload against isolation benefit, operational ownership, backup/PITR, and rollback — not slogans.

### 5.1 Fit matrix

| Fit | Workloads | Rationale |
|-----|-----------|-----------|
| **HIGH — Docker default when introduced** | Devin staging/execution sidecars; LangGraph Studio dev environment; Redis or similar cache **if** introduced as new infrastructure; greenfield stateless replicas; CI/test database clones | Isolation and reproducibility win; no legacy PITR story to migrate |
| **MEDIUM — coordinate both ecosystems** | Meilisearch for Recall; Recall API containerization | Requires Swarm + AgentCore ADR; must preserve loopback contracts and neutral Recall boundary; server-side only exposure |
| **LOW — keep native Windows service on F: (default)** | **PG18** `agent_core` + `cognee_core` + LangGraph checkpoints | Production authority, Milestone-gated; migration needs ADR, full backup, PITR proof, rehearsed rollback |
| **LOW** | **Bifrost** (Windows scheduled task, `F:\AgentCore\runtime\bifrost`) | Gateway is governance surface; container move is high risk for little gain unless ADR says otherwise |
| **LOW** | **SwarmClaw SQLite on H:** | Swarm-owned; AgentCore does not migrate |
| **LOW** | **Context Fabric `cf.db`** | Repo-local, rebuildable from Git hook/CLI |

### 5.2 Decision principle

Migrate to Docker when **isolation or reproducibility** clearly wins **and** the **ownership, backup, and PITR story** is preserved or improved with tested rollback. Reject “Docker because container.”

### 5.3 Phase B deliverable (per database / service)

For each persisted store, Phase B must document:

- **Owner** (AgentCore, Swarm, Neutral Recall, Devin, IDE-local)
- **Current path** (host, port, data directory)
- **Target architecture** (stay native, Docker pilot, hybrid)
- **Risk** (data loss, downtime, boundary violation)
- **Rollback** (snapshot, PG backup, task XML, launcher script)

Phase C database moves (milestone C5) happen **only** after ADR + PITR proof + operator ACCEPT.

---

## 6. Cursor Stage B execution harness gap (CRITICAL audit finding)

### 6.1 Problem statement

Stage B hooks **block writes** when session scope and resolvable targets are ambiguous, but **agents are not consistently informed** of execution state before they attempt mutations. Symptoms observed in reconstruction prep:

- Missing or stale **`GLOBAL_STATE.md`** projection for agent orientation. User-scope file `C:\Users\ynotf\.agentcore\GLOBAL_STATE.md` exists as of 2026-08-25.
- Empty **`session-scope`** Step 0 — operator seeded this on 2026-08-25. That chicken-and-egg is closed for the next session unless the file is wiped.
- **`init_session_scope` never called from `beforeSubmitPrompt`**.
- **Prompt capture** can still deny same-turn writes with `current operator prompt is not durably captured` even when Step 0 is populated.
- **Opaque deny messages**.
- **Profile path writes** (`~\.openinterpreter`, `~\.codex`) blocked by design; use **`D:\launchers\`** external PowerShell.
- Desktop, OneDrive, and `D:\launchers` are outside the assigned worktree, so Cursor agents cannot save those copies.

This is a **harness** problem, not an invitation to disable Stage B integrity hooks.

### 6.2 Required harness (implement in **C0** before other IDE reconstruction work)

**Layer 1 — Preflight**

- On `sessionStart` and `beforeSubmitPrompt`, inject **`AGENTCORE_EXECUTION_STATE`**.
- CLI: `python -m agentcore cursor preflight` (from `scripts` venv per `AGENTS.md`).

**Layer 2 — Auto-arm Step 0**

- Parse operator prompt for intent, acceptance, and file scope; write **`.agentcore/runtime/session-scope.json`** automatically.
- **Bootstrap exception:** allow session-scope.json write without pre-existing scope (only this file).
- **Projection worker** ensures **`GLOBAL_STATE.md`** exists.

**Layer 3 — Actionable deny messages**

- Modes: **`implementation`**, **`read_only_audit`**, **`authority_maintainer`**.
- Deny payload must state: rule id, missing field, enrolled path expected, and one recommended remediation command.

**Layer 4 — Prompt capture**

- Capture the current operator prompt before tools, bound to this session and conversation, before any write is attempted.

### 6.3 Acceptance test

In a **fresh Cursor chat**, an agent can write a **declared repo file** within **two tool calls** without manual `session-scope.json` editing.

---

## 7. Codex orchestration model vs Cursor

### 7.1 Codex (known-good pattern)

- Primary agent acts as **engineer/orchestrator**.
- **Morph MCP** for fast GitHub code pull — allowed on Codex and Open Interpreter Desktop. Not on Cursor.
- Protected architecture and contracts remain with Codex authority-maintainer per `AGENTS.md`.

### 7.2 Cursor recommendations

**YES — adopt the orchestration *pattern* in Cursor** with parent agent plus bounded `.cursor/agents/` subagents, `model: inherit`.

**NO — duplicate Codex authority in Cursor.** Cursor is bounded implementation + independent review.

**Morph in Cursor:** do not add direct Morph MCP to Cursor global `mcp.json`.

---

## 8. Phase B reconstruction design

Phase B output is a single **Reconstruction Design Packet** requiring operator **ACCEPT** before Phase C.

### 8.1 Design principles

- One gateway entry per non-Swarm IDE; leases for OpenRouter MCP tools per M6 policy.
- Launchers own profile mutations; repo hooks own repo integrity.
- Minimize scheduled tasks and startup entries to an audited allowlist.
- Preserve F:/H:/neutral Recall boundaries; add Devin as third namespace.

### 8.2 Docker matrix

Embed Section 5 matrix with per-service Phase B rows (owner, path, target, risk, rollback).

### 8.3 Devin third runtime

- Candidate roots: **`I:\LocalApps\Devin`** and/or **`D:\devin-workspace`**.
- Enroll in gateway/project continuity **only** after isolated cwd and secrets model documented.
- No shared Postgres with PG18 production without ADR.
- Clean `%APPDATA%\devin\mcp_config.json` (literal key + direct MCP sprawl) using env vars only.

### 8.4 Conflict backlog

From Phase A audit: list each conflict with recommended owner and milestone (C0–C5).

### 8.5 Launcher strategy

- **`D:\launchers\`** is the operator-facing mutation surface.
- Handoff copies live under **`D:\launchers\handoffs\`**.

---

## 9. Phase C milestones

| Milestone | Scope | Exit evidence |
|-----------|--------|----------------|
| **C0** | Cursor harness fix (Section 6) + disable/document dead automations | Harness acceptance test passes; task/startup audit diff |
| **C1** | IDE alignment — OpenRouter defaults, deepseek-v4-pro primary, gateway-only MCP baselines | Per-IDE checklist in audit JSON |
| **C2** | Devin infrastructure — namespace, enrollments, sidecars if any | Devin health probe + boundary review |
| **C3** | Docker pilot — **one** approved service (e.g., Studio dev or Devin sidecar) | Compose file + rollback + probe |
| **C4** | Swarm `H:` verification — no AgentCore contamination | Swarm maintainer sign-off or read-only audit note |
| **C5** | Optional DB moves — **only** with ADR + PITR proof + operator ACCEPT | Restore test log in `audits/M5/` pattern |

Dependencies: **C0 before C1**. **C5** is optional and last.

---

## 10. Open Interpreter cross-contamination notes

- OI-related packages under **`.codex\packages`** are structural — inventory before blaming mystery MCP.
- **Post-commit Context Fabric** is expected.
- **Skill-installer** defaults may target **`CODEX_HOME`** paths.
- **Desktop vs CLI** must remain separate.
- `CODEX_HOME` in the CLI launcher is process-scoped isolation, not a Cursor rule.

---

## 11. Acceptance criteria (program complete)

1. Full inventory in `audits/PC_INFRASTRUCTURE_AUDIT_2026-08-25.json`.
2. Zero boundary violations per Section 2, or explicit operator-waived ADR.
3. Health probes green for Bifrost, PG18, gateway memory surface.
4. OpenRouter / DeepSeek defaults verified on OI Desktop and agreed IDE baselines (C1).
5. Devin runtime isolated and documented (C2).
6. Dead automations removed or disabled; launcher map current.
7. Docker only where approved.
8. Harness test passes (Section 6.3).
9. Evidence committed; secrets never committed.

---

## 12. First message for next agent

```text
Continue PC infrastructure reconstruction per operator handoff:
D:\github\agentcore-control-plane\docs\handoffs\PC_INFRASTRUCTURE_RECONSTRUCTION_HANDOFF_2026-08-25.md
(backup: D:\launchers\handoffs\PC_INFRASTRUCTURE_RECONSTRUCTION_HANDOFF_2026-08-25.md)
Also read: C:\Users\ynotf\OneDrive\Desktop\Temp\restart.txt

Phase A first: read-only full audit; output audits/PC_INFRASTRUCTURE_AUDIT_2026-08-25.json.
Do not execute Phase B/C without operator ACCEPT.
If Cursor writes are denied, fix harness per Section 6 before other work.
Authority: PROJECT_ANCHOR.md → DOC_AUTHORITY.md → this handoff.
```

---

## 13. Zoo-Code

Zoo-Code / Cursor:
- Morph stays out of Cursor.
- Cursor Zoo-Code is signed into ynotfins@gmail.com and opens directly into Zoo-Code.
- Zoo-Code token in Windows EV appears to be an extension/device token, not a universal IDE login token. Never commit it.
- Cursor Zoo-Code model targets:
  primary = openrouter/deepseek-v4-pro
  fast = openrouter/deepseek-v4-flash-vision-exp
  image/video = openrouter/minimax-m3
- Cursor MCP baseline remains agentcore-gateway only.

Open Interpreter:
- CLI confirms TOML MCP config loads agentcore-gateway on Desktop.
- UI may not show MCP servers; verify via `interpreter mcp list`.
- Update CLI config to use DeepSeek V4 Pro primary, DeepSeek V4 Flash Vision Exp fast, MiniMax M3 image/video, large context.
- Keep Desktop operator mode and CLI sandbox mode separate.

Devin:
- Recent logs show agentcore-gateway connected, but user-scope mcp_config has extra direct MCPs and a literal API key.
- Audit and clean after restart.
- Do not use Zoo extension token as a generic Devin login.

---

## 14. Secrets Rule

Secrets live only in Windows User-scope Environment Variables or approved external secret stores.
Never write tokens, API keys, bearer values, OAuth tokens, DB passwords, or extension tokens into repo files, IDE config templates, MCP config committed to Git, logs, handoffs, or screenshots.
Live installers may read env vars and materialize secrets only into app-owned live config when the app cannot expand env vars, and those files must never be committed.

---

## 15. Verified extras 2026-08-25

Git: branch `setup/zoo-code-qdrant-nfa-20260820`, commit `91b918e`.

Enrollment exact paths: `agentcore-control-plane` = `D:\github\agentcore-control-plane`; `agentcore-context-engine` = `D:\github\agentcore-context-engine`; `codebase-analyzer` = `D:\codebase-analyzer`; `openhands` = `D:\OpenHands`; `nfa-alerts-database` = `D:\nfa-alerts-database`; `nfa-notification-collector` = `D:\github\nfa-notification-collector`; `odysseus` = `D:\odysseus`.

`D:\github2` does not exist. No `Devin-NFA-Platform` folder on `D:`. NFA also present at `D:\github\nfa-alerts-enterprise`, `D:\nfa-alert`, `D:\NFA-Database-Control`, `D:\NFA-OpenHands-Control`.

Cloud Mia is a separate restart-safe project, not AgentCore Phase A: `D:\CloudMia` main `2fa6f80`; engine `D:\CloudMia\vendor\lobe-chat` canary `7cfe63f689`; docs `a93e7aa`. After reboot start Docker Desktop for miaknuckles.com. `D:\postgreSQL18-control-plane` is local-only and not the Cloud Mia builder.

Do not: pull/fetch/merge/rebase unless asked; edit `~\.codex`; write `H:`; SQL to `65432`; Morph in Cursor; Docker-move PG18/Bifrost/Swarm SQLite/cf.db; print secrets; create `.env`; hand-edit generated STATE/DECISIONS/CONTEXT_INDEX; disable Stage B.