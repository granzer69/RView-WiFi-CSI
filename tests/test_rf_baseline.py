from pathlib import Path

import numpy as np
import pytest

from datasets.esp_fi import SUBCARRIERS, TIME_STEPS
from ingestion.ml_contract import LABEL_TO_ID
from models.rf import RandomForestHarModel, train_random_forest
from preprocessing.pipeline import PreprocessConfig
from training.esp_fi import load_esp_fi_split_bundle

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"


def _synthetic_batch(n: int, label_offset: int = 0) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(0)
    amplitudes = rng.normal(size=(n, TIME_STEPS, SUBCARRIERS)) + label_offset
    labels = np.arange(n, dtype=np.int64) % len(LABEL_TO_ID)
    return amplitudes.astype(np.float64), labels


def test_rf_train_predict_evaluate_roundtrip():
    train_x, train_y = _synthetic_batch(40)
    test_x, test_y = _synthetic_batch(16, label_offset=2)
    model = train_random_forest(train_x, train_y, random_state=42, n_estimators=25)
    predictions = model.predict(test_x)
    assert predictions.shape == (test_x.shape[0],)
    metrics = model.evaluate(test_x, test_y)
    assert "macro_f1" in metrics
    assert metrics["inference_latency"]["per_sample_ms_mean"] > 0


def test_rf_save_load(tmp_path: Path):
    train_x, train_y = _synthetic_batch(24)
    model = train_random_forest(train_x, train_y, random_state=3, n_estimators=20)
    model.save(tmp_path / "model")
    loaded = RandomForestHarModel.load(tmp_path / "model")
    np.testing.assert_array_equal(model.predict(train_x), loaded.predict(train_x))


@pytest.mark.skipif(not DATA.exists(), reason="ESP-Fi archive is not present")
def test_rf_end_to_end_on_real_subset():
    bundle = load_esp_fi_split_bundle(DATA, strategy="in_domain", verify_assignment_hash=True)
    train_x, train_y = bundle.amplitudes_and_labels("train")
    val_x, val_y = bundle.amplitudes_and_labels("val")
    model = train_random_forest(train_x[:120], train_y[:120], random_state=42, n_estimators=30)
    metrics = model.evaluate(val_x[:24], val_y[:24])
    assert 0.0 <= metrics["accuracy"] <= 1.0
