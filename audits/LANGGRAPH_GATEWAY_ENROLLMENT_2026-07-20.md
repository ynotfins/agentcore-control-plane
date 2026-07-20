# LangGraph / Studio AgentCore Gateway Enrollment Evidence (2026-07-20)

**See also:** `BLUEPRINT.md` · `docs/operations/AUTONOMOUS_WORKFLOW_AND_STUDIO.md` · `docs/operations/OPENROUTER_MCP.md` · `docs/bifrost/UNIFIED_GATEWAY_SETUP.md` · `audits/CHERRY_GATEWAY_ENROLLMENT_2026-07-20.md`

## Shared MCP adapter

| Item | Value |
| --- | --- |
| Module | `scripts/agentcore_workflow/mcp_client.py` |
| Sync memory helper | `scripts/agentcore_workflow/memory_gateway.py` |
| Node policy | `scripts/agentcore_workflow/node_tool_policy.py` |
| Library | `langchain-mcp-adapters==0.3.0` (catalog-approved) |
| URL | `http://127.0.0.1:8080/mcp` |
| Transport | HTTP / streamable HTTP |
| Timeout | 300s |
| Auth | Bearer from `BIFROST_MCP_VK_WORKFLOW` if set, else `BIFROST_MCP_VIRTUAL_KEY` |
| Localhost only | enforced |

## Workflow VK / profile decision

**Decision:** Do **not** add a permanent Bifrost `workflow` capability profile (unnecessary architecture).  
Use governed builder VK with node-scoped tool filtering. Optional override: `BIFROST_MCP_VK_WORKFLOW` when the operator creates a dedicated key later.

## Node / tool policy

| Node | Tools |
| --- | --- |
| bootstrap / recovery | session_open, startup_context, retrieve_context, expand_source |
| evidence / state | append_event, build_handoff, session_close |
| project activation | project_list, project_activate, project_status |
| builder | current Milestone / JIT tools only |
| critic / judge | read-only retrieval/docs/memory_status |
| operator decision | explicitly approved operator tools only |

Refresh tools at workflow start, after lease activation/revocation, and before resume (`bump_lease_epoch`).

## Automatic JIT bridge

| Item | Value |
| --- | --- |
| Module | `scripts/bifrost/jit_vk_bridge.py` |
| Hook | `agentcore_workflow.db.create_jit_lease` / `revoke_lease` / `expire_jit_leases` |
| Live proof | discovery grant → 13 `openrouter-*` tools incl. presets; revoke → 0; memory = 10 |
| Client sync | expands openrouter MCP `tools_to_execute` to registry `permitted_tools` (18); denied stay out |
| Fail-closed | grant failure leaves tools hidden |

## Production / Studio fixtures

Full fixture-to-done / timeout / kill-resume suite: run via existing `fixture_e2e.py` / `python -m agentcore workflow studio` after dependency install. Topology fingerprint remains shared via `studio/graph.py` → `build_studio_graph`.

## Invariants

- Exact ten-tool agentcore-memory surface unchanged
- No direct OpenRouter MCP IDE entries
- No default model/provider changes
- No `.env` files
- Swarm untouched
- Secrets not printed
