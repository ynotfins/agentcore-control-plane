"""Governed per-node role, tool, model, and skill resolution.

Resolution occurs inside existing LangGraph nodes. It does not add nodes, edges,
checkpointers, tools, or durable authorities.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import asdict, dataclass
from functools import lru_cache, wraps
from pathlib import Path
from typing import Any, Callable, Mapping

from .node_tool_policy import tools_for_node

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "contracts" / "context-engine-execution-catalog.json"
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
MODEL_ORDER = {
    "deterministic": 0,
    "fast": 1,
    "capable": 2,
    "independent": 3,
    "frontier": 4,
}


@dataclass(frozen=True)
class ExecutionProfile:
    node: str
    risk: str
    roles: tuple[str, ...]
    tools: tuple[str, ...]
    model_class: str
    model_id: str | None
    skills: tuple[str, ...]
    skill_capsules: tuple[str, ...]
    catalog_version: str
    catalog_sha256: str
    resolution_sha256: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


@lru_cache(maxsize=1)
def load_catalog() -> dict[str, Any]:
    value = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if value.get("schema_version") != 1:
        raise RuntimeError("unsupported Context Engine execution catalog schema")
    return value


def resolve_execution_profile(
    state: Mapping[str, Any],
    node: str,
    *,
    active_tools: tuple[str, ...] = (),
) -> ExecutionProfile:
    catalog = load_catalog()
    risk = str(state.get("current_risk_class") or "low").lower()
    if risk not in RISK_ORDER:
        risk = "medium"
    role_minimum = catalog["role_minimum_risk"]
    roles = tuple(
        role
        for role in catalog["node_roles"].get(node, [])
        if RISK_ORDER[risk] >= RISK_ORDER.get(role_minimum.get(role, "low"), 0)
    )
    if not roles:
        raise RuntimeError(f"no governed roles resolved for node={node}")

    jit_tools = tuple(
        str(item.get("tool_name") or "")
        for item in (state.get("active_tools") or [])
        if isinstance(item, dict)
    )
    tools = tuple(
        sorted(
            tools_for_node(
                node,
                jit_tools=tuple(sorted(set(active_tools) | set(jit_tools))),
            )
        )
    )

    model_classes = [catalog["role_model_class"][role] for role in roles]
    model_class = max(model_classes, key=lambda item: MODEL_ORDER.get(item, 1))
    model_id = _resolve_model(catalog["model_policy"], model_class, state)

    skill_ids: list[str] = []
    for role in roles:
        for skill_id in catalog["role_skills"].get(role, []):
            if skill_id not in skill_ids:
                skill_ids.append(skill_id)
    max_skills = int(catalog["limits"]["max_skills_per_node"])
    skills = tuple(skill_ids[:max_skills])
    capsules = tuple(
        str(catalog["skill_capsules"][skill_id]["instructions"])
        for skill_id in skills
    )
    catalog_raw = CATALOG_PATH.read_bytes()
    catalog_sha = hashlib.sha256(catalog_raw).hexdigest()
    resolution = {
        "node": node,
        "risk": risk,
        "roles": roles,
        "tools": tools,
        "model_class": model_class,
        "model_id": model_id,
        "skills": skills,
        "catalog_sha256": catalog_sha,
    }
    resolution_sha = hashlib.sha256(
        json.dumps(resolution, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return ExecutionProfile(
        node=node,
        risk=risk,
        roles=roles,
        tools=tools,
        model_class=model_class,
        model_id=model_id,
        skills=skills,
        skill_capsules=capsules,
        catalog_version=str(catalog["catalog_version"]),
        catalog_sha256=catalog_sha,
        resolution_sha256=resolution_sha,
    )


def governed_node(
    node: str,
    function: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> Callable[[Mapping[str, Any]], dict[str, Any]]:
    """Resolve a bounded execution profile immediately before one node runs."""

    @wraps(function)
    def wrapped(state: Mapping[str, Any]) -> dict[str, Any]:
        active_tools: tuple[str, ...] = ()
        project_id = str(state.get("project_id") or "")
        if project_id:
            try:
                from . import db

                active_tools = tuple(
                    str(item["tool_name"])
                    for item in db.get_project_tools(project_id)
                    if item.get("tool_name")
                )
            except Exception:
                active_tools = ()
        profile = resolve_execution_profile(
            state,
            node,
            active_tools=active_tools,
        )
        runtime_state = dict(state)
        runtime_state["resolved_execution_profile"] = profile.as_dict()
        result = dict(function(runtime_state))
        result["resolved_execution_profile"] = profile.as_dict()
        result["resolved_execution_history"] = [profile.as_dict()]
        return result

    return wrapped


def _resolve_model(
    policy: Mapping[str, Any],
    model_class: str,
    state: Mapping[str, Any],
) -> str | None:
    definition = policy.get(model_class) or {}
    env_name = str(definition.get("env") or "")
    configured = str(os.environ.get(env_name) or "").strip() if env_name else ""
    if configured:
        return configured
    source = definition.get("source")
    if source in ("none", "explicit_env_only", "explicit_env_or_deterministic"):
        return None
    model = str(state.get("model") or "").strip()
    provider = str(state.get("provider") or "").strip()
    if not model:
        return None
    if provider and ":" not in model:
        return f"{provider}:{model}"
    return model
