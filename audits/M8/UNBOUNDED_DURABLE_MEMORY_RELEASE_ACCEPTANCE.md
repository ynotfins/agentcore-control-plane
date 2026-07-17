# Unbounded Durable Memory — Release Acceptance Report

**Date:** 2026-07-17  
**Scope:** AgentCore Control Plane — M8 Final Consolidation  
**Authority:** `BLUEPRINT.md` (locked), `MASTER_CONFIG_AND_PROMPT.md`  
**Operator:** Tony Valentine (`ynotf`) — CHAOSCENTRAL  

---

## 1. Final Main Commit

| Item | Value |
|------|-------|
| Canonical repository | `D:\github\agentcore-control-plane` |
| Branch | `main` |
| HEAD commit | `bd749aa` |
| HEAD message | `chore(evidence): add M5 PITR restore test audit for post-M3.002 recovery validation` |
| Previously reported main merge | `8a87739` (unbounded durable memory M3.002 live) |
| Reconciled commits promoted to main | `0953673`, `bd749aa` (both now in main via fast-forward) |
| Remote | `https://github.com/ynotfins/agentcore-control-plane.git` |
| Push verified | Yes — pushed `8a87739..bd749aa` on 2026-07-17 |

### Commit Classification

| Commit | Status | Notes |
|--------|--------|-------|
| `e07708d` | Already in main | feat: deploy unbounded durable memory live — M3.002 + v0.6.0 |
| `44d53bc` | Already in main | fix: canonical source path, WAL archive G:, PITR proof, >1M token proof |
| `8a87739` | Already in main | feat: unbounded durable memory M3.002 live + canonical source path |
| `0953673` | **Promoted to main** | fix: ON CONFLICT target for repositories table (UniqueViolation fix) |
| `bd749aa` | **Promoted to main** | chore: M5 PITR restore test audit evidence |

---

## 2. Runtime Source Path

| Item | Value |
|------|-------|
| agentcore-memory server | `D:\github\agentcore-control-plane\scripts\agentcore_memory\server.py` |
| Source verified | Yes — file exists in canonical repo |
| Bifrost config | `H:\AgentRuntime\bifrost\config.json` updated 2026-07-17 via `render_bifrost_config.py` |
| Previous stale path | `D:\github\agentcore-control-plane-unbounded-memory\scripts\agentcore_memory\server.py` |
| Renderer | `scripts/bifrost/render_bifrost_config.py` from `contracts/bifrost-upstream-mcp-registry.json` |

---

## 3. Drive and Database State (2026-07-17)

| Drive | Role | State |
|-------|------|-------|
| D: | Repos / canonical source | Clean — one canonical checkout at `D:\github\agentcore-control-plane` |
| E: | Cold archive / PG18 backups | Latest backup: `E:\AgentCoreArchive\agentcore-memory\backups\pg18\20260717-030001` |
| F: | PostgreSQL 18 hot data | `agent_core` + `cognee_core` at `127.0.0.1:55433` |
| G: | Backup copies | WAL+backup coverage per ops schedule |
| H: | Bifrost runtime | `H:\AgentRuntime\bifrost` — scheduled task `\AgentCore\AgentCore-Bifrost-Gateway` Running |
| I: | Scratch | Temp restore tests only (deleted at task close) |

PostgreSQL 18 (`127.0.0.1:55433`) schemas applied:
- M2 (m2.001) — canonical identity, immutable evidence, RLS
- M3 (m3.001, m3.002) — lossless context, unbounded recovery, model-aware profiles
- M4 (m4.001) — quarantine filter, context window assembly
- M5 (m5.001) — hybrid retrieval, Cognee promotion boundary
- M6 (m6.001) — LangGraph workflow, wf_ tables, capability leases
- **M8 (m8.001) — resource-location model: storage tiers, artifact metadata, worktree status, v_project_resource_map view** *(applied 2026-07-17)*

---

## 4. Template Parser Result (Copier templates)

Template sources validated by `scripts/engineering/test_copier_template_sources.py`.  
Templates use explicit `.jinja` suffix for all Jinja-parsed files per approved convention.  
Evidence: `audits/M7/M7-EXIT-EVIDENCE.md` §Template Parser.

---

## 5. Post-M3.002 PITR Result

Evidence file: `audits/M5/pg18-pitr-m3002-m3002-20260717-124311.json`

| Check | Result |
|-------|--------|
| PITR overall | `ok: true` |
| Backup source | `E:\AgentCoreArchive\agentcore-memory\backups\pg18\20260717-030001` |
| WAL archive | `E:\AgentCoreArchive\agentcore-memory\wal\pg18` |
| Restore port | 55441 (isolated test instance) |
| PITR marker found after recovery | `marker_count_after_recovery: 1` (present) |
| PITR fence absent after recovery | `fence_count_after_recovery: 0` (correct stop point) |
| WAL segment switched | `000000010000000000000070` |
| m3.002 migration present in restored DB | `m3002_present: true` |
| Migration records in restored DB | m2.001, m3.001, m4.001, m5.001, m6.001, m3.002 |
| Evidence events recovered | 138 |
| Context summaries recovered | 23 |
| pgvector extension | `vector=0.8.5` |

Reference JSON: `audits/M5/pg18-pitr-m3002-m3002-20260717-124311.json`

---

## 6. >1M Retained-History Proof

Evidence file: `audits/M5/million-token-proof-20260717164708.json`

| Check | Result |
|-------|--------|
| Test type | `unbounded_durable_memory_million_token_proof` |
| Tokenizer | `cl100k_base-conservative (1 token per 4 chars)` |
| Events seeded | 257 |
| Retained payload bytes | 4,232,166 |
| Conservative token estimate | **1,058,041** |
| Exceeds 1 million tokens | `true` |
| Pagination complete | `true` (52 pages, 5 per page) |
| No page duplicates | `true` |
| Hash mismatches | 0 |
| Compaction deletes no originals | `true` |
| Full history pageable | `true` |
| One million is not storage ceiling | `true` |

Reference JSON: `audits/M5/million-token-proof-20260717164708.json`

---

## 7. Exact Ten-Tool Surface

Verified in live Bifrost config (`H:\AgentRuntime\bifrost\config.json`, `agentcore_memory` entry):

| # | Tool | Purpose |
|---|------|---------|
| 1 | `memory_status` | Health and session status |
| 2 | `startup_context` | Assemble high-signal startup packet |
| 3 | `retrieve_context` | Pageable exact project recovery |
| 4 | `append_event` | Write governed memory event |
| 5 | `propose_fact` | Propose stable global fact candidate |
| 6 | `expand_source` | Recover exact original source |
| 7 | `session_open` | Open session with project/worktree identity binding |
| 8 | `session_close` | Close session and record outcome |
| 9 | `build_handoff` | Assemble recovery-ready handoff packet |
| 10 | `docs_search` | Search indexed library documentation |

Live validation: `scripts/agentcore/test_database_gating.py` — 18/18 pass (see §10 below).  
No SQL, DDL, database-admin, backup-admin, or Bifrost-admin tools exposed.

---

## 8. Backup and WAL Status

| Item | Value |
|------|-------|
| Latest PG18 backup | `E:\AgentCoreArchive\agentcore-memory\backups\pg18\20260717-030001` |
| WAL archive root | `E:\AgentCoreArchive\agentcore-memory\wal\pg18` |
| WAL archive active | Yes (`Test-Path` returns True) |
| G: backup copy | Managed by `ops/Archive-AgentCoreWal.ps1` and `ops/Backup-AgentCorePostgres.ps1` |
| PITR tested | Yes — post-M3.002 PITR test passed (see §5) |

---

## 9. IDE Self-Enrollment Status

| IDE | Status |
|-----|--------|
| Cursor | `C:\Users\ynotf\.cursor\mcp.json` — single `agentcore-gateway` entry, no PG credentials ✓ |
| Codex | `ide-profiles/codex/` — renderer present, direct enrollment required by operator |
| Claude Code | `ide-profiles/claude-code/` — renderer present, direct enrollment required by operator |
| Claude Desktop | `ide-profiles/claude-desktop/` — renderer present, direct enrollment required by operator |
| MiniMax | `ide-profiles/minimax/` — renderer present, direct enrollment required by operator |
| Mavis | `ide-profiles/mavis/` — renderer present, direct enrollment required by operator |
| Antigravity | `ide-profiles/antigravity/` — renderer present, direct enrollment required by operator |
| Open Interpreter | `ide-profiles/open-interpreter/` — renderer present, direct enrollment required by operator |

Automated cutover: `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1`  
Self-enrollment guide: `docs/prompts/install-agentcore-gateway-in-ide.md`

---

## 10. Worktree Retirement Result

| Item | Value |
|------|-------|
| Feature worktree path | `D:\github\agentcore-control-plane-unbounded-memory` |
| Feature branch | `task/unbounded-durable-memory` at `44d53bc` |
| All commits in main | Yes — `git merge-base --is-ancestor` confirmed |
| Bifrost config references | None — live config updated before removal |
| Git worktree remove | Success (`git worktree remove` 2026-07-17) |
| Directory existence after removal | `False` — path gone |
| DB worktree record | Updated to `status=retired, worktree_kind=feature, retired_at=2026-07-17` |
| Final `git worktree list` | `D:/github/agentcore-control-plane` `bd749aa` [main] |

Retained (not retired):
- `D:/AgentSwarm/runs/agentcore-memory-v1/worktree` at `c688fde [ai/global-memory-platform-v1]` — separate Swarm ecosystem worktree, untouched

---

## 11. Project Resource-Location Model Result

Migration `m8.001` applied 2026-07-17 to `agent_core` schema:

- `agentcore.storage_tier` extended: `backup_g`, `canonical_d`, `scratch_i` added
- `agentcore.artifact_locations` extended: `last_verified_at`, `resource_kind`, `classification`, `retention_class`, `restore_instructions`, `superseded_by_id`, `backup_coverage`
- `agentcore.worktrees` extended: `worktree_status`, `worktree_kind`, `retired_at`
- `agentcore.v_project_resource_map` — canonical cross-table location view created
- `agentcore.v_active_worktrees` — non-retired worktrees per project
- `agentcore.v_project_storage_tiers` — storage tier summary

Drift validation: `ops/Test-AgentCoreResourceLocationDrift.ps1` — 11/11 PASS (2026-07-17)

CONTEXT_INDEX: `.agentcore/CONTEXT_INDEX.md` updated with canonical project resource map.

---

## 12. Validator Results

| Validator | Result |
|-----------|--------|
| `scripts/bifrost/validate_contracts.py` | OK — registry+gateway schemas valid, 12 enabled, master-config drift clean |
| `scripts/agentcore/test_database_gating.py` | 18/18 PASS — role isolation, RLS, SECURITY DEFINER gates, 10-tool surface |
| `ops/Test-AgentCoreResourceLocationDrift.ps1` | 11/11 PASS — worktree paths, Bifrost config, storage tiers, CONTEXT_INDEX |
| Swarm untouched | Confirmed — no SwarmRecall, SwarmVault, SwarmClaw modifications |

---

## 13. Remaining IDE Self-Enrollment Actions

The following IDEs require operator-initiated self-enrollment (see `OPERATOR_ACTIONS_REQUIRED.md`):
- Codex CLI
- Claude Code
- Claude Desktop
- MiniMax
- Mavis
- Antigravity
- Open Interpreter

Run: `ops/bifrost/Invoke-AgentCoreIdeGatewayCutover.ps1` for each IDE, or follow  
`docs/prompts/install-agentcore-gateway-in-ide.md` for manual enrollment.

---

## 14. MASTER_CONFIG_AND_PROMPT.md

| Item | Value |
|------|-------|
| Path | `D:\github\agentcore-control-plane\MASTER_CONFIG_AND_PROMPT.md` |
| SHA-256 | `A89A048F61BAD8BF827EB0FE136F5EAB1D9C323A298F6705A54E4E5E8C83DC84` |
| Updated | 2026-07-17 — M8 consolidation additions |
| New sections | §12 Project resource-location and CONTEXT_INDEX |
| Updated phrases | resource-location registration, no-unregistered-paths rule, CONTEXT_INDEX policy, non-destructive compaction |
| Validator | `validate_contracts.py` master-config drift check — no failures |

---

## 15. Secrets and Security

- No secrets in any committed file (verified by `validate_contracts.py` secret scan)
- No PG credentials in IDE configs (verified by `test_database_gating.py`)
- No secret-bearing content in this report
- Evidence JSON files referenced by path only — not copied into this document
- All secrets remain in Windows User-scope environment variables

---

*This report is source-controlled evidence under `audits/M8/` in the canonical repository.*  
*PostgreSQL is the canonical data authority; this document is a human-readable summary.*
