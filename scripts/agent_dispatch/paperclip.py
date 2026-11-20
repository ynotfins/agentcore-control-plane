"""Paperclip backend over its local REST API (no second MCP, no data migration)."""

from __future__ import annotations

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


def company_id() -> str:
    if COMPANY:
        return COMPANY
    active = [c for c in _items(_call("GET", "/api/companies"), "companies", "data") if c.get("status") == "active"]
    if len(active) != 1:
        raise PaperclipError("set AGENTCORE_DISPATCH_PAPERCLIP_COMPANY (need exactly one active company)")
    return active[0]["id"]


def slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def routing(agent: dict) -> str:
    adapter = agent.get("adapterType") or ""
    model = str((agent.get("adapterConfig") or {}).get("model") or "")
    if adapter == "process":
        return "no_model"
    if model.startswith("omniroute/"):
        return "omniroute"
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
