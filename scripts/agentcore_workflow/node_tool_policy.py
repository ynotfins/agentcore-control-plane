"""Node-scoped tool policy for AgentCore LangGraph workflows.

Tools are bound per node — never load the full Bifrost surface into every model call.
Gateway visibility is still governed by the active VK + PostgreSQL capability lease.
"""

from __future__ import annotations

from typing import Mapping

# Exact agentcore-memory surface (10 tools) — do not expand.
MEMORY_TOOLS = (
    "memory_status",
    "startup_context",
    "retrieve_context",
    "append_event",
    "propose_fact",
    "expand_source",
    "session_open",
    "session_close",
    "build_handoff",
    "docs_search",
)

PROJECT_TOOLS = (
    "project_list",
    "project_activate",
    "project_status",
    "project_clear",
)

# Bifrost may prefix with server name depending on client; accept both forms.
def _aliases(names: tuple[str, ...], prefixes: tuple[str, ...] = ("agentcore_memory-", "agentcore_project_router-")) -> frozenset[str]:
    out: set[str] = set(names)
    for n in names:
        for p in prefixes:
            out.add(f"{p}{n}")
            # underscore/hyphen variants seen in some gateways
            out.add(f"{p.replace('-', '_')}{n}")
    return frozenset(out)


NODE_TOOL_POLICY: Mapping[str, frozenset[str]] = {
    "bootstrap": _aliases(("session_open", "startup_context", "retrieve_context", "expand_source")),
    "recovery": _aliases(("session_open", "startup_context", "retrieve_context", "expand_source")),
    "evidence": _aliases(("append_event", "build_handoff", "session_close")),
    "state": _aliases(("append_event", "build_handoff", "session_close")),
    "project_activation": _aliases(("project_list", "project_activate", "project_status"), prefixes=("agentcore_project_router-",)),
    "builder": frozenset(),  # filled at runtime from current milestone / JIT lease tools only
    "critic": _aliases(("retrieve_context", "expand_source", "startup_context", "docs_search", "memory_status")),
    "judge": _aliases(("retrieve_context", "expand_source", "startup_context", "docs_search", "memory_status")),
    "operator_decision": frozenset(),  # explicitly approved operator tools only (injected per step)
}

REFRESH_TRIGGERS = (
    "workflow_start",
    "lease_activation",
    "lease_revocation",
    "resume_before_run",
)


def tools_for_node(node_key: str, *, jit_tools: tuple[str, ...] = (), operator_tools: tuple[str, ...] = ()) -> frozenset[str]:
    key = node_key.strip().lower().replace("-", "_")
    # Normalize aliases
    aliases = {
        "node_bootstrap": "bootstrap",
        "node_recovery": "recovery",
        "node_evidence": "evidence",
        "node_state": "state",
        "node_project_activation": "project_activation",
        "node_da_builder": "builder",
        "node_builder": "builder",
        "node_da_critic": "critic",
        "node_critic": "critic",
        "node_judge": "judge",
        "node_operator_decision": "operator_decision",
        "operator": "operator_decision",
    }
    key = aliases.get(key, key)
    base = set(NODE_TOOL_POLICY.get(key, frozenset()))
    if key == "builder":
        base.update(jit_tools)
    if key == "operator_decision":
        base.update(operator_tools)
    return frozenset(base)


def assert_ten_memory_tools(discovered_names: list[str]) -> None:
    """Ensure the exact ten-tool memory surface is present (names may be prefixed)."""
    bare = set()
    for n in discovered_names:
        for mem in MEMORY_TOOLS:
            if n == mem or n.endswith(f"_{mem}") or n.endswith(f"-{mem}") or n.endswith(mem):
                bare.add(mem)
    missing = [t for t in MEMORY_TOOLS if t not in bare]
    if missing:
        raise AssertionError(f"agentcore-memory surface incomplete; missing={missing}")
