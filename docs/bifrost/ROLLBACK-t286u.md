# Bifrost t286u rollback

Times below are America/New_York (UTC-5).

## Backups taken before mutation

Taken 2026-11-09 8:49:59 PM EST, before any t286u config edit.

1. Official config.json backup (no secret-bearing DB):

   `F:\AgentCore\runtime\bifrost\backups\20261109-204959\`

   Contains `config.json`, `config_config.json` (copy of `F:\AgentCore\runtime\bifrost\config\config.json`), and `config.sanitized.json` (renderer snapshot).

   Live `config.json` at backup time: 90659 bytes, mtime 2026-11-09 8:43:03 PM EST, sha256 `173B6329C90F1D37B577EB1BC6128D64CB3EB94A295B8FEF1840BBBB80473357`.

2. Secret-bearing SQLite backup (treat as secrets; do not copy to E: or F: extras):

   `D:\Autonomy\secrets-backups\bifrost\20261109-204959\`

   Contains `config.db` (44113920 bytes, mtime 2026-11-09 7:49:54 PM EST, sha256 `4804EF9D76FD61A85164780A73824B85FE58858A2CEED1EAF2419F9D163CFF35`) and a paired `config.json`.

Important drift at backup time: Bifrost process pid 32640 had been running since 2026-11-08 7:19:49 PM EST. The 8:43 PM EST GitOps `config.json` (23 MCP clients, `ide` VK, no `raven` VK) had not yet been reconciled into the live DB (19 clients, still had `raven`, no `context7`/`depwire`/`github_mcp`/`tentra`/`ide`). A restart applies the file (`source_of_truth=config.json`).

## Rollback steps

Do not touch NFA, AgentCore-PostgreSQL18, cloudflared, or `AgentCore-Grokbot-Cloudflare-Tunnel`. Official stop/start only act on `AgentCore-Bifrost-Gateway`, `bifrost-http.exe` on 127.0.0.1:8080, and the builder-compat proxy on :18082.

1. Restore the GitOps file with the official script:

   ```powershell
   & D:\github\agentcore-control-plane\ops\bifrost\Backup-AgentCoreBifrostConfig.ps1
   & D:\github\agentcore-control-plane\ops\bifrost\Restore-AgentCoreBifrostConfig.ps1 -BackupDir 'F:\AgentCore\runtime\bifrost\backups\20261109-204959'
   ```

   Also copy `config_config.json` back to `F:\AgentCore\runtime\bifrost\config\config.json` if the restore script does not (the official restore does this when `config_config.json` is present).

2. If you also need the pre-t286u *running* DB state (the 7:49 PM EST DB, including `raven` and excluding the unapplied 8:43 file entities), stop the gateway first, then copy the secret backup over the live DB, then start:

   ```powershell
   & D:\github\agentcore-control-plane\ops\bifrost\Stop-AgentCoreBifrostGateway.ps1
   Copy-Item -LiteralPath 'D:\Autonomy\secrets-backups\bifrost\20261109-204959\config.db' -Destination 'F:\AgentCore\runtime\bifrost\data\config.db' -Force
   # If rolling all the way back to pre-8:43 runtime, also restore config.json as in step 1.
   & D:\github\agentcore-control-plane\ops\bifrost\Start-AgentCoreBifrostGateway.ps1 -SkipPiShim -SkipSerenaShim
   ```

   Because `source_of_truth=config.json`, restoring only the DB and then starting will re-apply whatever is currently in `config.json` at startup. To return to the exact 7:49 PM running state you must restore **both** the 8:49 PM `config.json` *and* accept that the next start will still reconcile that 8:43 file into the DB. There is no supported way to keep the old DB rows after a start if the file is the source of truth, unless you also restore an older `config.json` that matches that DB (not captured as a pre-8:43 official file backup in this folder; the 8:49 backup *is* the 8:43 file).

3. Verify:

   ```powershell
   Invoke-RestMethod http://127.0.0.1:8080/health
   Invoke-RestMethod http://127.0.0.1:8080/api/version
   Get-NetTCPConnection -LocalPort 8787,18090,18091,20128,8080 -State Listen | Format-Table LocalPort,OwningProcess
   Get-ScheduledTask -TaskName AgentCore-Grokbot-Cloudflare-Tunnel,AgentCore-Bifrost-Gateway,AgentCore-Serena-Session-Shim | Format-Table TaskName,State
   ```

   Expect health `ok`, version `v2.0.0`, NFA :8787 still listening, Pi :18091 and Serena :18090 still listening, grokbot tunnel task Running.

## Other local change to undo if needed

If the eye2byte packaging shim was added, it is:

`C:\Users\ynotf\AppData\Local\Packages\PythonSoftwareFoundation.Python.3.12_qbz5n2kfra8p0\LocalCache\local-packages\Python312\site-packages\eye2byte_policy.py`

Remove that file to undo the shim. It was not part of the PyPI 0.7.0 sdist.
