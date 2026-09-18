# Arabold Eager Token Measurement (2026-09-16)

- Bifrost health: `ok` (HTTP 200)
- Eager tools/list total: **29**
- Arabold eager tools: **10** (`arabold_docs-cancel_job, arabold_docs-fetch_url, arabold_docs-find_version, arabold_docs-get_job_info, arabold_docs-list_jobs, arabold_docs-list_libraries, arabold_docs-refresh_version, arabold_docs-remove_docs, arabold_docs-scrape_docs, arabold_docs-search_docs`)
- Arabold compact o200k BEFORE: **1009** (tiktoken)
- AFTER Code Mode (counterfactual arabold eager=0): **1** (save 1008)
- AFTER bounded subset (5 tools): **639** (save 370)
- Recommendation: **keep_full_eager**

## Rationale

- arabold compact o200k=1009 is modest (13.9% of eager list); docs-first hot path benefits from direct tool schemas without Code Mode discovery latency.
- counterfactual savings rejected: code_mode~1008, bounded_subset~370 o200k — not worth docs-first friction or dropping admin tools from tools_to_execute.

Evidence JSON: `D:/github/agentcore-control-plane/audits/bifrost/ARABOLD_EAGER_TOKEN_MEASUREMENT_2026-09-16.json`

No live Bifrost recycle. No registry mutation this pass.
