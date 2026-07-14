# SYSTEM_INVENTORY — CHAOSCENTRAL

**Generated:** 2026-07-03
**Mode:** Read-only investigation (no edits, no installs, no service starts)
**Source authority:** `D:\github\agentcore-control-plane` (canonical Git repo)
**Live ops root (compatibility/evidence only):** `D:\MCP-Control-Plane`
**Evidence base:** `D:\github\agentcore-control-plane\reports\_raw\`

---

## 1. Host Identity

| Property | Value |
|----------|-------|
| Hostname | `CHAOSCENTRAL` |
| OS | Windows 11 Pro (Build 10.0.26200) |
| User profile | `C:\Users\ynotf` |
| Domain/workgroup | Standalone workstation |
| Time zone | Not asserted in evidence (system clock shown as 2026-07-03 08:35:16 UTC context) |

This host is the single canonical machine for AgentCore local runtime, memory, and IDE orchestration. All architecture decisions below assume this single-node context; there is no plan B host in scope.

---

## 2. Compute Resources

| Component | Specification |
|-----------|---------------|
| CPU | Intel Core i9-14900KF — 24 cores / 32 threads |
| RAM | 128 GB DDR5 (Team Group UD5-6000) |
| GPU | NVIDIA GeForce RTX 4070 SUPER, 12 GB GDDR6X |
| Motherboard | ASUS Z790 GAMING WIFI7 |

The CPU and RAM envelope is well in excess of any realistic local memory/vector workload; the GPU is currently used for local model inference (Ollama installed but no listener active at audit time). No compute bottleneck is expected to constrain the memory architecture.

---

## 3. Drive Topology (verified, not assumed)

| Letter | Label | Capacity | Free | Filesystem | Type | Role (per design + verified usage) |
|--------|-------|----------|------|------------|------|-----------------------------------|
| **C:** | (Windows boot) | 1.9 TB | ~585 GB | NTFS | T-FORCE NVMe | OS, apps, user profile (`C:\Users\ynotf`), IDE configs |
| **D:** | (workspace) | 1.9 TB | ~852 GB | NTFS | T-FORCE NVMe | Source repos, project folders, build evidence (`D:\github`, `D:\MCP-Control-Plane`, `D:\AgentOps`, `D:\Codex_Managed`, `D:\Obsidian`, `D:\openclaw`) |
| **E:** | (archive) | 932 GB | ~470 GB | exFAT | SanDisk Extreme SSD (external) | Archive, WAL, base backups, cold storage (`E:\AgentCoreArchive`, `E:\CodexMemory`). **Correction to common assumption: E: is a 932 GB external SSD, NOT a 10 TB HDD.** |
| **F:** | `Agent_Vector_4TB` | 3.7 TB | ~3.7 TB | NTFS (64 KB AU) | Samsung SSD 990 PRO 4TB NVMe | Hot local memory / RAG / database tier (`F:\AgentCore`, `F:\AgentMemory`, `F:\Postgres`, `F:\Scratch`, `F:\VectorDB`) |
| **G:** | (backup) | 3.7 TB | n/a | (HDD) | Seagate Backup Plus external | Backup target only |

**Critical correction.** The drive-role map in `database-plan.md` §3.2 states that E: is archive / WAL / cold storage. The audit confirms this. The 10 TB HDD assumption present in some older planning documents does not match reality: E: is a 932 GB SanDisk Extreme SSD (exFAT). All architecture must respect this constraint — E: cannot be used for primary hot data and is too small for any new 4 TB-tier dataset.

The 4 TB NVMe (F:) is the only realistic target for any large local memory plane (vector indexes, raw/wiki state, Meilisearch data, PostgreSQL cluster).

---

## 4. Active AgentCore Runtime Directories on F:

Verified live runtime layout (all paths exist):

- `F:\AgentCore\` — active runtime root
  - `F:\AgentCore\database_cluster\` — PostgreSQL data cluster (governed memory spine)
  - `F:\AgentCore\postgres_runtime_engine\pgsql\` — PostgreSQL engine binaries
  - `F:\AgentCore\agents_workspace\{Cursor,Autonomy,Codex,OpenClaw,MiniMax,AndroidStudio}` — per-IDE workspaces
  - `F:\AgentCore\ingestion_staging\` — ingest staging
  - `F:\AgentCore\backups_hot\` — hot backups
  - `F:\AgentCore\scratch\` — scratch
  - `F:\AgentCore\agentmemory\`
    - `swarmvault\` — SwarmVault runtime (file-based RAG/wiki)
      - `raw\`, `wiki\`, `state\`, `agent\`, `swarmvault.config.json`, `swarmvault.schema.md`
    - `swarmrecall\` — SwarmRecall runtime
      - `bin\meilisearch.exe` (process running at audit time)
      - `meilisearch\data\`, `hf-cache\`, `config\agentcore.swarmrecall.local.json`
    - `lcm\`, `swarmclaw\`, `swarmrelay\` — local memory subdirs (state only; no active runtime)
- `F:\AgentMemory\` — empty / legacy
- `F:\Postgres\` — data + backups (legacy)
- `F:\Scratch\` — empty
- `F:\VectorDB\` — pre-wired substrate directories: `chroma\`, `lancedb\`, `pgvector\`, `qdrant\`. These directories exist but do not yet host active runtime data; they are placeholders for optional local vector backends.

**Observation.** `F:\VectorDB\pgvector\` exists as a directory but is **not** the live PostgreSQL location. The live PostgreSQL cluster is at `F:\AgentCore\database_cluster\`. Naming overlap can confuse later engineers.

---

## 5. Postgres Runtime Topology

| Item | Value |
|------|-------|
| Engine | PostgreSQL 16.6 |
| Extension | pgvector 0.8.2 |
| Engine binaries | `F:\AgentCore\postgres_runtime_engine\pgsql\bin\` |
| Cluster data dir | `F:\AgentCore\database_cluster\` |
| Host | `127.0.0.1` |
| Port | `55432` |
| Active databases | `agent_core` (governed memory), `swarmrecall` (SwarmRecall runtime) — **separate, do not merge** |
| WAL archive | `E:\AgentCoreArchive\backups_cold\pgvector\wal\` |
| Base backup | `E:\AgentCoreArchive\backups_cold\pgvector\base\` |
| Startup task | `\AgentCore\PostgresRuntime` (Windows Task Scheduler, on logon) |

**State at audit (2026-07-03):** No PostgreSQL listener was detected on `127.0.0.1:55432`. The Task Scheduler task exists per `SYSTEM_HANDOVER_BLUEPRINT.md`, but the live service was not running at the moment of this read-only scan. Architecture must assume "intended-state" with on-demand cold start, not "always-on."

---

## 6. Active Meilisearch

| Item | Value |
|------|-------|
| Binary | `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe` |
| Data path | `F:\AgentCore\agentmemory\swarmrecall\meilisearch\data` |
| Bound | `127.0.0.1:7700` |
| Master key in process args | None (intentional) |
| Process state at audit | **Running** (process observed in `Get-Process` scan) |

The single meilisearch process matches the SwarmRecall `n` ≥ 1 / n ≤ 1 design constraint from the handover blueprint. No second meilisearch instance is present.

---

## 7. Active Ollama State

Ollama is installed (binary present on system). At audit time the Ollama HTTP listener was not bound to `127.0.0.1:11434`. `Test-AgentCoreOllamaReadiness.ps1` previously reported `WARN — installed, not listening` (expected, no auto-pull). Ollama is therefore classified as **optional layer — not part of the always-on baseline.**

---

## 8. Memory & Database Components Inventory

| Component | Location | Status | Notes |
|-----------|----------|--------|-------|
| PostgreSQL 16.6 + pgvector 0.8.2 | `F:\AgentCore\database_cluster\` | Cold (task-scheduled start) | Spine of governed memory |
| `agent_core` database | same cluster | Schema applied | `system_info`, `projects`, `project_facts`, `messages`, `embeddings`, `global_vector_memory_store` (1536-d HNSW cosine), `agent_cross_project_telemetry` |
| `swarmrecall` database | same cluster | Schema applied | Local-only SwarmRecall backend |
| SwarmRecall API (Python) | `D:\github\vendor\swarm\swarmrecall` | Source only; service **not running** at audit | Intended `127.0.0.1:3300` |
| Meilisearch 1.x | `F:\AgentCore\agentmemory\swarmrecall\bin\meilisearch.exe` | **Running** | `127.0.0.1:7700` |
| SwarmVault | `F:\AgentCore\agentmemory\swarmvault` | File-based state present | Native CLI build at `D:\github\vendor\swarm\swarmvault\packages\cli\dist\index.js` |
| Obsidian vault | `D:\Obsidian\Dungeon Vault\` | Long-form notes | Local REST API `https://127.0.0.1:27124` (not running at audit) |
| Lossless Claw (LCM) | `C:\Users\ynotf\.openclaw\lossless-claw\` | `lcm.sqlite` 4.6 MB + `config.foundation.json` | Local file-based; not the canonical plane |
| `~/.openclaw/memory/` | `C:\Users\ynotf\.openclaw\memory\` | Multiple sqlite DBs | `main.sqlite`, `manager.sqlite`, `sparky-chief-product-quality-officer.sqlite`, `sparky_ceo_bot.sqlite` |
| `~/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite` | (under user profile) | Present | QMD local index |
| Codex native memories | `C:\Users\ynotf\.codex\memories_1.sqlite` | 4.3 MB | Plus `logs_2.sqlite` (1.4 GB), `goals_1.sqlite` (24 KB), `state_5.sqlite` (1.8 MB) |
| Codex memory pack | `codex-lossless-memory-pack@personal` plugin | Installed | Native lossless pack |
| Chroma / LanceDB / Qdrant | `F:\VectorDB\*` | Pre-wired dirs only | No active runtime |
| `F:\AgentCore\agentmemory\swarmvault\state\extracts\…` | (large) | Populated | Substantial extract corpus already on disk |

**Total memory-plane disk footprint (estimated from observed dirs):** tens of MB on F: for SwarmVault/SwarmRecall state, plus ~1.4 GB Codex logs. The 4 TB NVMe has ample headroom for years of growth.

---

## 9. Process & Listener Snapshot (audit moment)

| Service | TCP listening? | Process running? | Notes |
|---------|----------------|------------------|-------|
| PostgreSQL `:55432` | No (at audit) | No | Cold, task-scheduled |
| SwarmRecall API `:3300` | No | No | Source clone only |
| Meilisearch `:7700` | (loopback assumed) | Yes | One process only |
| OpenClaw gateway `:18789` | No | No | Gateway **NOT started** at audit; port is 18789, not 3000 |
| Obsidian REST `:27124` | No | No | Obsidian not in MCP server mode at audit |
| Ollama `:11434` | No | No | Installed, not listening |
| Antigravity IDE | n/a | Yes | Process observed |
| Claude Code | n/a | Yes | Process observed |
| ClawX | n/a | Yes (5 procs) | Process observed |
| Codex | n/a | Yes | Process observed |
| Cursor | n/a | Yes (many) | Process observed |
| Docker Desktop | n/a | Yes | Service stopped |
| MiniMax Code (mavis) | n/a | Yes | Process observed |

**Critical implication.** At this moment, **no universal memory gateway is online.** Any architecture that depends on a live `127.0.0.1:3000/v1` or `127.0.0.1:3300` endpoint is currently in an unreachable state. Architecture must include a deterministic cold-start contract.

---

## 10. Power, Thermal, Reliability Posture

Not measured in this audit. With an i9-14900KF on an ASUS Z790 and a 4 TB NVMe on the same board, sustained write workloads to F: are well within spec. No UPS detection was performed; loss-of-power durability is therefore **assumed at the level of the existing PostgreSQL WAL archive on E:** but not verified in this pass.

---

## 11. Summary

CHAOSCENTRAL is a high-end Windows 11 workstation with 128 GB RAM, a 4 TB NVMe (F:) sized for hot memory/vector workloads, a corrected 932 GB E: SSD for cold archive, and a pre-wired but mostly dormant AgentCore runtime (PostgreSQL + SwarmRecall + SwarmVault + Meilisearch). The native memory infrastructure is present and validated by prior rollout reports; the live services were largely offline at audit time. The next phase of this investigation quantifies which IDEs/agents are wired into which plane, and whether the assumed "OpenClaw universal gateway at localhost:3000" matches reality.