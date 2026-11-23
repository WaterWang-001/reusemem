"""Read-only environment and external-input checks; no model calls or secret reads."""

from __future__ import annotations

import importlib.metadata
import os
import platform
import shutil
import sys
from pathlib import Path
from typing import Any

EXTERNAL_FILES = (
    "evaluation/SCORING_V5.md",
    "evaluation/evalkit/runner.py",
    "evaluation/tools/replay_trajectories.py",
    "evaluation/tools/score_memory_runs.py",
)


def inspect_environment(
    external_eval_root: Path | None = None,
    benchmark_root: Path | None = None,
    trajectories_root: Path | None = None,
) -> dict[str, Any]:
    """Inspect only requested paths. Availability does not establish data validity."""
    checks: dict[str, Any] = {
        "python": {
            "version": platform.python_version(),
            "executable": sys.executable,
            "ok": sys.version_info >= (3, 11),
        },
        "platform": {"system": platform.system(), "machine": platform.machine()},
        "cpu_count": os.cpu_count(),
        "tools": {name: shutil.which(name) is not None for name in ("git", "uv", "docker")},
        "provider_configuration": {
            name: bool(os.environ.get(name))
            for name in ("REUSEMEM_BASE_URL", "REUSEMEM_MODEL", "REUSEMEM_API_KEY")
        },
        "scope": "offline synthetic memory probes; no GPU, API calls, or coding-agent execution",
        "inputs": {},
    }
    versions: dict[str, str | None] = {}
    for name in ("reusemem", "pytest", "ruff"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = None
    checks["packages"] = versions
    if external_eval_root is not None:
        root = external_eval_root.expanduser().resolve()
        required = {rel: (root / rel).is_file() for rel in EXTERNAL_FILES}
        checks["inputs"]["external_eval"] = {
            "path": str(root),
            "required_files": required,
            "ok": all(required.values()),
            "note": "Code availability only; benchmark, trajectories, and source environments are separate.",
        }
    if benchmark_root is not None:
        root = benchmark_root.expanduser().resolve()
        checks["inputs"]["benchmark"] = {
            "path": str(root),
            "ok": (root / "setup" / "repos.json").is_file(),
            "note": "Checks setup/repos.json only; completeness, identity, and task validity are not audited.",
        }
    if trajectories_root is not None:
        root = trajectories_root.expanduser().resolve()
        checks["inputs"]["trajectories"] = {
            "path": str(root),
            "ok": root.is_dir() and any(root.iterdir()),
            "note": "Directory availability only; coverage and provenance are not audited.",
        }
    checks["ok"] = checks["python"]["ok"] and all(
        item["ok"] for item in checks["inputs"].values()
    )
    return checks
