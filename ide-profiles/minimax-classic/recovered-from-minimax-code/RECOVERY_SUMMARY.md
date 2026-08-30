# Recovery Summary — Chats recovered from prior "minimax code" sessions

**Recovered on:** 2026-08-05
**Recovered by:** MiniMax Agent Classic (current session)
**Source OS user:** ynotf (Tony Valentine)

## Where these came from

I scanned the C drive for prior agent project folders:

| Path | Type | Recovery value |
| --- | --- | --- |
| `C:\Users\ynotf\.mavis\context-snapshots\` | Mavis/minimax snapshot files | **High** — full chat transcripts (already compacted) |
| `C:\Users\ynotf\.mavis\memory\user.md` | Cross-project user memory | **High** — Tony's durable preferences/identity |
| `C:\Users\ynotf\.mavis\memory\tracking\` | Per-day session check-ins | Medium — recent session IDs only |
| `C:\Users\ynotf\.mavis\sessions\` | Session index dirs | Low — folder shells only, no payloads |
| `C:\Users\ynotf\.minimax\` | Mirror of `.mavis` | Same as above (symlink-like mirror) |
| `C:\Users\ynotf\.cagent\session.db` | Cagent SQLite | Low — only July 9-11 "config get" test sessions |
| `C:\Users\ynotf\AppData\Roaming\MiniMax Agent\IndexedDB\` | Electron leveldb | Not extracted — binary; runtime state |
| `C:\Users\ynotf\AppData\Roaming\MiniMax Agent\blob_storage\` | One 0f47... blob | Not extracted — likely runtime cache |
| `C:\Users\ynotf\.mmx\config.json` | Just config | None |
| `C:\Users\ynotf\agentcore-secrets\` | (excluded — secrets) | — |

## What was NOT recoverable

- **`.mavis\sessions\*` directory contents** — the per-session folder shells exist (27 of them, newest is `mvs_37542264e3c3402587e6597da77c2560` from 7/8/2026) but they are all empty. The actual session payloads appear to have been moved out to `context-snapshots` and `context-replacements` when they were compacted. The session IDs in `memory\tracking\2026-08-04.json` (`mvs_ade0f10887e54b85bf30ea8a7f67ecef`) do not have a corresponding folder under `sessions\` — they exist only as compacted snapshots.
- **Live chat UI history** for the most recent `mvs_ade0f10887e54b85bf30ea8a7f67ecef` session — the live chat was being compacted at the time of last write; only the *compacted* form is on disk.

## Recovered files (in this folder)

```
recovered-from-minimax-code\
├── RECOVERY_SUMMARY.md                                ← you are here
├── sessions-INDEX.csv                                 ← list of 27 session folders (.mavis)
├── USER_MESSAGES_2026-08-04_session.md                ← Tony's 13 user messages from 8/4 session
├── USER_MESSAGES_2026-07-26_session.md                ← Tony's 11 user messages from 7/26 session
├── memory\
│   ├── user.md                                        ← durable cross-project user profile
│   └── tracking\2026-07-13.json … 2026-08-04.json     ← 13 daily session check-in files
└── context-snapshots\
    ├── mvs_ade0f10887e54b85bf30ea8a7f67ecef\
    │   └── mvs_ade0f10887e54b85bf30ea8a7f67ecef-af90f1a3-e3d5-40f5-b98a-397c0a6572e3-initial-ctx_9a53b17971c746449ccc5ce0cfdacc23.json   (2.6 MB, 355 msgs, Reasonix+Hindsight)
    └── mvs_a6bb119ba181403ba41996bf10ac44a7\
        └── mvs_a6bb119ba181403ba41996bf10ac44a7-45bd39ce-42ec-4b9b-81c3-d1af0ecb9c81-initial-ctx_4aa9c7a8580242ba9977f1a8878cacfe.json   (3.2 MB, 475 msgs, notification-database)
```

## Session 1 — Reasonix + Hindsight + Bifrost setup (2026-08-03 → 2026-08-04)

- **sessionId:** `mvs_ade0f10887e54b85bf30ea8a7f67ecef`
- **Created:** 2026-08-04 04:26:42 UTC
- **Workspace at the time:** `D:\SillyTavern`
- **Data dir at the time:** `C:\Users\ynotf\.minimax`
- **Agent name:** `mavis` (display: "Mavis"; model: MiniMax-M3)
- **Stats:** 355 messages → compacted to 1; 417,308 → 15,776 tokens; 13 user messages, 150 assistant, 192 tool results
- **Tools used:** bash x140, write x16, web_search x15, web_fetch x7, read x7, todowrite x7
- **First user message:** "I installed an app called reasonix https://github.com/esengine/DeepSeek-Reasonix I installed the winsows version Reasonix-windows-amd64-installer.exe and it worked for a day but it won't open now. What is the difference in performance from installing it as an exe or cloning it onto this PC? Tell me about the benefits of this app and and the best way to install it. If we use terminal to install it can we install via pnpm because that is the policy of this PC when possible. Also tell me what other similar apps would be better for automated development."
- **Topic drift:** Reasonix install → Caveman vs Graphify evaluation → IDE profile creation for `ide-profiles\reasonix` → Hindsight DB schema in PG18 → Bifrost upstream wiring → pnpm install of Reasonix → E2E verification

## Session 2 — notification-database GUI testing (2026-07-26)

- **sessionId:** `mvs_a6bb119ba181403ba41996bf10ac44a7`
- **Created:** 2026-07-26 05:00:54 UTC
- **Stats:** 475 messages → compacted to 1; 415,225 → 12,374 tokens; 11 user messages, 154 assistant, 310 tool results
- **Tools used:** bash x211, read x33, write x19, edit x17, task_output x9, task_query x5, memory x4, grep x3, todowrite x3
- **First user message:** "i wnt to test this notification app. Does it have a gui that allows us to set the app that it sends the notifications from and change the endpoints."
- **Topic:** Android `notification-database` app (NotificationListenerService journaling) — GUI for selecting source app and configuring endpoints.

## User profile recovered (`memory\user.md`)

Key durable rules Tony wants every agent to follow:

- Detailed, structured task briefs. "Values X Must Provide" sections. No mid-flight clarification pings.
- Push back when a better tool exists. Research best-in-class, never be sycophantic. "I am a vibe coder so I won't be correct the majority of the time." Most technical suggestions are discussion, not commands.
- Production-grade engineering + Apple-style UI polish + all settings changeable in GUI.
- Cloud security: BitLocker keys offline-only, no MS escrow. Zero-knowledge / client-side encryption preferred (Cryptomator > VeraCrypt > rclone). Open-source over proprietary.
- Tooling: IPED 4.2.2, Avilla-File-System-Forensics, WDK, YARA, ExifTool, FFmpeg, MediaInfo, Bento4, libimobiledevice. Phones: S24/S25/S26 Ultra. Hardware: ASUS, dual T-FORCE 2TB NVMe (C:/D:), Samsung 990 PRO 4TB (F:), Crucial P5 Plus 2TB (H:), BX500 1TB SATA (I:), 10TB HGST E: ("Archive_Cold"), 2TB USB K:. All NVMe BitLocker XTS-AES 256, TPM+PIN. Secure Boot DISABLED.

## Recommended next steps for the new "minimax classic" session

1. **Read** `memory\user.md` first — those rules apply to every session.
2. **Re-read** the 8/4 session's user messages (`USER_MESSAGES_2026-08-04_session.md`) to remember the active workstream (Reasonix IDE + Hindsight + Bifrost).
3. **If work on Reasonix/Hindsight was in progress**, check whether the IDE profile at `D:\github\agentcore-control-plane\ide-profiles\reasonix` was actually created — the 8/4 session planned to populate it but may have been interrupted mid-stream.
4. **If work on notification-database is current**, re-read the 7/26 user messages first.
