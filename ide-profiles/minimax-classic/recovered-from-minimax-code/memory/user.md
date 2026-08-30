# User profile

### Identity (2026-06-07)
Type: identity
- Name: Tony
- Has a personal Android phone and uses a private Firebase project (Firestore) for personal data logging.
- Built (or had me build) `notification-database` — a personal NotificationListenerService-based journaling app to replace a MacroDroid workflow.
- Prefers highly prescriptive, production-grade engineering specs over open-ended asks.

### Communication style (2026-06-07)
Type: preference
- Detailed, structured task briefs with explicit "no questions" instructions.
- Wants "Values X Must Provide" sections rather than being interrupted for clarification.
- Comfortable with technical depth: mentions Hilt vs manual DI, dedup keys, Firestore security rules, Android quirks (Doze, OEMs) without prompting.
<!-- mem-append-reason: User-level privacy posture applies across all projects. -->
### Cloud security & key storage posture (2026-07-21)
Type: preference
- BitLocker recovery keys: offline only. Refuses MS account upload. Disables MS key escrow.
- Cloud (Dropbox/OneDrive/GDrive): distrusts providers holding recoverable keys. Worried about social engineering.
- Prefers zero-knowledge / client-side encryption (Cryptomator > VeraCrypt > rclone). Open-source over proprietary.
- Threat model: future coercion/breach, not current policy.
<!-- mem-append-reason: User-level domain identity (forensics) and hardware posture are durable across projects and shape every future recommendation. -->
### Digital forensics / PI (2026-07-22)
Type: identity
- Tony does digital forensics / PI work. Tooling: IPED 4.2.2, Avilla-File-System-Forensics, WDK, YARA, ExifTool, FFmpeg, MediaInfo, Bento4, libimobiledevice, body-cam/PD video sets, video-repair work.
- Hardware: ASUS board, 2x T-FORCE 2TB NVMe (C:/D:), Samsung 990 PRO 4TB (F:), Crucial P5 Plus 2TB (H:), BX500 1TB SATA (I:), 10TB HGST E: = "Archive_Cold", 2TB USB K:. All NVMe BitLocker XTS-AES 256, TPM+PIN. Secure Boot DISABLED.
<!-- mem-append-reason: Cross-project rules for working with Tony; applies to every session. -->
### Communication with Tony (2026-07-24)
Type: preference
- Vibe coder. His tech ideas are discussion, not commands. Push back when better path exists.
- Research best-in-class tools he hasn't mentioned. Don't just agree.
- He decides direction/goal; I decide architecture/how. Plan-approval = carte blanche.
- Phones: S20 missing, S24/S25/S26 Ultra.
<!-- mem-append-reason: Cross-project rules; applies to every session with Tony. -->

### Reinforced engineering rules (2026-07-26)
Type: preference
- Tony explicitly restated at the start of the EMU rebuild: "Do not just agree with the things I say because I say them. Research and find the best software, repos, and tools I do not mention. Do not agree with everything I say unless what I say is clearly the best choice."
- "I am a vibe coder so I won't be correct the majority of the time. I have great ideas but no idea how to build them."
- "Most technical suggestions I discuss are not commands — they are only discussion and should never direct or influence your coding and architecture decisions; they should only determine your direction and goal."
- My job: better his ideas, make them buildable, keep us grounded with proven architecture and best practices.
- Default stance: even when he says "go", I should still name the right tool if a better one exists — never be sycophantic.
- Production-grade engineering, Apple-style UI polish, all settings changeable in GUI is the bar. He repeats this — it matters.
<!-- mem-append-reason: Same cross-project rule restated by Tony with explicit examples. -->
