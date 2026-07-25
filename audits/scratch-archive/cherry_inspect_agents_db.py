"""Inspect Cherry agents.db schema/rows without printing secrets."""
from __future__ import annotations

import json
import os
import sqlite3
from pathlib import Path

DB = Path(os.environ["APPDATA"]) / "CherryStudio" / "Data" / "agents.db"
SECRET_KEYS = ("key", "token", "secret", "password", "auth", "bearer")


def redact(k: str, v):
    if isinstance(v, str) and any(x in k.lower() for x in SECRET_KEYS):
        return f"<redacted len={len(v)}>"
    if isinstance(v, (bytes, memoryview)):
        return f"<blob {len(v)} bytes>"
    if isinstance(v, str) and len(v) > 240:
        return v[:240] + f"...<{len(v)} chars>"
    return v


def main() -> None:
    con = sqlite3.connect(str(DB))
    con.row_factory = sqlite3.Row
    tables = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print("tables:", tables)
    for t in tables:
        cols = [r[1] for r in con.execute(f"PRAGMA table_info({t})")]
        n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"-- {t} cols={cols} rows={n}")
        try:
            rows = con.execute(f"SELECT * FROM {t} LIMIT 30").fetchall()
        except Exception as e:
            print("  read_error", e)
            continue
        for r in rows:
            d = {k: redact(k, r[k]) for k in r.keys()}
            print(json.dumps(d, default=str)[:2500])
    con.close()


if __name__ == "__main__":
    main()
