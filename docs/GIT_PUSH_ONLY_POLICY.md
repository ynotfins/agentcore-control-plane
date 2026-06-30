# Git Remote Policy — AgentCore Working Repos

**Status:** Enforced. **Owner:** ynotfins. **Date:** 2026-06-30.

Working repos under `D:\github` use **normal GitHub `origin` remotes** for both fetch and push:

```text
origin  https://github.com/ynotfins/<repo>.git  (fetch)
origin  https://github.com/ynotfins/<repo>.git  (push)
```

This does **not** authorize autonomous remote sync. It only restores a standard remote shape so local repos can push cleanly to GitHub without the over-engineered push-only hack.

## Hard rules
- Agents must **not** run `git pull`, `git fetch`, `git merge`, or `git rebase` in these working repos unless the user explicitly asks for remote sync.
- Normal push is allowed after local review and secret/junk scan.
- Never force-push without explicit operator approval.
- Before any push, run `git status` and confirm no secrets, runtime state, or generated junk are being staged.
- Before any remote sync, ask the user.

## Read-only lookup policy
- Remote docs/lookups and safe comparison work should happen in separate read-only clones under `D:\github-readonly\<repo>`, not by pulling into the working repos under `D:\github`.
- Treat the working repos as the active implementation trees.

## Repos covered
- `agentcore-control-plane` (primary source authority)
- `swarmclaw`, `swarmrecall`, `swarmvault`, `swarmrelay`, `swarmfeed`, `swarmdock` (vendor Swarm clones)

## Practical workflow
1. Local work in `D:\github\<repo>`
2. `git status`
3. Secret/junk scan
4. Commit after review
5. `git push`

If remote synchronization is ever needed, stop and ask the user before any `pull`, `fetch`, `merge`, or `rebase`.
