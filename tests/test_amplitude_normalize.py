import numpy as np

from features.amplitude_normalize import AmplitudeNormalizer


def test_amplitude_normalizer_train_only():
    rng = np.random.default_rng(0)
    train = rng.normal(size=(4, 10, 3)).astype(np.float64)
    test = rng.normal(size=(2, 10, 3)).astype(np.float64) + 3.0
    norm = AmplitudeNormalizer().fit(train)
    out_train = norm.transform(train)
    out_test = norm.transform(test)
    assert np.isclose(out_train.mean(), 0.0, atol=1e-6)
    assert np.isclose(out_train.std(), 1.0, atol=1e-6)
    assert out_test.shape == test.shape
    assert not np.allclose(out_test, 0.0)
