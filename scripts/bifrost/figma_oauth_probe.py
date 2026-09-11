#!/usr/bin/env python3
"""Secret-safe Bifrost Figma MCP OAuth first-auth probe.

Prints authorize_url when present. Never prints admin passwords or tokens.
"""

from __future__ import annotations

import base64
import json
import os
import urllib.error
import urllib.request
import winreg


def user_env(name: str) -> str:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as key:
            return str(winreg.QueryValueEx(key, name)[0])
    except OSError:
        return ""


def admin_headers() -> dict[str, str]:
    user = os.environ.get("BIFROST_ADMIN_USERNAME") or user_env("BIFROST_ADMIN_USERNAME")
    password = os.environ.get("BIFROST_ADMIN_PASSWORD") or user_env("BIFROST_ADMIN_PASSWORD")
    if not user or not password:
        raise SystemExit("BIFROST_ADMIN_USERNAME/PASSWORD missing from User/Process env")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }


def request(method: str, url: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=admin_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode(errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"raw": raw[:1500]}
        return exc.code, parsed


def main() -> int:
    _, clients = request("GET", "http://127.0.0.1:8080/api/mcp/clients?limit=200")
    figs = [
        client
        for client in clients.get("clients", [])
        if (client.get("config") or {}).get("name") == "figma_mcp"
    ]
    if len(figs) != 1:
        print(f"figma_client_count={len(figs)}")
        return 1
    client = figs[0]
    client_id = client["config"]["client_id"]
    print(f"state={client.get('state')}")
    print(f"client_id_present={bool(client_id)}")

    candidates = [
        f"/api/mcp/client/{client_id}/initiate-verification",
        f"/api/mcp/client/{client_id}/initiate_verification",
        f"/api/mcp/client/{client_id}/oauth/initiate",
        f"/api/mcp/client/{client_id}/start-oauth",
        f"/api/mcp/client/{client_id}/verify",
    ]
    for path in candidates:
        code, body = request("POST", "http://127.0.0.1:8080" + path)
        print(f"TRY {path} -> {code}")
        if not isinstance(body, dict):
            print(f" body={body!r}")
            continue
        print(f" keys={sorted(body.keys())}")
        auth = body.get("authorize_url") or body.get("authorization_url")
        if auth:
            print(f"AUTHORIZE_URL={auth}")
            return 0
        err = body.get("error")
        if isinstance(err, dict):
            print(f" err={err.get('message')}")
        elif "raw" in body:
            print(f" raw={body['raw'][:300]}")
        elif err:
            print(f" err={err}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
