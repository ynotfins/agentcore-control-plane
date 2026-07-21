# Cherry Studio ↔ AgentCore Gateway Operations

**Status:** Live-aligned 2026-07-20 (runtime repaired same night — see `audits/CHERRY_RUNTIME_FAILURE_2026-07-20.md`)  
**Cherry version:** 1.9.12 (official **x64** setup; per-user install)  
**Install path:** `%LOCALAPPDATA%\Programs\Cherry Studio\Cherry Studio.exe`  
**Live data:** `%APPDATA%\CherryStudio`  
**Gateway:** `agentcore-gateway` → `http://127.0.0.1:8080/mcp`  
**Capability profile:** `builder` (`BIFROST_MCP_VIRTUAL_KEY`)  
**Client identity:** `client_key=cherry-studio`, `agent_key=cherry-studio-assistant`  
**Agent model:** `deepseek:deepseek-v4-pro` (must be a live chat model with key — not empty CherryIN)

## Install / enrollment

1. Fully quit Cherry Studio (no `lockfile`, no `Cherry Studio.exe`).
2. Confirm `BIFROST_MCP_VIRTUAL_KEY` is set in Windows User env (never print the value).
3. Confirm Bifrost health: `GET http://127.0.0.1:8080/health`.
4. Run:

```powershell
python scripts/cherry/enroll_agentcore_gateway.py --apply
python scripts/cherry/configure_agentcore_agent.py --apply
python scripts/cherry/validate_cherry_studio.py
```

5. Restart Cherry Studio.
6. Open **AgentCore Workspace Agent**. MCP Tools should list tools from `agentcore-gateway` only.

Enrollment materializes the bearer into Cherry Local Storage because Cherry does **not** expand `${env:}`. The sanitized renderer keeps the placeholder:

- `renderers/gateway-clients/cherry-studio.json`
- `contracts/agentcore-gateway-client.json` → `client_render_hints.cherry-studio`

## Agent setup

- Agent id: `agentcore-workspace-agent`
- Display name: `AgentCore Workspace Agent`
- MCP mount: `["agentcore-gateway"]` only
- Prompt: `docs/prompts/cherry-agentcore-workspace-agent.md` (must match `agents.db` instructions)
- Skills: approved hash-pinned set from `audits/CHERRY_STUDIO_SKILLS_AUDIT_2026-07-19.md` (excludes `find-skills`)
- Workspace: `%APPDATA%\CherryStudio\Data\Agents\agentcore-workspace`
- `soul_enabled=false`, scheduler/heartbeat off; permission_mode `default`

Do not create duplicate Agents on re-run; configure script upserts by id.

## Prompt installation

Source of truth: `docs/prompts/cherry-agentcore-workspace-agent.md`  
Installed by: `scripts/cherry/configure_agentcore_agent.py`

## Model-provider separation

- OpenRouter **API/model provider** records are independent of OpenRouter **MCP**.
- Never point an OpenAI-compatible provider at `http://127.0.0.1:8080/mcp`.
- OpenRouter MCP remains dormant behind Bifrost leases (`docs/operations/OPENROUTER_MCP.md`).

## Memory policy

| Surface | Policy |
| --- | --- |
| AgentCore `agentcore-memory` via gateway | Canonical |
| Cherry `globalMemoryEnabled` | **OFF** |
| Built-in `@cherry/*` inMemory MCP | Inactive / not used as AgentCore memory |
| Knowledge bases | Do not create as AgentCore project/user memory |
| Topics / chat history / traces | App-owned ephemeral; not canonical |

Path:

```text
Cherry Studio -> agentcore-gateway -> agentcore-memory -> PostgreSQL 18 (127.0.0.1:55433)
```

## Validation

```powershell
python scripts/cherry/validate_cherry_studio.py
python scripts/cherry/validate_cherry_memory_lifecycle.py
python scripts/bifrost/validate_contracts.py
```

Lifecycle evidence: `audits/CHERRY_MEMORY_LIFECYCLE_2026-07-20.json`  
Enrollment evidence: `audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md`

Validators fail on: wrong URL, duplicate gateway, direct upstream MCP, Swarm MCP, 8081 shim, Global Memory on, secrets in source-controlled renderers.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Empty `mcp.servers` | Quit Cherry fully; re-run enroll `--apply` |
| `${env:}` stored literally | Cherry cannot expand env; use enroll materialization |
| POST `/register` 405 / OAuth loop | Do not add 8081 shim; fix enrollment URL/auth |
| Tools missing in UI | Confirm gateway `isActive=true`; restart; open AgentCore Workspace Agent |
| Session tools fail | Use `context_profile=standard-context`; activate project first |
| `registry.node is not a valid Win32 application` | Wrong arch package. Reinstall official **x64** setup; verify PE `0x8664` on exe and `registry.node`. Never patch asar. See `audits/CHERRY_RUNTIME_FAILURE_2026-07-20.md` |
| Home `toLowerCase` / blank error banner | Assistant topics missing `model`. Quit Cherry; run `node scripts/cherry/repair_cherry_assistant_models.js --repair --confirm` |
| Agent cannot chat / CherryIN empty | Point Agent at an enabled provider+model with key (e.g. `deepseek:deepseek-v4-pro`) |

## Backup

Protected backups live outside Git under `E:\AgentCore-Backups\`:

- Full pre-task: `cherry-pre-alignment-*`
- Enroll snapshots: `cherry-enroll-*`
- Runtime repair: `cherry-runtime-repair-*`, `cherry-installers-*`, `cherry-assistant-model-repair-*`

Each includes SHA-256 manifests where generated. Treat LevelDB/agents.db backups as **secret-bearing**.

## Rollback

```powershell
# Prove backup exists (no restore)
python scripts/cherry/rollback_cherry_alignment.py --latest-pre-alignment --prove-only

# Restore (Cherry must be quit)
python scripts/cherry/rollback_cherry_alignment.py --latest-pre-alignment --apply
```

Rollback restores Cherry app data/config/MCP/Agent/Global Memory/Developer Mode preferences from the backup. It does **not** modify Bifrost, PostgreSQL, other IDEs, Swarm, or canonical AgentCore memory.

## Upgrade / revalidation

After Cherry upgrades:

1. Quit Cherry.
2. Backup AppData to `E:\AgentCore-Backups\`.
3. Re-run enroll + configure + validate scripts.
4. Confirm agent prompt still matches `docs/prompts/cherry-agentcore-workspace-agent.md`.
5. Re-run memory lifecycle validator.
6. Update `audits/CHERRY_GATEWAY_ENROLLMENT_*.md` with status fields (do not collapse into one vague “working”).

## Call Trace / Developer Mode

Developer Mode / Call Trace can expose MCP I/O. Use only for temporary validation, keep sanitized evidence, and restore the prior preference (`config.json` → `enableDeveloperMode`). Trace storage is local app state, not AgentCore evidence. Cleanup: quit Cherry; delete or rotate `%APPDATA%\CherryStudio\logs\` as needed; do not commit traces.

## Swarm / OpenClaw boundary

No SwarmRecall, SwarmVault, SwarmClaw, OpenClaw, or ClawX integration for this AgentCore client. Cherry’s built-in OpenClaw slice must remain stopped/unconfigured for AgentCore work. Existing unrelated Agents (for example Cherry Assistant / Cherry Claw) are preserved but are not the governed AgentCore path.
