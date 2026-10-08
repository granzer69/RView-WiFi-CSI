from pathlib import Path

import pytest

from datasets.esp_fi import SUBCARRIERS, TIME_STEPS, discover_trials, load_window

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"


pytestmark = pytest.mark.skipif(not DATA.exists(), reason="ESP-Fi archive is not present")


def test_archive_is_the_full_grid_and_one_file_per_class_loads():
    records = discover_trials(DATA)
    assert len(records) == 2240
    assert len({record.session_id for record in records}) == 2240
    assert all(not record.label_verified_by_folder for record in records)
    seen = set()
    for record in records:
        if record.dataset_label in seen:
            continue
        window = load_window(record)
        assert window.amplitude.shape == (TIME_STEPS, SUBCARRIERS)
        assert window.phase is None
        assert window.sample_rate_hz is None
        seen.add(record.dataset_label)
    assert seen == {"run", "walk", "jump", "squat", "arm_wave", "turn", "fall"}
