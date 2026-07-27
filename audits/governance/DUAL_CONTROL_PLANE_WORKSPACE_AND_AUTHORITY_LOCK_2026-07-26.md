# Dual Control Plane Workspace and Authority Lock — AgentCore

Date: 2026-07-26

Scope: AgentCore repository-local authority lock and Swarm foreign-boundary pointer.

## Verdict

The neutral dual-root workspace is a read-only integration, comparison, and planning surface. It is not a third control plane and must not be used as a two-worktree write session.

AgentCore Stage B correctly blocks writes outside `D:\github\agentcore-control-plane`. Swarm implementation must occur in a fresh Swarm-rooted session or in SwarmClaw itself.

## Authority Lock

Created:

- `AUTHORITY_LOCK.md`
- `contracts/authority-lock.yaml`
- `scripts/validate_authority_lock.py`

Integrated:

- `scripts/agentcore_cursor/hooks.py`
- `scripts/agentcore_cursor/test_stage_b_suite.py`
- `scripts/bifrost/validate_contracts.py`

Protected classes:

- `operator_locked`
- `governed_mutable`
- `generated_read_only`
- `normal_workstream`

Authorization capabilities:

- `authority_maintainer`
- `projection_worker`
- `normal_builder`
- `independent_reviewer`

Model names are not authorization identities.

## Swarm Foreign Boundary

Created:

- `docs/boundaries/SWARM_FOREIGN_BOUNDARY.md`
- `contracts/foreign-ecosystem-boundaries.yaml`

AgentCore keeps only pointer-level Swarm facts: authority path, repository URL, commit, forbidden dependencies, permitted developer-only relationship, and shared-machine collision constraints.

Mutable Swarm runtime facts remain owned by `D:\github\swarm-ecosystem-control`.

## Serena Read-Only Root Cause

The observed Serena failure was consistent with `D:\github\agentcore-control-plane\.serena\project.yml` lacking `languages:` while using `language_servers:` with only `powershell`.

Swarm had no project-scoped `.serena\project.yml` during the read-only audit.

Serena project configs must remain separate per control plane. Do not create a combined dual-root Serena project.

## Swarm Read-Only Handoff

Swarm setup remains read-only from this AgentCore session. Required Swarm/SwarmClaw work includes:

- Create Swarm-local `AGENTS.md`, `CLAUDE.md`, `MILESTONES.md`/planning docs if needed.
- Set Windows User-scope Swarm variables.
- Reconcile SwarmVault viewer address (`3500` vs `4123`) under Swarm authority.
- Start and verify SwarmRecall, SwarmVault, and SwarmClaw through Swarm-owned lifecycle.
- Complete Swarm e2e acceptance before first autonomous project.

## Rollback

Use Git to restore source changes in this repository only:

```powershell
git restore -- AUTHORITY_LOCK.md contracts/authority-lock.yaml contracts/foreign-ecosystem-boundaries.yaml docs/boundaries/SWARM_FOREIGN_BOUNDARY.md scripts/validate_authority_lock.py scripts/agentcore_cursor/hooks.py scripts/agentcore_cursor/test_stage_b_suite.py scripts/bifrost/validate_contracts.py AGENTS.md DOC_AUTHORITY.md MASTER_CONFIG_AND_PROMPT.md audits/governance/DUAL_CONTROL_PLANE_WORKSPACE_AND_AUTHORITY_LOCK_2026-07-26.md
```
