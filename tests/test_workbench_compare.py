"""Workbench run comparison compatibility checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from api.workbench import compare_runs
from common.errors import DatasetError

ROOT = Path(__file__).resolve().parents[1]


def _write_metrics(path: Path, assignment_sha: str, macro_f1: float = 0.5) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "assignment_sha256": assignment_sha,
                "test": {"macro_f1": macro_f1, "accuracy": macro_f1},
            }
        ),
        encoding="utf-8",
    )


def test_compare_runs_rejects_incompatible_split_hashes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("api.workbench.workbench_root", lambda repo: tmp_path / "wb")
    wb = tmp_path / "wb"
    wb.mkdir()
    reg = {
        "runs": [
            {"run_id": "run_a", "family": "logreg", "status": "completed", "artifacts_dir": str(wb / "logreg" / "run_a")},
            {"run_id": "run_b", "family": "logreg", "status": "completed", "artifacts_dir": str(wb / "logreg" / "run_b")},
        ]
    }
    (wb / "registry.json").write_text(json.dumps(reg), encoding="utf-8")
    _write_metrics(wb / "logreg" / "run_a" / "in_domain" / "metrics.json", "hash_a")
    _write_metrics(wb / "logreg" / "run_b" / "in_domain" / "metrics.json", "hash_b")

    result = compare_runs(tmp_path, ["run_a", "run_b"], "in_domain")
    assert result["compatible_splits"] is False
    assert set(result["assignment_sha256_values"]) == {"hash_a", "hash_b"}


def test_compare_runs_compatible_when_hashes_match(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("api.workbench.workbench_root", lambda repo: tmp_path / "wb")
    wb = tmp_path / "wb"
    wb.mkdir()
    reg = {
        "runs": [
            {"run_id": "run_a", "family": "logreg", "status": "completed", "artifacts_dir": str(wb / "logreg" / "run_a")},
            {"run_id": "run_b", "family": "logreg", "status": "completed", "artifacts_dir": str(wb / "logreg" / "run_b")},
        ]
    }
    (wb / "registry.json").write_text(json.dumps(reg), encoding="utf-8")
    _write_metrics(wb / "logreg" / "run_a" / "in_domain" / "metrics.json", "same")
    _write_metrics(wb / "logreg" / "run_b" / "in_domain" / "metrics.json", "same")

    result = compare_runs(tmp_path, ["run_a", "run_b"], "in_domain")
    assert result["compatible_splits"] is True


def test_compare_unknown_run_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("api.workbench.workbench_root", lambda repo: tmp_path / "wb")
    (tmp_path / "wb").mkdir()
    (tmp_path / "wb" / "registry.json").write_text(json.dumps({"runs": []}), encoding="utf-8")
    with pytest.raises(DatasetError):
        compare_runs(tmp_path, ["missing"], "in_domain")
