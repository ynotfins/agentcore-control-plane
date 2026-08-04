# Current AgentCore Project Reconstruction

**Document type:** Current evidence synthesis; not architecture authority
**Verified:** 2026-08-04
**Approval:** `AUTH-2026-08-04-AGENTCORE-LANGGRAPH-DOC-RECONCILIATION`
**Repository:** `D:\github\agentcore-control-plane`

This file reconstructs the live AgentCore/LangGraph posture without promoting
point-in-time audits into permanent truth. The authority order remains:

```text
PROJECT_ANCHOR.md
  -> DOC_AUTHORITY.md
  -> BLUEPRINT.md
  -> CONTEXT_BLOCK.md
  -> docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md
  -> current contracts and runbooks
  -> live probes and dated audits
```

When this synthesis conflicts with `CONTEXT_BLOCK.md` or a newer live probe,
the newer evidence wins and this file must be updated or reclassified.

## 1. Stable architecture

```text
AgentCore / enrolled non-Swarm IDE or workflow
  -> agentcore-gateway / Bifrost :8080
  -> agentcore-memory (exact ten-tool facade)
       -> PG18 :55433 (canonical exact evidence, identity, policy, checkpoints)
       -> Cognee (optional curated graph adapter)
       -> neutral SwarmRecall :3300 (non-canonical semantic projection)
  -> portable Context Engine (rolling context and host lifecycle orchestration)

LangGraph production
  -> PG18 PostgresSaver public.checkpoints/checkpoint_blobs/checkpoint_writes

LangGraph Studio
  -> localhost :2024, disposable Agent Server dev checkpointer
  -> never production thread IDs
```

Bifrost owns MCP aggregation/governance. AgentCore owns canonical truth and
recovery. The Context Engine owns rolling-context orchestration. Neutral Recall
owns semantic projections. LangGraph owns the AgentCore autonomous workflow.
No ordinary IDE receives raw Recall or database credentials.

## 2. Current live evidence

| Surface | Verified fact |
| --- | --- |
| Bifrost | Native runtime at `F:\AgentCore\runtime\bifrost`; `/health` returned 200; scheduled gateway owner running |
| AgentCore memory | `0.9.1`, status `healthy`, exact ten-tool facade retained |
| PG18 | Reachable at `127.0.0.1:55433`; canonical `agent_core` and production checkpoints live on `F:\PostgreSQL18\data` |
| Cognee | `1.3.0`, available through its isolated native Windows environment |
| Neutral Recall | API/database health passed at `127.0.0.1:3300`; server-side projection only |
| LangGraph | Locked 15-node topology fingerprint `a86e40e8ddd0a370498bf75d612cfda9b8c18eb7c5f178000ba1fe61db94ae32` |
| Workflow tests | 88 workflow unit/boundary tests passed on 2026-08-04 |
| Last production proof | RUN11 completed with 23 PostgresSaver checkpoints; this remains point-in-time evidence, not current release recertification |

Mutable aggregate tool counts are intentionally omitted. Use the authenticated
gateway status probe instead of copying a count from this file.

## 3. Current release and launch gates

The Context Engine is not currently final-certified:

- source repository is v0.2.1 release-candidate material;
- the machine-installed distribution and installation manifest still report
  v0.2.0;
- `agentcore-context validate --live` fails `engine_version`;
- the 2026-08-02 acceptance certifies the earlier v0.2.0/RUN11 snapshot only;
- v0.2.1 needs exact installation, full host/memory lifecycle proof, and an
  independent review of the exact final SHA.

LangGraph is a working live baseline but not yet cleared for the first new
commercial project. Required gates are:

1. final Context Engine v0.2.1 acceptance;
2. one governed PG18 lifecycle owner and reboot/restart proof;
3. a new post-v0.2.1 production canary;
4. worktree-path enforcement and `wf_runs.completed_at` metadata repair or
   explicit residual acceptance;
5. live neutral Recall pool/project-isolation proof.

## 4. Supported operator runtime

The reproducible operator runtime is:

```text
D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe
```

Create or repair it with:

```powershell
& 'D:\github\agentcore-control-plane\scripts\bootstrap-runtime.ps1'
```

Run workflow commands from `D:\github\agentcore-control-plane\scripts`:

```powershell
$AgentCorePython = 'D:\github\agentcore-control-plane\scripts\.venv\Scripts\python.exe'
Set-Location 'D:\github\agentcore-control-plane\scripts'
& $AgentCorePython -m agentcore workflow topology --json
```

Bare system Python is a bootstrap source or explicit diagnostic fallback. It
is not the production operator contract.

## 5. Drive and ecosystem ownership

| Location | Owner / role |
| --- | --- |
| `D:\github\agentcore-control-plane` | AgentCore source/config authority |
| `F:\AgentCore\...` | AgentCore hot runtime |
| `F:\PostgreSQL18\data` | AgentCore canonical PG18 data/checkpoints |
| `E:\AgentCore\...` | AgentCore cold/archive/backup namespace |
| `I:` | AgentCore disposable staging only |
| `H:\SwarmData\recall` | Physical neutral Recall data; AgentCore has no filesystem authority there |
| Other `H:\SwarmData\...` | Swarm execution/runtime state; forbidden to AgentCore normal operations |
| `E:\Swarm\...` | Swarm cold/backup namespace |

AgentCore and Swarm share only the neutral Recall service through bounded,
separate adapters. They do not share workflow state, exact evidence, databases,
credentials, checkpoints, schedules, or authority.

## 6. Current known residuals

1. Context Engine source/install version mismatch.
2. PG18 automatic service stopped while a separate process launcher owns the
   healthy database process.
3. Neutral Recall global/project pools and consistent projection `pool_id`
   wiring lack current acceptance evidence.
4. `wf_runs.completed_at` may be null for a completed run.
5. RUN11 used the project root rather than the intended isolated worktree.
6. Signed writes are enforced; unsigned reads remain temporarily allowed under
   `legacy_compat` until the approved migration window closes.
7. Cursor MCP discovery can latch disconnected while direct Bifrost remains
   healthy.
8. The ChatGPT compatibility proxy at `:18081` lacks a governed lifecycle
   owner; direct Bifrost is the supported gateway health surface.
9. Context Fabric Windows drift severity is unreliable under the current CRLF
   behavior; Git objects and explicit diffs remain authoritative.

## 7. Document classification rule

- `CONTEXT_BLOCK.md` owns current mutable readiness.
- Dated audits prove only the named release/run at the recorded time.
- `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md` is v0.2.0/RUN11
  point-in-time evidence, not v0.2.1 acceptance.
- Archived development chats, old handoffs, direct-MCP configs, PG16-era plans,
  and Swarm-first AgentCore documents are evidence only and must never be
  executed as current instructions.
- Runtime readiness must be re-probed after package, service, gateway,
  checkpoint, or host-lifecycle changes.

## 8. Immediate completion sequence

1. Finish and independently certify Context Engine v0.2.1 in its own repo.
2. Reconcile PG18 to one governed lifecycle owner without interrupting a
   concurrent canary.
3. Prove Recall pool/project isolation.
4. Run a fresh production LangGraph canary through deterministic checks,
   critic, scorer, judge, evidence, checkpoints, memory and recovery.
5. Run validators, secret/junk scan, independent review, commit and push only
   task-owned changes.

Current reconciliation evidence:
`audits/AGENTCORE_LANGGRAPH_AUTHORITY_RECONCILIATION_2026-08-04.md`.
