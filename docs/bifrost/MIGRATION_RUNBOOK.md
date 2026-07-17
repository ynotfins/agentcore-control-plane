# Migration Runbook — Bifrost MCP Gateway Cutover

**Date:** 2026-07-12
**Authority:** ADR-2026-07-12-bifrost-mcp-gateway + configuration-source-of-truth
**Do not invent validation results.** Record only what was actually run.

## Preconditions

1. Repo contracts present:
   - `contracts/bifrost-upstream-mcp-registry.json`
   - `contracts/agentcore-gateway-client.json`
2. Binary present: `H:\AgentRuntime\bifrost\bin\bifrost-http.exe` (v2.0.0-prerelease1 native Windows)
3. Windows User env `BIFROST_MCP_VIRTUAL_KEY` set (do not print)
4. Backup root available on E: (cold/backup tier)

## Implemented in repo (ops)

| Script | Role |
|--------|------|
| `ops/bifrost/Backup-AgentCoreBifrostConfig.ps1` | Backup Bifrost/runtime-related configs |
| `ops/bifrost/Install-AgentCoreBifrostGateway.ps1` | Runtime dirs, render config, optional scheduled task |
| `ops/bifrost/Start-AgentCoreBifrostGateway.ps1` | Start gateway |
| `ops/bifrost/Stop-AgentCoreBifrostGateway.ps1` | Stop gateway |
| `ops/bifrost/Test-AgentCoreBifrostGateway.ps1` | Health/smoke tests |
| `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1` | Per-IDE cutover to single gateway entry |
| `ops/bifrost/Restore-AgentCoreBifrostConfig.ps1` | Restore Bifrost config |
| `scripts/bifrost/render_bifrost_config.py` | Contract → config.json |
| `scripts/bifrost/validate_contracts.py` | Schema/drift validation |

## Migration steps

1. **Backup** live IDE configs + Bifrost appdata to `E:\AgentCore-Backups\bifrost-gateway-cutover-<stamp>\`. Record SHA256 (see `artifacts/bifrost-gateway-cutover-2026-07-12/BACKUP_MANIFEST.md`).
2. **Validate contracts:** `python scripts/bifrost/validate_contracts.py`
3. **Render + install:** `ops/bifrost/Install-AgentCoreBifrostGateway.ps1`
4. **Start gateway:** `ops/bifrost/Start-AgentCoreBifrostGateway.ps1`
5. **Test gateway:** `ops/bifrost/Test-AgentCoreBifrostGateway.ps1` (record actual results in evidence; do not fabricate).
6. **IDE cutover:** `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1` (or per-IDE follow `docs/prompts/install-agentcore-gateway-in-ide.md`).
7. **Restart each IDE** and discover tools via `agentcore-gateway` only.
8. **Sanitized evidence** under `ops/bifrost/evidence/` or `artifacts/bifrost-gateway-cutover-2026-07-12/`.

## Client list (non-Swarm)

cursor, minimax, mavis, claude-desktop, claude-code, codex, antigravity, open-interpreter

**Out of scope:** OpenClaw/ClawX, Swarm product installs.

## Success criteria (checklist — mark only when evidenced)

- [ ] Bifrost listens on `127.0.0.1:8080`
- [ ] Each migrated IDE has single `agentcore-gateway` baseline entry
- [ ] No Postgres credentials in IDE MCP configs
- [ ] No whole-drive filesystem roots
- [ ] No Swarm MCP required in non-Swarm IDEs
- [ ] Rollback copies + hashes retained
- [ ] Contracts validate

## Failures

If cutover fails mid-client, stop, keep backups, follow `ROLLBACK_RUNBOOK.md` for that client or for Bifrost runtime as needed. Do not reintroduce full direct baselines as the “fix” unless rolling back intentionally.
