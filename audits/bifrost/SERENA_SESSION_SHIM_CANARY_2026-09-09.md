# Serena HTTP Session Shim Acceptance Canary Audit (2026-09-09)

**Authority:** `docs/adr/ADR-2026-09-09-serena-http-session-shim.md`, `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-project-enrollment.json`  
**Test Suites:** `scripts/bifrost/test_serena_session_shim.py`, `scripts/bifrost/test_session_identity.py`  
**Execution Environment:** Python 3.13 (`scripts\.venv\Scripts\python.exe`)  
**Status:** **PASS** (18 tests: 7 identity + 11 shim/canary)

---

## 1. Intent & Scope

Under ADR-2026-09-09, Serena is admitted to Bifrost via a loopback HTTP session shim (`http://127.0.0.1:18090/mcp`) rather than an unsafe shared sticky STDIO connection.

This audit records acceptance evidence for:
1. **Default-deny** project enrollment resolution (no `agentcore-control-plane` fallback).
2. Strict refusal of Swarm roots and markers (`swarm_project_refused`).
3. Immediate synthetic ping interception.
4. MCP protocol compliance (`initialize`, `tools/list` returning 21 tools).
5. Multi-IDE concurrent isolation canary (mocked children for routing isolation).
6. `tools/call` without project headers denied with `PROJECT_NOT_ENROLLED`.

Shared resolver: `scripts/bifrost/session_identity.py`.

---

## 2. Test Execution & Results

```powershell
scripts\.venv\Scripts\python.exe -m unittest scripts.bifrost.test_session_identity scripts.bifrost.test_serena_session_shim -v
```

```text
Ran 18 tests in 1.308s
OK
```

### Key assertions (default-deny repair)

| Test | Assertion | Result |
|---|---|---|
| `test_unknown_key_denied` | Unknown key → `PROJECT_NOT_ENROLLED`, not control-plane | **PASS** |
| `test_empty_identity_denied` | Empty resolve → `PROJECT_NOT_ENROLLED` | **PASS** |
| `test_unenrolled_path_denied` | Unenrolled path → `PROJECT_NOT_ENROLLED` | **PASS** |
| `test_unenrolled_project_denied` | Shim registry: unknown/empty/unenrolled path denied | **PASS** |
| `test_missing_identity_never_falls_back_to_control_plane` | Explicit anti-fallback | **PASS** |
| `test_tools_call_without_project_identity_denied` | HTTP `tools/call` without headers → `-32002` / `PROJECT_NOT_ENROLLED` | **PASS** |
| `test_concurrent_sessions_isolated_and_no_leakage` | Two enrolled sessions route separately; Swarm refused | **PASS** |

---

## 3. Surface Admission Verdict

- **Registry Status:** `active` (HTTP shim, Code Mode)
- **Default-deny:** Fixed 2026-09-09 — prior fallback to `agentcore-control-plane` removed
- **Eager Surface Impact:** 0 Serena tools in eager context when VFS hydrates `servers/serena.pyi`
- **Sticky STDIO:** Permanently retired for shared gateway routing
- **Live VFS caveat:** Cursor `listToolFiles` may omit `serena` until the shim process is running and Bifrost reconnects; do not conflate registry `enabled=true` with live VFS presence
