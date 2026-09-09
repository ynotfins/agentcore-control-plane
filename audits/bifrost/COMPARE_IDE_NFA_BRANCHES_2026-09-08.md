# Compare IDE NFA Branches — 2026-09-08

Pointer audit only. No nfa-platform product redesign from AgentCore.

## Source

| Field | Value |
| --- | --- |
| Repo | `D:\github\nfa-platform` |
| Default remote HEAD | `origin/master` |
| Base SHA | `7882536f575fb2b1a84ecbf44d560ed318a9dec3` |
| Working checkout left on | `feat/goal-mode-complete` @ `c445f42437b791b8a847046c3c334ddf0cf3117f` (dirty local files untouched; compare branches created by SHA without checkout) |
| AgentCore worktree | undisturbed on `setup/zoo-code-qdrant-nfa-20260820` |

## Branches (pushed)

| Branch | Tip SHA | Pushed |
| --- | --- | --- |
| `compare/eigent-finish-build-20260908` | `7882536f575fb2b1a84ecbf44d560ed318a9dec3` | yes (`origin`, `-u`) |
| `compare/antigravity-finish-build-20260908` | `7882536f575fb2b1a84ecbf44d560ed318a9dec3` | yes (`origin`, `-u`) |
| `compare/zed-finish-build-20260908` | `7882536f575fb2b1a84ecbf44d560ed318a9dec3` | yes (`origin`, `-u`) |

## Temporary compare-lane permission (operator 2026-09-08)

Eigent, Antigravity, and Zed are authorized as Trust Class A **comparison builders only** on their assigned nfa-platform compare branches / dedicated worktrees:

- Write only inside the assigned nfa-platform worktree on the assigned `compare/*` branch
- One write-capable session per worktree
- Antigravity may use `agentcore-gateway` via process-attested `http://127.0.0.1:18082/mcp` (no materialized VK)
- Eigent/Zed: do **not** paste/materialize `BIFROST_MCP_VIRTUAL_KEY`; if gateway needed and enrollment is unverified, stop and propose a credential-free path
- No authority over Bifrost desired-state on `agentcore-control-plane` (Cursor owns that plane)
- No `H:\` Swarm; follow nfa-platform DB/alert boundaries (no freelance PG18 DDL)
- After comparison, operator decides merge/discard

## IDE fetch note

IDEs should fetch from `D:\github\nfa-platform` `compare/*` branches (or their dedicated worktrees of those branches). Bootstrap prompts for the three IDEs are owned by the nfa-platform agent — not invented here.

## Eigent / Zed gateway blockers (known)

- Eigent and Zed must not materialize `BIFROST_MCP_VIRTUAL_KEY`
- If their gateway enrollment is unverified, they must stop and propose a credential-free path rather than pasting a VK
- Antigravity path: process-attested `:18082` only
