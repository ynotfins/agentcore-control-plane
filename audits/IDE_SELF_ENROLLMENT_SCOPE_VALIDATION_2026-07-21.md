# IDE Self-Enrollment Scope Validation (2026-07-21)

**See also:** `contracts/global-agent-policy.yaml` · `docs/prompts/install-agentcore-gateway-in-ide.md` · `scripts/bifrost/validate_ide_enrollment_scope.py` · `MASTER_CONFIG_AND_PROMPT.md` §10

## Goal

Hard-scope IDE-local enrollment prompts so an agent running an install/update prompt may touch **only its own** live IDE configuration. Cross-IDE reconciliation remains a separate control-plane task requiring explicit operator authorization.

**Out of scope for this change:** live IDE configs, MiniMax/Cherry/Mavis live files, `PROJECT_ANCHOR.md`, `BLUEPRINT.md`.

## Rule text (canonical)

```text
CLIENT-LOCAL EXECUTION SCOPE

The IDE running this prompt may inspect and modify only its own live
configuration, rules, agent settings, and backup.

Configuration examples for other IDEs are reference material only.

Do not inspect, back up, repair, restart, validate, or modify another IDE.

Cross-IDE reconciliation is a separate AgentCore control-plane task that
requires explicit operator authorization.
```

## Surfaces updated

| Surface | How |
| --- | --- |
| `MASTER_CONFIG_AND_PROMPT.md` §10 Global IDE setup prompt | Rule inserted into copy-paste prompt before Safety rules |
| `docs/prompts/install-agentcore-gateway-in-ide.md` | Same rule in the Prompt block |
| `contracts/global-agent-policy.yaml` | New mandatory clause `client-local-execution-scope` (policy_revision `2026-07-21`) |
| `ide-profiles/*/INSTALL_OR_UPDATE.md` (8 clients) | Rendered via `scripts/render_ide_rules.py` (not hand-edited) |
| `ide-profiles/*/GLOBAL_RULES.md` | Regenerated so mandatory-rule parity includes the new clause |

Clients covered: antigravity, claude-code, claude-desktop, codex, cursor, mavis, minimax, open-interpreter.

## Validator

| Item | Value |
| --- | --- |
| Script | `scripts/bifrost/validate_ide_enrollment_scope.py` |
| Harness wire-in | `scripts/bifrost/test_contracts.py` → check `ide:client-local enrollment scope` |
| Fail conditions | Missing CLIENT-LOCAL EXECUTION SCOPE title/phrases; multi-IDE live-path edit instructions; per-IDE install ordering foreign live-path edits |

### Command + result (PASS)

```text
> python scripts/bifrost/validate_ide_enrollment_scope.py
Checked 10 enrollment prompt file(s) against 9 live IDE path(s).
OK: CLIENT-LOCAL EXECUTION SCOPE present; no multi-IDE live edit instructions.
exit 0

> python scripts/bifrost/test_contracts.py
PASS 112 checks
OK: all contract/renderer tests passed
exit 0
```

### Negative detection (PASS_DETECT — not committed)

Synthetic prompt containing imperative edits against both Cursor and Codex live paths yields imperative hits for `['codex', 'cursor']` via `find_imperative_ide_hits` (would fail the multi-IDE gate). Phrase detector also matches `Edit all IDEs now`.

## Constraints honored

- No live IDE config edits
- No MiniMax / Cherry / Mavis live-file edits
- No edits to `PROJECT_ANCHOR.md` or `BLUEPRINT.md`

## Verdict

**PASS** — CLIENT-LOCAL EXECUTION SCOPE is present on all required enrollment surfaces; deterministic validator and contract harness exit 0.
