#!/usr/bin/env python3
"""Silent Paperclip budget guard: clear zero-cost unpriced usage, then resume.

Run by the agent-dispatch watchdog every cycle. Exits 0 with one JSON line.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from agent_dispatch import paperclip  # noqa: E402


def main() -> int:
    try:
        print(json.dumps(paperclip.clear_zero_cost_unpriced()))
    except paperclip.PaperclipError as exc:
        print(json.dumps({"error": str(exc)}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
