# Proposal: retire dormant-Serena wording in remaining authority tables

Status: applied in live instruction sources and CONTEXT_BLOCK. PROJECT_ANCHOR remains locked.

## Already applied

- contracts/global-agent-policy.yaml policy_revision 2026-11-01-serena-live-tool-gates-v1
- AGENTS.md, SERENA.md, CONTEXT_BLOCK.md, required-foundation-tools.mdc, GLOBAL_AGENT_RULES.md rule 8
- Serena Code Mode identity via agentcore_project on executeToolCode
- sessionStart bind + SERENA ROUTING reminder

## Needs UNLOCK

PROJECT_ANCHOR.md Canonical upstream set still says Implicit-project Serena remain dormant. Replace that clause with: Serena is live as Code Mode behind the HTTP session shim; every executeToolCode Serena call must pass agentcore_project. Implicit-project Depwire, Tentra, filesystem, and Context Fabric upstreams remain dormant in shared profiles.