# Caveman Docs Corpus — Site Agent Index

**Purpose:** complete documentation corpus for the Caveman family of AI-token-savings tools, pulled from `github.com/JuliusBrussee/caveman` and a handful of sibling repos. This folder is the single source of truth an agent should read before generating or updating any caveman-flavored site pages (landing, install, benchmarks, pricing, individual tool pages).

**Source repo:** <https://github.com/JuliusBrussee/caveman>
**Fetched:** 2026-08-05
**Working directory:** `D:\github\agentcore-control-plane\tools\caveman-docs\`

---

## Directory tree

```
caveman-docs/
├── README.md                       ← you are here (site-agent index)
├── README.md                       (root copy of JuliusBrussee/caveman README, 17.5 KB)
├── CLAUDE.md                       (maintainer guide, hook architecture, file ownership, CI sync)
├── CONTRIBUTING.md                 (how to add a new skill / agent to the caveman family)
├── SECURITY.md                     (privacy / telemetry, network call inventory)
├── AGENTS.md                       (entry-point notes for AI agents working in the repo)
│
├── windows-install/                ← all Windows + general install / setup files
│   ├── INSTALL.md                  (full per-agent install matrix — 30+ agents, flags, dry-run, uninstall)
│   ├── install-windows.md          (Windows-specific addendum)
│   ├── install.ps1                 (PowerShell one-line installer for Windows)
│   ├── install.sh                  (POSIX one-line installer)
│   ├── package.json                (npm metadata for the caveman plugin)
│   ├── gemini-extension.json       (Gemini CLI extension manifest)
│   ├── skills-lock.json            (locked skill-version manifest)
│   └── HONEST-NUMBERS.md           (the honest-numbers pricing/benchmark methodology doc)
│
├── skills/                         ← the seven caveman skills, each with README + SKILL.md
│   ├── caveman/                    the core "speak caveman" skill (default on, 4 levels)
│   ├── cavecrew/                   multi-agent subagent team (investigator, builder, reviewer)
│   ├── caveman-commit/             one-shot conventional-commit helper
│   ├── caveman-compress/           memory-file compressor + scripts/ (compress.py etc.)
│   ├── caveman-help/               help/cheatsheet skill
│   ├── caveman-review/             PR one-line comment generator
│   └── caveman-stats/              token-savings / cost reporting
│
├── agents/                         ← the three cavecrew subagent manifests
│   ├── cavecrew-builder.md
│   ├── cavecrew-investigator.md
│   └── cavecrew-reviewer.md
│
├── plugins/                        ← the marketplace-shaped plugin bundle
│   ├── .codex-plugin/plugin.json   (Codex plugin manifest)
│   ├── agents/                     (mirrors of the three cavecrew agents)
│   ├── assets/                     (caveman.svg, caveman-small.svg — site assets to use)
│   └── skills/                     (bundles of the four core skills)
│
├── cli/                            ← the Node installer + OpenClaw integration
│   ├── install.js                  (the actual installer script — 78 KB, 30+ agents)
│   └── lib/
│       ├── openclaw.js            (OpenClaw gateway integration)
│       ├── opencode-agent.js      (OpenCode agent shim)
│       └── settings.js            (settings & per-agent adapter)
│
├── benchmarks/                     ← the prose benchmark suite
│   ├── run.py                      (the benchmark harness)
│   ├── prompts.json                (the 10 chat-style prompts)
│   ├── requirements.txt
│   └── results/.gitkeep
│
├── evals/                          ← the eval / measurement suite
│   ├── README.md
│   ├── llm_run.py / measure.py / plot.py
│   ├── prompts/en.txt              (the prompt corpus)
│   └── snapshots/results.json      (the latest 37 KB results snapshot)
│
└── external/                       ← sibling repos, only the README pulled
    ├── caveman-code/README.md      (the "whole agent" — terminal coding agent)
    ├── cavemem/README.md           (cross-session memory)
    ├── cavekit/README.md           (spec-driven build loop)
    ├── cavegemma/README.md         (CaveGemma — Gemma fine-tune, the weight-baked version)
    ├── pricing/EXTERNAL-NOT-FOUND.md
    ├── cavebench/EXTERNAL-NOT-FOUND.md
    ├── cloud/EXTERNAL-NOT-FOUND.md
    ├── caveman-engine/EXTERNAL-NOT-FOUND.md
    ├── caveman-agent-sdk/EXTERNAL-NOT-FOUND.md
    └── caveman-gateway/EXTERNAL-NOT-FOUND.md
```

71 files, ~425 KB total. Nothing is fabricated; everything is either a verbatim copy of upstream content or a placeholder noting upstream was unreachable.

---

## Tool-by-tool map (what to read for what page)

### Caveman Skill — `skills/caveman/`
- **What it is:** the default-on "speak caveman" prompt that ships with caveman. Compresses an agent's output prose without touching code, commands, or errors. Six verbosity levels (normal / lite / full / ultra / wenyan / plus an OpenClaw marker-fence block).
- **Key facts for the site:**
  - "**65% fewer output tokens on prose, 8.5% on long-horizon agentic runs**" — quote the table in `README.md` (root), it shows per-task savings from 22% to 87% across 10 prompts.
  - JetBrains measured the 8.5% number on 86 SkillsBench tasks (linked in `README.md`).
  - Works in 30+ agents (full list in `windows-install/INSTALL.md`).
  - Turn on with `/caveman`, off with "normal mode". On Claude Code / Codex / Gemini it's on from message one.
  - Statusline: `[CAVEMAN] ⛏ 12.4k` — lifetime tokens saved.
- **Files to read:** `README.md` (root), `skills/caveman/SKILL.md`, `skills/caveman/README.md`, `windows-install/INSTALL.md`.

### CaveGemma — `external/cavegemma/README.md`
- **What it is:** the Gemma fine-tune of the caveman skill — compression **baked into the model weights** rather than achieved by prompt.
- **What we know:** the linked repo is `JuliusBrussee/finetune-caveman` (per caveman root README). No detailed public spec in the README we fetched, but the description is clear: "the compression baked into weights (Gemma fine-tune)".
- **Files to read:** `external/cavegemma/README.md`, plus the "Five tools" table in `README.md` (root).

### Caveman Code — `external/caveman-code/README.md`
- **What it is:** a full terminal coding agent, caveman top to bottom. Claimed **~2× fewer tokens than Codex** on identical tasks. 20+ providers, plan mode, autopilot goal loop, MIT.
- **Install command:** `npm install -g @juliusbrussee/caveman-code`
- **Files to read:** `external/caveman-code/README.md`, plus the "Want the whole agent, not just its mouth?" section in `README.md` (root).

### Cavemem — `external/cavemem/README.md`
- **What it is:** shrinks "what the agent **remembers**, across sessions." Companion to caveman (which shrinks what the agent **says**).
- **Files to read:** `external/cavemem/README.md`, plus the "Five tools" table in `README.md` (root).

### Cavekit — `external/cavekit/README.md`
- **What it is:** the build loop — spec-driven, no guessing. Shrinks "the **build loop**".
- **Files to read:** `external/cavekit/README.md`, plus the "Five tools" table in `README.md` (root).

### Cloud (Caveman Cloud) — `external/cloud/EXTERNAL-NOT-FOUND.md`
- **Status:** mentioned as part of the caveman family in the root README, but no public repository README was reachable. **Site guidance:** render as "Cloud — coming soon" or "via caveman.so" placeholder, do not invent product claims.

### Caveman Engine — `external/caveman-engine/EXTERNAL-NOT-FOUND.md`
- **Status:** same as Cloud — listed in the family, no public README. Render as a placeholder.

### Caveman Agent SDK — `external/caveman-agent-sdk/EXTERNAL-NOT-FOUND.md`
- **Status:** placeholder. Likely the developer SDK for building caveman-flavored agents. Render as "Coming soon" / "Join the waitlist".

### Caveman Gateway — `external/caveman-gateway/EXTERNAL-NOT-FOUND.md`
- **Status:** placeholder. Likely a hosted gateway that serves caveman-flavored agent traffic. Note `cli/lib/openclaw.js` is in this repo and deals with the OpenClaw gateway (a related but different thing — open-source self-host), so be careful not to confuse them on the site.

### Pricing — `external/pricing/EXTERNAL-NOT-FOUND.md`
- **What we know from upstream:** caveman is "free forever". Caveman 2 is the paid / team-tier product — it adds team-wide measurement, dashboards, and verified receipts for token savings. Pricing lives on caveman.so. The current site messaging: "Free like mass mammoth on open plain."
- **For the page:** lead with "Free, MIT" + "Caveman 2 — measured, verified, team-wide" with a waitlist CTA. Pull quotes from `windows-install/HONEST-NUMBERS.md` and the "Caveman 2" section in `README.md` (root).
- **Honest numbers doc:** `windows-install/HONEST-NUMBERS.md` is the source of truth on what caveman does and does not save (e.g. it only shrinks **output** tokens; input and reasoning are untouched; the skill itself adds ~1–1.5 k input tokens per turn; on already-terse workloads it can go net-negative; quality was statistically indistinguishable across JetBrains' 86 tasks).

### CaveBench — `external/cavebench/EXTERNAL-NOT-FOUND.md`
- **Status:** placeholder. Implied by the Caveman 2 promise ("a baseline on your own traffic and a receipt at the end of the month") and the existence of `benchmarks/` and `evals/` in this repo, but no public README. Render as "Caveman 2's measurement surface — see caveman.so".

### Supporting files (less prominent on the site, but useful)

- **`agents/cavecrew-*.md`** — three subagents (~60% fewer tokens than vanilla). Used inside caveman for multi-step work.
- **`skills/caveman-stats/`** — `/caveman-stats` command: real session token usage, lifetime savings, USD. Tweetable line with `--share`.
- **`skills/caveman-compress/`** — `/caveman-compress <file>`: rewrites a memory file (like `CLAUDE.md`) into caveman-speak, ~46% smaller input tokens every session after. Source: `skills/caveman-compress/scripts/compress.py` (~16 KB).
- **`skills/caveman-commit/`** — `/caveman-commit`: conventional commits, ≤50-char subject, "why over what".
- **`skills/caveman-review/`** — `/caveman-review`: one-line PR comments.
- **`skills/caveman-help/`** — cheatsheet.
- **`skills/cavecrew/`** — meta-skill for the three subagents.

### Benchmarks / measurement (for the "Benchmarks" page)

- **`README.md` (root)** has the headline 10-prompt table (range 22–87% savings, average 65% prose, 8.5% agentic).
- **`windows-install/HONEST-NUMBERS.md`** is the methodology / honesty disclaimer.
- **`benchmarks/`** has the raw runnable: `prompts.json` (10 prompts), `run.py` (the harness), `results/.gitkeep`.
- **`evals/`** has the larger eval harness: `llm_run.py`, `measure.py`, `plot.py`, `prompts/en.txt`, `snapshots/results.json` (37 KB snapshot).
- **JetBrains / SkillsBench**: 86-task independent measurement, mentioned in the root README (link: <https://blog.jetbrains.com/ai/2026/07/speak-to-ai-agents-like-cavemen-tosave-tokens/>).

### Install page source-of-truth

- **`windows-install/INSTALL.md`** — the comprehensive install matrix for 30+ agents. Use this as the primary content for the install page.
- **`windows-install/install.ps1`** + **`install.sh`** — the actual one-liner installers.
- **`windows-install/install-windows.md`** — Windows-specific notes.
- **`package.json`** + **`gemini-extension.json`** + **`skills-lock.json`** — manifests.
- **`CONTRIBUTING.md`** — how to add a new agent adapter (useful for the install page's "support for your agent" CTA).
- **`SECURITY.md`** — privacy / telemetry disclosure; install-time fetches; no phone-home after install.

### Branding assets

- **`plugins/assets/caveman.svg`** + **`plugins/assets/caveman-small.svg`** — the caveman logo. Use these (or higher-res versions from the live `docs/assets/` folder of the repo).
- The "dancing rock" emoji + caveman puns ("Caveman no make brain smaller. Caveman make *mouth* smaller.") are intentional brand voice — see the root `README.md` and `skills/caveman/SKILL.md`.

---

## How to use this corpus (a guide for the site agent)

1. **Don't invent.** Every claim in this corpus is sourced. If a tool's README is missing (`EXTERNAL-NOT-FOUND.md`), do not invent features. Render as "Coming soon" / "Join waitlist" and link to caveman.so.
2. **Lead with the headline numbers.** 65% prose / 8.5% agentic — both are real, both are measured, both belong on the landing page. Use the per-prompt table in `README.md` (root) for the breakdown.
3. **Be honest about the trade-offs.** `windows-install/HONEST-NUMBERS.md` is the project's own "this is when it works and when it doesn't" doc. Site should not hide this; the JetBrains quote ("quality was statistically indistinguishable") is the strongest asset.
4. **One install command, multiple surfaces.** The install page should show the PowerShell one-liner first (Windows audience) and the bash one-liner second. `windows-install/INSTALL.md` is the long-form fallback for the per-agent matrix.
5. **The tool page map** is the "Five tools" table in `README.md` (root): caveman, caveman-code, cavemem, cavekit, cavegemma. Plus the three newer slots (Cloud, Engine, Agent SDK, Gateway, CaveBench) — all currently placeholder.
6. **For Pricing,** lean on `windows-install/HONEST-NUMBERS.md` plus the "Caveman 2" section in `README.md` (root). Don't promise dollar amounts we don't have.
7. **For Benchmarks,** use `README.md` (root) prose benchmark table + `evals/snapshots/results.json` for the latest numbers + a link to the JetBrains blog post.
8. **Voice.** Casual, caveman-pun, dry. The README itself demonstrates the tone.

---

## Quick start for the site build

- [ ] Read `README.md` (root) end-to-end. This is the canonical voice + headline numbers.
- [ ] Read `windows-install/INSTALL.md` for the install page.
- [ ] Read `windows-install/HONEST-NUMBERS.md` for the honesty/benchmarks page.
- [ ] Read each of the 4 successful external `README.md` files for the per-tool pages: `caveman-code`, `cavemem`, `cavekit`, `cavegemma`.
- [ ] Read the 7 `SKILL.md` files in `skills/` for the per-skill deep dives (the `/caveman-*` commands).
- [ ] Render the 6 placeholder tools (Cloud, Engine, Agent SDK, Gateway, CaveBench, Pricing) with "Coming soon" or "Caveman 2" CTAs — do not fabricate.
- [ ] Wire the install CTA to the PowerShell + bash one-liners.
- [ ] Add the JetBrains 86-task result + the 10-prompt benchmark table to the benchmarks page.
- [ ] Use the caveman SVG from `plugins/assets/` for branding.
- [ ] When in doubt, link to `https://github.com/JuliusBrussee/caveman` as the canonical source.
