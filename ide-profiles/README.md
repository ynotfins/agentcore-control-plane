# IDE Profiles — Per-IDE Global Rule Renderings

**Canonical semantic policy:** `contracts/global-agent-policy.yaml` (one source of truth).
**Renderer:** `python scripts/render_ide_rules.py` (writes `GLOBAL_RULES.md`, `INSTALL_OR_UPDATE.md`, `VALIDATION.md` per IDE; `--check` verifies freshness).
**Cross-IDE facts:** `IDE_CAPABILITY_MATRIX.yaml`.

Every managed non-Swarm IDE receives the same semantic rules as closely as its product supports. Product-specific omissions are recorded explicitly in each `IDE_PROFILE.yaml` (`known_limitations`, `semantic_parity_gaps`) and surface in the rendered `GLOBAL_RULES.md`.

## Structure

```text
ide-profiles/
  README.md                    ← this file + parity report
  IDE_CAPABILITY_MATRIX.yaml   ← cross-IDE capability/editability summary
  <ide>/
    IDE_PROFILE.yaml           ← hand-maintained facts (versions, paths, editability — 'unverified' until evidenced)
    GLOBAL_RULES.md            ← DERIVED from canonical policy (do not hand-edit)
    MCP_CONFIG_TEMPLATE.*      ← DERIVED from renderers/gateway-clients/<ide>.json
    INSTALL_OR_UPDATE.md       ← DERIVED install/update procedure
    VALIDATION.md              ← DERIVED post-change checks
```

## Rules of this directory

- Profiles distinguish the source-controlled desired policy and templates from dated, sanitized observations of live settings. An observed file does not prove native tool calls, account-synced settings, or approval of a direct MCP companion. Never commit raw live IDE configurations or application databases.
- Live changes require the owning IDE's authority, a backup, and post-change verification per `docs/prompts/install-agentcore-gateway-in-ide.md`.
- Semantic changes go into `contracts/global-agent-policy.yaml`, then re-render. Hand-edits to derived files are drift and fail `--check`.
- Editability values are declared, never guessed: `direct_write` / `generated_prompt` / `manual_import` / `unsupported` / `unverified`.
- OpenClaw/ClawX are AgentCore-owned hosts with separate verified/unverified profiles; they are not Swarm-managed.
- An installed client is not automatically eligible for gateway enrollment. A client without an approved environment-backed, native-token, or process-attested route remains `unsupported_with_reason`; its renderer and MCP template must contain no active gateway entry.
- Historical credential-bearing client state is recorded as `legacy_drift`. Repository guidance must preserve that evidence and must not instruct an agent to paste or persist a virtual key.
- New managed clients are added only after verification against the live machine.

## Semantic parity and delivery report

All mandatory rules from the canonical policy are present in every rendered `GLOBAL_RULES.md`. Delivery capability differs by product:

| IDE | Configuration mode | Rules delivery | MCP entry | Parity status |
| -- | -- | -- | -- | -- |
| cursor | generated_prompt | machine-local foundation file verified 2026-09-14; account User Rules `manual_import` and unverified | one AgentCore gateway entry observed 2026-09-14; two direct Google entries and disabled Dart also present | generated policy installed locally; account UI delivery unverified; prior gateway lifecycle proof remains dated 2026-07-16 |
| codex | generated_prompt | `AGENTS.md` `direct_write` | one gateway entry (config validated 2026-07-14) | full pending live session validation |
| claude-code | generated_prompt | `CLAUDE.md` `direct_write` | one gateway entry (unvalidated) | full pending live validation |
| claude-desktop | unsupported | `manual_import` (no rules file) | inactive template; prior credential-bearing entry is legacy drift | AgentCore enrollment unsupported pending a secure route |
| minimax | generated_prompt | `AGENT.md` `direct_write` | process-attested `:18082` route; no stored bearer | configured; fresh in-app lifecycle acceptance pending |
| minimax-classic | unsupported | `AGENT.md` `direct_write` | inactive template; no AgentCore Matrix cloud enrollment | AgentCore enrollment unsupported pending a secure route |
| antigravity | generated_prompt | global rules unverified | process-attested `:18082` route; no stored bearer | configured; restart/fresh-task proof pending |
| open-interpreter | generated_prompt | CLI home `AGENT.md` + project `AGENTS.md`; GUI instructions are separate | CLI direct `:8080` with `bearer_token_env_var`; GUI process-attested `:18082` with no stored bearer | configured; full native lifecycle pending |
| cherry-studio | unsupported | `manual_import` via AgentCore Workspace Agent prompt | inactive template; prior LevelDB entry is legacy drift | AgentCore enrollment unsupported pending a secure route |
| zed | unsupported | personal/project `AGENTS.md` supported | inactive template; prior credential-bearing entry is legacy drift | AgentCore enrollment unsupported pending a secure route |
| eigent | unsupported | native skills; global rules unverified | inactive template; prior credential-bearing entry is legacy drift | AgentCore enrollment unsupported pending a secure route |
| zoo-code | unsupported | project rules and Zoo-owned skills remain | inactive template; prior credential-bearing entry is legacy drift | AgentCore enrollment unsupported pending a secure route |

`C:\Users\ynotf\.mavis` is a junction to `C:\Users\ynotf\.minimax` (same MiniMax Code data root); it is not a separate executable Mavis client and does not receive its own managed profile.

No mandatory rule is silently omitted anywhere: every gap above is recorded in the corresponding `IDE_PROFILE.yaml` and rendered into that IDE's `GLOBAL_RULES.md` under "Product-specific notes and omissions".
