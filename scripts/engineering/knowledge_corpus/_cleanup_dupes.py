"""Remove earlier knowledge_corpus rows superseded by framework=fastapi re-ingest."""

import json
import os

import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    host="127.0.0.1",
    port=55433,
    dbname="agent_core",
    user="postgres",
    password=os.environ["AGENT_CORE_POSTGRES_PASSWORD"],
    row_factory=dict_row,
)
with conn.cursor() as cur:
    cur.execute(
        """
        DELETE FROM agentcore.retrieval_documents
        WHERE provenance->>'ingest' = 'knowledge_corpus'
          AND metadata->>'asset_type' IN ('boilerplate', 'openapi')
          AND version = '2026-10-29'
        RETURNING id
        """
    )
    deleted = cur.fetchall()
    conn.commit()
print(json.dumps({"deleted": len(deleted)}))
conn.close()
