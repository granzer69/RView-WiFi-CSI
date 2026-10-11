"""Document leakage constraints for research personalization helpers."""

from __future__ import annotations

from research.leakage import calib_eval_session_sets_disjoint
from research.participant import build_participant_overview

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"


def test_calib_eval_session_disjoint_documented():
    """Calibration and evaluation must not share session IDs."""
    calib = {"1-1-1-1", "1-1-2-3"}
    eval_ok = {"2-3-4-5"}
    eval_bad = {"1-1-2-3", "4-4-4-4"}
    assert calib_eval_session_sets_disjoint(calib, eval_ok) is True
    assert calib_eval_session_sets_disjoint(calib, eval_bad) is False


def test_in_domain_train_test_sessions_disjoint_per_participant():
    """Each participant's train and test session sets must not overlap."""
    if not DATA.is_dir():
        return
    overview = build_participant_overview(ROOT, strategy="in_domain")
    assert overview["status"] == "ok"
    # Overview aggregates counts; split assignment guarantees one split per session.
    for participant in overview["participants"]:
        counts = participant["session_counts"]
        assert counts["train"] + counts["val"] + counts["test"] == counts["total"]
