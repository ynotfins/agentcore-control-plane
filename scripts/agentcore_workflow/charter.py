"""AgentCore workflow — goal/charter synthesis into immutable macro/micro steps.

Charter rows live in ``agentcore.wf_charters``. This module is pure synthesis
plus helpers used by ``node_start`` / ``workflow_cli``; it does not own topology.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any


M6_MACRO_STEPS: list[dict[str, Any]] = [
    {"key": "M6.1", "label": "Apply M6 migration and verify schema", "ordinal": 1, "risk_class": "medium"},
    {"key": "M6.2", "label": "Initialize LangGraph checkpointer", "ordinal": 2, "risk_class": "medium"},
    {"key": "M6.3", "label": "Configure per-project capability profiles", "ordinal": 3, "risk_class": "high"},
    {"key": "M6.4", "label": "Validate project/thread isolation", "ordinal": 4, "risk_class": "high"},
    {"key": "M6.5", "label": "Run acceptance tests", "ordinal": 5, "risk_class": "medium"},
]

M6_MICRO_STEPS: list[dict[str, Any]] = [
    {"key": "M6.1.1", "label": "Run UP migration", "ordinal": 1, "risk_class": "medium", "macro_key": "M6.1"},
    {"key": "M6.1.2", "label": "Verify schema_migrations row", "ordinal": 2, "risk_class": "low", "macro_key": "M6.1"},
    {"key": "M6.2.1", "label": "Run setup_tables()", "ordinal": 1, "risk_class": "medium", "macro_key": "M6.2"},
    {"key": "M6.2.2", "label": "Smoke-test checkpoint write/read", "ordinal": 2, "risk_class": "low", "macro_key": "M6.2"},
    {"key": "M6.3.1", "label": "Seed core_active tools for project", "ordinal": 1, "risk_class": "low", "macro_key": "M6.3"},
    {"key": "M6.3.2", "label": "JIT lease test tool — verify expiry", "ordinal": 2, "risk_class": "medium", "macro_key": "M6.3"},
    {"key": "M6.4.1", "label": "Concurrent project isolation test", "ordinal": 1, "risk_class": "high", "macro_key": "M6.4"},
    {"key": "M6.5.1", "label": "Run all 18 acceptance checks", "ordinal": 1, "risk_class": "medium", "macro_key": "M6.5"},
]

M6_CHECKLIST_ITEMS: list[dict[str, Any]] = [
    {"key": "M6.1.1.a", "label": "Migration applied without errors", "ordinal": 1, "micro_key": "M6.1.1"},
    {"key": "M6.1.1.b", "label": "DOWN migration verified reversible", "ordinal": 2, "micro_key": "M6.1.1"},
    {"key": "M6.2.1.a", "label": "checkpoints schema created", "ordinal": 1, "micro_key": "M6.2.1"},
    {"key": "M6.3.2.a", "label": "JIT lease created", "ordinal": 1, "micro_key": "M6.3.2"},
    {"key": "M6.3.2.b", "label": "JIT lease expired on step completion", "ordinal": 2, "micro_key": "M6.3.2"},
    {"key": "M6.4.1.a", "label": "Project A tools invisible to Project B", "ordinal": 1, "micro_key": "M6.4.1"},
]


def use_m6_hardcoded_catalogue(
    milestone_key: str,
    *,
    acceptance_criteria: list | str | None = None,
    charter_override: bool = False,
) -> bool:
    """True when M6.1–M6.5 catalogue must be preserved (M6/M8 acceptance)."""
    if charter_override:
        return False
    if str(milestone_key or "") != "M6":
        return False
    if acceptance_criteria:
        if isinstance(acceptance_criteria, str) and acceptance_criteria.strip():
            return False
        if isinstance(acceptance_criteria, list) and any(str(x).strip() for x in acceptance_criteria):
            return False
    return True


def _normalize_acceptance(acceptance: list | str | None) -> list[str]:
    if acceptance is None:
        return []
    if isinstance(acceptance, str):
        lines = [ln.strip(" -*\t") for ln in acceptance.splitlines()]
        return [ln for ln in lines if ln]
    return [str(x).strip() for x in acceptance if str(x).strip()]


def _split_goal_bullets(goal: str) -> list[str]:
    text = (goal or "").strip()
    if not text:
        return ["Complete operator goal"]
    # Prefer explicit bullets / numbered lines
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    bullets: list[str] = []
    for ln in lines:
        m = re.match(r"^(?:[-*]|\d+[.)])\s+(.*)$", ln)
        if m:
            bullets.append(m.group(1).strip())
    if bullets:
        return bullets
    # Sentence split fallback (keep short goals as one unit)
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", text) if p.strip()]
    if len(parts) >= 2:
        return parts[:8]
    return [text]


def _risk_for_profile(risk_profile: str) -> str:
    rp = (risk_profile or "medium").strip().lower()
    if rp in ("low", "medium", "high", "critical"):
        return rp
    if rp in ("budget", "cost", "cheap"):
        return "low"
    if rp in ("strict", "prod", "production"):
        return "high"
    return "medium"


def synthesize_from_goal(
    goal: str,
    *,
    milestone_key: str = "G1",
    acceptance_criteria: list | str | None = None,
    risk_profile: str = "medium",
    title: str | None = None,
) -> dict[str, Any]:
    """Synthesize immutable requirement capture + macro/micro/checklist catalogue.

    Deterministic: same inputs always produce the same keys/labels/ordinals.
    """
    goal_text = (goal or "").strip() or "Operator goal (unspecified)"
    acceptance = _normalize_acceptance(acceptance_criteria)
    risk = _risk_for_profile(risk_profile)
    ms = re.sub(r"[^A-Za-z0-9]+", "", str(milestone_key or "G1")).upper() or "G1"
    digest = hashlib.sha256(goal_text.encode("utf-8")).hexdigest()[:8]

    bullets = _split_goal_bullets(goal_text)
    # Cap macros; fold remainder into the last macro label.
    macros: list[dict[str, Any]] = []
    for i, bullet in enumerate(bullets[:5], start=1):
        macros.append({
            "key": f"{ms}.{i}",
            "label": bullet[:200],
            "ordinal": i,
            "risk_class": risk if i == 1 else "medium",
        })
    if len(bullets) > 5:
        macros[-1]["label"] = (macros[-1]["label"] + " (+more)")[:200]

    micros: list[dict[str, Any]] = []
    checklists: list[dict[str, Any]] = []

    if acceptance:
        # One micro per acceptance criterion under the first macro; extra macros get a plan micro.
        first_macro = macros[0]["key"]
        for i, crit in enumerate(acceptance[:12], start=1):
            micro_key = f"{first_macro}.{i}"
            micros.append({
                "key": micro_key,
                "label": crit[:200],
                "ordinal": i,
                "risk_class": risk,
                "macro_key": first_macro,
            })
            checklists.append({
                "key": f"{micro_key}.a",
                "label": f"Accepted: {crit[:160]}",
                "ordinal": 1,
                "micro_key": micro_key,
            })
        for macro in macros[1:]:
            micro_key = f"{macro['key']}.1"
            micros.append({
                "key": micro_key,
                "label": f"Execute: {macro['label'][:160]}",
                "ordinal": 1,
                "risk_class": "medium",
                "macro_key": macro["key"],
            })
            checklists.append({
                "key": f"{micro_key}.a",
                "label": f"Completed: {macro['label'][:160]}",
                "ordinal": 1,
                "micro_key": micro_key,
            })
    else:
        for macro in macros:
            micro_key = f"{macro['key']}.1"
            micros.append({
                "key": micro_key,
                "label": f"Execute: {macro['label'][:160]}",
                "ordinal": 1,
                "risk_class": macro.get("risk_class", "medium"),
                "macro_key": macro["key"],
            })
            checklists.append({
                "key": f"{micro_key}.a",
                "label": f"Done: {macro['label'][:160]}",
                "ordinal": 1,
                "micro_key": micro_key,
            })
            checklists.append({
                "key": f"{micro_key}.b",
                "label": "Evidence recorded for this micro",
                "ordinal": 2,
                "micro_key": micro_key,
            })

    charter_title = title or f"Goal charter {ms}-{digest}"
    return {
        "title": charter_title,
        "goal": goal_text,
        "locked_milestones": [ms],
        "acceptance_criteria": acceptance,
        "macro_steps": macros,
        "micro_steps": micros,
        "checklist_items": checklists,
        "digest": digest,
    }


def m6_catalogue() -> dict[str, list[dict[str, Any]]]:
    return {
        "macro_steps": [dict(x) for x in M6_MACRO_STEPS],
        "micro_steps": [dict(x) for x in M6_MICRO_STEPS],
        "checklist_items": [dict(x) for x in M6_CHECKLIST_ITEMS],
    }


def first_micro_key(macro_steps: list[dict], micro_steps: list[dict], current_macro_key: str = "") -> str:
    """Return the first micro key for the current (or first) macro."""
    macro_key = current_macro_key or (macro_steps[0]["key"] if macro_steps else "")
    if not macro_key:
        return ""
    candidates = sorted(
        [m for m in micro_steps if m.get("macro_key") == macro_key],
        key=lambda x: int(x.get("ordinal") or 0),
    )
    return candidates[0]["key"] if candidates else ""
