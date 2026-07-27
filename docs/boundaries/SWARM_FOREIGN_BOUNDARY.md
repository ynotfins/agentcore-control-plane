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

AgentCore must not consume SwarmRecall memory, SwarmVault graph/wiki/state, SwarmClaw sessions, Swarm credentials, Swarm databases, Swarm backup roots, or Swarm MCP entries as AgentCore authority or non-Swarm IDE baseline.

Permitted relationship: AgentCore may provide developer continuity while editing Swarm repositories. That relationship is editor-side only and must not enter Swarm runtime.

Shared-machine collision constraints: AgentCore and Swarm must keep distinct ports, databases, credentials, process supervisors, prompts, tools, projections, and backup roots.

Last verification timestamp: `2026-07-26T07:00:00Z`
