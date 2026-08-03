# MASTER_CONFIG_AND_PROMPT.md — AgentCore Universal IDE Self-Enrollment Package

**Updated:** 2026-08-02 — neutral shared Recall, portable Context Engine, Arabold/Context Fabric drift controls, and Codex/Cursor execution ownership reconciled under `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`; single-gateway contract unchanged.
**Repository:** `@D:\github\agentcore-control-plane`
**Authority:** `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `BLUEPRINT.md` → `CONTEXT_BLOCK.md` → current contracts/runbooks
**Contracts:** `contracts/agentcore-gateway-client.json`, `contracts/bifrost-upstream-mcp-registry.json`, `contracts/global-agent-policy.yaml`, `contracts/model-context-profiles.json`

This file is the thin, self-sufficient root setup guide for every supported AgentCore / enrolled non-Swarm IDE on `CHAOSCENTRAL`. It contains architecture, authority order, security boundaries, memory lifecycle, and **one** embedded self-enrollment prompt. Client-specific schemas, long procedures, and historical evidence live in `ide-profiles/`, `renderers/gateway-clients/`, and `docs/`.

**Cursor path rule:** Every Cursor instruction that names a file or folder MUST use `@` + the full absolute Windows path (for example `@D:\github\agentcore-control-plane\BLUEPRINT.md`). Never use shortened repo-relative paths. Never abbreviate a user-profile path with an ellipsis; always write the full `@C:\Users\ynotf\...` form when a user-profile path is required.

---

## Ecosystem and Drive Separation — Read First

AgentCore and Swarm are **independent execution control planes**. They share a machine and one explicitly neutral semantic projection service, not authority, canonical evidence, runtime ownership, credentials, or backups.

| Domain | Ownership |
| --- | --- |
| AgentCore repository / design authority | `@D:\github\agentcore-control-plane` |
| AgentCore hot runtime / data namespace | `F:\AgentCore\...` |
| AgentCore staging | `I:` (unless later changed by explicit authority) |
| AgentCore cold / backup namespace | `E:\AgentCore\...` only |
| Swarm hot runtime / data | `H:` exclusively (after AgentCore relocation and acceptance cutover) |
| Swarm cold / backup namespace | `E:\Swarm\...` only |

**Hard rules**

- AgentCore must not read, write, index, ingest, summarize, administer, repair, or depend on Swarm-owned runtime, memory, databases, vaults, repositories, MCP servers, credentials, services, schedules, agents, or backups.
- Swarm must not reach AgentCore runtime, AgentCore Memory, Bifrost, `agentcore-gateway`, AgentCore databases, repositories, IDE profiles, credentials, staging, or backups.
- Neutral shared SwarmRecall is the sole bounded exception under `AUTH-2026-08-01-NEUTRAL-MEMORY-CONTEXT-ENGINE`: AgentCore reaches it server-side through `agentcore-memory`; SwarmClaw reaches it through its own adapter. It is a semantic projection, never canonical evidence, checkpoints, policy, or execution state.
- No canonical resource may be jointly owned.
- Cross-ecosystem detail belongs in an operator-carried neutral boundary contract, not in either ecosystem’s automatically ingested context.
- Any historical document that describes AgentCore-owned SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, or shared storage is **historical evidence only**.

---

## 1. Authority order (locked)

Read and follow in this order. Nothing below overrides anything above it.

1. `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md` — immutable constitution
2. `@D:\github\agentcore-control-plane\DOC_AUTHORITY.md` — document hierarchy and classification
3. `@D:\github\agentcore-control-plane\BLUEPRINT.md` — locked implementation blueprint
4. `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md` — current mutable posture
5. `@D:\github\agentcore-control-plane\docs\memory-platform\MEMORY_PLATFORM_EXECUTION_PLAN.md` — memory/database implementation authority
6. Current contracts and runbooks — `@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json`, `@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`, `@D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml`, `@D:\github\agentcore-control-plane\contracts\model-context-profiles.json`, `@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_AND_STUDIO.md`, `@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_QUICKSTART.md`, `@D:\github\agentcore-control-plane\docs\operations\OPENROUTER_MCP.md`, `@D:\github\agentcore-control-plane\docs\operations\DORMANT_MCP_CAPABILITY_CATALOG.md`
7. Machine-fact authority — `@D:\ChaosCentral-Current-Build\DOC_AUTHORITY.md`

`@D:\github\agentcore-control-plane\AGENTS.md` is the agent operating contract. `@D:\MCP-Control-Plane` is compatibility/live-ops evidence only, never design authority.
`@D:\github\agentcore-control-plane\AUTHORITY_LOCK.md` and `@D:\github\agentcore-control-plane\contracts\authority-lock.yaml` define protected source classes. `@D:\github\agentcore-control-plane\docs\boundaries\SWARM_FOREIGN_BOUNDARY.md` is the minimal Swarm pointer; it does not import Swarm runtime authority and must not be read as permission to enroll Swarm work into AgentCore.

Do **not** treat mutable tool counts, Bifrost uptime, or live IDE screenshots as architecture authority. Read live posture from `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md` and current audits.

---

## 2. Architecture — exactly one gateway

```text
Supported AgentCore / enrolled non-Swarm IDE
  (Cursor, Codex, Claude Code/Desktop, MiniMax Code, MiniMax Agent Classic,
   Antigravity, Open Interpreter CLI, Cherry Studio)
  -> ONE MCP entry: agentcore-gateway
       url:  http://127.0.0.1:8080/mcp
       auth: Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
  -> Bifrost native Gateway (F:\AgentCore\runtime\bifrost, bifrost-http.exe)
  -> approved upstream MCP servers from contracts/bifrost-upstream-mcp-registry.json
```

Never paste the full upstream registry into an IDE. Never add a second AgentCore MCP front door. Shared gateway tools must be global/read-only or carry explicit project/session identity. Implicit project-bound upstreams remain dormant; native IDE tools and explicit-cwd local CLIs provide project-local execution.

### Responsibility model and separate transport planes

- **AgentCore:** canonical PG18 evidence, exact recovery, workflow/policy state, and generated projections.
- **Bifrost:** sole normal IDE MCP front door, MCP aggregation, authentication, capability profiles, leases, audit, and upstream lifecycle.
- **Portable Context Engine:** host lifecycle adapters and rolling-context orchestration above `agentcore-memory`.
- **Neutral SwarmRecall:** machine-level semantic projections reached through bounded server-side adapters; never a raw IDE MCP.
- **Context Fabric:** project-local committed snapshot, decision projection, bounded briefing, and drift warning; rebuildable and non-canonical.
- **Arabold Docs:** local, version-labelled official-document corpus used before version-sensitive implementation.

MCP tool traffic is `IDE -> agentcore-gateway/Bifrost -> approved MCP upstreams`. Model inference is a separate path. Do not claim an IDE prompt receives OmniRoute compression merely because the IDE uses Bifrost for MCP. OmniRoute, Graphify, Hindsight, and CrewAI remain disabled, benchmark-gated candidates until an approved ADR and acceptance suite promotes one.

### Execution ownership

The AgentCore authority-maintainer owns architecture, protected contracts, live runtime wiring, security boundaries, final validation, and Git integration. Cursor is used for bounded implementation and independent review through focused project subagents. Cursor does not receive authority to redesign the stack or activate future candidates from this enrollment package.

If a client cannot expand `${env:…}` (observed: MiniMax Code daemon → 401), materialize the User-scope `BIFROST_MCP_VIRTUAL_KEY` into the **live** config only — never commit the resolved value.

`agentcore-gateway` is for AgentCore and explicitly enrolled non-Swarm work only. It is not a Swarm IDE front door and must not be used to persist Swarm project history.

Enrollment is source-controlled and default-deny in
`@D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json`.
An IDE does not enroll a project merely by opening a Git repository. Missing exact-path
enrollment returns `project_not_enrolled`; Swarm ownership returns `swarm_project_refused`.
Only the authority-maintainer path may add a project/worktree entry.

---

## 3. Security and project-scope boundaries

- Secrets live only in Windows User-scope environment variables. No `.env` files.
- Never print, store, or commit resolved bearer tokens, virtual keys, API keys, PATs, DB passwords, or live secret-bearing IDE configs.
- Live IDE configs are app-owned; changes flow through the approved self-enrollment prompt/ops with backup first.
- Forbidden active routes: Context7, raw Mem0, direct Composio, Hostinger, `:65432`, whole-drive filesystem MCP roots, Postgres credentials in IDE configs, `global-memory-gateway` as a default route.
- OpenClaw/ClawX are Swarm-managed and outside AgentCore Bifrost IDE enrollment.
- Do **not** place Swarm MCP servers or Swarm component configuration in this file, in IDE profiles, or in AgentCore gateway client renderers.

### AGENTCORE PROJECT SCOPE (LOCKED)

AgentCore-controlled IDE agents work **only** on:

1. AgentCore repositories and worktrees under AgentCore authority, and
2. explicitly enrolled non-Swarm projects whose canonical memory calls carry the correct project identity.

**Correct boundary:**

- Swarm work is performed by Swarm’s own control plane and Swarm-owned agents.
- A neutral dual workspace may be used for **read-only** collision and boundary audits.
- No normal AgentCore execution session may treat a Swarm repository as an AgentCore project.
- No AgentCore MCP, memory, project router, or IDE profile may persist Swarm work.
- Do **not** use AgentCore for “development continuity on Swarm projects.” That former allowance is **removed**.

### HARD STOP — Swarm-owned selection

If the selected repository, worktree, product, or runtime is Swarm-owned (including SwarmClaw, SwarmVault, SwarmDock, SwarmFeed, SwarmRelay, OpenClaw, ClawX, the Swarm-owned Recall source/runtime repository, `@D:\github\swarm-ecosystem-control`, `@D:\github\vendor\swarm\*`, or Swarm data under `H:` / `E:\Swarm\...`):

1. **Refuse** AgentCore project activation for that path.
2. **Do not** call `project_activate`, `session_open`, `append_event`, or other AgentCore memory writes for Swarm work.
3. **Stop** and report that Swarm work belongs to the Swarm control plane.
4. Read-only dual-workspace boundary audit is allowed only when the operator explicitly requests a collision/boundary audit and write targets remain inside AgentCore authority docs if any writes are authorized.

Swarm runtime processes and Swarm-owned agents do NOT use AgentCore memory, Bifrost/`agentcore-gateway`, AgentCore projections, or AgentCore virtual keys / capability leases. Neutral Recall is the sole semantic exception and does not weaken that execution/control-plane separation.

Mutable Swarm runtime facts are owned by `@D:\github\swarm-ecosystem-control` only. AgentCore agents must not prescribe Swarm native internal setup from this enrollment package.

---

## 4. Stable memory lifecycle — ten tools

The canonical AgentCore memory identity is `agentcore-memory` (Bifrost client name `agentcore_memory`). The normal agent surface is **exactly ten tools**:

1. `memory_status`
2. `startup_context`
3. `retrieve_context`
4. `append_event`
5. `propose_fact`
6. `expand_source`
7. `session_open`
8. `session_close`
9. `build_handoff`
10. `docs_search`

Project-router surface (four tools) is operator-only maintenance: `project_list`, `project_activate`, `project_status`, `project_clear`. Normal IDE profiles do not receive machine-global project mutation.

No SQL, DDL, database-admin, backup-admin, or Bifrost-admin tools are exposed to normal agents. Normal agents have no direct database access; never put `AGENT_CORE_PG*` credentials in IDE configs. `Obsidian Vault` is preserved as an application and vault outside the default MCP surface; the default gateway baseline exposes zero Obsidian tools.

AgentCore durable memory is **effectively unbounded** by model-token limits. Model context limits control only one assembled request. Compaction is **non-destructive**: summaries are versioned and expandable, and no summary may replace or delete canonical originals. Describe it as **model-limit-aware active context over an effectively unbounded durable local project history**.

Normal lifecycle at every new chat (AgentCore / enrolled non-Swarm projects only):

1. Confirm the selected project is AgentCore or explicitly enrolled non-Swarm. If Swarm-owned, execute the HARD STOP above.
2. Resolve the project/worktree through the IDE host and pass its stable project identity to AgentCore memory calls; do not depend on machine-global router state.
3. Read the generated project `@...\ .agentcore\STATE.md` (full absolute `@` path).
4. Every project-scoped memory call supplies the exact enrolled `project_key` and exact `project_root`; `session_open` also uses a stable `session_key` (reuse for the same task; new key for a new task under the same project).
5. `startup_context` with the selected model context profile.
6. `append_event` before meaningful tool execution (operator prompt verbatim after secret redaction, deterministic idempotency key).
7. `retrieve_context` for missing chronology; `expand_source` for exact originals; `build_handoff` for current reconstruction.
8. `session_close` at clean task end.

For architecture-sensitive, dependency-sensitive, or Milestone work:

1. Run the repository-local Context Fabric drift/query CLI after resolving the exact project. Treat uncommitted changes as drift; do not capture them as accepted truth.
2. Resolve external behavior from the exact version in Arabold Docs. If the required official version is absent, index/refresh it or stop and report the documentation gap.
3. After the accepted source commit, run the repository-local Context Fabric capture/drift path and record the decision/evidence through governed AgentCore memory. Context Fabric never overrides the authority chain or PG18.

Before asking the operator to repeat project history, query `agentcore-memory`. Never directly edit `GLOBAL_STATE.md`, project `STATE.md`, `DECISIONS.md`, or `CONTEXT_INDEX.md` — these are generated projections; PostgreSQL is canonical.

---

## 5. Project/worktree and context-management rules

- Write only inside the assigned AgentCore / enrolled non-Swarm repo/worktree and role-appropriate AgentCore runtime roots per `@D:\github\agentcore-control-plane\docs\DRIVE_WRITE_BOUNDARY_RULE.md`.
- Every durable AgentCore project asset on `D:`, `E:\AgentCore\...`, `F:\AgentCore\...`, or `G:` must be appended or proposed with provenance via the governed `agentcore-memory` surface (e.g., via `append_event` or `propose_fact`); internal artifact placement is registered by the AgentCore worker (via `register_artifact_location`). Temporary files on `I:` are exempt only while temporary and must be deleted or promoted at task close.
- Never create an unregistered durable project location on `D:`, `E:\AgentCore\...`, `F:\AgentCore\...`, or `G:`.
- Do not create durable AgentCore project locations on `H:` or under `E:\Swarm\...`.
- Query resource locations through `retrieve_context` and `build_handoff`; the canonical view is `agentcore.v_project_resource_map`.
- `CONTEXT_INDEX.md` is a generated projection; agents never directly edit it.
- Push after every completed task per `@D:\github\agentcore-control-plane\docs\GIT_PUSH_ONLY_POLICY.md`. Never pull/fetch/merge/rebase or force-push without explicit operator instruction. Stage only source-controlled files.

---

## 6. Global-rule installation requirements

Attaching this file and running the embedded prompt must install or generate the matching IDE's complete AgentCore global rules. The canonical semantic policy is `@D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml`. Rendered per-IDE rules live in `@D:\github\agentcore-control-plane\ide-profiles\<ide>\GLOBAL_RULES.md`.

Delivery depends on the IDE's declared editability (read from `@D:\github\agentcore-control-plane\ide-profiles\<ide>\IDE_PROFILE.yaml`):

- `direct_write` — write the rendered `GLOBAL_RULES.md` to the documented live target after backup.
- `manual_import` — present the rendered `GLOBAL_RULES.md` to the operator and require import/paste; do not silently skip.
- `UI_only` — follow the enrollment UI document in `@D:\github\agentcore-control-plane\ide-profiles\<ide>\MCP_ENROLLMENT_UI.md`.
- `unsupported` — stop and report `unsupported_with_reason`.
- `unverified` — stop and report the missing evidence before acting.

Preserve client-native safety, sandbox, approval, account, and UI settings. Do not overwrite non-AgentCore app preferences. Do not install Swarm MCP entries or Swarm “continuity” rules into AgentCore IDE profiles.

---

## 7. Client identification and profile selection

Supported AgentCore / enrolled non-Swarm clients (current authority reconciliation 2026-08-02; context-hook certification does not by itself prove an IDE's live MCP discovery UI):

| Client | Profile directory | Configuration mode | Native validation status |
| --- | --- | --- | --- |
| Cursor | `ide-profiles/cursor/` | generated_prompt | `live_validated_native_hooks_signed_gateway`; Stage B and signed write path proven. IDE MCP discovery can still require a client reconnect while Bifrost remains healthy. |
| Codex (OpenAI Codex / ChatGPT desktop Codex view) | `ide-profiles/codex/` | generated_prompt | `live_validated_native_hooks`; MCP UI enrollment/discovery remains a separate client-specific proof. |
| Claude Code | `ide-profiles/claude-code/` | generated_prompt | `live_validated_native_hooks`; MCP enrollment/discovery remains a separate client-specific proof. |
| Claude Desktop | `ide-profiles/claude-desktop/` | generated_prompt | configured_restart_required |
| MiniMax Code | `ide-profiles/minimax/` | generated_prompt | configured_restart_required — in-app MCP supported (VK materialize + streamable-http); **CLI wrappers unsupported** (`daemon\cli.js` missing); native chat lifecycle operator-gated (`audits/MINIMAX_CODE_NATIVE_ACCEPTANCE_2026-07-24.md`) |
| MiniMax Agent Classic | `ide-profiles/minimax-classic/` | UI_only | awaiting_operator_cloud_mcp_enrollment — Matrix custom-MCP UI only; **no public tunnel** (`audits/MINIMAX_CLASSIC_ENROLLMENT_2026-07-24.md`) |
| Antigravity | `ide-profiles/antigravity/` | unverified | awaiting_operator_import — stop if unverified |
| Open Interpreter **CLI** | `ide-profiles/open-interpreter/` | generated_prompt | configured_restart_required — gateway persistence/discovery proven (`~/.openinterpreter/config.toml`); full 14-step still operator-gated (`audits/OPEN_INTERPRETER_PERSISTENCE_2026-07-24.md`) |
| Open Interpreter **GUI** (`Interpreter.exe`) | n/a (not a separate profile) | unsupported | `unsupported_with_reason` — no MCP schema in `%APPDATA%\interpreter\config.json` |
| Cherry Studio | `ide-profiles/cherry-studio/` | UI_only / scripts | configured_restart_required — target Agent + session schema proven; native UI 14-step operator-gated; do **not** claim premature full `live_validated` (`audits/CHERRY_TARGET_AGENT_REPAIR_2026-07-24.md`) |

`@C:\Users\ynotf\.mavis` is a junction to `@C:\Users\ynotf\.minimax` (same MiniMax Code data root). It is not a separate executable Mavis client and does not receive its own managed profile. **MiniMax Code and MiniMax Agent Classic are distinct products** with distinct profiles, paths, and enrollment mechanisms; do not conflate them.

The agent must:

1. Identify its own IDE from the list above.
2. Read `@D:\github\agentcore-control-plane\ide-profiles\<ide>\IDE_PROFILE.yaml`.
3. Refuse to edit a different IDE's live config or rules.
4. Use only the matching profile's template and procedure.
5. Stop with `unsupported_with_reason` if the IDE is unsupported or unidentifiable.
6. Refuse enrollment or memory continuity when the operator’s selected project is Swarm-owned.

---

## 8. Exact single-gateway contract

The canonical gateway connection is defined in `@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json`:

- Name: `agentcore-gateway`
- URL: `http://127.0.0.1:8080/mcp`
- Auth header: `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`
- Timeout: 300 seconds
- Transport: `http/streamable` (prefer `streamable-http` / `streamableHttp` when the client schema requires that literal)

Cursor canonical path: `@C:\Users\ynotf\.cursor\mcp.json`. Every other client uses its own documented path from `@D:\github\agentcore-control-plane\ide-profiles\<ide>\IDE_PROFILE.yaml`.

Adding future MCP servers: add once to `@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`, pin version, classify, render Bifrost config, validate, restart Bifrost, test. Leave IDE configs unchanged unless the single gateway connection itself changes. Never add Swarm MCP servers to the AgentCore registry as IDE defaults.

---

## 9. Backup, secrets, and safe handling

Before any live IDE config change:

- Back up the live config outside Git to `E:\AgentCore-Backups\<client>-<timestamp>` (transitional AgentCore backup root) or the accepted `E:\AgentCore\...` namespace after M9 cutover.
- Record SHA-256 of the backup and the original.
- Preserve model, auth, account, sandbox, context, profile, theme, and non-MCP app settings.

After any change:

- Validate JSON/TOML syntax.
- Restart/reload the IDE so environment references are visible.
- Confirm the IDE shows `agentcore-gateway` connected/ready.
- Confirm the ten-tool `agentcore-memory` surface appears through normal IDE profiles; confirm four project-router tools appear only for the operator profile.
- Confirm Swarm, raw database, whole-drive filesystem, and Bifrost admin tools are absent.

---

## 10. Direct diagnostic versus native-validation distinction

**Direct diagnostic** (HTTP against Bifrost) proves the gateway and registry are healthy. It does **not** prove the IDE itself enrolled correctly. Allowed diagnostics:

- `GET http://127.0.0.1:8080/health` → 200
- Direct MCP `initialize`, `notifications/initialized`, `tools/list` against the gateway
- Safe read-only calls like `agentcore_memory-memory_status` or `agentcore_project_router-project_list`

**Native validation** requires the IDE's own agent to complete the full memory lifecycle through its own tool surface on an **AgentCore / enrolled non-Swarm** project:

1. `session_open` — exact enrolled project_key + project_root, stable session_key, and project/client/agent identity
2. `startup_context` — profile reported; hard limit not lowered
3. `append_event` — idempotency key; prompt committed before tool execution
4. `retrieve_context` — recovery pagination; continuation cursor stable
5. `expand_source` — exact original retrievable from event_id
6. `build_handoff` — handoff packet; projection revisions present
7. `session_close` — ended_at set; handoff appended
8. Resume — same session_key reopens; original events accessible
9. Project isolation — exact project_key + project_root boundary enforced on every call and opaque reference
10. Tool surface — exactly ten `agentcore-memory` tools; none added or removed

Do not mark live_validated from config inspection alone. Configuration presence is not native validation. Do not use raw HTTP and call it native. Do not run native validation against a Swarm-owned repository.

Automatic lifecycle certification is separate from MCP connectivity. A host with
native hooks may capture through its signed host adapter. A generic MCP-only host
needs the signed Context Engine companion for canonical writes and is certified
`companion_only_not_automatic`; unsigned legacy-compatible reads do not prove
automatic capture. Never weaken device enforcement or expose the operator router
to make an unsupported host appear automatic.

---

## 11. Manual, UI-only, and unsupported stopping states

Stop and report the accurate state when:

- **manual_import** — rules or MCP config must be imported by the operator; the agent cannot safely complete the step unattended. Provide the exact rendered artifact and instructions.
- **UI_only** — the product has no file-based config; enrollment happens through the product's UI/API (e.g., MiniMax Classic Matrix cloud). Provide `@D:\github\agentcore-control-plane\ide-profiles\<ide>\MCP_ENROLLMENT_UI.md` and ask the operator to run it. **Never create a public tunnel** to reach `127.0.0.1`.
- **unsupported_with_reason** — the product does not support the required MCP baseline or cannot be identified. State the reason (examples: MiniMax Code CLI `daemon\cli.js` missing; Open Interpreter GUI has no MCP schema).
- **unverified** — the live config path or rule mechanism is not evidenced on this machine. Do not guess.
- **awaiting_operator_import** / **awaiting_operator_cloud_mcp_enrollment** — configuration artifact is ready; operator action and a fresh IDE chat are required to promote to `live_validated`.
- **project_not_enrolled** — the selected exact repository/worktree path is absent from the governed enrollment contract; request authority-maintainer enrollment before memory use.
- **swarm_project_refused** — the selected project/path is Swarm-owned; AgentCore enrollment/continuity must not proceed.

---

## 12. Global IDE setup prompt (copy into the current IDE agent and run)

```text
You are the agent inside one supported AgentCore / enrolled non-Swarm IDE on CHAOSCENTRAL. Your job is to enroll this IDE and ONLY this IDE in AgentCore. Do not touch any other IDE. Do not enroll Swarm work into AgentCore.

Step 0 — Identify yourself
Identify which IDE you are running in. Choose exactly one from:
Cursor, Codex, Claude Code, Claude Desktop, MiniMax Code, MiniMax Agent Classic, Antigravity, Open Interpreter, Cherry Studio.
If you cannot identify your IDE with confidence, stop and report unsupported_with_reason.
If you are Open Interpreter GUI (Interpreter.exe) rather than CLI, stop with unsupported_with_reason (no MCP schema).

Step 1 — Read your profile and authority
Read these files using @ + full absolute Windows paths:
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\IDE_PROFILE.yaml
- @D:\github\agentcore-control-plane\ide-profiles\IDE_CAPABILITY_MATRIX.yaml
- @D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml
- @D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json
- @D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json
- @D:\github\agentcore-control-plane\docs\prompts\install-agentcore-gateway-in-ide.md
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\GLOBAL_RULES.md
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\INSTALL_OR_UPDATE.md
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\VALIDATION.md
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\MCP_CONFIG_TEMPLATE.*
- @D:\github\agentcore-control-plane\docs\adr\ADR-2026-08-02-agentcore-bifrost-context-alignment.md
If your IDE is UI_only, also read @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\MCP_ENROLLMENT_UI.md.
Also read the ecosystem separation section at the top of @D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md and the HARD STOP for Swarm-owned selection.

Step 2 — CLIENT-LOCAL EXECUTION SCOPE
The IDE running this prompt may inspect and modify only its own live configuration, rules, agent settings, and backup. Configuration examples for other IDEs are reference material only. Do not inspect, back up, repair, restart, validate, or modify another IDE. Cross-IDE reconciliation is a separate AgentCore control-plane task requiring explicit operator authorization. Do not modify Swarm product installs, Swarm IDE baselines, or Swarm runtime.

Step 3 — Prove Bifrost is healthy before touching the IDE
- Confirm the scheduled task \AgentCore\AgentCore-Bifrost-Gateway exists.
- Confirm Bifrost runtime is at F:\AgentCore\runtime\bifrost (not H:\AgentRuntime).
- Confirm GET http://127.0.0.1:8080/health returns 200.
- Confirm direct MCP initialize + notifications/initialized + tools/list succeed through the gateway.
If any check fails, stop and report the exact failure. Do not edit the IDE config while Bifrost is down.

Also distinguish gateway health from IDE discovery. A healthy direct gateway plus a disconnected IDE MCP session is a client discovery/reconnect issue; do not restart or redesign Bifrost until the gateway/upstream probes fail.

Step 4 — Install global rules per your IDE's editability
Read IDE_PROFILE.yaml editability and installation_mode, then:
- direct_write: back up the live target, then write the rendered GLOBAL_RULES.md content to the documented live path.
- manual_import: present the rendered GLOBAL_RULES.md to the operator and ask them to paste/import it; do not skip.
- UI_only: follow MCP_ENROLLMENT_UI.md for the operator-driven UI/API enrollment.
- unsupported/unverified: stop and report the state; do not act.
Preserve the IDE's native safety, sandbox, approval, account, and UI settings. Do not add Swarm MCP or Swarm continuity rules.

Step 5 — Configure exactly one MCP entry
Add or merge only one AgentCore baseline entry named agentcore-gateway:
  url: http://127.0.0.1:8080/mcp
  Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
Use the schema-correct MCP_CONFIG_TEMPLATE for your IDE. For clients that cannot expand ${env:}, materialize the bearer from Windows User env into the live config only (never commit it). Remove any direct duplicate baseline MCP entries now served by Bifrost. For Cursor, remove MCP_DOCKER unless the operator explicitly approves a documented unique-capability exception. Do not paste the full upstream registry. Do not add Swarm MCP, OpenRouter MCP direct, or raw database tools. Do not create a public tunnel for localhost MCP.

Step 6 — Restart/reload the IDE
Fully restart or reload the IDE so environment references and the new MCP config are visible. The required restart behavior is in your IDE_PROFILE.yaml.

Step 7 — Validate syntax and discovery
- Validate JSON/TOML syntax of the live config.
- Confirm the IDE lists agentcore-gateway as connected/ready.
- Confirm tools/list through the gateway includes exactly ten agentcore_memory-* tools: memory_status, startup_context, retrieve_context, append_event, propose_fact, expand_source, session_open, session_close, build_handoff, docs_search.
- For ordinary IDE profiles, confirm zero agentcore_project_router-* tools. The operator maintenance profile alone may expose exactly four: project_list, project_activate, project_status, project_clear.
- Confirm no Swarm, raw SQL/database, whole-drive filesystem, or Bifrost admin tools are exposed.

Step 8 — Native memory lifecycle validation (do not skip)
Use only an AgentCore / enrolled non-Swarm project. If the selected path is Swarm-owned, stop with swarm_project_refused.
1. Resolve the current project from the IDE/workflow's exact workspace root; do not mutate machine-global project-router state from an ordinary IDE profile.
2. session_open through the signed host adapter/companion with the exact enrolled project_key + project_root and a stable task session_key. The key must be independent of chat/conversation ID and date, must be reused across new chats for the same task, and must change only for an explicitly new task. Supply that same exact project_key + project_root on every subsequent project-scoped memory call.
3. startup_context with the selected model context profile (use standard-context if your model is unknown; never lower the IDE's configured hard context window).
4. signed append_event documenting this enrollment/validation run with a deterministic idempotency key.
5. Repeat the same append_event and confirm idempotent_replay=true.
6. retrieve_context with a recovery mode and stable pagination.
7. expand_source on the event_id from step 4 to recover the exact original payload.
8. build_handoff and verify projection revisions are present.
9. session_close.
10. Resume: session_open with the same session_key and confirm the same session_id is returned with prior events accessible.
11. Project isolation: open a separate session with a different explicit AgentCore / enrolled non-Swarm project identity, retrieve_context, and prove no cross-project leak without changing shared router state.
12. Re-confirm exactly ten agentcore-memory tools.
All steps must pass before you mark a hook-capable IDE `live_validated` for
automatic lifecycle. A generic MCP-only client must instead be recorded as
`companion_only_not_automatic` unless current native middleware evidence proves
transparent signed lifecycle behavior.

Step 9 — Record sanitized evidence
Record: IDE name, version, config path, backup path, SHA-256 hashes, tool count, context profile, recovery result, resume result, isolation result, blockers, rollback path. Do not print or commit secret values.

Step 10 — Report the final state
Report one of: live_validated, configured_restart_required, awaiting_operator_import, awaiting_operator_cloud_mcp_enrollment, manual_import_pending, UI_only_pending, unsupported_with_reason, unverified, or swarm_project_refused. Do not claim completion from config files alone.
```

---

## 13. Validation and references

Run these validators after any change to this package or its contracts:

```powershell
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
python D:\github\agentcore-control-plane\scripts\bifrost\test_contracts.py
python D:\github\agentcore-control-plane\scripts\render_ide_rules.py --check
python D:\github\agentcore-control-plane\scripts\bifrost\validate_ide_enrollment_scope.py
python D:\github\agentcore-control-plane\scripts\validate_cursor_prompt_format.py D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md
python D:\github\agentcore-control-plane\scripts\validate_ecosystem_separation.py
```

Also run a secret/junk scan before commit. Live IDE configs are not committed.

Key references:

- `@D:\github\agentcore-control-plane\docs\bifrost\UNIFIED_GATEWAY_SETUP.md`
- `@D:\github\agentcore-control-plane\docs\bifrost\CAPABILITY_PROFILES.md`
- `@D:\github\agentcore-control-plane\docs\operations\OPENROUTER_MCP.md`
- `@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_AND_STUDIO.md`
- `@D:\github\agentcore-control-plane\docs\operations\AUTONOMOUS_WORKFLOW_QUICKSTART.md`
- `@D:\github\agentcore-control-plane\docs\operations\AUTOMATIC_NEW_CHAT_RECOVERY.md`
- `@D:\github\agentcore-control-plane\audits\cursor-context\CURSOR_CONTINUE_HARD_GATE_AND_STAGE_B_REGISTRATION_2026-07-24.md`
- `@D:\github\agentcore-control-plane\audits\MINIMAX_CODE_NATIVE_ACCEPTANCE_2026-07-24.md`
- `@D:\github\agentcore-control-plane\audits\MINIMAX_CLASSIC_ENROLLMENT_2026-07-24.md`
- `@D:\github\agentcore-control-plane\audits\OPEN_INTERPRETER_PERSISTENCE_2026-07-24.md`
- `@D:\github\agentcore-control-plane\audits\CHERRY_TARGET_AGENT_REPAIR_2026-07-24.md`
- `@D:\github\agentcore-control-plane\audits\CODEX_DESKTOP_REPAIR_2026-07-24.md`
- `@D:\github\agentcore-control-plane\audits\IDE_SELF_ENROLLMENT_SCOPE_VALIDATION_2026-07-21.md`

---

## 14. Historical reference (do not execute as current baseline)

Before the Bifrost cutover, each IDE carried a full direct MCP server list. That model drifted and is superseded by the single `agentcore-gateway` entry. Pre-cutover direct-server blocks are preserved only as rollback evidence under `E:\AgentCore-Backups\` and archived handoffs; they are not the current active setup path.

The July 12 Bifrost cutover handoff is historical evidence only — do not execute it as the current baseline. Use `@D:\github\agentcore-control-plane\CONTEXT_BLOCK.md` and current Phase 4 audits instead.

Former language permitting AgentCore IDE “development continuity on Swarm projects” is **historical and revoked** as of 2026-07-31. Do not restore it.

Historical Bifrost runtime path `H:\AgentRuntime\bifrost` is vacated for Bifrost; current Bifrost root is `F:\AgentCore\runtime\bifrost`. Remaining H: vacation work is Milestone M9, not this enrollment package.

The `experiments/bifrost-go-sdk-smoke/` directory is an isolated Go SDK proof-of-concept; it is **not** the Bifrost MCP Gateway.

---

## 15. New Project mandatory steps

Every new AgentCore-managed project runs Milestone 0 per `@D:\github\agentcore-control-plane\docs\agent-policy\NEW_PROJECT_BOOTSTRAP.md` before broad implementation. Swarm repositories are not AgentCore-managed projects and must not be bootstrapped through this path.

---

## CURSOR CONTINUATION PROMPT

If additional Cursor work is needed after this audit (for example, running the native memory lifecycle acceptance inside MiniMax Code, MiniMax Agent Classic, Codex, Claude Code/Desktop, Antigravity, Cherry Studio, or Open Interpreter CLI), paste the following into a fresh Cursor chat on `@D:\github\agentcore-control-plane`:

```text
Run the AgentCore native lifecycle acceptance for the selected IDE only.
Authority: @D:\github\agentcore-control-plane\PROJECT_ANCHOR.md, @D:\github\agentcore-control-plane\DOC_AUTHORITY.md, @D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md.
Read the IDE profile at @D:\github\agentcore-control-plane\ide-profiles\<ide>\IDE_PROFILE.yaml and the validation steps at @D:\github\agentcore-control-plane\ide-profiles\<ide>\VALIDATION.md.
Scope to the selected IDE's live config only; do not touch other IDEs. Prove Bifrost health at F:\AgentCore\runtime\bifrost, then complete session_open -> startup_context -> append_event -> retrieve_context -> expand_source -> build_handoff -> session_close -> resume -> project isolation on an AgentCore / enrolled non-Swarm project only, and confirm exactly ten agentcore-memory tools. If the selected project is Swarm-owned, stop with swarm_project_refused. Record sanitized evidence in @D:\github\agentcore-control-plane\audits\ and update the IDE profile last_validation_date.
```
