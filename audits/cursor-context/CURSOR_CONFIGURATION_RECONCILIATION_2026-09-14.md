# Cursor configuration reconciliation (2026-09-14)

Approval reference: `AUTH-2026-09-14-CURSOR-PROFILE-RECONCILIATION`, based on the operator's request in this task. This is a sanitized file observation, not a fresh Cursor chat or MCP tool-call acceptance test.

## Rules

- Running `Cursor.exe` product version: `3.19.19`.
- Canonical semantics: `contracts/global-agent-policy.yaml`, revision `2026-09-14-cursor-configuration-provenance-v2`. Derived rule: `ide-profiles/cursor/GLOBAL_RULES.md`.
- Machine-local global rule: `C:\Users\ynotf\.cursor\rules\agentcore-foundation.mdc`, SHA-256 `96379E45FC24E89A510389C74ABFE6E4A05DA42CC8F56B75747A18189176CE72`. It equals the generated rule plus the pre-existing NFA appendix; the appendix was preserved during the installer update. Only one active `.mdc` file exists in the home rules directory. An older memory rule has a `.quarantined` suffix.
- Cursor account User Rules in Customize > Rules are account-synced and were not inspected or changed through the UI. Their content and parity are **unverified**. `ide-profiles/cursor/USER_RULES_REPLACEMENT.txt` is a prepared plain-text replacement, not evidence of installation. Project `.cursor/rules/*.mdc` and `AGENTS.md` are separate repository-scoped surfaces.

## MCP and settings

`C:\Users\ynotf\.cursor\mcp.json` SHA-256: `5195A9EB1B4172F331A5E55ECF888EDFC7E0285FB1FC68B79DAC0D9671CD7972`. The sanitized entry inventory is:

| Entry | Observed transport/target | Disabled flag | Classification |
| --- | --- | --- | --- |
| `agentcore-gateway` | `streamable-http` at `http://127.0.0.1:8080/mcp` | absent | Sole AgentCore gateway entry; Authorization is a Windows environment-variable reference, not a stored key. |
| `google-sheets` | `http` at `https://sheetsmcp.googleapis.com/mcp/v1` | absent | Direct external route observed; approval and native auth/tool readiness unverified. |
| `google-drive` | `http` at `https://drivemcp.googleapis.com/mcp/v1` | absent | Direct external route observed; approval and native auth/tool readiness unverified. |
| `dart` | `stdio` via `dart.exe` | `true` | Disabled host-native companion; environment and arguments were not copied. |

The source-controlled `ide-profiles/cursor/MCP_CONFIG_TEMPLATE.json` intentionally contains only `agentcore-gateway`. The two direct Google entries are live observations, not approved AgentCore companion exceptions; no MCP entry was added, removed, restarted, or changed in this task.
Under the current `ide-profiles/cursor/VALIDATION.md` direct-entry gate, this live file **fails configuration acceptance** until those entries receive the required approved exception or are reconciled in a separate authorized live-config task. Documentation of their presence alone is not approval.

`C:\Users\ynotf\AppData\Roaming\Cursor\User\settings.json` SHA-256: `B558D02A9BB7E3A1A430AFD6B46E4C2641C24D71D24438322C61C23E95F3FFEA`. The inspected Cursor-specific preferences are `cursor.composer.queueMessageDefaultBehavior=stop-and-send` and `cursor.composer.usageSummaryDisplay=always`. Other settings and account databases were not copied into Git.

## Validation and limits

The local installer created its final backup and manifest at `E:\AgentCore-Backups\agentcore-control-plane\cursor-global-rule-20260914-172741\` (foundation before SHA-256 `5812C0A6BF78EB425D5460D6F284C866280C8739C8AFE728E3FD7ECCD86F0529`). The protected policy and profile/matrix/README had pre-edit backups at `E:\AgentCore-Backups\agentcore-control-plane\20260914-cursor-profile-reconcile\`.

The protected `contracts/global-agent-policy.yaml` changed from SHA-256 `FC0BC2365ACA4A96D879A698A824FB17A518383B50D2C22EE4A00530634F2A19` to `8C6540757104F6C71BC247587D629F34081616A30D5898CA4B61681212C2AC64` and was re-locked read-only. Renderer parity, authority-lock validation, Bifrost contract validation, 215 contract tests, 16 Cursor installer tests, and a structured profile/matrix/hash cross-check passed.

The foundation matched its regenerated content exactly after install; the NFA appendix matched the backup. `last_validation_date` remains `2026-07-13`, and previous M8 tool-call evidence remains dated `2026-07-16`. A fresh Cursor chat, account User Rules UI inspection, and native MCP acceptance were not performed. No full-current-readiness claim follows from the file snapshot.

Arabold `find_version(cursor, 3.19.19)` returned `3.14.7` as the closest indexed version; the running Cursor `3.19.19` does not have verified exact-version local coverage. Current official Cursor rules documentation was consulted, but that does not satisfy the durable exact-version ingest gate.

Independent authority review returned `ACCEPT` after the validation, account-rule preservation, and `AGENTS.md` path corrections. The reviewer did not approve the two unchanged direct Google MCP entries. The source changes remain uncommitted: this worktree contains substantial inherited dirty state in the governed policy and generated profiles, so staging them now would include unrelated changes. The account User Rules and fresh native MCP acceptance remain separate follow-up work.
