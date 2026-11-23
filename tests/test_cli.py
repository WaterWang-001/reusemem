"""Verify input isolation and read-only environment diagnostics."""

from pathlib import Path

import pytest

from reusemem.cli import main
from reusemem.doctor import EXTERNAL_FILES, inspect_environment


def test_doctor_checks_external_code_without_claiming_data_available(tmp_path: Path) -> None:
    for relative in EXTERNAL_FILES:
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("", encoding="utf-8")
    report = inspect_environment(external_eval_root=tmp_path, benchmark_root=tmp_path / "missing")
    assert report["inputs"]["external_eval"]["ok"]
    assert not report["inputs"]["benchmark"]["ok"]
    assert not report["ok"]


def test_doctor_does_not_disclose_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("REUSEMEM_API_KEY", "sentinel-secret-not-to-print")
    report = inspect_environment()
    assert report["provider_configuration"]["REUSEMEM_API_KEY"] is True
    assert "sentinel-secret-not-to-print" not in str(report)


def test_replay_rejects_nonpositive_budget() -> None:
    with pytest.raises(SystemExit) as error:
        main(["replay", "--input", "missing", "--output", "missing", "--memory-budget", "0"])
    assert error.value.code == 2
