"""AgentCore M6 — Durable LangGraph Autonomous Workflow package.

PostgreSQL-backed LangGraph workflow implementing:
- Project/thread isolation via agentcore schema
- Milestone/Macro/Micro/checklist state persistence
- Deterministic gates (requirement, scope, arch, doc_version, security, migration, resource)
- Deterministic tests before LLM critics
- Risk-selected critics, deterministic scorer, independent judge
- Human pause/resume for operator decisions
- Progressive tool disclosure and JIT capability leases
- A/B implementation only when risk justifies it

Authority: BLUEPRINT.md M6 and MEMORY_PLATFORM_EXECUTION_PLAN.md M6.
"""

__version__ = "0.6.0"
