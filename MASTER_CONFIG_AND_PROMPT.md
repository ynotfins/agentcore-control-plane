# MASTER_CONFIG_AND_PROMPT.md — AgentCore Universal IDE Self-Enrollment Package

**Updated:** 2026-07-22 — dynamic IDE-profile selection, MiniMax Code and MiniMax Agent Classic split into distinct profiles, Cherry Studio live-validated, Mavis removed as separate client, Obsidian tools not in default gateway baseline, zero mutable runtime counts as architecture authority.
**Repository:** `@D:\github\agentcore-control-plane`
**Authority:** `PROJECT_ANCHOR.md` §0 Bifrost Gateway Override → `DOC_AUTHORITY.md` → `BLUEPRINT.md` → `CONTEXT_BLOCK.md` → current contracts/runbooks
**Contracts:** `contracts/agentcore-gateway-client.json`, `contracts/bifrost-upstream-mcp-registry.json`, `contracts/global-agent-policy.yaml`, `contracts/model-context-profiles.json`

This file is the thin, self-sufficient root setup guide for every supported non-Swarm IDE on `CHAOSCENTRAL`. It contains architecture, authority order, security boundaries, memory lifecycle, and **one** embedded self-enrollment prompt. Client-specific schemas, long procedures, and historical evidence live in `ide-profiles/`, `renderers/gateway-clients/`, and `docs/`.

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

---

## 2. Architecture — exactly one gateway

```text
Supported non-Swarm IDE (Cursor, Codex, Claude Code/Desktop, MiniMax Code and MiniMax Agent Classic, Antigravity, Open Interpreter, Cherry Studio)
  -> ONE MCP entry: agentcore-gateway
       url:  http://127.0.0.1:8080/mcp
       auth: Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
  -> Bifrost native Gateway (H:\AgentRuntime\bifrost, bifrost-http.exe v2.0.0-prerelease1)
  -> approved upstream MCP servers from contracts/bifrost-upstream-mcp-registry.json
```

Never paste the full upstream registry into an IDE. Never add a second AgentCore MCP front door. Project-specific behavior is selected through `agentcore-project-router`, not duplicate gateway entries.

---

## 3. Security and Swarm boundaries

- Secrets live only in Windows User-scope environment variables. No `.env` files.
- Never print, store, or commit resolved bearer tokens, virtual keys, API keys, PATs, DB passwords, or live secret-bearing IDE configs.
- Live IDE configs are app-owned; changes flow through the approved self-enrollment prompt/ops with backup first.
- SwarmRecall, SwarmVault, and SwarmClaw are a **separate ecosystem**. Do not require Swarm MCP, Swarm databases, or Swarm file roots for non-Swarm IDE work. Do not modify Swarm product installs.
- OpenClaw/ClawX are Swarm-managed and outside the non-Swarm Bifrost IDE cutover.
- Forbidden active routes: Context7, raw Mem0, direct Composio, Hostinger, `:65432`, whole-drive filesystem MCP roots, Postgres credentials in IDE configs, `global-memory-gateway` as a default route.

---

## 4. Stable memory lifecycle — ten tools

The canonical non-Swarm memory identity is `agentcore-memory` (Bifrost client name `agentcore_memory`). The normal agent surface is **exactly ten tools**:

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

Project-router surface (four tools): `project_list`, `project_activate`, `project_status`, `project_clear`.

No SQL, DDL, database-admin, backup-admin, or Bifrost-admin tools are exposed to normal agents. Normal agents have no direct database access; never put `AGENT_CORE_PG*` credentials in IDE configs. `Obsidian Vault` is preserved as an application and vault outside the default MCP surface; the default gateway baseline exposes zero Obsidian tools.

AgentCore durable memory is **effectively unbounded** by model-token limits. Model context limits control only one assembled request. Compaction is **non-destructive**: summaries are versioned and expandable, and no summary may replace or delete canonical originals. Describe it as **model-limit-aware active context over an effectively unbounded durable local project history**.

Normal lifecycle at every new chat:

1. Activate the project/worktree via `agentcore-project-router`.
2. Read the generated `@D:\github\agentcore-control-plane\.agentcore\STATE.md`.
3. `session_open` with a stable `session_key` (reuse for the same task; new key for a new task under the same project).
4. `startup_context` with the selected model context profile.
5. `append_event` before meaningful tool execution (operator prompt verbatim after secret redaction, deterministic idempotency key).
6. `retrieve_context` for missing chronology; `expand_source` for exact originals; `build_handoff` for current reconstruction.
7. `session_close` at clean task end.

Before asking the operator to repeat project history, query `agentcore-memory`. Never directly edit `GLOBAL_STATE.md`, project `STATE.md`, `DECISIONS.md`, or `CONTEXT_INDEX.md` — these are generated projections; PostgreSQL is canonical.

---

## 5. Project/worktree and context-management rules

- Write only inside the assigned repo/worktree and role-appropriate runtime roots per `docs/DRIVE_WRITE_BOUNDARY_RULE.md`.
- Every durable project asset on `D:`, `E:`, `F:`, `G:`, or `H:` must be registered via the governed memory surface (`register_artifact_location`). Temporary files on `I:` are exempt only while temporary and must be deleted or promoted at task close.
- Query resource locations through `retrieve_context` and `build_handoff`; the canonical view is `agentcore.v_project_resource_map`.
- `CONTEXT_INDEX.md` is a generated projection; agents never directly edit it.
- Never create an unregistered durable project location on `D:`, `E:`, `F:`, `G:`, or `H:`.
- Push after every completed task per `docs/GIT_PUSH_ONLY_POLICY.md`. Never pull/fetch/merge/rebase or force-push without explicit operator instruction. Stage only source-controlled files.

---

## 6. Global-rule installation requirements

Attaching this file and running the embedded prompt must install or generate the matching IDE's complete AgentCore global rules. The canonical semantic policy is `contracts/global-agent-policy.yaml`. Rendered per-IDE rules live in `ide-profiles/<ide>/GLOBAL_RULES.md`.

Delivery depends on the IDE's declared editability (read from `ide-profiles/<ide>/IDE_PROFILE.yaml`):

- `direct_write` — write the rendered `GLOBAL_RULES.md` to the documented live target after backup.
- `manual_import` — present the rendered `GLOBAL_RULES.md` to the operator and require import/paste; do not silently skip.
- `UI_only` — follow the enrollment UI document in `ide-profiles/<ide>/MCP_ENROLLMENT_UI.md`.
- `unsupported` — stop and report `unsupported_with_reason`.
- `unverified` — stop and report the missing evidence before acting.

Preserve client-native safety, sandbox, approval, account, and UI settings. Do not overwrite non-AgentCore app preferences.

---

## 7. Client identification and profile selection

Supported non-Swarm clients (current as of 2026-07-22):

| Client | Profile directory | Configuration mode | Native validation status |
| --- | --- | --- | --- |
| Cursor | `ide-profiles/cursor/` | generated_prompt | live_validated (2026-07-16) |
| Codex (ChatGPT desktop Codex view) | `ide-profiles/codex/` | generated_prompt | configured_restart_required |
| Claude Code | `ide-profiles/claude-code/` | generated_prompt | awaiting_operator_import |
| Claude Desktop | `ide-profiles/claude-desktop/` | generated_prompt | configured_restart_required |
| MiniMax Code | `ide-profiles/minimax/` | generated_prompt | configured_restart_required (native acceptance pending) |
| MiniMax Agent Classic | `ide-profiles/minimax-classic/` | UI_only | awaiting_operator_cloud_mcp_enrollment |
| Antigravity | `ide-profiles/antigravity/` | unverified | awaiting_operator_import |
| Open Interpreter | `ide-profiles/open-interpreter/` | generated_prompt | awaiting_operator_import |
| Cherry Studio | `ide-profiles/cherry-studio/` | UI_only | live_validated (2026-07-20) |

`@C:\Users\ynotf\.mavis` is a junction to `@C:\Users\ynotf\.minimax` (same MiniMax Code data root). It is not a separate executable Mavis client and does not receive its own managed profile. MiniMax Code and MiniMax Agent Classic are distinct products with distinct profiles, paths, and enrollment mechanisms; do not conflate them.

The agent must:
1. Identify its own IDE from the list above.
2. Read `ide-profiles/<ide>/IDE_PROFILE.yaml`.
3. Refuse to edit a different IDE's live config or rules.
4. Use only the matching profile's template and procedure.
5. Stop with `unsupported_with_reason` if the IDE is unsupported or unidentifiable.

---

## 8. Exact single-gateway contract

The canonical gateway connection is defined in `contracts/agentcore-gateway-client.json`:

- Name: `agentcore-gateway`
- URL: `http://127.0.0.1:8080/mcp`
- Auth header: `Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}`
- Timeout: 300 seconds
- Transport: `http/streamable`

Cursor canonical path: `@C:\Users\ynotf\.cursor\mcp.json`. Every other client uses its own documented path from `ide-profiles/<ide>/IDE_PROFILE.yaml` and `contracts/agentcore-gateway-client.json`.

If a client cannot expand `${env:…}` in headers, materialize the Windows User-env value into the **live** config only during the approved cutover — never commit the resolved value.

Adding future MCP servers: add once to `contracts/bifrost-upstream-mcp-registry.json`, pin version, classify, render Bifrost config, validate, restart Bifrost, test. Leave IDE configs unchanged unless the single gateway connection itself changes.

---

## 9. Backup, secrets, and safe handling

Before any live IDE config change:
- Back up the live config outside Git to `E:\AgentCore-Backups\<client>-<timestamp>`.
- Record SHA-256 of the backup and the original.
- Preserve model, auth, account, sandbox, context, profile, theme, and non-MCP app settings.

After any change:
- Validate JSON/TOML syntax.
- Restart/reload the IDE so environment references are visible.
- Confirm the IDE shows `agentcore-gateway` connected/ready.
- Confirm the ten-tool `agentcore-memory` surface and four project-router tools appear through the gateway.
- Confirm Swarm, raw database, whole-drive filesystem, and Bifrost admin tools are absent.

---

## 10. Direct diagnostic versus native-validation distinction

**Direct diagnostic** (HTTP against Bifrost) proves the gateway and registry are healthy. It does **not** prove the IDE itself enrolled correctly. Allowed diagnostics:

- `GET http://127.0.0.1:8080/health` → 200
- Direct MCP `initialize`, `notifications/initialized`, `tools/list` against the gateway
- Safe read-only calls like `agentcore_memory-memory_status` or `agentcore_project_router-project_list`

**Native validation** requires the IDE's own agent to complete the full memory lifecycle through its own tool surface:

1. `session_open` — stable session_key and project/client/agent identity
2. `startup_context` — profile reported; hard limit not lowered
3. `append_event` — idempotency key; prompt committed before tool execution
4. `retrieve_context` — recovery pagination; continuation cursor stable
5. `expand_source` — exact original retrievable from event_id
6. `build_handoff` — handoff packet; projection revisions present
7. `session_close` — ended_at set; handoff appended
8. Resume — same session_key reopens; original events accessible
9. Project isolation — project_key boundary enforced
10. Tool surface — exactly ten `agentcore-memory` tools; none added or removed

Do not mark live_validated from config inspection alone. Configuration presence is not native validation.

---

## 11. Manual, UI-only, and unsupported stopping states

Stop and report the accurate state when:

- **manual_import** — rules or MCP config must be imported by the operator; the agent cannot safely complete the step unattended. Provide the exact rendered artifact and instructions.
- **UI_only** — the product has no file-based config; enrollment happens through the product's UI/API (e.g., Cherry Studio LevelDB scripts, MiniMax Classic Matrix cloud). Provide the enrollment UI document and ask the operator to run it.
- **unsupported_with_reason** — the product does not support the required MCP baseline or cannot be identified. State the reason.
- **unverified** — the live config path or rule mechanism is not evidenced on this machine. Do not guess.
- **awaiting_operator_import** / **awaiting_operator_cloud_mcp_enrollment** — configuration artifact is ready; operator action and a fresh IDE chat are required to promote to `live_validated`.

---

## 12. Global IDE setup prompt (copy into the current IDE agent and run)

```text
You are the agent inside one supported non-Swarm IDE on CHAOSCENTRAL. Your job is to enroll this IDE and ONLY this IDE in AgentCore. Do not touch any other IDE.

Step 0 — Identify yourself
Identify which IDE you are running in. Choose exactly one from:
Cursor, Codex, Claude Code, Claude Desktop, MiniMax Code, MiniMax Agent Classic, Antigravity, Open Interpreter, Cherry Studio.
If you cannot identify your IDE with confidence, stop and report unsupported_with_reason.

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
If your IDE is UI_only, also read @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\MCP_ENROLLMENT_UI.md.

Step 2 — CLIENT-LOCAL EXECUTION SCOPE
The IDE running this prompt may inspect and modify only its own live configuration, rules, agent settings, and backup. Configuration examples for other IDEs are reference material only. Do not inspect, back up, repair, restart, validate, or modify another IDE. Cross-IDE reconciliation is a separate AgentCore control-plane task requiring explicit operator authorization.

Step 3 — Prove Bifrost is healthy before touching the IDE
- Confirm the scheduled task \AgentCore\AgentCore-Bifrost-Gateway exists.
- Confirm Bifrost runtime is at H:\AgentRuntime\bifrost.
- Confirm GET http://127.0.0.1:8080/health returns 200.
- Confirm direct MCP initialize + notifications/initialized + tools/list succeed through the gateway.
If any check fails, stop and report the exact failure. Do not edit the IDE config while Bifrost is down.

Step 4 — Install global rules per your IDE's editability
Read IDE_PROFILE.yaml editability and installation_mode, then:
- direct_write: back up the live target, then write the rendered GLOBAL_RULES.md content to the documented live path.
- manual_import: present the rendered GLOBAL_RULES.md to the operator and ask them to paste/import it; do not skip.
- UI_only: follow MCP_ENROLLMENT_UI.md for the operator-driven UI/API enrollment.
- unsupported/unverified: stop and report the state; do not act.
Preserve the IDE's native safety, sandbox, approval, account, and UI settings.

Step 5 — Configure exactly one MCP entry
Add or merge only one AgentCore baseline entry named agentcore-gateway:
  url: http://127.0.0.1:8080/mcp
  Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
Use the schema-correct MCP_CONFIG_TEMPLATE for your IDE. For clients that cannot expand ${env:}, materialize the bearer from Windows User env into the live config only (never commit it). Remove any direct duplicate baseline MCP entries now served by Bifrost. For Cursor, remove MCP_DOCKER unless the operator explicitly approves a documented unique-capability exception. Do not paste the full upstream registry. Do not add Swarm MCP, OpenRouter MCP direct, or raw database tools.

Step 6 — Restart/reload the IDE
Fully restart or reload the IDE so environment references and the new MCP config are visible. The required restart behavior is in your IDE_PROFILE.yaml.

Step 7 — Validate syntax and discovery
- Validate JSON/TOML syntax of the live config.
- Confirm the IDE lists agentcore-gateway as connected/ready.
- Confirm tools/list through the gateway includes exactly ten agentcore_memory-* tools: memory_status, startup_context, retrieve_context, append_event, propose_fact, expand_source, session_open, session_close, build_handoff, docs_search.
- Confirm exactly four agentcore_project_router-* tools: project_list, project_activate, project_status, project_clear.
- Confirm no Swarm, raw SQL/database, whole-drive filesystem, or Bifrost admin tools are exposed.

Step 8 — Native memory lifecycle validation (do not skip)
1. Activate the current project via agentcore_project_router-project_activate (e.g., agentcore-control-plane at `@D:\github\agentcore-control-plane`).
2. session_open with a stable session_key that includes your IDE id and today's date.
3. startup_context with the selected model context profile (use standard-context if your model is unknown; never lower the IDE's configured hard context window).
4. append_event documenting this enrollment/validation run with a deterministic idempotency key.
5. Repeat the same append_event and confirm idempotent_replay=true.
6. retrieve_context with a recovery mode and stable pagination.
7. expand_source on the event_id from step 4 to recover the exact original payload.
8. build_handoff and verify projection revisions are present.
9. session_close.
10. Resume: session_open with the same session_key and confirm the same session_id is returned with prior events accessible.
11. Project isolation: activate a different registered project, retrieve_context, and prove no cross-project leak.
12. Re-confirm exactly ten agentcore-memory tools.
All steps must pass before you mark the IDE live_validated.

Step 9 — Record sanitized evidence
Record: IDE name, version, config path, backup path, SHA-256 hashes, tool count, context profile, recovery result, resume result, isolation result, blockers, rollback path. Do not print or commit secret values.

Step 10 — Report the final state
Report one of: live_validated, configured_restart_required, awaiting_operator_import, awaiting_operator_cloud_mcp_enrollment, manual_import_pending, UI_only_pending, unsupported_with_reason, or unverified. Do not claim completion from config files alone.
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
```

Also run a secret/junk scan before commit. Live IDE configs are not committed.

Key references:
- `@D:\github\agentcore-control-plane\docs\bifrost\UNIFIED_GATEWAY_SETUP.md`
- `@D:\github\agentcore-control-plane\docs\bifrost\CAPABILITY_PROFILES.md`
- `@D:\github\agentcore-control-plane\docs\operations\OPENROUTER_MCP.md`
- `@D:\github\agentcore-control-plane\docs\operations\AUTOMATIC_NEW_CHAT_RECOVERY.md`
- `@D:\github\agentcore-control-plane\audits\M8\UNBOUNDED_DURABLE_MEMORY_RELEASE_ACCEPTANCE.md`
- `@D:\github\agentcore-control-plane\audits\MEMORY_GATEWAY_HEALTH_2026-07-22.md`
- `@D:\github\agentcore-control-plane\audits\CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md`
- `@D:\github\agentcore-control-plane\audits\MINIMAX_CODE_REPAIR_2026-07-22.md`
- `@D:\github\agentcore-control-plane\audits\MINIMAX_CLASSIC_REPAIR_2026-07-22.md`
- `@D:\github\agentcore-control-plane\audits\IDE_SELF_ENROLLMENT_SCOPE_VALIDATION_2026-07-21.md`

---

## 14. Historical reference (do not execute as current baseline)

Before the Bifrost cutover, each IDE carried a full direct MCP server list (arabold-docs, serena, sequential-thinking, swarmrecall, swarmvault, filesystem with broad roots, etc.). That model drifted and is superseded by the single `agentcore-gateway` entry. The pre-2026-07-12 direct-server blocks are preserved only as rollback evidence under `E:\AgentCore-Backups\` and archived handoffs; they are not the current active setup path.

The `experiments/bifrost-go-sdk-smoke/` directory is an isolated Go SDK proof-of-concept; it is **not** the Bifrost MCP Gateway.

---

## CURSOR CONTINUATION PROMPT

If additional Cursor work is needed after this audit (for example, running the native memory lifecycle acceptance inside MiniMax Code, MiniMax Agent Classic, Codex, Claude Code/Desktop, Antigravity, or Open Interpreter), paste the following into a fresh Cursor chat on `@D:\github\agentcore-control-plane`:

```text
Run the AgentCore native lifecycle acceptance for the selected IDE only.
Authority: @D:\github\agentcore-control-plane\PROJECT_ANCHOR.md, @D:\github\agentcore-control-plane\DOC_AUTHORITY.md, @D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md.
Read the IDE profile at @D:\github\agentcore-control-plane\ide-profiles\<ide>\IDE_PROFILE.yaml and the validation steps at @D:\github\agentcore-control-plane\ide-profiles\<ide>\VALIDATION.md.
Scope to the selected IDE's live config only; do not touch other IDEs. Prove Bifrost health, then complete session_open -> startup_context -> append_event -> retrieve_context -> expand_source -> build_handoff -> session_close -> resume -> project isolation, and confirm exactly ten agentcore-memory tools. Record sanitized evidence in @D:\github\agentcore-control-plane\audits\ and update the IDE profile last_validation_date.
```
