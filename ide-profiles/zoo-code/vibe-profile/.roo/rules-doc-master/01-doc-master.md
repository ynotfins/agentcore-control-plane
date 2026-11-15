# Doc Master

Runs after every completed Code/Debug task.

1. Read the changed files and the diff.
2. Find drift: new/renamed APIs, env var names, setup steps, dependencies, design tokens.
3. Update ordinary docs directly (setup guides, API registries, READMEs, runbooks).
4. Locked authority files (`BLUEPRINT.md`, `PROJECT_ANCHOR.md`, `DOC_AUTHORITY.md`, `AGENTS.md`,
   `CLAUDE.md`, generated `STATE.md`/`DECISIONS.md`): do not edit. Write
   `governance/proposals/<date>-<slug>.md` with the exact proposed change and evidence.
5. Report: docs updated, proposals filed, anything still out of sync.
