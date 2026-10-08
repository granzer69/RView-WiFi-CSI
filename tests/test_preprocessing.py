import json
from pathlib import Path

import numpy as np

from ingestion.schema import CsiWindow
from preprocessing.pipeline import PreprocessConfig, process, processed_hash

ROOT = Path(__file__).resolve().parents[1]


def _window(values: np.ndarray) -> CsiWindow:
    return CsiWindow(
        amplitude=values,
        phase=None,
        sample_rate_hz=None,
        timestamp=None,
        subcarriers=values.shape[1],
        antennas=None,
        metadata={"session_id": "1-1-1-1"},
    )


def test_default_config_matches_file_and_keeps_the_trial():
    document = json.loads((ROOT / "configs" / "preprocessing" / "default.json").read_text())
    config = PreprocessConfig()
    assert config.to_dict() == {key: document[key] for key in config.to_dict()}
    original = np.arange(20, dtype=np.float64).reshape(5, 4)
    window = _window(original)
    result = process(window)
    assert result.dropped_tail == 0
    assert len(result.windows) == 1
    assert np.array_equal(result.windows[0].amplitude, original)
    assert np.array_equal(window.amplitude, original)
    assert processed_hash(result) == processed_hash(process(window, config))


def test_zscore_and_clip_can_be_toggled():
    values = np.arange(12, dtype=np.float64).reshape(6, 2)
    values[0, 0] = 1000.0
    window = _window(values)
    clipped = process(window, PreprocessConfig(clip_mad=True, mad_k=5.0))
    assert clipped.windows[0].amplitude[0, 0] < 1000.0
    plain = process(window, PreprocessConfig(clip_mad=False))
    assert plain.windows[0].amplitude[0, 0] == 1000.0
    flat = process(_window(np.ones((4, 2))), PreprocessConfig(clip_mad=True))
    assert np.array_equal(flat.windows[0].amplitude, np.ones((4, 2)))

    scaled = process(window, PreprocessConfig(normalize="per_window_zscore"))
    np.testing.assert_allclose(scaled.windows[0].amplitude.mean(), 0.0, atol=1e-12)
    np.testing.assert_allclose(scaled.windows[0].amplitude.std(), 1.0, atol=1e-12)

    constant = process(_window(np.full((4, 2), 3.0)), PreprocessConfig(normalize="per_window_zscore"))
    assert np.array_equal(constant.windows[0].amplitude, np.zeros((4, 2)))


def test_segments_stay_inside_the_session():
    window = _window(np.arange(20, dtype=np.float64).reshape(10, 2))
    result = process(window, PreprocessConfig(window_length=4, hop=4))
    assert [item.metadata["segment_start"] for item in result.windows] == [0, 4]
    assert result.dropped_tail == 2
    assert all(item.session_id == "1-1-1-1" for item in result.windows)
    assert all(item.metadata["segment_end"] <= window.n_times for item in result.windows)
    rebuilt = np.concatenate([item.amplitude for item in result.windows], axis=0)
    assert np.array_equal(rebuilt, window.amplitude[:8])
