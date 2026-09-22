"""Runs the board's pure-JS unit tests under node (skipped where node is absent)."""

import shutil
import subprocess
from pathlib import Path

import pytest

NODE = shutil.which("node")
TESTS = Path(__file__).parent / "board"


@pytest.mark.skipif(NODE is None, reason="node is not installed")
def test_board_js() -> None:
    specs = sorted(str(p) for p in TESTS.glob("*.test.mjs"))
    assert specs, "no tests/board/*.test.mjs files found"
    proc = subprocess.run(
        [NODE, "--test", *specs],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stdout + proc.stderr
