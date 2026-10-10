import numpy as np
import pytest

from ingestion.ml_contract import LABEL_TO_ID

pytest.importorskip("torch")

from models.gru import GruHarModel, train_gru  # noqa: E402


def _tiny_batch(n: int, times: int = 32, subcarriers: int = 8) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(3)
    x = rng.normal(size=(n, times, subcarriers)).astype(np.float64)
    y = np.arange(n, dtype=np.int64) % len(LABEL_TO_ID)
    return x, y


def test_gru_train_evaluate_save_load(tmp_path):
    train_x, train_y = _tiny_batch(24)
    val_x, val_y = _tiny_batch(8)
    model = train_gru(
        train_x,
        train_y,
        val_x,
        val_y,
        random_state=1,
        epochs=2,
        batch_size=8,
        device="cpu",
    )
    metrics = model.evaluate(val_x, val_y)
    assert "macro_f1" in metrics
    model.save(tmp_path / "gru")
    loaded = GruHarModel.load(tmp_path / "gru")
    np.testing.assert_array_equal(model.predict(val_x), loaded.predict(val_x))
