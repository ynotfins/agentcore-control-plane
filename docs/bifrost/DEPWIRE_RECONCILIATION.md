# Depwire Reconciliation — Post Bifrost Cutover

**Updated:** 2026-07-12
**Related:** `DEPWIRE.md`, registry entries `depwire` / `depwire-cloud`

## Target state

After Bifrost cutover, **Depwire is accessed through `agentcore-gateway`** for normal IDE work:

```text
IDE -> agentcore-gateway -> depwire (local, project-router wrapper)
```

Depwire Cloud (`https://api.depwire.dev/mcp`) remains in the registry as **`enabled: false` / deferred** until healthy verification. Auth pattern (when enabled): `Authorization: Bearer env.DEPWIRE_API_KEY` — never hardcode.

## Local still available for diagnostics

- Global CLI: `depwire-cli` / `depwire.cmd mcp`
- Direct local MCP may still be used for **diagnostics**, offline work, or when the gateway is down — say so explicitly; do not silently reintroduce a permanent dual baseline in IDE configs.
- Prefer gateway-mediated Depwire for day-to-day builder/reviewer/operator profiles.

## Telemetry

Do **not** set `DEPWIRE_NO_TELEMETRY` unless the operator explicitly requests it.

## Ignore hygiene

```gitignore
.depwire/
depwire-output.json
```

## Reconciliation checklist

1. IDE has single `agentcore-gateway` entry (no permanent direct `depwire` + full baseline duplicate).
2. Project activated via `agentcore-project-router` before Depwire graph ops on a worktree.
3. `connect_repo` only against verified local roots (never remote clone/pull without approval).
4. Cloud stays disabled until registry `enabled: true`.
5. `DEPWIRE.md` describes gateway-primary + local diagnostic fallback (see top of that file).
