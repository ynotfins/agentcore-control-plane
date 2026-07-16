# Dependency Catalog

**Authority:** `docs/engineering/CONSTITUTION.md` §13.  
**File:** `catalog.yaml` — machine-readable YAML.

## How to Use

1. **Before adding any dependency:** check `catalog.yaml` for status.
   - `approved` → use the pinned `tested_version` or `version_policy` range.
   - `under_review` → submit an evidence-backed proposal; do not use in production.
   - `rejected` → do not use. The rejection reason is in the catalog entry.

2. **Adding a new dependency:**
   - Run the admission gate: `python scripts/engineering/admission_gate.py --candidate <name>`
   - If it passes, submit a PR adding the entry to `catalog.yaml` with `status: under_review`.
   - Operator promotes to `approved` after evidence review.

3. **Updating a dependency:**
   - Run the admission gate against the new version.
   - Update `tested_version` and `last_review` in the catalog entry.
   - Note any API changes in `security_notes` or `approval_reason`.

## Admission Gate Checks

The gate at `scripts/engineering/admission_gate.py` verifies:

1. Official or clearly attributable source
2. Current maintenance evaluation (last release < 12 months)
3. Pinned and reproducible version
4. Clean PyPI metadata (no yanked versions at proposed version)
5. License compatibility (MIT/Apache-2.0/LGPL preferred; GPL requires review)
6. No known CVEs at the pinned version
7. Required catalog fields all present

## Catalog Entry Required Fields

```yaml
- package: <name>
  ecosystem: python | node | powershell | system
  status: approved | under_review | rejected
  purpose: <one line>
  version_policy: <semver range or pinned version>
  tested_version: <exact version tested>
  source: <PyPI or registry URL>
  repository: <GitHub or official URL>
  documentation: <official docs URL>
  license: <SPDX identifier>
  provenance: <who publishes, what license implies>
  security_notes: <CVE check, storage concerns>
  alternatives_considered: <what else was evaluated>
  approval_reason: <why this was chosen>   # for approved/under_review
  rejection_reason: <why rejected>          # for rejected
  last_review: <YYYY-MM-DD>
```
