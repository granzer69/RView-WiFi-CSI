import numpy as np
import pytest

from common.errors import DatasetError
from ingestion.schema import CsiWindow


def _window(**overrides):
    values = {"amplitude": np.ones((4, 3)), "phase": None, "sample_rate_hz": None, "timestamp": None, "subcarriers": 3, "antennas": None, "metadata": {"session_id": "1-1-1-1"}}
    values.update(overrides)
    return CsiWindow(**values)


def test_window_keeps_absent_phase_and_rate():
    window = _window()
    assert window.phase is None
    assert window.sample_rate_hz is None
    assert window.antennas is None
    assert window.n_times == 4
    assert window.session_id == "1-1-1-1"


def test_window_rejects_wrong_rank_and_non_finite():
    with pytest.raises(DatasetError):
        _window(amplitude=np.ones((4, 3, 1)))
    with pytest.raises(DatasetError):
        _window(amplitude=np.array([[1.0, 2.0], [3.0, np.nan], [4.0, 5.0]]), subcarriers=2)
    with pytest.raises(DatasetError):
        _window(sample_rate_hz=0)
    with pytest.raises(DatasetError):
        _window(phase=np.ones((3, 3)))
