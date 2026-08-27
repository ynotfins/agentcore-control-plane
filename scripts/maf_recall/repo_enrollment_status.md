# Repo enrollment status (read-only note)

Avoid editing contracts/agentcore-project-enrollment.json from this package.

## Currently enrolled project_key values

- agentcore-control-plane
- agentcore-context-engine
- codebase-analyzer
- openhands
- nfa-alerts-database
- nfa-notification-collector
- odysseus

## Swarm roots must not be enrolled

Swarm ecosystem roots remain denylisted. Use agentcore-memory behind gateway only.

## Not enrolled yet

- nfa-platform
- Cloud Mia

Authority-maintainer change required to enroll those identities.

## Runtime/staging roots checked 2026-08-27

| Path | Exists | Enrollment decision |
|------|--------|---------------------|
| `D:\github\agentcore-control-plane` | yes | enrolled as `agentcore-control-plane` |
| `D:\OpenHands` | yes | enrolled as `openhands` |
| `D:\devin-workspace` | yes | staging parent only; do not use as a blanket memory identity |
| `D:\OpenHandsProjects` | yes | OpenHands project parent only; enroll actual repo/worktree paths individually before memory writes |
| `D:\github\swarm-ecosystem-control` | yes | foreign Swarm authority; do not enroll in AgentCore memory |
| `H:\SwarmData` | yes | foreign Swarm hot runtime/data; do not enroll |
| `I:\LocalApps\OpenHands` | yes | runtime state/bind root; not a project memory identity |
| `I:\LocalApps\Devin` | yes | runtime state/bind root; not a project memory identity |

Rule: project enrollment is for exact repo/worktree roots, not broad staging parents or runtime data roots.
