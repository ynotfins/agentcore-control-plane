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
| Context Engine | Exact v0.2.4 wheels installed; `agentcore-context validate --live` passed against gateway `v2.0.0-prerelease1`, memory `0.9.1`, and the exact ten-tool facade |
| Workflow tests | 105 workflow unit/boundary tests passed on 2026-08-04 |
| Current production proof | Run `cdb3a8ae-346e-4798-9477-fcee962280f6`, thread `1af1a09d-8b9b-4cf0-bfa8-01e42b1eb7a5`: one atomic CE024 micro, exact `OK\n` bytes durably attested as 3 bytes / SHA-256 `a12b7cb43c9d9134b5bb1b35e9096b66775d9e92e7611d1cc92b02edd6782a87`, strict-schema critic pass, score 1.0, 13 PostgresSaver checkpoints |

Mutable aggregate tool counts are intentionally omitted. Use the authenticated
gateway status probe instead of copying a count from this file.

## 3. Current release and launch gates

Context Engine v0.2.4 release and live-integration gates passed:

- final source/artifact commit `789b42a12e55a98e71327a8ce6c49f30320f2143`;
- exact core wheel SHA-256 `7d1601211014b1e76c24f84ca79488c3f17ef5b963c0c093cb09742fd66804dd`;
- exact host-adapter wheel SHA-256 `eea046dd985a6ec5373c6f9e6150ed20a59550459948de6400448f259c74cf4d`;
- release-manifest SHA-256 `cce767fae6bc52c922bb4b5df8b7da98c1c868e63a302740c251f04ad79f3753`;
- 127 Context Engine tests, reproducible wheel rebuild, four-host install,
  signed companion lifecycle, and live gateway validation passed;
- LangGraph run `cdb3a8ae-346e-4798-9477-fcee962280f6` durably attested those
  artifacts and passed builder, independent critic, exact-byte acceptance,
  completion metadata, isolated-worktree enforcement, and 13 checkpoints.

The controlled first-project workflow path is certified. Fully unattended
commercial launch still requires the operational residuals in section 6 to be
accepted or closed; those residuals do not roll back the v0.2.4 release proof.

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

1. PG18 automatic service stopped while a separate process launcher owns the
   healthy database process.
2. Neutral Recall global/project pools and consistent projection `pool_id`
   wiring lack current acceptance evidence.
3. Signed writes are enforced; unsigned reads remain temporarily allowed under
   `legacy_compat` until the approved migration window closes.
4. Cursor MCP discovery can latch disconnected while direct Bifrost remains
   healthy.
5. The ChatGPT compatibility proxy at `:18081` lacks a governed lifecycle
   owner; direct Bifrost is the supported gateway health surface.
6. Context Fabric Windows drift severity is unreliable under the current CRLF
   behavior; Git objects and explicit diffs remain authoritative.
7. Native alignment-skill copies are hash-matched but remain
   `installed_unverified` until each host proves fresh-task discovery.
8. SwarmClaw still requires its separate Swarm-owned adapter/skills acceptance
   and live autonomous canary; no AgentCore skill was installed into Swarm.
9. `deepseek/deepseek-v4-flash` did not terminate reliably in the bounded Deep
   Agents file-write canary. Gemini `gemini-3.6-flash` is the currently proven
   live worker for this path; model qualification remains per model/task class.

## 7. Document classification rule

- `CONTEXT_BLOCK.md` owns current mutable readiness.
- Dated audits prove only the named release/run at the recorded time.
- `audits/CONTEXT_ENGINE_FINAL_ACCEPTANCE_2026-08-02.md` is v0.2.0/RUN11
  point-in-time evidence and is superseded for release status by
  `audits/CONTEXT_ENGINE_0_2_4_AND_ALIGNMENT_ACCEPTANCE_2026-08-04.md`.
- Archived development chats, old handoffs, direct-MCP configs, PG16-era plans,
  and Swarm-first AgentCore documents are evidence only and must never be
  executed as current instructions.
- Runtime readiness must be re-probed after package, service, gateway,
  checkpoint, or host-lifecycle changes.

## 8. Immediate completion sequence

1. Reconcile PG18 to one governed lifecycle owner and prove reboot recovery.
2. Prove neutral Recall global/project pool isolation and projection identity.
3. Validate native alignment-skill discovery in each supported host.
4. Build and validate the separate Swarm-owned SwarmClaw adapter and run its
   first autonomous canary.
5. Start the first governed AgentCore project with an explicit goal and
   acceptance file; use Gemini Flash until another worker model is qualified.

Current reconciliation evidence:
`audits/AGENTCORE_LANGGRAPH_AUTHORITY_RECONCILIATION_2026-08-04.md`.
Current release/canary evidence:
`audits/CONTEXT_ENGINE_0_2_4_AND_ALIGNMENT_ACCEPTANCE_2026-08-04.md`.
