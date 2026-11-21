# Proposal: G: second-copy headroom and recovery-chain retention

**Date:** 2026-10-21
**Status:** Applied to `normal_workstream` docs on 2026-10-21 after operator "update all docs". Locked authority files still need UNLOCK / AUTH.

## Applied (Tier 1)

- `docs/memory-platform/RETENTION_POLICY.md`
- `docs/memory-platform/BACKUP_RESTORE_WAL_PITR.md`
- `docs/DRIVE_WRITE_BOUNDARY_RULE.md`
- `docs/GLOBAL_AGENT_RULES.md`
- `docs/AGENTCORE_AUTOMATION_OPERATIONS.md`
- `docs/database_overview.md`
- `ops/M8-LIFECYCLE-REGISTRY.md`
- `.cursor/rules/g-drive-backup-headroom.mdc`
- `contracts/secondary-backup-drive-policy.json`

## Still needs UNLOCK / AUTH (not edited)

- `PROJECT_ANCHOR.md` / `BLUEPRINT.md` — drive-role wording can stay; no size claim required
- `contracts/global-agent-policy.yaml` — governed; mirrors `docs/GLOBAL_AGENT_RULES.md` G: headroom line
- `docs/operations/**` and `docs/agent-policy/**` — historical or governed; no current-runbook rewrite
- `D:\postgreSQL18-control-plane\DATABASE.md` — outside this worktree; add the same G: headroom bullets in §6 when that repo is opened

## Live facts used

- `G:` is a 119 GB external NVMe second-copy volume
- Primary backups/WAL stay on `E:\AgentCoreArchive\agentcore-memory\...`
- `archive_command` must succeed when the `G:` copy is skipped
- Prune runner: `ops/Prune-AgentCoreSecondaryBackupDrive.ps1`
- Task: `\AgentCore\SecondaryBackupHeadroom` daily 02:45
