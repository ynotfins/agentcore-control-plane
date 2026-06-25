# Global Agent Rules

## Environment Variable Policy

AgentCore does not use `.env` files for secrets or local runtime configuration.

- Store AgentCore secrets in Windows User or System Environment Variables only.
- Do not create, request, read, write, generate, template, commit, or recommend `.env`, `.env.local`, `.env.production`, `.env.example`, dotenv files, or dotenv loaders for AgentCore unless the operator explicitly orders an exception.
- Documentation may list variable names only, never values.
- Config files may reference variables by name only, for example `${env:VARIABLE_NAME}`, `process.env.VARIABLE_NAME`, or `$env:VARIABLE_NAME`.
- If a tool expects a `.env` file, adapt it to Windows Environment Variables instead.
- If a required variable is missing, stop and report the variable name. Do not create a local fallback.
- Do not store passwords, database credentials, API keys, private keys, tokens, certificates, incident data, or first-responder data in Git, docs, Markdown, JSON, YAML, TOML, SQLite, pgvector memory payloads, Obsidian, SwarmVault `raw/`, `wiki/`, `state/`, or agent memory.

Known current AgentCore variables include:

- `AGENT_CORE_AGENT_ADMIN_PASSWORD`
- `AGENT_CORE_AGENT_INGEST_PASSWORD`
- `AGENT_CORE_AGENT_READ_PASSWORD`
- `AGENT_CORE_POSTGRES_PASSWORD`
- `AGENT_CORE_PGPASSWORD`
- `AGENT_CORE_PGUSER`
- any future `AGENT_CORE_*` variables

## Write Classes

### Normal IDE Agents

- No direct SQL into PostgreSQL.
- Use `global-memory-gateway` only.
- Read project facts and static facts before planning.

### Trusted Ingest Agents

- Approved scripts and runners only.
- Direct SQL is allowed only for control-plane-approved ingest work.
- Use Windows environment variables for credentials; do not materialize local secret files.

### Admin Or Migration Agents

- Schema, backup, restore, validation, and repair work only.
- Require explicit operator intent before using admin-level database access.
- Must validate rollback and keep raw secrets out of reports and docs.

## Source And Runtime Separation

- Source repos: `D:\github`
- Runtime data: `F:\AgentCore`
- Backups: `E:\AgentCoreBackups`

Do not place runtime databases, logs, backups, incident data, or private response data inside source repositories.

## Privacy Defaults

- Private first-responder data is local-only by default.
- `SwarmFeed`, `SwarmDock`, and hosted services must not receive incident data unless the operator explicitly approves the route.
- Governed memory writes must be redacted, minimum-necessary summaries only.

## Gateway Contract

- `global-memory-gateway` must use `agent_ingest` through Windows environment variables.
- Expected pattern:
  - `AGENT_CORE_PGUSER=agent_ingest`
  - `AGENT_CORE_PGPASSWORD=${env:AGENT_CORE_AGENT_INGEST_PASSWORD}`

Normal IDE agents must not bypass the gateway with direct PostgreSQL writes.
