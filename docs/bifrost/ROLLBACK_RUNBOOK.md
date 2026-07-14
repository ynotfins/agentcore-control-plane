# Rollback Runbook — Bifrost MCP Gateway

**Updated:** 2026-07-12
**Backup example root:** `E:\AgentCore-Backups\bifrost-gateway-cutover-20260712-223149`
**Hashes:** `artifacts/bifrost-gateway-cutover-2026-07-12/BACKUP_MANIFEST.md`

## Principles

1. Prefer restore-from-backup over inventing a new hybrid architecture.
2. Never print secrets while restoring.
3. Swarm product installs were not part of cutover — do not “fix” them during Bifrost rollback.
4. Repo contracts remain authority; after emergency live restore, re-render from contracts when stable.

## A. Roll back a single IDE

1. Locate backup file (timestamped `.bak` beside live config, or copy under the E: backup root `live-configs\`).
2. Verify SHA256 against `BACKUP_MANIFEST.md` when available.
3. Stop/close the IDE.
4. Replace live config with backup copy.
5. Restart IDE and confirm prior MCP surface returns.
6. Record evidence (paths + hashes only).

## B. Roll back Bifrost runtime config

1. Stop gateway: `ops/bifrost/Stop-AgentCoreBifrostGateway.ps1`
2. Restore via `ops/bifrost/Restore-AgentCoreBifrostConfig.ps1` **or** manually restore `config.json` / sqlite from the backup root (`bifrost-appdata\`).
3. Start gateway: `ops/bifrost/Start-AgentCoreBifrostGateway.ps1`
4. Run `ops/bifrost/Test-AgentCoreBifrostGateway.ps1` and record actual results.

## C. Full cutover abort (IDEs + gateway)

1. Stop Bifrost.
2. Restore all IDE live-configs from the backup root.
3. Restore Bifrost appdata/config from the same stamp.
4. Optionally leave Bifrost stopped if returning to pre-gateway direct baselines.
5. Do **not** commit live secret-bearing configs to Git.

## D. What not to do

- Do not use the Go SDK smoke as a substitute gateway.
- Do not paste unresolved upstream registries into IDEs “temporarily” without calling it a rollback.
- Do not delete E: backup roots until operator confirms retention policy.
