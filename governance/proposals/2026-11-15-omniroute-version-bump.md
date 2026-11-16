# Proposal — OmniRoute version bump 3.8.49 → 3.8.53 (governed docs)

**ID:** `governed-doc-drift-2026-11-15-omniroute-version-3.8.53`
**Class:** `governed_mutable` (`contracts/authority-lock.yaml`)
**Blast radius:** docs reconciliation for commit `7ec2a58` ("feat(policy): register first-class apps, OmniRoute-routed Zoo vibe profile")

## Why

`audits/FIRST_CLASS_APPS_OMNIROUTE_2026-11-15.md` records a machine-state OmniRoute reinstall during this change: clean
reinstall of `omniroute@3.8.53` (published 2026-11-06), launcher flag flipped from `--no-tray --log --no-recovery` to
`--tray`, and `omniroute health` verified at version `3.8.53`. The three governed docs below still state the prior pin,
`3.8.49`, which is now stale.

## Proposed changes

### 1. `AGENTS.md:61`

- **Current:** `OmniRoute 3.8.49 is enrolled as a Job-B loopback companion under AUTH-2026-11-04-LOCKED-DOC-HARDENING-OMNIROUTE (127.0.0.1:20128, data I:\LocalApps\OmniRoute); it is not the IDE MCP front door.`
- **Proposed:** `OmniRoute 3.8.53 is enrolled as a Job-B loopback companion under AUTH-2026-11-04-LOCKED-DOC-HARDENING-OMNIROUTE (127.0.0.1:20128, data I:\LocalApps\OmniRoute; launcher runs with --tray); it is not the IDE MCP front door.`
- **Source:** `audits/FIRST_CLASS_APPS_OMNIROUTE_2026-11-15.md:11,16` (reinstall to `omniroute@3.8.53`; `omniroute health healthy, version 3.8.53`; launcher `--tray`)

### 2. `CONTEXT_BLOCK.md:163,178`

- **Current (163):** `| OmniRoute | `3.8.49` | Live Job-B companion on `127.0.0.1:20128` (data `I:\LocalApps\OmniRoute`); MCP via Bifrost VK `BIFROST_MCP_VK_OMNIROUTE` |`
- **Proposed (163):** `| OmniRoute | `3.8.53` | Live Job-B companion on `127.0.0.1:20128` (data `I:\LocalApps\OmniRoute`, launcher `--tray`); MCP via Bifrost VK `BIFROST_MCP_VK_OMNIROUTE` |`
- **Current (178):** `...OmniRoute `3.8.49` is enrolled as a Job-B loopback companion (`127.0.0.1:20128`, BelowNormal) under `AUTH-2026-11-04-LOCKED-DOC-HARDENING-OMNIROUTE`...`
- **Proposed (178):** `...OmniRoute `3.8.53` is enrolled as a Job-B loopback companion (`127.0.0.1:20128`, BelowNormal) under `AUTH-2026-11-04-LOCKED-DOC-HARDENING-OMNIROUTE`...`
- **Source:** same as above.

### 3. `DOC_AUTHORITY.md:192`

- **Current:** `| \`omniroute\` / \`omniroute-rtk\` / \`omniroute-compression\` | \`3.8.49\` | release-pinned upstream README and compression guides |`
- **Proposed:** `| \`omniroute\` / \`omniroute-rtk\` / \`omniroute-compression\` | \`3.8.53\` | release-pinned upstream README and compression guides |`
- **Source:** same as above.

## Not in scope

Three archived snapshots under `audits/rollback/**/DOC_AUTHORITY.md` and `audits/rollback/**/CONTEXT_BLOCK.md` also
contain `3.8.49`. Those are point-in-time rollback evidence, not live docs; they are intentionally left untouched.

## Requires

`authority_maintainer` + AUTH id + rollback + validators (`python scripts/validate_authority_lock.py`,
`python scripts/bifrost/validate_contracts.py`) + independent review, per `contracts/authority-lock.yaml`
(`governed_mutable` class, which covers `AGENTS.md`/`CONTEXT_BLOCK.md`; `DOC_AUTHORITY.md` is also `governed_mutable`).
