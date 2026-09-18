#!/usr/bin/env python3
"""Live proof: Serena shim accepts agentcore_project tool arg without sticky STDIO.

Posts JSON-RPC tools/call to http://127.0.0.1:18090/mcp with NO x-agentcore-project
header. Enrollment must succeed via arguments.agentcore_project=agentcore-control-plane.
Uses find_symbol (stable schema) rather than get_symbols_overview.

Does not enable sticky STDIO. Does not print secrets. Requires the shim listening on
127.0.0.1:18090 (ops/runtime start is out of band).

Usage:
  python scripts/bifrost/prove_serena_identity_injection.py
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

SHIM_URL = "http://127.0.0.1:18090/mcp"
PROJECT_KEY = "agentcore-control-plane"
PROJECT_ROOT = Path(r"D:\github\agentcore-control-plane").resolve()
ABS_RELATIVE = str(PROJECT_ROOT / "scripts" / "bifrost" / "session_identity.py")
REL_PATH = "scripts/bifrost/session_identity.py"
NAME_PATH_PATTERN = "extract_project_arg"
EVIDENCE = (
    PROJECT_ROOT
    / "audits"
    / "bifrost"
    / "SERENA_IDENTITY_INJECTION_EVIDENCE_2026-09-16.json"
)


def post_mcp(payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SHIM_URL,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read().decode("utf-8"))


def find_symbol_args(**extra: object) -> dict:
    # Only required schema field by default. Extra kwargs override/add filters.
    args: dict = {"name_path_pattern": NAME_PATH_PATTERN}
    args.update(extra)
    return args


def tools_call_ok(resp: dict) -> bool:
    if "error" in resp:
        return False
    result = resp.get("result")
    if not isinstance(result, dict):
        return result is not None
    if result.get("isError") is True:
        return False
    return True


def summarize_resp(resp: dict) -> str:
    if "error" in resp:
        return json.dumps(resp["error"], default=str)[:500]
    result = resp.get("result")
    if isinstance(result, dict):
        return json.dumps(
            {
                "isError": result.get("isError"),
                "keys": sorted(result.keys()),
                "preview": str(result)[:300],
            },
            default=str,
        )[:500]
    return f"{type(result).__name__}:{str(result)[:300]}"


def probe_param_variants() -> tuple[dict | None, dict]:
    """Try minimal → filtered find_symbol arg shapes; return (winning_resp, meta)."""
    variants: list[tuple[str, dict]] = [
        ("minimal", find_symbol_args(agentcore_project=PROJECT_KEY)),
        (
            "with_relative",
            find_symbol_args(
                agentcore_project=PROJECT_KEY,
                relative_path=REL_PATH,
            ),
        ),
        (
            "with_relative_no_body",
            find_symbol_args(
                agentcore_project=PROJECT_KEY,
                relative_path=REL_PATH,
                include_body=False,
            ),
        ),
        (
            "absolute_rewrite",
            find_symbol_args(
                agentcore_project=PROJECT_KEY,
                relative_path=ABS_RELATIVE,
            ),
        ),
    ]
    meta: dict = {"variants_tried": [], "winning_variant": None}
    for name, args in variants:
        resp = post_mcp(
            {
                "jsonrpc": "2.0",
                "id": 100 + len(meta["variants_tried"]),
                "method": "tools/call",
                "params": {"name": "find_symbol", "arguments": args},
            }
        )
        ok = tools_call_ok(resp)
        entry = {"name": name, "ok": ok, "summary": summarize_resp(resp)}
        meta["variants_tried"].append(entry)
        print(f"  variant={name} ok={ok} summary={entry['summary']}")
        if ok:
            meta["winning_variant"] = name
            return resp, meta
    return None, meta


def main() -> int:
    print("prove_serena_identity_injection: no sticky STDIO; no project headers")
    print(f"  target={SHIM_URL}")
    print(f"  agentcore_project={PROJECT_KEY}")
    print(f"  tool=find_symbol name_path_pattern={NAME_PATH_PATTERN}")

    init = post_mcp(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "prove-serena-identity", "version": "0.3.0"},
            },
        }
    )
    if "error" in init:
        print("FAIL initialize:", init["error"])
        return 1
    print("OK initialize")

    deny = post_mcp(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "find_symbol",
                "arguments": find_symbol_args(),
            },
        }
    )
    deny_ok = "error" in deny and "PROJECT_NOT_ENROLLED" in str(
        (deny.get("error") or {}).get("message", "")
    )
    print(f"OK deny_without_identity={deny_ok}")
    if not deny_ok:
        print("WARN deny response:", deny.get("error") or deny.get("result"))

    print("Probing find_symbol arg variants...")
    call, probe_meta = probe_param_variants()
    relative_ok = call is not None
    absolute_ok = probe_meta.get("winning_variant") == "absolute_rewrite"
    if not absolute_ok and relative_ok:
        # Separate absolute rewrite proof when a relative/minimal shape already won.
        abs_resp = post_mcp(
            {
                "jsonrpc": "2.0",
                "id": 4,
                "method": "tools/call",
                "params": {
                    "name": "find_symbol",
                    "arguments": find_symbol_args(
                        agentcore_project=PROJECT_KEY,
                        relative_path=ABS_RELATIVE,
                    ),
                },
            }
        )
        absolute_ok = tools_call_ok(abs_resp)
        print(f"  absolute_rewrite_followup ok={absolute_ok} summary={summarize_resp(abs_resp)}")

    if not relative_ok:
        print("FAIL: no find_symbol variant succeeded after identity enrollment")
        evidence = {
            "evidence_id": "SERENA_IDENTITY_INJECTION_EVIDENCE_2026-09-16",
            "shim_url": SHIM_URL,
            "tool": "find_symbol",
            "sticky_stdio": False,
            "headers_sent": False,
            "agentcore_project_arg": PROJECT_KEY,
            "relative_path_call_ok": False,
            "absolute_path_rewrite_ok": False,
            "deny_without_identity": deny_ok,
            "tools_call_ok": False,
            "probe": probe_meta,
            "secrets_printed": False,
            "pass": False,
        }
        EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
        EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
        print(f"evidence={EVIDENCE}")
        print("FAIL")
        return 2

    result = call.get("result") if call else None
    print("OK tools/call routed with agentcore_project arg (no headers, no sticky STDIO)")
    print(f"  absolute_path_rewrite_ok={absolute_ok}")
    print(f"  winning_variant={probe_meta.get('winning_variant')}")
    print("  result_type=", type(result).__name__)

    evidence = {
        "evidence_id": "SERENA_IDENTITY_INJECTION_EVIDENCE_2026-09-16",
        "shim_url": SHIM_URL,
        "tool": "find_symbol",
        "name_path_pattern": NAME_PATH_PATTERN,
        "sticky_stdio": False,
        "headers_sent": False,
        "agentcore_project_arg": PROJECT_KEY,
        "relative_path_call_ok": relative_ok,
        "absolute_path_rewrite_ok": absolute_ok,
        "deny_without_identity": deny_ok,
        "tools_call_ok": relative_ok,
        "probe": probe_meta,
        "secrets_printed": False,
        "pass": bool(deny_ok and relative_ok),
    }
    EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print(f"evidence={EVIDENCE}")
    print("PASS" if evidence["pass"] else "FAIL")
    return 0 if evidence["pass"] else 4


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except urllib.error.URLError as exc:
        print(f"FAIL: shim unreachable at {SHIM_URL}: {exc}")
        print("Start serena_session_shim on :18090, then re-run.")
        raise SystemExit(3) from exc
