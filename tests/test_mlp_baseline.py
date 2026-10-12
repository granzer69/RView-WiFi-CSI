import numpy as np

from ingestion.ml_contract import LABEL_TO_ID
from models.mlp import MlpHarModel, train_mlp


def _tiny_batch(n: int, times: int = 32, subcarriers: int = 8) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(3)
    x = rng.normal(size=(n, times, subcarriers)).astype(np.float64)
    y = np.arange(n, dtype=np.int64) % len(LABEL_TO_ID)
    return x, y


def test_mlp_train_evaluate_save_load(tmp_path):
    train_x, train_y = _tiny_batch(28)
    test_x, test_y = _tiny_batch(12)
    model = train_mlp(train_x, train_y, random_state=1, max_iter=80, hidden_layer_sizes=(32, 16))
    metrics = model.evaluate(test_x, test_y)
    assert "macro_f1" in metrics
    model.save(tmp_path / "mlp")
    loaded = MlpHarModel.load(tmp_path / "mlp")
    np.testing.assert_array_equal(model.predict(test_x), loaded.predict(test_x))
