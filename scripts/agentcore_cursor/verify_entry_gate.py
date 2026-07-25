import os
import psycopg
from psycopg.rows import dict_row

pw = os.environ.get('AGENT_CORE_POSTGRES_PASSWORD', '')
dsn = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={pw}"
conn = psycopg.connect(dsn, row_factory=dict_row)
cur = conn.cursor()

cur.execute("SELECT column_name FROM information_schema.columns WHERE table_schema = 'agentcore' AND table_name = 'sessions';")
for c in cur.fetchall():
    print(" ", c["column_name"])

cur.execute("SELECT id, session_key FROM agentcore.sessions WHERE session_key LIKE '%hook-test%' OR id::text LIKE '%hook-test%';")
sessions = cur.fetchall()
print("Hook test sessions count:", len(sessions))

cur.close()
conn.close()
