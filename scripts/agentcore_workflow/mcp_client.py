"""Shared AgentCore gateway MCP client for LangGraph production and Studio.

Uses langchain-mcp-adapters MultiServerMCPClient over streamable HTTP.
Reads BIFROST_MCP_VK_WORKFLOW when set; otherwise BIFROST_MCP_VIRTUAL_KEY (builder).
Never persists or logs the resolved Authorization header.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Iterable, Optional, Sequence

logger = logging.getLogger(__name__)

GATEWAY_URL = os.environ.get("AGENTCORE_GATEWAY_MCP_URL", "http://127.0.0.1:8080/mcp")
GATEWAY_TIMEOUT_SECONDS = int(os.environ.get("AGENTCORE_GATEWAY_MCP_TIMEOUT", "300"))
VK_WORKFLOW_ENV = "BIFROST_MCP_VK_WORKFLOW"
VK_BUILDER_ENV = "BIFROST_MCP_VIRTUAL_KEY"
PINNED_ADAPTERS_VERSION = "0.3.0"


def _read_user_env(name: str) -> str:
    val = os.environ.get(name) or ""
    if val:
        return val
    if os.name == "nt":
        try:
            import winreg

            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment") as k:
                val, _ = winreg.QueryValueEx(k, name)
                return str(val or "")
        except OSError:
            return ""
    return ""


def resolve_workflow_vk() -> tuple[str, str]:
    """Return (env_name, key_value). Prefer workflow VK; fall back to builder."""
    wf = _read_user_env(VK_WORKFLOW_ENV)
    if wf:
        return VK_WORKFLOW_ENV, wf
    builder = _read_user_env(VK_BUILDER_ENV)
    if builder:
        return VK_BUILDER_ENV, builder
    raise RuntimeError(
        f"Neither {VK_WORKFLOW_ENV} nor {VK_BUILDER_ENV} is set in process/User env"
    )


@dataclass
class AgentCoreMcpSession:
    """Cached tool list with lease-aware refresh."""

    client: Any
    vk_env_name: str
    tools: list[Any] = field(default_factory=list)
    fetched_at: float = 0.0
    lease_epoch: int = 0

    def invalidate(self) -> None:
        self.tools = []
        self.fetched_at = 0.0


_SESSION: Optional[AgentCoreMcpSession] = None
_LEASE_EPOCH = 0


def bump_lease_epoch() -> int:
    """Call after lease activation/revocation so nodes refresh tools."""
    global _LEASE_EPOCH
    _LEASE_EPOCH += 1
    if _SESSION is not None:
        _SESSION.invalidate()
        _SESSION.lease_epoch = _LEASE_EPOCH
    return _LEASE_EPOCH


def create_agentcore_mcp_client(*, url: str = GATEWAY_URL) -> AgentCoreMcpSession:
    """Create a MultiServerMCPClient bound to agentcore-gateway.

    Decision: prefer BIFROST_MCP_VK_WORKFLOW when present; otherwise use the
    governed builder key with node-level tool filtering (see node_tool_policy.py).
    A dedicated permanent workflow profile is not required — OpenRouter and other
    JIT tools never appear without a lease on any VK.
    """
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            f"langchain-mcp-adapters=={PINNED_ADAPTERS_VERSION} is required"
        ) from exc

    if not url.startswith("http://127.0.0.1") and not url.startswith("http://localhost"):
        raise RuntimeError("AgentCore MCP client allows localhost gateway URLs only")

    env_name, vk = resolve_workflow_vk()
    # Header is constructed in-memory only; never log vk.
    headers = {"Authorization": f"Bearer {vk}"}
    client = MultiServerMCPClient(
        {
            "agentcore-gateway": {
                "transport": "http",
                "url": url,
                "headers": headers,
                "timeout": GATEWAY_TIMEOUT_SECONDS,
            }
        }
    )
    session = AgentCoreMcpSession(client=client, vk_env_name=env_name, lease_epoch=_LEASE_EPOCH)
    logger.info(
        "AgentCore MCP client created via %s (adapters=%s, url=%s)",
        env_name,
        PINNED_ADAPTERS_VERSION,
        url,
    )
    return session


def get_shared_mcp_session(*, force_new: bool = False) -> AgentCoreMcpSession:
    global _SESSION
    if force_new or _SESSION is None:
        _SESSION = create_agentcore_mcp_client()
    return _SESSION


async def refresh_gateway_tools(
    session: Optional[AgentCoreMcpSession] = None,
    *,
    allowed_names: Optional[Sequence[str]] = None,
) -> list[Any]:
    """Fetch tools from the gateway; optionally filter to exact names."""
    sess = session or get_shared_mcp_session()
    if sess.lease_epoch != _LEASE_EPOCH:
        sess.invalidate()
        sess.lease_epoch = _LEASE_EPOCH
    tools = await sess.client.get_tools()
    if allowed_names is not None:
        allow = set(allowed_names)
        tools = [t for t in tools if getattr(t, "name", None) in allow]
    sess.tools = list(tools)
    sess.fetched_at = time.time()
    return sess.tools


def filter_tools_by_names(tools: Iterable[Any], allowed_names: Sequence[str]) -> list[Any]:
    allow = set(allowed_names)
    return [t for t in tools if getattr(t, "name", None) in allow]


def tool_names(tools: Iterable[Any]) -> list[str]:
    return [getattr(t, "name", "") for t in tools if getattr(t, "name", None)]
