"""LangGraph Studio (Agent Server) graph factory for the AgentCore workflow.

Studio is a development / debugging surface. This module exports the SAME
graph topology as production (:func:`agentcore_workflow.workflow.build_studio_graph`).
It does NOT register a production checkpointer: Agent Server injects its own
dev checkpointer (in-memory / sqlite) at runtime. This avoids creating
duplicate or conflicting checkpointers against the canonical AgentCore
PostgresSaver in ``public.checkpoints``.

Authority:
    BLUEPRINT.md M6, BLUEPRINT.md §10 (security; no AgentCore data leaves the
    machine unless explicitly approved). PROJECT_ANCHOR.md §10 (no secret
    values in langgraph.json, documentation, logs, or Git).

Topology parity: ``TOPOLOGY_FINGERPRINT`` is computed at import time from the
same :func:`build_topology` used by production. The studio CLI launcher
verifies parity before starting ``langgraph dev``.
"""

from __future__ import annotations

import os
import sys

# Make the parent scripts dir importable so ``agentcore_workflow`` resolves
# when LangGraph CLI loads this file from a subprocess.
_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.dirname(_HERE)
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from agentcore_workflow.workflow import (  # noqa: E402
    build_topology,
    topology_fingerprint,
    build_studio_graph,
)


# Exposed at module load so the studio launcher can validate parity without
# invoking the graph factory (which would compile a graph unnecessarily).
_t = build_topology()
TOPOLOGY_FINGERPRINT: str = topology_fingerprint(_t)


# ``graph`` is the variable the LangGraph CLI loads via ``langgraph.json``.
# We compile lazily so importing this module has no side effects beyond
# computing the topology fingerprint.
def _make_graph():
    return build_studio_graph(_t)


graph = _make_graph()
