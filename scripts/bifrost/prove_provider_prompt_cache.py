"""Live proof: provider prompt-cache reads on openai/openrouter chat routes.

Probes POST http://127.0.0.1:8080/v1/chat/completions through the live Bifrost
gateway (builder virtual key) for two routes:

  - openai direct:    model "gpt-4o-mini"
  - openrouter:       model "openrouter/openai/gpt-4o-mini"

For each route, sends two calls sharing the exact same stable system+tools
prefix (see provider_prompt_cache.build_stable_system_prompt /
build_stable_tools) with a different user-message suffix, and the same
prompt_cache_key. A route PASSes only when the second call's usage shows
cached_read_tokens or cached_tokens > 0 AND Bifrost's own hash
cache_debug.cache_hit is not true (rules out the dimension=1 exact-match
semantic-cache plugin as the explanation).

Writes audits/bifrost/BIFROST_PROVIDER_PROMPT_CACHE_PROOF_2026-09-14.json.
Evidence JSON only: usage keys, prompt_tokens counts, cache counters,
hash_cache_hit. Never writes message bodies, tool schemas, or secret values.

Run: python scripts/bifrost/prove_provider_prompt_cache.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / "audits" / "bifrost" / "BIFROST_PROVIDER_PROMPT_CACHE_PROOF_2026-09-14.json"
GATEWAY_URL = "http://127.0.0.1:8080/v1/chat/completions"


def _load_ppc():
    spec = importlib.util.spec_from_file_location(
        "provider_prompt_cache", REPO / "scripts" / "bifrost" / "provider_prompt_cache.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PPC = _load_ppc()


def _resolve_virtual_key() -> str:
    for key in ("BIFROST_INFERENCE_VIRTUAL_KEY", "BIFROST_VK_BUILDER", "BIFROST_MCP_VIRTUAL_KEY"):
        value = os.environ.get(key)
        if value:
            return value
    return ""


def _post_chat(body: dict[str, Any], *, vk: str, timeout: float = 90.0) -> dict[str, Any]:
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        GATEWAY_URL,
        data=data,
        headers={
            "Authorization": f"Bearer {vk}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Console-only diagnostic (stderr), never persisted to the evidence
        # JSON: request bodies/response bodies must not land in the audit file.
        if os.environ.get("AGENTCORE_PROVE_PROMPT_CACHE_DEBUG") == "1":
            try:
                detail = exc.read().decode("utf-8", errors="replace")[:800]
            except Exception:  # noqa: BLE001
                detail = "<unreadable>"
            print(f"DEBUG_HTTP_ERROR {exc.code} {detail}", flush=True)
            raise urllib.error.HTTPError(exc.url, exc.code, exc.reason, exc.headers, None) from None
        raise


def probe_route(*, model: str, provider: str, vk: str) -> dict[str, Any]:
    cache_key = f"agentcore-p1-prompt-cache-{provider}-{uuid.uuid4().hex[:12]}"
    calls: list[dict[str, Any]] = []
    error: str | None = None
    try:
        for suffix in ("first", "second"):
            body = PPC.build_chat_request(
                model=model,
                provider=provider,
                cache_key=cache_key,
                user_suffix=f"{suffix}-{uuid.uuid4().hex[:8]}",
            )
            payload = _post_chat(body, vk=vk)
            calls.append(PPC.extract_usage_evidence(payload))
            time.sleep(2.5)
    except urllib.error.HTTPError as exc:
        error = f"HTTPError {exc.code}: {exc.reason}"
    except urllib.error.URLError as exc:
        error = f"URLError: {exc.reason}"
    except Exception as exc:  # noqa: BLE001
        error = f"{type(exc).__name__}: {str(exc)[:200]}"

    second_evidence = calls[1] if len(calls) == 2 else None
    passed = bool(second_evidence and PPC.route_passes(second_evidence))
    return {
        "provider": provider,
        "model": model,
        "cache_key_prefix": cache_key.rsplit("-", 1)[0] + "-<redacted-suffix>",
        "calls": calls,
        "error": error,
        "pass": passed,
    }


def main() -> int:
    vk = _resolve_virtual_key()
    evidence: dict[str, Any] = {
        "gateway_url": GATEWAY_URL,
        "vk_env_present": bool(vk),
        "routes": {},
        "overall_pass": False,
    }
    if not vk:
        evidence["error"] = (
            "No BIFROST_INFERENCE_VIRTUAL_KEY / BIFROST_VK_BUILDER / "
            "BIFROST_MCP_VIRTUAL_KEY environment value found."
        )
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print("PROOF_PATH", OUT)
        print(json.dumps(evidence, indent=2))
        return 1

    openai_result = probe_route(model="gpt-4o-mini", provider="openai", vk=vk)
    openrouter_result = probe_route(
        model="openrouter/openai/gpt-4o-mini", provider="openrouter", vk=vk
    )
    evidence["routes"] = {
        "openai_direct": openai_result,
        "openrouter_openai": openrouter_result,
    }
    evidence["overall_pass"] = bool(openai_result["pass"] or openrouter_result["pass"])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("PROOF_PATH", OUT)
    print(json.dumps(evidence, indent=2))
    return 0 if evidence["overall_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
