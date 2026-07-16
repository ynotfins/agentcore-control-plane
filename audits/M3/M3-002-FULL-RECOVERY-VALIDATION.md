# M3.002 Full-Recovery Validation

**Date:** 2026-07-16  
**Scope:** Source-only additive clarification of the locked M3 lossless architecture  
**Live rollout:** Not performed

## Outcome

PASS. The additive M3.002 migration, model-context contract, existing ten-tool memory surface,
stable recovery pagination, exact source expansion, summary correction, governed Git snapshot
metadata, cold-artifact recovery, and backup/restore graph integrity were validated in disposable
PostgreSQL 18 databases.

## Evidence

- `python -m pytest scripts/agentcore_memory/test_recovery.py -q`
  - PASS: 21 deterministic checks.
  - Covers all 18 required recovery invariants plus cursor tamper/scope checks, unchanged ten-tool
    surface, and IDE model/Git self-enrollment schema.
- `powershell -ExecutionPolicy Bypass -File scripts/memory_platform/Test-M3FullRecovery.ps1`
  - PASS against disposable databases only.
  - Retained 268 events, including a PostgreSQL history above one million conservative tokens and
    one quarantined event excluded from normal recovery.
  - Retrieved the complete accepted chronology through 91 bounded recovery operations.
  - Preserved two summary versions and 18 exact source edges after deliberately correcting an
    incorrect summary.
  - Expanded exact original content after moving its active artifact location from the configured
    hot tier to a simulated E:-class cold tier.
  - Preserved events, summaries, source edges, recovery metadata, snapshot metadata, profiles, and
    graph hashes through `pg_dump`/`pg_restore`.
  - Cleanup dropped both disposable databases and removed dump/hot/cold scratch artifacts.
- M3.002 up/down dry run
  - PASS: migrations M2 -> M3.001 -> M3.002.
  - PASS: exact 1,000,000 hard context profile.
  - PASS: future 2,000,000 hard context profile.
  - PASS: partial current-summary uniqueness in UP and guarded compatibility uniqueness in DOWN.
- `python scripts/bifrost/validate_contracts.py`
  - PASS.
- `python scripts/bifrost/test_contracts.py`
  - PASS: 111 checks.
- `python scripts/render_ide_rules.py --check`
  - PASS for all managed IDE profiles.

## Safety and rollback

- No migration was applied to live `agent_core`.
- The DOWN migration refuses to remove M3.002 while durable recovery, snapshot, or correction rows
  exist. This prevents rollback from silently deleting accepted evidence.
- Live rollout requires the normal operator-approved backup/restore gate and migration runner.
- Physical PostgreSQL restart/PITR remains governed by
  `ops/Test-AgentCorePg18Pitr.ps1`; this source task did not restart or mutate the live service.

## Residual operational step

After operator approval, deploy M3.002 to live PostgreSQL, re-render/deploy the Bifrost runtime
configuration from source, restart through the scheduled-task owner, and repeat the gateway-level
self-enrollment/recovery smoke test. Source acceptance does not authorize that rollout.
