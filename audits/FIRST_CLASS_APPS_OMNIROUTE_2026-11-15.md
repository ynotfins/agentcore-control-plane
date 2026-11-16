# First-class app registration + OmniRoute repair — evidence 2026-11-15

Operator authority: `UNLOCK contracts/global-agent-policy.yaml` (2026-11-15 chat). Operator decision: every
app reaches PostgreSQL only through agentcore-gateway; no direct database MCP for any app.

## OmniRoute (machine state, outside Git)

- Blocker: `npm install -g omniroute` failed because the running server (PID 67296) held native
  `.node` files open (better-sqlite3, keytar, wreq-js); npm had already removed `dist/` and `package.json`.
- Fix: data backup `I:\LocalApps\OmniRoute\backups\data-bak-20261115-1657-preinstall`; watchdog paused;
  server stopped; clean reinstall `omniroute@3.8.53` (published 2026-11-06) with one-time
  `--allow-scripts` for its install scripts (npm 11.19 blocks them by default; npm config unchanged).
- Launcher `I:\LocalApps\OmniRoute\runtime\Launch-OmniRoute.ps1`: `--no-tray --log --no-recovery` ->
  `--tray` (tray mode rejects `--log` and `--no-recovery`). Backup beside the file.
- Watchdog `Watch-OmniRoute.ps1`: relaunch now goes through `conhost.exe --headless`. Backup beside the file.
- Verified: `omniroute health` healthy, version 3.8.53; listener `127.0.0.1:20128` only; tray process
  `tray_windows_release.exe` running; tasks `\AgentCore-OmniRoute` (logon trigger) and
  `\AgentCore-OmniRoute-Watchdog-Poll` enabled. `omniroute autostart` intentionally stays disabled
  (it would start a second server on the same port).
- `omniroute skill list --apps` does not exist in 3.8.53; equivalents are `omniroute config list` and `setup-*`.
- Verified routing (dry run): `sol-kie-heavy` -> KIE `kie/gpt-6-1-sol`, `kie/gpt-6.1-sol` only.

## Focus-steal fix (machine state)

Visibility-only change (no stop, disable, or schedule change). Task XML backups:
`I:\LocalApps\AgentCore\task-backups\focus-fix-20261115-172818\`. Now wrapped in `conhost.exe --headless`:
`\AgentCore\DailyDriftCheck`, `\AgentCore\NFA-Sheets-Sync`, `\AgentCore\SwarmRecallApi`,
`\AgentCore\SwarmRecallMeilisearch`, `\cua-driver-serve`, `\RecoverOS-API`, `\RecoverOS-Meilisearch`,
`\RecoverOS-NAD-Ingest`, `\Windows Tools Weekly PC Health Report`. All other non-Microsoft script tasks
were already headless. Not changed: `Startup\Swarm Stack.cmd` (Swarm-owned; Swarm isolation).

## Repository changes

- `contracts/global-agent-policy.yaml`: Trust Class A adds VSCodium, Zoo Code, OpenCode, Zed, Eigent,
  Reasonix, Cherry Studio, Open Design, OpenHands, OpenMausBot; SwarmClaw excluded; gateway-only DB access.
- `ops/bifrost/Resolve-AgentCoreBuilderCaller.ps1`: :18082 process attestation adds VSCodium.exe,
  Cherry Studio.exe, Open Design.exe, OpenMausBot.exe. Live effect requires merge + Bifrost restart.
- New profiles: `ide-profiles/{vscodium,openhands,openmausbot,open-design}` (all dimensions `unverified`).
- `ide-profiles/zoo-code/vibe-profile/`: `.roomodes`, `.roo/rules*`, `.roo/mcp.json` (gateway only),
  `.rooignore`, `zoo-omniroute-settings.json`, `setup-zoocode-workspace.ps1` (tested against a temp folder).

## Live app inventory (names only)

| App | Gateway entry | OmniRoute |
|---|---|---|
| Zoo Code in Cursor | env-ref `BIFROST_MCP_VK_IDE` :8080 | not set as provider |
| Zoo Code in VSCodium | env-ref :8080 | present |
| VSCodium mcp.json | env-ref :8080 | present |
| Cursor | env-ref :8080 | MCP entry present; models are UI-only |
| OpenCode / ZCode / Zed / Eigent | :18082 attested | present |
| Reasonix | present | not set |
| Open Interpreter | env-ref :8080 | not set |
| OpenMausBot | :8080 entry disabled | OmniRoute MCP present |
| OpenHands | :8080 via host.docker.internal, literal bearer in settings.json | not set (Ollama/OpenRouter) |
| Devin | n/a | not set (Devin uses its own models) |

## Follow-up 2026-11-15 (evening)

- Key rotation: the OpenHands literal bearer equalled Windows User env `BIFROST_MCP_VIRTUAL_KEY` (builder VK,
  `vk-agentcore-builder`). The value had also been copied into chat transcripts and several app backups.
  New value generated and set in User env; Bifrost stopped/started via `ops/bifrost/Stop-/Start-AgentCoreBifrostGateway.ps1`
  (config.db backup `F:\AgentCore\runtime\bifrost\backups\vk-rotate-20261115-184537`). Verified: new key HTTP 200,
  old key HTTP 401 on `http://127.0.0.1:8080/mcp`. Old value scrubbed from OpenHands and Cherry backups written in this task.
- Live `:18082` resolver: same allowlist edit applied to `D:\github\agentcore-control-plane\ops\bifrost\Resolve-AgentCoreBuilderCaller.ps1`
  (uncommitted there; identical to this PR).
- OpenHands: LLM -> OmniRoute `openai/default-deepseek-v4-pro` via `host.docker.internal:20128` (reachability 200 from
  container); gateway bearer updated to the rotated value (OpenHands has no verified env-ref support; value stays in its own
  state file on I:, not Git). Container restarted.
- Reasonix: `[providers.omniroute]`; default `omniroute/default-deepseek-v4-pro`, subagent `omniroute/deepseek-v4.1-flash`.
- Open Interpreter: `[model_providers.omniroute]`; default and `sandboxed` profile -> `default-deepseek-v4-pro`.
- OpenMausBot: `agentcore-gateway` enabled on `:18082` with no headers. Model provider is UI-owned (OpenAI-compatible).
- Cherry Studio: MCP import JSON now `:18082`, no bearer. Live settings are LevelDB/UI-owned.
- Open Design: no file-owned MCP/provider config; it runs local agents that use their own configs.
- Zoo import file (stable copy): `I:\LocalApps\ZooCode\zoo-omniroute-settings.json`; debug mode -> `sol-kie-heavy`.
- Governed docs bumped to OmniRoute 3.8.53 on operator approval (AGENTS.md, CONTEXT_BLOCK.md, DOC_AUTHORITY.md).

## Follow-up 2026-11-15 (night, after PC restart)

- OmniRoute default: mappings `default`, `auto`, `auto/best-coding` -> combo `deepseek-v4.1-flash`; active combo
  switched to `deepseek-v4.1-flash`. Live check: `model=default` answered by `deepseek/deepseek-v4.1-flash-1017` via
  OpenRouter (`x-omniroute-decision: strategy=priority; provider=openrouter`). Explicit `deepseek-v4-pro` still routes to V4 Pro.
- V4 Pro -> V4.1 Flash defaults: Zoo bundle (code/ask/docs/ops), Reasonix CLI workspace, Reasonix desktop/Studio
  (`%APPDATA%\reasonix\config.toml` default + planner), OpenHands, Continue.
- Reasonix desktop/Studio: OmniRoute provider shown (provider_access), `api_key_env = OMNIROUTE_API_KEY` (User env,
  value is the local placeholder); `agentcore-gateway` plugin via `mcp-remote` with env-referenced bearer.
- Open Interpreter: unknown top-level `model_provider = "omniroute"` triggered re-onboarding; reverted top-level to
  OpenRouter V4.1 Flash and added an app profile `agentcore:omniroute-deepseek-v4-1-flash` as `default_profile_id`.

## Per-app virtual keys (2026-11-15, operator request)

- 17 builder-profile virtual keys `vk-agentcore-app-<client>` with values from Windows User env
  `BIFROST_MCP_VK_APP_<CLIENT>` (cursor, codex, devin, antigravity, zcode, minimax-code, open-interpreter-desktop,
  vscodium, zoo-code, opencode, zed, eigent, reasonix, cherry-studio, open-design, openhands, openmausbot).
  Live config.json patched (backup `*.bak-appvk-*`), Bifrost restarted; all 17 keys and the builder key return
  HTTP 200 on `initialize`.
- `:18082` proxy now injects the caller's own app key (by attested client id), falling back to the builder key.
- Env-header clients moved to their own key: Cursor, VSCodium, Zoo Code (Cursor + VSCodium), Reasonix desktop/Studio,
  OpenHands (container env + settings).
- Builder key `BIFROST_MCP_VIRTUAL_KEY` stays for scripts, renderers, and fallback.
- Pre-existing test failures unchanged: `test_builder_compat_proxy.py::test_proxy_denies_untrusted_loopback_but_accepts_existing_bearer`,
  `test_stdio_env_isolation.py::test_agentcore_memory_declarations_cover_its_runtime_source_inventory` (fail on main too).
