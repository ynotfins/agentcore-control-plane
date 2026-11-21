# RGDS 1.0.0 external-ops status

Generated: 2026-09-22T19:50:00.925080+00:00

## npm `@r3lentless/rgds-web@1.0.0`

| Check | Result |
| --- | --- |
| Verdict | **PUBLISHED** — do not republish 1.0.0 |
| Evidence | `npm view @r3lentless/rgds-web` → 1.0.0; registry HTTP 200; dist-tag `latest` |
| Earlier 404 | Expected: (1) publish-time malware scan delay (~5–15+ min); (2) script bug `npm view ...@version` (literal version name) |
| Script fix | `scripts/publish-web.ps1` now polls availability; skips if already published; classifies failures |

## Figma

| Check | Result |
| --- | --- |
| Team Library | **Published** (23 sets) |
| Make kit | Guidelines ready — UI assembly remains |

## Package manager

**Keep npm + package-lock.json** for RGDS (see repo `docs/PACKAGE_MANAGER.md` and AgentCore `docs/operations/WORKSTATION_PACKAGE_MANAGERS.md`). Workstation Corepack is **disabled by policy**; pnpm remains available via npm-global for pnpm-lock repos — not a reason to migrate RGDS mid-1.0.0.
