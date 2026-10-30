"""Sync worker policy tests that do not touch the live cluster."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sync_worker import filter_changed_files, parse_major, source_recency


def test_include_globs_skip_unmatched_and_flag_denied(tmp_path: Path) -> None:
    src = tmp_path / "src"
    allowed = src / "src" / "app.py"
    extra = src / "node_modules" / "pkg" / "index.js"
    allowed.parent.mkdir(parents=True)
    extra.parent.mkdir(parents=True)
    allowed.write_text("ok\n", encoding="utf-8")
    extra.write_text("nope\n", encoding="utf-8")
    kept, unexpected = filter_changed_files(
        [allowed, extra],
        ["src/*.py", "src/**/*.py"],
        src,
    )
    assert kept == [allowed]
    assert extra not in kept
    denied, unexpected_denied = filter_changed_files(
        [extra],
        ["**/*.js"],
        src,
    )
    assert denied == []
    assert any("node_modules" in item for item in unexpected_denied)


def test_major_parse() -> None:
    assert parse_major("v2.3.1") == "2"
    assert parse_major("1.0.0") == "1"
    assert parse_major("main") is None


def test_source_recency_uses_commit_date_when_no_tags(tmp_path: Path) -> None:
    recency = source_recency("https://example.invalid/repo.git", tmp_path, "abc123def456")
    assert recency["source_commit_sha"] == "abc123def456"
    assert recency["is_latest"] is True
    assert recency["version"]
