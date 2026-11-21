# Git Remote Policy — AgentCore Working Repos

**Status:** Enforced. **Owner:** ynotfins. **Date:** 2026-06-30. **Updated:** 2026-11-21 (operator
decision — commit, push, open PR, and merge after every completed task; supersedes the push-only
end state below). See `AGENTS.md` §Git policy and the global `010-end-of-task-integration` rule for
the current authoritative wording; this document still governs remote shape and secret/junk hygiene.

Working repos under `D:\github` use **normal GitHub `origin` remotes** for both fetch and push:

```text
origin  https://github.com/ynotfins/<repo>.git  (fetch)
origin  https://github.com/ynotfins/<repo>.git  (push)
```

This does **not** authorize autonomous remote sync. It only restores a standard remote shape so local repos can push cleanly to GitHub without the over-engineered push-only hack.

## Hard rules
- `git fetch` and `git pull --ff-only` are allowed so the working branch does not drift; other
  remote-update forms (merge, rebase, non-ff pull) still require the operator to ask.
- Commit, push, open the PR, and merge it after every completed task slice or Milestone once
  validators are green and no reviewer has blocked it (operator decision 2026-11-21). A PR bot will
  take over merge duty later; until the operator says it is live, the implementing agent merges its
  own green PR.
- Never force-push without explicit operator approval.
- Before any push: run `git status`, run a secret/junk scan, stage only intended source-controlled files.

## Read-only lookup policy
- Remote docs/lookups and safe comparison work should happen in separate read-only clones under `D:\github-readonly\<repo>`, not by pulling into the working repos under `D:\github`.
- Treat the working repos as the active implementation trees.

## Repos covered
- `agentcore-control-plane` (primary source authority)
- `swarmclaw`, `swarmrecall`, `swarmvault`, `swarmrelay`, `swarmfeed`, `swarmdock` (vendor Swarm clones)

## Practical workflow — commit, push, PR, merge after every completed task
1. Local work on a task branch in `D:\github\<repo>` (`git fetch` / `git pull --ff-only` first if the
   branch needs to catch up with `origin`).
2. Run the narrowest relevant validation.
3. `git status --short`
4. Secret/junk scan — never stage live secret-bearing configs, rendered PAT URLs, DB dumps, caches, node_modules, runtime artifacts, Docker inspect output with secrets, `.env` files, or `F:\AgentCore` runtime state.
5. Stage only intended source-controlled files.
6. Commit with a concise task-specific message.
7. `git push` the task branch, open the PR, and merge it once validators are green and no reviewer has blocked it.

**Completed task** means: all requested changes are done and validated, OR the task is blocked and a blocker report with exact next commands was written to source control.

If the task changes only live runtime state or live IDE configs (no source-controlled files), create an evidence report under `artifacts/task-runs/` or `artifacts/rollout-*/` documenting what changed, backup path, validation result, rollback path, and that secrets were not printed — then commit, push, and merge that report through the same PR flow.

If there are no source-controlled changes and no runtime/live-config changes, report "no source-controlled delta; no push required" and do not create an empty commit.

If remote synchronization beyond `fetch` / `pull --ff-only` is ever needed, stop and ask the operator before any `merge`, `rebase`, non-ff `pull`, or `git remote update`.
