# Serena Dual-Control-Plane Repair

**Date:** 2026-07-26  
**Status:** `PASS_WITH_NATIVE_CURSOR_REATTACH_PENDING`  
**Scope:** AgentCore and Swarm control-plane Serena wiring only

## Root cause

The installed Serena `1.5.4.dev0` requires a top-level `languages` list in
each `.serena/project.yml`. The AgentCore project file used the legacy
`language_servers` key. The global
`C:\Users\ynotf\.serena\serena_config.yml` also registered unrelated projects
with the same stale schema, so every Serena launch emitted repeated
`KeyError: 'languages'` failures. The Swarm control repository had no Serena
project configuration.

The Bifrost prewarm wrapper had a separate lifecycle defect: it forwarded the
entire Serena stderr stream into its own pipe and waited on an unreliable,
chunk-local readiness check. The child could initialize successfully while the
wrapper blocked or Bifrost disconnected it. The wrapper also hard-coded the
AgentCore project instead of following the active project-router state.

## Changes

- Repaired AgentCore Serena project languages:
  - `D:\github\agentcore-control-plane\.serena\project.yml`
  - `languages: [python, powershell]`
- Created the Swarm control-plane Serena project configuration:
  - `D:\github\swarm-ecosystem-control\.serena\project.yml`
  - `languages: [powershell, typescript]`
- Narrowed the global Serena registry to the two control-plane projects.
- Added bounded maintenance command:
  - `D:\github\agentcore-control-plane\scripts\agentcore_cursor\serena_maintenance.py`
- Integrated an exact approval/capability gate into the existing Stage B
  shell policy. Direct out-of-worktree filesystem writes remain denied.
- Added regression tests:
  - `D:\github\agentcore-control-plane\scripts\agentcore_cursor\test_serena_maintenance.py`
- Repaired `ops\bifrost\wrappers\serena-prewarm.js`:
  - bounded readiness buffering;
  - no unbounded child-stderr forwarding;
  - bounded startup fallback;
  - active-project allowlist;
  - child restart when the AgentCore project router switches between the two
    control planes.
- Updated the Serena registry notes in
  `contracts\bifrost-upstream-mcp-registry.json`.
- Removed the explicit `grok-4.5` model pin from
  `D:\github\agentcore-control-plane\.cursor\agents\optimizer.md` so the
  background optimizer inherits the normal Cursor-selected model. Gemini 3.6
  was not present in the current background-model inventory and was not
  guessed or hard-coded.
- Added `SERENA.md`, updated the canonical global policy to revision
  `2026-07-26`, regenerated all 27 IDE rule artifacts, and installed the
  current single Cursor foundation rule at
  `C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc`.

## Rollback

The live Serena configuration backup and manifest are outside Git at:

`E:\AgentCore-Backups\agentcore-control-plane\serena-maintenance-20260726-185621`

The backup contains the global registry and both project-config before-state
copies plus `MANIFEST.json`. The Swarm project file was created by the
maintenance command and can be removed by the rollback procedure if required.

The live Cursor foundation-rule backup is:

`E:\AgentCore-Backups\agentcore-control-plane\cursor-global-rule-20260726-200111`

The rule was refreshed after the Cursor profile documentation alignment. The
latest rollback copy is:

`E:\AgentCore-Backups\agentcore-control-plane\cursor-global-rule-20260726-200321`

The final global-policy refinement and rule refresh are backed up at:

`E:\AgentCore-Backups\agentcore-control-plane\serena-global-future-projects-20260726-202233`

That refinement requires future projects to have their own current
`.serena/project.yml` with a `languages` list and prohibits sharing one Serena
process across unrelated projects.

## Validation

- Serena maintenance unit tests: **6 passed**
- Stage B hook protocol test (`--iterations 10`): **passed**
- Bifrost contract validator: **passed**
- Serena wrapper `node --check`: **passed**
- Direct Serena AgentCore semantic query: **passed**
  - Python and PowerShell servers initialized.
  - `get_symbols_overview` completed for
    `scripts/agentcore_cursor/hooks.py`.
- Direct Serena Swarm semantic query: **passed**
  - PowerShell and TypeScript servers initialized.
  - `get_symbols_overview` completed for
    `scripts/status-swarm.ps1`.
- Prewarm bridge diagnostic: **passed**
  - initialize;
  - Serena initial instructions;
  - tool forwarding.
- Dynamic project switch diagnostic: **passed**
  - AgentCore → Swarm;
  - Swarm semantic query;
  - Swarm → AgentCore.
- Authenticated Bifrost HTTP acceptance: **passed**
  - initialize;
  - tools/list;
  - project activation;
  - Serena semantic query against both control planes;
  - AgentCore restoration.
- Final Bifrost gateway health/contract test: **passed**
- Cursor user/profile settings read-only audit: no active OpenAI base-URL or
  custom-model setting was present; no `state.vscdb` edits were attempted.
- Global policy/rendering validation: **passed**
  - `render_ide_rules.py --check`
  - `validate_contracts.py`
  - `test_contracts.py` (124 checks)
  - `validate_ide_enrollment_scope.py`
- Live Cursor foundation rule installation: **passed** with backup and
  generated-content validation.

## Remaining acceptance

The global Serena registry is intentionally limited to the two control planes
for this repair. Other repositories were not modified; they must be
re-enrolled with a current `.serena/project.yml` before Serena is used there.

The current Cursor MCP meta connection was disconnected by the intentional
Bifrost restart and did not reattach inside this chat. The authenticated
localhost Bifrost acceptance above passed independently. A fresh Cursor
restart/session is still required to prove native IDE reattachment, Explorer
indexing, independent Source Control views, and combined-workspace behavior.

No Swarm product source was modified. No AgentCore or Swarm commit/push was
performed by this repair.
