"""Sanitized read-only inspect of Cherry agents.db model/provider fields."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

db = Path(os.environ["APPDATA"]) / "CherryStudio" / "Data" / "agents.db"
con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
con.row_factory = sqlite3.Row

tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")]
print("tables:", tables)
cols = [r[1] for r in con.execute("PRAGMA table_info(agents)")]
print("agent_cols:", cols)
interesting = [
    c
    for c in cols
    if any(x in c.lower() for x in ("model", "provider", "mcp", "config", "name", "id"))
]
print("interesting_cols:", interesting)

for r in con.execute(f"SELECT {', '.join(cols)} FROM agents"):
    d = dict(r)
    out = {}
    for k, v in d.items():
        lk = k.lower()
        if any(s in lk for s in ("key", "secret", "token", "password", "api")):
            out[k] = f"<redacted len={len(v) if v else 0}>"
        elif k == "instructions":
            out[k] = f"<len={len(v or '')}>"
        elif isinstance(v, str) and len(v) > 400:
            out[k] = v[:160] + "...<trunc>"
        else:
            out[k] = v
    print("AGENT:", json.dumps(out, default=str))

con.close()
