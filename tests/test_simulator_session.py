"""Simulator session controller and dataset replay source."""

from __future__ import annotations

from pathlib import Path

import pytest

from datasets.esp_fi import discover_trials
from simulator.clock import ALLOWED_SPEEDS, ReplayClock
from simulator.session_controller import SessionController, TransportState
from simulator.sources.dataset_replay import DatasetReplaySource

ESP_FI_ROOT = Path(__file__).resolve().parents[1] / "data" / "raw" / "esp-fi-har"


@pytest.fixture(scope="module")
def any_session_id() -> str:
    records = discover_trials(ESP_FI_ROOT)
    return sorted(records, key=lambda r: r.session_id)[0].session_id


def test_replay_clock_speed_validation():
    clock = ReplayClock()
    for speed in ALLOWED_SPEEDS:
        clock.set_speed(speed)
        assert clock.tick_interval_seconds == pytest.approx(1.0 / (95.0 * speed))
    with pytest.raises(ValueError):
        clock.set_speed(3.0)


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
