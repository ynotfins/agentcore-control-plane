# Project Charter — {{project_name}}

**Policy:** `docs/agent-policy/NEW_PROJECT_BOOTSTRAP.md` (AgentCore control plane)
**Status vocabulary:** see `docs/agent-policy/CHECKLIST_STANDARD.md`

## Identity

| Field | Value |
| -- | -- |
| project_id | {{project_id}} |
| repo_path | {{repo_path}} |
| repo_remote | {{repo_remote}} |
| worktree_path | {{worktree_path}} |
| created_at | {{created_at}} |
| current_milestone_id | M0 |
| security_level | {{security_level: normal | sensitive | restricted}} |

## Operator goal (preserved verbatim — do not paraphrase or edit)

```text
{{operator_original_prompt}}
```

Evidence reference: {{prompt_evidence_id_or_path}}

## Final product outcome

{{final_outcome}}

## Non-negotiable constraints

- {{constraint_1}}

## Architecture boundaries

- {{boundary_1}}

## Definition of done

- {{definition_of_done_1}}

## Acceptance criteria

- {{acceptance_criterion_1}}

## Policies

| Policy | Value |
| -- | -- |
| dependency_policy | Exact versions resolved via Arabold Docs; no unpinned installs |
| documentation_policy | Arabold checkpoint per Milestone; project docs index kept current |
| memory_scope | Contribute via `agentcore-memory` only; no direct STATE file edits |
| tool_policy | `docs/agent-policy/TOOL_LIFECYCLE_POLICY.md`; manifest: `.agentcore/TOOL_MANIFEST.yaml` |

## Authoritative sources

1. `D:\github\agentcore-control-plane\PROJECT_ANCHOR.md` + `DOC_AUTHORITY.md`
2. `docs/agent-policy/` (global execution policy)
3. This charter
4. `.agentcore/MILESTONES.md`
