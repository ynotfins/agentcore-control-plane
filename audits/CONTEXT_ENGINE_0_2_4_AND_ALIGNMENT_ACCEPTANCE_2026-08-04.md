# Context Engine v0.2.4 and Alignment Acceptance

**Date:** 2026-08-04
**Approval:** `AUTH-2026-08-04-CONTEXT_ENGINE_024_CERT`
**Architecture authority:** `BLUEPRINT.md` (unchanged)
**Scope:** Context Engine exact release, governed alignment skill, and AgentCore LangGraph CE024 production canary

## Decision

Context Engine v0.2.4 and its AgentCore LangGraph integration pass the release
and controlled-production canary gates. This does not certify SwarmClaw, every
IDE's native skill discovery, PG18 reboot ownership, or neutral Recall
global/project pool isolation.

## Exact release identity

| Item | Accepted value |
| --- | --- |
| Context Engine repository commit | `789b42a12e55a98e71327a8ce6c49f30320f2143` |
| Core wheel | `agentcore_context_engine-0.2.4-py3-none-any.whl` |
| Core wheel SHA-256 | `7d1601211014b1e76c24f84ca79488c3f17ef5b963c0c093cb09742fd66804dd` |
| Host adapters wheel | `agentcore_context_host_adapters-0.2.4-py3-none-any.whl` |
| Host adapters SHA-256 | `eea046dd985a6ec5373c6f9e6150ed20a59550459948de6400448f259c74cf4d` |
| Release manifest SHA-256 | `cce767fae6bc52c922bb4b5df8b7da98c1c868e63a302740c251f04ad79f3753` |
| Alignment skill SHA-256 | `3de60a3b0e892f2b335fb980f8f8285f717d2cb624217e4148b7ccc5939943d1` |
| Topology fingerprint | `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` |

Rebuilding both wheels from immutable Git bytes reproduced the accepted bytes
and hashes. Same-second Windows installation rollback allocation produced
distinct `...\<timestamp>\installation.json` and
`...\<timestamp>-001\installation.json` paths.

## Verification

- Context Engine: 127 tests passed; Ruff and mypy passed.
- Exact wheels installed into system Python, the Context Engine venv, and the
  control-plane `scripts\.venv` runtime.
- `agentcore-context validate --live` returned `ok=true`, gateway
  `v2.0.0-prerelease1`, memory `0.9.1`, exact ten memory tools, and tool-surface
  SHA-256 `cbde93af6fc11181af068dd0bc514767618a6d27a4fdbb8135f0be4db4d8b42a`.
- Cursor, Codex, Claude Code, and generic-MCP host manifests report v0.2.4.
- Signed companion lifecycle opened, hydrated, appended idempotently,
  checkpointed, built a handoff, and closed without degradation.
- AgentCore workflow suite: 105 tests passed after fail-closed critic,
  super-step budget, and immutable-requirement regressions were added.

## Production canary

| Field | Evidence |
| --- | --- |
| Run | `cdb3a8ae-346e-4798-9477-fcee962280f6` |
| Thread | `1af1a09d-8b9b-4cf0-bfa8-01e42b1eb7a5` |
| Project / milestone | `agentcore-context-engine` / `CE024` |
| Worker | `gemini:gemini-3.6-flash` |
| Isolated worktree | `D:\agentcore-worktrees\agentcore-context-engine` |
| Changed path | `runtime_probe.txt` only |
| Exact bytes before cleanup | `4F4B0A` (`OK\n`); 3 bytes; SHA-256 `a12b7cb43c9d9134b5bb1b35e9096b66775d9e92e7611d1cc92b02edd6782a87` |
| Builder | `status=completed`, 7,584 ms; system-verified artifact manifest persisted |
| Independent critic | `status=completed`, `passed=true`, score `1.0`, 9,277 ms |
| Final | `status=completed`, `completed_at` populated, score `1.0`, errors `[]` |
| Checkpoints | 13 in PG18 PostgresSaver |

The canary's durable `runtime_attestation` names Context Engine v0.2.4, both
wheel hashes, release-manifest hash, control-plane commit
`8afd852aba86165edc9b8f55d88b3caa7a092f53`, the repo-owned Python runtime, and
the locked topology fingerprint. The canary artifact was removed after its
bytes and durable evidence were verified; the assigned worktree is clean.

## Fail-closed defects found and closed

1. A critic `GraphRecursionError` was previously scored as advisory and allowed
   a false workflow success. Critic runtime failure now always blocks.
2. LangGraph `recursion_limit` counts graph super-steps, not model iterations.
   The bounded worker profile now permits 12 agent iterations / 97 super-steps
   while retaining the independent 180-second worker timeout.
3. Sentence splitting detached constraints from the operator goal. Plain prose
   now remains one atomic requirement, and the immutable goal/acceptance
   contract is supplied to both builder and independent critic.
4. An intermediate run returned `completed` while producing the wrong bytes.
   It was rejected; the replacement canary proves exact bytes and independent
   criterion verification.
5. Malformed/non-JSON critic output previously defaulted to pass. The critic
   now requires a boolean `passed`, bounded numeric `score`, and string-list
   `findings`; parse or schema failure returns a failed worker result.

## Alignment skill disposition

The canonical skill is `skills/agentcore-project-lifecycle/`. Native copies for
Cursor, Codex, Claude Code, and MiniMax are hash-matched. Mavis shares the
MiniMax data root. Other managed IDEs use governed rule/prompt adapters until
native discovery exists. These native copies remain `installed_unverified`
until a fresh task proves discovery. LangGraph consumed the hash-pinned skill
capsule. SwarmClaw deliberately received no AgentCore skill; its equivalent is
a separate Swarm-owned deliverable.

## Residuals outside this acceptance

1. Reconcile PG18 to one governed reboot/service owner.
2. Prove neutral Recall global/project pool isolation and projection `pool_id`.
3. Complete per-host fresh-task skill discovery evidence.
4. Build and certify the separate SwarmClaw adapter and autonomous canary.
5. Keep unsigned reads under `legacy_compat` only for the approved migration
   window; signed writes remain enforced.
6. Treat DeepSeek v4 Flash as unqualified for this exact Deep Agents task until
   a bounded model-behavior canary passes. Gemini 3.6 Flash is the proven path.

## Rollback

- Protected-document copies:
  `E:\AgentCore-Backups\authority-unlock-AUTH-2026-08-04-CONTEXT_ENGINE_024_CERT\20260804-074021`.
- Context Engine source backups:
  `E:\AgentCore-Backups\context-engine-0.2.4-source\20260804-064700`.
- Restore exact prior files only after validating the target path and rerun the
  release, gateway, workflow, and authority validators.

## Independent review

PASS. A fresh-context read-only reviewer independently verified the strict
critic failure path, 105-test workflow suite, system-verified 3-byte artifact
manifest and clean canary worktree, 11-test current-document validator,
Context Engine release identity, unchanged `BLUEPRINT.md`, honest host status,
and exclusion of unrelated inherited WIP. No review mutations were made.
