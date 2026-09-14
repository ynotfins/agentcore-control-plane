"""Sync rendered is_code_mode_client flags into live Bifrost config.db clients.

Bifrost v2.0.0 keeps MCP client runtime state in SQLite config.db. Copying a
rendered config.json does not update existing client rows while the process is
already running, and restart reconciliation can leave is_code_mode_client stale.
PUT /api/mcp/client/{id} with only {is_code_mode_client: bool}.
Never prints secret values.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable

REPO = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO / "contracts" / "bifrost-upstream-mcp-registry.json"
DEFAULT_RENDERED = REPO / "renderers" / "bifrost" / "config.json"
LIVE_RENDERED = Path(r"F:\AgentCore\runtime\bifrost\config.json")
DEFAULT_BASE = os.environ.get("BIFROST_BASE_URL", "http://127.0.0.1:8080")
ADMIN_USERNAME_ENV = "BIFROST_ADMIN_USERNAME"
ADMIN_PASSWORD_ENV = "BIFROST_ADMIN_PASSWORD"


def read_env(name: str) -> str:
    value = os.environ.get(name) or ""
    if not value and os.name == "nt":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
                value, _ = winreg.QueryValueEx(key, name)
        except OSError:
            value = ""
    return str(value or "")


def admin_headers() -> dict[str, str]:
    user = read_env(ADMIN_USERNAME_ENV)
    password = read_env(ADMIN_PASSWORD_ENV)
    if not user or not password:
        raise RuntimeError("%s/%s required" % (ADMIN_USERNAME_ENV, ADMIN_PASSWORD_ENV))
    token = base64.b64encode(("%s:%s" % (user, password)).encode("utf-8")).decode("ascii")
    return {"Authorization": "Basic %s" % token, "Content-Type": "application/json", "Accept": "application/json"}


def request_json(method: str, path: str, body: dict[str, Any] | None = None, *, base: str = DEFAULT_BASE) -> dict[str, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(base.rstrip("/") + path, data=data, headers=admin_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raise RuntimeError("Bifrost %s %s failed: HTTP %s" % (method, path, exc.code)) from None


def desired_flags(registry: dict[str, Any], rendered: dict[str, Any] | None = None) -> dict[str, bool]:
    desired: dict[str, bool] = {}
    for sid, server in (registry.get("servers") or {}).items():
        if not isinstance(server, dict) or not server.get("enabled"):
            continue
        name = str(server.get("bifrost_client_name") or sid)
        desired[name] = server.get("is_code_mode_client") is True
    if not rendered:
        return desired
    rendered_flags: dict[str, bool] = {}
    for client in ((rendered.get("mcp") or {}).get("client_configs")) or []:
        if isinstance(client, dict) and client.get("name"):
            rendered_flags[str(client["name"])] = client.get("is_code_mode_client") is True
    for name in list(desired):
        if name in rendered_flags:
            desired[name] = rendered_flags[name]
    return desired


def index_live_clients(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    by_name: dict[str, dict[str, Any]] = {}
    for row in payload.get("clients") or []:
        cfg = row.get("config") or {}
        name = cfg.get("name")
        if name:
            by_name[str(name)] = cfg
    return by_name


def plan_sync(desired: dict[str, bool], live: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for name, want in sorted(desired.items()):
        cfg = live.get(name)
        if not cfg:
            rows.append({"name": name, "action": "skip_missing", "want": want, "have": None, "client_id": None})
            continue
        have = cfg.get("is_code_mode_client") is True
        cid = cfg.get("client_id")
        if have == want:
            action = "ok"
        elif not cid:
            action = "skip_no_id"
        else:
            action = "drift"
        rows.append({"name": name, "action": action, "want": want, "have": have, "client_id": cid})
    return rows


def apply_plan(rows: list[dict[str, Any]], *, mode: str, requester: Callable[[str, str, dict[str, Any] | None], dict[str, Any]]) -> list[str]:
    updated: list[str] = []
    if mode != "apply":
        return updated
    for row in rows:
        if row["action"] != "drift":
            continue
        requester("PUT", "/api/mcp/client/%s" % row["client_id"], {"is_code_mode_client": bool(row["want"])})
        row["action"] = "updated"
        row["have"] = bool(row["want"])
        updated.append(str(row["name"]))
    return updated


def resolve_rendered_path(explicit: str | None) -> Path | None:
    if explicit:
        path = Path(explicit)
        return path if path.is_file() else None
    if LIVE_RENDERED.is_file():
        return LIVE_RENDERED
    if DEFAULT_RENDERED.is_file():
        return DEFAULT_RENDERED
    return None


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def report_rows(rows: list[dict[str, Any]]) -> None:
    for row in rows:
        action = str(row["action"]).upper()
        name = row["name"]
        if action in {"OK", "UPDATED"}:
            print(action, name, row["want"])
        elif action == "DRIFT":
            print("DRIFT", name, "have", row["have"], "want", row["want"])
        elif action == "SKIP_MISSING":
            print("SKIP_MISSING", name)
        elif action == "SKIP_NO_ID":
            print("SKIP_NO_ID", name)
        else:
            print(action, name)


def evidence_payload(*, mode: str, rendered_path: str | None, rows: list[dict[str, Any]], updated: list[str]) -> dict[str, Any]:
    return {
        "mode": mode,
        "rendered_path_kind": (
            "live" if rendered_path and str(rendered_path).startswith(r"F:\AgentCore\runtime\bifrost")
            else "repo" if rendered_path else "registry_only"
        ),
        "desired_count": sum(1 for row in rows if row["action"] != "skip_missing"),
        "ok": [row["name"] for row in rows if row["action"] == "ok"],
        "drift": [row["name"] for row in rows if row["action"] == "drift"],
        "updated": updated,
        "skip_missing": [row["name"] for row in rows if row["action"] == "skip_missing"],
        "skip_no_id": [row["name"] for row in rows if row["action"] == "skip_no_id"],
        "code_mode_true": [row["name"] for row in rows if row["want"] is True and row["action"] != "skip_missing"],
        "code_mode_false": [row["name"] for row in rows if row["want"] is False and row["action"] != "skip_missing"],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("check", "apply"), default="check")
    parser.add_argument("--registry", default=str(DEFAULT_REGISTRY))
    parser.add_argument("--config", default="", help="Rendered Bifrost config.json path")
    parser.add_argument("--base-url", default=DEFAULT_BASE)
    parser.add_argument("--json-out", default="", help="Write sanitized evidence JSON")
    args = parser.parse_args(argv)
    registry = load_json(Path(args.registry))
    rendered_path = resolve_rendered_path(args.config or None)
    rendered = load_json(rendered_path) if rendered_path else None
    desired = desired_flags(registry, rendered)
    try:
        live_payload = request_json("GET", "/api/mcp/clients?limit=100", base=args.base_url)
    except RuntimeError as exc:
        print("SYNC_FAIL %s" % exc)
        return 1
    rows = plan_sync(desired, index_live_clients(live_payload))
    try:
        updated = apply_plan(rows, mode=args.mode, requester=lambda method, path, body: request_json(method, path, body, base=args.base_url))
    except RuntimeError as exc:
        print("SYNC_FAIL %s" % exc)
        return 1
    report_rows(rows)
    drift = [row["name"] for row in rows if row["action"] == "drift"]
    evidence = evidence_payload(mode=args.mode, rendered_path=str(rendered_path) if rendered_path else None, rows=rows, updated=updated)
    if args.json_out:
        Path(args.json_out).write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("SYNC_DONE", "mode", args.mode, "updated_count", len(updated), "drift_count", len(drift))
    if args.mode == "check" and drift:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
