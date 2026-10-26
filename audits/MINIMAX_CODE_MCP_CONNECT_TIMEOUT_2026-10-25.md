# MiniMax Code — agentcore-gateway never binds in agent sessions (2000 ms discovery cap)

**Date:** 2026-10-25
**Product:** MiniMax Code `3.1.4` (observed User-Agent `MiniMaxAgent/3.1.4`; `ide-profiles/minimax/IDE_PROFILE.yaml` still records `3.0.65.122` — stale)
**Active data root:** `C:\Users\ynotf\.minimax`
**Approval:** `AUTH-2026-10-25-MINIMAX-MCP-TIMEOUT-MS` (operator-approved in session 2026-10-25)
**Capability:** `authority_maintainer`
**Rollback set:** `artifacts/rollback/AUTH-2026-10-25-MINIMAX-MCP-TIMEOUT-MS/` (gitignored — local only)

> This record was rewritten on 2026-10-25 after independent review overturned the first
> root-cause hypothesis. The corrected analysis is below; the earlier hypothesis is quoted
> only where it explains a superseded change.

---

## Verdict

| Layer | State |
| --- | --- |
| Gateway reachability (`:18082` → `:8080` → PG18 `:55433`) | **Healthy** — full MCP session (initialize → initialized → tools/list, 29 tools, 35 KB) measured at **103 ms** |
| Gateway tool catalog | **29 tools** — `agentcore_memory-*` ×10, `arabold_docs-*` ×10, `sequential_thinking-sequentialthinking`, `agentcore_capability_catalog-*` ×2, `context7-*` ×2, Code Mode ×4 |
| Agent-session tool binding | **Still broken — blocked product-side** |
| Root cause | **A hard 2000 ms CAP on the agent-turn discovery connect budget**, plus a ~3.5 s proxy cold connect. No MCP `timeout` value can exceed the cap. |
| Repo-side durable fix | **Landed** — the MiniMax enrollment now targets the *effective* config file, carries the correct millisecond timeout, re-asserts it on every reconcile, and the cap is recorded so it is not re-litigated |

---

## Symptom

Every agent turn begins with a `tool_catalog_build` stage that connects to the gateway and aborts:

```text
[18:53:02.414] Connecting MCP server {"serverName":"agentcore-gateway","transportType":"http","timeoutMs":2000,"connectionKey":["agentcore-gateway",null]}
[18:53:04.421] Failed to connect MCP server {"serverName":"agentcore-gateway","error":"MCP error -32001: AbortError: This operation was aborted","durationMs":2007}
[18:53:04.434] tool_catalog_build completed
```

`tool_catalog_build` then completes **with no `agentcore-gateway` tools**, so `agentcore_memory-*`, `arabold_docs-*` and `sequential_thinking-*` are never bound into the session. The pattern is unbroken: 26 identical failures from 2026-10-22 16:28 to 2026-10-25 (18:00, 18:53, **19:56 — after the live config was corrected** — and 20:10).

## Root cause (verified against the shipped bundle)

MiniMax Code's agent-turn tool discovery (`listToolsForTurn`, `app.asar` → `@mavis/local-runtime`) computes:

```js
const turnDiscoveryTimeoutMs = this.options.turnDiscoveryTimeoutMs ?? 2_000;
const timeoutMs = Math.min(configuredTimeout(config), discoveryTimeoutMs);
```

- `turnDiscoveryTimeoutMs` has exactly 4 references in the 352 MB bundle, all at this one site, and is **never assigned**. The effective HTTP discovery budget is therefore **always 2000 ms**.
- `Math.min` is a **cap, not a floor**. `configuredTimeout()` returns the raw millisecond value, `MCP_DEFAULTS.timeout = 120_000` ("Per-call timeout in ms"), and `normalizeServerConfig` copies `timeout` verbatim. There is **no 2000 ms floor anywhere**.
- Consequently `timeout: 300000` still yields `timeoutMs: 2000` on the agent-turn path. The settings-panel *test* path uses `configuredTimeout(config)` uncapped, which is why it connected with `timeoutMs=300000` in 3522 ms at 18:31 and why the two paths disagreed.
- The cap covers the **entire** discovery sequence, not one request: `withConfiguredConnectionTimeout(operation, timeoutMs, onTimeout)` races the whole `pool.listTools(...)` (overrides → connect → initialize → initialized → tools/list) against a single 2000 ms timer and aborts the controller.
- There is **no override**: `turnDiscoveryTimeoutMs` is never assigned (`initializeMcpService` constructs `new LocalMcpService(() => options.dataDir, { nowMs?, connectionPool?, builtinMatrix })`), there is no env var (`MCODE_MCP_STDIO_DISCOVERY_TIMEOUT_MS` is stdio-only), no settings key and no CLI flag.
- The effective MCP config file is `C:\Users\ynotf\.minimax\mcp.json` (`LocalMcpService.filePath()` → `join(dataDir,'mcp.json')`). The only bundle reference to `mcp\mcp.json` is `readConfiguredMcpServerNames`, which only hides legacy proxy skill names — it is **not** a server-config source. The root file already carried `timeout: 300000` (mtime 2026-10-22 16:12), so the `timeout: 300` found in the legacy file was never the cause of the agent-turn failure.

**Binding constraint:** the 2000 ms cap sits on top of a proxy cold connect that costs ~3.5 s.

### Latency budget (measured 2026-10-25)

| Stage | Measured |
| --- | --- |
| Bifrost `:8080` — full session (initialize → initialized → `tools/list`, 29 tools, 34 985 B) | **73 ms cold**, 2.7 ms warm |
| Proxy — `pwsh` cold start | 194 ms |
| Proxy — `Get-CimInstance Win32_Process -Filter "ProcessId = N"` (one filtered query) | **2811 ms** |
| Proxy — `Resolve-AgentCoreBuilderCaller.ps1` early-exit path | 414 ms |
| Observed cold connect through `:18082` (settings panel, 18:31) | **3522 ms** |

The gateway is ~50× faster than the 2 s budget. **The whole gap is proxy attestation**: `ops/bifrost/Resolve-AgentCoreBuilderCaller.ps1:128` walks the process ancestry with one WMI/CIM query **per ancestor level**, and `ops/bifrost/agentcore-builder-compat-proxy.cjs:51-54` spawns that resolver **per connection** (cached per socket only). `194 ms + 2811 ms ≈ the measured 3522 ms`.

## Durable repo remediation (landed in this change)

| File | Before SHA256 | After SHA256 | Change |
| --- | --- | --- | --- |
| `contracts/agentcore-gateway-client.json` | `BAF5296C…B2CC` | `6E190C17…C5EC` | `config_path` → the effective `…\.minimax\mcp.json`; legacy path added as `alternate_config_paths`; `connect_timeout_ms: 300000`; three notes recording the effective file, the millisecond unit, and the 2000 ms cap |
| `contracts/schemas/agentcore-gateway-client.schema.json` | `1EF55E57…F6F6D` | `D92BD369…3D7` | `client_hint.connect_timeout_ms` (integer 1000–3600000); required because `client_hint` is `additionalProperties: false` |
| `renderers/gateway-clients/minimax.json` | `5420ACF4…A925` | `88A7CA79…15B` | `timeout: 300000`, `_agentcore.timeout_unit: "milliseconds"`, corrected note (cap, not floor) |
| `ide-profiles/minimax/MCP_CONFIG_TEMPLATE.json` | `6DB725A7…498A` | `C5397ABA…B43CD` | `timeout: 300000`, `_template_note` corrected |
| `ops/bifrost/Reconcile-AgentCoreTrustAClients.ps1` | `6966B46C…9779` | `1A6CB8AD…6E8` | minimax target changed to `C:\Users\ynotf\.minimax\mcp.json`; branch requires only `agentcore-gateway` (matrix/cu/trash are app builtins), sets `url`, `timeout: 300000`, `enabled`, removes `headers` |
| `scripts/bifrost/test_contracts.py` | `5E168661…495F` | `7712EF70…D6C7` | six regression checks (renderer, template, contract agreement, effective config path, reconciler value compared **numerically**) |
| `scripts/bifrost/test_trust_a_client_reconcile.py` | *(was untracked)* | `A7D4489D…204D` | behavioral assertions (url/timeout/enabled/companion preservation) + a new test for the effective root-file shape |
| `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` | — | `C62A8109…F57F` | MiniMax canonical block + matrix row corrected to the effective path and the real mechanism |
| `ide-profiles/minimax/IDE_PROFILE.yaml` | — | `A3529773…F408` | `live_mcp_config_target` → effective file; `installed_version` → `3.1.6.192`; `last_validation_date` → `2026-10-25`; new known-limitation + audit evidence |
| `ide-profiles/minimax/GLOBAL_RULES.md` | — | `578C7E87…ECEB` | regenerated from `IDE_PROFILE.yaml` via `scripts/render_ide_rules.py` (no hand edit) |
| `audits/MINIMAX_CODE_MCP_CONNECT_TIMEOUT_2026-10-25.md` | *(new)* | — | this record |

The contract is `governed_mutable` (`contracts/authority-lock.yaml`): edited under `authority_maintainer` + the AUTH id above, ReadOnly attribute cleared for the write and restored, byte-exact rollback set captured, all three required validators run, independent review completed.

### Live client state

`C:\Users\ynotf\.minimax\mcp.json` (effective, SHA256 `7C9BA72B…B9B0F`) is already compliant:

```json
{"type":"streamable-http","transport":"streamable-http","url":"http://127.0.0.1:18082/mcp","enabled":true,"timeout":300000}
```

The legacy `C:\Users\ynotf\.minimax\mcp\mcp.json` was also corrected (`timeout` 300 → 300000, backup `mcp.json.backup-20261025-1902`, SHA256 `FEB884B7…2732`). Neither live file needs further change for the timeout; the blocker is the product cap.

## Verification

| Check | Result |
| --- | --- |
| `python scripts/validate_authority_lock.py` | PASS |
| `python scripts/bifrost/validate_contracts.py` | PASS (schema-valid with the new field) |
| `python scripts/validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md` | PASS |
| `python scripts/bifrost/test_contracts.py` | PASS — **236 checks** (was 231) |
| `pytest scripts/bifrost/test_trust_a_client_reconcile.py` | PASS — **8 tests** |
| `python scripts/render_ide_rules.py --check` | PASS |
| Mutation — renderer reverted to `timeout: 300` | **2 checks FAIL**; PASS again after restore |
| Mutation — reconciler changed to `$gateway.timeout = 3000000` | **1 check FAIL** (the substring-match false negative found by independent review is fixed); PASS again after restore |
| Gateway `tools/list` via `:8080` | 29 tools; all three required families present |
| `agentcore_memory-memory_status` | `ok`, server `0.9.1`, `postgres_agent_core.reachable = true`, `127.0.0.1:55433`, migrations `m2.001 → m8.002` |

The `:18082` proxy correctly refuses non-approved callers (`403 caller identity denied`); discovery used the keyed `:8080` route with `BIFROST_MCP_VIRTUAL_KEY` from the Windows User environment. The key value was never printed, written, or committed.

## Independent review — findings and dispositions

An independent reviewer (read-only, `verifier`) overturned the first root-cause hypothesis. Dispositions:

| Finding | Severity | Disposition |
| --- | --- | --- |
| The 2000 ms value is a **cap**, not a floor; `turnDiscoveryTimeoutMs` is never assigned | blocker | **Accepted** — analysis and all affected notes corrected; recorded in contract, renderer, template and docs |
| The effective config file is the root `mcp.json`, not `mcp\mcp.json` | blocker | **Accepted** — `config_path` corrected, legacy path demoted to `alternate_config_paths`, reconciler retargeted |
| `ops:` check substring-match false negative (`3000000` passed) | major | **Fixed** — now parsed with `re.search` and compared numerically; mutation-tested |
| No coverage for companion-server or `type`/`transport` survival | major | **Fixed** — companion preservation and the effective root-file shape are now asserted |
| `IDE_CAPABILITY_MATRIX.yaml` legacy_m8_notes and `docs/MCP_SERVER_CONFIGURATION_REFERENCE.md` are stale | minor | **Open, out of scope** — `legacy_`-prefixed history and the legacy-renderer retirement are separate operator work |
| Rollback set lacked the pre-change reconcile test and is gitignored | minor | **Accepted** — rollback is a local runtime artifact by repo policy; the audit record and AUTH id are committed so the change is traceable |

## Remaining blocker and ranked remedies

The agent-session bind stays broken until the **whole discovery sequence fits inside 2000 ms**. Ranked by feasibility:

1. **Cut the proxy attestation off WMI (in-repo, bounded, recommended).** Replace the per-level `Get-CimInstance Win32_Process` ancestry walk in `ops/bifrost/Resolve-AgentCoreBuilderCaller.ps1:128` with a native `CreateToolhelp32Snapshot` parent-chain lookup, and cache the verdict per client PID + process start time in the proxy (which already holds a per-socket `socketIdentities` WeakMap). That removes the measured 2811 ms and drops the proxy connect to roughly 250–400 ms — inside the 2 s budget — while keeping the process-attested model intact. It needs a proxy restart to take effect, which is an operator-gated service action.
2. **Do not route MiniMax at `:8080`.** MCP headers are copied raw (`normalizeServerMetadata` → `readStringRecord(config['headers'])`); `resolveHeaders()` is only used for model-provider headers, and `${env:VAR}` is not even a valid template for the MCP path (`ENV_VAR_NAME_RE = /^[A-Za-z_][A-Za-z0-9_]*$/` — the colon makes it a literal). Embedding a key would materialise a secret in live JSON, which the Trust Class A policy forbids. The contract's `supports_env_headers: false` is **correct** and must not be "fixed".
3. **Raise the product's discovery budget (vendor change).** `turnDiscoveryTimeoutMs` exists as an option and is simply never assigned; wiring it to a setting or env var would lift the cap. Worth filing upstream — and needed for headroom even after (1) lands.

## Rollback

```powershell
Copy-Item 'artifacts\rollback\AUTH-2026-10-25-MINIMAX-MCP-TIMEOUT-MS\contracts_agentcore-gateway-client.json' `
          'contracts\agentcore-gateway-client.json' -Force
# …and the sibling files in the same rollback directory
attrib +R contracts\agentcore-gateway-client.json
```

## Residual / out of scope

- `ide-profiles/minimax/IDE_PROFILE.yaml` is corrected (effective config path, installed build `3.1.6.192`, validation date, the 2000 ms cap limitation, and this audit as evidence). `ide-profiles/IDE_CAPABILITY_MATRIX.yaml` still records the 2026-07-22 enrollment (`last_validated: 2026-09-08`, `installed_version: 3.0.65.122`, and a `legacy_m8_notes` entry with `timeout=300` / `:8080` / a materialised bearer). The matrix is a re-baselined operator record, not part of this change.
- `MASTER_CONFIG_AND_PROMPT.md:324` still states a single "Timeout: 300 seconds" for every client. That file is `governed_mutable` and carries unrelated in-flight edits; the correction is persisted as `governed-doc-drift-2026-10-25-minimax-mcp-timeout-ms` in `docs/drift-ledger.md` for operator authorisation rather than applied here.
- `docs/MCP_SERVER_CONFIGURATION_REFERENCE.md:32,43,80,445` still names the legacy `renderers/minimax.mcp.json` (a 10-server direct-MCP list with no `agentcore-gateway` entry) as MiniMax's source of truth. Correcting it requires the legacy-renderer retirement, which is entangled with `contracts/master-mcp-server-config.json` and `validators/validate-control-plane.ps1` — separate operator work.
- The rollback set has no pre-change copy of `scripts/bifrost/test_trust_a_client_reconcile.py`: that file was untracked when this change began. It is tracked after this commit, so its prior content is recoverable from git history.
- Other Trust Class A clients (`cursor`, `claude-code`, `devin`, `eigent`, `open-interpreter`) keep `timeout: 300` because their hosts read that field in seconds. Do not blanket-change them.
