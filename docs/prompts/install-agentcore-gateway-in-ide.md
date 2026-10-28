# Install AgentCore Gateway in an IDE

Reusable operator/agent prompt for **any** supported non-Swarm IDE on this PC.

**Authority:** `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`, `@D:\github\agentcore-control-plane\DOC_AUTHORITY.md`, `@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md`, `@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json`, `@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`, `@D:\github\agentcore-control-plane\ide-profiles\IDE_CAPABILITY_MATRIX.yaml`
**Endpoint:** `http://127.0.0.1:8080/mcp`
**Auth env:** `BIFROST_MCP_VIRTUAL_KEY` (never print the value)
**Display name in IDEs:** `agentcore-gateway`
**Host-native exception rule:** Zoo-Code/Roo-Code may be installed directly only in compatible VS Code-family hosts. Any direct MCP beside `agentcore-gateway` requires a proven Bifrost parity gap, bounded scope, and rollback.

---

## Prompt (copy into the current IDE agent)

```text
You are the agent inside one supported AgentCore IDE or autonomous runtime on CHAOSCENTRAL. Your job is to enroll this host and ONLY this host in AgentCore. Do not touch another host. SwarmClaw, SwarmRecall, and SwarmVault remain outside AgentCore. OpenClaw/ClawX is AgentCore-owned.

Step 0 — Identify yourself
Identify which host you are running in. Choose exactly one from:
Cursor, Codex, Devin, Eigent, Zed, Zcode, MiniMax Code/Mavis, Reasonix, OpenCode, Open Design, AutoGPT, Agent Orchestrator, Cherry Studio, LobeHub, OpenHands, Antigravity, Open Interpreter, OpenClaw/ClawX, Claude Code, Claude Desktop, MiniMax Agent Classic, Zoo-Code/Roo-Code.
If you cannot identify your host with confidence, stop and report unsupported_with_reason.

Step 1 — Read your profile and authority
Read these files using @ + full absolute Windows paths:
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\IDE_PROFILE.yaml
- @D:\github\agentcore-control-plane\ide-profiles\IDE_CAPABILITY_MATRIX.yaml
- @D:\github\agentcore-control-plane\contracts\global-agent-policy.yaml
- @D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json
- @D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json
- @D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json
- @D:\github\agentcore-control-plane\contracts\agentcore-alignment-skill-hosts.json
- @D:\github\agentcore-control-plane\docs-lock.json
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\GLOBAL_RULES.md
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\INSTALL_OR_UPDATE.md
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\VALIDATION.md
- @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\MCP_CONFIG_TEMPLATE.*
If your IDE is UI_only, also read @D:\github\agentcore-control-plane\ide-profiles\<your-ide>\MCP_ENROLLMENT_UI.md.

Step 2 — CLIENT-LOCAL EXECUTION SCOPE
The IDE running this prompt may inspect and modify only its own live configuration, rules, agent settings, and backup. Configuration examples for other IDEs are reference material only. Do not inspect, back up, repair, restart, validate, or modify another IDE. Cross-IDE reconciliation is a separate AgentCore control-plane task requiring explicit operator authorization.

Step 3 — Prove Bifrost is healthy before touching the IDE
- Confirm the scheduled task \AgentCore\AgentCore-Bifrost-Gateway exists.
- Confirm Bifrost runtime is at F:\AgentCore\runtime\bifrost.
- Confirm GET http://127.0.0.1:8080/health returns 200.
- Confirm direct MCP initialize + notifications/initialized + tools/list succeed through the gateway.
If any check fails, stop and report the exact failure. Do not edit the IDE config while Bifrost is down.

Step 4 — Install global rules and skills per your host's editability
Read IDE_PROFILE.yaml editability and installation_mode, then:
- direct_write: back up the live target, then write the rendered GLOBAL_RULES.md content to the documented live path.
- manual_import: present the rendered GLOBAL_RULES.md to the operator and ask them to paste/import it; do not skip.
- UI_only: follow MCP_ENROLLMENT_UI.md for the operator-driven UI/API enrollment.
- unsupported/unverified: stop and report the state; do not act.
Preserve the IDE's native safety, sandbox, approval, account, and UI settings.
Install the approved Bifrost skills through the host's native mechanism when supported: agentcore-project-lifecycle, agentcore-tool-discovery, morph-source-workflows, zoo-roo-code-workflows, nia, and langfuse. Otherwise install the generated rule/runtime adapter and report the actual certification state.

Step 5 — Configure the AgentCore MCP entry and proven host-native exceptions
Add or merge only one AgentCore baseline entry named agentcore-gateway:
  url: http://127.0.0.1:8080/mcp
  Authorization: Bearer ${env:BIFROST_MCP_VIRTUAL_KEY}
Use the schema-correct MCP_CONFIG_TEMPLATE for your host. Header-capable clients use the direct `:8080` endpoint with an environment-backed bearer. Approved Trust Class A clients that cannot expand environment headers use the Bifrost-owned process-attested `http://127.0.0.1:18082/mcp` endpoint without storing a bearer; unresolved, ambiguous, or unapproved callers fail closed. Other clients follow their exact profile-specific enrollment gate. Remove direct duplicate AgentCore upstreams while preserving documented host/plugin-owned integrations. Install Zoo-Code/Roo-Code directly only in compatible VS Code-family hosts. Any direct MCP beside agentcore-gateway requires a native smoke test proving a necessary capability or material performance characteristic is lost through Bifrost, plus bounded scope and rollback. Do not add Swarm MCP, raw database credentials, or whole-drive filesystem baselines.

Step 6 — Restart/reload the IDE
Fully restart or reload the IDE so environment references and the new MCP config are visible. The required restart behavior is in your IDE_PROFILE.yaml.

Step 7 — Validate syntax and discovery
- Validate JSON/TOML syntax of the live config.
- Confirm the IDE lists agentcore-gateway as connected/ready.
- Confirm direct MCP entries besides `agentcore-gateway` are documented host/plugin integrations or approved parity exceptions, never duplicate AgentCore upstreams.
- Confirm tools/list through the gateway includes exactly ten agentcore_memory-* tools: memory_status, startup_context, retrieve_context, append_event, propose_fact, expand_source, session_open, session_close, build_handoff, docs_search.
- Call listToolFiles, read the smallest relevant tool file or docs, and execute one safe read-only Code Mode canary. Retain only a compact server/tool-name inventory in context.
- Confirm an ordinary IDE profile exposes zero agentcore_project_router-* tools. The four router controls are operator-only maintenance tools.
- Confirm no Swarm, raw SQL/database, whole-drive filesystem, or Bifrost admin tools are exposed.

Step 8 — Native memory lifecycle validation (do not skip)
1. Confirm the exact repository/worktree path appears in `@D:\github\agentcore-control-plane\contracts\agentcore-project-enrollment.json`. Stop with `project_not_enrolled` when absent or `swarm_project_refused` for Swarm ownership; do not broaden the contract from the IDE.
2. Call session_open with the exact enrolled project_key + project_root and a stable task session_key. Reuse it across new chats for the same task; do not derive it from the date or conversation ID. Supply the same exact project_key + project_root on every subsequent project-scoped memory call.
3. startup_context with the selected model context profile (use standard-context if your model is unknown; never lower the IDE's configured hard context window).
4. append_event documenting this enrollment/validation run with a deterministic idempotency key.
5. Repeat the same append_event and confirm idempotent_replay=true.
6. retrieve_context with a recovery mode and stable pagination.
7. expand_source on the event_id from step 4 to recover the exact original payload.
8. build_handoff and verify projection revisions are present.
9. session_close.
10. Resume: session_open with the same session_key and confirm the same session_id is returned with prior events accessible.
11. Project isolation: open a separate session with a second exact enrolled non-Swarm project identity, retrieve_context, and prove no cross-project leak without changing shared router state.
12. Re-confirm exactly ten agentcore-memory tools.
All steps must pass before you mark the IDE live_validated.

Step 9 — Record sanitized evidence
Record: IDE name, version, config path, backup path, SHA-256 hashes, tool count, context profile, recovery result, resume result, isolation result, blockers, rollback path. Do not print or commit secret values.

Step 10 — Report the final state
Report one of: live_validated, configured_restart_required, awaiting_operator_import, awaiting_operator_cloud_mcp_enrollment, manual_import_pending, UI_only_pending, unsupported_with_reason, or unverified. Do not claim completion from config files alone.
```

---

## Host dispatch authority

The complete current host list, profile path, configuration mode, and evidence-backed status is maintained in section 8 of `@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md` and `@D:\github\agentcore-control-plane\ide-profiles\IDE_CAPABILITY_MATRIX.yaml`. Do not duplicate or infer a newer status here.

Supported certification values are `source_ready`, `installed_unverified`, `configured_restart_required`, `live_validated`, `manual_import_pending`, `UI_only_pending`, and `unsupported_with_reason`.

`@C:\Users\ynotf\.mavis` is a junction to `@C:\Users\ynotf\.minimax` and is not a separate managed client. Zoo-Code/Roo-Code is a client extension, not a Bifrost MCP upstream.

---

## Validation

After running the prompt, verify the package with:

```powershell
python D:\github\agentcore-control-plane\scripts\bifrost\validate_contracts.py
python D:\github\agentcore-control-plane\scripts\bifrost\test_contracts.py
python D:\github\agentcore-control-plane\scripts\render_ide_rules.py --check
python D:\github\agentcore-control-plane\scripts\bifrost\validate_ide_enrollment_scope.py
python D:\github\agentcore-control-plane\scripts\validate_cursor_prompt_format.py D:\github\agentcore-control-plane\docs\prompts\install-agentcore-gateway-in-ide.md
```

Do not claim completion from config files alone. Direct MCP and IDE discovery must pass.
