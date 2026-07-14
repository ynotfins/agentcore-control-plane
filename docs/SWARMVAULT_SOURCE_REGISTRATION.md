> **SWARM ECOSYSTEM ONLY (2026-07-14).** SwarmVault is part of the independent Swarm ecosystem.
> This procedure applies only inside Swarm work. It is not part of the non-Swarm IDE baseline or
> the AgentCore memory platform (`docs/memory-platform/MEMORY_PLATFORM_EXECUTION_PLAN.md`).

# SwarmVault Source Registration — Safe Strategy

**Native-first.** SwarmVault must be proven healthy natively (`doctor`, `retrieval status`, `graph stats`) before any new source registration. Do not mutate vault state without explicit approval.

## Hard rules
- **Do NOT run broad recursive `source add` on vendor repos.** The rogue incident OOM'd registering `swarmclaw` by scanning the full tree. Register doc/subpath scope, not whole repos with dependencies.
- Always exclude generated/dependency/junk directories before any `source add`:
  ```
  node_modules
  .next
  dist
  build
  coverage
  .turbo
  .pnpm-store
  .cache
  .git
  out
  *.log
  generated artifacts
  ```
- Do not register secrets, `.env` files, runtime DB dumps, or `F:\AgentCore` raw runtime state as sources.
- Do not delete existing SwarmVault sources or artifacts without explicit operator approval.

## Current registered sources (read-only audit, 2026-06-30)
`doctor` reports 5 managed sources, 2465 raw sources, 7071 pages — healthy, no disk balloon (raw ~22 MB). Registered: `swarmvault-staging`, `agentcore-control-plane`, `swarmrecall`, `swarmvault`, `swarmclaw`. `swarmrelay`/`swarmfeed`/`swarmdock` are not registered.
- `swarmclaw` registration may be ingest-incomplete from the prior OOM. Re-validate before relying on it; if re-registering, use the exclude strategy above and a targeted scope.

## Recommended registration pattern (when approved)
1. Prove native health first: `node <cli> doctor --json`, `node <cli> retrieval status`.
2. Register a targeted scope with excludes (per SwarmVault CLI `source add` options / `.swarmvaultignore` if supported by the installed version), not a broad recursive add.
3. Re-run `doctor` and confirm `raw`/page counts grew proportionally (no node_modules balloon).
4. Only then `compile`/`query` as needed.

## Validator behavior
`ops/Test-AgentCoreSwarmVault.ps1` is native-first and timeout-bounded:
- Read-only smokes by default (`mcp help`, `doctor`, `retrieval status`, `graph stats`).
- `query` is single-attempt and BLOCKED on timeout (`-QueryTimeoutSeconds`, default 60). Use `-SkipQuery` for a fast native-only pass.
- `context build` (mutation) is SKIP unless `-IncludeContextBuild` is passed.
