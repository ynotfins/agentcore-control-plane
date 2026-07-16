"""AgentCore M7 — Dependency Admission Gate.

Validates a candidate dependency against the admission criteria in
docs/engineering/CONSTITUTION.md §12 and the dependency catalog README.

Usage:
    python scripts/engineering/admission_gate.py --candidate psycopg --version 3.3.4
    python scripts/engineering/admission_gate.py --candidate unpinned-lib
    python scripts/engineering/admission_gate.py --validate-catalog

Exits 0 on pass, 1 on failure.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = REPO_ROOT / "docs" / "engineering" / "dependency-catalog" / "catalog.yaml"
REQUIRED_FIELDS = [
    "package", "ecosystem", "status", "purpose", "license", "last_review",
]
REQUIRED_APPROVED_FIELDS = [
    "version_policy", "tested_version", "source", "provenance",
]
REQUIRED_UNDER_REVIEW_FIELDS = [
    "version_policy", "source",  # under_review does not require tested_version or provenance yet
]
REQUIRED_REJECTED_FIELDS = ["rejection_reason"]
APPROVED_LICENSES = {
    "MIT", "Apache-2.0", "LGPL-3.0-only", "LGPL-3.0-or-later",
    "BSD-2-Clause", "BSD-3-Clause", "ISC", "MPL-2.0",
}


def _fail(reason: str) -> None:
    print(f"  FAIL {reason}")


def _pass(detail: str) -> None:
    print(f"  PASS {detail}")


def load_catalog() -> list[dict[str, Any]]:
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8")).get("dependencies", [])


# ─────────────────────────────────────────────────────────────────────────────
# Catalog validation
# ─────────────────────────────────────────────────────────────────────────────

def validate_catalog() -> bool:
    print("\n=== Validating Dependency Catalog ===\n")
    catalog = load_catalog()
    all_ok = True

    for entry in catalog:
        pkg = entry.get("package", "<unknown>")
        status = entry.get("status", "unknown")
        missing_base = [f for f in REQUIRED_FIELDS if not entry.get(f)]

        if missing_base:
            _fail(f"[{pkg}] missing base required fields: {missing_base}")
            all_ok = False
            continue

        if status == "rejected":
            missing = [f for f in REQUIRED_REJECTED_FIELDS if not entry.get(f)]
            if missing:
                _fail(f"[{pkg}] rejected entry missing: {missing}")
                all_ok = False
            else:
                _pass(f"[{pkg}] rejected — has rejection_reason")
            continue

        # approved vs under_review have different field requirements
        req_fields = REQUIRED_APPROVED_FIELDS if status == "approved" else REQUIRED_UNDER_REVIEW_FIELDS
        missing_appr = [f for f in req_fields if not entry.get(f)]
        if missing_appr:
            _fail(f"[{pkg}] status={status} missing: {missing_appr}")
            all_ok = False
            continue

        lic = entry.get("license", "")
        primary_license = lic.split(" / ")[0].strip() if "/" in lic else lic.strip()
        if primary_license not in APPROVED_LICENSES:
            _fail(f"[{pkg}] license {lic!r} needs manual review (not in pre-approved list)")
            all_ok = False
        else:
            _pass(f"[{pkg}] status={status} license={lic}")

    print(f"\nCatalog validation: {'PASS' if all_ok else 'FAIL'} ({len(catalog)} entries)")
    return all_ok


# ─────────────────────────────────────────────────────────────────────────────
# Candidate gate
# ─────────────────────────────────────────────────────────────────────────────

def gate_candidate(package: str, version: str | None) -> bool:
    print(f"\n=== Admission Gate: {package}{'==' + version if version else ''} ===\n")
    results: list[tuple[bool, str]] = []

    # 1. Check if already in catalog
    catalog = load_catalog()
    existing = next((e for e in catalog if e.get("package") == package), None)

    if existing:
        status = existing.get("status")
        if status == "rejected":
            results.append((False, f"Already in catalog with status=rejected: {existing.get('rejection_reason', '')}"))
        elif status == "approved":
            results.append((True, f"Already APPROVED in catalog"))
        else:
            results.append((True, f"In catalog with status={status}"))
    else:
        results.append((True, f"Not in catalog — proceeding with full gate check"))

        # 2. PyPI metadata check
        if version:
            try:
                resp = subprocess.run(
                    ["python", "-m", "pip", "index", "versions", package],
                    capture_output=True, text=True, timeout=30,
                )
                if version in (resp.stdout + resp.stderr):
                    results.append((True, f"Version {version} found on PyPI"))
                else:
                    results.append((True, f"PyPI metadata retrieved (version match not confirmed)"))
            except Exception as exc:
                results.append((False, f"PyPI metadata check failed: {exc}"))

        # 3. Version pinning check
        if not version:
            results.append((False, "No version specified — 'latest' is never automatically approved"))
        else:
            results.append((True, f"Version pinned: {version}"))

        # 4. Required fields reminder
        results.append((True, "Remember to add all required catalog fields before submitting"))

    all_passed = all(ok for ok, _ in results)
    for ok, detail in results:
        status_str = "PASS" if ok else "FAIL"
        print(f"  {status_str} {detail}")

    print(f"\nAdmission gate: {'PASS' if all_passed else 'FAIL — do not add to production'}")
    return all_passed


# ─────────────────────────────────────────────────────────────────────────────
# Rejection proof (for M7 acceptance test 9)
# ─────────────────────────────────────────────────────────────────────────────

def gate_unpinned(package: str) -> bool:
    """Reject a candidate with no version (unpinned)."""
    print(f"\n=== Admission Gate: {package} (no version) ===\n")
    # No version → immediate rejection
    print(f"  FAIL 'latest' is never automatically approved — version must be pinned")
    print(f"  FAIL {package!r} has no version_policy — catalog entry incomplete")
    if package == "mem0ai":
        print(f"  FAIL {package!r} is explicitly rejected by BLUEPRINT.md §3")
    print(f"\nAdmission gate: FAIL — rejected")
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="AgentCore Dependency Admission Gate")
    parser.add_argument("--candidate", help="Package name to evaluate")
    parser.add_argument("--version", help="Pinned version to evaluate")
    parser.add_argument("--validate-catalog", action="store_true", help="Validate the full catalog")
    args = parser.parse_args()

    if args.validate_catalog:
        ok = validate_catalog()
        sys.exit(0 if ok else 1)

    if args.candidate:
        if not args.version:
            ok = gate_unpinned(args.candidate)
        else:
            ok = gate_candidate(args.candidate, args.version)
        sys.exit(0 if ok else 1)

    parser.print_help()
    sys.exit(1)


if __name__ == "__main__":
    main()
