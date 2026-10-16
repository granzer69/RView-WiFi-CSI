"""Simulator session controller and dataset replay source."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

from datasets.esp_fi import SUBCARRIERS, TIME_STEPS, discover_trials
from simulator.clock import ALLOWED_SPEEDS, ReplayClock
from simulator.session_controller import SessionController, TransportState
from simulator.sources.dataset_replay import DatasetReplaySource

ESP_FI_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "esp-fi-har"
ESPFI_DATASET_SKIP = "ESP-Fi dataset required at data/raw/esp-fi-har (see docs/SETUP.md)"


def _esp_fi_archive_ready() -> bool:
    if not ESP_FI_ROOT.is_dir():
        return False
    return any(ESP_FI_ROOT.rglob("*.mat"))


pytestmark = pytest.mark.skipif(
    not _esp_fi_archive_ready(),
    reason="ESP-Fi archive is not present",
)


@pytest.fixture(scope="module")
def any_session_id() -> str:
    if not ESP_FI_ROOT.is_dir():
        pytest.skip(ESPFI_DATASET_SKIP)
    records = discover_trials(ESP_FI_ROOT)
    if not records:
        pytest.skip(ESPFI_DATASET_SKIP)
    return sorted(records, key=lambda r: r.session_id)[0].session_id


@pytest.fixture
def minimal_replay_root(tmp_path: Path) -> Path:
    """One-trial ESP-Fi layout for dataset replay without the full corpus."""
    mat_dir = tmp_path / "scenario1" / "mat"
    mat_dir.mkdir(parents=True)
    amp = np.linspace(0.0, 1.0, TIME_STEPS * SUBCARRIERS, dtype=np.float64).reshape(
        TIME_STEPS, SUBCARRIERS
    )
    sio.savemat(mat_dir / "1-1-2-1.mat", {"CSIamp": amp})
    return tmp_path


def test_replay_clock_speed_validation():
    clock = ReplayClock()
    for speed in ALLOWED_SPEEDS:
        clock.set_speed(speed)
        assert clock.tick_interval_seconds == pytest.approx(1.0 / (95.0 * speed))
    with pytest.raises(ValueError):
        clock.set_speed(3.0)


def test_dataset_replay_emits_rows_synthetic(minimal_replay_root: Path):
    source = DatasetReplaySource(minimal_replay_root)
    source.open("1-1-2-1")
    assert source.frame_count == 950
    first = source.read_next()
    assert first is not None
    assert first.time_index == 0
    assert len(first.subcarriers) == 52
    assert first.subcarriers[0] == pytest.approx(0.0)
    assert first.meta["data_tier"] == "real"
    assert first.meta["session_id"] == "1-1-2-1"


@pytest.mark.skipif(not ESP_FI_ROOT.is_dir(), reason=ESPFI_DATASET_SKIP)
def test_dataset_replay_emits_rows(any_session_id: str):
    source = DatasetReplaySource(ESP_FI_ROOT)
    source.open(any_session_id)
    assert source.frame_count == 950
    first = source.read_next()
    assert first is not None
    assert first.time_index == 0
    assert len(first.subcarriers) == 52
    assert first.meta["data_tier"] == "real"
    assert first.meta["session_id"] == any_session_id


@pytest.mark.skipif(not ESP_FI_ROOT.is_dir(), reason=ESPFI_DATASET_SKIP)
def test_session_controller_restart(any_session_id: str):
    source = DatasetReplaySource(ESP_FI_ROOT)
    controller = SessionController(source=source)
    controller.open_session(any_session_id)
    controller.control("play")
    frame = controller.tick()
    assert frame is not None
    controller.control("pause")
    assert controller.state == TransportState.PAUSED
    controller.control("restart")
    assert controller.source.read_next() is not None
    assert controller.source.read_next().time_index == 1
