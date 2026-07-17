from __future__ import annotations

import json
import shutil
from pathlib import Path

repo = Path(__file__).resolve().parents[1]
reg_path = repo / "contracts" / "bifrost-upstream-mcp-registry.json"
reg = json.loads(reg_path.read_text(encoding="utf-8"))

py = shutil.which("python") or r"C:\Users\ynotf\AppData\Local\Programs\Python\Python313\python.exe"
node = shutil.which("node") or r"C:\Program Files\nodejs\node.exe"
npx = shutil.which("npx.cmd") or r"C:\Program Files\nodejs\npx.cmd"
pwsh = shutil.which("pwsh") or r"C:\Program Files\PowerShell\7\pwsh.exe"

updates = {
    "agentcore-memory": {"executable_or_url": py, "health_check_type": "mcp_list_tools"},
    "agentcore-project-router": {"executable_or_url": py, "health_check_type": "mcp_list_tools"},
    "arabold-docs": {"executable_or_url": node},
    "context-fabric": {"executable_or_url": node},
    "sequential-thinking": {"executable_or_url": npx},
    "cursor-agent-mcp": {"executable_or_url": npx},
    "mcp-debugger": {"executable_or_url": npx},
    "playwright": {"executable_or_url": npx},
    "tentra": {"executable_or_url": npx},
    "obsidian-vault": {"executable_or_url": pwsh},
}

for cid, patch in updates.items():
    if cid in reg["servers"]:
        reg["servers"][cid].update(patch)

reg_path.write_text(json.dumps(reg, indent=2) + "\n", encoding="utf-8")
print("python", py)
print("node", node)
print("npx", npx)
print("pwsh", pwsh)
print("updated registry executables")
