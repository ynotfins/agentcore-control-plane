# AgentCore Bifrost and Context Alignment Acceptance — 2026-08-03

**Approval:** `AUTH-2026-08-02-AGENTCORE-BIFROST-CONTEXT-ALIGNMENT`

**Status:** RELEASE CANDIDATE LIVE-PROVEN; FINAL EXACT-SHA REVIEWS PENDING

**Canonical repository:** `D:\github\agentcore-control-plane`
**Candidate parent:** `d2fcaea935b65782fc9a6837c312d5278029841f`

## Outcome

The v0.9.1 AgentCore memory and Context Engine integration is live behind the
single `agentcore-gateway` Bifrost endpoint. The release closes the identity,
session-reuse, project-boundary, recovery-write, Cursor lifecycle, router
rollback, workflow-path, ChatGPT-profile, Cherry lifecycle, and stale storage
authority findings raised by the prior independent reviews.

No OmniRoute, Hindsight, Graphify, CrewAI, alternate memory authority, raw
Swarm MCP route, second IDE gateway, or model-inference reroute was introduced.

## Governed change and rollback

- Source rollback root:
  `E:\AgentCore-Backups\agentcore-control-plane\coderabbit-remediation-20260803-025407`
- Protected pre-change `CONTEXT_BLOCK.md` SHA-256:
  `28608576671C1FA1A34D3E825D70161153EB2257A82E49709ACDA1703585A115`
- Live Bifrost configuration backup:
  `F:\AgentCore\runtime\bifrost\backups\20260803-043315`
- Canonical renderer generated the live and repository projections before a
  single scheduled-service stop/start. The scheduled task returned healthy.

## Release behavior

### Memory and context

- `agentcore-memory` reports live version `0.9.1` and status `healthy`.
- PG18 is reachable at `127.0.0.1:55433` with the accepted M2-M8 migrations.
- Cognee `1.3.0` imports successfully from its isolated native Windows venv.
- Neutral shared SwarmRecall reports HTTP 200 and database healthy; it remains
  server-side only and is not exposed as raw IDE tools.
- LangGraph remains M6-integrated with the PG18 PostgresSaver tables.
- Reopening an exact task key returned the same live session ID; startup
  context succeeded; the diagnostic session closed cleanly.
- An unsigned legacy read requesting `record_recovery=true` remained readable
  during the migration window but did not write a recovery record:
  `agentcore.recovery_operations` stayed `4396 -> 4396`.

### Bifrost and IDE surface

- Scheduled owner: `\AgentCore\AgentCore-Bifrost-Gateway`.
- Direct health: `127.0.0.1:8080/health` PASS.
- Ordinary builder profile: 57 total tools, exactly 10 memory tools, zero router
  tools, and at least three skills-hub tools.
- Cursor inventory: one foundation rule, one lifecycle skill, one MCP entry
  named `agentcore-gateway`, no shared third-party skill noise, and no Swarm MCP
  entry.
- ChatGPT virtual-key direct profile: exact 18 tools PASS on Bifrost. The
  verifier now exits nonzero when any required direct or proxy layer fails.
- Cherry lifecycle calls are exact-project and signed; machine-global router
  use was removed. Its documentation now states the true companion-only
  behavior when native hooks are unavailable.

## Verification evidence

| Gate | Result |
| --- | --- |
| AgentCore memory tests | PASS — 61 |
| Cursor lifecycle and Serena-policy tests | PASS — 31 plus 11 alias subtests |
| Workflow and project-boundary tests | PASS — 78 |
| Router, Bifrost, and Cherry tests | PASS — 32 |
| Portable Context Engine | PASS — 110 at `82450b8c3b3884d12e2e1eece22b5771484e8686` |
| Bifrost contract unit suite | PASS — 136 |
| Cursor Stage B comprehensive suite | PASS — 26/26, including 100 protocol iterations and deterministic LangGraph fixture |
| Contract, authority-lock, ecosystem-separation, IDE-scope, prompt-format, compile, and whitespace validators | PASS |
| Live Bifrost status | PASS — 57 total / 10 memory / 0 router / skills-hub >= 3 |
| Live memory status | PASS — v0.9.1 healthy |
| Live signed open/reopen/context/close | PASS |
| Live unsigned recovery-write suppression | PASS |

Sequential Thinking was successfully used through `agentcore-gateway` for the
architecture/security boundary. Serena was not silently bypassed: the ordinary
builder profile intentionally exposes zero router tools, so project activation
and Serena wrapper calls were unavailable in this session.

## Independent review

- CodeRabbit committed-diff review of `663eb4f` completed with 12 findings. All
  were reproduced and closed with focused regression tests: worktree creation
  ordering, rollback state-write handling, exact Windows test paths, safe
  PowerShell option/redirect parsing, contract-validator coupling, enrolled
  device override, empty-router-profile rejection, signed bootstrap evidence,
  routing wording, Cherry enrollment stop, and pending-evidence wording. A
  fresh review of `544f520` found one additional critical single-pipe shell
  composition gap; it was reproduced and closed with fail-closed parsing and a
  regression test. The next review found two additional affected-path gaps:
  common PowerShell/cmd aliases and source/wildcard authority classification.
  Both were reproduced and closed by returning every affected path, expanding
  globs before classification, and fail-closing incomplete path sets. A final
  clean review remains required.
- Cursor GPT-5.6 Sol exact-SHA control-plane review: **PENDING FINAL COMMIT**.
- Cursor GPT-5.6 Sol exact-SHA portable Context Engine review: **PENDING**.

No final acceptance claim is permitted until the pending reviews are recorded
and every material correctness or security finding is closed.

## True residuals

1. Device enforcement remains `legacy_compat` until the approved migration
   window ends on 2026-08-09. Writes are signed; unsigned reads remain possible,
   but cannot create recovery-ledger writes.
2. The ChatGPT compatibility proxy on `127.0.0.1:18081` is down and has no
   governed scheduled lifecycle owner. Direct Bifrost health and its exact
   18-tool ChatGPT profile pass. This release does not start an unmanaged proxy
   or hide the failure.
3. Generic MCP-only clients remain companion-only for automatic lifecycle;
   automatic rolling context requires a certified native hook/plugin/bridge.
4. `agentcore.wf_runs.completed_at` may remain null while status is completed;
   status is authoritative.
5. RUN11 used the project root rather than its intended isolated worktree.
6. Context Fabric retains six historical failed captures and reports false
   Windows drift under `core.autocrlf=true`; its repo-local database integrity,
   hook readiness, and capture/query functions remain usable.
7. Twelve inherited secret-like backup files remain outside this task and need
   separate operator approval. Inherited Langfuse/M6-M8 work remains unstaged.

## Final release record

- Control-plane final commit: **PENDING**
- Final pushed branch: `origin/main` **PENDING**
- Final Context Fabric capture: **PENDING**
