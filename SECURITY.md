# Security Policy

## Secrets

- Never hard-code API keys, bearer tokens, refresh tokens, cookies, private keys, passwords, license files, or PAT values.
- Use Windows User-scope environment variables for durable local secrets.
- Generated config fragments may reference secrets only with placeholders such as `${env:ARTIFORGE_PAT}` or `${ENV:OPENAI_API_KEY}`.
- Do not write secret values into reports, Markdown, registry files, validators, renderers, or logs.

## Approval Gates

- Repo-only hardening may update files under `D:\MCP-Control-Plane`.
- Live client config writes require an explicit user instruction for that rollout.
- Composio is quarantined by default and must not be rendered into client fragments.
- Raw Mem0 is not a normal-agent memory route; use PostgreSQL-backed `global-memory-gateway`.
- Raw secrets must not be stored in PostgreSQL vector memory; store only secret references, scopes, status, and non-reversible fingerprints.

## Read-only Enforcement

Managed governance and renderer files should be re-locked after validation.
Unlock only the exact files being edited, keep a rollback copy, run validation, then restore read-only attributes.
