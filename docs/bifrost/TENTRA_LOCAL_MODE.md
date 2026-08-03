# Tentra Local Mode (AgentCore)

**Updated:** 2026-07-12
**Registry id:** `tentra`
**Pinned package:** `tentra-mcp@1.3.3` with `--local`

## Decision

Tentra runs in **local explicit-project mode only** for AgentCore non-Swarm work. Its shared Bifrost upstream is dormant. Data stays on the AgentCore runtime drive:

```text
F:\AgentCore\runtime\tentra\data
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
2. Always set data under `F:\AgentCore\runtime\tentra\data` (not C: user profile and never under neutral Recall or Swarm-owned roots).
3. Launch Tentra only from a governed workflow/host with an explicit project cwd/root.
4. Reject Swarm / `F:\AgentCore\agentmemory` paths before launch.
5. Keep Tentra disabled in Bifrost client configs until per-session routing is accepted; leave data intact unless the operator requests removal.

## Ops

Install script ensures the Tentra data directory exists:

`ops/bifrost/Install-AgentCoreBifrostGateway.ps1` creates `F:\AgentCore\runtime\tentra\data`.

Do not document or store Tentra cloud credentials for this control-plane baseline.
