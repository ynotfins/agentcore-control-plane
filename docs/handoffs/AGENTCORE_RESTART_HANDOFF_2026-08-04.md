# AgentCore Restart Handoff — 2026-08-04

**Classification:** Point-in-time restart evidence. Current architecture remains
`PROJECT_ANCHOR.md` → `DOC_AUTHORITY.md` → `BLUEPRINT.md` → `CONTEXT_BLOCK.md`.

## Restart decision

The workstation is safe to restart after this handoff is committed and pushed.
Completed Context Engine, alignment-skill, and LangGraph work is durable in Git
and canonical AgentCore memory. Unrelated inherited working-tree files remain
intentionally unstaged and must not be discarded, stashed, or absorbed without
separate provenance review.

## Durable accepted state

| Scope | Durable state before this handoff |
| --- | --- |
| AgentCore control plane | `main` at `632242554c4c9263fbd676029742f65b9113bc37`; `origin/main` matched 0 behind / 0 ahead |
| Context Engine | `main` at `789b42a12e55a98e71327a8ce6c49f30320f2143`; `origin/main` matched 0 behind / 0 ahead; only `.agentcore/runtime/` remained local |
| SwarmClaw vendor repo | `local/swarm-ecosystem-s5` at `b28f558b11fe42ef97df629e3092f28d86d43578`; configured upstream matched 0 behind / 0 ahead |
| Swarm control plane | `master` at `e4cc151ee32af03327cfbecf323d488436360d91`; no Git upstream configured; unrelated local security-audit scripts remain untracked |
| Context Engine runtime | Core and host-adapter distributions both exact-installed at `0.2.4` in the control-plane venv |
| Production canary | Run `cdb3a8ae-346e-4798-9477-fcee962280f6`; thread `1af1a09d-8b9b-4cf0-bfa8-01e42b1eb7a5`; completed, score 1.0, 13 checkpoints |

Authoritative acceptance evidence:
`audits/CONTEXT_ENGINE_0_2_4_AND_ALIGNMENT_ACCEPTANCE_2026-08-04.md`.

## Pre-restart runtime proof

- `agentcore-memory` `0.9.1`: healthy; canonical PG18 reachable; Cognee
  available; neutral shared Recall healthy; LangGraph M6 integrated.
- Bifrost `http://127.0.0.1:8080/health`: HTTP 200.
- AgentCore PG18 `127.0.0.1:55433`: listening from
  `F:\PostgreSQL18\data`.
- Neutral/Swarm services: PostgreSQL `:65432`, Meilisearch `:7700`, Recall API
  `:3300`, Recall Web `:3400`, and SwarmClaw `:3456` listening on loopback;
  Recall, Meilisearch, and SwarmClaw health endpoints returned HTTP 200.
- SwarmVault viewer `:4123` was down, which is the accepted on-demand baseline.
- AgentCore nightly backup and restore-test scheduled tasks last returned 0 on
  2026-08-04.

## Reboot ownership

- Bifrost: enabled logon task `\AgentCore\AgentCore-Bifrost-Gateway`, restart
  interval one minute, continuous retry, `StartWhenAvailable=true`.
- PG18: Automatic service `AgentCore-PostgreSQL18` and logon guard
  `\AgentCore\PostgresRuntime` both target the same
  `F:\PostgreSQL18\data`. The guard checks `pg_ctl status` and starts only when
  stopped. This makes restart recoverable, but the duplicate lifecycle-owner
  condition remains a hardening residual and must be reconciled separately.
- Neutral Recall and SwarmClaw: the Swarm-owned Startup-folder launcher
  `Swarm Stack.cmd` exists and calls
  `D:\github\swarm-ecosystem-control\scripts\start-swarm.ps1`.
- The historical AgentCore-owned Recall scheduled tasks remain disabled and
  must not be re-enabled.

## Preserved local work

The control-plane contains inherited unstaged/untracked Langfuse, M6–M8
generated audit, Bifrost registry/schema, IDE-profile, dependency, skill-cache,
and local evidence files. They are saved on disk but are not part of the
accepted Context Engine task and are intentionally not pushed. Run
`git status --short` before touching them after reboot.

The Context Engine repository contains only local rebuildable
`.agentcore/runtime/` state outside Git. The accepted source is fully pushed.

## Post-login acceptance

Wait up to 90 seconds after login, then run:

```powershell
Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8080/health
Test-NetConnection 127.0.0.1 -Port 55433
& 'D:\github\agentcore-control-plane\scripts\.venv\Scripts\agentcore-context.exe' validate --live
Set-Location 'D:\github\swarm-ecosystem-control'
& '.\scripts\status-swarm.ps1'
git -C 'D:\github\agentcore-control-plane' status --short --branch
git -C 'D:\github\agentcore-context-engine' status --short --branch
```

Acceptance requires Bifrost health 200, PG18 reachable, Context Engine live
validation `ok=true` with ten memory tools, Swarm's accepted health matrix, and
no loss or silent staging of inherited working-tree files.

If AgentCore services are not ready, use the repo-owned lifecycle owners only;
do not start replacement terminals or enable the historical Recall tasks. If
Swarm is not ready, use its `scripts\start-swarm.ps1` from the Swarm control
plane and keep AgentCore environment variables stripped as that script defines.

## Security follow-up

The Swarm Meilisearch credential is currently supplied on its process command
line. Its value is intentionally excluded from this handoff. Moving it to a
non-command-line mechanism and rotating it requires separate Swarm-owned
approval and is not a restart blocker.
