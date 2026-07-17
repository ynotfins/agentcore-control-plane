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

- **This task creates and validates source-controlled profiles and rendered artifacts only. No live IDE global-rule or MCP file is edited.** Live changes remain approval-gated per `docs/prompts/install-agentcore-gateway-in-ide.md`.
- Semantic changes go into `contracts/global-agent-policy.yaml`, then re-render. Hand-edits to derived files are drift and fail `--check`.
- Editability values are declared, never guessed: `direct_write` / `generated_prompt` / `manual_import` / `unsupported` / `unverified`.
- OpenClaw/ClawX are **Swarm-managed** — recorded in the matrix, no non-Swarm profile created.
- New managed clients are added only after verification against the live machine.

## Semantic parity report (2026-07-14)

All 15 mandatory rules from the canonical policy are present in every rendered `GLOBAL_RULES.md`. Delivery capability differs by product:

| IDE | Rules delivery | MCP entry | Parity status |
| -- | -- | -- | -- |
| cursor | project rules `direct_write`; global User Rules `manual_import` | one gateway entry (validated 2026-07-13, 127 tools) | full (delivery of global rules is manual paste) |
| codex | `AGENTS.md` `direct_write` | one gateway entry (validated 2026-07-14) | full |
| claude-code | `CLAUDE.md` `direct_write` | one gateway entry (unvalidated) | full pending live validation |
| claude-desktop | `manual_import` (no rules file) | one gateway entry; VK materialized live-only | partial — depends on operator pasting rules |
| minimax | `unverified` rule mechanism | one gateway entry (unvalidated) | pending verification |
| antigravity | `unverified` rule mechanism; two candidate MCP paths | one gateway entry (unvalidated) | pending verification |
| mavis | `unverified` rule mechanism | one gateway entry (unvalidated) | pending verification |
| open-interpreter | `manual_import` via profile system message | one gateway entry; VK materialized live-only | partial — depends on operator import |

No mandatory rule is silently omitted anywhere: every gap above is recorded in the corresponding `IDE_PROFILE.yaml` and rendered into that IDE's `GLOBAL_RULES.md` under "Product-specific notes and omissions".
