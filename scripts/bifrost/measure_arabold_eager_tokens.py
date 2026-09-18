"""Measure arabold-docs eager tools/list token cost (before + counterfactual after).

Live BEFORE: builder-profile MCP tools/list at http://127.0.0.1:8080/mcp.
AFTER variants are computed from the same live schemas (no Bifrost recycle):
  - code_mode: arabold schemas removed from eager list (0 arabold eager tools)
  - bounded_eager_subset: keep docs-first hot path only

Docs-first remains mandatory either way; this measures tool-list token cost only.
Never prints secrets or tool parameter default values that may contain env refs.
"""
from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
import winreg
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
EVIDENCE_JSON = REPO / "audits" / "bifrost" / "ARABOLD_EAGER_TOKEN_MEASUREMENT_2026-09-16.json"
EVIDENCE_MD = REPO / "audits" / "bifrost" / "ARABOLD_EAGER_TOKEN_MEASUREMENT_2026-09-16.md"

# Docs-first hot path: search/find/scrape/wait/list. Admin/maintenance stay out of
# the bounded eager subset counterfactual.
BOUNDED_SUBSET_SUFFIXES = {
    "search_docs",
    "find_version",
    "scrape_docs",
    "get_job_info",
    "list_libraries",
}

ARABOLD_NAME_RE = re.compile(
    r"(?i)^(arabold[_-]docs[-_])?(cancel_job|fetch_url|find_version|get_job_info|"
    r"list_jobs|list_libraries|refresh_version|remove_docs|scrape_docs|search_docs)$"
)


def get_user_env(name: str) -> str:
    val = os.environ.get(name, "")
    if val:
        return val
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment")
        val, _ = winreg.QueryValueEx(key, name)
        winreg.CloseKey(key)
        return str(val or "")
    except OSError:
        return ""


def mcp_tools_list(url: str, vk: str, timeout: int = 60) -> list[dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "Authorization": f"Bearer {vk}",
    }
    session = ""

    def post(payload: dict[str, Any]) -> dict[str, Any]:
        nonlocal session
        req_headers = dict(headers)
        if session:
            req_headers["Mcp-Session-Id"] = session
        body = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers=req_headers, method="POST")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            sid = resp.headers.get("Mcp-Session-Id") or resp.headers.get("mcp-session-id")
            if sid:
                session = sid
            raw = resp.read().decode("utf-8", errors="replace")
        if raw.startswith("event:") or "data:" in raw[:80]:
            data_lines = [
                line[5:].strip()
                for line in raw.splitlines()
                if line.startswith("data:")
            ]
            raw = data_lines[-1] if data_lines else "{}"
        return json.loads(raw)

    post(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "arabold-eager-token-measure", "version": "1.0"},
            },
        }
    )
    try:
        post({"jsonrpc": "2.0", "method": "notifications/initialized"})
    except Exception:
        pass
    listed = post({"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}})
    result = listed.get("result") or {}
    tools = result.get("tools") or []
    if not isinstance(tools, list):
        raise RuntimeError("tools/list did not return a tools array")
    return [t for t in tools if isinstance(t, dict)]


def tool_suffix(name: str) -> str:
    base = name.split("-")[-1] if "-" in name else name
    if "_" in base and base.startswith("arabold"):
        parts = name.replace("-", "_").split("_")
        return parts[-1] if parts else name
    # arabold_docs-search_docs -> search_docs
    if "-" in name:
        return name.split("-", 1)[-1]
    return name


def is_arabold_tool(name: str) -> bool:
    n = str(name or "")
    if n.lower().startswith("arabold_docs-") or n.lower().startswith("arabold-docs-"):
        return True
    return bool(ARABOLD_NAME_RE.match(n))


def compact_tool(tool: dict[str, Any]) -> dict[str, Any]:
    """Drop bulky optional fields similar to prior Phase A compact measurement."""
    keep = {
        "name": tool.get("name"),
        "description": tool.get("description"),
        "inputSchema": tool.get("inputSchema") or tool.get("input_schema"),
    }
    if tool.get("outputSchema") is not None:
        keep["outputSchema"] = tool.get("outputSchema")
    return keep


def estimate_tokens(text: str) -> dict[str, int]:
    """Prefer tiktoken o200k_base; fall back to char/4 estimate."""
    chars = len(text)
    out = {
        "chars": chars,
        "bytes_utf8": len(text.encode("utf-8")),
        "estimate_chars_div_4": max(1, (chars + 3) // 4) if chars else 0,
    }
    try:
        import tiktoken  # type: ignore

        enc = tiktoken.get_encoding("o200k_base")
        out["o200k_base"] = len(enc.encode(text))
    except Exception:
        out["o200k_base"] = out["estimate_chars_div_4"]
        out["o200k_base_source"] = "fallback_chars_div_4"
    else:
        out["o200k_base_source"] = "tiktoken"
    return out


def measure_set(tools: list[dict[str, Any]], label: str) -> dict[str, Any]:
    full = json.dumps(tools, ensure_ascii=False, separators=(",", ":"))
    compact = json.dumps(
        [compact_tool(t) for t in tools], ensure_ascii=False, separators=(",", ":")
    )
    names = sorted(str(t.get("name") or "") for t in tools)
    return {
        "label": label,
        "tool_count": len(tools),
        "tool_names": names,
        "full_json": estimate_tokens(full),
        "compact_json": estimate_tokens(compact),
    }


def decide(
    before_arabold: dict[str, Any],
    after_code_mode: dict[str, Any],
    after_bounded: dict[str, Any],
    total_before: dict[str, Any],
) -> dict[str, Any]:
    """Architectural decision from measured savings + docs-first friction."""
    before_tok = before_arabold["compact_json"]["o200k_base"]
    code_save = before_tok - after_code_mode["compact_json"]["o200k_base"]
    bounded_save = before_tok - after_bounded["compact_json"]["o200k_base"]
    total_tok = total_before["compact_json"]["o200k_base"]
    arabold_share = (before_tok / total_tok) if total_tok else 0.0

    # Keep arabold eager when:
    # - absolute arabold compact cost is modest relative to prior Phase A win, OR
    # - Code Mode would add discovery friction to the docs-first hot path every turn.
    # Prefer bounded subset only when it removes material tokens AND keeps the
    # docs-first tools (search/find/scrape/wait/list) eager.
    recommendation = "keep_full_eager"
    rationale = []
    # Docs-first foundation: keep all 10 arabold schemas eager unless the compact
    # cost is large. Code Mode adds discovery latency on every search_docs path;
    # tools_to_execute shrink without Code Mode drops tools entirely (Bifrost
    # is_code_mode_client is all-or-nothing per client).
    if before_tok < 2500 and arabold_share < 0.30:
        recommendation = "keep_full_eager"
        rationale.append(
            f"arabold compact o200k={before_tok} is modest "
            f"({arabold_share:.1%} of eager list); docs-first hot path benefits from "
            "direct tool schemas without Code Mode discovery latency."
        )
        rationale.append(
            f"counterfactual savings rejected: code_mode~{code_save}, "
            f"bounded_subset~{bounded_save} o200k — not worth docs-first friction "
            f"or dropping admin tools from tools_to_execute."
        )
    elif before_tok >= 2500 and bounded_save >= 800 and after_bounded["tool_count"] >= 5:
        recommendation = "bounded_eager_subset"
        rationale.append(
            f"bounded subset saves ~{bounded_save} compact o200k while keeping "
            f"{after_bounded['tool_count']} docs-first tools eager; remaining tools "
            "would be dropped from tools_to_execute (not available via Code Mode "
            "unless the whole client moves)."
        )
    else:
        recommendation = "code_mode"
        rationale.append(
            f"moving arabold to Code Mode saves ~{code_save} compact o200k; "
            "docs-first remains via listToolFiles/readToolFile/executeToolCode."
        )

    return {
        "recommendation": recommendation,
        "arabold_compact_o200k_before": before_tok,
        "savings_code_mode_o200k": code_save,
        "savings_bounded_subset_o200k": bounded_save,
        "arabold_share_of_eager_compact": round(arabold_share, 4),
        "rationale": rationale,
        "apply_live": False,
        "apply_note": (
            "Measurement-only this pass; no registry/renderer mutation and no "
            "Bifrost recycle. Operator may apply the recommendation in a follow-up."
        ),
    }


def main() -> int:
    health_url = "http://127.0.0.1:8080/health"
    try:
        with urllib.request.urlopen(health_url, timeout=10) as resp:
            health = json.loads(resp.read().decode("utf-8"))
            health_code = resp.status
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL: Bifrost health unreachable: {exc}", file=sys.stderr)
        return 2
    if health_code != 200 or (health.get("status") or "").lower() != "ok":
        print(f"FAIL: Bifrost unhealthy status={health!r}", file=sys.stderr)
        return 2

    vk = get_user_env("BIFROST_MCP_VIRTUAL_KEY")
    if not vk:
        print("FAIL: BIFROST_MCP_VIRTUAL_KEY missing", file=sys.stderr)
        return 2

    tools = mcp_tools_list("http://127.0.0.1:8080/mcp", vk)
    arabold = [t for t in tools if is_arabold_tool(str(t.get("name") or ""))]
    non_arabold = [t for t in tools if t not in arabold]
    bounded = [
        t
        for t in arabold
        if tool_suffix(str(t.get("name") or "")) in BOUNDED_SUBSET_SUFFIXES
        or str(t.get("name") or "").split("-")[-1] in BOUNDED_SUBSET_SUFFIXES
    ]

    before_all = measure_set(tools, "eager_all_before")
    before_arabold = measure_set(arabold, "arabold_eager_before")
    after_code_mode = measure_set([], "arabold_after_code_mode")
    after_bounded = measure_set(bounded, "arabold_after_bounded_eager_subset")
    after_all_code_mode = measure_set(non_arabold, "eager_all_if_arabold_code_mode")
    after_all_bounded = measure_set(
        non_arabold + bounded, "eager_all_if_arabold_bounded_subset"
    )

    decision = decide(before_arabold, after_code_mode, after_bounded, before_all)

    evidence = {
        "measurement_id": "ARABOLD_EAGER_TOKEN_MEASUREMENT_2026-09-16",
        "bifrost_health": {"http_status": health_code, "status": health.get("status")},
        "endpoint": "http://127.0.0.1:8080/mcp",
        "profile": "builder",
        "method": "tools/list",
        "secrets_printed": False,
        "before": {
            "eager_all": before_all,
            "arabold_only": before_arabold,
        },
        "after_counterfactual": {
            "note": (
                "Computed from the same live tools/list schemas without applying "
                "config or recycling Bifrost."
            ),
            "arabold_code_mode": after_code_mode,
            "arabold_bounded_eager_subset": after_bounded,
            "eager_all_if_arabold_code_mode": after_all_code_mode,
            "eager_all_if_arabold_bounded_subset": after_all_bounded,
            "bounded_subset_suffixes": sorted(BOUNDED_SUBSET_SUFFIXES),
        },
        "decision": decision,
        "acceptance": {
            "measured_before": before_arabold["tool_count"] > 0,
            "measured_after_counterfactuals": True,
            "evidence_json_written": True,
            "docs_first_unchanged": True,
        },
    }

    EVIDENCE_JSON.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_JSON.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    md_lines = [
        "# Arabold Eager Token Measurement (2026-09-16)",
        "",
        f"- Bifrost health: `{health.get('status')}` (HTTP {health_code})",
        f"- Eager tools/list total: **{before_all['tool_count']}**",
        f"- Arabold eager tools: **{before_arabold['tool_count']}** "
        f"(`{', '.join(before_arabold['tool_names'])}`)",
        f"- Arabold compact o200k BEFORE: "
        f"**{before_arabold['compact_json']['o200k_base']}** "
        f"({before_arabold['compact_json'].get('o200k_base_source')})",
        f"- AFTER Code Mode (counterfactual arabold eager=0): "
        f"**{after_code_mode['compact_json']['o200k_base']}** "
        f"(save {decision['savings_code_mode_o200k']})",
        f"- AFTER bounded subset ({after_bounded['tool_count']} tools): "
        f"**{after_bounded['compact_json']['o200k_base']}** "
        f"(save {decision['savings_bounded_subset_o200k']})",
        f"- Recommendation: **{decision['recommendation']}**",
        "",
        "## Rationale",
        "",
    ]
    for line in decision["rationale"]:
        md_lines.append(f"- {line}")
    md_lines.extend(
        [
            "",
            f"Evidence JSON: `{EVIDENCE_JSON.as_posix()}`",
            "",
            "No live Bifrost recycle. No registry mutation this pass.",
            "",
        ]
    )
    EVIDENCE_MD.write_text("\n".join(md_lines), encoding="utf-8")

    print(
        json.dumps(
            {
                "ok": True,
                "arabold_tool_count": before_arabold["tool_count"],
                "arabold_compact_o200k": before_arabold["compact_json"]["o200k_base"],
                "recommendation": decision["recommendation"],
                "evidence_json": str(EVIDENCE_JSON),
                "evidence_md": str(EVIDENCE_MD),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
