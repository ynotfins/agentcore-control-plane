# Cursor Native Skill Surface & Third-Party Discovery Audit

**Date:** 2026-07-24  
**Task:** PHASE_5B_NATIVE_SKILL_SURFACE_NORMALIZATION  
**Status:** PASS / READY  

---

## 1. Executive Summary

This audit documents the normalization of Cursor's active skill discovery surface and the native execution acceptance of the `agentcore-project-lifecycle` skill against `D:\github\phase5-disposable-fixture`.

---

## 2. Third-Party Discovery Setting State

- **Cursor Version:** 0.45.11 (win32 x64)
- **Setting Checked:** `cursor/thirdPartyExtensibilityEnabled`
- **Location:** `C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\state.vscdb`
- **Observed Persisted Value:** `false`
- **Confirmation:** The third-party extensibility setting is verified **OFF**.

---

## 3. Skill Catalog Transformation & Quarantine

| Surface | Pre-Phase 5B Count | Post-Phase 5B Action | Post-Phase 5B Count |
|---|---|---|---|
| Shared Catalog (`C:\Users\ynotf\.agents\skills`) | 52 skills | Quarantined to `C:\Users\ynotf\.agents\skills.quarantined-20260724` | 0 active |
| Superpowers Plugin (`C:\Users\ynotf\.cursor\plugins`) | 14 skills | Quarantined / Disabled from active discovery | 0 active |
| Operator Managed Skills (`C:\Users\ynotf\.cursor\skills`) | 0 skills | Deployed `agentcore-project-lifecycle` | 1 skill |
| Built-in Cursor Skills (`C:\Users\ynotf\.cursor\skills-cursor`) | 13 skills (37 files) | Preserved intact (immutable built-in product surface) | 13 built-in skills |

---

## 4. Lifecycle Skill Frontmatter & Hash Audit

- **Canonical Source:** `D:\github\agentcore-control-plane\skills\agentcore-project-lifecycle\SKILL.md`
- **User Live Path:** `C:\Users\ynotf\.cursor\skills\agentcore-project-lifecycle\SKILL.md`
- **Fixture Local Path:** `D:\github\phase5-disposable-fixture\.cursor\skills\agentcore-project-lifecycle\SKILL.md`
- **SHA-256 Hash:** `7C97B389A4123AA0A3E4301BD9CE05F52110C58A210EA324C06074B7F4209B68` (Byte-identical across all 3 locations)
- **Encoding:** UTF-8 without BOM
- **YAML Validation:**
  - `name`: `agentcore-project-lifecycle`
  - `disable-model-invocation`: `false` (not present)
  - `category`: `meta`
  - Context Fabric: explicitly capability-gated and optional.

---

## 5. Native Lifecycle Acceptance Results

Execution against `D:\github\phase5-disposable-fixture`:

1. **Router Activation:** `agentcore_project_router-project_activate` resolved and activated `phase5-disposable-fixture`.
2. **Repository Identity:** Git worktree clean; HEAD `128e863 initial fixture commit`.
3. **Session Management:**
   - Session Key: `phase5-disposable-fixture:cursor:project-lifecycle-native-acceptance`
   - Session ID: `6acf5699-98a8-457b-b951-d89656a4ac35`
   - Open & Close: `ok: true`.
4. **Context & Expansion:** `startup_context` OK; `retrieve_context` OK; `expand_source` OK.
5. **Event Ledger & Idempotency:**
   - Append Event 1: `ok: true` (Idempotency Key: `phase5b-native-acceptance-20260724`).
   - Append Event 2: `idempotent_replay: true` / `ok: true`.
6. **Projections & Handoff:** Projection worker executed; deterministic `build_handoff` generated (`ok: true`).
7. **Context Fabric Boundary:** Verified optional and capability-gated.

---

## 6. Regression Gate Summary

- **Global Rules:** 1 (`agentcore-foundation.mdc`)
- **Operator Skills:** 1 (`agentcore-project-lifecycle`)
- **Built-in Skills:** 13 (reported separately)
- **MCP Config:** 1 (`agentcore-gateway`)
- **Bifrost Health:** 200 OK
- **PostgreSQL 18:** Running & Automatic (`127.0.0.1:55433`)
- **Tools Surface:** 10 memory, 4 project-router, 3 read-only skills-hub, 0 Firebase, 0 Sheets, 0 Swarm.
