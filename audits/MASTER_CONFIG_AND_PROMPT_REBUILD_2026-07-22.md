# Audit — Rebuild of MASTER_CONFIG_AND_PROMPT.md

**Date:** 2026-07-22  
**Canonical repository:** `D:\github\agentcore-control-plane`  
**Branch:** `main`  
**Commit:** `9fdcb73` — pushed to `origin main`  
**Rebuilt file:** `MASTER_CONFIG_AND_PROMPT.md`  
**SHA-256 (final):** `d3f7aeb3720b2dd2b975b4de97b671aae85ceca53755c3932648d0ea2e700189`

---

## 1. Was the old master safe to use?

No. The previous `MASTER_CONFIG_AND_PROMPT.md` predated the following verified 2026-07-22 facts and would have produced stale or incorrect self-enrollment behavior if attached to a fresh IDE chat:

- It treated Mavis as a separate managed client, while the current `.mavis` path is a junction to the MiniMax Code data root.
- It conflated MiniMax Code and MiniMax Agent Classic.
- It did not include the Cherry Studio live-validated UI-only enrollment path.
- It carried stale July 12 handoff pointers and pre-cutover direct-MCP examples in the active setup path.
- It did not enforce the operator's absolute `@D:\...` path rule deterministically.
- It lacked a dedicated client-local execution scope check.
- It did not distinguish direct Bifrost diagnostics from native IDE lifecycle validation.
- It did not include deterministic validators for the failure modes listed in the rebuild request.

The old file was not actively dangerous, but it would have led agents to misidentify the client, edit the wrong IDE, or skip required UI-only operator steps.

---

## 2. Stale assumptions corrected

| Stale assumption | Correction |
|---|---|
| Mavis is a separate managed client | Removed Mavis profile, renderer, and contract hint. `C:\Users\ynotf\.mavis` is documented as a junction to `C:\Users\ynotf\.minimax`. |
| MiniMax Code / Classic are one client | Split into two distinct profiles: `ide-profiles/minimax/` (MiniMax Code) and `ide-profiles/minimax-classic/` (MiniMax Agent Classic). |
| Cherry Studio unenrolled / not documented | Added live-validated `ide-profiles/cherry-studio/` with UI-only LevelDB enrollment, scripts, and runbook evidence. |
| Obsidian tools enabled by default | Clarified that zero Obsidian tools are exposed in the default gateway baseline; the Obsidian application/vault is preserved outside the MCP surface. |
| Direct upstream MCP registry belongs in IDE configs | Removed all historical direct-MCP examples from the active setup path; only one `agentcore-gateway` entry is permitted. |
| Configuration presence equals native validation | Added explicit rule: configuration presence is not native validation; `live_validated` requires the full memory lifecycle. |
| Mutable runtime counts as architecture | Removed mutable HEAD hashes, process IDs, and tool counts from permanent architecture authority. |
| Generic JSON prompts acceptable for all clients | Each client now uses its own `IDE_PROFILE.yaml`, `MCP_CONFIG_TEMPLATE`, and `MCP_ENROLLMENT_UI.md` as applicable. |
| `D:\MCP-Control-Plane` is design authority | Restated as compatibility/live-ops evidence only. |
| Old July 12 handoff pointers | Moved to the historical-reference section (do not execute) and referenced archived rollback evidence. |

---

## 3. Final supported IDE matrix

| Client | Profile directory | Configuration mode | Native validation status |
|---|---|---|---|
| Cursor | `ide-profiles/cursor/` | generated_prompt | live_validated (2026-07-16) |
| Codex (ChatGPT desktop Codex view) | `ide-profiles/codex/` | generated_prompt | configured_restart_required |
| Claude Code | `ide-profiles/claude-code/` | generated_prompt | awaiting_operator_import |
| Claude Desktop | `ide-profiles/claude-desktop/` | generated_prompt | configured_restart_required |
| MiniMax Code | `ide-profiles/minimax/` | generated_prompt | configured_restart_required (native acceptance pending) |
| MiniMax Agent Classic | `ide-profiles/minimax-classic/` | UI_only | awaiting_operator_cloud_mcp_enrollment |
| Antigravity | `ide-profiles/antigravity/` | unverified | awaiting_operator_import |
| Open Interpreter | `ide-profiles/open-interpreter/` | generated_prompt | awaiting_operator_import |
| Cherry Studio | `ide-profiles/cherry-studio/` | UI_only | live_validated (2026-07-20) |

**Mavis:** Removed. `.mavis` is a junction to `.minimax`, not a separate executable client.

---

## 4. Per-client configuration mode

- **Cursor:** `generated_prompt` — agent reads profile, renders rules, and guides operator through the documented Cursor config path (`@C:\Users\ynotf\.cursor\mcp.json`).
- **Codex:** `generated_prompt` — agent reads profile, renders rules, and guides operator through the documented Codex config path.
- **Claude Code:** `generated_prompt` — agent reads profile and renders rules/config instructions.
- **Claude Desktop:** `generated_prompt` — agent reads profile and renders rules/config instructions.
- **MiniMax Code:** `generated_prompt` — agent reads profile and renders rules/config instructions; native acceptance still pending operator UI confirmation.
- **MiniMax Agent Classic:** `UI_only` — enrollment happens through the product's Matrix cloud UI; agent provides `MCP_ENROLLMENT_UI.md` and stops for operator action.
- **Antigravity:** `unverified` — profile exists but live path/mechanism is not evidenced on this machine; agent stops and reports.
- **Open Interpreter:** `generated_prompt` — agent reads profile and renders rules/config instructions.
- **Cherry Studio:** `UI_only` — enrollment uses the LevelDB script (`scripts/cherry/setup_cherry_providers.py`) and the AgentCore Workspace Agent prompt; agent provides `MCP_ENROLLMENT_UI.md` and stops for operator action.

---

## 5. Native-validation status

- **Cursor:** `live_validated` — full memory lifecycle confirmed through the IDE's own tool surface on 2026-07-16.
- **Cherry Studio:** `live_validated` — full memory lifecycle and UI enrollment confirmed on 2026-07-20.
- **Codex, Claude Desktop, MiniMax Code:** `configured_restart_required` — config artifacts are generated, but operator restart and final acceptance are still required.
- **Claude Code, Antigravity, Open Interpreter:** `awaiting_operator_import` — generated artifacts need operator import/paste.
- **MiniMax Agent Classic:** `awaiting_operator_cloud_mcp_enrollment` — UI-only cloud enrollment requires operator action.

No client is marked `live_validated` from config inspection alone.

---

## 6. Validation results

Ran after the rebuild:

```text
OK: registry + gateway-client schemas valid
OK: enabled servers=12 disabled/deferred=5
OK: authority + policy contracts valid (hierarchy, banners, wildcard transitional note, rule files)
OK: master-config strict audit passed
PASS 120 checks
OK: all contract/renderer tests passed
OK: all IDE GLOBAL_RULES.md renderings current
Checked 11 enrollment prompt file(s) against 11 live IDE path(s).
OK: CLIENT-LOCAL EXECUTION SCOPE present; no multi-IDE live edit instructions.
PASS: 2 file(s)
```

- **Bifrost health:** `GET http://127.0.0.1:8080/health` → `{"status":"ok","components":{"db_pings":"ok"}}`
- **Tool surface:** exactly 10 `agentcore-memory` tools, 4 `agentcore-project-router` tools, 0 Obsidian tools, 0 Swarm tools, 24 Playwright tools (current live count, not locked as permanent architecture).

---

## 7. Confirmation of single-IDE configuration

The rebuilt `MASTER_CONFIG_AND_PROMPT.md` contains a single embedded prompt that:

1. Requires the agent to identify its own IDE from the explicit supported list.
2. Refuses to edit any other IDE's live config or rules.
3. Reads only the matching `ide-profiles/<ide>/IDE_PROFILE.yaml` and related templates.
4. Configures exactly one `agentcore-gateway` entry at `http://127.0.0.1:8080/mcp`.
5. Installs or generates the matching IDE's complete AgentCore global rules per `contracts/global-agent-policy.yaml`.
6. Completes native lifecycle validation or returns an accurate `manual_import`, `UI_only`, `unsupported_with_reason`, or `unverified` gate.

The `CLIENT-LOCAL EXECUTION SCOPE` paragraph is present in both `MASTER_CONFIG_AND_PROMPT.md` and `docs/prompts/install-agentcore-gateway-in-ide.md`.

---

## 8. Limitations requiring operator UI action

- **Cherry Studio:** operator must fully quit Cherry Studio, run the LevelDB enrollment script, and relaunch; the bearer cannot remain committed.
- **MiniMax Agent Classic:** operator must complete cloud MCP enrollment through the Matrix UI; no file-based config exists.
- **Claude Code, Claude Desktop, Codex, Antigravity, Open Interpreter:** operator must import/paste generated rules or restart the IDE to finalize enrollment.
- **MiniMax Code:** operator must confirm native acceptance after restart.
- **No live IDE configs were changed during this audit.** All changes are repo-controlled artifacts; live IDE rollout requires the operator to attach the master file to a fresh IDE chat and run the embedded prompt.

---

## 9. Files changed

Modified:
- `MASTER_CONFIG_AND_PROMPT.md` — rebuilt thin, self-sufficient universal self-enrollment package.
- `docs/prompts/install-agentcore-gateway-in-ide.md` — aligned with the master file's dynamic profile selection and absolute-path rules.
- `contracts/agentcore-gateway-client.json` — removed Mavis render hint; clarified MiniMax Code junction.
- `ide-profiles/IDE_CAPABILITY_MATRIX.yaml` — updated matrix: removed Mavis, added Cherry Studio and MiniMax Agent Classic, split MiniMax Code.
- `ide-profiles/README.md` — updated semantic parity report.
- `scripts/bifrost/validate_contracts.py` — added `strict_master_config_audit()` covering all stated failure modes.
- `scripts/validate_cursor_prompt_format.py` — exclude command lines from bare-path checks.

Added:
- `ide-profiles/cherry-studio/` — complete profile, templates, rules, install, validation, UI enrollment.

Deleted:
- `ide-profiles/mavis/` — Mavis is not a separate executable client.
- `renderers/gateway-clients/mavis.json` — same reason.

Not modified (per instructions):
- `PROJECT_ANCHOR.md`
- `BLUEPRINT.md`

Not committed (unrelated inherited WIP / scratch):
- `.cursor/hooks/state/continual-learning-index.json`
- `audits/M6/studio-launch-stdout.log`
- `docs/operations/archive/BLUEPRINT-2026-07-19.md` (reset)
- `docs/operations/archive/development-chat/BLUEPRINT-yesterday.md` (reset)
- All `scripts/_scratch/`, `scripts/cherry/_scratch*.py`, `scripts/cherry/_node_workspace/`, and other untracked scratch/runtime files.

---

## 10. Commit and push

Done.
- Commit: `9fdcb73` — `Rebuild MASTER_CONFIG_AND_PROMPT.md as verified universal IDE self-enrollment package`
- Pushed: `main -> origin main`
- 17 files changed, 939 insertions(+), 946 deletions(-)
