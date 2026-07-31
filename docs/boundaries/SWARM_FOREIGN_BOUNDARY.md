# Swarm Foreign Boundary

Foreign ecosystem: Swarm

Canonical control-plane path: `D:\github\swarm-ecosystem-control`

Canonical repository URL: `https://github.com/ynotfins/swarm-ecosystem.git`

Current source commit: `e6f0c2c01006796cbde8a328fdee570434478838`

Foreign authority lives in:

- `D:\github\swarm-ecosystem-control\SWARM_PROJECT_ANCHOR.md`
- `D:\github\swarm-ecosystem-control\SWARM_DOC_AUTHORITY.md`
- `D:\github\swarm-ecosystem-control\SWARM_BLUEPRINT.md`
- `D:\github\swarm-ecosystem-control\contracts\runtime-ports.yaml`
- `D:\github\swarm-ecosystem-control\contracts\storage-layout.yaml`

AgentCore and Swarm are independent control planes. AgentCore must not consume SwarmRecall memory, SwarmVault graph/wiki/state, SwarmClaw sessions, Swarm credentials, Swarm databases, Swarm backup roots, or Swarm MCP entries as AgentCore authority or AgentCore / enrolled non-Swarm IDE baseline.

SwarmRecall is the Swarm ecosystem’s required memory/context layer. AgentCore does not claim that SwarmRecall replaces SwarmClaw’s native internal application databases (including SQLite) unless separately proven under Swarm authority.

**HARD STOP:** No normal AgentCore IDE continuity on Swarm projects. Do not enroll, persist, or resume Swarm-owned work through AgentCore memory, project router, or IDE profiles. Selected Swarm-owned paths must stop with `swarm_project_refused`. A neutral dual workspace may be used only for read-only collision and boundary audits; that relationship must not enter Swarm runtime and must not restore AgentCore continuity on Swarm projects.

Shared-machine collision constraints: AgentCore and Swarm must keep distinct ports, databases, credentials, process supervisors, prompts, tools, projections, and backup roots. No canonical resource may be jointly owned. Exclusive Swarm hot ownership of `H:` is the target after Milestone M9 acceptance; AgentCore hot namespace remains `F:\AgentCore\...`.

Last verification timestamp: `2026-07-31T17:30:00Z`
