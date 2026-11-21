from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest


LAUNCHER = Path(__file__).with_name("claude-context-mcp-launch.cmd")
USER_VALUES = {
    "OPENAI_API_KEY": "stub-openai-key",
    "MILVUS_TOKEN": "stub-milvus-token",
    "MILVUS_ADDRESS": "http://stub-milvus.invalid:19530",
    "OPENAI_BASE_URL": "https://stub-openai.invalid/v1",
    "EMBEDDING_PROVIDER": "stub-provider",
    "EMBEDDING_MODEL": "stub-model",
}


def _write(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8", newline="\r\n")


def _build_sandbox(tmp_path: Path, *, installed: bool) -> tuple[Path, Path]:
    launcher = tmp_path / LAUNCHER.name
    shutil.copyfile(LAUNCHER, launcher)

    emitter = tmp_path / "emit_user_variable.py"
    emitter.write_text(
        "import sys\n"
        f"values = {USER_VALUES!r}\n"
        "request = ' '.join(sys.argv[1:])\n"
        "for name, value in values.items():\n"
        "    if name in request:\n"
        "        print(value)\n"
        "        break\n",
        encoding="utf-8",
    )
    _write(
        tmp_path / "powershell.cmd",
        f'@echo off\n"{sys.executable}" "{emitter}" %*\nexit /b %ERRORLEVEL%\n',
    )

    capture = tmp_path / "capture.txt"
    child_lines = [
        "@echo off",
        "> \"%TEST_CAPTURE%\" (",
        *[
            f'  if "%{name}%"=="{value}" (echo {name}=expected) else (echo {name}=unexpected)'
            for name, value in USER_VALUES.items()
        ],
        ")",
        "exit /b %STUB_EXIT_CODE%",
        "",
    ]
    child = "\n".join(child_lines)
    if installed:
        _write(tmp_path / "claude-context-mcp.cmd", child)
    else:
        _write(
            tmp_path / "npx.cmd",
            child.replace(
                "> \"%TEST_CAPTURE%\" (",
                "> \"%TEST_CAPTURE%\" (\necho ARGS=%*",
            ),
        )
    return launcher, capture


def _run(launcher: Path, capture: Path, exit_code: int) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    for name in USER_VALUES:
        env.pop(name, None)
    env["PATH"] = os.pathsep.join(
        [str(launcher.parent), str(Path(os.environ["SystemRoot"]) / "System32")]
    )
    env["PATHEXT"] = ".COM;.EXE;.BAT;.CMD"
    env["TEST_CAPTURE"] = str(capture)
    env["STUB_EXIT_CODE"] = str(exit_code)
    return subprocess.run(
        [os.environ.get("ComSpec", "cmd.exe"), "/d", "/c", str(launcher)],
        cwd=launcher.parent,
        env=env,
        text=True,
        capture_output=True,
        check=False,
        timeout=15,
    )


def _assert_imports(capture: Path) -> str:
    text = capture.read_text(encoding="utf-8")
    for name in USER_VALUES:
        assert f"{name}=expected" in text
    assert "stub-openai-key" not in text
    assert "stub-milvus-token" not in text
    return text


@pytest.mark.skipif(os.name != "nt", reason="Windows batch launcher test")
def test_installed_cmd_receives_user_variables_and_propagates_exit_code(tmp_path: Path) -> None:
    launcher, capture = _build_sandbox(tmp_path, installed=True)
    result = _run(launcher, capture, exit_code=37)

    assert result.returncode == 37, result.stderr
    _assert_imports(capture)


@pytest.mark.skipif(os.name != "nt", reason="Windows batch launcher test")
def test_pinned_npx_fallback_receives_user_variables_and_propagates_exit_code(tmp_path: Path) -> None:
    launcher, capture = _build_sandbox(tmp_path, installed=False)
    result = _run(launcher, capture, exit_code=41)

    assert result.returncode == 41, result.stderr
    text = _assert_imports(capture)
    assert "ARGS=--yes @zilliz/claude-context-mcp@0.1.15" in text
