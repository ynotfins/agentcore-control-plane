# Cursor Prompt-Format Policy Persistence — 2026-07-22

## Operator instruction

Every file/folder Cursor must read uses `@` + full absolute Windows path.
Completed tasks requiring further Cursor work include a ready-to-paste
`CURSOR CONTINUATION PROMPT` section.

## AgentCore fact proposal

| Field | Value |
| --- | --- |
| proposal_id | `3ae6b146-e072-415f-850f-5cd62ca8e6ff` |
| status | proposed |
| fact_key | `cursor.prompt_path_format` |
| project_key | `agentcore-control-plane` |
| trust_class | `operator_verified` |

## Policy files updated

- `contracts/global-agent-policy.yaml` — rule `cursor-prompt-path-format`, `policy_revision` `2026-07-22`
- `MASTER_CONFIG_AND_PROMPT.md` — Cursor prompt path format section
- `AGENTS.md` — Learned Workspace Facts entry
- `docs/agent-policy/DOCUMENTATION_READ_ORDER.md` — Cursor prompt path rule
- `scripts/validate_cursor_prompt_format.py` — deterministic validator
- Regenerated `ide-profiles/*/GLOBAL_RULES.md` (and install/validation companions) via `scripts/render_ide_rules.py`

## Validation

```text
python scripts/validate_cursor_prompt_format.py --self-test
→ SELF-TEST PASS

python scripts/bifrost/validate_contracts.py
→ OK (schemas, authority, policy contracts)
```

Projection files under Git are the rendered IDE rule files. PostgreSQL STATE/DECISIONS
projections are not hand-edited; fact proposal awaits operator accept/reject workflow.
