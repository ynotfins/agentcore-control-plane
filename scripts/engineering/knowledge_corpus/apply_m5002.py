"""AUTH-gated apply of m5.002. Dry-run ROLLBACK first, then live COMMIT."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import psycopg

SQL_PATH = Path(__file__).resolve().parents[3] / "migrations" / "m5" / "002_up_knowledge_corpus.sql"


def connect() -> psycopg.Connection:
    password = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    if not password:
        raise SystemExit("AGENT_CORE_POSTGRES_PASSWORD missing")
    return psycopg.connect(
        host="127.0.0.1",
        port=55433,
        dbname="agent_core",
        user="postgres",
        password=password,
        autocommit=False,
    )


def strip_tx_wrappers(sql: str) -> str:
    # Migration file contains BEGIN/COMMIT; we manage the transaction ourselves.
    lines = []
    for line in sql.splitlines():
        stripped = line.strip().upper()
        if stripped in {"BEGIN;", "COMMIT;"}:
            continue
        lines.append(line)
    return "\n".join(lines)


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "dry-run"
    sql = strip_tx_wrappers(SQL_PATH.read_text(encoding="utf-8"))
    print(f"mode={mode} sql={SQL_PATH}")
    with connect() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT version FROM agentcore.schema_migrations WHERE version = 'm5.002'"
            )
            if cur.fetchone():
                print("already_applied=m5.002")
                conn.rollback()
                return 0
            cur.execute(sql)
            cur.execute(
                """
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema='agentcore' AND table_name='retrieval_documents'
                  AND column_name IN ('chunk_id','embedding_model','embedding_dim')
                ORDER BY 1
                """
            )
            cols = [r[0] for r in cur.fetchall()]
            print("columns=", cols)
            cur.execute(
                "SELECT version FROM agentcore.schema_migrations WHERE version='m5.002'"
            )
            print("migration_row=", cur.fetchone())
        if mode == "apply":
            conn.commit()
            print("COMMIT ok")
        else:
            conn.rollback()
            print("ROLLBACK dry-run ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
