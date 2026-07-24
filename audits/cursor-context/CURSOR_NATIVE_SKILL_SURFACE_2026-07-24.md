# Cursor Native Skill Surface & Version Verification Audit (Phase 5C)

**Date:** 2026-07-24  
**Task:** PHASE_5C_FINAL_LEAN_SURFACE_AND_VERSION_VERIFICATION  
**Status:** PASS / READY_FOR_CURSOR_CONTINUE_HARD_GATE  

---

## 1. Executive Summary

This audit completes **Phase 5C — Final Lean-Surface and Version Verification**. It establishes the unambiguous running application binary identity for Cursor, verifies the removal and backup of temporary fixture-local skill copies, proves the inactive status of the Superpowers plugin during lean baseline operation, and confirms all 19 system lean-surface gates.

---

## 2. Running Cursor Application Binary Identity

The prior audit (Phase 5B) noted Cursor version `0.45.11` as recorded in SQLite database `state.vscdb`. Inspection proves that value was a stale, historical database key and NOT application-version authority.

### Active Application Metadata

- **Executable Path:** `C:\Users\ynotf\AppData\Local\Programs\cursor\Cursor.exe`
- **ProductName:** `Cursor`
- **ProductVersion:** `3.12.30`
- **FileVersion:** `3.12.30` (FileVersionRaw `3.12.30.0`)
- **Architecture:** `x64`
- **Install Root:** `C:\Users\ynotf\AppData\Local\Programs\cursor`
- **Update Channel:** `stable`
- **Build Commit:** `63a2996a10d9e476b6c28e951dd7691d9c0cf480`
- **Build Date:** `2026-07-21T22:50:03.568Z`
- **VS Code Base Version:** `1.128.0`
- **Windows Registry Registration:** `HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\Cursor (User)`
  - DisplayName: `Cursor (User)`
  - DisplayVersion: `3.12.30`
  - InstallLocation: `C:\Users\ynotf\AppData\Local\Programs\cursor\`
  - InstallDate: `20260721`
  - Publisher: `Anysphere`

### Coexisting Installation & Stale Version Analysis

- **Coexisting Binary Root Search:** Checked `AppData\Local`, `AppData\Roaming`, `Program Files`, `Program Files (x86)`, and HKLM/HKCU registry hives. Zero coexisting or obsolete secondary Cursor installation roots exist.
- **Stale Version Explanation:** SQLite database `C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\state.vscdb` retained a legacy `0.45.11` version string key from an older 0.x release series (late 2024 / early 2025). The database key was not updated or purged during application updates. Executable binary metadata and Windows installer registry confirm the active running application is unambiguously **version 3.12.30 (x64)**.

---

## 3. Fixture-Local Skill Removal & Backup

### SHA-256 Hash Verification

- **Canonical Source:** `D:\github\agentcore-control-plane\skills\agentcore-project-lifecycle\SKILL.md`
- **Global Live Path:** `C:\Users\ynotf\.cursor\skills\agentcore-project-lifecycle\SKILL.md`
- **Fixture Local Path:** `D:\github\phase5-disposable-fixture\.cursor\skills\agentcore-project-lifecycle\SKILL.md`
- **SHA-256 Hash:** `7C97B389A4123AA0A3E4301BD9CE05F52110C58A210EA324C06074B7F4209B68` (Byte-identical across all three paths prior to cleanup)

### Cleanup Execution

1. **Backup:** Copied `D:\github\phase5-disposable-fixture\.cursor\skills\agentcore-project-lifecycle\SKILL.md` to `D:\github\agentcore-control-plane\audits\cursor-context\archive\fixture_local_skill_backup_20260724.SKILL.md`.
2. **File Removal:** Deleted `D:\github\phase5-disposable-fixture\.cursor\skills\agentcore-project-lifecycle\SKILL.md`.
3. **Directory Cleanup:** Pruned empty parent directories `D:\github\phase5-disposable-fixture\.cursor\skills\agentcore-project-lifecycle`, `D:\github\phase5-disposable-fixture\.cursor\skills`, and `D:\github\phase5-disposable-fixture\.cursor`.
4. **Verification:** `Test-Path D:\github\phase5-disposable-fixture\.cursor` returned `False`.

---

## 4. Superpowers Inactivity Proof

Superpowers plugin cache source remains stored at `C:\Users\ynotf\.cursor\plugins\cache\cursor-public\superpowers`, but contributes **zero active context** to Cursor during the lean baseline:

- **Skills:** 0 Superpowers skills in active operator skill catalog (`C:\Users\ynotf\.cursor\skills`).
- **Rules:** 0 Superpowers rules active (only `agentcore-foundation.mdc` in `C:\Users\ynotf\.cursor\rules`).
- **Custom Agents:** 0 Superpowers custom agents configured.
- **Commands:** 0 Superpowers commands registered.
- **Hooks:** 0 Superpowers hooks in `.cursor\hooks.json` or `.agents\hooks`. Only `sessionStart` and `beforeSubmitPrompt` calling `agentcore-hook.ps1` exist in `.cursor\hooks.json`.
- **SessionStart Injection:** None.
- **Priority Blocks:** No `EXTREMELY-IMPORTANT` skill-priority block injected.
- **Third-Party Setting:** `cursor/thirdPartyExtensibilityEnabled = false` in `state.vscdb`.

---

## 5. Native Skill Catalog & Hook Catalog

### Native Skill Catalog

| Category | Location | Count | Items |
|---|---|---|---|
| **Operator Managed** | `C:\Users\ynotf\.cursor\skills` | 1 | `agentcore-project-lifecycle` |
| **Project Local** | `D:\github\phase5-disposable-fixture\.cursor` | 0 | None (removed & backed up) |
| **Shared `.agents`** | `C:\Users\ynotf\.agents\skills` | 0 | None (quarantined) |
| **Plugin Provided** | `C:\Users\ynotf\.cursor\plugins` | 0 | 0 active (cache only, third-party discovery OFF) |
| **Codex / Claude** | External | 0 | Excluded from Cursor |
| **Built-in Cursor** | `C:\Users\ynotf\.cursor\skills-cursor` | 22 | 13 built-in skill folders (`automate`, `babysit`, `canvas`, `create-hook`, `create-rule`, `create-skill`, `create-subagent`, `env-setup`, `loop`, `migrate-to-skills`, `onboard`, `review`, `review-bugbot`, `review-security`, `sdk`, `shell`, `split-to-prs`, `statusline`, `update-cli-config`, `update-cursor-settings`) + manifests |

### Hook Catalog

- **File:** `D:\github\agentcore-control-plane\.cursor\hooks.json`
- **Active Registered Hook Events:**
  1. `sessionStart`: `powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/agentcore-hook.ps1 -Event sessionStart` (timeout: 90s)
  2. `beforeSubmitPrompt`: `powershell -NoProfile -ExecutionPolicy Bypass -File .cursor/hooks/agentcore-hook.ps1 -Event beforeSubmitPrompt` (timeout: 90s)
- **Zero other hook events registered.**

---

## 6. Final Lean-Surface Gates Verification Matrix

| # | Lean-Surface Requirement | Result | Evidence |
|---|---|---|---|
| 1 | Global Rules | **PASS** | Exactly 1 active rule (`agentcore-foundation.mdc`), 0 other active rules (`30-memory-usage.mdc.quarantined`) |
| 2 | Operator Lifecycle Skill | **PASS** | Exactly 1 skill (`agentcore-project-lifecycle`) in `C:\Users\ynotf\.cursor\skills` |
| 3 | Project Local Duplicate | **PASS** | 0 duplicates (`D:\github\phase5-disposable-fixture\.cursor` removed) |
| 4 | Shared `.agents` Skills | **PASS** | 0 active (`C:\Users\ynotf\.agents\skills` absent/quarantined) |
| 5 | Plugin-provided Skills | **PASS** | 0 active |
| 6 | Built-in Cursor Skills | **PASS** | 13 built-in skill folders / 22 manifest items reported separately |
| 7 | MCP Configuration | **PASS** | 1 entry (`agentcore-gateway` in `C:\Users\ynotf\.cursor\mcp.json`) |
| 8 | Third-party Discovery | **PASS** | OFF (`cursor/thirdPartyExtensibilityEnabled = false`) |
| 9 | Hook Registration | **PASS** | Only `sessionStart` and `beforeSubmitPrompt` |
| 10 | Bifrost Gateway Health | **PASS** | HTTP 200 OK (`{"components":{"db_pings":"ok"},"status":"ok"}`) |
| 11 | PostgreSQL Service | **PASS** | `AgentCore-PostgreSQL18` Running and Automatic (`127.0.0.1:55433`) |
| 12 | Memory Tools | **PASS** | Exactly 10 tools (`agentcore_memory-*`) |
| 13 | Project-Router Tools | **PASS** | Exactly 4 tools (`agentcore_project_router-*`) |
| 14 | Skills-Hub Tools | **PASS** | Exactly 3 read-only tools (`skills_hub-*`) |
| 15 | Memory Lifecycle | **PASS** | Full lifecycle green (329 events, 84 projections, 145 sessions) |
| 16 | Current Projections | **PASS** | Verified in `agentcore.projection_revisions` |
| 17 | LangGraph Fixture | **PASS** | 17/17 tests PASS in `scripts/agentcore_workflow/tests/fixture_e2e.py` |
| 18 | Third-party Integrations | **PASS** | 0 Firebase, 0 Sheets tools exposed |
| 19 | Swarm Ecosystem | **PASS** | Untouched (0 Swarm MCP entries in Cursor) |

---

## 7. Rollback Paths & Files Changed

### Rollback Paths

- **Backed-Up Fixture Skill:** `D:\github\agentcore-control-plane\audits\cursor-context\archive\fixture_local_skill_backup_20260724.SKILL.md`
- Restore command if rollback needed:
  `Copy-Item "D:\github\agentcore-control-plane\audits\cursor-context\archive\fixture_local_skill_backup_20260724.SKILL.md" -Destination "D:\github\phase5-disposable-fixture\.cursor\skills\agentcore-project-lifecycle\SKILL.md"`

### Files Changed

- `audits/cursor-context/CURSOR_NATIVE_SKILL_SURFACE_2026-07-24.md` (updated with Phase 5C verification)
- `audits/cursor-context/archive/fixture_local_skill_backup_20260724.SKILL.md` (untracked backup artifact)
- Deleted from `D:\github\phase5-disposable-fixture`: `.cursor/skills/agentcore-project-lifecycle/SKILL.md` and empty parent directories.

---

## 8. Source Control Execution

Source-controlled audit evidence staged, committed, and pushed per Git policy:
- **Branch:** `main`
- **Commit:** `docs(audit): complete Phase 5C lean-surface and version verification`
- **Push Target:** `origin main`

---

**Status:** READY_FOR_CURSOR_CONTINUE_HARD_GATE
