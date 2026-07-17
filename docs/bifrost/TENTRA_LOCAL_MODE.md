# Tentra Local Mode (AgentCore)

**Updated:** 2026-07-12
**Registry id:** `tentra`
**Pinned package:** `tentra-mcp@1.3.3` with `--local`

## Decision

Tentra runs in **local mode only** for AgentCore non-Swarm work. Data stays on the AgentRuntime drive:

```text
H:\AgentRuntime\tentra\data
```

Launch path:

```text
IDE -> agentcore-gateway -> tentra (Bifrost)
      -> scripts/project_router/wrappers/tentra.cmd
      -> child_launcher sets TENTRA_DATA_DIR + active project cwd
      -> npx -y tentra-mcp@1.3.3 --local
```

## Rules

1. Always use `--local`.
2. Always set data under `H:\AgentRuntime\tentra\data` (not C: user profile, not F: Swarm roots).
3. Activate a registered project via `agentcore-project-router` before Tentra project-scoped use.
4. Reject Swarm / `F:\AgentCore\agentmemory` paths (enforced by project router exclusion list).
5. Rollback: disable Tentra in Bifrost client_configs; leave data directory intact unless operator requests wipe.

## Ops

Install script ensures the Tentra data directory exists:

`ops/bifrost/Install-AgentCoreBifrostGateway.ps1` creates `H:\AgentRuntime\tentra\data`.

Do not document or store Tentra cloud credentials for this control-plane baseline.
