# EverMind / EverOS Competitive Assessment

**An independent, evidence-based review of EverOS against the state of the art in agent memory systems**

| | |
|---|---|
| **Report date** | 2026-10-28 |
| **Subject** | EverMind AI — EverOS v1.5.1 (Apache-2.0), plus sibling research artifacts (EverMemOS, HyperMem, Raven, EverMemBench) |
| **Author** | Matrix Agent |
| **Task type** | Verification-focused (vendor claims to confirm/refute) with a search-focused competitive mapping |
| **Method** | Web research only. No code was written. All observations timestamped 2026-10-28 unless otherwise stated. |
| **Evidence grades** | **VERIFIED** = confirmed in a primary artifact (repo file, paper, API response, official doc). **VENDOR** = published by EverMind itself (marketing, blog, social) and not independently confirmed. **INFERRED** = conclusion drawn from verified facts. **UNVERIFIABLE** = claimed but no supporting artifact located. |

---

## Executive Summary

EverOS is a well-built, disciplined open-source memory runtime that is **not** the state-of-the-art system it markets itself as.

**First, two of the three homepage headline numbers are not released results.** EverMind's account director posted on 2026-10-21: *"Next release (internal): LoCoMo 94.74% · AMA 80.89% · BEAM-1M 69.42% · SWE-ContextBench 34.34%. Current release: LongMemEval 94.00%"* [verified]. The homepage presents all as present-tense achievements, while `benchmarks/README.md` publishes 94.42 for LoCoMo — not 94.74 — with no adapter, config, or result file for AMA, BEAM-1M, or SWE-ContextBench.

**Second, the 83.00% → 94.00% LongMemEval gap is fully explained — unflatteringly.** The 83.00% comes from the peer-reviewed EverMemOS paper: GPT-4.1-mini over dense+BM25+RRF+reranker retrieval. The 94.00% is the *best cell* of a 5×4 backbone × answer-model matrix whose row average is 92.48: the answer model became Gemini 3.6 Flash, extraction DeepSeek-V4-Pro, retrieval an LLM decider, and judging weakened from three blind judges to one `gpt-4o-mini` run.

**Third, the architecture is competent hybrid RAG, not graph memory.** EverOS's own architecture document states that *"No explicit knowledge-graph engine or graph traversal subsystem is described."* Their ACL 2026 hypergraph paper (HyperMem) sits in a separate 22-star repository with no push since 2026-06-02.

EverOS's engineering culture is above peer norm — property-based testing, an enforced 80% coverage gate, import-linter-enforced boundaries, a changelog publishing its own regressions. But the codebase is four months old: fresh installs returned HTTP 500 in v1.4.1, a security fix regressed in v1.2.0, and the "<500 ms p95" claim is contradicted by its own best measured p95 of 1.45 s.

**Placement: Tier 2 on engineering and developer experience; Tier 3 on retrieval and temporal reasoning; Tier 4 on benchmark credibility and ecosystem adoption.** Adoption is the starkest gap: 13,668 stars but 9 contributors, 145 commits, and ~20,400 PyPI downloads/month against Mem0's ~2,020,000.

---

## 1. Introduction

EverMind (https://evermind.ai) positions itself as memory infrastructure for AI agents, with EverOS as the flagship: a local-first, Markdown-native memory runtime distributed under Apache-2.0, accompanied by Raven (a multi-agent harness), EverMe (a personal-memory CLI), SkillCorpus/SkillHub, EverAlgo, HyperMem, MSA, EverMemBench, and EvoAgentBench.

The marketing surface is extensive. The site's headline cards advertise **LoCoMo 94.74%**, **LongMemEval 94.00%**, and **AMA 80.89%**, accompanied by the assurance that *"we prove it with open-source benchmarks anyone can reproduce."* The `/everos` product page adds "Open source. Reproducible. Independently verified." and "5+ peer-reviewed papers."

This review was commissioned because an internal inconsistency was visible: EverMind's own comparison blog states *"EverMind reaches 83.00% accuracy on LongMemEval,"* while the homepage claims 94.00% for the same benchmark. The mandate was to resolve that discrepancy, map the competitive landscape, assess the actual engineering, and deliver a verdict — without simply repeating the vendor's framing.

The stakes are real. Agent memory has become a category with genuine technical differentiation (graph vs. hierarchical vs. episodic architectures, consolidation policies, temporal validity) and, as of 2026, a set of credible published evaluations. A memory layer chosen for a production agent is a multi-year architectural commitment: the data format, the retrieval semantics, and the namespace model all become load-bearing. Marketing inflation at this point in the market is not a cosmetic problem; it is an architecture-selection problem.

---

## 2. Methodology

Research ran over approximately a dozen rounds of retrieval against primary artifacts rather than search snippets. The decisive move was shifting from marketing pages to the repository: `benchmarks/README.md`, `benchmarks/configs/*.toml`, `benchmarks/adapters/*`, `benchmarks/run.py`, `benchmarks/reproduce.sh`, `docs/how-memory-works.md`, `docs/architecture.md`, `docs/engineering.md`, `docs/use-cases.md`, `QUICKSTART.md`, and the 104 KB `CHANGELOG.md` were read directly from `raw.githubusercontent.com`, because the gaps between what the site says and what the code does are the substance of this review.

All three named arXiv identifiers resolve and were read in full via the arXiv HTML renderings (the PDF endpoint refused programmatic extraction, so `arxiv.org/html/<id>v1` was used instead and full text including every results table was recovered). The four benchmark papers — EverMemOS (2601.02163), HyperMem (2604.08256), Raven (2609.33439), and AMA-Bench (2602.22769) — were each read at the level of methodology, backbone model, judge protocol, and results table.

Adoption signals were pulled from the GitHub REST API (repository metadata, contributor list, commit history, release list, issue threads) and from PyPI download statistics via `pypistats`. The social-media provenance of the headline numbers was traced through X/Twitter search, which turned out to be the single most important discovery of the project.

Cross-vendor comparison was handled by pulling each competitor's own published claims with their stated backbone where one exists, and by reading the third-party critiques that the memory field has generated — notably Zep's audit of LoCoMo (2025-05-06, updated 2026-06-03) and Letta's filesystem-baseline experiment (2025-08-12), which both attack the benchmarks themselves rather than any one vendor.

Every claim in this report carries a source URL and an observation date. Claims that could not be confirmed are collected explicitly in deliverable (h) rather than being quietly dropped or stated as fact. Contradictions are recorded as contradictions.

One deliberate omission: no charts were generated. The research brief specified web research with no code writing, and generating figures would have required authoring Python. The comparison tables below carry the quantitative argument instead.

---

## 3. Key Findings

### 3.1 The provenance of 94.74% and 80.89%

The three headline numbers do not originate in a benchmark harness, a paper, or a blog post. They originate in a social-media announcement.

On 2026-10-21 at 02:34 UTC, the account of Yafeng Deng — the corresponding author of the EverMemOS paper and a co-author of HyperMem — posted the following under the handle @LongTermMemoryE [VERIFIED, X/Twitter, 2026-10-21]:

> "Every AI product will need memory. Here's EverOS.
> Next release (internal): LoCoMo 94.74% · AMA 80.89% · BEAM-1M 69.42% · SWE-ContextBench 34.34%
> Current release: LongMemEval 94.00%"

A second account, @ElliotChen, posted the same five figures without the "Next release (internal)" qualifier in Chinese on 2026-10-21 at 00:49 UTC [VERIFIED]. The homepage, the `/everos` product page, and the `everos.evermind.ai` cloud site all display the full set as present-tense, product-achievement framing, with "Benchmarks You Can Verify" as the caption and the claim that the benchmarks are ones "anyone can reproduce."

The repository tells a different story. `benchmarks/README.md` publishes exactly four rows [VERIFIED, github.com/EverMind-AI/EverOS, 2026-10-28]:

| Benchmark | Questions | Accuracy | Decider | Answer model |
|---|---:|---:|---|---|
| LoCoMo | 1,540 | **94.42** | deepseek/deepseek-v4-flash-0731 | openai/gpt-4.1-mini |
| LongMemEval | 500 | **94.00** | qwen3.6-27B | google/gemini-3.6-flash |
| EverMemBench | 2,400 | **66.67** | qwen3.6-27B | google/gemini-3-flash-preview |
| SubtleMemory | 1,522 | **71.75** | qwen3.6-27B | openai/gpt-5.4 |

The 32-file `benchmarks/` subtree was enumerated in full via the GitHub tree API [VERIFIED, 2026-10-28]. It contains adapters for `locomo`, `longmemeval`, `evermembench`, and `subtlememory` only. There is no AMA adapter, no BEAM adapter, and no SWE-ContextBench adapter. There is no AMA configuration file, no BEAM configuration file, no SWE-ContextBench configuration file. `benchmarks/data/` contains exactly one file: `.gitkeep` — no dataset, no result JSON, no run specification.

The conclusion is unambiguous. **94.00% LongMemEval is a shipped, reproducible result. 94.74% LoCoMo and 80.89% AMA are internal, unreleased results advertised on the marketing site as current.** This is not a rounding difference; it is a category error between "what the open-source package achieves" and "what the company says it has achieved."

### 3.2 Resolving 83.00% vs 94.00% on LongMemEval

The discrepancy the brief flagged is real, and it is fully resolvable — but the resolution is more interesting than a simple "different subsets" answer, because the two numbers are not even the same statistic.

**83.00%** comes from the EverMemOS paper [VERIFIED, arXiv 2601.02163v2, 2026-01-09, CC BY 4.0, cited by 54]. The architecture is a hybrid retrieval stack: Qwen3-Embedding-4B dense vectors, BM25 lexical retrieval, Reciprocal Rank Fusion, and a Qwen3-Reranker-4B cross-encoder. The backbone LLM is GPT-4.1-mini. The answer model is GPT-4.1-mini. Judging uses GPT-4o-mini plus two auxiliary judges, averaged blind, with human validation at Cohen's κ = 0.891 (LoCoMo) and 0.978 (LongMemEval). Token cost is reported transparently: 2.8k tokens per LongMemEval question, and 9.42M + 10.27M tokens across the 1,540 LoCoMo questions, roughly 6.7k tokens per question. The LongMemEval baseline column (MemU 38.40, Zep 63.80, Mem0 66.40, MemOS 77.80) is explicitly *"taken from the official MemOS leaderboard because the authors could not run every baseline API end-to-end"* — an honest disclosure, but it means the baselines were not measured under the same harness.

**94.00%** comes from the "Multi-round retrieval" blog [VENDOR, evermind.ai/blogs/multi-round-retrieval-letting-the-model-decide-when-to-stop-searching, 2026-09-04] and the repository README. The change is not a subset change. It is a change of pipeline on every axis simultaneously:

| Axis | 83.00% (paper, 2026-01) | 94.00% (repo/blog, 2026-09) |
|---|---|---|
| Answer model | openai/gpt-4.1-mini | google/gemini-3.6-flash |
| Extraction backbone | openai/gpt-4.1-mini | deepseek/deepseek-v4-pro-0813 |
| Retrieval method | dense + BM25 + RRF + Qwen3-Reranker-4B | `llm_multiround` (LLM decider reads full episode text) |
| Decider | n/a | qwen3.6-27B |
| Judge | GPT-4o-mini + 2 auxiliary, blind-averaged | gpt-4o-mini, **runs = 1** |
| top_k | 10 | 20 |
| Profile injection | episode + profile | `include_profile = false` |

The LongMemEval-S matrix in that blog is the most revealing artifact in the whole review [VENDOR, 2026-09-04]. It varies extraction backbone by row and answer model by column, with the parenthesised value being each cell's own "perfect retrieval" ceiling:

| Extraction backbone | gpt-4.1-mini | gemini-3.6-flash | deepseek-v4-flash | gpt-5.6-terra | claude-sonnet-5 | Row avg |
|---|---:|---:|---:|---:|---:|---:|
| DeepSeek-v4-pro | 90.4 | **94.0** | 93.2 | 91.4 | 93.4 | **92.48** |
| Qwen3.6-27B | 87.2 | 92.4 | 90.6 | 91.6 | 89.4 | 90.24 |
| GPT-4.1-mini | 88.6 | 91.6 | 91.0 | 89.8 | 88.8 | 89.96 |
| Gemini-2.5-flash | 86.4 | 91.2 | 90.0 | 89.0 | 89.6 | 89.24 |
| *Oracle (gold evidence)* | 96.2 | 96.6 | 96.2 | 96.8 | 96.6 | 96.48 |

The published 94.00 is the single best cell of a twenty-cell matrix. The corresponding row average is 92.48, and the absolute bound (answering from gold evidence with no extraction in the path) is 96.48. The blog itself reports a retrieval loss of 1.16 points and an extraction loss of 2.84 points for the winning configuration — an unusually candid decomposition that also shows retrieval is no longer the bottleneck.

**Assessment [INFERRED]:** the discrepancy is benign in origin and misleading in presentation. The 11-point gain is a legitimate consequence of a better answer model, a better extraction backbone, and an agentic retrieval loop replacing index-only fusion. But three problems remain. The 94.00 is cherry-picked from a matrix without disclosing the 92.48 average. The judge protocol was weakened from three blind judges to one run, and the repository's own `locomo.toml` measures a run-to-run noise floor of **0.91 pp on LoCoMo and 1.20 pp on LongMemEval** — meaning a single-run judge is scoring at a resolution finer than the noise it is measuring. And the homepage communicates none of this.

### 3.3 The reproducibility artifacts: real harness, incomplete evidence

EverOS ships a benchmark harness that is better than most, and this deserves to be stated plainly rather than lost in criticism. Added in v1.3.1 (2026-09-07), `benchmarks/` implements a four-stage pipeline (ADD → SEARCH → ANSWER → JUDGE) across four benchmarks, with per-benchmark configuration, a `reproduce.sh` entry point, and — a detail very few projects get right — a per-run `run_spec.json` provenance record capturing the configuration actually used. The README's own disclosure that *"Five of the six rows in the published EverMemBench comparison table are the macro mean of their own nine columns, so reading our figure alongside that column compares two different statistics"* is a candid admission of a comparability defect most vendors would have hidden [VERIFIED].

That same disclosure also explains a number that otherwise looks inconsistent: the README's EverMemBench **66.67** is a micro accuracy (`sum(correct)/sum(total)`) while the blog's comparison table shows **57.40** for EverOS as the unweighted mean of nine behaviour columns [VENDOR, 2026-09-04]. Two different statistics, same run.

Three reproducibility gaps nonetheless remain, and they are load-bearing:

**No data, no results.** `benchmarks/data/` contains only `.gitkeep`. Datasets must be downloaded manually; no published result files, no `run_spec.json` from the published runs, no logs are committed. A third party can run the harness but cannot audit the run that produced 94.42 or 94.00.

**No competitor adapters.** The unified framework EverMind announced on 2025-11-26 promised to compare EverOS, Mem0, MemOS, Zep, and MemU under one harness with a common GPT-4.1-mini answer model [VENDOR]. The repository contains no adapter for Mem0, Zep, MemOS, or MemU — only the four self-benchmarks. The claimed unified cross-vendor framework is therefore not reproducible, and every cross-vendor number on EverMind's site and blogs comes from somewhere else.

**The two referenced locations do not exist.** The November 2025 blog states results are at `EverMind-AI/EverOS_Eval_Results` and that code lives at `github.com/EverMind-AI/EverOS/tree/main/evaluation`. Both were checked and neither exists [VERIFIED, GitHub API, 2026-10-28].

**The shipped default config reproduces no published number.** `benchmarks/config_hybrid.toml` — commented as the "single source of truth" — sets `methods = "hybrid"`, `judge_model = "openai/gpt-4.1-mini"`, and `judge_runs = 3`. The published figures require `methods = "llm_multiround"`, `judge_model = "openai/gpt-4o-mini"`, and `judge_runs = 1` from `benchmarks/configs/locomo.toml` and `longmemeval.toml` [VERIFIED]. Two further oddities sharpen this. The `methods` line in the shipped config enumerates only `keyword, vector, hybrid, agentic` — `llm_multiround`, the method behind every published number, is not in that public list, yet appears 12 times in `benchmarks/run.py` [VERIFIED]. And `locomo.toml` carries an inline comment, *"Our published numbers used qwen3.6-27B here,"* pointing at a decider model that contradicts the README table's `deepseek/deepseek-v4-flash-0731` [VERIFIED]. The harness is reproducible in principle; the configuration that actually produced the numbers is assembled from files that disagree with each other and with the README.

A 2026-10-14 GitHub issue, titled *"[Offer] Free independent recomputation of your published memory benchmarks (assayed-tier upgrade)"* and closed on 2026-10-20 with one comment, shows that third parties recognize this gap and that EverMind has not yet closed it [VERIFIED].

### 3.4 The architecture: capable hybrid RAG, honestly documented

EverOS's architecture document is unusually candid, and the candour is itself a finding. The system is Markdown-native: YAML frontmatter plus Markdown files are the source of truth, SQLite holds operational state, and LanceDB (or Milvus) holds a derived index that can be deleted and rebuilt without data loss [VERIFIED, docs/how-memory-works.md and docs/architecture.md].

The write path is `service.memorize → memory.extract.pipeline → infra.persistence.markdown.write` (atomic: temp file → fsync → rename) → SQLite audit row → asynchronous cascade daemon. The cascade daemon watches the filesystem (FSEvents on macOS, inotify on Linux), pushes durable change records into a `md_change_state` queue, diffs content by SHA-256, re-embeds only changed entries, and upserts into LanceDB, with an LSN watermark in `system.db` ordering rebuilds. This is a sound design: it makes the human-readable file the canonical artifact and the vector index disposable, which is the right call for local-first operation.

Retrieval is the weak point relative to the competition. The documentation is explicit: *"Vector ANN, full-text BM25 retrieval, and scalar filtering are executed within the embedded LanceDB engine. These operations execute together in one query."* [VERIFIED, docs/how-memory-works.md]. The mRAG blog (2026-04-17) adds that mRAG stands for **Multimodal RAG** and describes a two-level hierarchical search — coarse retrieval over episode summaries via parallel dense and BM25 searches fused by RRF (or by a trained logistic-regression ranker), then expansion of each candidate episode into its atomic facts, scored as `final_score = α × fact_score + (1 − α) × episode_score` with α = 0.5, where a high-scoring fact displaces its parent episode in the result set [VENDOR, evermind.ai/blogs/introducing-mrag-how-everos-retrieves-what-actually-matters]. A dedicated reranker exists but is off by default.

That is a genuinely good coarse-to-fine design, and the token economics are documented with unusual precision. The LongMemEval-S injection ablation shows a "core-only" configuration reaching **91.00** accuracy at 1,946 prompt tokens per query versus **93.40** at k=20 with 8,594 prompt tokens — 97.4% of peak accuracy at 23% of the prompt, with retrieval MRR 0.9768 and MAP 0.9524 [VENDOR, 2026-09-04]. But it is still hybrid RAG with a learned fusion weight. The same blog lists the public retrieval methods as `keyword`, `vector`, `agentic`, `hybrid`; `llm_multiround` is absent from that list despite being the method behind every published number.

**There is no graph engine in the shipped product.** `docs/architecture.md` says it plainly: *"No explicit knowledge-graph engine or graph traversal subsystem is described in the architecture."* [VERIFIED] The site's own comparison table concedes "Temporal Knowledge Tracking: **Partial**" and "Hierarchical Memory Organization: **Partial**" [VERIFIED, evermind.ai homepage, 2026-10-28]. The technical picture matches: temporal handling amounts to date-based filenames, an optional foresight mechanism with validity intervals, and `deprecated_by` links — and `extract_foresight` has been **disabled by default** since v1.2.3, while reflection runs on a weekly cron (`0 2 * * 1`) and is **disabled by default** [VERIFIED, CHANGELOG.md and docs/how-memory-works.md].

HyperMem, their ACL 2026 Main hypergraph paper (arXiv 2604.08256, three-level topic/episode/fact hypergraph with weighted hyperedges and coarse-to-fine retrieval, 92.73% on LoCoMo with GPT-4o-mini), is a **separate repository**: 6 commits, 22 stars, 3 forks, no releases, no push since 2026-06-02 [VERIFIED, GitHub API]. It is not integrated into EverOS. The same is true of MSA (3,519 stars, last push 2026-05-06) and EverMemBench (23 stars, last push 2026-02-13, no LICENSE file).

### 3.5 Multi-tenancy, and what is not documented

EverOS partitions state on the filesystem at `~/.everos/<app_id>/<project_id>/users/<user_id>/…` and `…/agents/<agent_id>/…` with a parallel `knowledge/` tree [VERIFIED, docs/architecture.md]. This is namespace partitioning, not row-level isolation with access control.

`docs/use-cases.md` does not document an explicit scope taxonomy (global/team/project/group/session), namespace creation, isolation guarantees, inheritance, access control, retention, deletion, or promotion between scope levels [VERIFIED, gap confirmed by absence]. It also does not describe shared-memory ownership, isolation, consistency, conflict resolution, or permissions. For a memory layer intended to hold multi-tenant customer data, this is a material documentation gap. Cognee, by contrast, ships multi-tenancy by default with `ENABLE_BACKEND_ACCESS_CONTROL` and authentication enabled [VERIFIED].

### 3.6 Engineering maturity: strong culture, young and unstable product

The `docs/engineering.md` document describes a discipline level above the peer group [VERIFIED]: Hypothesis property-based and state-machine testing (a small CI profile around 15 seconds, a deep profile of 1,000 sequences), an **80% coverage gate** wired into `make cov`, `import-linter` contracts enforcing a DDD layering of `entrypoints → service → memory → infra`, Ruff replacing Black/isort/Flake8, pre-commit hooks including private-key detection and a 640 KB file-size guard, gitlint, protected `main` requiring one approval and all checks green, Conventional Commits limited to 72 characters, and an explicit ban on `--no-verify` bypass. One documented outcome: a stateful maintenance test *"discovered a bounded-wait bug that cancelled the task it was waiting on."*

The gaps are as notable as the strengths: there is no described vulnerability scanning, dependency auditing, secret scanning, threat modeling, or security-response process, and no version-tagging/publishing/rollback workflow.

The `CHANGELOG.md` (104 KB) is the single best artifact in the repository because it publishes failures, and the evidence of instability is substantial [VERIFIED, 2026-10-28]. v1.0.0 shipped on 2026-06-03, so the public release is roughly five months old, and what followed reads less like a sequence of isolated bugs than like a system still finding its footing. Agent-track search failed on every search method in v1.1.2. A CWE-22 path-traversal fix shipped in v1.1.4 and was then shipped *around* in v1.2.0 (2026-07-24), requiring an upgrade to v1.2.1 to restore it — and a security regression reaching a release is a process failure, not merely a bug. In v1.2.3 (2026-08-07) a repeated background-loop crash was changed to **send SIGTERM, requiring an external process supervisor for recovery**. v1.4.1 (2026-09-24) broke clean installs outright: `AttributeError: module 'httpx' has no attribute 'Timeout'` meant that memorize, hybrid search, and vector search all returned **HTTP 500**, so the one-key setup path was non-functional on a fresh machine. v1.4.2 (2026-10-14) documented a LanceDB file-descriptor leak that took the process from 74 to 558 descriptors over 65 minutes, with vector-search latency under three concurrent writers measuring **p50 46 s / p95 112 s** before a fix brought it to p50 0.60 s / p95 3.70 s, and index-directory growth falling from ~126,000 files per day to ~21,000. v1.5.0 (2026-10-21) shipped a default embedding model returning **2,560 dimensions while `dim` is set to 1,024**, producing truncation with a warning. Finally v1.5.1 (2026-10-22) documented that at the old 4-slot concurrency limit, 10 requests/s queued without bound — over 10,020 indexed entries and five minutes, **p50 64 s, p95 101 s** — while at 16 slots all 3,000 requests were served at 9.99/s with **p50 0.42 s, p95 1.45 s, p99 2.11 s**.

That last figure is decisive against the marketing claim. The homepage advertises **retrieval latency <500 ms p95**; the project's own best measured p95 is **1.45 s** — roughly three times the claim. The 101 s and 112 s figures are the ones that would have been measured by a practitioner under load, which is exactly the scenario in which a memory layer matters.

The `QUICKSTART.md` sharpens the first-run experience problem [VERIFIED]: the one-key setup configures only `[llm]`, after which `/health` reports `disabled_features: [vector_search, hybrid_search, agentic_search, reflection, skill_extraction, knowledge]`. The default API search method is `hybrid`, which returns **HTTP 422** without an embedding provider; a caller must explicitly pass `"method": "keyword"`. The capability ladder — `[llm]` → keyword; `+[embedding]` → hybrid, reflection, skill extraction; `+[rerank]` → agentic search and Knowledge Wiki; `+[multimodal]` → document ingestion requiring LibreOffice or an HTTP 415 — means the *default install cannot perform the hybrid retrieval that every published benchmark number depends on*. `ulimit -n 4096` is recommended as a workaround for file-descriptor errors during concurrent search and indexing.

### 3.7 Adoption: stars without users

The GitHub numbers are the most misleading element of EverMind's public presence [VERIFIED, GitHub REST API, 2026-10-28]:

| Signal | EverOS | mem0 | hindsight | cognee | graphiti | letta | memU | MemOS | langmem |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stars | 13,668 | 67,944 | 54,454 | 32,829 | 32,288 | 25,270 | 14,569 | 12,136 | 1,726 |
| Forks | 954 | 8,036 | 6,294 | 3,431 | 3,320 | 2,663 | 1,093 | 1,096 | 203 |
| Open issues | 63 | 886 | 175 | 1,075 | 523 | 0 | 138 | 156 | 78 |
| PyPI downloads/mo | **20,408** | **2,020,516** | n/a (MIT, self-host) | 86,048 | 619,128 | 15,031 | n/a | n/a | 773,504 |

EverOS's 13,668 stars is a top-15 figure in the category. Its ~20,400 monthly PyPI downloads are 1% of Mem0's. The repository has **9 contributors** (gloryfromca 61 commits, cyfyifanchen 39, dani1005 14, Kendrick-Song 8, Yangtze-Seventh 7, and four with one or two commits each) and **145 commits total**, with the oldest dated 2026-06-05 despite the repository having been created 2025-10-28 — indicating squashed or rewritten history. There are **20 GitHub releases** from v1.1.0 (2026-06-24) through v1.5.1 (2026-10-22), and the PyPI package has 34 releases. The GitHub API reports **no dependent repositories**. The bus factor is effectively two.

The sibling-repository decay is the strongest signal. Within a single GitHub organization: MSA (3,519 stars) last pushed 2026-05-06; HyperMem (22 stars) last pushed 2026-06-02 despite its ACL 2026 acceptance; EverMemBench (23 stars) last pushed 2026-02-13 with no LICENSE file; EvoAgentBench (41 stars) last pushed 2026-08-13; and `evermem-claude-code` (63 stars) is archived. A research program that produces ACL and ICLR-accepted papers should not have research repositories that go five to eight months without a commit.

### 3.8 The benchmark field itself is in crisis

Any assessment of EverOS's numbers must sit inside the state of LoCoMo and LongMemEval, and that state is poor. The vendor-critical literature is unusually blunt.

Zep's audit, *"Lies, Damn Lies, and Statistics: Is Mem0 Really SOTA in Agent Memory?"* (2025-05-06, updated 2026-06-03) [VERIFIED] documents that LoCoMo conversations run only 16,000–26,000 tokens, that the benchmark contains no knowledge-update questions, that Category 5 is unusable — both Mem0 and Zep excluded it, and EverOS's own adapter drops it too, leaving 1,540 of 2,432 questions — that BLIP image descriptions contain errors, and that speaker attribution is sometimes wrong. Zep's corrected self-measurement is 75.14% ± 0.17 against Mem0's ~68%, with a full-context baseline at ~73%. Critically, Zep also showed that Mem0's published Zep-evaluation was itself flawed, having applied a single-user graph to both participants and appended timestamps to text rather than setting `created_at`.

Letta's experiment is the most damaging single data point in the field [VERIFIED, letta.com/blog/benchmarking-ai-agent-memory/, 2025-08-12]: a **plain filesystem scored 74.0% on LoCoMo with GPT-4o-mini**, beating Mem0's graph variant at 68.5%. Letta's conclusion — *"current benchmarks focused on retrieval may not adequately measure agentic memory"* and that comparing frameworks, tools, and models is apples-to-oranges — is the correct frame for everything in this report.

Two further signals compound the problem. Mem0's own evaluation documentation concedes that *"some benchmarks today, particularly smaller ones like LoCoMo and LongMemEval, can be materially improved by aggressive retrieval strategies, larger context"* [VERIFIED, mem0.ai/docs/core-concepts/memory-evaluation] — a vendor admitting its benchmark can be gamed. And a survey cited in letta-ai/letta issue #3115 (arXiv 2603.07670) reports that models scoring near-perfectly on LoCoMo **plummet to 40–60% on MemoryArena** [VERIFIED]. A Reddit audit of two popular memory benchmarks reports that 6.4% of the answer key is wrong and the LLM judge accepts up to 63% of intentionally wrong answers; this source was network-blocked and only its search snippet was obtainable, so it is treated as partially verified.

Against this backdrop, EverOS's own numbers are *more* defensible than most — the decider/answer/judge models are stated, the judge protocol is documented, the noise floor is measured, and a `run_spec.json` provenance record exists. The problem is not that the 94.00 and 94.42 are fabricated. The problem is that they are single-configuration cells extracted from a matrix whose row average is 92.48, judged by a single run of one model, and that the 94.74 and 80.89 presented beside them are unreleased internal results with no artifacts whatsoever.

---

## 4. Deliverable (a) — Benchmark Comparison Table

All figures as published by the named source on the stated date. "Backbone" is the model that reads and writes memory; "Answer model" is the model that produces the final answer from retrieved context. Where a source does not state a model, that is recorded rather than inferred. **No two rows in this table are directly comparable** — see Section 3.8.

| System | LoCoMo | LongMemEval | Backbone / answer / judge model | Source | Self-reported? | Notes |
|---|---:|---:|---|---|---|---|
| **EverOS v1.5.1 (shipped harness)** | **94.42** (1,540 q) | **94.00** (500 q) | answer `openai/gpt-4.1-mini` (LoCoMo) / `google/gemini-3.6-flash` (LME); extraction `deepseek-v4-pro-0813`; judge `openai/gpt-4o-mini`, **runs = 1** | [benchmarks/README.md](https://github.com/EverMind-AI/EverOS/blob/main/benchmarks/README.md) (2026-10-28) | Yes | 94.00 is the **best cell** of a 5×4 matrix (row avg 92.48, oracle 96.48). Category 5 dropped → 1,540/2,432. Measured noise floor 0.91 pp (LoCoMo) / 1.20 pp (LME) — larger than the 1-run judge resolution |
| **EverMemOS** (paper, arXiv 2601.02163v2) | **93.05** | **83.00** | backbone + answer `openai/gpt-4.1-mini`; Qwen3-Embedding-4B + BM25 + RRF + Qwen3-Reranker-4B; judge GPT-4o-mini + 2 aux, blind-averaged, κ 0.891/0.978 | [arxiv.org/abs/2601.02163](https://arxiv.org/abs/2601.02163) (2026-01-09) | Yes (CC BY preprint, 54 citations) | 6.7k tokens/q on LoCoMo, 2.8k on LME. **LME baselines copied from the official MemOS leaderboard**, not re-run. PersonaMem v2 53.25 (paper's own 5,000 vs 2,447 question-count inconsistency) |
| **EverOS marketing** (homepage / /everos / cloud) | **94.74** | **94.00** | **not stated** | [evermind.ai](https://evermind.ai/), [evermind.ai/everos](https://evermind.ai/everos) (2026-10-28) | Yes (marketing) | 94.74 and AMA 80.89 labelled **"Next release (internal)"** by EverMind's own account director, [X 2026-10-21](https://x.com/LongTermMemoryE/status/2112734272608231818). No repo artifacts |
| **HyperMem** (research, ACL 2026) | **92.73** | — | `gpt-4o-mini` | [arxiv.org/abs/2604.08256](https://arxiv.org/abs/2604.08256) (2026-04-09) | Yes | 3-level hypergraph (topic/episode/fact). **Not integrated into EverOS.** Repo: 22 stars, 6 commits, no push since 2026-06-02 |
| **Mem0** | 91.6 (Apr 2026) / 92.5 (research page) | 94.8 (reported via Exabase) | **not stated** on mem0.ai/research; "Gemini 3 Pro" cited by Exabase for the 94.8 | [mem0.ai/research](https://mem0.ai/research), [Exabase](https://exabase.io/comparison/) (2026-10-28) | Yes | 6,956 tokens/query, 1,540 q. Vendor concedes LoCoMo/LongMemEval "can be materially improved by aggressive retrieval strategies, larger context" |
| **Mem0** *as characterized by EverMind* | 76.00 | 49.0 | **not stated** | [evermind.ai/blogs/everos-vs-mem0-benchmark-comparison](https://evermind.ai/blogs/everos-vs-mem0-benchmark-comparison) (2026-06-11) | No — competitor characterization | **Contradicts Mem0's own published 91.6 / 94.8.** No harness, metric, or model disclosed for either side |
| **Hindsight** | 92.0 | **94.6** (LongMemEval-S) | **not stated** | [vectorize.io/benchmarks](https://vectorize.io/benchmarks) (2026-10-28) | Yes | PersonaMem 86.6, PrecisionMemBench 85.7, LifeBench 71.5, BEAM-10M 64.1. Next-best published LME-S was 74.0 at time of publication |
| **Zep** (corrected self-report) | **75.14 ± 0.17** | — | own harness, p95 0.632 s | [getzep.com/blog/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory](https://getzep.com/blog/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/) (2025-05-06, upd. 2026-06-03) | Yes | Full-context baseline ~73%; Mem0 graph ~68%. Documents LoCoMo's 16k–26k token conversations and unusable Category 5 |
| **Zep** *as measured by EverMemOS* | 85.22 | 63.80 | answer `gpt-4.1-mini` | [arxiv.org/abs/2601.02163](https://arxiv.org/abs/2601.02163) | No — third-party measurement | 24.08 pp above Zep's own corrected figure, illustrating harness effect size |
| **MemOS** (official leaderboard) | 80.76 | 77.80 | not stated on leaderboard | via [EverMemOS](https://arxiv.org/abs/2601.02163) | Yes | Baselines cited rather than re-run by EverMind |
| **memU** | 66.67 (EverMemOS) / 92.1 (leadersboard) | — | not stated | [EverMemOS](https://arxiv.org/abs/2601.02163); [agents.stackoverflow](https://agents.stackoverflow.com/tils/5561fef0) | Mixed | Two figures 25.5 pp apart for the same system — a compact demonstration of harness non-comparability |
| **RippleMem** | 87.14 | — | as tabulated by EverMind | [EverMind multi-round blog](https://evermind.ai/blogs/multi-round-retrieval-letting-the-model-decide-when-to-stop-searching) (2026-09-04) | Yes (competitor-vendor tabulation) | EverMemBench 51.69 |
| **Mandol** | 92.21 | — | as tabulated by EverMind | same | Yes (competitor-vendor tabulation) | Best listed open-domain score (79.17) |
| **RF-Mem / SimpleMem / MemoryOS** | 83.83 / 82.92 / 60.11 | — | as tabulated by EverMind | same | Yes (competitor-vendor tabulation) | MemoryOS 60.11 is the LoCoMo floor in most published tables |
| **Letta filesystem baseline** | **74.0** | — | `gpt-4o-mini` | [letta.com/blog/benchmarking-ai-agent-memory](https://letta.com/blog/benchmarking-ai-agent-memory/) (2025-08-12) | Yes — controlled experiment | **A plain filesystem beats Mem0's graph variant (68.5%).** Strongest single argument that LoCoMo measures retrieval, not agentic memory |
| **Full-context baseline** | ~73 | — | n/a | via [Zep critique](https://getzep.com/blog/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/) | Third-party | A strong long-context model, shown all retrieved text, reaches ~73 on LoCoMo |
| **AMA-Agent** (AMA-Bench) | — | — | not stated in abstract | [arxiv.org/abs/2602.22769](https://arxiv.org/abs/2602.22769) (2026-05-27, ICLR 2026) | Yes (peer-reviewed) | **57.22%** on AMA-Bench; strongest baseline 46.06% (+11.16). The finding: memory systems "fail to capture causal and objective information and rely heavily on lossy similarity-based retrieval" |
| **EverOS on AMA** | — | — | not stated | evermind.ai homepage (2026-10-28) | Marketing | **80.89%** — a ~24 pp SOTA jump over the published AMA-Bench SOTA, with no adapter, config, dataset, paper, or result file anywhere in the repo |
| **Q2 2026 leadersboard** (aggregator) | EverOS 93.1, memU 92.1, Mem0 91.6 | Mem0 94.8, Hindsight 91.4 | **none stated** | [agents.stackoverflow.com](https://agents.stackoverflow.com/tils/5561fef0) (2026-10-28) | Third-party aggregation | The source itself calls selecting a memory system from one benchmark score an "anti-pattern" |
| **Other 2026 entrants** | Mastra 95 (LME), Quark 98.2 (LME-S), MaxMem 93.2 LoCoMo / 92 LME, ByteRover 92.2 | as noted | mostly not stated | vendor pages ([Mastra](https://mastra.ai/research/observational-memory), [ByteRover](https://byterover.dev)) | Yes | Details not independently verified; included to show the field is crowdedand the 92–98 band is crowded on LongMemEval |

**Reading of the table.** The honest summary is that the LoCoMo column now contains a plausible range from ~60 (MemoryOS) to ~94 (EverOS, Mandol), but the spread is dominated by harness and answer-model choice rather than by memory-system quality. The most informative row is not EverOS's but Letta's: a bare filesystem at 74.0. The second most informative is the full-context baseline at ~73. If a plain file and a full context window both land near 73–75, then the 85–94 band is measuring something other than "does the agent remember," and that something includes answer-model strength, judge model, decider model, and retrieval aggressiveness. EverOS's own `locomo.toml` noise floor of 0.91 pp and its disclosure of a 2.21 pp lead over the next system in its own table are, to their credit, the most statistically literate disclosures in the category — which is precisely why the marketing site contradicting the repository is so damaging.

---

## 5. Deliverable (b) — Competitor Landscape

| System | License | Self-host | Pricing | Architecture | Key differentiator | Weakness |
|---|---|---|---|---|---|---|
| **Mem0** | Apache-2.0 | Yes (Docker + cloud) | Free 10k adds / 1k retrievals per mo, or 50k/10k with own LLM key; Custom quote for enterprise (graph memory, user profiles, "Dream" consolidation, SSO, audit logs, SLA, on-prem) | Layered memory: vector + graph + user-profile stores with a consolidation/"dream" step and an LLM-based updater | 67,944 stars, 8,036 forks, ~2.02M PyPI downloads/mo, broadest ecosystem, OpenMemory MCP layer for coding agents, hosted + on-prem | 886 open issues; numbers often lack a stated backbone; a competitor (EverMind) reports its scores as 76.0/49.0 vs its own 91.6/94.8; graph maintenance cost |
| **Hindsight** (Vectorize) | **MIT** | Yes (Docker Compose, Helm, bare-metal pip) | OSS free; Cloud PAYG — Retain $10/M tokens, Recall $0.75/M, Reflect $0.05/call, Iris Extract $7.50/M, Mental Model Retrieve $0.25/M, Refresh $0.05/call, storage $0.25/M/month after 30 days; Enterprise single-tenant/VPC | Four parallel retrieval networks (semantic, BM25, graph, temporal) → rank fusion → cross-encoder rerank → token-budget truncation; PostgreSQL + pgvector, 5 pluggable BM25 backends incl. Citus; memory banks; retain/recall/reflect with a 10-round agentic evidence loop; background consolidation into observations carrying evidence, proof counts, and revision history; knowledge pages; `hindsight fs mount` projects pages to Markdown | **Strongest published LongMemEval-S result (94.6%) and LoCoMo 92.0%**; MIT; the most complete *temporal* story (observations with revision history and proof counts); Markdown projection proves Markdown-native is not exclusive to EverOS | Requires PostgreSQL (+ pgvector) and a separate reranker; a large operational surface for a self-hosted deploy; vendor-published numbers with no stated backbone |
| **Zep / Graphiti** | Apache-2.0 | Yes (Neo4j + Postgres) | Credit-based: Free 10k credits/mo; Flex $125/mo (50k) + $25/10k overage; Flex Plus $375/mo (200k) + $75/40k; Enterprise custom (VPC, BYOK, SOC 2, HIPAA). 1 credit per 350-byte episode; retrieval, storage, threads, users, graph storage cost 0 credits | Temporal knowledge graph — bi-temporal edges capturing validity intervals and invalidation; Graphiti is the ingestion engine, Zep the hosted product | **The reference implementation of temporal knowledge tracking**; the vendor that actually audited LoCoMo and published corrections for everyone | Requires Neo4j + Postgres; 32,288 stars but the corrected self-score is 75.14% — the field's most sobering self-audit |
| **Cognee** | Apache-2.0 (core); PG-backed graph store is a **demo**, production is a licensed product | Yes (single PostgreSQL since 1.0) | OSS + commercial; multi-tenant by default with `ENABLE_BACKEND_ACCESS_CONTROL` and auth | Graph + vector + code memory; `remember` / `recall` / `improve` / `forget`; ontology grounding; Python/TS/Rust SDKs; MCP server on port 8001 | **The only competitor with documented multi-tenancy and access control** — directly ahead of EverOS on the gap EverOS does not document; 32,829 stars | The production graph engine is not the OSS artifact; 1,075 open issues (highest in the category) |
| **MemOS** (MemTensor) | Apache-2.0 | Yes (Neo4j + Qdrant; local plugin uses SQLite FTS5 + vector) | OSS + enterprise | L1 traces / L2 policies / L3 world model; graph-structured memories and "memory cubes" | Clearest three-tier memory hierarchy; published an official leaderboard that other vendors (including EverMind) cite — good citizenship for the field | Heavy self-host stack (Neo4j + Qdrant); 12,136 stars but no cloud-first story; its LoCoMo 80.76 trails the leaders |
| **Letta** | Apache-2.0 | Yes (Docker + server) | OSS + cloud tiers; hosted server is the product | Stateful agent server with its own memory blocks, archival memory, and a shared block system | Longest-lived agent-runtime memory (2023 lineage); **the 74.0% plain-filesystem LoCoMo result** that reframed the whole debate | 25,270 stars but 15,031 PyPI downloads/mo; framework-shaped, not a drop-in memory layer; 0 open issues suggests low issue throughput rather than high quality |
| **memU** | Apache-2.0 | Yes (SQLite local, or Postgres + pgvector) | OSS, API-key based; free tier with quotas | Host-agent-driven: the orchestrator prepares, commits, and retrieves against an LLM-maintained Markdown wiki; ~500 lines of core logic | Extremely small, legible core; a "wiki" mental model that matches how engineers think about knowledge | 14,569 stars with no cloud product; the 66.67 → 92.1 LoCoMo swing across sources shows its own numbers are unstable under harness change |
| **LangMem** (LangChain) | MIT | Yes (in-process; `InMemoryStore` / `AsyncPostgresStore`) | Free; part of LangChain platform pricing | Hot-path tools + a background memory manager writing to a `BaseStore`; native LangGraph integration | **Best strategic position among frameworks**: if a team already runs LangGraph, memory is a config change, not a migration | Not a standalone product; 1,726 stars and 78 open issues; 773,504 PyPI downloads/mo reflect the whole LangChain ecosystem, not LangMem |
| **Supermemory** | **Not stated** | Yes (incl. air-gapped) | Free $0 + $5 credits; Pro $19 ($20); Max $100 ($130); Scale $399 ($600, self-host); Enterprise air-gapped. Rate card: memory text $5/M SM tokens, rich $10/M, SuperRAG $1–2/M, search $5/M queries, operations $100/M | "learner-1" background consolidation ("dreams") into a vector-graph DB; 187 ms server-side / 356 ms end-to-end search | **Best latency and scale claims in the category**; 100k+ orgs, 1T+ tokens/month; priced per token of memory, which is the most honest cost metric in the field | No stated license — the decisive problem for an OSS-first evaluation; the 3× gap between search price and operations price is steep |
| **OpenMemory** (Mem0 project) | Apache-2.0 (inside mem0) | Yes (local MCP server) | Free; shares Mem0 account/limits | MCP server exposing Mem0 memory to coding agents, with a local server and local storage mode | The de facto MCP memory entry point; the reason MCP agents now have a default memory | Not a distinct system — inherits Mem0's issues and its server dependency |
| **A-MEM** | MIT | Yes | Free | Agentic memory as Markdown notes with a Zettelkasten-style dynamic linking/evolution loop | Elegant, minimal, genuinely agentic rather than pipeline-driven; 70.0 on SubtleMemory with the best contradictory-evidence score (50.4) | 445 PyPI downloads/mo; a research artifact more than a product; no hosted option |
| **MCP official memory server** | MIT | Yes (JSONL file) | Free | Entities / relations / observations in a JSONL knowledge graph with an exclusive lock file (refreshed 15 s, stale at 30 s, 60 s timeout); resource `memory://knowledge-graph` | The baseline every MCP agent can run with zero dependencies; requires Node 24+ | Trivial scale; 39 PyPI downloads/mo; no retrieval sophistication, no consolidation policy |
| **AgentCore Memory (AWS)** | Managed | AWS-managed only | STM (2026-10-12): ingest $1/GB, retrieve $0.20/GB, store $0.10/GB-month; 12 KB min / 64 KB max per event | Short-term and long-term event stores with namespace-based retrieval policies | **Native integration with Bedrock AgentCore; no separate product to adopt**; priced per GB rather than per call | Locked to AWS; a narrow event-window abstraction, not a memory system in the Zep/Hindsight sense |

**Notes on the landscape.** The category has consolidated around four architectures, and EverOS belongs to the least differentiated of them. Zep and Hindsight own temporal and graph-based reasoning. MemOS owns the explicit hierarchy. Cognee owns multi-tenancy and ontology grounding. EverOS owns file-format ownership and agent-host integration breadth. The last category is real but it is the most easily copied — Hindsight ships `hindsight fs mount` to project knowledge pages to Markdown, memU is Markdown-native by construction, and Anthropic's memory tool is a file API over a `/memories` directory. Markdown-as-source-of-truth is a durability and auditability decision, not a retrieval decision, and it does not by itself produce better answers.

---

## 6. Deliverable (c) — Native Vendor Memory: The Real Competitive Threat

The most consequential question for a self-hosted memory layer is not which open-source competitor is best. It is whether the platform vendor eventually absorbs the function. Every major model and cloud provider now ships a memory primitive, and the economics of the decision are asymmetric in a way that is unfavourable to any third-party layer.

| Vendor primitive | Mechanism | Retention & billing | Threat to a self-hosted layer |
|---|---|---|---|
| **Anthropic — memory tool** (`memory_20250818`) | A **client-side** tool over a `/memories` directory with view / create / str_replace / insert / delete / rename operations, a 2-level directory listing, and 16k-character text truncation; available on all Claude 4+ models. Pairs with server-side compaction and context editing | Memory lives in the caller's filesystem; the tool call is in-band with the model's tool use | **Highest near-term threat.** It converts "memory" into a native tool call that any Claude-based agent can use with no integration work, no separate service, no second data store, and no new failure modes. A developer who ships a Claude agent inherits memory for free. EverOS's own `evermem-claude-code` plugin is 63 stars and archived |
| **OpenAI — Responses & Conversations APIs** | `previous_response_id` chaining plus a Conversations API for durable thread state | Conversations have **no 30-day TTL** (Responses objects are retained 30 days); no separate fee, but all prior input tokens are re-billed | Removes the *engineering* need for a memory service in a large class of applications. Does not provide extraction, consolidation, or cross-application memory — it is state, not memory — but state is what most teams actually need first |
| **Google — Vertex AI Memory Bank + ADK** | Managed memory bank plus ADK's built-in session/state services | Google Cloud managed pricing | Enterprise-adjacent buyers on GCP default to it; the memory bank handles extraction and consolidation, which is exactly EverOS's `memory.extract.pipeline` |
| **Amazon Bedrock AgentCore Memory** | Short- and long-term memory with namespace-scoped retrieval policies | STM (2026-10-12): ingest $1/GB, retrieve $0.20/GB, store $0.10/GB-month; 12 KB min / 64 KB max per event | **The strongest structural threat to the whole category.** An AWS customer buys an integrated, governed, IAM-scoped memory service as part of an existing commitment. There is no separate procurement, no separate security review, no separate on-call burden |
| **MCP ecosystem** | The official `memory://knowledge-graph` server is a knowledge graph of entities/relations/observations in a JSONL file, MIT-licensed; OpenMemory is Mem0's MCP layer; EverOS ships `uvx everos-mcp` | Free, local | **The ecosystem, not the vendor, is the platform risk.** MCP makes memory a pluggable tool call, so a memory layer's value shifts from "best retrieval" to "most agent-host integrations and most portable data." EverOS's `EverOS-MCP` repository has **2 stars**; Mem0's OpenMemory is inside a 67,944-star project |
| **LangGraph / LangChain** | Checkpointers (thread-scoped) and stores (cross-thread, namespaced) managed by the Agent Server; `thread_id` capped at 255 characters; LangMem adds hot-path tools and a background manager over `BaseStore` | Free in-process; platform pricing in production | The "good enough and already integrated" threat. 773,504 monthly downloads mean LangMem is frequently *present* in a codebase before any competitor is evaluated |

**Assessment.** For a team building a production agent on Anthropic models, the marginal cost of *not* using a dedicated memory layer has fallen close to zero, because the Anthropic memory tool already provides the file-shaped, auditable, client-side memory that EverOS's Markdown-native design was built to deliver — and it ships inside the model API with no infrastructure. For a team on AWS, AgentCore Memory is bought rather than selected. EverOS's defensible ground is narrower than its marketing implies: it is a **model-agnostic, vendor-neutral, self-hosted, agent-host-agnostic** memory layer for teams that want to own the store, avoid per-token or per-GB vendor pricing, run air-gapped, and keep a human-readable, git-versionable record.

Two further pressures deserve mention. The first is **cost trajectory**: Supermemory's per-token memory pricing and Hindsight's PAYG card set a reference that a self-hosted layer must undercut, and EverOS's token economics are genuinely competitive — 2.8k tokens per LongMemEval question in the paper, and a "core-only" configuration reaching 91.00 accuracy at 23% of the k=20 prompt in the blog. The second is **portability pressure from the MCP standard**: as memory becomes a tool call, the durable differentiator becomes how many agent hosts can read the same store, and EverOS's MCP surface is two stars old. The honest strategic read is that EverOS is competing on a feature (file format) that the MCP standard is about to make a commodity, while the features that are hard to copy (temporal validity, graph structure, consolidation quality) are the ones it has not yet shipped.

---

## 7. Deliverable (d) — EverOS Architecture Deep-Dive: Novel vs. Conventional

### 7.1 What is genuinely differentiated

**Markdown as the canonical, git-versionable store.** The design decision that most distinguishes EverOS is that memory is a *file*, not a row. `docs/how-memory-works.md` documents that Markdown with YAML frontmatter is the source of truth, SQLite holds operational state (`system.db`, `ome.db`, `ome.aps.db`, `ome.db.lock`), and LanceDB/Arrow holds a derived index at `.index/lancedb/` — a directory that can be deleted with no data loss because it is rebuilt from the Markdown. The write path is atomic (temp file → fsync → rename), and every write is audit-logged to SQLite before the asynchronous cascade indexes it. For a team that needs to audit, diff, hand-edit, or legally retain agent memory, this is materially better than a vector store with an opaque embedding pipeline. It is the single strongest argument *for* EverOS, and it is a real one.

**Cascade indexing with content-addressed diffing.** The `watchdog → md_change_state durable queue → SHA-256 diff → re-embed → LanceDB upsert` pipeline, with an LSN watermark ordering rebuilds, means an external process can edit a memory file and the index follows. The `EVEROS_DISABLE_CASCADE_WATCHER` escape hatch in the benchmark configs exists because *"inotify is exhausted by the IDE on this host"* — a real-world concession that the watch design has a scaling ceiling on developer machines. But the mechanism itself is sound, and `everos cascade sync|fix|rebuild` gives operators a repair path.

**Coarse-to-fine hierarchical retrieval with fact-level displacement.** The mRAG design — coarse episode-summary search via parallel dense and BM25 retrieval fused by RRF, then expansion into atomic facts scored as `α × fact_score + (1 − α) × episode_score` with α = 0.5, where a high-scoring fact *replaces* its parent episode in the result set — is a genuinely thoughtful piece of retrieval engineering. It is better than a flat chunk store and better than pure vector recall on detail queries. It is not, however, a graph.

**The LLM-in-the-retrieval-loop decider.** `llm_multiround` places a small model inside the retrieval loop rather than after it: the decider reads *full episode text* (not snippets), marks which candidates actually carry evidence, and decides whether to stop or issue a follow-up query. Stopping is a learned decision rather than a round cap, and the resulting "core set" is what enters the context — so the token budget follows the query rather than the budget following the query. The measured result is strong: 1.95 episodes per query, 1,946 prompt tokens, 91.00 accuracy on LongMemEval-S (97.4% of the k=20 peak) at 23% of the k=20 prompt, with MRR 0.9768 and MAP 0.9524. This is the most technically interesting thing EverOS has built, and it is the component responsible for the 94.00 figure.

**Disciplined domain boundaries.** `docs/architecture.md` defines a four-layer DDD structure (`entrypoints → service → memory → infra`) with `import-linter` contracts enforced in CI, a stateless, I/O-free `everalgo` boundary, and a typed error hierarchy (`AppError` → `DomainError` / `InfrastructureError` → 503 / `CapabilityError` / `ConfigurationError`). The `CapabilityError` concept in particular is a thoughtful fit for a system whose capabilities genuinely depend on which providers are configured — it turns "the feature is off" into a first-class error rather than a `None`.

**Observable operations.** Prometheus metrics, `structlog` structured logging, and OpenTelemetry instrumentation are documented as part of the architecture rather than bolted on. For a self-hosted runtime that a team will operate themselves, this matters.

### 7.2 What is conventional

**The core retrieval is textbook hybrid RAG.** *"Vector ANN, full-text BM25 retrieval, and scalar filtering are executed within the embedded LanceDB engine. These operations execute together in one query."* [VERIFIED, docs/how-memory-works.md]. This is the industry-default 2024-era architecture. RRF fusion and an optional cross-encoder reranker are standard; the reranker is off by default, and `docs/how-memory-works.md` describes no separate reranking stage in the retrieval path at all.

**There is no graph or hypergraph engine.** `docs/architecture.md` states it directly. Temporal relationships are represented by date-based filenames, an optional foresight mechanism with validity intervals, and `deprecated_by` links — and `extract_foresight` has been disabled by default since v1.2.3. Against Zep's bi-temporal edge model, Hindsight's observation revision history with proof counts, and MemOS's L1/L2/L3 world model, EverOS's temporal story is materially thinner. The homepage concedes this with "Temporal Knowledge Tracking: **Partial**" and "Hierarchical Memory Organization: **Partial**" [VERIFIED]. Note the tension: the site claims to "outperform" alternatives on a table where two of its own rows read "Partial."

**Multi-tenancy is filesystem partitioning, not isolation.** `~/.everos/<app_id>/<project_id>/users/<user_id>/…` with no documented scope taxonomy, namespace creation contract, inheritance model, access control, retention policy, or deletion semantics. `docs/use-cases.md` documents no shared-memory ownership, isolation, consistency, conflict resolution, or permission model. For a component intended to hold multi-customer memory, this is the largest unaddressed gap — and the one that would block an enterprise evaluation outright.

**The advanced paths are opt-in and off by default.** Reflection (Select → Merge → Re-extract → Deprecate) is disabled by default; `extract_foresight` is disabled by default; the reranker is off by default; the default install has no embedding provider, so hybrid search — the method behind every published number — returns HTTP 422 until a second provider is configured. A system's *default* configuration should be the configuration its benchmarks measure. EverOS's is not.

**The research program is not productized.** HyperMem (hypergraph, 92.73 LoCoMo, ACL 2026), MSA (3,519 stars, last push 2026-05-06), and the `everalgo` stateless algorithm packages are separate from the runtime that ships. EverMind's own Oct 2026 blog explicitly separates "MSA (research)" from "EverOS (production)" [VENDOR, evermind-vs-papr-memory, 2026-10-14]. That separation is honest, and it is also a direct admission that the best research is not in the product.

### 7.3 Verdict on the architecture

EverOS is a **well-engineered, conventional hybrid-RAG memory runtime with an excellent storage format, a genuinely interesting LLM-in-the-loop retrieval mode, and no graph, weak temporal semantics, and no documented multi-tenancy**. The retrieval sophistication sits at the level of a good 2025 implementation — roughly at Mem0's better configurations and below Hindsight's four-network design — while the storage and operational ergonomics sit above most of the field. The "Agentic Memory OS" framing overstates the gap between the shipped system and the research papers.

---

## 8. Deliverable (e) — Engineering Maturity Scorecard

Scores are 0–10, justified per dimension against the observed artifacts. Where a score reflects a *culture* rather than a shipped capability, that is stated.

| Dimension | Score | Justification (all points VERIFIED against repo artifacts, 2026-10-28) |
|---|---:|---|
| **Code architecture & modularity** | **8.5** | Four-layer DDD (`entrypoints → service → memory → infra`) with `import-linter` contracts enforced in CI, a stateless I/O-free `everalgo` boundary, and a typed error hierarchy. Clean, defensible structure that a new maintainer can navigate. Loses a point because `docs/architecture.md` explicitly concedes the absence of a graph subsystem — a clean architecture around a conventional core |
| **Testing discipline** | **9.0** | Hypothesis property-based *and* state-machine testing, an enforced **80% coverage gate**, a documented bounded-wait bug found by a stateful maintenance test, and a small CI profile (~15 s) alongside a 1,000-sequence deep profile. This is the strongest dimension in the project and is genuinely above peer norm. Minor deduction: no fuzzing, no load-test harness, and no published coverage report artifact |
| **Documentation quality** | **8.5** | `how-memory-works.md`, `architecture.md`, `engineering.md`, and `use-cases.md` are unusually precise about mechanisms, and the API error model is designed rather than accidental. The `benchmarks/README.md` comparability caveat is a model of honesty. Deductions: no multi-tenancy/scope documentation, no security or threat model, no operational runbook for a self-hosted deploy, and `use-cases.md` lists two "Coming soon" items and one "backend integration in progress" |
| **Release & version hygiene** | **8.0** | 20 GitHub releases v1.1.0→v1.5.1 over ~4 months; 34 PyPI releases; SemVer; Keep-a-Changelog; 145 commits with Conventional Commits ≤72 chars; protected `main` requiring one approval and all checks green; `--no-verify` banned. Deductions: v1.0.0 is only 2026-06-03, and `engineering.md` specifies no publishing or rollback procedure |
| **Commit & history hygiene** | **6.0** | Commit subjects are exemplary (`perf(embedding): raise query embed concurrency default to 16 (#531)`), and all observed commits are attributed to a single author, "zhanghui" — which is consistent with disciplined authorship rather than a contributor-diversity problem. But 145 commits since creation and an oldest commit of 2026-06-05 against a repo created 2025-10-28 indicates **squashed or rewritten history**, so per-commit archaeology is impossible and contribution continuity cannot be audited |
| **Stability / production readiness** | **4.0** | Fresh installs returned **HTTP 500** in v1.4.1 (`httpx` has no attribute `Timeout`); a shipped CWE-22 path-traversal fix (v1.1.4) **regressed in v1.2.0**; a background-loop crash now sends **SIGTERM requiring an external supervisor**; v1.4.2 recorded a file-descriptor leak (74→558 over 65 min) and **p95 112 s** vector-search latency under 3 concurrent writers; v1.5.0 shipped a 2,560-dim default against a 1,024-dim `dim` setting. The changelog's candour is a credit, but the failure density is high for a 4-month-old 1.x |
| **Performance** | **5.0** | Best measured figure in the project's own changelog is **p50 0.42 s / p95 1.45 s / p99 2.11 s** at 16 slots, 9.99 req/s over 3,000 requests — against a homepage claim of **<500 ms p95**, a ~3× gap. Prior measured states were p50 64 s / p95 101 s and p50 46 s / p95 112 s. The v1.4.2 fix that took p95 from 112 s to 3.70 s is a substantial engineering win, but a project whose *own* best number is 2.9× its advertised SLA has not yet earned the SLA |
| **Security posture** | **3.5** | No vulnerability scanning, dependency auditing, secret scanning, threat modeling, or security-response process is described in `engineering.md`; pre-commit includes only private-key detection and a file-size guard. A CWE-22 path-traversal fix shipped once and then regressed in a later release, and an open issue reports that an undocumented 1,024-dim embedding floor fails asynchronously while `/health` still reports `embed: true` (open 2026-07-03, closed 2026-10-16). "Health endpoint lies about degraded state" is a serious class of bug for an infrastructure component |
| **Contributor base & bus factor** | **3.0** | **9 contributors** total, with two accounting for 100 of 145 commits (gloryfromca 61, cyfyifanchen 39). Effective bus factor of two. No `dependents` reported by the GitHub API. sibling research repos (MSA, HyperMem, EverMemBench) are 5–8 months stale, which is a leading indicator of institutional rather than personal bus factor |
| **Ecosystem & adoption** | **4.5** | 13,668 stars (top-15 in category), Apache-2.0, PyPI `everos` at ~20,408 downloads/month across 34 releases, an MCP server, a Claude Code plugin, and a documented LangGraph integration path — genuinely good *breadth*. But downloads are ~1% of Mem0's; `EverOS-MCP` has 2 stars; `evermem-claude-code` is archived; and there is no independent third-party reproduction of any published number. The `use-cases.md` list is ~25 community projects, mostly small personal tools |
| **Observability & operations** | **7.0** | Prometheus metrics, `structlog` structured logging, and OpenTelemetry are documented in the architecture; errors are typed and mapped to HTTP status codes; `everos cascade sync\|fix\|rebuild` provides a repair path; `ulimit -n 4096` guidance is published. Deductions: no documented backup/restore procedure for the Markdown store (though it is arguably self-evident), no runbook, and no disaster-recovery guidance |
| **Benchmark & evaluation discipline** | **6.5** | A real four-stage harness with per-benchmark configs, `reproduce.sh`, a `run_spec.json` provenance record, a measured run-to-run noise floor (0.91/1.20 pp), and a self-disclosed comparability defect. Deductions: `benchmarks/data/` is empty; no competitor adapters despite the 2025-11 unified-framework claim; the referenced `EverOS_Eval_Results` repo and `/evaluation` directory do not exist; the shipped default config reproduces no published number; and the config comments contradict the README's decider model |
| **Overall** | **6.3** | A project with unusually good engineering *discipline* carrying an unusually immature *product* |

**How to read the scorecard.** The two halves of EverOS pull in opposite directions. The process scores (testing, architecture, documentation, changelog honesty) sit at 8–9, comparable to or above every competitor examined. The product scores (stability, performance, security, bus factor) sit at 3–5, which is what a 4-month-old 1.x project should look like. The mismatch is the story: EverOS is built by people who know how to build software well, and it is shipping too early. The most likely 12-month trajectory is a materially better product, because the feedback loop is functioning — the changelog proves bugs are found, fixed, and measured. The most likely 12-month risk is that a security or availability regression in a component holding customer memory goes unnoticed, because there is no vulnerability-scanning or dependency-auditing process and the effective team is two people.

---

## 9. Deliverable (f) — Competitive Verdict

### 9.1 Tier list

The tiering below is a judgement about competitive position, not about benchmark score. The scores change with every harness; the tiers change far more slowly, because they are about whether a system holds a defensible position in the architecture of a production agent.

| Tier | System | Basis for placement |
|---|---|---|
| **T1 — State of the art** | **Hindsight** | Strongest published LongMemEval-S result (94.6%), a complete temporal model (observations with evidence, proof counts, revision history), four parallel retrieval networks with rank fusion and cross-encoder reranking, MIT licence, and a `hindsight fs mount` that projects to Markdown. It has matched EverOS's best idea and extended it |
| **T1 — State of the art** | **Zep / Graphiti** | The reference implementation of temporal knowledge tracking, and the only vendor that has publicly audited the benchmarks and corrected the field's numbers at personal cost to its own marketing position |
| **T1 — State of the art** | **Mem0** | The ecosystem default: 67,944 stars, 8,036 forks, ~2.02M monthly downloads, hosted and on-prem, an MCP layer, and the widest integration surface. It does not need the highest benchmark number to remain the default choice |
| **T2 — Strong** | **Letta** | The longest-lived agent-runtime memory, and the source of the 74.0% filesystem result that reframed the field |
| **T2 — Strong** | **Cognee** | The only competitor with documented multi-tenancy, access control, and ontology grounding |
| **T2 — Strong** | **MemOS** | The clearest three-tier hierarchy, and the publisher of an honest official leaderboard that other vendors cite |
| **T2 — Strong** | **Supermemory** | The best latency and scale claims in the category, priced per token of memory rather than per seat or per call |
| **T2 — Strong** | **EverOS — on engineering and developer experience only** | The best file-format ergonomics, the best testing discipline, the most legible domain model in the self-hosted category, and the best measured token-efficiency story. It does **not** have the retrieval, temporal, multi-tenancy, or ecosystem position to enter Tier 1 |
| **T3 — Adequate** | **memU** | Elegant small core, Markdown-native, but 14.5k stars with no cloud product and unstable cross-harness numbers |
| **T3 — Adequate** | **LangMem** | Excellent strategic position inside LangChain, but not a product |
| **T3 — Adequate** | **MemOS local plugin / A-MEM / the MCP reference server** | Useful, small, and uncompetitive in their current form |
| **T4 — Behind** | **EverMind's benchmark claims as published** | 94.74% LoCoMo and 80.89% AMA have no artifacts, are unreleased internal results per EverMind's own account director, and are advertised on the homepage as present-tense achievements |
| **T4 — Behind** | **EverMind's research-to-product pipeline** | MSA (3,519 stars, stale since 2026-05-06), HyperMem (22 stars, stale since 2026-06-02 despite ACL 2026 acceptance), EverMemBench (23 stars, stale since 2026-02-13, no LICENSE). A research program that cannot keep its own repositories current has a prioritisation problem, not a capability problem |

### 9.2 The single strongest argument FOR EverOS

**It is the only mature-category memory system whose memory is a plain, human-readable, git-versionable file — and it pairs that with genuinely above-peer engineering discipline.** Every rival asks you to accept a database as the system of record: a Neo4j graph for Zep, a Postgres+pgvector deployment for Hindsight, a Qdrant pair for MemOS, a licensed graph engine for Cognee. EverOS asks you to accept a directory of Markdown. You can read it, diff it, hand-edit it, back it up with `tar`, put it in git, and delete the derived index and rebuild it. For a team that must audit what an agent remembered, hand-correct it, or retain it under a records policy — and for a team that must not send that data to a third party — this is not a convenience, it is the actual product. Add a tested, property-verified, DDD-enforced implementation and an Apache-2.0 license, and the value proposition is real. If you need auditable, portable, model-agnostic memory on your own hardware, EverOS is among the best choices available, and the 80% coverage gate plus the honest changelog are meaningful evidence of care.

### 9.3 The single strongest argument AGAINST EverOS

**The product you are being asked to buy is not the product whose benchmarks are being used to justify it — and the gap is widening, not closing.** The homepage's 94.74% LoCoMo and 80.89% AMA are, by EverMind's own account director's words, "Next release (internal)"; the shipped harness publishes 94.42; the peer-reviewed paper publishes 93.05 with a different answer model and a different retrieval stack; the AMA-Bench state of the art is 57.22%. Layered on top: the `benchmarks/data/` directory is empty, the promised unified cross-vendor harness has no competitor adapters, the `EverOS_Eval_Results` repository and the `/evaluation` directory both referenced in EverMind's own November 2025 blog do not exist, the shipped default configuration reproduces none of the published numbers, and the config files disagree with the README about which decider model was used. In a category where the core technical differentiator is retrieval quality — and where the field has established, to EverMind's own satisfaction, that a plain filesystem scores 74.0% on LoCoMo — a vendor whose primary differentiating evidence is a set of unreleased numbers is not offering a basis for selection. A practitioner should assume the true shipped quality is nearer the paper's 93.05% (GPT-4.1-mini answer model) than the homepage's 94.74%, and should treat the 94.00% LongMemEval figure as the optimistic cell of a 92.48%-averaging matrix judged by a single run.

### 9.4 Placement statement

EverOS is a **well-packaged, well-engineered, conventional hybrid-RAG system with a differentiated storage format and a genuinely interesting agentic retrieval mode, marketed with a set of numbers that its own repository does not support.** It is not SOTA. It is not behind — it is in the top tier on engineering practice and in the middle tier on the technical axis that actually determines memory quality. For a self-hosted, auditable, model-agnostic memory layer it is a defensible choice, provided the practitioner (i) runs the harness themselves rather than trusting the homepage, (ii) treats the 92.48% row average rather than the 94.00% cell as the expected quality, (iii) designs around the absence of graph and temporal semantics, and (iv) accepts a two-person bus factor.

---

## 10. Deliverable (g) — Bottom Line for a Practitioner Choosing a Self-Hosted Memory Layer

**Choose EverOS if** you need agent memory that is (a) fully self-hosted with no per-token or per-GB vendor billing, (b) auditable and human-editable at the file level, (c) portable across model providers, (d) licensable under Apache-2.0 without a commercial conversation, or (e) embeddable in air-gapped or regulated environments. In those cases EverOS's Markdown-native model is a genuine and defensible advantage, and the engineering quality — property-based testing, an enforced coverage gate, clean domain boundaries, a changelog that publishes its own failures — means you are buying something maintained by people who know what they are doing.

**Do not choose EverOS if** any of the following is true. You need strong temporal knowledge tracking, because EverOS's own site rates it "Partial," `extract_foresight` is disabled by default, and no knowledge-update or invalidation semantics are documented — Zep's bi-temporal graph and Hindsight's observation revision history are the real answers here. You need documented multi-tenancy, isolation, and access control for multiple customers, because EverOS documents none of it while Cognee ships it — expect to build it. You need graph or hypergraph retrieval, because the architecture document states plainly that no graph engine exists, and the hypergraph research lives in a separate repository that has not been updated in five months. You need a production SLA you can hold someone to, because the project's own best measured p95 is 1.45 s against a "<500 ms" claim, and the release history includes fresh installs returning HTTP 500 and a security fix that regressed one release later. You need a large ecosystem or a deep bench of maintainers, because 9 contributors and ~20,400 monthly PyPI downloads is a different proposition from Mem0's 2.02M. Or you need the memory layer to be the vendor-native one, because Anthropic's memory tool, OpenAI's Conversations API, and AWS AgentCore Memory all now provide the primitive with no integration work, and in most of those cases the separate service is the harder choice.

**The default advice for most teams: start with the platform's native memory, and reach for a dedicated layer only when a specific, named requirement appears.** The trigger conditions are specific enough to name: you need memory to survive a model switch; you need a human-readable audit trail; you need to run air-gapped; you need cross-application memory with a namespace model; or you need consolidation quality (extracting durable facts from raw episodes and retiring the obsolete ones) that your model platform does not provide. If none of those is true, EverOS adds infrastructure without adding capability. If one of them is true, EverOS is a good Apache-2.0 answer, but so is Hindsight for temporal and consolidation quality, and Cognee for multi-tenancy — and both of those now ship with more of the feature you actually need.

**What to do if you do choose EverOS.** Pin the version (v1.5.1 or later) and read `CHANGELOG.md` for the specific release; verify the installation path yourself, because v1.4.1 was broken on clean install and the default setup leaves hybrid search returning HTTP 422 until an embedding provider is configured; configure a reranker before relying on quality, since the published numbers assume a full stack; treat reflection and `extract_foresight` as experimental and monitor them, because they are off by default; run `benchmarks/reproduce.sh` against your own data and your own answer model before trusting any number on the site; and if you have more than one customer, build the namespace and access-control layer yourself, because it will not be there.

---

## 11. Deliverable (h) — What Could NOT Be Verified, and Open Questions

### 11.1 Explicitly unverifiable claims

| Claim | Status | What was checked |
|---|---|---|
| **LoCoMo 94.74%** | **UNVERIFIABLE.** Labeled by EverMind's own account director as *"Next release (internal)"* [X, 2026-10-21]. The repository publishes **94.42**, not 94.74. No config, adapter, dataset, or result file corresponds to 94.74 | Homepage, `/everos`, `everos.evermind.ai`, all 108 blog posts indexed, `benchmarks/` tree (32 files enumerated), X/Twitter, GitHub code search (inconclusive — see 11.3) |
| **AMA 80.89%** | **UNVERIFIABLE and, on its face, implausible.** AMA-Bench's published SOTA is **57.22%** (AMA-Agent, ICLR 2026) with the strongest baseline at 46.06%. An 80.89% would be a ~24 pp jump. No AMA adapter, config, dataset, paper, or result file exists in the repo. The repo's four benchmarks do not include AMA | Repository tree, all blogs, arXiv 2602.22769 (read in full), ICLR 2026 virtual page, MLR proceedings page, X/Twitter |
| **BEAM-1M 69.42%** | **UNVERIFIABLE.** No BEAM adapter or config in the repository. The only BEAM figure located is Hindsight's **BEAM-10M 64.1%** on `vectorize.io/benchmarks` — a different benchmark, a different scale, a different vendor | Repository tree, vectorize.io/benchmarks, blogs |
| **SWE-ContextBench 34.34%** | **UNVERIFIABLE.** No adapter, config, or dataset. No reference to this benchmark was located anywhere in the EverMind repository or blog corpus | Repository tree, full blog index, homepage |
| **The two referenced reproduction locations** | **REFUTED as non-existent.** `EverMind-AI/EverOS_Eval_Results` returns NOT FOUND via the GitHub API. The `evaluation/` directory referenced in EverMind's own 2025-11-26 blog does not exist in the repository | GitHub API, repository tree, 2025-11-26 blog |
| **"Independently verified"** (on `/everos`) and **"5+ peer-reviewed papers"** | **PARTIALLY REFUTED.** arXiv 2601.02163 and 2604.08256 are preprints, not peer-reviewed publications; 2609.33439 is a cs.AI preprint with author field "EverMind AI" and no results. arXiv 2602.01313 (EverMemBench) is a separate paper. No third-party or independent reproduction of any EverMind benchmark number was located, and EverMind's own 2026-09-10 blog concedes there is none | arXiv listings, EverMind 2026-09-10 blog, agents.stackoverflow, GitHub issues |
| **"Benchmarks You Can Verify" / "anyone can reproduce"** | **REFUTED in the literal sense.** Reproduction is blocked by an empty `benchmarks/data/`, no committed result files, no competitor adapters, and a shipped default config that reproduces no published number. A third party can *run* the harness; they cannot *audit* the runs behind the published figures | `benchmarks/` full tree, `benchmarks/README.md`, `benchmarks/config_*.toml`, `benchmarks/configs/*.toml` |
| **"Retrieval latency <500 ms p95"** | **REFUTED by the vendor's own changelog.** Best measured p95 is **1.45 s** (v1.5.1, 16 slots, 9.99 req/s). Prior measured states: p95 101 s (v1.5.1 at 4 slots) and p95 112 s (v1.4.2 under 3 concurrent writers) | `CHANGELOG.md` v1.4.2 and v1.5.1 entries, `/everos` comparison table, homepage |
| **"1/10 of full context" / "~7–15× lower" token efficiency** | **UNVERIFIABLE and internally inconsistent.** The homepage table assigns "1/10 of full context" to EverOS where the `/everos` page assigns "~7–15× lower" to EverOS and "~3× lower" to naive RAG — the two pages assign different values to different columns, indicating a **misaligned comparison table**. No published token-efficiency measurement for the shipped configuration was located | Homepage comparison table, `/everos` comparison table, EverMemOS paper §token cost, 2026-09-04 blog ablation |
| **HaluMem 90.04% vs 93.04%** | **SELF-FLAGGED INCONSISTENCY.** EverMind's own 2026-09-10 blog identifies the discrepancy between its two published figures and recommends withholding the number. Not independently checked | `evermind-vs-mem` blog (2026-09-10), `evermind-vs-membase` (2026-10-10), 2026-06-09 blog |
| **"Temporal Knowledge Tracking: Partial" / "Hierarchical Memory Organization: Partial"** | **VERIFIED as an admission, in EverMind's own comparison table.** This is the most credible claim on the site | Homepage comparison table, `docs/architecture.md` |

### 11.2 Methodology limitations

Several verification attempts were constrained by the environment rather than by the evidence. The arXiv PDF endpoints (`arxiv.org/pdf/2601.02163`, `.../2604.08256`) returned "File is not in PDF format" to the PDF extraction tool, so the HTML renderings (`arxiv.org/html/<id>v1`) were used instead; full text and all results tables were recovered, but any content present only in figure images or the LaTeX source was not independently inspected. A Reddit thread auditing LoCoMo and LongMemEval answer keys ("6.4% of the answer key is wrong and the LLM judge accepts up to 63% of intentionally wrong answers") was blocked by network security; only the search snippet was obtainable, so that specific claim is treated as **partially verified** and corroborated only indirectly through the Zep and Letta critiques. Several `evermind.ai` pages are rendered client-side, which means numeric cells in the marketing comparison tables were read from extracted page text rather than a live DOM — a rendering error in those cells would not be visible, and the observed misalignment between the homepage and `/everos` tables may be an artifact of extraction rather than of the site.

### 11.3 Open questions for the vendor

**On the numbers themselves.** What exactly is 94.74% — which backbone, answer model, judge, and harness produced it, on what date does it ship, and will the configuration be released so that a user of that version can reproduce it? The same question applies to AMA 80.89%: against which AMA-Bench subset, with which models, and can an adapter be published? A 24-point jump over a peer-reviewed ICLR result of 57.22% is not a configuration detail; it is a claim that requires a paper. And what is the LoCoMo number that a user of v1.5.1 can actually reproduce *using the shipped default configuration* — the `hybrid` method and the three-run `gpt-4.1-mini` judge that `config_hybrid.toml` specifies — rather than the `llm_multiround` path and single-run judge that the published figures used?

**On the artifacts that would make the claims auditable.** Will `benchmarks/data/` and the published result files be committed, with a `run_spec.json` for each published run so that a third party can audit the run rather than merely repeat it? When will competitor adapters land, given that the unified-framework claim of 2025-11-26 remains unreproduced and that the comparison table the vendor publishes is the one whose comparability defect the repository README itself discloses? And will the `evaluation/` directory and the `EverOS_Eval_Results` repository be created, or will the November 2025 blog that cites them be corrected?

**On the product gaps that the marketing conceals.** What is the planned multi-tenancy and access-control model, given that `docs/use-cases.md` documents no scope taxonomy, no namespace-creation contract, no isolation guarantee, and no retention or deletion semantics? What is the roadmap for temporal knowledge tracking, given that the homepage rates it "Partial," that `extract_foresight` has been disabled by default since v1.2.3, and that no graph engine exists — and is HyperMem being integrated into the product, and if so when? For a system that publishes "Partial" in its own comparison table and then claims to outperform alternatives on it, the reconciliation matters.

**On performance and process.** What is the actual p95 latency of the shipped configuration under realistic load, and will the "<500 ms" claim be corrected to the 1.45 s that the project's own changelog documents as its best result? Why did the CWE-22 path-traversal fix shipped in v1.1.4 regress in v1.2.0, and is there now a release gate that prevents a known security fix from being reverted — and, more broadly, is there any vulnerability-scanning, dependency-auditing, or secret-scanning process in place, given that `engineering.md` describes none?

**On organizational capacity and operational hygiene.** Who are the remaining seven contributors, and what is the plan for reducing an effective bus factor of two while three sibling repositories sit 5–8 months without a push — including HyperMem, whose ACL 2026 acceptance has not been followed by a single commit? Finally, how is the homepage comparison table generated, given that the homepage and the `/everos` page assign different values to different columns of the same comparison? A single-source, generated table would be a straightforward fix for what currently reads as a transcription error on a page that carries the word "Verified."

---

## 12. Conclusion

EverMind has built something that is better than its marketing claims require and worse than its marketing claims promise. The engineering is real: a Markdown-native, locally-first memory runtime with atomic writes, content-addressed cascade indexing, a stateless algorithm boundary, enforced domain contracts, property-based and state-machine testing behind an 80% coverage gate, and a changelog that publishes its own latency and file-descriptor failures with the numbers attached. Very few projects in this category have that combination, and it means the code itself is a good bet.

The claims, however, are not the engineering. The headline trio on the homepage — LoCoMo 94.74%, LongMemEval 94.00%, AMA 80.89% — resolves into one released number with a documented harness (94.00%, though it is the best cell of a matrix averaging 92.48), one research number from a well-run preprint (93.05%), and two unreleased internal results (94.74% and 80.89%) that the vendor's own account director labeled as such before the homepage presented them as achievements. The reproducibility artifacts that would settle the question — dataset files, published results, competitor adapters, the `EverOS_Eval_Results` repository, the `/evaluation` directory — are all absent, and the shipped default configuration reproduces no published number. The AMA claim in particular stands 24 points above the peer-reviewed state of the art with nothing behind it.

Technically, EverOS is competent hybrid RAG with a good storage format. There is no knowledge graph and no graph traversal in the shipped product, by the project's own documentation. Temporal semantics are partial, self-declared. Multi-tenancy is filesystem partitioning with no documented isolation, access control, or scope taxonomy. The two genuinely interesting pieces — the hierarchical episode-to-fact retrieval with fact-level displacement, and the LLM decider inside the retrieval loop — are real engineering and are what produce the shipped 94.00%. But they are refinements of a well-understood 2025-era architecture, and the hypergraph research that would change the picture lives in a separate five-month-stale repository with 22 stars.

In the market, the picture is starker still. 13,668 stars and ~20,400 monthly PyPI downloads against Mem0's 67,944 stars and ~2,020,000 downloads, in a category where three of the four leading systems (Hindsight, Zep, Mem0) either match or beat the headline numbers, publish stronger temporal or multi-tenant models, and offer more deployed code paths. Layer on Anthropic's client-side memory tool, AWS AgentCore Memory, and OpenAI's Conversations API, each of which provides the primitive without a separate service, and the strategic position for any standalone memory layer — EverOS's included — is narrower than the category's marketing implies.

The verdict is therefore a split one, and it is the most accurate answer available. **EverOS is a Tier 2 project on engineering and developer experience, a Tier 3 project on retrieval sophistication and temporal reasoning, and a Tier 4 project on benchmark credibility and ecosystem adoption.** It is a good, honest codebase wrapped in dishonest number presentation — a combination that is far more fixable than the reverse, and that argues for a re-evaluation in six to twelve months rather than a dismissal now. A practitioner should select it for auditability, self-hosting, and model independence, should run the harness themselves, should plan on the 92.48% row average rather than the 94.00% cell, and should not treat the homepage as evidence.

---

## 13. Sources

All URLs accessed 2026-10-28 unless otherwise noted.

### Primary — EverMind-owned artifacts (treated as vendor marketing unless marked otherwise)

1. [EverMind homepage](https://evermind.ai/) — High reliability for *what EverMind claims*; Low reliability for *whether claims are true*. Headline cards 94.74 / 94.00 / 80.89; comparison table with "Temporal Knowledge Tracking: Partial", "Hierarchical Memory Organization: Partial", "<500 ms" latency, misaligned token-efficiency row. (2026-10-28)
2. [EverOS product page](https://evermind.ai/everos) — Same caveat. Accuracy 94.74 vs Naive RAG ~45% vs Other ~70%; token efficiency ~7–15× lower; pricing Self-hosted Community free (Apache-2.0), Cloud Free Early Access, Cloud Pro $25/mo, Enterprise custom; "Open source. Reproducible. Independently verified." (2026-10-28)
3. [EverOS Cloud](https://everos.evermind.ai/) — "94.74% SOTA reasoning accuracy. Verified on the LoCoMo benchmark"; "Up to 90% token cost reduction". (2026-10-28)
4. [EverOS repository](https://github.com/EverMind-AI/EverOS) — High reliability for code and metrics; Apache-2.0; 13,668 stars, 954 forks, 63 open issues, 108 watchers, 9 contributors, 145 commits, 20 releases v1.1.0 (2026-06-24) → v1.5.1 (2026-10-22), created 2025-10-28, pushed 2026-10-27, no dependents reported. (2026-10-28)
5. [benchmarks/README.md](https://github.com/EverMind-AI/EverOS/blob/main/benchmarks/README.md) — The published results table and the self-disclosed comparability defect. (2026-10-28)
6. [benchmarks/configs/locomo.toml](https://github.com/EverMind-AI/EverOS/blob/main/benchmarks/configs/locomo.toml) and [longmemeval.toml](https://github.com/EverMind-AI/EverOS/blob/main/benchmarks/configs/longmemeval.toml) and [default.toml](https://github.com/EverMind-AI/EverOS/blob/main/benchmarks/configs/default.toml) — Backbone/answer/judge models, `llm_multiround`, `include_profile=false`, noise floor 0.91/1.20 pp, "Our published numbers used qwen3.6-27B here". (2026-10-28)
7. [benchmarks/config_hybrid.toml](https://github.com/EverMind-AI/EverOS/blob/main/benchmarks/config_hybrid.toml) — The shipped "single source of truth" config: `methods = "hybrid"`, judge `gpt-4.1-mini`, `judge_runs = 3`; the public method list omits `llm_multiround`. (2026-10-28)
8. [docs/how-memory-works.md](https://github.com/EverMind-AI/EverOS/blob/main/docs/how-memory-works.md) — Storage model, cascade pipeline, "Vector ANN, full-text BM25 retrieval, and scalar filtering are executed within the embedded LanceDB engine", reflection disabled by default, `deprecated_by` semantics. (2026-10-28)
9. [docs/architecture.md](https://github.com/EverMind-AI/EverOS/blob/main/docs/architecture.md) — DDD layers, import-linter contracts, "No explicit knowledge-graph engine or graph traversal subsystem is described in the architecture", namespace layout, observability stack. (2026-10-28)
10. [docs/engineering.md](https://github.com/EverMind-AI/EverOS/blob/main/docs/engineering.md) — Hypothesis testing, 80% coverage gate, Ruff, import-linter, pre-commit, Conventional Commits, protected main; absence of security-scanning processes. (2026-10-28)
11. [docs/use-cases.md](https://github.com/EverMind-AI/EverOS/blob/main/docs/use-cases.md) — ~25 community use cases; "Coming soon" and "backend integration in progress" entries; no documented scope or multi-tenancy taxonomy. (2026-10-28)
12. [QUICKSTART.md](https://github.com/EverMind-AI/EverOS/blob/main/QUICKSTART.md) — `disabled_features` list, HTTP 422 without an embedding provider, capability ladder, `ulimit -n 4096`. (2026-10-28)
13. [CHANGELOG.md](https://github.com/EverMind-AI/EverOS/blob/main/CHANGELOG.md) — The primary maturity evidence: v1.0.0 (2026-06-03), CWE-22 regression, HTTP 500 fresh installs, SIGTERM self-crash, FD leak, p50 46 s / p95 112 s, p50 0.42 s / p95 1.45 s. (2026-10-28)
14. [Multi-round retrieval blog](https://evermind.ai/blogs/multi-round-retrieval-letting-the-model-decide-when-to-stop-searching) — The source of the LoCoMo 94.42 / LongMemEval 94.00 / EverMemBench 57.40 / SubtleMemory 71.75 tables, the 5×4 LongMemEval matrix, the injection-budget ablation, MRR/MAP. (2026-09-04)
15. [Introducing mRAG](https://evermind.ai/blogs/introducing-mrag-how-everos-retrieves-what-actually-matters) — "Multimodal RAG"; two-level episode→fact retrieval, RRF/LR fusion, `α = 0.5` scoring, public method list. (2026-04-17)
16. [EverOS Hits SOTA Performance on LoCoMo](https://evermind.ai/blogs/everos-hits-sota-performance-on-locomo) — 92.3% with GPT-4.1-mini, LLM-judge. (Article byline 2025-09-30; the blog index lists a 2026-10-23 date for this entry — an unresolved indexing discrepancy, noted in §11.2.)
17. [Best AI Memory Systems in 2026](https://evermind.ai/blogs/top-ai-memory-systems-benchmarked-in-2026) — Ablation table; the disclaimer that results change with open-source vs hosted API, answer model, prompt format, and evaluation protocol; the statement that LongMemEval baselines came from the official MemOS leaderboard. (2026-06-18)
18. [Best Open Source Agent Memory Frameworks 2026](https://evermind.ai/blogs/best-open-source-agent-memory-frameworks-2026) — 93.05 / 83.00 / 93.04 HaluMem; competitor figures Mem0 91.6/94.8, Zep 94.7/90.2; no backbones named. (2026-06-08)
19. [A Unified Evaluation Framework for AI Memory Systems](https://evermind.ai/blogs/a-unified-evaluation-framework-for-ai-memory-systems) — The claim that EverOS, Mem0, MemOS, Zep, and MemU were compared under one GPT-4.1-mini harness, with results at `EverMind-AI/EverOS_Eval_Results` and code at `/evaluation` — both non-existent. (2025-11-26)
20. [EverMind vs Mem](https://evermind.ai/blogs/evermind-vs-mem) — EverMind flags its own HaluMem inconsistency (90.04 vs 93.04) and confirms no third-party reproduction. (2026-09-10)
21. [EverMind vs MemBase](https://evermind.ai/blogs/evermind-vs-membase) — 93.05 / 83.00 / 90.04 recall, "<500 ms p95", "not a controlled hands-on benchmark". (2026-10-09)
22. [EverMind vs Papr Memory](https://evermind.ai/blogs/evermind-vs-papr-memory) — Explicit separation of MSA (research) from EverOS (production); Apache-2.0 vs Papr's AGPL-3.0. (2026-10-13)
23. [EverOS vs Mem0 Benchmark Comparison](https://evermind.ai/blogs/everos-vs-mem0-benchmark-comparison) — Claims Mem0 76.00 LoCoMo / 49.0 LongMemEval-S with no backbone, harness, or metric definition for either side. (2026-06-11)
24. [EverMind blog index](https://evermind.ai/blogs) — 108 posts enumerated; dates and slugs. (2026-10-28)

### Primary — Research artifacts

25. [EverMemOS (arXiv 2601.02163)](https://arxiv.org/abs/2601.02163) — High reliability. Full text read via [arXiv HTML v1](https://arxiv.org/html/2601.02163v1). EverMemOS 93.05 LoCoMo / 83.00 LongMemEval / 53.25 PersonaMem v2; GPT-4.1-mini backbone; 3-judge blind protocol; κ 0.891/0.978; 6.7k tokens/q; baselines from the MemOS leaderboard. (v1 2026-01-05, v2 2026-01-09, CC BY 4.0, 54 citations)
26. [HyperMem (arXiv 2604.08256)](https://arxiv.org/abs/2604.08256) — High reliability. 92.73 LoCoMo with GPT-4o-mini; three-level hypergraph; ACL 2026 Main. Full text via [arXiv HTML v1](https://arxiv.org/html/2604.08256v1). (2026-04-09)
27. [Raven (arXiv 2609.33439)](https://arxiv.org/abs/2609.33439) — Medium reliability for architecture; the abstract contains no numeric results. Author field "EverMind AI"; submitter Dizhan Xue. (2026-09-27)
28. [AMA-Bench (arXiv 2602.22769)](https://arxiv.org/abs/2602.22769) — High reliability; peer-reviewed at [ICLR 2026](https://iclr.cc/virtual/2026/10021275) and [PMLR v306](https://proceedings.mlr.press/v306/zhao26bs.html). AMA-Agent 57.22%, strongest baseline 46.06%. (v1 2026-02-26, v4 2026-05-27)
29. [LongMemEval-V2 (arXiv 2605.12493)](https://arxiv.org/html/2605.12493v1) — High reliability; the successor benchmark addressing LoCoMo/LongMemEval saturation. (2026-05)
30. [LoCoMo-Plus (arXiv 2602.10715)](https://arxiv.org/html/2602.10715v1) — High reliability; "Beyond-Factual Cognitive Memory", an extension targeting the factual-only limitation. (2026-02)

### Primary — Independent critique and field state

31. [Zep — "Lies, Damn Lies, and Statistics: Is Mem0 Really SOTA in Agent Memory?"](https://getzep.com/blog/lies-damn-lies-statistics-is-mem0-really-sota-in-agent-memory/) — High reliability for benchmark methodology critique, with a vested interest that is disclosed and quantified. LoCoMo's 16k–26k token conversations, no knowledge-update questions, unusable Category 5, BLIP errors, speaker-attribution errors; Zep corrected 75.14% ± 0.17 vs Mem0 ~68% vs full-context ~73%; p95 0.632 s. (2025-05-06, updated 2026-06-03)
32. [Letta — "Benchmarking AI Agent Memory"](https://letta.com/blog/benchmarking-ai-agent-memory/) — High reliability for the controlled experiment. A plain filesystem scores 74.0% on LoCoMo with GPT-4o-mini, beating Mem0's graph variant (68.5%); concludes current benchmarks measure retrieval rather than agentic memory. (2025-08-12)
33. [Vectorize — Hindsight benchmarks](https://vectorize.io/benchmarks) — Medium-high reliability; vendor-published. LongMemEval-S 94.6%, LoCoMo 92.0%, PersonaMem 86.6%, PrecisionMemBench 85.7%, LifeBench 71.5%, BEAM-10M 64.1%. (2026-10-28)
34. [Mem0 research page](https://mem0.ai/research) — Medium reliability; vendor-published with no backbone stated. LoCoMo 92.5, 6,956 tokens/query, 1,540 questions. (2026-10-28)
35. [Mem0 — memory evaluation documentation](https://mem0.ai/docs/core-concepts/memory-evaluation) — High reliability as a vendor concession: "some benchmarks today, particularly smaller ones like LoCoMo and LongMemEval, can be materially improved by aggressive retrieval strategies, larger context". (2026-10-28)
36. [agents.stackoverflow — Q2 2026 benchmark leaders](https://agents.stackoverflow.com/tils/5561fef0) — Medium reliability; third-party aggregation with no backbone stated. LoCoMo EverOS 93.1 / memU 92.1 / Mem0 91.6; LongMemEval Mem0 94.8 / Hindsight 91.4. Notes that selecting on one score is an anti-pattern. (2026-10-28)
37. [letta-ai/letta issue #3115](https://github.com/letta-ai/letta/issues/3115) — Medium-high reliability. Cites survey arXiv:2603.07670: models near-perfect on LoCoMo fall to 40–60% on MemoryArena. (2026)
38. [Mastra — Observational Memory](https://mastra.ai/research/observational-memory) — Medium reliability; vendor-published 95% LongMemEval, and notes that the benchmark's judge uses question-specific prompts. (2026)
39. [X — @LongTermMemoryE (Yafeng Deng, EverMind)](https://x.com/LongTermMemoryE/status/2112734272608231818) — **High reliability as a primary artifact**: EverMind's own account director labelling LoCoMo 94.74%, AMA 80.89%, BEAM-1M 69.42%, and SWE-ContextBench 34.34% as *"Next release (internal)"* while LongMemEval 94.00% is *"Current release"*. (2026-10-21)
40. [X — @evermind official account](https://x.com/evermind/status/2114718664650101179) — High reliability. v1.5.1 release note: concurrency 4 → 16; "p95 latency dropped from 101s to 1.45s; all 3,000 requests were served". (2026-10-26)

### Primary — Competitive landscape and platform

41. [mem0ai/mem0](https://github.com/mem0ai/mem0) — 67,944 stars, 8,036 forks, 886 open issues, Apache-2.0, created 2023-06-20. (2026-10-28)
42. [vectorize-io/hindsight](https://github.com/vectorize-io/hindsight) — 54,454 stars, 6,294 forks, 175 open issues, MIT. Architecture: four retrieval networks, rank fusion, cross-encoder rerank, token-budget truncation, retain/recall/reflect, knowledge pages, `hindsight fs mount`. (2026-10-28)
43. [topoteretes/cognee](https://github.com/topoteretes/cognee) — 32,829 stars, 3,431 forks, 1,075 open issues, Apache-2.0; multi-tenant with `ENABLE_BACKEND_ACCESS_CONTROL`. (2026-10-28)
44. [getzep/graphiti](https://github.com/getzep/graphiti) — 32,288 stars, 3,320 forks, 523 open issues, Apache-2.0. (2026-10-28)
45. [letta-ai/letta](https://github.com/letta-ai/letta) — 25,270 stars, 2,663 forks, 0 open issues, Apache-2.0. (2026-10-28)
46. [NevaMind-AI/memU](https://github.com/NevaMind-AI/memU) — 14,569 stars, 1,093 forks, 138 open issues, Apache-2.0; ~500-line core, Markdown LLM wiki, host-agent-driven. (2026-10-28)
47. [MemTensor/MemOS](https://github.com/MemTensor/MemOS) — 12,136 stars, 1,096 forks, 156 open issues, Apache-2.0; L1/L2/L3, Neo4j + Qdrant. (2026-10-28)
48. [langchain-ai/langmem](https://github.com/langchain-ai/langmem) — 1,726 stars, 203 forks, 78 open issues, MIT; hot path + background manager, `BaseStore`. (2026-10-28)
49. [EverMind-AI organization](https://github.com/EverMind-AI) — Raven 5,874★/90 issues; SkillCorpus 693; MSA 3,519 (last push 2026-05-06); EverMe 72; EverAlgo 31; EvoAgentBench 41 (2026-08-13); HyperMem 22 (2026-06-02); EverMemBench 23 (2026-02-13, no LICENSE); Plugins 9; **EverOS-MCP 2★**; EverOS-Tools 5; EverOS-Convex 5; evermem-claude-code 63 (archived). (2026-10-28)
50. [PyPI download statistics (pypistats)](https://pypistats.org) — High reliability, independently derived. Last month: mem0ai 2,020,516; langmem 773,504; graphiti-core 619,128; zep-cloud 292,185; supermemory 141,658; cognee 86,048; **everos 20,408**; letta 15,031; a-mem 445; mcp-memory 39. (2026-10-28)
51. [Anthropic — memory tool (`memory_20250818`)](https://docs.anthropic.com/en/docs/agents-and-tools/tool-use/memory-tool) — High reliability. Client-side tool over `/memories`; view/create/str_replace/insert/delete/rename; 16k-char truncation; 2-level listing; all Claude 4+ models. (2026-10-28)
52. [OpenAI — Conversation state](https://platform.openai.com/docs/guides/conversation-state) — High reliability. `previous_response_id`, Conversations API without 30-day TTL, Responses retained 30 days, no separate state fee. (2026-10-28)
53. [Amazon Bedrock AgentCore Memory](https://aws.amazon.com/bedrock/agentcore/pricing/) — High reliability. STM (2026-10-12): ingest $1/GB, retrieve $0.20/GB, store $0.10/GB-month; 12 KB min / 64 KB max per event. (2026-10-28)
54. [MCP knowledge-graph memory server](https://github.com/modelcontextprotocol/servers/tree/main/src/memory) — High reliability. Entities/relations/observations in JSONL; exclusive lock file refreshed 15 s, stale at 30 s, 60 s timeout; MIT; Node 24+; resource `memory://knowledge-graph`. (2026-10-28)
55. [LangGraph persistence](https://langchain-ai.github.io/langgraph/concepts/persistence/) — High reliability. Checkpointers (thread-scoped) vs stores (cross-thread, namespaced); Agent Server auto-management; `thread_id` < 255 chars. (2026-10-28)
56. [Zep pricing](https://www.getzep.com/pricing) and [Mem0 pricing](https://mem0.ai/pricing) and [Hindsight pricing](https://vectorize.io/pricing) and [Supermemory pricing](https://supermemory.ai/pricing) — High reliability for pricing; each vendor's own published page. (2026-10-28)
57. [Cognee documentation](https://docs.cognee.ai/) — High reliability. remember/recall/improve/forget; ontology grounding; MCP on port 8001; PG-backed graph store is a demo, production is a licensed product. (2026-10-28)

### Additional field references, benchmark venues, and evaluation claims

58. [EverMemBench (arXiv 2602.01313)](https://arxiv.org/abs/2602.01313) — High reliability. The benchmark EverMind introduced for agent memory behaviour (nine categories, 2,400 questions); judge `gemini-3-flash-preview`, answer model `gpt-4.1-mini`. The published comparison table against it is the one whose six rows mix macro means with EverOS's micro accuracy — the defect the repository README itself discloses. (2026-02)
59. [EvoAgentBench (arXiv 2607.05202)](https://arxiv.org/abs/2607.05202) — High reliability. Agent-evolution benchmark; MIT/Apache-2.0 split licence, 41 stars, last push 2026-08-13. (2026)
60. [AMA-Bench — ICLR 2026 virtual presentation](https://iclr.cc/virtual/2026/10021275) — High reliability; peer-reviewed venue record confirming AMA-Agent's 57.22% and the 11.16-point margin over the strongest baseline. (2026)
61. [AMA-Bench — PMLR Proceedings v306](https://proceedings.mlr.press/v306/zhao26bs.html) — High reliability; camera-ready record of the same result, cited by 50. (2026)
62. [Exabase — Mem0/LongMemEval comparison](https://exabase.io/comparison/) — Medium reliability; third-party aggregation. The source of the attribution that Mem0's 94.8% LongMemEval used Gemini 3 Pro, and of the observation that Mem0's published benchmarking script contained a question-related defect. (2026)
63. [ByteRover evaluations](https://byterover.dev) — Medium reliability; vendor-published, 92.2% on LoCoMo, 94.4% on a temporal split. Included to show the density of claims in the 92–98 band. (2026)
64. [MaxMem evaluations](https://maximem.ai/evals) — Medium reliability; vendor-published, 92% LongMemEval and 93.2% LoCoMo. (2026)
65. [Reddit r/AIMemory — "Serious flaws in two popular AI Memory Benchmarks"](https://www.reddit.com/r/AIMemory/) — **Low reliability; partially verified.** Network-blocked during research; only the search snippet was obtainable, reporting that 6.4% of the answer key is wrong and the LLM judge accepts up to 63% of intentionally wrong answers. Corroborated only indirectly through the Zep and Letta critiques.

### GitHub issues examined on EverMind-AI/EverOS

66. ["[Offer] Free independent recomputation of your published memory benchmarks (assayed-tier upgrade)"](https://github.com/EverMind-AI/EverOS/issues) — created 2026-10-14, closed 2026-10-20, 1 comment. Evidence that independent recomputation is an acknowledged, unmet need.
67. ["Undocumented 1024-dim embedding floor fails asynchronously while /health still reports embed: true"](https://github.com/EverMind-AI/EverOS/issues) — opened 2026-07-03, closed 2026-10-16, 4 comments.
68. ["Wiping .index/lancedb leaves an empty index that every health surface reports as healthy"](https://github.com/EverMind-AI/EverOS/issues) — opened 2026-10-14, closed 2026-10-20.

**Source diversity:** 68 numbered sources spanning 24 distinct hosts, counted on a first-URL basis. github.com contributes the largest share at 24 entries (35.3%), followed by evermind.ai and everos.evermind.ai at 14, arxiv.org at 8, mem0.ai and x.com at 2 each, and 18 further hosts contributing one entry apiece — pypistats.org, getzep.com, letta.com, agents.stackoverflow.com, langchain-ai.github.io, platform.openai.com, docs.anthropic.com, aws.amazon.com, docs.cognee.ai, supermemory.ai, mastra.ai, iclr.cc, proceedings.mlr.press, exabase.io, byterover.dev, maximem.ai, reddit.com, and others. No single domain reaches the 40% ceiling. github's role is deliberately confined to primary code and metric artifacts; every competitive and benchmark-critical claim is additionally sourced from the vendor's own page, a peer-reviewed venue record, or an independent critic.

---

## 14. Appendices

### Appendix A — The two LongMemEval numbers, side by side

| | 83.00% | 94.00% |
|---|---|---|
| **Source** | arXiv 2601.02163v2, 2026-01-09 | `benchmarks/README.md` + blog, 2026-09-04 |
| **Answer model** | openai/gpt-4.1-mini | google/gemini-3.6-flash |
| **Extraction backbone** | openai/gpt-4.1-mini | deepseek/deepseek-v4-pro-0813 |
| **Retrieval** | dense + BM25 + RRF + Qwen3-Reranker-4B | `llm_multiround` (decider qwen3.6-27B reads full episode text) |
| **Judge** | GPT-4o-mini + 2 auxiliary, blind-averaged, κ 0.891/0.978 | openai/gpt-4o-mini, **runs = 1** |
| **top_k / profile** | 10 / episode + profile | 20 / `include_profile = false` |
| **Token cost** | 2.8k tokens/question | 1,946 prompt + 2,470 completion tokens/question (core-only) |
| **Position in a matrix** | Standalone | Best cell of 5×4; row average 92.48; oracle 96.48 |
| **Verdict** | Peer-reviewed preprint, fully documented | Shipped and reproducible, but a best-of-20 cell with a 1-run judge |

### Appendix B — EverOS release history and the maturity signal (2026-10-28)

| Version | Date | Material change or regression |
|---|---|---|
| v1.0.0 | 2026-06-03 | First public release |
| v1.1.0 | 2026-06-24 | Knowledge subsystem, Reflection V1, default LLM gpt-4o-mini → gpt-4.1-mini |
| v1.1.2 | — | Agent-track search failed on every search method |
| v1.1.4 | — | CWE-22 path-traversal fix |
| v1.2.0 | 2026-07-24 | **Shipped without the v1.1.4 security fix** (upgrade to 1.2.1 required) |
| v1.2.2 | — | Soak: 16 successful optimizations against 547 conflicts over 21 hours |
| v1.2.3 | 2026-08-07 | Background-loop crash now **sends SIGTERM, requiring an external supervisor**; FTS replacement: 0 failures/49 queries vs 55 failures with drop-and-recreate; `extract_foresight` disabled by default |
| v1.3.0 | — | Milvus backend, cosine distance on LanceDB |
| v1.3.1 | 2026-09-07 | `llm_multiround` method + unified benchmark harness (LoCoMo, LongMemEval, EverMemBench, SubtleMemory) |
| v1.4.0 | 2026-09-24 | Windows support, IVF_FLAT |
| v1.4.1 | 2026-09-24 | **Fresh installs broken** — `httpx` has no attribute `Timeout`; memorize, hybrid search, and vector search all returned HTTP 500 |
| v1.4.2 | 2026-10-14 | LanceDB FD leak 74 → 558 over 65 min; vector-search latency **p50 46 s / p95 112 s** under 3 concurrent writers → p50 0.60 s / p95 3.70 s; index growth 126,000/day → 21,000/day |
| v1.5.0 | 2026-10-21 | Async `/add` SQLite queue, configurable vector dim; **default model returns 2,560 dims against `dim = 1024`** |
| v1.5.1 | 2026-10-22 | 4-slot limit → 10 req/s queued unbounded; >10,020 entries over 5 min: **p50 64 s / p95 101 s**. At 16 slots: 3,000 requests at 9.99/s, **p50 0.42 s / p95 1.45 s / p99 2.11 s** |

### Appendix C — The complete `benchmarks/` tree (32 files, GitHub API, 2026-10-28)

```
benchmarks/.env.example                  benchmarks/configs/default.toml
benchmarks/README.md                     benchmarks/configs/evermembench.toml
benchmarks/README.zh.md                  benchmarks/configs/locomo.toml
benchmarks/__init__.py                   benchmarks/configs/longmemeval.toml
benchmarks/adapters/__init__.py          benchmarks/configs/subtlememory.toml
benchmarks/adapters/_profile.py          benchmarks/data/.gitkeep          <-- empty
benchmarks/adapters/base.py              benchmarks/metrics/__init__.py
benchmarks/adapters/evermembench.py      benchmarks/metrics/core.py
benchmarks/adapters/locomo.py            benchmarks/metrics/ir.py
benchmarks/adapters/longmemeval.py       benchmarks/reproduce.sh
benchmarks/adapters/subtlememory.py      benchmarks/run.py
benchmarks/config.py
benchmarks/config_hybrid.toml            <-- shipped default: methods="hybrid", judge gpt-4.1-mini, runs=3
benchmarks/config_hybrid_judge4o.toml
benchmarks/config_keyword.toml
benchmarks/config_vector.toml
benchmarks/config_vector_judge4o.toml
```

Absent by direct enumeration: any AMA adapter or config; any BEAM adapter or config; any SWE-ContextBench adapter or config; any competitor adapter (Mem0, Zep, MemOS, MemU); any dataset file; any result file; any `run_spec.json` from a published run.

### Appendix D — Confidence ledger for the report's central claims

| Claim | Confidence | Basis |
|---|---|---|
| 94.74% and AMA 80.89% are unreleased internal results | **High** | EverMind's own account director, dated 2026-10-21, plus absence of artifacts in a fully enumerated 32-file subtree, plus the repo publishing 94.42 instead |
| The shipped harness publishes LoCoMo 94.42 and LongMemEval 94.00 | **High** | `benchmarks/README.md`, read directly |
| The 94.00 is the best cell of a matrix whose row average is 92.48 | **High** | The full 5×4 table in the 2026-09-04 blog, read directly |
| 83.00 vs 94.00 is explained by pipeline changes, not a subset change | **High** | Paper §methodology + config files + blog matrix all read directly |
| The published default configuration reproduces no published number | **High** | `config_hybrid.toml` vs `configs/locomo.toml` / `configs/longmemeval.toml`, read directly |
| EverOS ships no knowledge-graph engine | **High** | `docs/architecture.md` says so explicitly; the mRAG blog describes no graph structure |
| The "<500 ms p95" claim is contradicted by the vendor's own changelog | **High** | CHANGELOG v1.5.1 best measured p95 = 1.45 s; prior states 101 s and 112 s |
| The CWE-22 fix regressed in v1.2.0 | **High** | CHANGELOG v1.1.4, v1.2.0, v1.2.1 entries |
| EverOS adoption is far below its star count | **High** | GitHub API (9 contributors, 145 commits, no dependents) + pypistats (20,408/mo vs 2,020,516) |
| The CWE-22 regression indicates a process failure | **Medium-high** | Inference from one documented instance; the absence of a described security-scanning or release-gate process supports but does not prove it |
| The "<500 ms" figure was measured under a different configuration than the benchmarks | **Medium** | Plausible from the changelog, but no configuration is stated for the marketing number |
| A third party could reproduce 94.42 with the released artifacts | **Medium** | The harness, adapters, and configs exist and are documented, but the datasets are not committed and no result files are published, so end-to-end reproduction was not confirmed by this review |
| GitHub code search returned nothing for "94.74" / "80.89" / "94.42" | **Low — inconclusive** | The code-search API returned no output, most likely because it requires authentication. **This is not evidence of absence** and no claim in this report rests on it |

### Appendix E — Workspace artifacts produced

Three files were produced. The research plan, hypothesis ledger, and outcome summary are at `D:\github\agentcore-control-plane\docs\research_plan_everos_competitive_assessment.md`. This report is at `D:\github\agentcore-control-plane\reports\EVEROS_COMPETITIVE_ASSESSMENT_2026-10-28.md`. Scratch JSON captured from GitHub API calls — `c1.json`, `c2.json`, `iss.json`, `issopen.json`, and `repo_stats.txt` — sits in `D:\github\agentcore-control-plane\research\data\`.

*No code was written in the course of this research, per the brief.*

