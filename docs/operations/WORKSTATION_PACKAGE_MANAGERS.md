# Workstation package managers (Windows)

**Corepack: DISABLED** (2026-09-22). Do not `corepack enable`.

Node v26.8.1 does not ship usable Corepack; leftover `%LOCALAPPDATA%\Corepack\shims` broke `pnpm`/`yarn`. Fixed by removing those shims from User PATH, placing `%AppData%\npm` after `nodejs`, and quarantining shims.

| Tool | Use | Source |
| --- | --- | --- |
| npm | Default (RGDS, AgentCore design pins, `@r3lentless/*` publish) | Node install |
| pnpm | Repos with `pnpm-lock.yaml` | `npm i -g pnpm` → `%AppData%\npm` (12.3.4) |
| yarn | `yarn.lock` repos only | `npm i -g yarn` if needed |
| Corepack | Not used | Off PATH; shims quarantined |

**Rules:** lockfile wins; RGDS stays npm; never re-add Corepack shims; `packageManager` fields do not auto-switch without Corepack.

**Validate:** `where.exe pnpm` under `%AppData%\npm`; `Test-Path $env:LOCALAPPDATA\Corepack\shims` → False.

Repair: `scripts/windows/Repair-WorkstationPackageManagers.ps1`

## Global rule propagation

Canonical mandatory rule id `workstation-package-managers` lives in `contracts/global-agent-policy.yaml` (policy_revision `2026-09-22-workstation-package-managers-v1`), approval `AUTH-2026-09-22-WORKSTATION-PACKAGE-MANAGERS`. All `ide-profiles/*/GLOBAL_RULES.md` and the Cursor foundation rule are derived renderings.
