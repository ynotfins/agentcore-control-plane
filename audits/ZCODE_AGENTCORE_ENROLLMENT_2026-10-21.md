# ZCode AgentCore Enrollment + Permanent-Layout Acceptance — 2026-10-21

**Client:** ZCode 3.10.1 (Trust Class A; distinct from Zoo-Code/Roo-Code)
**Performed by:** ZCode main agent session (fresh native task), operator-directed
**Authority context:** PROJECT_ANCHOR.md §0/§2/§4, DOC_AUTHORITY.md, contracts/agentcore-gateway-client.json (`zcode`), contracts/agentcore-project-enrollment.json, contracts/install-target-policy.json, contracts/secondary-backup-drive-policy.json, docs/DRIVE_WRITE_BOUNDARY_RULE.md
**Result:** Trust Class A enrollment reconciled and **live-validated**; permanent ZCode layout applied per drive-role policy.

---

## 1. Live MCP configuration (verified, sanitized)

`scripts/agentcore_zcode.signed_memory inspect` against `C:\Users\ynotf\.zcode\cli\config.json`:

- `mcp.servers.agentcore-gateway` → `http://127.0.0.1:18082/mcp`, `enabled: true`, **no Authorization header**, **no `BIFROST_MCP_VIRTUAL_KEY` literal** (`uses_compat_18082: true`, `has_vk_literal: false`).
- Other entries are client-local, non-AgentCore: `claude-context`, `figma` (env-token bridge; no stored secret).
- Process evidence: ZCode runs from `C:\Program Files\ZCode\ZCode.exe` (matches the process-attested proxy allowlist).

## 2. Project enrollment (default-deny honored)

- Added `zcode-workspace` to `contracts/agentcore-project-enrollment.json`: paths `G:\Zcode\.zcode\workspace\default` (legacy trial) and `I:\LocalApps\ZCode\workspace\default` (permanent), prefix `I:\LocalApps\ZCode\workspace`.
- The repo validator refused the first edit (`unapproved_path_prefix_refused`) because the prefix parent was not approved; fixed by adding `I:\LocalApps\ZCode\workspace` to `approved_path_prefix_parents` (operator-directed permanent-layout decision). Timestamped `.bak` kept next to the contract.
- `require_enrolled_path("G:\Zcode\.zcode\workspace\default")` resolves to `project_key: zcode-workspace` (enforcement exercised live).

## 3. Host signer (new, mirrors `agentcore_devin`)

`scripts/agentcore_zcode/` added: `signed_memory.py` + `__main__.py` + `__init__.py`.

- Reuses the Cursor `DeviceIdentityManager` enrollment (device.json + keyring) exactly like `scripts/agentcore_devin/signed_memory.py`; `CLIENT_KEY="zcode"`, `DEFAULT_AGENT_KEY="zcode-builder"`.
- CLI: `sign` / `call` / `inspect`. Host calls use the in-process memory server or `:8080` with the User-scope env VK; `:18082` host use is refused by the same guard as Devin's.
- No private key, VK, or bearer is written into ZCode MCP JSON or Git.

## 4. Signed memory lifecycle — full pass (canonical PG18)

Session `af7043d0-9fea-4ff9-b327-ddc75b98081b`, `session_key zcode-ecosystem-integration-20261021`, identity `device-7ae069c5…`, key `ed25519-ee879fc4…`, **`legacy_compat: false`** (full cryptographic attestation):

| Step | Result | Evidence |
| -- | -- | -- |
| `session_open` | ok | session/project/source-identity IDs returned |
| `startup_context` | ok | `standard-context`, hard limit 131072 |
| `append_event` | ok | event `fd571c5c-f3c0-456c-8257-287ca660c11d` (decision, idempotency key `zcode-ecosystem-integration-20261021-decision-001`, `idempotent_replay: false`) |
| `retrieve_context` | ok | bounded context returned |
| `expand_source` | ok | exact original decision payload expanded |
| `build_handoff` | ok | current-state handoff, milestone M0 |
| `session_close` | ok | session closed cleanly |

Note: `neutral_recall_projection` for the append was `degraded/skipped` (non-blocking; canonical PG18 write succeeded; SwarmRecall plane itself reports healthy in `memory_status`).

Signed in-session note: the ZCode MCP client cannot mint device assertions in-process; the sanctioned pattern (same as Devin) is sign-then-call via the host signer. In-session assertion injection through the native MCP schema is possible but was not demonstrated this session — recorded as follow-up.

## 5. Permanent layout (per PROJECT_ANCHOR §2 + install-target-policy)

| Role | Location |
| -- | -- |
| ZCode app / harness / live IDE config / hooks | `C:\Users\ynotf\.zcode` (C: = live IDE configs, app-owned) |
| ZCode durable app data (workspace scratch, MCP launchers) | `I:\LocalApps\ZCode\` (neutral LocalApps tier) |
| ZCode project work | `D:\github\<repo>` (source tier; e.g. ClawTeam) |
| Docs store | machine-global `F:\AgentCore\runtime\docs-store\arabold` via `arabold-docs` behind the gateway (verified in live Bifrost config; the trial-era `G:\Zcode\docs-store` reference was drift) |
| Local OCR tool | IureOCR v0.6.1 at `I:\LocalApps\IureOCR\app` (third-party local app tier; local Tesseract + pdfium, no network) |
| `G:\Zcode` trial tree | **retired** — G: reverts to its policy role (second backup copy target only, `secondary-backup-drive-policy.json`); physical cleanup left to the operator |

## 6. Outstanding / follow-up

- `fresh_chat_recovery` and `persistence_after_restart` need next-session proof (matrix fields set to `configured_restart_required`).
- In-session signed-call automation (auto device-assertion injection) is a future ZCode-client capability; host-signer pattern is the sanctioned interim.
- `G:\Zcode` legacy tree cleanup pending operator confirmation.
- Upstream IureOCR bug filed 2026-10-21: Windows verbatim `\\?\` path passed to `tesseract --tessdata-dir` yields zero languages (local workaround documented in the ZCode workspace `docs-lock.json`).
