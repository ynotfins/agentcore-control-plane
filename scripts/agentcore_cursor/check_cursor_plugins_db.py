import sqlite3
import json

db_path = r'C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\state.vscdb'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
query = "SELECT key, value FROM ItemTable WHERE key LIKE '%plugin%'"
cur.execute(query)
rows = cur.fetchall()
print(f'Found {len(rows)} matching plugin keys in state.vscdb:')
for k, v in rows:
    print(f'  {k}: {str(v)[:120]}')
