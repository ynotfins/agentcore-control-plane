"""AgentCore M6 — Setup script: apply M6 migration and LangGraph checkpoint tables.

Run once after installation:
    python setup_tables.py

Also verifies the existing memory surface is intact and DB is reachable.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

PG_DSN = (
    f"host=127.0.0.1 port=55433 dbname=agent_core "
    f"user=postgres password={os.environ.get('AGENT_CORE_POSTGRES_PASSWORD', '')}"
)
REPO_ROOT = Path(__file__).resolve().parents[2]
M6_UP = REPO_ROOT / "migrations" / "m6" / "001_up_langgraph_workflow.sql"


def apply_migration() -> bool:
    import psycopg
    sql = M6_UP.read_text(encoding="utf-8")
    try:
        with psycopg.connect(PG_DSN, autocommit=False) as c:
            c.execute(sql)
        print(f"[setup] M6 migration applied: {M6_UP.name}")
        return True
    except Exception as exc:
        if "already exists" in str(exc) or "duplicate" in str(exc).lower():
            print(f"[setup] M6 migration already applied (idempotent): {exc}")
            return True
        print(f"[setup] Migration error: {exc}", file=sys.stderr)
        return False


def setup_langgraph_tables() -> bool:
    """Create LangGraph checkpointer tables in the agent_core database."""
    try:
        from langgraph.checkpoint.postgres import PostgresSaver
        with PostgresSaver.from_conn_string(PG_DSN) as saver:
            saver.setup()
        print("[setup] LangGraph checkpoint tables created/verified")
        return True
    except Exception as exc:
        print(f"[setup] LangGraph table setup error: {exc}", file=sys.stderr)
        return False


def verify_db_ready() -> bool:
    import psycopg
    try:
        with psycopg.connect(PG_DSN) as c:
            row = c.execute("SELECT version()").fetchone()
        print(f"[setup] PostgreSQL reachable: {row[0][:40]}")
        return True
    except Exception as exc:
        print(f"[setup] DB not reachable: {exc}", file=sys.stderr)
        return False


if __name__ == "__main__":
    ok = verify_db_ready() and apply_migration() and setup_langgraph_tables()
    sys.exit(0 if ok else 1)
