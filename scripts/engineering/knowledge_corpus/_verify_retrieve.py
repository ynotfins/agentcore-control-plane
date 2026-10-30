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
        SELECT count(*) AS n,
               count(*) FILTER (WHERE metadata->>'asset_type' = 'boilerplate') AS boilerplate,
               count(*) FILTER (WHERE metadata->>'asset_type' = 'agent_rule') AS agent_rule,
               count(*) FILTER (WHERE metadata->>'asset_type' = 'openapi') AS openapi,
               count(*) FILTER (WHERE metadata->>'asset_type' = 'docs') AS docs,
               count(*) FILTER (WHERE embedding IS NOT NULL) AS with_embedding
        FROM agentcore.retrieval_documents
        WHERE provenance->>'ingest' = 'knowledge_corpus'
        """
    )
    print("COUNTS", json.dumps(cur.fetchone(), default=str))
    cur.execute(
        """
        SELECT title, metadata->>'asset_type' AS asset_type,
               metadata->>'framework' AS framework,
               left(text, 100) AS body_preview,
               retrieval_method, score
        FROM agentcore.hybrid_retrieve_documents(
          NULL, 'FastAPI dependency injection health', NULL, 8, NULL,
          ARRAY['postgres_fts','postgres_trigram']
        )
        """
    )
    print("RETRIEVE", json.dumps(cur.fetchall(), indent=2, default=str))
    cur.execute("SELECT version FROM agentcore.schema_migrations ORDER BY version")
    print("MIGRATIONS", [r["version"] for r in cur.fetchall()])
    cur.execute("SELECT extname, extversion FROM pg_extension WHERE extname='vector'")
    print("VECTOR", cur.fetchone())
conn.close()
