"""Probe prompt capture for acceptance via source_identities join."""
from __future__ import annotations

import json
import os

import psycopg
from psycopg.rows import dict_row

SID = "e1a52554-db42-4347-95ec-6c843a4efea4"


def main() -> None:
    pw = os.environ.get("AGENT_CORE_POSTGRES_PASSWORD", "")
    conn = psycopg.connect(
        host="127.0.0.1",
        port=55433,
        dbname="agent_core",
        user="postgres",
        password=pw,
        row_factory=dict_row,
    )
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT e.id::text AS event_id, e.event_kind::text, e.idempotency_key,
                   e.created_at::text, left(e.payload::text, 240) AS payload
            FROM agentcore.evidence_events e
            JOIN agentcore.source_identities si ON si.id = e.source_identity_id
            WHERE si.session_id = %s::uuid
              AND e.event_kind = 'prompt'
            ORDER BY e.created_at DESC
            LIMIT 10
            """,
            (SID,),
        )
        rows = cur.fetchall()
        print("prompt_rows", len(rows))
        for r in rows:
            print(json.dumps(r, default=str))
        cur.execute(
            """
            SELECT count(*) AS c
            FROM agentcore.evidence_events e
            JOIN agentcore.source_identities si ON si.id = e.source_identity_id
            WHERE si.session_id = %s::uuid
              AND e.event_kind = 'prompt'
              AND e.payload->>'text' = 'Continue.'
            """,
            (SID,),
        )
        print("exact_continue_dot_count", cur.fetchone())
        cur.execute(
            """
            SELECT count(*) AS c
            FROM agentcore.evidence_events e
            JOIN agentcore.source_identities si ON si.id = e.source_identity_id
            WHERE si.session_id = %s::uuid
              AND e.event_kind = 'prompt'
              AND lower(e.payload->>'text') = 'continue'
            """,
            (SID,),
        )
        print("exact_continue_count", cur.fetchone())
    conn.close()


if __name__ == "__main__":
    main()
