"""Retarget AgentCore Workspace Agent to a live chat model. Cherry must be quit."""
from __future__ import annotations

import sqlite3
import shutil
import time
from pathlib import Path
import os

AGENT_ID = "agentcore-workspace-agent"
TARGET = "deepseek:deepseek-v4-pro"
db = Path(os.environ["APPDATA"]) / "CherryStudio" / "Data" / "agents.db"
bak_root = Path(r"E:\AgentCore-Backups") / f"cherry-agents-model-{time.strftime('%Y%m%d-%H%M%S')}"
bak_root.mkdir(parents=True, exist_ok=True)
shutil.copy2(db, bak_root / "agents.db")

con = sqlite3.connect(db)
before = con.execute("SELECT id, model FROM agents WHERE id=?", (AGENT_ID,)).fetchone()
if not before:
    raise SystemExit("agent missing")
now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
con.execute(
    "UPDATE agents SET model=?, updated_at=? WHERE id=?",
    (TARGET, now, AGENT_ID),
)
con.commit()
after = con.execute("SELECT id, model FROM agents WHERE id=?", (AGENT_ID,)).fetchone()
con.close()
print({"before": before, "after": after, "backup": str(bak_root)})
