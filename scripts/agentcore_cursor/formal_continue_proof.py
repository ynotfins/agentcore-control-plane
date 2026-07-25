import json
import os
import psycopg
from psycopg.rows import dict_row

pw = os.environ.get('AGENT_CORE_POSTGRES_PASSWORD', '')
dsn = f"host=127.0.0.1 port=55433 dbname=agent_core user=postgres password={pw}"
conn = psycopg.connect(dsn, row_factory=dict_row)
cur = conn.cursor()

# Find prompt evidence events
cur.execute("""
    SELECT id, project_id, source_identity_id, event_kind, payload, occurred_at, accepted_at
    FROM agentcore.evidence_events
    WHERE event_kind = 'prompt'
    ORDER BY occurred_at ASC;
""")
prompt_rows = cur.fetchall()

exact_continue_prompts = []
for r in prompt_rows:
    p = r["payload"] or {}
    text = p.get("prompt") or p.get("text") or p.get("prompt_text") or p.get("user_prompt")
    if text == "Continue.":
        exact_continue_prompts.append({
            "id": str(r["id"]),
            "event_kind": str(r["event_kind"]),
            "occurred_at": str(r["occurred_at"]),
            "payload": p
        })

print(f"Total 'prompt' evidence events: {len(prompt_rows)}")
print(f"Exact 'Continue.' prompt events: {len(exact_continue_prompts)}")
for p in exact_continue_prompts:
    print(json.dumps(p, indent=2))

# Distinguish from acceptance-summary evidence
cur.execute("""
    SELECT id, event_kind, payload, occurred_at
    FROM agentcore.evidence_events
    WHERE payload::text LIKE '%Continue.%' AND event_kind != 'prompt';
""")
other_continue_rows = cur.fetchall()
print(f"\nNon-prompt evidence events mentioning 'Continue.': {len(other_continue_rows)}")
for o in other_continue_rows[:5]:
    print(f"  [{o['id']}] {o['event_kind']}: {str(o['payload'])[:100]}")

# Current projection revision
cur.execute("SELECT max(revision) as max_rev FROM agentcore.projection_revisions WHERE is_current = true;")
max_rev = cur.fetchone()["max_rev"]
print(f"\nCurrent projection revision: {max_rev}")

# Hook test session check
cur.execute("SELECT count(*) as cnt FROM agentcore.sessions WHERE session_key LIKE '%hook-test%';")
hook_cnt = cur.fetchone()["cnt"]
print(f"Surviving hook-test-sessions in DB: {hook_cnt}")

cur.close()
conn.close()
