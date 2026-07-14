# Milestones — {{project_name}}

**Standard:** `docs/agent-policy/MILESTONE_EXECUTION_STANDARD.md` (AgentCore control plane)
**Canonical checklist state:** `.agentcore/checklists/state.json` (this file and per-Milestone files are projections)

Milestones are outcome boundaries. Purposes, exit criteria, and ordering are fixed once approved; Macro/Micro steps inside a Milestone are implementation guidance refined at Milestone entry.

| ID | Name | Outcome | Status | File |
| -- | -- | -- | -- | -- |
| M0 | Project Bootstrap and Alignment | Governance, context, and safe tool surface established | pending | `milestones/M0-bootstrap.md` |
| M1 | {{milestone_1_name}} | {{milestone_1_outcome}} | pending | `milestones/M1-{{slug}}.md` |

## Rules

- No Milestone starts before its entry gate passes; none closes before its exit gate passes.
- Every Milestone records: Context Fabric checkpoint, Arabold documentation checkpoint, memory/handoff checkpoint, and tool-audit checkpoint.
- A completed Milestone generates the next Milestone's entry packet.
