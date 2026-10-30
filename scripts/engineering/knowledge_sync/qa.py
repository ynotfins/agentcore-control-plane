"""Quarantine QA: Tree-sitter for boilerplate, Markdown integrity, secret/binary hold."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

SECRET_PATTERNS = (
    re.compile(r"(?i)-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(api[_-]?key|secret|password|token)\s*[:=]\s*['\"][^'\"]{12,}"),
    re.compile(r"(?i)sk-[A-Za-z0-9]{20,}"),
)
MD_HEADING = re.compile(r"^#{1,6}\s+\S", re.MULTILINE)
MD_LOCAL_LINK = re.compile(r"\[[^\]]+\]\((?!https?://|mailto:|#)([^)]+)\)")
CODE_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".jsx", ".dart", ".kt", ".kts"}
MD_SUFFIXES = {".md", ".mdc", ".txt"}
BINARY_SUFFIXES = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ico",
    ".pdf",
    ".zip",
    ".exe",
    ".dll",
    ".so",
    ".dylib",
    ".pyc",
    ".wasm",
}


@dataclass
class QAFinding:
    path: str
    ok: bool
    reason: str


@dataclass
class QAReport:
    ok: bool
    findings: list[QAFinding] = field(default_factory=list)

    def add(self, path: Path, ok: bool, reason: str) -> None:
        self.findings.append(QAFinding(path=str(path), ok=ok, reason=reason))
        if not ok:
            self.ok = False


def _looks_binary(path: Path) -> bool:
    if path.suffix.lower() in BINARY_SUFFIXES:
        return True
    raw = path.read_bytes()[:2048]
    return b"\x00" in raw


def _secret_hit(text: str) -> str | None:
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            return pattern.pattern
    return None


def _language_object(language: str) -> Any | None:
    try:
        from tree_sitter import Language  # type: ignore
    except Exception:
        return None
    try:
        if language == "python":
            import tree_sitter_python as tsp  # type: ignore

            return Language(tsp.language())
        if language == "typescript":
            import tree_sitter_typescript as tst  # type: ignore

            return Language(tst.language_typescript())
        if language == "tsx":
            import tree_sitter_typescript as tst  # type: ignore

            return Language(tst.language_tsx())
        if language == "dart":
            import tree_sitter_dart as tsd  # type: ignore

            factory = getattr(tsd, "language", None) or getattr(tsd, "language_dart", None)
            return Language(factory()) if factory else None
        if language == "kotlin":
            import tree_sitter_kotlin as tsk  # type: ignore

            factory = getattr(tsk, "language", None) or getattr(tsk, "language_kotlin", None)
            return Language(factory()) if factory else None
    except Exception:
        return None
    return None


def _make_parser(language: str) -> Any | None:
    """Use the ingest-runner helper when present; otherwise bind local grammars."""
    try:
        from scripts.engineering.knowledge_corpus.chunkers import (  # type: ignore
            _make_tree_sitter_parser,
        )

        parser = _make_tree_sitter_parser(language)
        if parser is not None:
            return parser
    except Exception:
        pass
    try:
        from tree_sitter import Parser  # type: ignore
    except Exception:
        return None
    lang_obj = _language_object(language)
    if lang_obj is None:
        return None
    try:
        return Parser(lang_obj)
    except Exception:
        return None


def _parse_code(path: Path, text: str) -> tuple[bool, str]:
    """Fail closed if Tree-sitter cannot parse the file as a valid tree."""
    suffix = path.suffix.lower()
    language = {
        ".py": "python",
        ".ts": "typescript",
        ".js": "typescript",
        ".tsx": "tsx",
        ".jsx": "tsx",
        ".dart": "dart",
        ".kt": "kotlin",
        ".kts": "kotlin",
    }.get(suffix)
    if not language:
        return True, "not_code"
    parser = _make_parser(language)
    if parser is None:
        try:
            from tree_sitter import Parser  # noqa: F401
        except Exception:
            return False, "tree_sitter_unavailable"
        return False, f"no_grammar:{language}"
    try:
        tree = parser.parse(bytes(text, "utf8"))
    except Exception as exc:  # noqa: BLE001
        return False, f"parse_exception:{type(exc).__name__}"
    root = getattr(tree, "root_node", None)
    if root is None:
        return False, "no_root_node"
    if getattr(root, "has_error", False):
        return False, "syntax_error"
    return True, "tree_sitter_ok"


def _markdown_ok(path: Path, text: str) -> tuple[bool, str]:
    if not text.strip():
        return False, "empty_markdown"
    if path.suffix.lower() in {".md", ".mdc"} and not MD_HEADING.search(text):
        return False, "missing_heading"
    parent = path.parent
    for match in MD_LOCAL_LINK.finditer(text):
        target = match.group(1).split("#", 1)[0].strip()
        if not target:
            continue
        dest = (parent / target).resolve()
        try:
            dest.relative_to(parent.resolve())
        except ValueError:
            return False, f"link_escapes_tree:{target}"
        if not dest.exists():
            return False, f"broken_local_link:{target}"
    return True, "markdown_ok"


def qa_file(path: Path, *, root: Path | None = None) -> QAFinding:
    if not path.is_file():
        return QAFinding(str(path), False, "not_a_file")
    if _looks_binary(path):
        return QAFinding(str(path), False, "binary_or_media")
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return QAFinding(str(path), False, "not_utf8")
    secret = _secret_hit(text)
    if secret:
        return QAFinding(str(path), False, "secret_pattern")
    suffix = path.suffix.lower()
    if suffix in CODE_SUFFIXES:
        ok, reason = _parse_code(path, text)
        return QAFinding(str(path), ok, reason)
    if suffix in MD_SUFFIXES:
        ok, reason = _markdown_ok(path, text)
        return QAFinding(str(path), ok, reason)
    return QAFinding(str(path), True, "text_ok")


def qa_paths(paths: list[Path], *, root: Path | None = None) -> QAReport:
    report = QAReport(ok=True)
    for path in paths:
        finding = qa_file(path, root=root)
        report.findings.append(finding)
        if not finding.ok:
            report.ok = False
    return report


def evaluate_breaking_change(
    *,
    enrolled: bool,
    first_ingest: bool,
    major_jump: bool,
    changed_file_count: int,
    max_changed_files: int,
    unexpected_paths: list[str],
    qa_ok: bool,
    auto_promote: bool,
) -> dict[str, Any]:
    """Return a hold/promote decision. Last-good wins on any hold reason."""
    reasons: list[str] = []
    if not qa_ok:
        reasons.append("qa_failed")
    if not enrolled or first_ingest:
        reasons.append("first_or_unenrolled_remote")
    if major_jump:
        reasons.append("major_version_jump")
    if changed_file_count > max_changed_files:
        reasons.append("changed_file_bound")
    if unexpected_paths:
        reasons.append("unexpected_path")
    if not auto_promote and reasons:
        pass
    if not auto_promote and not reasons:
        reasons.append("auto_promote_disabled")
    action = "promote" if not reasons else "hold"
    return {
        "action": action,
        "reasons": reasons,
        "changed_file_count": changed_file_count,
        "unexpected_paths": unexpected_paths,
    }
