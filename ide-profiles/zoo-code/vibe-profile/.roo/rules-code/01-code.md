# Code mode

- Work autonomously through the spec: create files, patch, install dependencies, build, test.
  Do not stop for routine confirmation.
- Lockfile decides the package manager (package-lock.json -> npm, pnpm-lock.yaml -> pnpm).
  Never run `corepack enable`.
- Destructive command guard (always on): never run recursive deletes outside the project,
  `git push --force`, `git reset --hard`, `git clean -fdx`, disk/format commands, registry
  deletes, `DROP`/`TRUNCATE`, or anything that prints environment secrets. Stop and ask instead.
- UI (Material 3): large cards and buttons, generous white space, drop shadows from elevation
  tokens. Every color, radius, spacing, typography, and shadow value comes from theme tokens.
  The admin panel exposes a 4-token theme switcher (primary, secondary, surface, accent) bound to
  the token source. Zero hardcoded visual values.
- Finish: run tests/lint, commit task-owned files only, then hand off to `doc-master`.
