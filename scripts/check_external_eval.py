"""Run the external scoring snapshot's synthetic tests without copying its code."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

TESTS = (
    "test_reuse_v5.py",
    "test_score_v5.py",
    "test_archive_replay.py",
    "test_cdup.py",
    "test_cdup_input.py",
    "test_memory_replay.py",
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True, help="external snapshot root")
    args = parser.parse_args()
    evaluation = args.root.expanduser().resolve() / "evaluation"
    paths = [evaluation / "evalkit" / "tests" / filename for filename in TESTS]
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        parser.error("missing external tests: " + ", ".join(missing))
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTHONPATH"] = str(evaluation)
    command = [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"]
    return subprocess.run(
        command + [str(path) for path in paths],
        cwd=Path(__file__).resolve().parents[1],
        env=environment,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
