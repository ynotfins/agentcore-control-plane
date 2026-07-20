# Inherited WIP Disposition — 2026-07-20

**Purpose:** Record the operator-facing disposition decision for dirty working-tree items left after `794d972` docs reconcile.  
**Authority:** Does not change architecture. Complements `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md`.  
**Decision date:** 2026-07-20  
**Decision:** **Keep WIP separate from authority/documentation commits.** Do not mix Studio-interrupt or Cherry experimental tooling into the reconstruction/archive commit set.

---

## Classification

| Path | Class | Disposition |
| --- | --- | --- |
| `scripts/agentcore/workflow_cli.py` (modified) | Studio/workflow WIP | **Hold** — finish or discard in a dedicated Studio-interrupt task; do not commit with authority docs |
| `scripts/agentcore_memory/server.py` (modified) | Memory server WIP | **Hold** — review diff before any commit; may be related to interrupt/accept work |
| `scripts/agentcore_workflow/deepagents_worker.py` (modified) | Deep Agents worker WIP | **Hold** — large diff; finish/validate in dedicated task |
| `scripts/agentcore/studio_interrupt_accept.py` | New WIP tool | **Hold** with Studio-interrupt task |
| `audits/M6/studio-interrupt-accept.json` / `.log` | WIP evidence | **Hold** — commit only with Studio-interrupt closeout |
| `docs/CHERRY_NEWAPI_INTEGRATION.md` | Cherry WIP docs | **Hold** — separate Cherry/provider task |
| `renderers/gateway-clients/cherry-studio.json` | Cherry renderer WIP | **Hold** — validate against enroll path before commit |
| `scripts/cherry/inject_cherry_*.js`, `setup_cherry_providers.py` | Cherry tooling WIP | **Hold** — experimental; enroll path uses tracked `enroll_agentcore_gateway.py` |
| `scripts/cherry/_node_workspace/` | Scratch / node_modules | **Do not commit** |
| `scripts/_scratch/` | Scratch | **Do not commit** |
| `scripts/uv.lock` | Lockfile at scripts root | **Do not commit** unless a deliberate packaging decision is made |
| `docs/operations/archive/**` (chat + handoffs archive) | Historical evidence | **Commit candidate** with reconstruction docs |
| `docs/current/CURRENT_PROJECT_RECONSTRUCTION.md` | Synthesis | **Commit candidate** with authority reconciliation |

---

## Rationale

1. Memory L0 on `794d972` already recorded these script diffs as intentionally left uncommitted.
2. Authority reconstruction must not silently productize unfinished Studio-interrupt or Cherry NewAPI work.
3. Scratch and `node_modules` trees must stay out of Git (secrets/junk/size risk).

---

## Next actions (separate tasks)

1. **Studio interrupt:** Review the three modified scripts + accept artifacts; run acceptance; commit as one feature commit or discard.
2. **Cherry providers/NewAPI:** Decide whether inject scripts become governed tooling or remain local-only; enroll path remains `scripts/cherry/enroll_agentcore_gateway.py`.
3. **Authority/archive:** Commit reconstruction + DOC_AUTHORITY + archived chat/handoffs when the operator requests a git commit.
