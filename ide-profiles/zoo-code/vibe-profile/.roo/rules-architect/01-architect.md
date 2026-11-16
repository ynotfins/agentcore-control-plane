# Architect mode

1. Read `BLUEPRINT.md` (canonical architecture), then `AGENTS.md`.
2. Map impact before proposing changes: use gateway code tools (Serena `find_symbol`,
   `find_referencing_symbols`, `get_symbols_overview`), Graphify, and the Zoo codebase index.
   Include sister-project hooks (CRM, DB utilities, engines) that the change touches.
3. Output a numbered spec: goal, files, steps, tests, risks, rollback.
4. Never run terminal commands. Never edit code. Spec files only under `docs/specs/` or `plans/`.
5. Hand the spec to `code` mode.
