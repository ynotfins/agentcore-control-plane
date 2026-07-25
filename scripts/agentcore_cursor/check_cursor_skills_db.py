import sqlite3
import json

db_path = r'C:\Users\ynotf\AppData\Roaming\Cursor\User\globalStorage\state.vscdb'
conn = sqlite3.connect(db_path)
cur = conn.cursor()
query = "SELECT key, value FROM ItemTable WHERE key LIKE '%skill%' OR key LIKE '%plugin%' OR key LIKE '%third%' OR key LIKE '%agent%' OR key LIKE '%rule%' OR key LIKE '%setting%'"
cur.execute(query)
rows = cur.fetchall()
print(f'Found {len(rows)} matching keys in state.vscdb:')
for k, v in rows:
    val_str = str(v)
    if len(val_str) < 150:
        print(f'  {k}: {val_str}')
    else:
        print(f'  {k}: {val_str[:120]}...')
