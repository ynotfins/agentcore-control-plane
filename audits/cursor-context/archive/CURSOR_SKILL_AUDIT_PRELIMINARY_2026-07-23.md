# Preliminary Cursor Skill Audit

## Archive verification

- Archive: `cursor-rules-skills.zip`
- SHA-256: `AFE67086D258B5B80AB193D6E5EF575743B0F7BB3AEADE5C9CFF6919DE98723C`
- ZIP entries: `574`
- `SKILL.md` files in archive: `0`
- Top-level roots: `.agentcore, .agents, .codex, .context-fabric, .cursor, .depwire, .pytest_cache, .serena, automations`

**Conclusion:** the supplied ZIP contains project rules, hooks, AgentCore projections, Context Fabric runtime files, and caches, but it contains no skill definitions. A true one-by-one audit of the approximately 100 global skills reported by Cursor requires a second export from the actual global skill roots.

## Provisional audit of the known 14 Superpowers skills

| Skill | Disposition | Reason |
|---|---|---|
| `using-superpowers` | **QUARANTINE automatic invocation** | Its absolute-priority doctrine competes with AgentCore authority. Retain only after adapting it so AgentCore remains the sole governing instruction layer. |
| `brainstorming` | **KEEP, manual/on-demand** | Useful before new architecture or feature design; should not load on routine fixes. |
| `systematic-debugging` | **KEEP, use now** | Directly supports evidence-first root-cause repair. |
| `test-driven-development` | **KEEP** | Use for hook/parser regressions and status-validator invariants. |
| `verification-before-completion` | **KEEP, use now** | Prevents completion claims without fresh evidence. |
| `writing-plans` | **KEEP** | Useful for bounded plans after authority/context is clean. |
| `executing-plans` | **KEEP, enable after cleanup** | Good for sequential execution of an approved plan; not while context sources are contaminated. |
| `requesting-code-review` | **KEEP** | Useful for an explicit fresh-chat verifier handoff. |
| `receiving-code-review` | **KEEP** | Useful for rigorously applying review findings. |
| `dispatching-parallel-agents` | **KEEP but DISABLE for write work now** | Useful for independent read-only investigations; parallel writes must wait for clean context and worktree isolation. |
| `subagent-driven-development` | **KEEP but DISABLE now** | Useful after the agent-team contract and file-claim boundaries are proven. |
| `using-git-worktrees` | **KEEP, use for future parallel writes** | Required isolation mechanism for multiple write-capable agents. |
| `finishing-a-development-branch` | **KEEP** | Useful for controlled integration after tests and review. |
| `writing-skills` | **OPERATOR-ONLY / manual** | Can create persistent instruction sources; never allow automatic invocation or direct governance changes. |

## Additional named high-risk capabilities from Cursor's report

| Capability | Provisional disposition |
|---|---|
| `create-rule` | Operator-only; quarantine from automatic invocation |
| `create-hook` | Operator-only; quarantine from automatic invocation |
| `update-cursor-settings` | Operator-only; quarantine from automatic invocation |
| `.codex/skills/.system/review-agent` | Manual-only until its instructions and tool permissions are audited |
| Interpreter-branded skills under `.codex/skills` | Remove from Cursor discovery or manual-only unless a current Cursor workflow explicitly needs them |

## Required second export

Collect each complete skill directory containing a `SKILL.md` from:

- `C:\Users\ynotf\.cursor\skills-cursor`
- `C:\Users\ynotf\.cursor\skills`
- `C:\Users\ynotf\.claude\skills`
- `C:\Users\ynotf\.codex\skills`
- `C:\Users\ynotf\.agents\skills`
- Cursor plugin/extension directories that contain `SKILL.md`

The export must include the skill's Markdown, scripts, references, manifests, and hook/config files, while excluding secrets, caches, databases, `node_modules`, and binaries.
