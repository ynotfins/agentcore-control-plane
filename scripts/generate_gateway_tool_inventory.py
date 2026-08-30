"""Generate .agentcore/runtime/gateway-tool-inventory.md from a tools/list JSON capture.

Usage:
  python scripts/generate_gateway_tool_inventory.py path/to/tools-list.json
  python scripts/generate_gateway_tool_inventory.py --from-stdio-sample

Never write this inventory into AGENTS.md.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / ".agentcore" / "runtime" / "gateway-tool-inventory.md"


def render(tools: list[dict]) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines = [
        "# Gateway tool inventory",
        "",
        f"Generated: {now}",
        "Source: agentcore-gateway tools/list (or listToolFiles-derived names)",
        "Policy: contracts/global-agent-policy.yaml id milestone-gateway-tool-inventory",
        "Do not paste this file into AGENTS.md or CLAUDE.md.",
        "",
        "Tool name :: server hint",
        "---------- :: -----------",
    ]
    for tool in sorted(tools, key=lambda t: str(t.get("name") or "")):
        name = str(tool.get("name") or "")
        server = ""
        if "_" in name:
            server = name.split("_", 1)[0]
        elif "-" in name:
            server = name.split("-", 1)[0]
        lines.append(f"`{name}` :: {server}")
    lines.append("")
    lines.append(f"Total tools: {len(tools)}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("json_path", nargs="?", help="Path to tools/list JSON result")
    ap.add_argument(
        "--from-stdio-sample",
        action="store_true",
        help="Use F: docs-store last tools list if present",
    )
    args = ap.parse_args()
    if args.from_stdio_sample:
        sample = Path(r"F:\AgentCore\runtime\docs-store\last-tools-list.json")
        raw = json.loads(sample.read_text(encoding="utf-8"))
    else:
        if not args.json_path:
            raise SystemExit("json_path required unless --from-stdio-sample")
        raw = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    tools = raw.get("tools") if isinstance(raw, dict) else raw
    if not isinstance(tools, list):
        if isinstance(raw, dict) and isinstance(raw.get("result"), dict):
            tools = raw["result"].get("tools") or []
        else:
            raise SystemExit("unrecognized tools/list shape")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(render(tools), encoding="utf-8", newline="\n")
    print(f"wrote {OUT} count={len(tools)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
