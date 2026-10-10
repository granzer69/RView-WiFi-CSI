from pathlib import Path

import numpy as np
import pytest

from datasets.esp_fi import SUBCARRIERS, TIME_STEPS
from features.classical import ClassicalFeatureExtractor, classical_feature_dim, classical_feature_vector
from ingestion.ml_contract import LABEL_TO_ID, har_sample_from_window
from ingestion.schema import CsiWindow
from models.logreg import LogRegHarModel, train_logreg
from preprocessing.pipeline import PreprocessConfig
from training.esp_fi import (
    EXPECTED_ASSIGNMENT_SHA256,
    assignment_sha256,
    load_esp_fi_split_bundle,
)

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"


def _synthetic_batch(n: int, label_offset: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    amplitudes = rng.normal(size=(n, TIME_STEPS, SUBCARRIERS)) + label_offset
    labels = np.arange(n, dtype=np.int64) % len(LABEL_TO_ID)
    return amplitudes.astype(np.float64), labels


def test_classical_feature_vector_dimension():
    rng = np.random.default_rng(1)
    amplitude = rng.normal(size=(TIME_STEPS, SUBCARRIERS))
    vector = classical_feature_vector(amplitude)
    assert vector.shape == (classical_feature_dim(SUBCARRIERS),)
    assert np.isfinite(vector).all()


def test_feature_extractor_fit_transform_train_only_stats():
    train_x, _ = _synthetic_batch(8)
    test_x, _ = _synthetic_batch(4, label_offset=5)
    extractor = ClassicalFeatureExtractor().fit(train_x)
    train_features = extractor.transform(train_x)
    test_features = extractor.transform(test_x)
    assert train_features.shape[0] == 8
    assert test_features.shape[0] == 4
    assert np.isclose(train_features.mean(axis=0), 0.0, atol=1e-6).all()
    assert np.isclose(train_features.std(axis=0), 1.0, atol=1e-6).all()


def test_logreg_train_predict_evaluate_roundtrip():
    train_x, train_y = _synthetic_batch(28)
    test_x, test_y = _synthetic_batch(14, label_offset=2)
    model = train_logreg(train_x, train_y, random_state=42, max_iter=500)
    predictions = model.predict(test_x)
    assert predictions.shape == (test_x.shape[0],)
    metrics = model.evaluate(test_x, test_y)
    assert "accuracy" in metrics
    assert "macro_f1" in metrics
    assert metrics["confusion_matrix"]["labels"]
    assert metrics["inference_latency"]["per_sample_ms_mean"] > 0


def test_logreg_save_load(tmp_path: Path):
    train_x, train_y = _synthetic_batch(21)
    model = train_logreg(train_x, train_y, random_state=7)
    model.save(tmp_path / "model")
    loaded = LogRegHarModel.load(tmp_path / "model")
    np.testing.assert_array_equal(model.predict(train_x), loaded.predict(train_x))


def test_har_sample_training_contract_metadata():
    amplitude = np.ones((TIME_STEPS, SUBCARRIERS), dtype=np.float64)
    window = CsiWindow(
        amplitude=amplitude,
        phase=None,
        sample_rate_hz=None,
        timestamp=None,
        subcarriers=SUBCARRIERS,
        antennas=None,
        metadata={
            "dataset_id": "esp-fi-har",
            "normalized_label": "walking",
            "session_id": "9-9-2-1",
            "participant_id": 9,
            "scenario_id": 9,
            "activity_code": 2,
            "trial_id": 1,
        },
    )
    sample = har_sample_from_window(window, split="train", split_strategy="in_domain")
    assert sample.metadata.get("source_path") is None
    assert sample.label_id == LABEL_TO_ID["walking"]


@pytest.mark.skipif(not DATA.exists(), reason="ESP-Fi archive is not present")
def test_locked_split_assignment_hashes():
    for strategy, expected in EXPECTED_ASSIGNMENT_SHA256.items():
        bundle = load_esp_fi_split_bundle(
            DATA,
            strategy=strategy,
            preprocess=PreprocessConfig(),
            verify_assignment_hash=True,
        )
        assert assignment_sha256(bundle.assignment) == expected
        train_x, train_y = bundle.amplitudes_and_labels("train")
        assert train_x.shape[1:] == (TIME_STEPS, SUBCARRIERS)
        assert train_y.ndim == 1


@pytest.mark.skipif(not DATA.exists(), reason="ESP-Fi archive is not present")
def test_logreg_end_to_end_on_real_subset():
    bundle = load_esp_fi_split_bundle(DATA, strategy="in_domain", verify_assignment_hash=True)
    train_x, train_y = bundle.amplitudes_and_labels("train")
    val_x, val_y = bundle.amplitudes_and_labels("val")
    # Small deterministic subset keeps CI fast while touching real CSI.
    model = train_logreg(train_x[:140], train_y[:140], random_state=42, max_iter=300)
    metrics = model.evaluate(val_x[:28], val_y[:28])
    assert 0.0 <= metrics["accuracy"] <= 1.0
