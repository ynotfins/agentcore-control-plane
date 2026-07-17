# M2 Exit Evidence — Canonical Identity and Immutable Evidence

**Status:** PASSED  
**Completed on:** 2026-07-15 / 2026-07-16 UTC  
**Database:** PostgreSQL 18.4 at `127.0.0.1:55433/agent_core`  
**Migration:** `m2.001` (`migrations/m2/001_up_canonical_identity_immutable_evidence.sql`)  
**Harness:** `scripts/memory_platform/Test-M2CanonicalIdentity.ps1`  
**Acceptance summary:** `audits/M2/m2-acceptance-summary.json` (run `20260715202520`)

## Exit Criteria

| BLUEPRINT.md M2 exit criterion | Result | Evidence |
| -- | -- | -- |
| Separate machine, user, project, repository, worktree, IDE/client, agent, session, run, LangGraph thread, and workflow identities | PASS | `m2-acceptance-summary.json` check `separate identities seeded`; tables in `role-grants.txt` |
| Append-only evidence ledger works | PASS | `agentcore.evidence_events`; immutable trigger; append function exercised by harness |
| Idempotent writes work | PASS | duplicate event submission returned the same event id and one row |
| Large payloads externalize by content hash | PASS | harness wrote payload to `H:\AgentRuntime\agentcore-memory\artifacts\sha256\57\575c...03c9.txt`, stored artifact row, appended event reference |
| Project A cannot write Project B | PASS | `agentcore.append_evidence_event` rejected cross-project write by `agentcore.current_project_id` boundary |
| Normal IDE agents have no database credentials | PASS | live IDE configs scanned; no PostgreSQL credential markers found |
| Raw evidence cannot be updated or deleted by normal service roles | PASS | `agentcore_ingest` UPDATE and DELETE attempts failed |
| Trust, provenance, timestamps, schema version, and source identity enforced | PASS | required columns on `agentcore.evidence_events`, `agentcore.artifact_objects`, `agentcore.source_identities`; harness inserted operator-verified evidence with provenance |
| Queue, claim, lease, and dead-letter primitives recover after restart | PASS | controlled PostgreSQL 18 restart; recovery output: pending=1, dead=1, dead_letters=1, expired_leases=1, total queue=2, active claims=0 |

## Migration / Rollback Proof

- Up migration applied live and recorded in `agentcore.schema_migrations`: `m2.001`.
- Down migration `migrations/m2/001_down_canonical_identity_immutable_evidence.sql` was tested in a disposable PostgreSQL 18 database by the harness: up created `agentcore` schema; down removed it; database dropped.
- Rollback is versioned and reversible at the migration boundary. Live rollback remains operator-gated because it drops the M2 `agentcore` schema.

## PostgreSQL Authorization Boundary

`pg_hba.conf` controls authentication only. M2 authorization is enforced with SQL:

- `GRANT` / `REVOKE`
- row-level security policies on project-scoped tables
- `agentcore.assert_project_scope(uuid)`
- governed `SECURITY DEFINER` operations such as `agentcore.append_evidence_event`, `agentcore.enqueue_work`, `agentcore.claim_work`, and `agentcore.create_capability_lease`

The cross-project write rejection is operational in M2 itself and is not deferred to the future M4 gateway.

## Queue Restart Recovery Proof

`audits/M2/queue-restart-recovery-output.txt`:

```text
1|1|1              -- recover_expired_work(): recovered_pending=1, moved_to_dead=1, expired_leases=1
pending|1
dead|1
1                  -- one dead-letter row
expired|1
2                  -- two queue rows, no duplicates
0                  -- zero active claims after recovery
```

## Out of Scope Confirmed

- No LangGraph checkpoint tables were created (M6).
- No M3 context hierarchy or STATE projection tables were created.
- No memory gateway implementation was changed (M4).
- No Cognee tables beyond the existing empty `cognee_core` database (reserved for M5).
- Old `ai/global-memory-platform-v1` worktree was not used.
