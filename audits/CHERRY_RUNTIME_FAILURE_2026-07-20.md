# Cherry Studio Runtime Failure & Repair (2026-07-20)

**Authority:** `BLUEPRINT.md` · `docs/operations/CHERRY_STUDIO_AGENTCORE.md` · `audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md`  
**Machine:** Windows AMD64  
**Preserved commits:** `e7ae011`, `3105a43` (not reset/reverted)  
**Repo HEAD at task start:** `3105a43704ddb7072d13bb895e3ec3d5a015db08` on `main`

## Status fields (do not collapse)

| Field | Status | Evidence |
| --- | --- | --- |
| configuration enrolled | PASS | `validate_cherry_studio.py` → single `agentcore-gateway` @ `http://127.0.0.1:8080/mcp` |
| MCP protocol validated externally | PASS | Authenticated initialize + tools/list (155 tools; Swarm=0) via lifecycle validator |
| application runtime usable | PASS | Official x64 install; window title `Cherry Studio`; local API `/health` 200 |
| Home usable | PASS | Post-repair screenshot: assistants list + chat UI; no `toLowerCase` overlay |
| Agents usable | PASS | Agents tab present without crash overlay; `agentcore-workspace-agent` in `agents.db` with gateway MCP mount |
| provider/model usable | PASS | Agent model `deepseek:deepseek-v4-pro`; Cherry API chat returned `PONG` |
| Agent conversation usable | PASS | `POST http://127.0.0.1:23333/v1/chat/completions` model `deepseek:deepseek-v4-pro` → content `PONG` |
| MCP mounted | PASS | Live LevelDB: only `agentcore-gateway`; no Swarm / 8081 / direct upstream |
| memory lifecycle via app credentials | PASS | `validate_cherry_memory_lifecycle.py` → `LIFECYCLE=PASS` (same VK Cherry stores) |
| project isolation validated | PASS | Lifecycle A/B project isolation checks PASS |
| Global Memory | PASS (OFF) | `globalMemoryEnabled=false` |
| rollback validated | PASS | Protected backups under `E:\AgentCore-Backups\` (see below) |
| complete live UI Agent conversation in Agents tab | PARTIAL | Home chat path + API proven; Electron a11y did not expose Agents tab for automated click |

## Root cause

### A. Native module architecture mismatch (primary crash)

| Artifact | Broken install (`C:\Program Files\Cherry Studio`) | Repaired install (`%LOCALAPPDATA%\Programs\Cherry Studio`) |
| --- | --- | --- |
| `Cherry Studio.exe` | PE `0x8664` (x64) | PE `0x8664` (x64) |
| `registry.node` | PE `0xAA64` (ARM64) — **invalid on this PC** | PE `0x8664` (x64) |
| Symptom | `ERR_DLOPEN_FAILED` / `registry.node is not a valid Win32 application` | Absent after reinstall |

Broken `registry.node` SHA-256: `81081E71C8EAADAB4D8D1C489A67FF1CDDF7C876D409021E92B7CFC565BEE3D5` (size 891904)  
Fixed `registry.node` SHA-256: `C46FA65CB72A22C4ED846DF91C4CA733C5AB7B6BFFF711EB2510DBA15B1E3033` (size 696320)

**Conclusion:** The prior package mixed an x64 Electron host with an ARM64 `registry-js` native addon (consistent with an ARM64/wrong-channel package residue or corrupt unpack). Not an app.asar logic bug.

### B. Home `toLowerCase` crash (secondary)

All assistant topics and assistant records lacked `model` objects (`model === undefined`). Home rendering called into provider/model helpers that assume a Model-shaped value → `Cannot read properties of undefined (reading 'toLowerCase')`.

### C. Agent chat model mis-pointed

`agentcore-workspace-agent` used `cherryin:agent/deepseek-v4-pro` while CherryIN had **no API key** and **0 models**. Retargeted to `deepseek:deepseek-v4-pro` (enabled provider with key + chat models).

### D. Memory config warn (non-fatal)

`Failed to update memory config: Cannot use 'in' operator to search for 'provider' in undefined` comes from Cherry `MemoryProcessor` / `isModel(obj)` when embedding model resolution returns `undefined` while Global Memory is OFF. Schema stubs were written; warn may still appear because `getModel('','')` returns undefined. **Global Memory remains OFF; AgentCore memory is gateway-only.**

## Repair performed

1. Quit Cherry; verified no processes.
2. Protected backup: `E:\AgentCore-Backups\cherry-runtime-repair-20260720-202353` (+ SHA-256 manifest).
3. Downloaded official `Cherry-Studio-1.9.12-x64-setup.exe`  
   - Expected SHA-256: `0675d440ac7d28e9b1d1ddf6ded95ff9faddf8d15bfdbaadfb0818c92b4afe44`  
   - Actual: match (`HASH_OK`).
4. Quiet-uninstalled broken all-users tree; installed official x64 setup (current-user path). All-users reinstall blocked on elevation; current-user x64 is architecture-correct and operational.
5. Preserved `%APPDATA%\CherryStudio` (no clean profile wipe).
6. Repaired agent model + assistant/topic models via:
   - `scripts/cherry/repair_cherry_memory_model.js`
   - `scripts/cherry/repair_cherry_assistant_models.js`
7. Revalidated: PE arches, UI Home screenshot, chat probe, `validate_cherry_studio.py`, `validate_cherry_memory_lifecycle.py`.

**Did not:** patch `app.asar`, replace `registry.node` manually, enable Global Memory, touch Swarm, or commit AppData/LevelDB/secrets.

## Install posture (final)

| Item | Value |
| --- | --- |
| Channel | Official GitHub release v1.9.12 x64 setup |
| Path | `%LOCALAPPDATA%\Programs\Cherry Studio\Cherry Studio.exe` |
| Version | 1.9.12 |
| Windows arch | AMD64 |
| Electron (from process args) | 41.2.1 / Win64 |
| Remaining ARM64 native | Optional Claude SDK `audio-capture` vendor arm64 binary only (not startup-critical) |

## Backups (secret-bearing — outside Git)

- `E:\AgentCore-Backups\cherry-runtime-repair-20260720-202353`
- `E:\AgentCore-Backups\cherry-installers-20260720\` (official setup + `latest.yml`)
- `E:\AgentCore-Backups\cherry-agents-model-*`
- `E:\AgentCore-Backups\cherry-memory-model-repair-*`
- `E:\AgentCore-Backups\cherry-assistant-model-repair-*`

## Unresolved limitations

- Interactive click into top-level **Agents** tab not proven via UI Automation (Electron a11y names empty). Home is proven; AgentCore agent is proven in DB + MCP validators.
- Cherry may still log non-fatal memory-config warnings while Global Memory is OFF.
- Prior all-users Program Files install removed; new default is per-user LocalAppData (document in ops runbook).
- Cherry logs can contain local API keys — never commit logs.
