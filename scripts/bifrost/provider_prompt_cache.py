"""Provider prompt-cache policy, stable-prefix builder, and usage extractor.

Bifrost 2.0.0 has no provider-level prompt-cache toggle (no live
``providers.<name>.prompt_cache`` config field exists in the Bifrost schema).
Provider prompt caching is controlled entirely by request-body fields that an
inference client sends through Bifrost's OpenAI-compatible
``/v1/chat/completions`` route. This module is the single source of truth for
those fields so the renderer's ``agentcore_meta`` documentation and the live
proof probe cannot drift apart.

Scope: openai (direct) and openrouter (openai-family upstream) chat-completions
routes only. Live Bifrost ``providers.openai`` / ``providers.openrouter`` blocks
stay keys-only (see ``render_bifrost_config.py::build_bifrost_config``); this
module never emits a value that render_bifrost_config.py should place there.

Doc-derived facts (arabold-docs, openai@2026.9.14 and openrouter@2026.9.14):

- OpenAI prompt caching (models before GPT-5.6, e.g. gpt-4o-mini) is automatic
  once a request's hidden-content-excluded prefix reaches >= 1,024 visible
  input tokens; no opt-in field is required for the cache write/read itself.
- ``prompt_cache_key`` (root-level) is a routing hint for pre-GPT-5.6 models;
  it helps subsequent requests land on the same warm cache shard. It does not
  guarantee a hit and is not a cache toggle.
- ``prompt_cache_retention`` (root-level, pre-GPT-5.6 models) controls cache
  lifetime. Supported values for this family are ``in_memory`` (5-10 minutes
  inactive, up to ~1 hour) or ``24h`` (extended retention, model-allowlisted).
  ``in_memory`` is always a valid value for this family and requires no
  allowlist, so it is the value this module uses.
- OpenRouter forwards OpenAI-family requests to OpenAI's own automatic
  caching mechanism. OpenRouter's own explicit ``cache_control`` breakpoint
  mechanism (the ``{"type": "ephemeral"}`` block placed on a message content
  part) is documented for Anthropic, Google Gemini, and Alibaba Qwen
  families — not for OpenAI-family models. Sending ``cache_control`` on an
  OpenAI-routed request is harmless (inert / ignored by the OpenAI upstream)
  but is not itself the caching mechanism for this route. It is included here
  only for operator-locked parity with the Anthropic/Gemini request shape;
  the actual OpenRouter/OpenAI cache signal is the same automatic mechanism
  plus ``prompt_cache_key``.

This caveat is deliberately preserved in ``CACHE_POLICY`` (not silently
dropped) so the renderer's recorded policy documents the exact mechanism
rather than a wrong assumption.
"""
from __future__ import annotations

from typing import Any

# --- Stable, non-secret, deterministic prefix content -----------------------
#
# The prefix must be byte-identical across every call for a given route so a
# provider-side cache can actually be reused. It must never contain a
# timestamp, nonce, or secret. Text is padded to comfortably exceed 1,024
# visible input tokens (roughly 4 chars/token for English prose) using a
# fixed repeated paragraph rather than random content, so the resulting hash
# is reproducible run over run.

_STABLE_REFERENCE_PARAGRAPH = (
    "This is a stable, non-secret reference passage used only to establish a "
    "deterministic prompt-cache prefix for the AgentCore Bifrost provider "
    "prompt-cache proof. The passage content never changes between requests "
    "that share a route, and it never contains dynamic timestamps, nonces, "
    "secrets, or user data. Its only purpose is to exceed each provider's "
    "minimum cacheable-prefix length so that a second request sharing this "
    "exact system content and tool schema can be measured for a genuine "
    "provider-side prompt-cache read, separate from Bifrost's own exact-match "
    "hash-based semantic-cache plugin (dimension=1, Redis 127.0.0.1:6381). "
)

_STABLE_PREFIX_HEADER = (
    "AgentCore Bifrost Provider Prompt-Cache Reference (stable, non-secret).\n\n"
)

# Comfortably above the 1,024-token minimum for pre-GPT-5.6 OpenAI-family
# models even under a conservative (short) chars-per-token estimate.
DEFAULT_MIN_PREFIX_CHARS = 6000


def build_stable_system_prompt(min_chars: int = DEFAULT_MIN_PREFIX_CHARS) -> str:
    """Return a deterministic system-prompt prefix >= ``min_chars`` long.

    Same ``min_chars`` always yields byte-identical output; no randomness, no
    wall-clock content.
    """
    body = _STABLE_PREFIX_HEADER
    index = 0
    while len(body) < min_chars:
        body += f"[section {index}] {_STABLE_REFERENCE_PARAGRAPH}\n"
        index += 1
    return body


def build_stable_tools() -> list[dict[str, Any]]:
    """Return a deterministic, stable OpenAI-style tool/function schema list.

    Never invoked by the model in practice (probe replies "OK"); present only
    to extend the cacheable system+tools prefix with a realistic shape.
    """
    return [
        {
            "type": "function",
            "function": {
                "name": "agentcore_cache_probe_lookup",
                "description": (
                    "Stable no-op tool schema used only to extend the cached "
                    "system+tools prefix for the provider prompt-cache proof. "
                    "It is never actually invoked."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "Probe topic identifier; unused.",
                        },
                    },
                    "required": ["topic"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "agentcore_cache_probe_status",
                "description": (
                    "Second stable no-op tool schema for the same purpose; "
                    "kept separate so the tool-definition prefix has a "
                    "realistic multi-tool shape. Never actually invoked."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "route": {
                            "type": "string",
                            "description": "Route identifier; unused.",
                        },
                    },
                    "required": ["route"],
                },
            },
        },
    ]


SUPPORTED_PROVIDERS = ("openai", "openrouter")


def build_chat_request(
    *,
    model: str,
    provider: str,
    cache_key: str,
    user_suffix: str,
    max_tokens: int = 32,
) -> dict[str, Any]:
    """Build a chat-completions body with a stable system+tools prefix.

    ``provider`` selects which provider-specific cache fields are attached.
    The system+tools prefix is identical across calls; only ``user_suffix``
    varies, matching the locked probe shape (same prefix, different tail).
    """
    if provider not in SUPPORTED_PROVIDERS:
        raise ValueError(f"unsupported provider: {provider!r}")

    system_text = build_stable_system_prompt()
    tools = build_stable_tools()

    if provider == "openrouter":
        # Operator-locked parity field for the Anthropic/Gemini cache_control
        # shape. Per the module docstring, this is inert for OpenAI-family
        # upstream models; the real cache signal here is OpenAI's automatic
        # mechanism plus prompt_cache_key below. Included, not relied upon.
        system_message: dict[str, Any] = {
            "role": "system",
            "content": [
                {
                    "type": "text",
                    "text": system_text,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
        }
    else:
        system_message = {"role": "system", "content": system_text}

    body: dict[str, Any] = {
        "model": model,
        "messages": [
            system_message,
            {
                "role": "user",
                "content": (
                    "AgentCore prompt-cache probe. Reply with exactly OK. "
                    f"suffix={user_suffix}"
                ),
            },
        ],
        "tools": tools,
        # The probe tools are never meant to be invoked; force a plain text
        # reply so the model doesn't spend the (small) max_tokens budget on a
        # tool-call attempt. The tool schemas stay in the request either way,
        # so they remain part of the cached system+tools prefix.
        "tool_choice": "none",
        "max_tokens": max_tokens,
        "temperature": 0,
        "prompt_cache_key": cache_key,
    }
    if provider == "openai":
        # Pre-GPT-5.6 family; "in_memory" is always a supported retention
        # value for this family (no model allowlist required, unlike "24h").
        body["prompt_cache_retention"] = "in_memory"
    return body


def extract_usage_evidence(payload: dict[str, Any] | None) -> dict[str, Any]:
    """Pull structured, non-secret cache evidence out of a response payload.

    Never returns message content or bodies — only key names, counts, and
    flags. Checks multiple provider-field name variants defensively
    (``cached_tokens`` is the documented openai/openrouter field name;
    ``cached_read_tokens`` is checked as an alternate name some providers use).
    """
    payload = payload if isinstance(payload, dict) else {}
    usage = payload.get("usage")
    usage = usage if isinstance(usage, dict) else {}
    details = usage.get("prompt_tokens_details")
    details = details if isinstance(details, dict) else {}
    extra = payload.get("extra_fields")
    extra = extra if isinstance(extra, dict) else {}
    cache_debug = extra.get("cache_debug")
    cache_debug = cache_debug if isinstance(cache_debug, dict) else {}

    cached_tokens = details.get("cached_tokens")
    cached_read_tokens = details.get("cached_read_tokens")
    if cached_read_tokens is None:
        cached_read_tokens = usage.get("cached_read_tokens")
    cache_write_tokens = details.get("cache_write_tokens")

    return {
        "usage_keys": sorted(usage.keys()),
        "prompt_tokens_details_keys": sorted(details.keys()),
        "prompt_tokens": usage.get("prompt_tokens"),
        "completion_tokens": usage.get("completion_tokens"),
        "cached_tokens": cached_tokens,
        "cached_read_tokens": cached_read_tokens,
        "cache_write_tokens": cache_write_tokens,
        "cache_debug_present": bool(cache_debug),
        "hash_cache_hit": cache_debug.get("cache_hit") if cache_debug else None,
        "has_choices": bool(payload.get("choices")),
    }


def route_passes(evidence: dict[str, Any]) -> bool:
    """PASS rule: a provider cache-read signal, and not Bifrost's hash cache.

    ``cached_read_tokens`` or ``cached_tokens`` must be > 0, AND Bifrost's own
    exact-match hash cache_debug.cache_hit must not be True (a True hash-cache
    hit would explain token savings without proving provider-side caching).
    """
    cached_tokens = evidence.get("cached_tokens")
    cached_read_tokens = evidence.get("cached_read_tokens")
    token_signal = (isinstance(cached_tokens, (int, float)) and cached_tokens > 0) or (
        isinstance(cached_read_tokens, (int, float)) and cached_read_tokens > 0
    )
    return bool(token_signal) and evidence.get("hash_cache_hit") is not True


# --- Policy recorded into renderers/bifrost/config.sanitized.json's --------
# --- agentcore_meta block only. Never written into the live "providers" ----
# --- block; providers.openai / providers.openrouter stay keys-only. --------

CACHE_POLICY: dict[str, Any] = {
    "note": (
        "Bifrost 2.0.0 has no provider-level prompt-cache toggle; provider "
        "prompt caching is controlled entirely by request-body fields sent "
        "through Bifrost's OpenAI-compatible /v1/chat/completions route. "
        "This policy documents the exact fields; it is not a live Bifrost "
        "config surface and does not add keys to providers.openai / "
        "providers.openrouter."
    ),
    "implementation": "scripts/bifrost/provider_prompt_cache.py",
    "routes": {
        "openai_direct": {
            "model_example": "gpt-4o-mini",
            "mechanism": (
                "OpenAI automatic prefix caching (implicit breakpoints); no "
                "opt-in field enables the cache write/read itself."
            ),
            "minimum_cacheable_prefix_tokens": 1024,
            "request_fields": {
                "prompt_cache_key": (
                    "stable per-route string; optimizes routing to a warm "
                    "cache shard on models before GPT-5.6"
                ),
                "prompt_cache_retention": (
                    "in_memory; always-supported retention value for this "
                    "model family"
                ),
            },
            "usage_fields": ["usage.prompt_tokens_details.cached_tokens"],
        },
        "openrouter_openai": {
            "model_example": "openrouter/openai/gpt-4o-mini",
            "mechanism": (
                "OpenRouter forwards to OpenAI's own automatic prefix "
                "caching; OpenRouter's explicit cache_control breakpoints "
                "are documented for Anthropic/Gemini/Alibaba families, not "
                "OpenAI models."
            ),
            "minimum_cacheable_prefix_tokens": 1024,
            "request_fields": {
                "prompt_cache_key": (
                    "stable per-route string; also used by OpenRouter "
                    "provider sticky routing"
                ),
                "cache_control_on_system_block": (
                    "included for operator-locked request-shape parity with "
                    "the Anthropic/Gemini pattern; documented as inert for "
                    "OpenAI-family upstream per current openrouter docs"
                ),
            },
            "usage_fields": [
                "usage.prompt_tokens_details.cached_tokens",
                "usage.prompt_tokens_details.cache_write_tokens",
            ],
            "docs_caveat": (
                "openrouter@2026.9.14 prompt-caching guide documents "
                "cache_control breakpoints for Anthropic, Gemini, and "
                "Alibaba; OpenAI-family caching there is automatic with a "
                "1024-token minimum and no additional configuration."
            ),
        },
    },
    "pass_rule": (
        "A route passes only when the second call sharing the stable prefix "
        "reports cached_read_tokens or cached_tokens > 0 AND Bifrost's own "
        "hash cache_debug.cache_hit is not true (rules out the dimension=1 "
        "exact-match semantic-cache plugin as the source of token savings)."
    ),
    "non_goals": [
        "No live providers.*.prompt_cache field invented in Bifrost config "
        "(2.0.0 has none)",
        "No static OpenRouter x-session-id",
        "No change to MCP eager surface, Code Mode, device_assertion, "
        "enrollment, Stage B, or disable_content_logging",
    ],
}


def agentcore_meta_policy() -> dict[str, Any]:
    """Return the exact, secret-free policy block for agentcore_meta."""
    return CACHE_POLICY
