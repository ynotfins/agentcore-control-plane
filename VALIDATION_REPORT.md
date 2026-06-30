# Validation Report

Historical baseline report: this document captures the initial repo/bootstrap validation pass from 2026-06-24. Current source-of-truth status should be read from the newer control-plane docs, current validators, and current handoff documents.

**Superseded by:** `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `docs/handoffs/AGENTCORE_SWARM_ROLLOUT_HANDOFF_2026-06-30.md`, `artifacts/rollout-2026-06-30/ROLLOUT_REPORT.md`, `database-plan.md`, and the current validators under `validators/` and `ops/Test-AgentCore*.ps1`. Do not use pass/fail status from this file as a current acceptance gate.

Follow-up hardening after this historical baseline added:

- local-only SwarmVault runtime initialization under `F:\AgentCore\agentmemory\swarmvault`
- local-only SwarmRecall runtime under `F:\AgentCore\agentmemory\swarmrecall`
- scoped `hostssl` PostgreSQL auth for `swarmrecall_app`
- native Meilisearch on `F:` with `--no-analytics`
- loopback-only SwarmRecall API on `127.0.0.1:3300`
- AgentCore scheduled-task ownership for SwarmRecall API and Meilisearch:
  - `\AgentCore\SwarmRecallApi`
  - `\AgentCore\SwarmRecallMeilisearch`
- aggregate runtime validator: `D:\github\agentcore-control-plane\ops\Test-AgentCoreRuntimeSuite.ps1`

Generated: 2026-06-24

## Scope

This report validates the initial AgentCore control-plane bootstrap and vendor/source layout work:

- vendor repositories cloned into `D:\github\vendor`
- control-plane repository initialized at `D:\github\agentcore-control-plane`
- runtime paths created under `F:\AgentCore`
- backup paths created under `E:\AgentCoreBackups`
- governance/docs/scripts migrated from `D:\MCP-Control-Plane`
- secret and runtime data protections applied through `.gitignore`

## Cloned Repositories

All required repositories were cloned into the isolated vendor roots and were not placed in IDE workspace folders or app-project folders.

| Repo | Path | HEAD commit |
| --- | --- | --- |
| `swarmclaw` | `D:\github\vendor\swarm\swarmclaw` | `e1e45f501c516aa85de6920b9851698e018679a1` |
| `swarmvault` | `D:\github\vendor\swarm\swarmvault` | `4ce0c7cb545c669f3cd35fc6d0300c6b088a52ea` |
| `swarmdock` | `D:\github\vendor\swarm\swarmdock` | `fc6babd3b804539735496ec456cc20a808828b35` |
| `swarmfeed` | `D:\github\vendor\swarm\swarmfeed` | `0a1ec85b395e9b6a20eada6c3253fa2927874b2f` |
| `swarmrelay` | `D:\github\vendor\swarm\swarmrelay` | `4e73ea8db6f9285f37ac90e280185f16fa91318b` |
| `swarmrecall` | `D:\github\vendor\swarm\swarmrecall` | current local checkout after 2026-06-25 hardening pass |
| `lossless-memory4agent` | `D:\github\vendor\memory\lossless-memory4agent` | `213a6ccae874ad542dc94242de68abb4b93550ad` |
| `lossless-claw` | `D:\github\vendor\memory\lossless-claw` | `753721fc95b763c95a620f535c6743ba70b1c34a` |

README validation:

- Root README files were read for all seven repositories before any install step.
- No package installation was performed during this layout/bootstrap pass.

## Directory Validation

### Source roots

Verified present:

- `D:\github\vendor\swarm`
- `D:\github\vendor\memory`
- `D:\github\agentcore-control-plane`

### Runtime roots

Verified present:

- `F:\AgentCore\postgres`
- `F:\AgentCore\agentmemory`
- `F:\AgentCore\agentmemory\swarmvault`
- `F:\AgentCore\agentmemory\lcm`
- `F:\AgentCore\agentmemory\swarmclaw`
- `F:\AgentCore\agentmemory\swarmrelay`
- `F:\AgentCore\scratch`

Existing runtime directories were preserved in place:

- `F:\AgentCore\agents_workspace`
- `F:\AgentCore\backups_hot`
- `F:\AgentCore\database_cluster`
- `F:\AgentCore\ingestion_staging`
- `F:\AgentCore\postgres_runtime_engine`

### Backup roots

Verified present:

- `E:\AgentCoreBackups\postgres`
- `E:\AgentCoreBackups\agentmemory`
- `E:\AgentCoreBackups\swarmvault-exports`
- `E:\AgentCoreBackups\logs`

## Migration Validation

Migrated into `D:\github\agentcore-control-plane`:

- root governance and architecture Markdown files
- `contracts/`
- `docs/`
- `inventory/`
- `ops/` excluding historical `ops/logs/`
- `probes/`
- `registry/`
- `renderers/`
- `rules/`
- `schemas/`
- `scripts/`
- `supervisor/`
- `validators/`

Excluded from migration:

- `.git/`
- `.context-fabric` data from the old repo
- `.serena/cache/`
- `artifacts/`
- `ops/logs/`
- runtime databases and secret-bearing local state

Verification:

- `ops/logs/` is absent from the migrated repo.
- The new repo contains governance/source material only.

## Security Validation

### Secret scan

Pattern scan for likely secret material found no raw keys, bearer tokens, private-key blocks, or certificate bodies committed into the repo.

Observed matches were limited to safe environment-variable usage and documentation references such as:

- `$env:PGPASSWORD = [Environment]::GetEnvironmentVariable(...)`
- policy/docs mentioning secret handling requirements

No hardcoded secret values were found.

### `.gitignore` validation

Explicit ignore probes confirmed the repo blocks sensitive patterns including:

- `.env`
- `.env.local`
- `*.pem`
- `*.key`
- `runtime/*`
- `backups/*`
- `state/*`
- `raw/*`
- `wiki/*`
- `logs/*`
- `agentmemory/*`

### First-responder data posture

The repo-level policy documents and new integration docs set the default posture to:

- private/local-only by default
- no incident-data routing into `swarmdock`, `swarmfeed`, or hosted services
- governed memory writes through `global-memory-gateway`
- redaction required before any cross-project memory write

## Repo Content Stats

Measured before the initial commit:

- file count (excluding `.git` internals): `105`
- total tracked-content bytes: `659565`

## Commit Readiness

Pending final commit action:

- `git add .`
- commit message:
  `Initial AgentCore control plane: hardened database docs, vendor layout, runtime plan, and local swarm integration foundation`

After commit:

- verify `git status` is clean
- capture the resulting commit hash in operator output

## Recommended Next Steps

1. Keep all private-response workflows in local-only mode until a separate approval expands the boundary.
2. Configure runtime paths for SwarmClaw, SwarmVault, SwarmRelay, and LCM to use the `F:\AgentCore\agentmemory` subtree rather than upstream defaults.
3. If Swarm components are brought online later, validate them one at a time starting with `swarmclaw`, `swarmvault`, and `swarmrelay`.
