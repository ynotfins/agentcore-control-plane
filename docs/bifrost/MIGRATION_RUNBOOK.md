# Migration Runbook — Bifrost MCP Gateway Cutover

**Updated:** 2026-09-08
**Authority:** ADR-2026-07-12-bifrost-mcp-gateway + configuration-source-of-truth
**Do not invent validation results.** Record only what was actually run.

## Preconditions

1. Repo contracts present:
   - `contracts/bifrost-upstream-mcp-registry.json`
   - `contracts/agentcore-gateway-client.json`
2. Binary present at the runtime path classified by current authority, and its reported version matches the current `PROJECT_ANCHOR.md` pin.
3. Windows User env `BIFROST_MCP_VIRTUAL_KEY` set (do not print)
4. Backup root available on E: (cold/backup tier)

## Implemented in repo (ops)

| Script | Role |
|--------|------|
| `ops/bifrost/Backup-AgentCoreBifrostConfig.ps1` | Rendered-configuration backup helper only; not a complete runtime checkpoint |
| `ops/bifrost/Install-AgentCoreBifrostGateway.ps1` | Runtime dirs, render config, optional scheduled task |
| `ops/bifrost/Start-AgentCoreBifrostGateway.ps1` | Start gateway |
| `ops/bifrost/Stop-AgentCoreBifrostGateway.ps1` | Stop gateway |
| `ops/bifrost/Test-AgentCoreBifrostGateway.ps1` | Health/smoke tests |
| `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1` | Per-IDE cutover to single gateway entry |
| `ops/bifrost/Restore-AgentCoreBifrostConfig.ps1` | Restore Bifrost config |
| `scripts/bifrost/render_bifrost_config.py` | Contract → config.json |
| `scripts/bifrost/validate_contracts.py` | Schema/drift validation |

## Migration steps

1. **Backup** affected live client files and Bifrost state under `E:\AgentCore\Backups\<bounded-stamp>\`. A material migration must preserve rendered config, `data\config.db`, OAuth metadata without token disclosure, affected client configuration, and scheduled-task definitions as applicable. Record SHA-256 hashes.
2. **Validate contracts:** `scripts\.venv\Scripts\python.exe scripts/bifrost/validate_contracts.py`
3. **Render + install:** `ops/bifrost/Install-AgentCoreBifrostGateway.ps1`
4. **Start gateway:** `ops/bifrost/Start-AgentCoreBifrostGateway.ps1`
5. **Test gateway:** `ops/bifrost/Test-AgentCoreBifrostGateway.ps1` (record actual results in evidence; do not fabricate).
6. **IDE cutover:** `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1` (or per-IDE follow `docs/prompts/install-agentcore-gateway-in-ide.md`).
7. **Restart each IDE** and discover tools via `agentcore-gateway` only.
8. **Sanitized evidence** under `ops/bifrost/evidence/` or `artifacts/bifrost-gateway-cutover-2026-07-12/`.

## Client scope

Resolve the current managed-client list, route, and authentication mode from
`contracts/agentcore-gateway-client.json`; do not maintain a copied client list
in this runbook. OpenClaw is AgentCore-owned and follows its dedicated profile.
SwarmClaw and other Swarm product installs remain outside AgentCore migration scope.

## Success criteria (checklist — mark only when evidenced)

- [ ] Bifrost listens on `127.0.0.1:8080`
- [ ] Each migrated IDE has single `agentcore-gateway` baseline entry
- [ ] No Postgres credentials in IDE MCP configs
- [ ] No whole-drive filesystem roots
- [ ] No Swarm MCP required in non-Swarm IDEs
- [ ] Rollback copies + hashes retained
- [ ] Contracts validate

## Failures

If cutover fails mid-client, stop, keep backups, and follow `ROLLBACK_RUNBOOK.md` for that client or for the Bifrost runtime. Ordinary rollback restores the last accepted Bifrost and client state. If gateway restoration fails, stop and report `agentcore-gateway` unavailable; do not create a direct MCP substitute. A legacy direct baseline requires an explicit authority change and is never an ordinary rollback.
