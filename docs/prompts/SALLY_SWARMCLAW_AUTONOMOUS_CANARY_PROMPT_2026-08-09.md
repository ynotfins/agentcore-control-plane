# Sally Prompt — SwarmClaw Autonomous Canary

Sally, run a standalone SwarmClaw autonomous-runtime canary.

Goal:

Prove the SwarmClaw runtime can accept an operator goal, delegate work to the configured Swarm agent team, produce a small verifiable artifact, verify that artifact through a second agent or QA path, and write a final evidence report without touching AgentCore, Bifrost, LangGraph, IDE configs, or non-Swarm project folders.

Boundaries:

- SwarmClaw/Sally owns this canary.
- Use existing SwarmClaw, SwarmRecall, SwarmVault, Meilisearch, and Swarm PostgreSQL configuration.
- Do not modify AgentCore files, Bifrost files, LangGraph files, Cursor/Codex/Claude/Zed/Eigent IDE configs, Windows boot config, or non-Swarm project repositories.
- Do not expose or print secrets.
- Keep all canary writes inside Swarm-owned roots, preferably under:
  - `H:\SwarmData\claw\workspace\sally\canaries\`
  - `E:\SwarmBackups\` only if a canary backup/restore artifact is needed.
- Do not change Swarm product source code unless the canary discovers a blocking configuration issue and stops for operator approval.

Required canary:

1. Record current Swarm service health.
2. Start one bounded autonomous task through Sally/SwarmClaw.
3. Delegate artifact creation to the configured Builder or equivalent implementation agent.
4. Delegate verification to QA/Reviewer or equivalent verification agent.
5. Produce a small artifact such as a markdown report or JSON receipt that includes:
   - canary ID;
   - timestamp;
   - participating agents;
   - task objective;
   - created artifact path;
   - verification result;
   - explicit no-cross-write boundary statement.
6. Verify the artifact exists and is readable.
7. Verify no writes occurred outside Swarm-owned roots.
8. Return final status PASS/FAIL with evidence.

Final report:

Write the final report to:

`H:\SwarmData\claw\workspace\sally\SWARMCLAW_AUTONOMOUS_CANARY_2026-08-09.md`

The final report must include these exact section headings:

- `# SwarmClaw Autonomous Canary — 2026-08-09`
- `## Final Status`
- `## Service Health`
- `## Autonomous Delegation`
- `## Artifact Evidence`
- `## Verification Evidence`
- `## Boundary Proof`
- `## Changed Files`
- `## Residuals`
- `## Final Report Path`

Return only:

1. Final PASS/FAIL.
2. Final report path.
3. Short evidence summary.
