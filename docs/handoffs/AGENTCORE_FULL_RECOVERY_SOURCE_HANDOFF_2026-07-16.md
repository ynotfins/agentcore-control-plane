# AgentCore Full-Recovery Source Handoff — 2026-07-16

## Status

Source implementation and disposable acceptance are complete. Live PostgreSQL/Bifrost rollout was
not authorized and was not performed.

## Binding interpretation

`BLUEPRINT.md` remains the locked architecture authority. AgentCore is model-limit-aware active
context over an effectively unbounded durable local project history:

- model limits bound one request, never durable storage or retention;
- one million tokens is a supported active-context profile, not a memory ceiling;
- compaction never overwrites or deletes canonical originals;
- complete history is recovered through stable bounded pages plus exact source expansion;
- PostgreSQL metadata remains searchable after hot artifacts move from H: to E:.

## Implemented source changes

- Copier source parsing now uses explicit `.jinja` suffixes for all Jinja-bearing files in both
  governed templates. Generated projects pass TOML/build/lint/type/test/security admission.
- `contracts/model-context-profiles.json` defines small, standard, large, exact one-million, and
  future above-one-million capability profiles with all required reserves and provenance.
- M3.002 adds model profiles, versioned summary correction, auditable recovery operations,
  governed project snapshot metadata, and self-enrolled session context profiles.
- Recovery and snapshot tables enforce project isolation with RLS plus same-project relationship
  validation; summary creation is concurrency-idempotent.
- The existing ten-tool `agentcore-memory` surface is unchanged:
  - `retrieve_context` adds bounded recovery modes and HMAC-authenticated keyset cursors;
  - `expand_source` adds project-scoped exact event/summary/artifact expansion and byte paging;
  - `build_handoff` reconstructs identity, projections, snapshots, active context, and chronology;
  - `session_open` records verified project/Git/client/model/profile identity.
- Current-state handoffs start from the newest accepted evidence, large-artifact retries preserve
  the original event/artifact edge, and pre-M3.002 tool compatibility remains additive.
- Canonical recovery and non-destructive compaction rules are rendered to all eight managed IDE
  profiles.
- `MASTER_CONFIG_AND_PROMPT.md`, the memory execution plan, retention policy, Engineering
  Constitution, install prompt, AGENTS contract, registry, and migration index are aligned.

## Validation

See `audits/M3/M3-002-FULL-RECOVERY-VALIDATION.md`.

Key results:

- deterministic recovery suite: PASS (23);
- contract/renderer suite: PASS (111);
- all IDE renderings current: PASS;
- M3.002 UP/DOWN in disposable PostgreSQL: PASS;
- source history above one million conservative tokens: PASS;
- complete stable chronology, summary correction, quarantine filtering, exact cold expansion:
  PASS;
- non-superuser RLS isolation, cross-project write rejection, concurrent summary creation, signed
  cursor rejection, artifact retry idempotency, and guarded DOWN boundary test: PASS;
- logical backup/restore event/source/summary/snapshot/recovery graph integrity: PASS.

## Continuation / rollout

1. Review and merge/push the source commit.
2. Obtain operator approval for live migration and runtime rollout.
3. Run the normal backup/restore/PITR gate.
4. Apply M3.002 through the approved PostgreSQL admin runner.
5. Deploy `agentcore-memory` 0.6.0 and the rendered Bifrost config through the scheduled-task owner.
6. Self-enroll each managed IDE with its verified provider/model/profile identity.
7. Repeat gateway-level startup, chronology pagination, exact expansion, and handoff smoke tests.
8. Append the rollout evidence through `agentcore-memory` and regenerate STATE projections; never
   hand-edit `GLOBAL_STATE.md` or project `STATE.md`.

## Rollback

Source rollback is the task commit. Database DOWN is intentionally guarded and refuses to remove
M3.002 after recovery, snapshot, or summary-correction records exist. Once live data exists,
rollback requires operator-approved data preservation/restore rather than destructive schema
removal.
