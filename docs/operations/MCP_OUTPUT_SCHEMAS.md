# MCP Output Schemas — agentcore-gateway

**Status:** implemented in source; requires one operator render + Bifrost restart to go live.
**Authority:** `PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `BLUEPRINT.md` → `contracts/bifrost-upstream-mcp-registry.json`
**Spec:** MCP 2025-06-18+ — `tool.outputSchema` describes `CallToolResult.structuredContent`. It does **not** describe the human-readable `content[]` blocks, which are always preserved.

---

## 1. Why this exists

ChatGPT (and other MCP clients) report `OUTPUT SCHEMA RECOMMENDED` for every tool whose
definition has no `outputSchema`. Bifrost is a **passthrough** gateway: it forwards each
upstream's `tools/list` verbatim and does not synthesize schemas. Most approved upstreams
predate MCP structured output, so nothing in the surface advertised one.

The only architecture-preserving injection point is the upstream **stdio launch** itself.
No new MCP route, no second gateway front door, no new tool.

```text
IDE / ChatGPT
  -> agentcore-gateway (Bifrost, http://127.0.0.1:8080/mcp)   [unchanged]
       -> python -u mcp_output_schema_adapter.py --server <id> -- <original upstream command>
            -> upstream MCP server                            [unchanged]
```

---

## 2. Source of truth

| Artifact | Role |
| --- | --- |
| `schemas/tools/_shared/mcp-output-envelope.schema.json` | Canonical envelope + per-family `data` hint shapes. Edit this to change the contract. |
| `contracts/mcp-tool-output-schemas.json` | Binds each registry server (and specific tools) to a profile/family, and declares its adapter mode. |
| `contracts/schemas/mcp-tool-output-schemas.schema.json` | JSON Schema for the binding contract. Update **before** the contract. |
| `contracts/bifrost-upstream-mcp-registry.json` → `output_schema_adapter` | Renderer wiring: interpreter, normalizer script, contract path, master on/off switch. |

Everything advertised in `tools/list` is derived from these files. No hand-written per-tool
output schemas, no generated artifact is the source of truth.

### Envelope

```jsonc
{
  "success": true,
  "status": "ok",              // ok | partial | error
  "summary": "…",              // short, secret-scrubbed, never a raw dump
  "data": { },                 // upstream payload (family hints are advisory, extra keys allowed)
  "evidence": [],              // { type, id?, path?, url?, label?, hash? }
  "warnings": [],
  "errors": [],                // { code, message, retryable }
  "next_actions": [],
  "meta": { "tool": "…", "server": "…", "schema_version": "1.0.0", "redacted": false }
}
```

`data` is deliberately permissive (`additionalProperties: true`, no required keys) so a
conforming upstream payload can never fail validation against the advertised schema.

### Adapter modes

| Mode | Meaning |
| --- | --- |
| `stdio_envelope` | Renderer wraps the stdio launch with the normalizer. Produces `outputSchema` + `structuredContent`. |
| `upstream_native` | Upstream already advertises `outputSchema` and emits conforming `structuredContent`. Reserved; nothing uses it today. |
| `unsupported` | No normalization path (http/sse upstreams). Must stay out of every `capability_profiles[*].allowed_server_ids`; the validator enforces this. |

---

## 3. Runtime behaviour

`scripts/bifrost/mcp_output_schema_adapter.py` is a byte-faithful JSON-RPC relay with two
additive transforms:

* **`tools/list` result** — any tool without an `outputSchema` gets the envelope schema for
  its contract-declared family. An upstream-supplied `outputSchema` is **never** overwritten.
* **`tools/call` result** — any result without a conforming `structuredContent` gets one.
  Rules: an existing `structuredContent` is preserved verbatim under `data`; a JSON-in-text
  result is parsed into `data` (bounded by `max_structured_bytes`); a prose result keeps its
  text and gets `data: null`. `content[]` and `isError` are never modified. Re-normalizing an
  already-normalized result is a no-op.
* **Fail open** — any load/parse/transform problem degrades to raw passthrough, so a schema
  bug can never remove the gateway tool surface.
* **Redaction** — `summary` is scrubbed for `sk-…`, `gh*_…`, `Bearer …`, and
  `api_key/password/secret/token = …` patterns; `meta.redacted` records that it happened.

Direct-stdio consumers (acceptance scripts, `probes/probe_stdio.py`, PowerShell M-series
tests) are unaffected: the AgentCore memory and project-router servers were **not** modified,
so their native `structuredContent` shape is unchanged when invoked outside the gateway.

---

## 4. Operator procedure (must be run on the Bifrost host)

```powershell
cd D:\github\agentcore-control-plane

# 1. Offline proofs (no gateway needed)
python scripts\bifrost\mcp_output_schema_adapter.py --self-test
python scripts\bifrost\validate_output_schemas.py --skip-rendered

# 2. Re-render the Bifrost config from source (writes runtime + sanitized copies)
python scripts\bifrost\render_bifrost_config.py

# 3. Full gate, including generated-artifact drift
python scripts\bifrost\validate_output_schemas.py
python scripts\bifrost\validate_contracts.py
python scripts\bifrost\test_contracts.py

# 4. Restart Bifrost, then prove it live
#    (BIFROST_MCP_VIRTUAL_KEY must be resolvable in the shell environment)
python scripts\bifrost\validate_output_schemas.py --probe-gateway
```

Step 4 is the only step that proves `MissingOutputSchema == 0` on the **live** surface: it
performs MCP `initialize` + `tools/list` against `http://127.0.0.1:8080/mcp` and counts tools
whose definition has no `outputSchema`. Steps 1–3 prove the contract, the emitted schemas, and
the rendered launch commands only.

Expected render output includes a line like:

```text
Output-schema normalizer wrapped 12 stdio upstream(s): agentcore-memory, agentcore-project-router, …
```

---

## 5. Rollback

Any one of these restores the previous behaviour (and re-introduces `MissingOutputSchema`,
which the validator will then report):

```powershell
# Preferred: flip the contract switch, re-render, restart Bifrost
#   contracts\bifrost-upstream-mcp-registry.json -> output_schema_adapter.enabled = false
python scripts\bifrost\render_bifrost_config.py

# One-off render without the normalizer
python scripts\bifrost\render_bifrost_config.py --no-output-adapter
```

Per-server rollback: set that server's `adapter` to `unsupported` in
`contracts/mcp-tool-output-schemas.json` and re-render. The server keeps working; only its
`outputSchema` and `structuredContent` injection stop.

---

## 6. Size budget

`defaults.detail` in the binding contract controls how much schema detail is advertised:

| `detail` | Per tool | Notes |
| --- | --- | --- |
| `compact` (default) | ~1.5 KB | Descriptions stripped; family `data` hints and evidence/error/meta shapes kept. |
| `minimal` | ~0.5 KB | Also collapses evidence/error/meta shapes and `data` hints. `structuredContent` still validates. |
| `full` | largest | Keeps descriptions. Review/debug only. |

Switch to `minimal` if client context cost matters more than per-tool schema detail, then
re-render. `max_output_schema_bytes` is the validator ceiling for a single advertised schema.

Note that structured output intentionally duplicates the payload: MCP requires the
human-readable `content[]` block to remain alongside `structuredContent`.

---

## 7. Known gaps

* **http/sse upstreams cannot be wrapped.** `artiforge`, `depwire-cloud`, `openrouter`, and
  `google-sheets-mcp` are `adapter: unsupported`. None is currently enabled *and* present in a
  capability profile, so none contributes to `MissingOutputSchema`. If one is ever activated
  for a profile, the validator fails until an http-side contract exists.
* **Tool-granular offline accounting is only possible for explicit allowlists.** Wildcard
  (`permitted_tools: ["*"]`) servers are counted at server granularity offline; the live
  `--probe-gateway` run is what proves coverage tool-by-tool.
* **Windows process cost.** Each wrapped stdio upstream now runs one extra Python relay
  process. If a specific upstream misbehaves under the relay, set its `adapter` to
  `unsupported`, re-render, and file the exception here.
