# Install AgentCore Gateway in an IDE

Reusable operator/agent prompt for **any** supported non-Swarm IDE on this PC.

**Authority:** `@D:\github\agentcore-control-plane\PROJECT_ANCHOR.md`, `@D:\github\agentcore-control-plane\DOC_AUTHORITY.md`, `@D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md`, `@D:\github\agentcore-control-plane\contracts\agentcore-gateway-client.json`, `@D:\github\agentcore-control-plane\contracts\bifrost-upstream-mcp-registry.json`, `@D:\github\agentcore-control-plane\ide-profiles\IDE_CAPABILITY_MATRIX.yaml`
**Endpoint:** `http://127.0.0.1:8080/mcp`
**Auth env:** `BIFROST_MCP_VIRTUAL_KEY` (never print the value)
**Display name in IDEs:** `agentcore-gateway`

---

## Prompt (copy into the current IDE agent)

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

## Supported IDE matrix

| Client | Profile | Configuration mode | Native validation status |
| --- | --- | --- | --- |
| Cursor | `ide-profiles/cursor/` | generated_prompt | live_validated (2026-07-16) |
| Codex | `ide-profiles/codex/` | generated_prompt | configured_restart_required |
| Claude Code | `ide-profiles/claude-code/` | generated_prompt | awaiting_operator_import |
| Claude Desktop | `ide-profiles/claude-desktop/` | generated_prompt | configured_restart_required |
| MiniMax Code | `ide-profiles/minimax/` | generated_prompt | configured_restart_required (native acceptance pending) |
| MiniMax Agent Classic | `ide-profiles/minimax-classic/` | UI_only | awaiting_operator_cloud_mcp_enrollment |
| Antigravity | `ide-profiles/antigravity/` | unverified | awaiting_operator_import |
| Open Interpreter | `ide-profiles/open-interpreter/` | generated_prompt | awaiting_operator_import |
| Cherry Studio | `ide-profiles/cherry-studio/` | UI_only | live_validated (2026-07-20) |

`@C:\Users\ynotf\.mavis` is a junction to `@C:\Users\ynotf\.minimax` (same MiniMax Code data root) and is not a separate managed client.

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
