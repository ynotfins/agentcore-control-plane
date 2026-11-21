# Proposal: retire dormant-Serena wording in remaining authority tables

Status: applied in live instruction sources and CONTEXT_BLOCK. PROJECT_ANCHOR remains locked.

## Already applied (this task)

- `contracts/global-agent-policy.yaml` policy_revision `2026-11-01-serena-live-tool-gates-v1`
- `AGENTS.md` Tool Routing
- `.cursor/rules/required-foundation-tools.mdc` (always-apply when-to-use)
- `.cursor/rules/docs-first-arabold.mdc`
- `SERENA.md` runtime header
- `rules/canonical/GLOBAL_AGENT_RULES.md` rule 8
- `.agentcore/docs-checkpoint.json` + `scripts/agentcore_cursor/docs_checkpoint.py`
- sessionStart reminder in `scripts/agentcore_cursor/hooks.py`
- Serena Code Mode identity via agentcore_project on executeToolCode

## Needs UNLOCK

`PROJECT_ANCHOR.md` Canonical upstream set still says Implicit-project Serena ... remain dormant. Replace that clause with: Serena is live as Code Mode behind the HTTP session shim; every executeToolCode Serena call must pass agentcore_project. Implicit-project Depwire, Tentra, filesystem, and Context Fabric upstreams remain dormant in shared profiles.

Do not copy the F: Arabold corpus into Git. Durable docs stay at `F:\AgentCore\runtime\docs-store`.
