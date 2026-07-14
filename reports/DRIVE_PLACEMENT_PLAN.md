# DRIVE_PLACEMENT_PLAN — CHAOSCENTRAL

**Generated:** 2026-07-03
**Scope:** Where every memory/context/backplane artifact should live on the four working drives (C, D, E, F), based on the audited drive topology and the source-controlled `database-plan.md` §3.2 drive-role map.
**Key correction:** E: is a **932 GB SanDisk SSD**, not a 10 TB HDD. All planning must respect this constraint.

---

## 1. Drive-Role Map (verified + corrected)

| Letter | Capacity | Free | Filesystem | Type | Verified role | Notes |
|--------|----------|------|------------|------|---------------|-------|
| **C:** | 1.9 TB | ~585 GB | NTFS | T-FORCE NVMe (boot) | OS, apps, user profile, IDE configs | `C:\Users\ynotf` |
| **D:** | 1.9 TB | ~852 GB | NTFS | T-FORCE NVMe (workspace) | Source repos, build evidence, project folders | `D:\github`, `D:\MCP-Control-Plane`, `D:\AgentOps`, `D:\Codex_Managed`, `D:\Obsidian`, `D:\openclaw` |
| **E:** | **932 GB** | ~470 GB | exFAT | SanDisk Extreme SSD (external) | Archive, WAL, base backups, cold storage, emergency spool | **`E:\AgentCoreArchive`**. **NOT** a 10 TB HDD. |
| **F:** | 3.7 TB | ~3.7 TB | NTFS (64 KB AU) | Samsung SSD 990 PRO 4TB NVMe | Hot local memory / RAG / database tier | `F:\AgentCore` |
| **G:** | 3.7 TB | n/a | HDD | Seagate Backup Plus external | Backup target only | Off-host, optional |

**Hard rule.** Per `database-plan.md` §3.2:
- Do not create primary SQL databases on E:.
- Do not add hot AgentCore runtime data to C:.
- D: is source/code only; no DB cluster data on D:.
- Hot AgentCore runtime lives on F:.

---

## 2. Existing Placement (verified)

| Path | Drive | Component | Status |
|------|-------|-----------|--------|
| `C:\Users\ynotf\.codex` | C | Codex profile | Live |
| `C:\Users\ynotf\.claude` | C | Claude Code profile | Live |
| `C:\Users\ynotf\.cursor` | C | Cursor profile | Live |
| `C:\Users\ynotf\.openclaw` | C | OpenClaw profile (incl. LCM) | Live |
| `C:\Users\ynotf\.openinterpreter` | C | Open Interpreter profile | Live |
| `C:\Users\ynotf\.minimax` | C | MiniMax Code profile | Live |
| `C:\Users\ynotf\.mavis` | C | Mavis profile (linked config) | Live |
| `D:\github\agentcore-control-plane` | D | Canonical source repo | Live |
| `D:\github\swarm-agent-team` | D | Working repo | Live |
| `D:\github\agent-team` | D | Working repo | Live (20 dirty) |
| `D:\github\autonomous-agent-team` | D | Working repo | Live (22 dirty, HEAD detached) |
| `D:\Obsidian\Dungeon Vault` | D | Obsidian vault | Live (long-form human notes) |
| `D:\Codex_Managed` | D | Codex extra | Live |
| `D:\AgentOps` | D | Operations dir | Live |
| `D:\openclaw` | D | OpenClaw install | Live |
| `F:\AgentCore\database_cluster` | F | PostgreSQL data cluster | Live |
| `F:\AgentCore\postgres_runtime_engine` | F | PostgreSQL binaries | Live |
| `F:\AgentCore\agentmemory\swarmvault` | F | SwarmVault file state | Live |
| `F:\AgentCore\agentmemory\swarmrecall` | F | SwarmRecall runtime + Meilisearch | Live |
| `F:\AgentCore\agentmemory\lcm\swarmclaw\swarmrelay` | F | Local memory subdirs | Empty placeholder |
| `F:\AgentCore\agents_workspace\{Cursor,Autonomy,Codex,OpenClaw,MiniMax,AndroidStudio}` | F | Per-IDE workspace roots | Live |
| `F:\AgentCore\ingestion_staging` | F | Ingest staging | Live |
| `F:\AgentCore\backups_hot` | F | Hot backups | Live |
| `F:\AgentCore\scratch` | F | Scratch space | Live |
| `F:\VectorDB\{chroma,lancedb,pgvector,qdrant}` | F | Pre-wired vector dirs | Empty placeholders |
| `E:\AgentCoreArchive\backups_cold\pgvector\wal` | E | PostgreSQL WAL archive | Live|
| `E:\AgentCoreArchive\backups_cold\pgvector\base` | E | PostgreSQL base backups | Live |

The placement already conforms to the design. No re-placement is required. The architecture only needs to confirm the plan and identify any new components.

---

## 3. Placement Plan by Component

### 3.1 Governed Memory (PostgreSQL + pgvector)

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| Engine binaries | F | `F:\AgentCore\postgres_runtime_engine\pgsql\` | Hot tier; NTFS; high IOPS NVMe |
| Data cluster | F | `F:\AgentCore\database_cluster\` | Hot tier; same reason |
| `agent_core` DB | F (cluster) | same | Governed cross-project memory |
| `swarmrecall` DB | F (cluster) | same | Separate DB; same cluster; per design |
| WAL archive | E | `E:\AgentCoreArchive\backups_cold\pgvector\wal\` | Cold; archive; survives F: failure |
| Base backups | E | `E:\AgentCoreArchive\backups_cold\pgvector\base\` | Cold; archive |
| Hot backups | F | `F:\AgentCore\backups_hot\` | For fast restore |

**Rationale.** WAL on E: gives disaster recovery even if F: dies. Base backups on E: same. Hot backups on F: for fast incremental restore. This split is already implemented and is correct.

### 3.2 Semantic Recall (SwarmRecall + Meilisearch)

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| API source | D | `D:\github\vendor\swarm\swarmrecall` | Source code, Git-managed |
| Runtime root | F | `F:\AgentCore\agentmemory\swarmrecall` | Hot runtime |
| Meilisearch binary | F | `F:\AgentCore\agentmemory\swarmrecall\bin\` | Hot |
| Meilisearch data | F | `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data` | Hot; persistent |
| HuggingFace cache | F | `F:\AgentCore\agentmemory\swarmrecall\hf-cache` | Hot; model downloads |
| Local config | F | `F:\AgentCore\agentmemory\swarmrecall\config\agentcore.swarmrecall.local.json` | Hot |

### 3.3 Local RAG (SwarmVault)

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| Source | D | `D:\github\vendor\swarm\swarmvault` | Source code |
| Vendored CLI build | D | `D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js` | Build artifact in source tree |
| Runtime root | F | `F:\AgentCore\agentmemory\swarmvault` | Hot runtime |
| `raw\` | F | same root | Indexed source content |
| `wiki\` | F | same root | Curated wiki |
| `state\` | F | same root | Graph, retrieval, context-packs |
| `agent\` | F | same root | Agent-specific state |
| Extracts corpus | F | `F:\AgentCore\agentmemory\swarmvault\state\extracts\…` | Already populated, substantial content |

**Rationale.** Source on D: for Git hygiene. Runtime on F: for IOPS. No part of SwarmVault should ever be on E: (cold) or C: (OS).

### 3.4 Lossless Claw (LCM)

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| LCM root | C | `C:\Users\ynotf\.openclaw\lossless-claw\` | OpenClaw profile lives on C:; LCM is OpenClaw-local |
| `lcm.sqlite` | C | same | Local |
| `config.foundation.json` | C | same | Local |
| `files\` | C | same | Local |

**Status quo is acceptable.** LCM is OpenClaw-local; the design treats it as a local retrieval plane, not canonical durable storage. Future consolidation may move LCM to F: under `F:\AgentCore\agentmemory\lcm\`, but this is **deferred** (not in baseline).

### 3.5 Codex Native Memory

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| Codex profile | C | `C:\Users\ynotf\.codex\` | IDE profile on C: |
| `memories_1.sqlite` | C | same | Native |
| `logs_2.sqlite` (1.4 GB) | C | same | Native; **needs a rotation policy** |
| `goals_1.sqlite` | C | same | Native |
| `state_5.sqlite` | C | same | Native |
| `codex-lossless-memory-pack@personal` plugin state | C | `C:\Users\ynotf\.codex\memories\` | Native |

**Status quo is acceptable** for native Codex state. The 1.4 GB logs DB warrants a future rotation policy.

### 3.6 OpenClaw Per-Agent Memory

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| `~/.openclaw\memory\` | C | `C:\Users\ynotf\.openclaw\memory\` | OpenClaw profile on C: |
| `main.sqlite`, `manager.sqlite`, `sparky-*.sqlite` | C | same | Per-agent local |
| `qmd.foundation.json` | C | same | Local |

Status quo is acceptable. Future consolidation may merge per-agent stores into LCM, deferred.

### 3.7 Obsidian Vault

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| Vault | D | `D:\Obsidian\Dungeon Vault\` | Human-authored notes; Git-friendly; backup-able |

Status quo is correct. Obsidian lives on D: alongside source repos, so it can be synced with Git (e.g., `obsidian-git`) and is backed up with the rest of D:.

### 3.8 Pre-wired Optional Vector Stores

`F:\VectorDB\{chroma,lancedb,pgvector,qdrant}\` exist as empty directories. They are placeholders. The live pgvector is inside PostgreSQL, not in `F:\VectorDB\pgvector\` (naming overlap noted in `SYSTEM_INVENTORY.md`). No new placement needed unless the user wants to activate one of the optional stores. Recommendation: **leave them empty** until a specific use case appears.

### 3.9 Workspace Roots

| IDE | Workspace |
|-----|-----------|
| Cursor | `F:\AgentCore\agents_workspace\Cursor` |
| Autonomy | `F:\AgentCore\agents_workspace\Autonomy` |
| Codex | `F:\AgentCore\agents_workspace\Codex` |
| OpenClaw | `F:\AgentCore\agents_workspace\OpenClaw` |
| MiniMax | `F:\AgentCore\agents_workspace\MiniMax` |
| AndroidStudio | `F:\AgentCore\agents_workspace\AndroidStudio` |

Status quo is correct.

### 3.10 MCP Server Vendored Packages

| Package | Drive | Path |
|---------|-------|------|
| arabold-docs | C | `C:\Users\ynotf\.cursor\vendor\arabold-docs-mcp\…` |
| context-fabric | C | `C:\Users\ynotf\.cursor\vendor\context-fabric-mcp\…` |
| Codex mcp-wrappers | C | `C:\Users\ynotf\.codex\mcp-wrappers\…` |
| Obsidian MCP wrapper | C | `C:\Users\ynotf\.openclaw\start-obsidian-mcp-server.ps1` |

Status quo is correct. MCP vendored installs are per-IDE and stay with the IDE profile on C:.

### 3.11 Source Authority

| Artifact | Drive | Path | Rationale |
|----------|-------|------|-----------|
| Canonical Git source | D | `D:\github\agentcore-control-plane` | Source code; Git; deployable |
| Vendor swarm subtrees | D | `D:\github\agentcore-control-plane\vendor\swarm\*` | Subtrees inside canonical repo |
| Other working repos | D | `D:\github\swarm-agent-team`, `D:\github\agent-team`, `D:\github\autonomous-agent-team` | Working code |

Status quo is correct.

---

## 4. New Components — Placement Plan

For any new memory/context/backplane artifact, the decision matrix is:

| Type of artifact | Drive | Why |
|------------------|-------|-----|
| Hot runtime state (DB cluster, search engine data, vault file state) | **F:** | NVMe, NTFS, IOPS |
| Cold archive (WAL, base backups, emergency spool) | **E:** | Survives F: failure |
| Source code, Git repos | **D:** | Git-friendly, versioned |
| IDE / agent profile (config, plugins, native memory) | **C:** | OS-managed |
| Long-form human notes (Obsidian) | **D:** | Git-friendly |
| Vendored MCP packages (Node/Python) | **C:** | Per-IDE vendor dir |
| Optional vector store (chroma/lancedb/qdrant) | **F:** under `F:\VectorDB\*` | Already pre-wired |

### 4.1 Future: Unified Memory Catalog

When `migrations\0001`–`0005` are applied, the new tables go inside the existing `agent_core` PostgreSQL cluster on F:. No new drive placement needed.

### 4.2 Future: Lossless Claw Consolidation (deferred)

If/when LCM is consolidated, the natural home is `F:\AgentCore\agentmemory\lcm\`. The empty placeholder already exists. The migration would move `C:\Users\ynotf\.openclaw\lossless-claw\` → `F:\AgentCore\agentmemory\lcm\`. Deferred.

### 4.3 Future: Pre-wired Vector Stores

If/when chroma/lancedb/qdrant are activated, they should go under their pre-existing `F:\VectorDB\*` dirs. No new placement needed.

### 4.4 Source Repo Backups

Source repo backups (e.g., `artifacts\backups\…`) currently live inside the canonical repo on D:. This is acceptable for read-only pre-mutation snapshots. If backups grow large, move to `E:\AgentCoreArchive\backups_cold\source-repo\` (≤ 932 GB E: budget).

### 4.5 Off-host Backup

The G: drive (3.7 TB external HDD) is the right target for periodic full-image snapshots of F:. A weekly `robocopy /MIR F:\AgentCore G:\AgentCoreMirror` would give disaster recovery without depending on E: (which is small).

---

## 5. Drive Headroom Forecast

| Drive | Free now | Expected 12-month growth | Net free in 12 months |
|-------|----------|--------------------------|------------------------|
| C: | ~585 GB | ~50 GB (logs, npm caches, etc.) | ~535 GB |
| D: | ~852 GB | ~200 GB (working repos, vendored builds) | ~652 GB |
| E: | ~470 GB | ~100 GB (WAL + base backups + source-repo backups) | ~370 GB |
| F: | ~3.7 TB | ~50 GB (memory plane growth) | ~3.65 TB |

F: has effectively unlimited headroom for the memory architecture. E: should be monitored if WAL retention is extended. C: and D: are not at risk for any of the planned workloads.

---

## 6. Risks and Mitigations

| Risk | Drive affected | Mitigation |
|------|----------------|------------|
| E: only 932 GB — not 10 TB as some older docs assumed | E | Confirm in all future docs; off-load long-term retention to G: |
| Codex `logs_2.sqlite` 1.4 GB | C | Add rotation policy; future cleanup prompt |
| `F:\VectorDB\pgvector\` naming overlap with live pgvector | F | Document clearly; consider rename or symlink |
| No off-host backup of F: | F | Schedule weekly `robocopy /MIR` to G: |
| WAL archive on E: only — single point of failure for archive | E | Periodic copy to G: for off-host retention |
| SwarmVault extracts corpus growing | F | Periodic doctor + raw/page count cap; safe source-registration strategy |

---

## 7. Conclusion

The audited drive topology matches the source-controlled design. Hot memory/vector/database tier on F: (4 TB NVMe), cold archive on E: (932 GB SanDisk SSD — corrected from the older 10 TB assumption), source code on D:, IDE profiles on C:. The corrected E: size is the only change vs. some older planning docs and must be propagated forward. No re-placement of existing artifacts is required. New artifacts follow the same placement rules: hot on F:, cold on E:, code on D:, profile on C:. The architecture options in the next deliverable assume this placement plan as a fixed input.