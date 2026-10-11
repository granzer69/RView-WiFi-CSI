"""In-domain personalization experiment tests."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from research.leakage import calib_eval_session_sets_disjoint
from research.personalization import (
    _fit_participant_calibrator,
    run_in_domain_personalization_ab,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"


def test_calibrator_fits_small_synthetic():
    rng = np.random.default_rng(0)
    x = rng.standard_normal((40, 8))
    y = rng.integers(0, 3, size=40)
    model = _fit_participant_calibrator(x, y, n_classes=3)
    pred = model.predict(x[:5])
    assert pred.shape == (5,)


@pytest.mark.skipif(not DATA.is_dir(), reason="ESP-Fi not on disk")
def test_in_domain_personalization_runs():
    result = run_in_domain_personalization_ab(ROOT)
    assert result["status"] == "completed"
    assert result["cross_user_personalization"] == "blocked"
    assert len(result["experiments"]) >= 1
    exp = result["experiments"][0]
    assert exp["aggregate"]["participants_evaluated"] >= 1
    for row in exp["participants"]:
        if row.get("status") == "ok":
            assert row["calibration_session_count"] > 0
            assert row["evaluation_session_count"] > 0
            assert "macro_f1_delta" in row


def test_personalization_session_disjoint_helper():
    assert calib_eval_session_sets_disjoint({"a"}, {"b"}) is True
    assert calib_eval_session_sets_disjoint({"a"}, {"a"}) is False
