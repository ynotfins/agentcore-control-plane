# Research Plan: EverMind / EverOS Competitive Assessment vs. State-of-the-Art Agent Memory

**Task type:** Verification-Focused Task (specific vendor claims to confirm/refute) + Search-Focused landscape mapping
**Date:** 2026-10-28
**Author:** Matrix Agent
**Constraint:** Web research only. No code writing. Every number gets URL + observation date.

## Working hypothesis (to test)
H1: The headline trio (LoCoMo 94.74%, LongMemEval 94.00%, AMA 80.89%) is reproducible from public artifacts.
H2: The 94.00% vs 83.00% LongMemEval discrepancy is a real internal inconsistency (cherry-picking) rather than a pipeline difference.
H3: EverOS ships a graph/hypergraph retrieval engine that differentiates it from plain hybrid-RAG systems.
H4: EverOS's GitHub popularity (stars) reflects real production adoption.
H5: EverMind's benchmark claims are methodologically comparable to those of Mem0, Zep, Hindsight, etc.

## Preliminary signals (2026-10-28)
- Homepage cards and `/everos` page carry 94.74 / 94.00 / 80.89 with no backbone model, harness, or protocol disclosure.
- `benchmarks/README.md` in the repo publishes a *different* LoCoMo number (94.42) and an EverMemBench number (66.67).
- `benchmarks/configs/locomo.toml` contains an inline comment contradicting the README's decider model.
- `benchmarks/data/` holds only `.gitkeep`; `EverMind-AI/EverOS_Eval_Results` and `docs/../evaluation/` do not exist.
- `docs/architecture.md` states plainly that no knowledge-graph engine or graph traversal subsystem is described.
- GitHub code search for the headline numbers is inconclusive (likely auth-gated) -> record as "could not verify."

## Steps
- [x] 1.1 Read the 4 named EverMind blogs + homepage + /everos; catalogue every number with date
- [x] 1.2 Read `benchmarks/README.md`, `benchmarks/configs/*.toml`, `benchmarks/adapters/*`, `benchmarks/data/`, `reproduce.sh`
- [x] 1.3 Resolve arXiv 2601.02163 (EverMemOS), 2604.08256 (HyperMem), 2609.33439 (Raven) - all three resolve
- [x] 1.4 Read EverMemBench + EvoAgentBench + HyperMem + EverMemOS repos
- [x] 1.5 Trace the 94.74 / 80.89 / BEAM-1M / SWE-ContextBench numbers to their announcement source
- [x] 2.1 Map competitors: Mem0, Zep/Graphiti, LangMem, Letta, Hindsight, memU, Supermemory, Cognee, MemOS, OpenMemory, A-Mem, plus 2025-26 entrants
- [x] 2.2 Native vendor memory: OpenAI, Anthropic, Google, AWS AgentCore, MCP, LangGraph
- [x] 3.1 Read `docs/how-memory-works.md`, `docs/architecture.md`, `docs/engineering.md`, `docs/use-cases.md`, `QUICKSTART.md`, `CHANGELOG.md`
- [x] 3.2 GitHub signals: stars, forks, issues, contributors, commits, release cadence, issue responsiveness
- [x] 3.3 PyPI download stats; dependency/dependent counts
- [x] 3.4 Third-party benchmark criticism: Zep, Letta, agents.stackoverflow, vectorize.io, mem0.ai, arXiv surveys
- [x] 4.1 Cross-check >= 3 independent sources per critical fact; assign confidence
- [x] 4.2 Write final report with deliverables (a) through (h)
- [x] 5.1 Final review: list-density audit, source diversity (>=5 sources, >=3 domains), all claims carry URL + date

## Verification standard
Critical fact = 3 independent credible sources where possible. Primary preferred (official site / GitHub / paper). Contradictions recorded explicitly, never silently resolved. EverMind-authored content is treated as **vendor marketing** and labelled as such every time it is the sole source. Vendor benchmark numbers are always reported with the backbone model stated, or explicitly marked "backbone not stated."

## Outcome summary
- H1 **REFUTED.** 94.74 / AMA 80.89 are labelled "Next release (internal)" by EverMind's own account director (X, 2026-10-21). No adapters, configs, or results exist for AMA, BEAM-1M, or SWE-ContextBench in the repo.
- H2 **REFUTED (benign explanation).** 83.00 vs 94.00 is explained by answer model, extraction backbone, retrieval method, and judge protocol changes - but the 94.00 is the best single cell of a 5x4 matrix whose row average is 92.48, and the homepage omits the context.
- H3 **REFUTED.** No graph/hypergraph engine in the shipped product. mRAG = "Multimodal RAG" hierarchical episode->fact search. Their own HyperMem hypergraph paper is a separate, 5-month-stale research repo.
- H4 **REFUTED.** 13,668 stars but 9 contributors, 145 commits, ~20.4k PyPI downloads/month vs Mem0's ~2.02M.
- H5 **REFUTED.** Cross-vendor numbers come from different harnesses, judges, and answer models; EverMind's own Mem0 comparison uses baselines (76.0 / 49.0) that contradict Mem0's own published numbers (91.6 / 94.8).
