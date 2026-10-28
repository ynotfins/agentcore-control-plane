# Rollback Runbook — Bifrost MCP Gateway

**Updated:** 2026-07-12
**Current backup namespace:** `E:\AgentCore\Backups\` (older `E:\AgentCore-Backups\` paths are historical evidence)
**Hashes:** `artifacts/bifrost-gateway-cutover-2026-07-12/BACKUP_MANIFEST.md`

## Principles

1. Prefer restore-from-backup over inventing a new hybrid architecture.
2. Never print secrets while restoring.
3. Swarm product installs were not part of cutover — do not “fix” them during Bifrost rollback.
4. Repo contracts remain authority; after emergency live restore, re-render from contracts when stable.

`ops/bifrost/Backup-AgentCoreBifrostConfig.ps1` preserves rendered configuration
only. A complete material-change checkpoint must separately preserve and
integrity-check `data\config.db`, OAuth metadata, affected client configuration,
and scheduled-task definitions as applicable.

## A. Roll back a single IDE

1. Locate backup file (timestamped `.bak` beside live config, or copy under the E: backup root `live-configs\`).
2. Verify SHA256 against `BACKUP_MANIFEST.md` when available.
3. Stop/close the IDE.
4. Replace live config with backup copy.
5. Restart IDE and confirm prior MCP surface returns.
6. Record evidence (paths + hashes only).

## B. Roll back Bifrost runtime config

1. Stop gateway: `ops/bifrost/Stop-AgentCoreBifrostGateway.ps1`
2. Restore via `ops/bifrost/Restore-AgentCoreBifrostConfig.ps1` or the exact bounded recovery procedure. Preserve and integrity-check `data\config.db` before replacing any persisted client/OAuth state; do not delete the whole database to repair one client.
3. Start gateway: `ops/bifrost/Start-AgentCoreBifrostGateway.ps1`
4. Run `ops/bifrost/Test-AgentCoreBifrostGateway.ps1` and record actual results.

## C. Full cutover abort (IDEs + gateway)

1. Stop Bifrost.
2. Restore all IDE live-configs from the backup root.
3. Restore Bifrost appdata/config from the same stamp.
4. Restore and validate the last accepted Bifrost gateway and client state.
5. If gateway restoration fails, stop and report `agentcore-gateway` unavailable; do not create a direct MCP substitute.
6. Do **not** commit live secret-bearing configs to Git.

## D. What not to do

- Do not use the Go SDK smoke as a substitute gateway.
- Do not paste unresolved upstream registries into IDEs, including under a rollback label.
- A legacy direct baseline requires an explicit authority change and is never an ordinary rollback.
- Do not delete E: backup roots until operator confirms retention policy.
