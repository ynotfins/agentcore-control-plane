# DepWire Global + Codex MCP Setup Evidence — 2026-07-12

## Outcome

- Installed `depwire-cli@1.8.2` globally with npm.
- Verified launcher: `C:\Users\ynotf\AppData\Roaming\npm\depwire.cmd`.
- Set Windows User-scope `DEPWIRE_NO_TELEMETRY=1`.
- Added governed `depwire` stdio definitions to the source generator, supervisor JSON/YAML, registry, master contract, six renderer candidates, validators, routing rules, and documentation.
- Added one reusable prompt for every managed IDE/client: `docs\prompts\depwire-global-setup-prompt.md`.
- Merged DepWire into live Codex `C:\Users\ynotf\.codex\config.toml` and global `C:\Users\ynotf\.codex\AGENTS.md` after timestamped backups.
- Corrected the pre-existing invalid Codex `model_reasoning_effort = "max"` value to the currently supported `xhigh` value so Codex could parse the config and validate MCP registration. The 1,000,000 context window and 850,000 auto-compact limit were preserved.

## Credential conclusion

Inspection of official DepWire CLI `1.8.2` and VS Code extension `1.0.13` established:

- `depwire-cli` MCP has no DepWire API/license environment variable and exposes the 23 local MCP tools without one.
- DepWire Pro uses the VS Code/Cursor extension setting `depwire.licenseKey`, entered through `Depwire: Enter License Key`.
- No Pro license value was read, printed, copied, or stored by this rollout.

## Live rollback

Backup root:

```text
C:\Users\ynotf\.codex\backups\depwire-20260712-012341
```

The backup contains `config.toml`, `AGENTS.md`, `.gitignore_global`, and a hash/rollback manifest. To roll back, close Codex, restore the backed-up files from that directory, restore the previous `DEPWIRE_NO_TELEMETRY` User-variable state if desired, and restart Codex.

Source pre-change copies are under:

```text
D:\github\agentcore-control-plane\artifacts\backups\20260712-011527-depwire-integration
```

## Validation evidence

- `depwire --version`: `1.8.2`.
- `npm list --global depwire-cli --depth=0`: `depwire-cli@1.8.2`.
- `codex mcp list --json`: `depwire` registered and enabled with absolute stdio launcher, args `mcp`, and telemetry-off environment.
- Direct MCP protocol handshake: healthy in 374 ms, protocol `2025-11-25`, 23 tools.
- Required tools present: `connect_repo`, `get_architecture_summary`, `impact_analysis`, `simulate_change`, `security_scan`, `verify_change`.
- Read-only MCP smoke: connected `D:\github\agentcore-control-plane` as a local path and returned `get_architecture_summary` successfully. This exposed that `connect_repo` creates `.depwire/cache.db`; the generated cache was removed after validation and `.depwire/` plus `depwire-output.json` were added to the backed-up global Git excludes file.
- `ops\Test-AgentCoreDepwireIntegration.ps1 -IncludeLiveCodex`: all 29 checks passed.
- Fixed the existing Windows stdio probe process-tree cleanup after reproducing a leaked child `node.exe`; rerun left zero DepWire node processes. The probe now also accepts an `@spec-file`, avoiding Windows PowerShell 5.1 native-argument JSON corruption.
- The exact staged-index snapshot passed the 29-check test under Windows PowerShell 5.1. Its control-plane validator passed JSON, credential scope, live Codex routing/budget, all renderer sets (13/11/5/9/10/1), entrypoint, secret, and read-only checks; its sole remaining failure was the unrelated offline PostgreSQL listener at `127.0.0.1:55432`.
- JSON parsing, PowerShell AST parsing, and Python byte-compilation are included in the final validation pass.

## Scope and restart boundary

- Live rollout completed for Codex only, as requested in this task.
- The source renderers and universal prompt are ready for the remaining IDE/client-specific live merges.
- A full Codex restart and fresh task are still required for callable DepWire tools to appear inside the desktop session; registration and direct protocol/tool usability are already proven.

## Remaining low-risk cleanup

npm left one hidden update-temporary directory because Windows denied deletion of a loaded/native `better_sqlite3.node` file during package cleanup. The governed install and launcher are healthy. Do not force-delete it while a process may hold the native module; remove it after a reboot or with an elevated ownership-aware cleanup if it remains.
