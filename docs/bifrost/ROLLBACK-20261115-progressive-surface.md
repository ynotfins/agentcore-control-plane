# Rollback: progressive tool surface fix (2026-11-15)

Times are America/New_York (EST). Do not touch NFA, AgentCore-PostgreSQL18, cloudflared or the Grokbot tunnel.

Fast rollback, live and without a restart: for each of depwire, tentra, eye2byte and windows_mcp, send `PUT /api/mcp/client/{client_id}` with `{"is_code_mode_client": false}` using Basic auth from `BIFROST_ADMIN_USERNAME`/`BIFROST_ADMIN_PASSWORD`. Get the client ids from `GET /api/mcp/clients?limit=100`.

File rollback: copy `F:\AgentCore\runtime\bifrost\config.json.bak-20261115-1603` over `config.json`, and `config\config.json.bak-20261115-1603` over `config\config.json`. Or run `ops\bifrost\Restore-AgentCoreBifrostConfig.ps1 -BackupDir F:\AgentCore\runtime\bifrost\backups\20261115-160312`.

DB rollback, last resort: stop the gateway with the official script, copy `D:\Autonomy\secrets-backups\bifrost\20261115-1603\config.db` over the live `data\config.db` (also remove its `-wal`/`-shm`), then start it again.

Verify with `python scripts\bifrost\check_eager_tool_budget.py --skip-registry --live`.
