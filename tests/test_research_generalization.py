"""Tests for research generalization helpers."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.generalization import (
    BASELINE_RUN_IDS,
    EXTENDED_RUN_IDS,
    baseline_metrics_entries,
    build_generalization_rows,
    compute_generalization_gap,
    confused_pairs_from_matrix,
    extended_metrics_entries,
    load_metrics_json,
    supplement_macro_averages,
)

ROOT = Path(__file__).resolve().parents[1]


def test_generalization_gap_sign():
    assert compute_generalization_gap(0.9, 0.7) == pytest.approx(0.2)
    assert compute_generalization_gap(0.5, 0.6) == pytest.approx(-0.1)


def test_confused_pairs_sorted_off_diagonal():
    confusion = {
        "labels": ["a", "b", "c"],
        "matrix": [
            [10, 3, 0],
            [1, 8, 5],
            [0, 2, 7],
        ],
    }
    pairs = confused_pairs_from_matrix(confusion, top_k=5)
    assert pairs[0]["count"] == 5
    assert pairs[0]["true_label"] == "b"
    assert pairs[0]["predicted_label"] == "c"
    assert all(pair["true_label"] != pair["predicted_label"] for pair in pairs)


def test_load_metrics_json_missing():
    with pytest.raises(FileNotFoundError):
        load_metrics_json(ROOT / "artifacts" / "missing" / "metrics.json")


def test_supplement_macro_from_per_class():
    test = {
        "per_class": {
            "running": {"precision": 0.8, "recall": 0.6, "f1": 0.7, "support": 10},
            "walking": {"precision": 0.4, "recall": 0.2, "f1": 0.3, "support": 10},
        }
    }
    enriched = supplement_macro_averages(test)
    assert enriched["macro_precision"] == pytest.approx(0.6)
    assert enriched["macro_recall"] == pytest.approx(0.4)


@pytest.mark.skipif(
    not (ROOT / "artifacts" / "v2_logreg" / BASELINE_RUN_IDS["logreg"] / "in_domain" / "metrics.json").is_file(),
    reason="baseline logreg metrics missing",
)
def _write_minimal_metrics(path: Path, macro_f1: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "assignment_sha256": "test",
                "test": {"accuracy": macro_f1, "macro_f1": macro_f1},
            }
        ),
        encoding="utf-8",
    )


def test_extended_entries_include_mlp_when_artifacts_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    run_id = "fixture_extended_run"
    for strategy, macro in (
        ("in_domain", 0.5),
        ("cross_user", 0.3),
        ("cross_environment", 0.25),
    ):
        _write_minimal_metrics(
            tmp_path / "artifacts" / "v2_mlp" / run_id / strategy / "metrics.json",
            macro,
        )
    monkeypatch.setitem(EXTENDED_RUN_IDS, "mlp", run_id)
    entries = extended_metrics_entries(tmp_path)
    mlp = [e for e in entries if e["family"] == "mlp"]
    assert len(mlp) == 3
    assert all(e["run_id"] == run_id for e in mlp)


def test_baseline_entries_and_gaps():
    entries = baseline_metrics_entries(ROOT)
    assert len(entries) >= 12
    rows = build_generalization_rows(entries)
    in_domain = next(
        r for r in rows if r["family"] == "logreg" and r["split_strategy"] == "in_domain"
    )
    cross_user = next(
        r for r in rows if r["family"] == "logreg" and r["split_strategy"] == "cross_user"
    )
    assert in_domain["generalization_gap"] == pytest.approx(0.0)
    assert cross_user["generalization_gap"] == pytest.approx(
        compute_generalization_gap(in_domain["macro_f1"], cross_user["macro_f1"])
    )
    assert cross_user["confused_pairs"]
