"""Inspect memory.memoryConfig shape and fix agent model + memory schema safely."""
from __future__ import annotations

import json
import os
import shutil
import sqlite3
import time
from pathlib import Path

from level import Level  # may not exist; use node instead via subprocess

print("use node path")
