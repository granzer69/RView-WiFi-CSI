"""Tests for participant profiling helpers."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ingestion.ml_contract import har_sample_from_window
from ingestion.schema import CsiWindow
from research.participant import (
    build_participant_overview,
    calib_eval_session_sets_disjoint,
    per_participant_test_metrics_for_model,
)
from datasets.esp_fi import SUBCARRIERS, TIME_STEPS

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"


def test_calib_eval_disjoint_helper():
    assert calib_eval_session_sets_disjoint({"a", "b"}, {"c"}) is True
    assert calib_eval_session_sets_disjoint({"a"}, {"a", "b"}) is False


def test_participant_overview_blocked(tmp_path: Path):
    overview = build_participant_overview(tmp_path)
    assert overview["status"] == "blocked"
    assert overview["participants"] == []


@pytest.mark.skipif(not DATA.is_dir(), reason="ESP-Fi not on disk")
def test_participant_overview_test_counts_sum():
    overview = build_participant_overview(ROOT, strategy="in_domain")
    assert overview["status"] == "ok"
    total_test = sum(p["session_counts"]["test"] for p in overview["participants"])
    assert total_test == 224
    for participant in overview["participants"]:
        counts = participant["session_counts"]
        assert counts["train"] + counts["val"] + counts["test"] == counts["total"]


def test_per_participant_metrics_test_only_filtering(tmp_path: Path):
    def fake_sample(session_id: str, participant_id: int, split: str):
        parts = [int(p) for p in session_id.split("-")]
        amplitude = np.ones((TIME_STEPS, SUBCARRIERS), dtype=np.float64)
        window = CsiWindow(
            amplitude=amplitude,
            phase=None,
            sample_rate_hz=None,
            timestamp=None,
            subcarriers=SUBCARRIERS,
            antennas=None,
            metadata={
                "session_id": session_id,
                "dataset_id": "esp-fi-har",
                "normalized_label": "running",
                "participant_id": participant_id,
                "scenario_id": parts[0],
                "activity_code": parts[2],
                "trial_id": parts[3],
            },
        )
        return har_sample_from_window(
            window,
            split=split,
            split_strategy="in_domain",
        )

    samples = [
        fake_sample("1-1-1-1", 1, "train"),
        fake_sample("1-1-1-2", 1, "test"),
        fake_sample("1-2-1-1", 2, "test"),
    ]
    bundle = MagicMock()
    bundle.samples_by_split = {"test": tuple(s for s in samples if s.split == "test")}

    backend = MagicMock()
    backend.label_names = ("running", "walking", "jumping", "squatting", "arm_wave", "turning", "falling")
    backend.predict.side_effect = lambda batch: np.zeros(batch.shape[0], dtype=np.int64)

    artifact_dir = tmp_path / "artifacts" / "v2_logreg" / "run" / "in_domain"
    artifact_dir.mkdir(parents=True)

    with (
        patch("research.participant.check_esp_fi_available") as availability,
        patch("research.participant.load_esp_fi_split_bundle", return_value=bundle),
        patch("research.participant._load_backend", return_value=backend),
        patch("research.participant.baseline_artifact_dir", return_value=artifact_dir),
    ):
        availability.return_value.present = True
        availability.return_value.root = tmp_path
        availability.return_value.reason = None
        result = per_participant_test_metrics_for_model(
            tmp_path,
            family="logreg",
            strategy="in_domain",
            run_id="run",
            verify_assignment_hash=False,
        )

    assert result["status"] == "ok"
    test_count = sum(p["test_session_count"] for p in result["participants"])
    assert test_count == len(bundle.samples_by_split["test"])
