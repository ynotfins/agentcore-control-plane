# Environment and Secrets Rules

## Windows Scope

- Durable local secrets belong in Windows User-scope environment variables.
- Process-scope values are acceptable for one-off validation but are not durable.
- Machine-scope secrets require explicit user approval.
- Never persist secrets in `.env`, JSON, YAML, Markdown, logs, reports, screenshots, or email.

## Allowed References

- `${env:ARTIFORGE_PAT}`
- `${ENV:ARTIFORGE_PAT}`
- `${env:OPENAI_API_KEY}`
- `${ENV:OPENAI_API_KEY}`
- `${env:GITHUB_PERSONAL_ACCESS_TOKEN}`
- `${ENV:GITHUB_PERSONAL_ACCESS_TOKEN}`
- `${env:CURSOR_API_KEY}`
- `${ENV:CURSOR_API_KEY}`
- `${env:OBSIDIAN_API_KEY}`
- `${ENV:OBSIDIAN_API_KEY}`
- `${env:OBSIDIAN_LOCAL_REST_API}`
- `${ENV:OBSIDIAN_LOCAL_REST_API}`
- `${env:MEM0_API_KEY}`
- `${ENV:MEM0_API_KEY}`
- `${env:COMPOSIO_API_KEY}`
- `${ENV:COMPOSIO_API_KEY}`
- `${env:MEMORY_GATEWAY_BACKEND}`
- `${ENV:MEMORY_GATEWAY_BACKEND}`
- `${env:AGENT_CORE_PGHOST}`
- `${ENV:AGENT_CORE_PGHOST}`
- `${env:AGENT_CORE_PGPORT}`
- `${ENV:AGENT_CORE_PGPORT}`
- `${env:AGENT_CORE_PGDATABASE}`
- `${ENV:AGENT_CORE_PGDATABASE}`
- `${env:AGENT_CORE_PGUSER}`
- `${ENV:AGENT_CORE_PGUSER}`
- `${env:AGENT_CORE_PGPASSWORD}`
- `${ENV:AGENT_CORE_PGPASSWORD}`
- `${env:AGENT_CORE_AGENT_ADMIN_PASSWORD}`
- `${ENV:AGENT_CORE_AGENT_ADMIN_PASSWORD}`
- `${env:AGENT_CORE_AGENT_INGEST_PASSWORD}`
- `${ENV:AGENT_CORE_AGENT_INGEST_PASSWORD}`
- `${env:AGENT_CORE_AGENT_READ_PASSWORD}`
- `${ENV:AGENT_CORE_AGENT_READ_PASSWORD}`
- `${env:AGENT_CORE_POSTGRES_PASSWORD}`
- `${ENV:AGENT_CORE_POSTGRES_PASSWORD}`
- `${env:MEMORY_GATEWAY_EMBEDDING_PROVIDER}`
- `${ENV:MEMORY_GATEWAY_EMBEDDING_PROVIDER}`
- `${env:OPENAI_EMBEDDING_MODEL}`
- `${ENV:OPENAI_EMBEDDING_MODEL}`
- `${env:MEMORY_GATEWAY_EMBEDDING_DIMENSIONS}`
- `${ENV:MEMORY_GATEWAY_EMBEDDING_DIMENSIONS}`

Literal secret values are forbidden. Validators must fail if they detect likely hard-coded credentials outside rollback backups.
