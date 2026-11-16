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
