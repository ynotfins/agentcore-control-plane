# M1 Entry Evidence — Storage and PostgreSQL 18 Safety Foundation

**Date:** 2026-07-14  
**Branch:** task/authority-reconciliation (HEAD: cfe341c)  
**M0 verification:** Passed — see audits/VALIDATION_REPORT_2026-07-14.md + cfe341c

## Confirmed live state

### Drive allocation units (WMI Win32_Volume BlockSize — 2026-07-14)

| Drive | Model | Disk# | SN | FileSystem | BlockSize | Target | Action |
|---|---|---|---|---|---|---|---|
| E: | HGST HUH721010ALE600 | 1 | 2YHS1ZMD | NTFS | 65536 | 64KB ✓ | None |
| F: | Samsung 990 PRO 4TB | 3 | 0025_384C... | NTFS | 65536 | 64KB ✓ | None |
| H: | Crucial CT2000P5PSSD8 | 4 | 0000...FE73 | NTFS | 65536 | 64KB ✓ | None |
| I: | Crucial CT1000BX500SSD1 | 0 | 2306E6AAD10C | NTFS | **512** | 64KB ✗ | **Format** |

### I: physical disk identity (required before format by BLUEPRINT §4)

- Disk: #0 (CT1000BX500SSD1, SATA)
- Serial: 2306E6AAD10C
- Capacity: 932 GB (WMI) / 915 GB usable
- Volume GUID: {ac27f734-60e4-4783-a6ec-6e9f922ad9d1}
- Drive letter: I:
- Label: Scratch 1 TB Sata
- Free: 914 GB / Used: < 1 GB
- Contents: **0 files at root** (confirmed 2026-07-14 live check)
- Current filesystem: NTFS / 512-byte allocation units
- Target: NTFS / 65536 (64 KB)

### PostgreSQL 16

- Binary: F:\AgentCore\postgres_runtime_engine\pgsql\bin\postgres.exe v16.6
- Data directory: F:\AgentCore\database_cluster (172 MB)
- Port: 55432 (currently not listening — service Ready, not running)
- Cluster: agent_core DB, SCRAM-SHA-256 SSL auth
- pg_dump.exe, pg_basebackup.exe: present
- Ops scripts: ops/Backup-AgentCorePostgres.ps1, ops/Start-AgentCorePostgres.ps1, ops/Test-AgentCorePostgresRestore.ps1

### Rollback point

Committed at M1 entry: cfe341c (BLUEPRINT.md code fence fix + AGENTS.md read order)  
PG16 cluster intact at F:\AgentCore\database_cluster

## M1 stop gates (per BLUEPRINT §15 / operator authorization)

STOP only for:
- Ambiguous physical disk identity on I: (confirmed above — proceed)
- Unexpected data or dependencies on I: (0 files — proceed)
- Failed backup or restore proof
- Unverifiable installer source
- A proposed change to a locked architecture decision
- An operation that would damage PostgreSQL 16 or the Swarm ecosystem
