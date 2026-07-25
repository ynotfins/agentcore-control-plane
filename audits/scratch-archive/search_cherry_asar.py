"""Search extracted Cherry asar for Agent MCP / memory schema hints."""
from __future__ import annotations

import os
from pathlib import Path

root = Path(os.environ.get("TEMP", ".")) / "cherry-asar-extract" / "app"
print("exists", root.exists(), root)
if not root.exists():
    raise SystemExit(2)

hits: list[tuple[str, str, str]] = []
for p in root.rglob("*"):
    if not p.is_file():
        continue
    if p.suffix.lower() not in {".js", ".mjs", ".cjs", ".ts", ".tsx", ".json"}:
        continue
    if p.stat().st_size > 2_500_000:
        continue
    try:
        text = p.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        continue
    rel = str(p.relative_to(root))
    if "globalMemoryEnabled" in text:
        i = text.find("globalMemoryEnabled")
        snip = text[max(0, i - 120) : i + 180].replace("\n", " ")
        hits.append(("gmem", rel, snip[:260]))
    if ("mcps" in text) and ("agent" in text.lower()):
        if any(x in text for x in ("streamableHttp", "mcpServers", "serverIds", "allowed_tools", "claude-code")):
            i = text.find("mcps")
            snip = text[max(0, i - 100) : i + 220].replace("\n", " ")
            hits.append(("mcps", rel, snip[:280]))
    if len(hits) >= 40:
        break

for kind, rel, snip in hits[:40]:
    print("---", kind, rel)
    print(snip)
print("hit_count", len(hits))
