"""One-shot continuity probe — delete after use."""
from __future__ import annotations

import os
import sys

import psycopg
from psycopg.rows import dict_row


def main() -> int:
    pw = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    if not pw:
        print("MISSING_PASSWORD")
        return 2
    conn = psycopg.connect(
        f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={pw}",
        row_factory=dict_row,
    )
    with conn.cursor() as cur:
        cur.execute(
            "SELECT version FROM agentcore.schema_migrations "
            "WHERE version LIKE 'm8%' ORDER BY version"
        )
        print("migrations", [r["version"] for r in cur.fetchall()])
        cur.execute("SELECT to_regclass('agentcore.v_client_memory_continuity') AS v")
        print("view", cur.fetchone())
        cur.execute(
            """
            SELECT project_key, client_key, agent_key, session_key, continuity_status,
                   last_session_open::text, last_append::text, last_close::text
            FROM agentcore.v_client_memory_continuity
            WHERE project_key = 'agentcore-control-plane'
            ORDER BY last_session_open DESC NULLS LAST
            LIMIT 8
            """
        )
        rows = cur.fetchall()
        print("continuity_rows", len(rows))
        for r in rows:
            print({k: (str(v)[:100] if v is not None else None) for k, v in r.items()})
    conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
