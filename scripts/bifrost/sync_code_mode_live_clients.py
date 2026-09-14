"""Sync registry is_code_mode_client flags into live Bifrost config.db clients."""
from __future__ import annotations

import base64
import json
import os
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / 'contracts' / 'bifrost-upstream-mcp-registry.json'
BASE = os.environ.get('BIFROST_BASE_URL', 'http://127.0.0.1:8080')


def admin_headers() -> dict[str, str]:
    user = os.environ.get('BIFROST_ADMIN_USERNAME') or ''
    password = os.environ.get('BIFROST_ADMIN_PASSWORD') or ''
    if not user or not password:
        raise SystemExit('BIFROST_ADMIN_USERNAME/PASSWORD required')
    token = base64.b64encode(f'{user}:{password}'.encode()).decode()
    return {'Authorization': f'Basic {token}', 'Content-Type': 'application/json'}


def api(method: str, path: str, body: dict | None = None):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(f'{BASE}{path}', data=data, headers=admin_headers(), method=method)
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read().decode()
        return json.loads(raw) if raw else {}


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding='utf-8'))
    desired = {
        (server.get('bifrost_client_name') or sid): bool(server.get('is_code_mode_client') is True)
        for sid, server in (registry.get('servers') or {}).items()
        if isinstance(server, dict) and server.get('enabled')
    }
    live = api('GET', '/api/mcp/clients?limit=100')
    rows = live.get('clients') or []
    by_name = {}
    for row in rows:
        cfg = row.get('config') or {}
        name = cfg.get('name')
        if name:
            by_name[name] = cfg
    updated = []
    for name, want in sorted(desired.items()):
        cfg = by_name.get(name)
        if not cfg:
            print('SKIP_MISSING', name)
            continue
        have = bool(cfg.get('is_code_mode_client') is True)
        if have == want:
            print('OK', name, want)
            continue
        cid = cfg.get('client_id')
        if not cid:
            print('SKIP_NO_ID', name)
            continue
        api('PUT', f'/api/mcp/client/{cid}', {'is_code_mode_client': want})
        updated.append(name)
        print('UPDATED', name, 'to', want)
    print('SYNC_DONE updated_count', len(updated))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
