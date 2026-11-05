"""Open Design enrollment: exact D:\\open-design only; no AppData, install dir, or PG18."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENROLLMENT_PATH = ROOT / "contracts" / "agentcore-project-enrollment.json"

FORBIDDEN_SUBSTRINGS = (
    r"AppData\Roaming\Open Design",
    r"AppData\Local\Programs\Open Design",
    r"F:\PostgreSQL18",
    r"H:\SwarmData",
)


def load_enrollment() -> dict:
    return json.loads(ENROLLMENT_PATH.read_text(encoding="utf-8"))


def test_open_design_is_exact_d_open_design_only() -> None:
    enrollment = load_enrollment()
    project = next(item for item in enrollment["projects"] if item["project_key"] == "open-design")
    assert project["name"] == "Open Design"
    assert project["paths"] == [r"D:\open-design"]
    assert not project.get("path_prefixes")


def test_open_design_does_not_enroll_product_or_database_roots() -> None:
    dumped = ENROLLMENT_PATH.read_text(encoding="utf-8")
    for forbidden in FORBIDDEN_SUBSTRINGS:
        assert forbidden not in dumped


def test_open_design_is_not_a_duplicate_key() -> None:
    enrollment = load_enrollment()
    keys = [item["project_key"] for item in enrollment["projects"]]
    assert keys.count("open-design") == 1
