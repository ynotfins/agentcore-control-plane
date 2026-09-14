from __future__ import annotations
import json
import os
import socket
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / 'audits' / 'bifrost' / 'BIFROST_HASH_CACHE_PROOF_2026-09-14.json'

def tcp(host: str, port: int, timeout: float = 2.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False

def admin_get(path: str):
    user = os.environ.get('BIFROST_ADMIN_USERNAME') or ''
    pw = os.environ.get('BIFROST_ADMIN_PASSWORD') or ''
    if not user or not pw:
        return None
    import base64
    token = base64.b64encode(f'{user}:{pw}'.encode()).decode()
    req = urllib.request.Request(
        f'http://127.0.0.1:8080{path}',
        headers={'Authorization': f'Basic {token}'},
        method='GET',
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode())

def chat(nonce: str):
    vk = os.environ.get('BIFROST_MCP_VIRTUAL_KEY') or ''
    # Prefer inference VK if present
    for key in ('BIFROST_INFERENCE_VIRTUAL_KEY', 'BIFROST_VK_BUILDER', 'BIFROST_MCP_VIRTUAL_KEY'):
        if os.environ.get(key):
            vk = os.environ[key]
            break
    body = {
        'model': os.environ.get('AGENTCORE_CACHE_PROBE_MODEL', 'gpt-4o-mini'),
        'messages': [{
            'role': 'user',
            'content': f'AgentCore hash-cache probe {nonce}. Reply with exactly OK.',
        }],
        'max_tokens': 8,
        'temperature': 0,
    }
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        'http://127.0.0.1:8080/v1/chat/completions',
        data=data,
        headers={
            'Authorization': f'Bearer {vk}',
            'Content-Type': 'application/json',
            'x-bf-cache-key': 'agentcore-hash-cache-probe-20260914',
        },
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        payload = json.loads(resp.read().decode())
        headers = {k.lower(): v for k, v in resp.headers.items()}
    extra = ((payload.get('extra_fields') or {}) if isinstance(payload, dict) else {})
    cache_debug = extra.get('cache_debug') if isinstance(extra, dict) else None
    usage = payload.get('usage') if isinstance(payload, dict) else None
    return {
        'http_cache_header_keys': sorted([k for k in headers if 'cache' in k]),
        'cache_debug_present': isinstance(cache_debug, dict),
        'cache_hit': (cache_debug or {}).get('cache_hit') if isinstance(cache_debug, dict) else None,
        'usage_keys': sorted(usage.keys()) if isinstance(usage, dict) else [],
        'has_choices': bool(payload.get('choices')) if isinstance(payload, dict) else False,
    }

def main() -> int:
    cfg = json.loads((REPO / 'renderers' / 'bifrost' / 'config.sanitized.json').read_text(encoding='utf-8'))
    plugins = cfg.get('plugins') or []
    sc = next((p for p in plugins if isinstance(p, dict) and p.get('name') == 'semantic_cache'), None)
    evidence = {
        'redis_6381_tcp': tcp('127.0.0.1', 6381),
        'disable_content_logging': (cfg.get('client') or {}).get('disable_content_logging') is True,
        'semantic_cache_config': {
            'enabled': bool(sc and sc.get('enabled')),
            'dimension': (sc or {}).get('config', {}).get('dimension'),
            'ttl': (sc or {}).get('config', {}).get('ttl'),
            'default_cache_key_set': bool((sc or {}).get('config', {}).get('default_cache_key')),
            'cache_by_model': (sc or {}).get('config', {}).get('cache_by_model'),
            'cache_by_provider': (sc or {}).get('config', {}).get('cache_by_provider'),
        },
        'vector_store_enabled': bool((cfg.get('vector_store') or {}).get('enabled')),
        'vector_store_type': (cfg.get('vector_store') or {}).get('type'),
    }
    try:
        live = admin_get('/api/plugins')
        rows = (live or {}).get('plugins') or []
        row = next((r for r in rows if (r.get('name') == 'semantic_cache' or r.get('actualName') == 'semantic_cache')), None)
        evidence['live_plugin'] = {
            'found': bool(row),
            'status': ((row or {}).get('status') or {}).get('status') if row else None,
        }
    except Exception as exc:
        evidence['live_plugin'] = {'found': False, 'error': type(exc).__name__}
    nonce = '20260914-phase-b'
    try:
        first = chat(nonce)
        second = chat(nonce)
        evidence['inference_probe'] = {'first': first, 'second': second, 'ok': True}
    except Exception as exc:
        evidence['inference_probe'] = {'ok': False, 'error': type(exc).__name__, 'detail': str(exc)[:180]}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print('PROOF_PATH', OUT)
    print(json.dumps(evidence, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
