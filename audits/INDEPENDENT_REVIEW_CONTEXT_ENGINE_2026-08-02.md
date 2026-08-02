# Independent Security Review — Context Engine / LangGraph Integration

**Date:** 2026-08-02  
**Reviewer:** Independent security review (scoped local diff)  
**Verdict:** **PASS**  
**Scope:** Option B device write assertions, LangGraph `memory_gateway` signing, OpenRouter timeout fix, workflow `run_db_id` / evidence plumbing, native host hooks @ context-engine `57c32fe`  
**Excluded:** Langfuse WIP, M6/M7/M8 acceptance summary churn

## Summary

Reviewed modified control-plane paths for authorization bypass, unsigned memory writes, credential leakage, and workflow evidence integrity. Changes materially **harden** memory write paths (unsigned writes rejected regardless of `legacy_compat`) and **align** LangGraph gateway calls with Ed25519 signing. No medium-or-higher exploitable issues were validated in changed code.

Native Codex/Claude hook installers at context-engine `57c32fe` contain no committed secrets; one low hygiene note (bridge stderr unsanitized on CLI failure).

## Components reviewed

| Component | Change | Security assessment |
|-----------|--------|---------------------|
| `scripts/agentcore_memory/device_identity.py` | `WRITE_TOOLS` gate | Write bypass closed; reads unchanged during migration |
| `scripts/agentcore_workflow/memory_gateway.py` | Device signing on `tools/call` | Consistent with server verification; localhost + VK handling OK |
| `scripts/agentcore_workflow/deepagents_worker.py` | OpenRouter timeout ms fix | No auth/privilege impact |
| Workflow `run_db_id` / evidence plumbing | CLI → state → DB | Integrity improvement |
| Context Engine native hooks | Codex/Claude installers | No secrets; portable resolution via env/platformdirs |

## Findings

None at medium, high, or critical severity in scope.

## Residual risks (accepted / documented)

1. Unsigned **read** memory tools remain available under `legacy_compat` + valid gateway VK (Option B tradeoff). Full `required` mode for reads would need Tony approval for Bifrost VK→device middleware (Option C) or acceptance of signed-read breakage for bare MCP clients.
2. Memory bootstrap fail-open in `node_start` if signing/gateway unavailable (operator-local degradation).
3. RUN11 builder operated against the project root path rather than `D:\agentcore-worktrees\...` — deliverable created; isolation hardening remains a follow-up.

## Tests referenced

- `scripts/agentcore_memory/tests/test_device_write_assertions.py`
- Context Engine `110` pytest / ruff / mypy at `57c32fe`
- SwarmClaw projection tests `11/11` at `b28f558b`
