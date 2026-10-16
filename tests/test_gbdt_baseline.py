import numpy as np

from ingestion.ml_contract import LABEL_TO_ID
from models.gbdt import GbdtHarModel, train_gbdt


def _tiny_batch(n: int, times: int = 32, subcarriers: int = 8) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(4)
    x = rng.normal(size=(n, times, subcarriers)).astype(np.float64)
    y = np.arange(n, dtype=np.int64) % len(LABEL_TO_ID)
    return x, y


def test_gbdt_train_evaluate_save_load(tmp_path):
    train_x, train_y = _tiny_batch(28)
    test_x, test_y = _tiny_batch(12)
    model = train_gbdt(train_x, train_y, random_state=1, max_iter=30, max_depth=4)
    metrics = model.evaluate(test_x, test_y)
    assert "macro_f1" in metrics
    model.save(tmp_path / "gbdt")
    loaded = GbdtHarModel.load(tmp_path / "gbdt")
    np.testing.assert_array_equal(model.predict(test_x), loaded.predict(test_x))
