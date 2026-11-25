"""Paperclip backend over its local REST API (no second MCP, no data migration)."""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import urllib.error
import urllib.request
from typing import Any, Optional

from .backends import ALLOW_DIRECT_OPENROUTER

BASE = os.environ.get("AGENTCORE_DISPATCH_PAPERCLIP_URL", "http://127.0.0.1:3100").rstrip("/")
COMPANY = os.environ.get("AGENTCORE_DISPATCH_PAPERCLIP_COMPANY", "")
DONE = {"done": "succeeded", "cancelled": "cancelled", "blocked": "blocked", "in_review": "needs_review"}


class PaperclipError(RuntimeError):
    pass


def _call(method: str, path: str, body: Optional[dict] = None, timeout: float = 15) -> Any:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data, method=method,
                                 headers={"Content-Type": "application/json", "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        raise PaperclipError(f"paperclip {method} {path} -> HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise PaperclipError(f"paperclip unreachable: {exc}") from exc
    return json.loads(raw) if raw.strip() else None


def _items(payload: Any, *keys: str) -> list:
    if isinstance(payload, list):
        return payload
    for k in keys:
        if isinstance(payload, dict) and isinstance(payload.get(k), list):
            return payload[k]
    return []


_COMPANY_ID_CACHE: dict[str, str] = {}


def company_id() -> str:
    """Resolve the configured company to its id.

    ``AGENTCORE_DISPATCH_PAPERCLIP_COMPANY`` may be a company id or a company
    name; every API path needs the id, so a name is resolved once and cached.
    """
    key = COMPANY.strip()
    if key and key in _COMPANY_ID_CACHE:
        return _COMPANY_ID_CACHE[key]
    companies = _items(_call("GET", "/api/companies"), "companies", "data")
    if key:
        for c in companies:
            if key == c.get("id") or key.lower() == str(c.get("name") or "").strip().lower():
                _COMPANY_ID_CACHE[key] = c["id"]
                return c["id"]
        raise PaperclipError(
            f"AGENTCORE_DISPATCH_PAPERCLIP_COMPANY '{COMPANY}' matches no company id or name"
        )
    active = [c for c in companies if c.get("status") == "active"]
    if len(active) != 1:
        raise PaperclipError("set AGENTCORE_DISPATCH_PAPERCLIP_COMPANY (need exactly one active company)")
    return active[0]["id"]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


_OMNIROUTE_CACHE: dict[str, tuple[float, frozenset]] = {}
_OMNIROUTE_TTL_SEC = 60.0


def _omniroute_connection_ids(cid: str) -> frozenset:
    """AI-connection IDs that route to the loopback OmniRoute endpoint (:20128)."""
    import time

    now = time.time()
    hit = _OMNIROUTE_CACHE.get(cid)
    if hit and now - hit[0] < _OMNIROUTE_TTL_SEC:
        return hit[1]
    ids = set()
    try:
        payload = _call("GET", f"/api/companies/{cid}/ai-connections")
        for c in _items(payload, "connections", "aiConnections", "data"):
            if not isinstance(c, dict):
                continue
            base = str((c.get("routing") or {}).get("baseUrl") or "")
            name = str(c.get("name") or "")
            if ":20128" in base or "omniroute" in (base + " " + name).lower():
                if c.get("id"):
                    ids.add(c["id"])
    except PaperclipError:
        pass
    frozen = frozenset(ids)
    _OMNIROUTE_CACHE[cid] = (now, frozen)
    return frozen


def routing(agent: dict) -> str:
    adapter = agent.get("adapterType") or ""
    model = str((agent.get("adapterConfig") or {}).get("model") or "")
    if adapter == "process":
        return "no_model"
    binding = ((agent.get("runtimeConfig") or {}).get("aiConnection") or {})
    conn_id = binding.get("connectionId")
    if model.startswith("omniroute/"):
        return "omniroute"
    if conn_id:
        try:
            if conn_id in _omniroute_connection_ids(company_id()):
                return "omniroute"
        except PaperclipError:
            pass
    if adapter == "codex_local":
        return "subscription"
    return "direct_provider"


def runnable(agent: dict) -> tuple[bool, str]:
    if agent.get("status") == "paused":
        return False, "agent_paused"
    if routing(agent) == "direct_provider" and not ALLOW_DIRECT_OPENROUTER:
        return False, "routing_not_omniroute"
    return True, ""


def list_agents() -> list[dict]:
    cid = company_id()
    out = []
    for a in _items(_call("GET", f"/api/companies/{cid}/agents"), "agents", "data"):
        ok, why = runnable(a)
        out.append({"agent": f"paperclip/{slug(a['name'])}", "id": a["id"], "role": a.get("role"),
                    "adapter": a.get("adapterType"), "status": a.get("status"), "routing": routing(a),
                    "runnable": ok, "blocked_reason": why or None})
    return out


def find_agent(name: str) -> dict:
    want = name.split("/", 1)[-1]
    cid = company_id()
    for a in _items(_call("GET", f"/api/companies/{cid}/agents"), "agents", "data"):
        if slug(a["name"]) == want or a["id"] == want:
            return a
    raise PaperclipError(f"unknown paperclip agent: {name}")


def create_issue(agent: dict, task: str, workdir: str, job_id: str) -> dict:
    cid = company_id()
    title = (task.strip().splitlines() or ["Dispatched task"])[0][:120]
    body = {"title": title, "status": "todo", "assigneeAgentId": agent["id"], "parentId": None,
            "description": f"{task}\n\n---\nFiled by agentcore agent-dispatch job `{job_id}`. Workdir hint: `{workdir}`."}
    issue = _call("POST", f"/api/companies/{cid}/issues", body)
    if not isinstance(issue, dict) or not issue.get("id"):
        raise PaperclipError("paperclip issue create returned no id")
    return issue


def issue_state(issue_id: str) -> tuple[str, dict]:
    issue = _call("GET", f"/api/issues/{issue_id}")
    return DONE.get(issue.get("status"), "running"), issue


def issue_comments(issue_id: str) -> list[dict]:
    return _items(_call("GET", f"/api/issues/{issue_id}/comments"), "comments", "data")


def cancel_issue(issue_id: str) -> None:
    res = _call("PATCH", f"/api/issues/{issue_id}", {"status": "cancelled", "comment": "Cancelled via agent-dispatch job_cancel."})
    if not isinstance(res, dict) or res.get("status") != "cancelled":
        raise PaperclipError("paperclip cancel not confirmed")


def clear_zero_cost_unpriced(company: Optional[str] = None) -> dict:
    """Release a budget pause caused only by zero-cost unpriced usage.

    A process-adapter run can record usage with no price; with
    ``unpricedUsagePolicy=block`` that hard-stops the whole company. Only events
    already sitting at 0.00 are adjusted, so real spend can never be erased.
    """
    cid = company or company_id()
    health = _call("GET", f"/api/companies/{cid}/accounting/health")
    cleared, skipped = [], []
    for item in _items(health, "items", "data"):
        event_id = item.get("costEventId")
        if not event_id:
            continue
        stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
        body = {
            "idempotencyKey": f"agentcore-zero-unpriced-{event_id}-{stamp}",
            "expectedCents": "0",
            "correctedCents": "0",
            "reason": "Zero-cost unpriced usage from a no-model run; operator adjustment to release the budget hard-stop.",
            "pricing": {"source": "operator", "evidence": "agent-dispatch paperclip guard"},
        }
        try:
            _call("POST", f"/api/companies/{cid}/accounting/events/{event_id}/adjustments", body)
            cleared.append(event_id)
        except PaperclipError:
            skipped.append(event_id)
    resumed = False
    if cleared:
        try:
            _call("PATCH", f"/api/companies/{cid}", {"status": "active"})
            resumed = True
        except PaperclipError:
            pass
    return {"companyId": cid, "cleared": cleared, "skipped": skipped, "resumed": resumed}
