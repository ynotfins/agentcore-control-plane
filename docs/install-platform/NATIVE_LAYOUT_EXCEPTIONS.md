# Native-layout exception registry

**Authority:** `docs/install-platform/INSTALLATION_POLICY.md` (Native-layout apps exception, Tony Nov 4 2026) under `PROJECT_ANCHOR.md` drive roles.
**Approval:** `AUTH-2026-11-05-EXECUTE-ALL`
**Updated:** 2026-11-05 (America/New_York)

One line per app. Add new rows only when Tony approves a case-by-case native-layout exception. Do not print secrets.

| App | Paths it uses | Doc link |
| --- | --- | --- |
| Paperclip | Hot data home `I:\LocalApps\Paperclip` (`PAPERCLIP_HOME`); instance `I:\LocalApps\Paperclip\instances\default\` (config, workspaces, logs); docs-native embedded Postgres data dir `I:\LocalApps\Paperclip\instances\default\db` on loopback port **54329** (see instance `embeddedPostgresPort`). Source/checkout also at `D:\Paperclip`. Backups: `E:\LocalApps\Backups\Paperclip` + Paperclip built-in hourly backups. *(On disk 2026-11-05 the instance still points at external AgentCore PG18 `127.0.0.1:55433` database `paperclip` pending the separate DB-owner cutover in `D:\Paperclip\PROMPT_DB_OWNER.md`; this exception authorizes the docs-native embedded layout, not a permanent PG18 attachment.)* | https://docs.paperclip.ing/reference/deploy/database/ |
| SwarmClaw ecosystem (SwarmClaw, SwarmRecall, SwarmVault + runtime) | Dedicated self-managed drive **`H:`** per existing policy: data root `H:\SwarmData` (incl. `H:\SwarmData\claw`, `H:\SwarmData\vault`, `H:\SwarmData\postgres-native`, Meilisearch under `H:\SwarmData\meilisearch`), runtime `H:\SwarmRuntime` (incl. `H:\SwarmRuntime\pgsql`). Own memory plane; not shared with agentcore-memory; not managed by other bots. Swarm control plane: `D:\github\swarm-ecosystem-control`. | `PROJECT_ANCHOR.md` Ecosystem and Drive Separation + §2 drive role for `H:`; Swarm facts in `D:\github\swarm-ecosystem-control\CONTEXT_BLOCK.md` / `SWARM_PROJECT_ANCHOR.md` |

## Still required (every row)

- Never use `H:` **except** the SwarmClaw ecosystem row above (H: is Swarm-only).
- Never affect nfa-platform or its sister projects.
- Loopback-only unless Tony approves exposure.
- Keep the app's data covered by backups.
- Never print secrets.
