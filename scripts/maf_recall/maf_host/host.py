"""Minimal MAF host spike (does not own memory or MCP aggregation).

Pin: agent-framework==1.15.0 (see requirements.txt). Activate later — this file is a
documented stub so operators do not invent a second Postgres or a second :8080 server.

Binding intent (future):
  IDE / MAF SDK host
      -> agentcore-gateway http://127.0.0.1:8080/mcp
          -> Bifrost
              -> agentcore-memory -> SwarmRecall REST http://127.0.0.1:3300

This module MUST NOT:
  - create postgres://localhost:5432/agent_memory
  - create a new Postgres cluster on F:
  - replace Bifrost as the MCP aggregator
  - start a conflicting listener on :8080 by default
"""

from __future__ import annotations

import os
from dataclasses import dataclass


RECALL_REST_PLACEHOLDER = "http://127.0.0.1:3300"
GATEWAY_MCP_URL = "http://127.0.0.1:8080/mcp"
DEFAULT_OPENROUTER_MODEL = "deepseek/deepseek-v4-pro"
DEFAULT_FOUNDRY_DEPLOYMENT = "deepseek-v4-pro"


@dataclass(frozen=True)
class RecallContextProviderStub:
    """Placeholder context provider pointing at SwarmRecall REST (adapter path later)."""

    base_url: str = RECALL_REST_PLACEHOLDER

    def describe(self):
        return (
            "RecallContextProviderStub: semantic context should be fetched via "
            "agentcore-memory behind %s, using Recall at %s. "
            "Do not open direct IDE SQL to :65432."
            % (GATEWAY_MCP_URL, self.base_url)
        )


@dataclass(frozen=True)
class ProviderSelection:
    provider: str
    endpoint: str
    model: str
    auth_mode: str


@dataclass(frozen=True)
class GatewayRoutePlan:
    """Future route plan; do not hot-swap Bifrost without a separate acceptance gate."""

    current_gateway: str = GATEWAY_MCP_URL
    current_memory_facade: str = "agentcore-memory"
    future_maf_role: str = "policy/middleware host behind existing gateway contract"
    recall_adapter: str = "server-side Recall REST adapter"
    recall_rest: str = RECALL_REST_PLACEHOLDER
    no_peer_mesh: bool = True

    def invariant_summary(self):
        return (
            "GatewayRoutePlan: keep %s as the IDE contract; MAF adds policy/middleware "
            "behind the gateway, not a direct IDE mesh. Memory remains %s -> %s -> %s."
            % (
                self.current_gateway,
                self.current_gateway,
                self.current_memory_facade,
                self.recall_rest,
            )
        )


def choose_provider():
    foundry_endpoint = os.environ.get("AZURE_AI_PROJECT_ENDPOINT") or os.environ.get(
        "FOUNDRY_PROJECT_ENDPOINT", ""
    )
    foundry_model = os.environ.get("AZURE_AI_MODEL_DEPLOYMENT_NAME", DEFAULT_FOUNDRY_DEPLOYMENT)
    if foundry_endpoint.strip() and foundry_model.strip():
        return ProviderSelection(
            provider="azure_foundry",
            endpoint=foundry_endpoint.strip(),
            model=foundry_model.strip(),
            auth_mode="azure_cli_or_entra",
        )

    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        return ProviderSelection(
            provider="openrouter_fallback",
            endpoint="https://openrouter.ai/api/v1",
            model=os.environ.get("OPENROUTER_MODEL", DEFAULT_OPENROUTER_MODEL).strip(),
            auth_mode="api_key_env",
        )

    return ProviderSelection(
        provider="unconfigured",
        endpoint="",
        model="",
        auth_mode="missing_provider_credentials",
    )


def build_host_notes():
    provider = choose_provider()
    route = GatewayRoutePlan()
    return {
        "sdk_pin": "agent-framework==1.15.0",
        "gateway": GATEWAY_MCP_URL,
        "recall_rest": RECALL_REST_PLACEHOLDER,
        "postgres_policy": "no-new-maf-postgres-on-F",
        "checkpoint_policy": "langgraph-remains-pg18-55433",
        "route_plan": route.invariant_summary(),
        "provider_preference": provider.provider,
        "provider_endpoint": provider.endpoint or "unset",
        "provider_model": provider.model or "unset",
        "provider_auth_mode": provider.auth_mode,
    }


def maybe_bind_debug_server():
    """Optional debug bind — off unless MAF_HOST_BIND=1.

    Never bind :8080 here; that port is reserved for Bifrost / agentcore-gateway.
    """
    if os.environ.get("MAF_HOST_BIND") != "1":
        return
    bind_host = os.environ.get("MAF_HOST_ADDR", "127.0.0.1")
    bind_port = os.environ.get("MAF_HOST_PORT", "8091")
    if bind_port == "8080":
        raise RuntimeError("Refusing to bind MAF host on :8080 (reserved for Bifrost)")
    print("[maf_host] debug bind requested on %s:%s (stub; no listen)" % (bind_host, bind_port))


def main():
    provider = RecallContextProviderStub()
    notes = build_host_notes()
    print("[maf_host] spike")
    print(provider.describe())
    for key, value in notes.items():
        print("  %s=%s" % (key, value))
    maybe_bind_debug_server()


if __name__ == "__main__":
    main()
