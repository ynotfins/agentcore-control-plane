import os
import json
from pathlib import Path

plugin_dir = Path(r"C:\Users\ynotf\.cursor\plugins\cache")
if plugin_dir.exists():
    for p in plugin_dir.glob("**/*"):
        if p.name in ("manifest.json", "plugin.json", "package.json"):
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                name = data.get("name") or data.get("displayName") or data.get("id")
                print(f"{p}: name={name}")
            except Exception as e:
                print(f"{p}: error {e}")
