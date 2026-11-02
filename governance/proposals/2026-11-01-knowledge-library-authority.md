# Proposal: lock the knowledge-library laws and point every agent at them

**Date:** 2026-11-01  
**Status:** applied 2026-11-01 after operator UNLOCK. Four laws added to `operator_locked`. Pointers landed in `DOC_AUTHORITY.md`, `AGENTS.md`, `contracts/global-agent-policy.yaml`, and `DOCUMENTATION_READ_ORDER.md`.  
**Approval:** `AUTH-2026-11-01-KNOWLEDGE-LIBRARY-AUTHORITY`

## Already written (normal workstream — no UNLOCK)

- `docs/knowledge-library/LIBRARY_CONSTITUTION.md`
- `docs/knowledge-library/AGENT_USE_LAW.md`
- `docs/knowledge-library/PROMOTION_AND_TRUST.md`
- `docs/knowledge-library/LIBRARY_AGENT_CHARTER.md`
- `docs/prompts/library-agent-goal-mode.md`
- `.cursor/rules/knowledge-library-first.mdc`

These exist in worktree `D:\agentcore-worktrees\agentcore-control-plane\knowledge-library-gov`. They are **not yet operator-locked**.

## Why these locked files must change

The new laws cannot become the authority chain, and cannot appear in the lock manifest, until the files below are unlocked. Ordinary agents will still see the Cursor rule after this PR merges; they will not see the laws in `DOC_AUTHORITY.md` / `AGENTS.md` until the unlock edits land.

## UNLOCK list (do not edit until operator pastes UNLOCK)

| File | Class today | After unlock, do this |
| --- | --- | --- |
| `contracts/authority-lock.yaml` | operator_locked | Add the four `docs/knowledge-library/*.md` law files to `operator_locked.paths`. Do not lock the prompt or the Cursor rule (those may need small wording fixes). |
| `DOC_AUTHORITY.md` | governed_mutable | Add the four laws to the attach list (minimum for any scaffold/UI/library work) and to the **Authoritative — stable** table. State that they derive from BLUEPRINT M5 and do not create a new MCP or database. |
| `AGENTS.md` | governed_mutable | Under Tool Routing / Docs: after Arabold, require `docs_search` / `retrieve_context` with `framework` + `asset_type` before scaffolding the enrolled frameworks. Point at the four laws. |
| `contracts/global-agent-policy.yaml` | governed_mutable | Add a hardcoded rule sibling to `arabold-docs`: operator corpus query is mandatory before boilerplate/scaffold work; Arabold remains the official-version plane. |
| `docs/agent-policy/DOCUMENTATION_READ_ORDER.md` | governed_mutable | After Arabold (step 13), add: for Flutter/Android/Refine/Next.js/React/FastAPI structure, query the knowledge library before implementation files. |

## Do not unlock

| File | Why |
| --- | --- |
| `PROJECT_ANCHOR.md` | The library is M5 hybrid retrieval through the existing `docs_search` / `retrieve_context` tools. It is not a new memory plane, drive, or MCP. |
| `BLUEPRINT.md` | M5 already says official files on E: and indexes on F:. No outcome change. |
| `AUTHORITY_LOCK.md` | It describes classes; it does not list paths. |
| `CONTEXT_BLOCK.md` | Live counts/SHAs must not be frozen as law. |

## Independent review / validators (after UNLOCK edits)

- `python scripts/validate_authority_lock.py`
- `python scripts/bifrost/validate_contracts.py`
- `python scripts/validate_cursor_prompt_format.py MASTER_CONFIG_AND_PROMPT.md` (only if that file is touched — it should not be)
- Documentation guard ACCEPT on each unlocked file
- External rollback copies + before/after hashes

## Non-goals

- No new MCP tool
- No live DDL
- No catalog remote changes in the unlock PR
- No raven checkout cleanup
