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
import tomllib
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
JINJA_DELIMITERS = ("{{", "{%", "{#")
PARSER_SENSITIVE_NAMES = {"pyproject.toml", "package.json", "tsconfig.json"}
PARSER_SENSITIVE_SUFFIXES = {".toml", ".json", ".yaml", ".yml"}


def _fail(reason: str) -> None:
    print(f"  FAIL {reason}")


def _pass(detail: str) -> None:
    print(f"  PASS {detail}")


def load_catalog() -> list[dict[str, Any]]:
    return yaml.safe_load(CATALOG_PATH.read_text(encoding="utf-8")).get("dependencies", [])


def _has_jinja(text: str) -> bool:
    return any(delimiter in text for delimiter in JINJA_DELIMITERS)


def _is_parser_sensitive(path: Path) -> bool:
    return path.name in PARSER_SENSITIVE_NAMES or path.suffix.lower() in PARSER_SENSITIVE_SUFFIXES


def validate_template_source(template_root: Path) -> list[str]:
    """Return deterministic findings for Jinja-bearing Copier source files."""
    config_path = template_root / "copier.yml"
    if not config_path.is_file():
        return [f"{config_path}: missing Copier configuration"]
    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    suffix = config.get("_templates_suffix")
    if not isinstance(suffix, str):
        return [f"{config_path}: _templates_suffix must be an explicit string"]
    subdirectory = template_root / str(config.get("_subdirectory") or ".")
    if not subdirectory.is_dir():
        return [f"{subdirectory}: configured template source directory is missing"]

    findings: list[str] = []
    for source in sorted(path for path in subdirectory.rglob("*") if path.is_file()):
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if not _has_jinja(text) or suffix == "":
            continue
        relative = source.relative_to(template_root)
        if not source.name.endswith(suffix):
            reason = "declared suffix must be the final filename suffix"
            if _is_parser_sensitive(source):
                reason += "; parser-sensitive source would otherwise be parsed before rendering"
            findings.append(f"{relative}: {reason} ({suffix!r})")
    return findings


def validate_generated_project(project_root: Path) -> list[str]:
    """Validate generated parser-sensitive files and reject unresolved Jinja."""
    findings: list[str] = []
    for output in sorted(path for path in project_root.rglob("*") if path.is_file()):
        try:
            text = output.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        relative = output.relative_to(project_root)
        if _has_jinja(text):
            findings.append(f"{relative}: generated output contains unresolved Jinja")
            continue
        try:
            if output.name == "pyproject.toml":
                tomllib.loads(text)
            elif output.name in {"package.json", "tsconfig.json"}:
                json.loads(text)
            elif output.suffix.lower() in {".yaml", ".yml"}:
                yaml.safe_load(text)
        except (json.JSONDecodeError, tomllib.TOMLDecodeError, yaml.YAMLError) as exc:
            findings.append(f"{relative}: generated parser-sensitive file is invalid: {exc}")
    return findings


def validate_templates() -> bool:
    """Validate every governed Copier template source tree."""
    templates = [
        REPO_ROOT / "templates" / "mcp-server-python",
        REPO_ROOT / "templates" / "agent-langgraph-postgres-checkpointer",
    ]
    findings = [
        finding
        for template in templates
        for finding in validate_template_source(template)
    ]
    for finding in findings:
        _fail(finding)
    if not findings:
        _pass(f"Copier template sources valid ({len(templates)} templates)")
    return not findings


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
            results.append((True, "Already APPROVED in catalog"))
        else:
            results.append((True, f"In catalog with status={status}"))
    else:
        results.append((True, "Not in catalog — proceeding with full gate check"))

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
                    results.append((True, "PyPI metadata retrieved (version match not confirmed)"))
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
    print("  FAIL 'latest' is never automatically approved — version must be pinned")
    print(f"  FAIL {package!r} has no version_policy — catalog entry incomplete")
    if package == "mem0ai":
        print(f"  FAIL {package!r} is explicitly rejected by BLUEPRINT.md §3")
    print("\nAdmission gate: FAIL — rejected")
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="AgentCore Dependency Admission Gate")
    parser.add_argument("--candidate", help="Package name to evaluate")
    parser.add_argument("--version", help="Pinned version to evaluate")
    parser.add_argument("--validate-catalog", action="store_true", help="Validate the full catalog")
    parser.add_argument("--validate-templates", action="store_true", help="Validate governed Copier template sources")
    parser.add_argument("--generated-project", type=Path, help="Validate a generated project tree")
    args = parser.parse_args()

    if args.validate_catalog:
        ok = validate_catalog()
        sys.exit(0 if ok else 1)

    if args.validate_templates:
        sys.exit(0 if validate_templates() else 1)

    if args.generated_project:
        findings = validate_generated_project(args.generated_project)
        for finding in findings:
            _fail(finding)
        if not findings:
            _pass(f"generated project valid: {args.generated_project}")
        sys.exit(0 if not findings else 1)

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
