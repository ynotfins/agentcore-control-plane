# Bifrost unsigned MCP identity gap — options analysis (2026-08-02)

## Problem statement

`agentcore-memory` (v0.7.0) supports Ed25519 per-request `device_assertion` envelopes verified in `scripts/agentcore_memory/device_identity.py` and invoked from `server.py` → `verify_tool_identity()`. Enforcement mode is stored in `agentcore.device_identity_policy`:

- **`legacy_compat`** — unsigned calls succeed when migration window is open (maps to enrolled legacy machine/user).
- **`required`** — unsigned calls fail with `device_assertion_required`.

**Certified hook paths** (Cursor `gateway.py`, context-engine native hooks) sign memory tool calls before they reach Bifrost. **Residual gap:** any IDE or agent that calls `agentcore-memory` tools directly through `http://127.0.0.1:8080/mcp` presents only the Bifrost bearer VK. The memory server cannot distinguish *which physical device* originated the call unless the caller supplies a valid `device_assertion`.

Bifrost registry (`contracts/bifrost-upstream-mcp-registry.json`) documents v0.7.0 assertions as backward-compatible schema additions; it does **not** define gateway-level device binding. Changing that is an authority/Bifrost contract matter.

---

## Current code facts

| Component | Behavior |
|-----------|----------|
| `device_identity.py` | `UNPROTECTED_TOOLS = {"memory_status"}` only. All other tools go through `verify_tool_identity()`. |
| `server.py` | Strips `device_assertion` after verification; returns `identity.legacy_compat` on `session_open`. |
| `gateway.py` (Cursor hooks) | Signs all memory tools except `memory_status` via `DeviceIdentityManager.sign_tool_call()`. |
| Bifrost | Authenticates MCP HTTP with VK; forwards tool calls unchanged to stdio `agentcore_memory/server.py`. |
| Registry | Single `agentcore-memory` entry; no second MCP surface; no VK→device mapping. |

---

## Options evaluated

### A) Keep `legacy_compat` until all hosts route writes only through signed hooks *(current)*

| Pros | Cons |
|------|------|
| No Bifrost/registry change | Unsigned direct MCP writes still accepted during migration window |
| Zero authority risk | `required` mode breaks unsigned IDE MCP until every host signs |
| Matches v0.7.0 backward-compat promise | Does not close the direct-MCP bypass |

**Authority:** repo-only (policy toggle via `device_admin.py`).

**Verdict:** Safe default today; insufficient for production-grade device binding while migration window is open.

---

### B) Require assertions on write tools only; allow unsigned reads (`memory_status`, `startup_context`, `retrieve_context`, `expand_source`)

| Pros | Cons |
|------|------|
| Closes unsigned **write** bypass without Bifrost changes | Read tools can still be invoked unsigned (lower risk) |
| Implementable entirely in `device_identity.py` / `server.py` | Slightly diverges from “all tools except memory_status” docstring |
| IDE chat can still cold-start context unsigned | `session_open` unsigned would still need legacy or assertion |
| Aligns with bounded-write classification in registry | Cherry/other hosts must sign writes before enforcement flip |

**Implementation sketch:** extend `UNPROTECTED_TOOLS` or add `READ_ONLY_TOOLS`; in `required` mode, read tools skip assertion; write tools (`session_open`, `append_event`, `propose_fact`, `session_close`, `build_handoff`) require assertion.

**Authority:** repo-only — no Bifrost contract change, no new MCP entry.

**Verdict:** **Safest incremental path that does not require Tony approval.**

---

### C) Bifrost middleware attaching verified VK → device mapping

| Pros | Cons |
|------|------|
| Central binding at gateway | **Changes Bifrost gateway contract** |
| Callers need not embed assertions | Requires VK issuance tied to device enrollment |
| | New trust boundary: Bifrost must verify device proofs or hold mapping table |
| | Touches `render_bifrost_config.py`, registry, possibly `AUTHORITY_LOCK.md` |

**Authority:** **Tony / authority-maintainer approval required** — gateway contract and possibly `contracts/agentcore-gateway-client.json`.

**Verdict:** Production-grade long-term option, but **not implementable without explicit authority**.

**Exact ask for Tony:**

> Approve a Bifrost gateway enhancement that maps each `BIFROST_MCP_VIRTUAL_KEY` to an enrolled `device_id`/`user_key` and injects or validates device identity on upstream `agentcore-memory` tool calls, with registry + renderer updates and a documented rollback. Confirm this does not violate the single-gateway / ten-tool memory surface invariant.

---

### D) Short-lived server-issued session capability token after signed `session_open`

| Pros | Cons |
|------|------|
| Reduces per-call signing overhead | New schema + server state (capability table) |
| Binds subsequent MCP calls to an opened session | Unsigned `session_open` still the bootstrap problem |
| | Token must be carried on every tool call (schema change to all tools) |
| | Replay/expiry semantics add operational complexity |

**Authority:** repo memory-server change (medium); if Bifrost must attach tokens, becomes (C).

**Verdict:** Reasonable future optimization **after** write-path assertions are mandatory; not the first fix.

---

### E) Other patterns from current architecture

1. **Certified-host-only `required` mode** — Enable `required` only on machines where Cursor/Codex/Claude native hooks are installed and enrolled. Unsigned direct MCP fails by design; operators use hooks. Residual: manual MCP debugging needs signed CLI shim.

2. **Context-engine as sole memory writer** — Route all durable writes through context-engine lifecycle (already partially true for Cursor). Memory MCP becomes read-heavy for IDEs. Large behavioral change.

3. **Lease-scoped VK per device** (M6 pattern) — Issue device-scoped Bifrost VKs via capability lease. Combines with (C); requires lease + JIT bridge policy extension.

---

## Residual risk (all options except C)

> After Cursor/Codex/Claude native hooks, certified hosts survive `required` mode for hook-mediated paths. **Direct IDE MCP tool calls bypass hooks** and therefore bypass signing unless the IDE client itself signs (today: only hook `GatewayClient` does).

---

## Recommendation

| Decision | Action |
|----------|--------|
| **Implement now (no Tony)** | **Option B** — extend server-side enforcement so `required` mode mandates assertions on **write** tools while keeping selected **read** tools unsigned (`memory_status` already exempt; add `startup_context`, `retrieve_context`, `expand_source`). Keep `legacy_compat` globally until all certified hosts sign writes in CI/hook proofs. |
| **Defer** | Option D (capability tokens) until write enforcement is stable. |
| **Ask Tony before any work** | **Option C** — Bifrost VK→device middleware. Do **not** modify Bifrost renderers or gateway contract without approval. |
| **Do not rely on alone** | Option A — necessary migration posture, not a terminal security control. |

### Suggested rollout (repo-only)

1. Ship Option B in `device_identity.py` behind unchanged policy modes.
2. Expand hook/native-host proof audits (this file’s companion `CURSOR_DEVICE_PROOF_LIVE_2026-08-02.json` is the template).
3. When Cherry, LangGraph workflow, and context-engine hosts all sign writes, flip policy to `required` (writes enforced, reads still unsigned per B).
4. Open Tony review for Option C only if per-call assertions prove too heavy or cross-host VK binding becomes a hard requirement.

---

## Related evidence

- Live hook + enforcement proof: `audits/CURSOR_DEVICE_PROOF_LIVE_2026-08-02.json`
- Device verification implementation: `scripts/agentcore_memory/device_identity.py`
- Cursor signing client: `scripts/agentcore_cursor/gateway.py`
- Bifrost registry entry: `contracts/bifrost-upstream-mcp-registry.json` → `agentcore-memory` v0.7.0
