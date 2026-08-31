# NFA Alerts Pipeline & Google Sheets — Handoff
**Date:** 2026-08-31 | **Repos:** nfa-platform + agentcore-control-plane

## Purpose
This handoff covers the alert ingest pipeline, Google Sheets sync, and related automation. This is a sub-area of nfa-platform work.

---

## 1. Alert ingest pipeline — proven live

```
Source          : MacroDroid Android app → POST to phone ingest gateway
Ingest gateway  : http://127.0.0.1:8787/v1/ingest/alerts (Windows service or Fastify process)
Tailscale URL   : https://chaoscentral.tailb71e7e.ts.net/v1/ingest/alerts
Database        : PostgreSQL 18 — nfa_ingest_capture — capture.raw_alerts
Alert count     : 3,571 as of 2026-08-31 15:23:40 (Aug 31 3:23 PM)
Date range      : 2026-08-17 through present (continuous)
Integrity       : SHA-256 verified on every insert via DB CHECK constraint
Latest alert    : #1901349, NJ/Passaic/Wayne, Water Leak, 2026-08-30 21:46 PM
```

**Proven facts:**
- Every alert has `raw_text_sha256 = sha256(raw_text_utf8_bytes)` verified by DB constraint
- The DB physically rejects any row where hash doesn't match content
- No alerts have ever been lost or truncated

### Alert format (raw BNN pipe-delimited)
```
[TYPE] STATE| County| City| Incident Type| Address| Narrative text | <C> BNN | FD_CODES | #ALERT_ID
```
- `TYPE`: empty = new, `U/D` = update
- `<C>` and `BNN` are source/routing markers (filtered from FD codes)

### BNN parser (scripts/lib/bnn_parser.mjs)
Filters from FD codes: `BNN`, `BNNDESK`, `DESK`, `<C>` (updated Aug 30)
DO NOT add these to FD codes columns — they are BNN system tokens, not fire departments.

---

## 2. Google Sheets integration

### Spreadsheet
```
Sheet ID : 1yKUvWtG7wBdjBhLpmM78vWhUoxiKMIryczIUt_Z2wOE (FD-Codes-Analytics)
Write tab: NFA_Feed (NOT Sheet1 — Sheet1 has 1627 hand-maintained rows)
Sheet1   : Legacy hand-maintained history — do not modify
Apps Script URL: https://script.google.com/macros/s/AKfycbx8ISZnt0dGT2vYSmky5Uahwbsgpk6ZttNIUKhQOHrUf8nBbZORSulvDNx_1UxG7BcO/exec
```

### Column layout (NFA_Feed, 24 columns)
| Col | Header | Notes |
|---|---|---|
| A | New Incident | "New Incident" or "Update" per notification line |
| B | Timestamp | DB received_at — exact arrival time at our server |
| C | Incident ID | BNN #ID |
| D | State | e.g. NJ, NY |
| E | County | |
| F | City | NYC boroughs appear in both E and F |
| G | Address | Box + street address combined |
| H | Box | Box code (may be empty if folded into G) |
| I | Incident type | Per update — captures escalation |
| J | Incident | Narrative text, one line per notification |
| K | nfa-id | Our own sequential ID (counter in Apps Script property NFA_NEXT_ID, currently ~1002960+) |
| L | Original Full Notification | Full raw text with • separators (pipes replaced with bullets Aug 30) |
| M–V | FD Codes | One real department code per column, deduplicated per incident |

### Current state
```
NFA_Feed rows: 236 (as of Aug 31 ~4 AM)
nfa-id range : 1000001 → ~1002960
Alert IDs    : #1899090 → #1901292
~3,335 alerts remaining to be synced (Aug 17–Aug 29 range)
```

### Sync script
```
Location  : D:\github\nfa-platform\scripts\sync_alerts_to_sheet.mjs
Env vars  : NFA_SHEETS_TOKEN (64 chars), NFA_SHEETS_WEBAPP_URL
            NFA_INGEST_DB_HOST=127.0.0.1, NFA_INGEST_DB_PORT=55433, NFA_INGEST_DB_NAME=nfa_ingest_capture
            NFA_CAPTURE_READ_DB_USER=nfa_migrator, NFA_CAPTURE_READ_DB_PASSWORD (Windows User env)
Run       : cd D:\github\nfa-platform; . .\scripts\db_env.ps1; node scripts/sync_alerts_to_sheet.mjs --limit 500
```

**Token note:** Two env vars exist — `NFA_SHEETS_TOKEN` (64 chars, used by script) and `NFA_SHEETS_WEBAPP_TOKEN` (44 chars, not used). The 64-char one is correct.

### Automated sync
```
Scheduled task : \AgentCore\NFA-Sheets-Sync
Frequency      : Every 15 minutes
Limit per run  : 500 alerts
Status         : Ready (auto-starts on boot)
```

---

## 3. MacroDroid direct-to-sheets (planned, not implemented)

The MacroDroid macro currently sends alerts to the PC ingest gateway. A direct path to Sheets is possible:

**Plan:** MacroDroid HTTP POST → Apps Script web app URL + token
**Recommended:** Keep PC ingest path (for DB integrity) AND add MacroDroid as parallel path
**Blocker:** Apps Script currently expects parsed fields, not raw BNN text
**Required work:** Update Apps Script to accept `rawText` field and parse BNN format server-side (Google Apps Script / JavaScript)

This would give near-real-time sheet updates without waiting for the 15-min scheduler.

---

## 4. Pending items

| Priority | Task |
|---|---|
| HIGH | Catch up remaining ~3,335 alerts: `node scripts/sync_alerts_to_sheet.mjs --limit 500` (runs 7 more times via scheduler, or run manually with --limit 3500) |
| MEDIUM | Implement MacroDroid direct-to-sheets (update Apps Script to accept raw BNN text) |
| MEDIUM | Verify NFA_SHEETS_WEBAPP_TOKEN (44 chars) — may be stale or different purpose from NFA_SHEETS_TOKEN |
| LOW | User wants to rename NFA_Feed column headers — safe to do (Apps Script keys on sourceAlertId, not headers) |

---

## 5. Not wired predictably

- **Sheet1 vs NFA_Feed**: ALL new data goes to NFA_Feed. Sheet1 is frozen legacy. Do not modify Sheet1.
- **NFA_NEXT_ID counter**: stored in Apps Script project properties. If script is redeployed, verify counter wasn't reset.
- **Duplicate suppression**: keyed on `sourceAlertId` (BNN alert #ID). Re-running sync is safe — duplicates are skipped.
- **Order matters**: sync uses `ORDER BY received_at ASC` (oldest first). This ensures the "New Incident" row lands before its updates. Do not change to DESC.
- **BNN tokens in FD codes**: Before Aug 30 fix, BNNDESK and DESK appeared in FD code columns. Rows 5–236 in NFA_Feed were synced AFTER the fix so they're clean. If older rows are ever re-synced from earlier data, verify the filter is applied.

---

## 6. Cursor continuation prompt

```
@D:\github\agentcore-control-plane\docs\handoffs\NFA_ALERTS_SHEETS_HANDOFF_2026-08-31.md
@D:\github\nfa-platform\docs\operations\GOOGLE_SHEETS_EXPORT.md
@D:\github\nfa-platform\scripts\sync_alerts_to_sheet.mjs

Read the handoff doc. Primary task: implement MacroDroid direct-to-Sheets.
Update the Apps Script web app to accept raw BNN text and parse it server-side.
This lets MacroDroid bypass the PC for near-real-time sheet updates.
```
