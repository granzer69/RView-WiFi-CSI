import json
from pathlib import Path

import numpy as np
import pytest

from datasets.audit import audit_numeric, audit_split_assignment, session_leakage_answer
from datasets.esp_fi import SUBCARRIERS, TIME_STEPS, discover_trials, load_window
from datasets.splits import assign_splits
from ingestion.ml_contract import (
    LABEL_TO_ID,
    MODEL_INPUT_SHAPES,
    NORMALIZED_LABELS,
    PUBLISHED_SPLIT_ROLE,
    har_sample_from_window,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"
ESP_FI_CONFIG = ROOT / "configs" / "datasets" / "esp_fi_har.json"
SPLITS_CONFIG = ROOT / "configs" / "experiments" / "esp_fi_splits.json"

pytestmark = pytest.mark.skipif(not DATA.exists(), reason="ESP-Fi archive is not present")


def test_numeric_audit_on_full_archive():
    records = discover_trials(DATA)
    report = audit_numeric(records)
    assert report.files_read == 2240
    assert report.non_finite_count == 0
    assert report.unique_shapes == {"(950, 52)": 2240}
    assert report.dtype == "float64"
    assert report.amplitude_min >= 0
    assert report.amplitude_max > report.amplitude_min


def test_no_session_crosses_splits_for_all_strategies():
    records = discover_trials(DATA)
    for strategy in ("in_domain", "cross_user", "cross_environment"):
        assignment = assign_splits(records, strategy=strategy, seed=42)
        leakage = session_leakage_answer(assignment)
        assert leakage["same_recording_leaks_train_and_test"] is False
        assert leakage["shared_sessions_train_test"] == []
        audit = audit_split_assignment(records, assignment)
        assert audit["groups_crossing_splits"] == []


def test_split_class_balance_is_uniform_per_split_in_domain():
    records = discover_trials(DATA)
    assignment = assign_splits(records, strategy="in_domain", seed=42)
    audit = audit_split_assignment(records, assignment)
    for split_name in ("train", "val", "test"):
        labels = audit["per_split"][split_name]["by_normalized_label"]
        assert len(labels) == 7
        assert all(count == audit["per_split"][split_name]["samples"] // 7 for count in labels.values())


def test_har_sample_contract_from_loader():
    record = discover_trials(DATA)[0]
    window = load_window(record)
    sample = har_sample_from_window(window, split="train", split_strategy="in_domain")
    assert sample.amplitude.shape == (TIME_STEPS, SUBCARRIERS)
    assert sample.normalized_label in NORMALIZED_LABELS
    assert sample.label_id == LABEL_TO_ID[sample.normalized_label]
    assert sample.metadata.get("source_path") is None
    assert sample.flattened().shape == (TIME_STEPS * SUBCARRIERS,)
    assert MODEL_INPUT_SHAPES["gru"]["shape"] == (TIME_STEPS, SUBCARRIERS)


def test_published_split_is_leakage_check_only_in_config():
    dataset = json.loads(ESP_FI_CONFIG.read_text())
    splits = json.loads(SPLITS_CONFIG.read_text())
    assert dataset["published_split_role"] == PUBLISHED_SPLIT_ROLE
    assert splits["published_folders"] == "leakage check only; not an evaluation split"
    leakage_src = (ROOT / "src" / "datasets" / "leakage.py").read_text()
    splits_src = (ROOT / "src" / "datasets" / "splits.py").read_text()
    assert "train_amp" in leakage_src
    assert "train_amp" not in splits_src
