"""Thesis benchmark ladder: extended families and assignment hashes."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from research.generalization import (
    BASELINE_RUN_IDS,
    EXTENDED_FAMILIES,
    EXTENDED_RUN_IDS,
    STRATEGIES,
    extended_metrics_entries,
    load_metrics_json,
)

ROOT = Path(__file__).resolve().parents[1]

LOCKED_ASSIGNMENT_SHA256: dict[str, str] = {
    "in_domain": "6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da",
    "cross_user": "ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72",
    "cross_environment": "00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8",
}


def _logreg_baseline_hashes() -> dict[str, str]:
    run_id = BASELINE_RUN_IDS["logreg"]
    out: dict[str, str] = {}
    for strategy in STRATEGIES:
        path = (
            ROOT
            / "artifacts"
            / "v2_logreg"
            / run_id
            / strategy
            / "metrics.json"
        )
        metrics = load_metrics_json(path)
        out[strategy] = metrics["assignment_sha256"]
    return out


@pytest.mark.skipif(
    not all(
        (ROOT / "artifacts" / f"v2_{fam}" / EXTENDED_RUN_IDS.get(fam, "") / "in_domain" / "metrics.json").is_file()
        for fam in EXTENDED_FAMILIES
        if fam in EXTENDED_RUN_IDS
    ),
    reason="extended-family artifacts missing",
)
def test_extended_metrics_entries_full_ladder():
    entries = extended_metrics_entries(ROOT)
    assert len(entries) == 21
    families = {e["family"] for e in entries}
    assert families == {"logreg", "rf", "cnn1d", "gru", "mlp", "gbdt", "tcn"}
    for family in EXTENDED_FAMILIES:
        run_id = EXTENDED_RUN_IDS[family]
        for strategy in STRATEGIES:
            artifact = ROOT / "artifacts" / f"v2_{family}" / run_id / strategy
            assert (artifact / "metrics.json").is_file()


@pytest.mark.parametrize("family", EXTENDED_FAMILIES)
def test_extended_family_macro_f1_in_unit_interval(family: str):
    run_id = EXTENDED_RUN_IDS.get(family)
    if not run_id:
        pytest.skip("run not pinned")
    for strategy in STRATEGIES:
        path = ROOT / "artifacts" / f"v2_{family}" / run_id / strategy / "metrics.json"
        if not path.is_file():
            pytest.skip(f"missing {path}")
        test = load_metrics_json(path)["test"]
        macro_f1 = test["macro_f1"]
        assert 0.0 <= macro_f1 <= 1.0


@pytest.mark.parametrize("family", EXTENDED_FAMILIES)
def test_extended_assignment_hash_matches_locked_and_logreg(family: str):
    run_id = EXTENDED_RUN_IDS.get(family)
    if not run_id:
        pytest.skip("run not pinned")
    logreg_hashes = _logreg_baseline_hashes()
    for strategy in STRATEGIES:
        path = ROOT / "artifacts" / f"v2_{family}" / run_id / strategy / "metrics.json"
        if not path.is_file():
            pytest.skip(f"missing {path}")
        metrics = load_metrics_json(path)
        sha = metrics["assignment_sha256"]
        assert sha == LOCKED_ASSIGNMENT_SHA256[strategy]
        assert sha == logreg_hashes[strategy]
