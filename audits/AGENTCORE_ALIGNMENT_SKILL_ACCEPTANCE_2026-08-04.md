# AgentCore Alignment Skill Acceptance — 2026-08-04

## Verdict

**PASS — source-ready and installed-unverified on supported native hosts.**

The existing `agentcore-project-lifecycle` skill is now the single AgentCore lifecycle and tool-routing skill. It remains subordinate to `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, locked `BLUEPRINT.md`, and `CONTEXT_BLOCK.md`.

This acceptance does not claim every IDE is natively skill-capable or live-validated. Manual, UI-only, unverified, workflow, and Swarm adapters retain honest classifications in `contracts/agentcore-alignment-skill-hosts.json`.

## Delivered

- Canonical progressive-disclosure skill with separate references for tool routing, memory/STATE, project gates, and host/runtime adapters.
- Exact task gates for sequential-thinking, Arabold Docs, Serena, Depwire, Tentra, Context Fabric, Playwright, Artiforge, Skills Hub, and AgentCore memory.
- Explicit refusal of Swarm-owned execution and prohibition on direct Recall, SQL, generated-STATE edits, shared implicit-project tooling, or a second canonical store.
- Hash-pinned LangGraph execution-catalog capsule.
- Deterministic host manifest, backup-first transactional installer, complete-instruction validator, and installer fault tests.

## Native host installation

Canonical tree SHA-256: `c4c5e4715259ecfde0a42b4981993edb6fd6eab416c4f61207984d676eae6e03`

| Host | Target | Result |
| --- | --- | --- |
| Cursor | `C:\Users\ynotf\.cursor\skills\agentcore-project-lifecycle` | `installed_unverified` |
| Codex | `C:\Users\ynotf\.agents\skills\agentcore-project-lifecycle` | `installed_unverified` |
| Claude Code | `C:\Users\ynotf\.claude\skills\agentcore-project-lifecycle` | `installed_unverified` |
| MiniMax Code | `C:\Users\ynotf\.minimax\skills\agentcore-project-lifecycle` | `installed_unverified` / empirical skill root |
| Mavis | junction to MiniMax data root | `same_data_root_no_second_copy` |

Latest replacement rollback: `E:\AgentCore-Backups\agentcore-alignment-skill\20260804T092420Z`

## Non-native and runtime adapters

- Claude Desktop, Open Interpreter, and Cherry Studio remain manual-import adapters.
- MiniMax Classic remains UI-only.
- Antigravity native rule/skill support remains unverified.
- LangGraph production and Studio consume the hash-pinned lifecycle capsule; a production canary is still required.
- SwarmClaw receives no AgentCore skill. Its equivalent adapter is Swarm-owned and must be validated under `D:\github\swarm-ecosystem-control`.

## Current vendor documentation basis

- OpenAI documents local Codex skill discovery from user and repository `.agents/skills` locations, progressive disclosure, and optional plugin distribution: <https://learn.chatgpt.com/docs/build-skills>
- Anthropic documents Claude Code user skills under `~/.claude/skills`, project skills, automatic discovery, and live change detection: <https://code.claude.com/docs/en/skills>
- Cursor documents Agent Skills as dynamic capabilities distinct from always-on Rules: <https://cursor.com/blog/agent-best-practices>

No undocumented native-skill claim was promoted for hosts outside the proven matrix.

## Verification evidence

```text
PASS agentcore alignment skill
skill_sha256=3de60a3b0e892f2b335fb980f8f8285f717d2cb624217e4148b7ccc5939943d1
hosts=13 native=4
```

```text
Ran 4 tests in 0.038s
OK
```

The four installer tests prove:

1. broadened manifest targets are refused;
2. source and backup hashes are verified;
3. failed post-swap verification restores the prior target;
4. a Windows-style cleanup lock cannot prevent prior restoration.

Additional checks passed:

- Python compile checks for installer, validator, and tests.
- Bifrost contract validator.
- IDE rule renderer check.
- Ecosystem-separation validator.
- Authority-lock validator.
- Git whitespace check.
- Scoped secret and junk scan.
- Independent authority review after fault remediation: **PASS**.

## True residuals and next gate

1. Open a fresh task in each native host and prove skill discovery plus the appropriate signed memory/tool lifecycle before promotion to `live_validated`.
2. Complete Context Engine v0.2.1 exact-wheel installation and live certification.
3. Run the bounded post-v0.2.1 LangGraph canary with the updated lifecycle capsule.
4. Validate the separate Swarm-owned alignment adapter and SwarmClaw automation without importing AgentCore authority.
5. Only after those gates pass, design the final synchronous-environment hardening skill.

`BLUEPRINT.md` was not modified.
