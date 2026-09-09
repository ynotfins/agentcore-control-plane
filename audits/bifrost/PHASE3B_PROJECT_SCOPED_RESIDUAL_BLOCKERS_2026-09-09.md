# Phase 3b — Project-Scoped Residual Blockers (2026-09-09)

**Authority:** `contracts/bifrost-upstream-mcp-registry.json`, `contracts/agentcore-project-enrollment.json`, `docs/adr/ADR-2026-09-09-serena-http-session-shim.md`, `scripts/bifrost/session_identity.py`  
**AUTH:** `AUTH-2026-09-09-BIFROST-TOOL-SURFACE`  
**Decision:** Keep siblings dormant. Do **not** enable shared Bifrost clients for identity-blocked servers.

---

## 1. Shared identity primitive (delivered)

`scripts/bifrost/session_identity.py` provides enrollment-bound resolution used by the Serena HTTP shim:

| Rule | Behavior |
| --- | --- |
| Default-deny | Missing key/path → `PROJECT_NOT_ENROLLED` |
| No fallback | Never resolves to `agentcore-control-plane` by default |
| Swarm refuse | `foreign_roots` / `foreign_markers` → `swarm_project_refused` |
| Header binding | `x-agentcore-project`, session bind map, absolute enrolled paths only |

Serena may reuse this module. Sibling servers must not be flipped `enabled=true` until each has an HTTP (or equivalent) adapter that consumes the same identity contract.

---

## 2. Sibling residual blockers

| Canonical ID | Registry status | Why blocked on shared Bifrost | Allowed near-term path |
| --- | --- | --- | --- |
| `filesystem` | `dormant_project_scoped` / `enabled=false` | Needs exact enrolled root per session; global FS is forbidden | Host-native project filesystem |
| `depwire` | `dormant_project_scoped` / `enabled=false` | STDIO sticky; no per-request cwd | Host-owned `depwire mcp` with explicit project cwd |
| `tentra` | `dormant_project_scoped` / `enabled=false` | Project index requires explicit project root | Governed explicit-project local workflow |
| `context-fabric` | `dormant_project_scoped` / `enabled=false` | Tools lack caller/project identity on shared gateway | Repo-local hook/CLI only |

**Non-goals this phase:** do not enable `github-mcp`, do not build FS/depwire/tentra/context-fabric HTTP shims, do not use `active-project.json` as a security boundary.

---

## 3. Admission gate for any future sibling shim

Before `enabled=true` for a sibling:

1. Named `tools/list` inventory (no new wildcards).
2. `session_identity` default-deny + Swarm refuse tests.
3. Concurrent two-project isolation canary (mocked children insufficient for live spawn claims).
4. Code Mode (`is_code_mode_client=true`) unless tool count ≤ ~3 and every-turn critical.
5. Render → validate → gateway acceptance under Cursor Bifrost ownership.

---

## 4. Verdict

Phase 3b complete as **residual-blocker documentation + shared identity extraction**. Sibling servers remain `enabled=false`.
