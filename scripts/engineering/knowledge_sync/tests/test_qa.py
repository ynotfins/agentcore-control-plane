"""QA unit tests for Markdown, secrets, and hold policy."""

from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from qa import evaluate_breaking_change, qa_file, qa_paths


def test_markdown_requires_heading_and_existing_local_link(tmp_path: Path) -> None:
    target = tmp_path / "other.md"
    target.write_text("# Other\n", encoding="utf-8")
    good = tmp_path / "guide.md"
    good.write_text("# Guide\nSee [other](other.md)\n", encoding="utf-8")
    assert qa_file(good).ok
    broken = tmp_path / "broken.md"
    broken.write_text("# Broken\nSee [missing](nope.md)\n", encoding="utf-8")
    finding = qa_file(broken)
    assert not finding.ok
    assert "broken_local_link" in finding.reason


def test_secret_and_binary_fail_closed(tmp_path: Path) -> None:
    secret = tmp_path / "leak.md"
    secret.write_text("# Leak\napi_key = 'sk-abcdefghijklmnopqrstuvwxyz'\n", encoding="utf-8")
    assert qa_file(secret).ok is False
    binary = tmp_path / "blob.exe"
    binary.write_bytes(b"MZ\x00\x00")
    assert qa_file(binary).ok is False


def test_valid_python_without_tree_sitter_holds_closed(tmp_path: Path) -> None:
    code = tmp_path / "app.py"
    code.write_text("def greet():\n    return 'ok'\n", encoding="utf-8")
    finding = qa_file(code)
    # Pass if Tree-sitter is installed; otherwise fail closed.
    if finding.reason.startswith("tree_sitter") or finding.reason.startswith("no_grammar") or finding.reason.endswith("unavailable"):
        assert finding.ok is False or finding.reason == "tree_sitter_ok"
    if finding.reason == "tree_sitter_ok":
        assert finding.ok


def test_breaking_change_policy_holds_first_remote() -> None:
    decision = evaluate_breaking_change(
        enrolled=False,
        first_ingest=True,
        major_jump=False,
        changed_file_count=2,
        max_changed_files=50,
        unexpected_paths=[],
        qa_ok=True,
        auto_promote=True,
    )
    assert decision["action"] == "hold"
    assert "first_or_unenrolled_remote" in decision["reasons"]


def test_auto_promote_only_when_all_gates_pass() -> None:
    decision = evaluate_breaking_change(
        enrolled=True,
        first_ingest=False,
        major_jump=False,
        changed_file_count=3,
        max_changed_files=50,
        unexpected_paths=[],
        qa_ok=True,
        auto_promote=True,
    )
    assert decision["action"] == "promote"
    report = qa_paths([])
    assert report.ok


def test_enrolled_first_ingest_can_promote() -> None:
    decision = evaluate_breaking_change(
        enrolled=True,
        first_ingest=True,
        major_jump=False,
        changed_file_count=3,
        max_changed_files=50,
        unexpected_paths=[],
        qa_ok=True,
        auto_promote=True,
    )
    assert decision["action"] == "promote"


def test_valid_dart_parses_when_grammar_available(tmp_path: Path) -> None:
    code = tmp_path / "main.dart"
    code.write_text("void main() { print('ok'); }\n", encoding="utf-8")
    finding = qa_file(code)
    assert finding.reason in {"tree_sitter_ok", "no_grammar:dart", "tree_sitter_unavailable"}
    if finding.reason == "tree_sitter_ok":
        assert finding.ok
