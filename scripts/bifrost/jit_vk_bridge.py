"""AgentCore Bifrost JIT VK bridge.

Maps PostgreSQL capability leases to Bifrost virtual-key mcp_configs tool grants.

Security invariants:
- Never print or log secret values (admin key, virtual keys, OAuth tokens).
- Preserve existing mcp_configs[].id fields (Bifrost returns 409 if omitted incorrectly).
- No wildcard grants; exact tool names only.
- Failure leaves tools hidden (deny-by-default).
- Idempotent grant/revoke; restart-safe.
"""

from __future__ import annotations

import json
import logging
import os
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)

BIFROST_BASE = os.environ.get("AGENTCORE_BIFROST_BASE", "http://127.0.0.1:8080").rstrip("/")
ADMIN_KEY_ENV = "BIFROST_ADMIN_KEY"
REGISTRY_PATH = Path(__file__).resolve().parents[2] / "contracts" / "bifrost-upstream-mcp-registry.json"

# Bifrost numeric client id for openrouter (config_mcp_clients.id). Resolved live when possible.
OPENROUTER_CLIENT_NAME = "openrouter"
DEFAULT_VK_ID = "vk-agentcore-operator"

DENIED_ALWAYS = frozenset({"send-message", "generate-image"})


def load_permitted_tools(registry_path: Path = REGISTRY_PATH) -> list[str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    tools = list((registry.get("servers") or {}).get("openrouter", {}).get("permitted_tools") or [])
    return [t for t in tools if t not in DENIED_ALWAYS]


def ensure_openrouter_client_permitted_tools(registry_path: Path = REGISTRY_PATH) -> BridgeResult:
    """Expand the live openrouter MCP client's tools_to_execute to registry permitted_tools.

    Does not grant visibility to any VK. Failure leaves prior client filter in place.
    """
    permitted = load_permitted_tools(registry_path)
    if not permitted:
        return BridgeResult(False, "client_sync", "", (), "no_permitted_tools")
    try:
        payload = _request("GET", "/api/mcp/clients?limit=100")
        client_uuid = None
        for c in payload.get("clients") or []:
            cfg = c.get("config") or {}
            if cfg.get("name") == OPENROUTER_CLIENT_NAME:
                client_uuid = cfg.get("client_id")
                break
        if not client_uuid:
            return BridgeResult(False, "client_sync", "", tuple(permitted), "client_not_found")
        # Minimal PUT — Bifrost merges and preserves oauth_config_id.
        _request(
            "PUT",
            f"/api/mcp/client/{client_uuid}",
            {"name": OPENROUTER_CLIENT_NAME, "tools_to_execute": permitted},
        )
        return BridgeResult(True, "client_sync", "", tuple(permitted), "client_permitted_synced")
    except Exception as exc:  # noqa: BLE001
        logger.error("openrouter client tools sync failed: %s", type(exc).__name__)
        return BridgeResult(False, "client_sync", "", tuple(permitted), f"client_sync_failed:{type(exc).__name__}")


@dataclass(frozen=True)
class BridgeResult:
    ok: bool
    action: str
    vk_id: str
    tools: tuple[str, ...]
    detail: str


def _admin_headers() -> dict[str, str]:
    key = os.environ.get(ADMIN_KEY_ENV) or os.environ.get(ADMIN_KEY_ENV, "")
    # Prefer User-scope on Windows when process env is empty.
    if not key and os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                key, _ = winreg.QueryValueEx(k, ADMIN_KEY_ENV)
        except OSError:
            key = ""
    if not key:
        raise RuntimeError(f"{ADMIN_KEY_ENV} not set; JIT VK bridge cannot mutate Bifrost")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def _request(method: str, path: str, body: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    url = f"{BIFROST_BASE}{path}"
    data = None if body is None else json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=_admin_headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:400]
        raise RuntimeError(f"Bifrost {method} {path} failed: HTTP {exc.code}") from None


def load_tool_group(group_id: str, registry_path: Path = REGISTRY_PATH) -> list[str]:
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    groups = (registry.get("servers") or {}).get("openrouter", {}).get("tool_groups") or {}
    if group_id not in groups:
        raise KeyError(f"Unknown OpenRouter tool group: {group_id}")
    tools = list(groups[group_id].get("tools") or [])
    # Never grant denied tools even if a group mistakenly lists them.
    return [t for t in tools if t not in DENIED_ALWAYS]


def resolve_openrouter_client_id() -> int:
    """Resolve numeric mcp_client_id for openrouter from live VK configs or clients table via API."""
    payload = _request("GET", "/api/governance/virtual-keys?limit=100")
    for vk in payload.get("virtual_keys") or []:
        for mc in vk.get("mcp_configs") or []:
            client = mc.get("mcp_client") or {}
            if client.get("name") == OPENROUTER_CLIENT_NAME:
                return int(mc["mcp_client_id"])
    # Fallback: known live id from config_mcp_clients (openrouter=15). Prefer live DB when available.
    db_path = Path(r"H:\AgentRuntime\bifrost\data\config.db")
    if db_path.is_file():
        import sqlite3

        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        try:
            row = con.execute(
                "SELECT id FROM config_mcp_clients WHERE name = ? LIMIT 1",
                (OPENROUTER_CLIENT_NAME,),
            ).fetchone()
            if row:
                return int(row[0])
        finally:
            con.close()
    raise RuntimeError("Could not resolve openrouter mcp_client_id")


def get_virtual_key(vk_id: str) -> dict[str, Any]:
    payload = _request("GET", f"/api/governance/virtual-keys/{vk_id}")
    vk = payload.get("virtual_key") or payload
    if not vk.get("id"):
        raise RuntimeError(f"Virtual key not found: {vk_id}")
    return vk


def _sanitize_mcp_configs_for_put(mcp_configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep id + mcp_client_id + mcp_client_name + tools_to_execute — never echo secrets."""
    out: list[dict[str, Any]] = []
    for mc in mcp_configs:
        entry: dict[str, Any] = {
            "mcp_client_id": int(mc["mcp_client_id"]),
            "tools_to_execute": list(mc.get("tools_to_execute") or []),
        }
        if mc.get("id") is not None:
            entry["id"] = int(mc["id"])
        name = mc.get("mcp_client_name")
        if not name:
            name = (mc.get("mcp_client") or {}).get("name")
        if name:
            entry["mcp_client_name"] = name
        out.append(entry)
    return out


def put_virtual_key_mcp_configs(vk_id: str, mcp_configs: list[dict[str, Any]]) -> None:
    vk = get_virtual_key(vk_id)
    body = {
        "name": vk["name"],
        "is_active": bool(vk.get("is_active", True)),
        "mcp_configs": _sanitize_mcp_configs_for_put(mcp_configs),
    }
    # Preserve provider_configs ids if present (empty list is valid for MCP-only VKs).
    providers = []
    for pc in vk.get("provider_configs") or []:
        item: dict[str, Any] = {
            "provider": pc.get("provider"),
            "weight": pc.get("weight", 1),
            "allowed_models": pc.get("allowed_models") or ["*"],
            "allow_all_keys": bool(pc.get("allow_all_keys", True)),
        }
        if pc.get("id") is not None:
            item["id"] = pc["id"]
        providers.append(item)
    if providers:
        body["provider_configs"] = providers
    _request("PUT", f"/api/governance/virtual-keys/{vk_id}", body)


def _find_openrouter_cfg(mcp_configs: list[dict[str, Any]], client_id: int) -> Optional[dict[str, Any]]:
    for mc in mcp_configs:
        if int(mc.get("mcp_client_id") or -1) == client_id:
            return mc
        client = mc.get("mcp_client") or {}
        if client.get("name") == OPENROUTER_CLIENT_NAME:
            return mc
    return None


def grant_tools(
    tools: Iterable[str],
    *,
    vk_id: str = DEFAULT_VK_ID,
    client_id: Optional[int] = None,
) -> BridgeResult:
    exact = tuple(sorted({t for t in tools if t and t not in DENIED_ALWAYS and t != "*"}))
    if not exact:
        return BridgeResult(False, "grant", vk_id, (), "no grantable tools after deny filter")
    cid = client_id if client_id is not None else resolve_openrouter_client_id()
    vk = get_virtual_key(vk_id)
    configs = list(vk.get("mcp_configs") or [])
    existing = _find_openrouter_cfg(configs, cid)
    if existing is None:
        configs.append(
            {
                "mcp_client_id": cid,
                "mcp_client_name": OPENROUTER_CLIENT_NAME,
                "tools_to_execute": list(exact),
            }
        )
    else:
        # Idempotent: set exact leased set (do not union wildcards).
        existing["tools_to_execute"] = list(exact)
        existing["mcp_client_id"] = cid
        existing["mcp_client_name"] = OPENROUTER_CLIENT_NAME
    try:
        put_virtual_key_mcp_configs(vk_id, configs)
    except Exception as exc:  # noqa: BLE001 — failure must leave tools hidden
        logger.error("JIT grant failed for vk=%s: %s", vk_id, type(exc).__name__)
        return BridgeResult(False, "grant", vk_id, exact, f"grant_failed:{type(exc).__name__}")
    return BridgeResult(True, "grant", vk_id, exact, "granted")


def revoke_openrouter_tools(*, vk_id: str = DEFAULT_VK_ID, client_id: Optional[int] = None) -> BridgeResult:
    cid = client_id if client_id is not None else resolve_openrouter_client_id()
    vk = get_virtual_key(vk_id)
    configs = list(vk.get("mcp_configs") or [])
    existing = _find_openrouter_cfg(configs, cid)
    if existing is None:
        return BridgeResult(True, "revoke", vk_id, (), "already_absent")
    # Remove the openrouter mcp_config entry entirely (zero exposure).
    configs = [
        mc
        for mc in configs
        if int(mc.get("mcp_client_id") or -1) != cid
        and (mc.get("mcp_client") or {}).get("name") != OPENROUTER_CLIENT_NAME
    ]
    try:
        put_virtual_key_mcp_configs(vk_id, configs)
    except Exception as exc:  # noqa: BLE001
        logger.error("JIT revoke failed for vk=%s: %s", vk_id, type(exc).__name__)
        # Best-effort hide: try emptying tools list if delete-style put failed.
        try:
            vk2 = get_virtual_key(vk_id)
            configs2 = list(vk2.get("mcp_configs") or [])
            ex2 = _find_openrouter_cfg(configs2, cid)
            if ex2 is not None:
                ex2["tools_to_execute"] = []
                put_virtual_key_mcp_configs(vk_id, configs2)
                return BridgeResult(True, "revoke", vk_id, (), "cleared_tools_fallback")
        except Exception:
            pass
        return BridgeResult(False, "revoke", vk_id, (), f"revoke_failed:{type(exc).__name__}")
    return BridgeResult(True, "revoke", vk_id, (), "revoked")


def sync_lease_group(
    group_id: str,
    *,
    active: bool,
    vk_id: str = DEFAULT_VK_ID,
) -> BridgeResult:
    """Grant or revoke a named OpenRouter tool group for a VK."""
    if not active:
        return revoke_openrouter_tools(vk_id=vk_id)
    # Ensure client-level allow-list includes classified permitted tools (not denied).
    ensure_openrouter_client_permitted_tools()
    tools = load_tool_group(group_id)
    # Discovery leases must never include denied billable tools.
    if group_id == "openrouter-discovery-read":
        tools = [t for t in tools if t not in DENIED_ALWAYS]
    return grant_tools(tools, vk_id=vk_id)


def list_openrouter_tools_on_vk(vk_id: str = DEFAULT_VK_ID) -> list[str]:
    vk = get_virtual_key(vk_id)
    cid = resolve_openrouter_client_id()
    existing = _find_openrouter_cfg(list(vk.get("mcp_configs") or []), cid)
    if not existing:
        return []
    return list(existing.get("tools_to_execute") or [])
