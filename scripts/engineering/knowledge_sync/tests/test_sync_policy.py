"""Sync worker policy tests that do not touch the live cluster."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from sync_worker import filter_changed_files, parse_major


def test_include_globs_reject_unexpected_paths(tmp_path: Path) -> None:
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
    assert any("node_modules" in item for item in unexpected)


def test_major_parse() -> None:
    assert parse_major("v2.3.1") == "2"
    assert parse_major("1.0.0") == "1"
    assert parse_major("main") is None
