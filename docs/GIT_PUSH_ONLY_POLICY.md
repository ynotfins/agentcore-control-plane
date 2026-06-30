# Git Push-Only Policy — AgentCore Working Repos

**Status:** Enforced. **Owner:** ynotfins. **Date:** 2026-06-30.

The working repos under `D:\github` (the AgentCore control plane and the vendor Swarm clones) are configured as **push-only**. This prevents an accidental `git pull`/`git fetch` from importing remote files into the live working trees on CHAOSCENTRAL.

## Hard rules
- **Never** run `git pull`, `git fetch`, `git merge`, or `git rebase` from a remote in these working repos.
- The `origin` remote has a deliberately invalid FETCH URL (`no_fetch://push-only`) and a real GitHub PUSH URL. A fetch/pull will fail by design.
- Push with `git push origin HEAD:main` (or `git push` after `push.default current`). Never force-push without explicit operator approval.
- For any future read-only clone or doc lookup, clone into a SEPARATE tree such as `D:\github-readonly\<repo>` — never into these working repos.

## Remote shape (every working repo)
```
origin  no_fetch://push-only                                   (fetch)   <- invalid by design
origin  https://github.com/ynotfins/<repo>.git                 (push)    <- real GitHub
```
Verify: `git remote -v` and `git config --get-all remote.origin.fetch` (must be empty).

## Repos covered
- `agentcore-control-plane` (primary source authority)
- `swarmclaw`, `swarmrecall`, `swarmvault`, `swarmrelay`, `swarmfeed`, `swarmdock` (vendor Swarm clones)

## Provenance note
As of 2026-06-30 the vendor working repos' `origin` no longer points at any upstream Swarm URL — a prior setup step already replaced `origin` with the push-only shape, so the original upstream clone URLs are NOT recorded in the current git config. If upstream sync is ever needed, do it in a separate read-only clone under `D:\github-readonly\` (recovering the upstream URL from the upstream project), never in these push-only working trees.

## If a push is rejected (non-fast-forward)
Do NOT fetch/pull/force here. Stop and report the exact error, local branch, and remote URL. Resolve via a separate read-only clone or explicit operator decision.
