from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

from common.errors import DatasetError, LabelMapError
from datasets.esp_fi import (
    ACTIVITY_CODE_TO_DATASET_LABEL,
    README_ACTIVITY_CODE_TO_DATASET_LABEL,
    load_window,
    observe_csv_packet_rate,
    parse_stem,
    record_from_path,
    sibling_csv,
)


def test_folder_map_disagrees_with_readme_except_run():
    assert ACTIVITY_CODE_TO_DATASET_LABEL[1] == "run"
    disagree = [
        code for code in ACTIVITY_CODE_TO_DATASET_LABEL
        if ACTIVITY_CODE_TO_DATASET_LABEL[code] != README_ACTIVITY_CODE_TO_DATASET_LABEL[code]
    ]
    assert disagree == [2, 3, 4, 5, 6, 7]


def test_stem_uses_folder_map_not_readme():
    scenario_id, participant_id, activity_code, trial_id = parse_stem("2-5-3-7")
    assert (scenario_id, participant_id, activity_code, trial_id) == (2, 5, 3, 7)
    record = record_from_path(Path("EnvironmentNo.2（Office）/mat/2-5-3-7.mat"))
    assert record.scenario_id == 2
    assert record.participant_id == 5
    assert record.dataset_label == "jump"
    assert record.normalized_label == "jumping"
    assert record.trial_id == 7
    assert record.label_verified_by_folder is False
    assert README_ACTIVITY_CODE_TO_DATASET_LABEL[3] == "walk"


def test_class_folder_must_match_the_code():
    matched = record_from_path(Path("walk/3-1-2-1.mat"))
    assert matched.dataset_label == "walk"
    assert matched.label_verified_by_folder is True
    with pytest.raises(LabelMapError):
        record_from_path(Path("fall/3-1-2-1.mat"))


def test_parse_rejects_unknown_codes():
    with pytest.raises(DatasetError):
        parse_stem("1-1-8-1")
    with pytest.raises(DatasetError):
        parse_stem("not-a-trial")


def test_load_window_accepts_time_major_and_transposed(tmp_path: Path):
    time_major = tmp_path / "mat"
    time_major.mkdir()
    path = time_major / "1-1-1-1.mat"
    sio.savemat(path, {"CSIamp": np.arange(950 * 52, dtype=np.float64).reshape(950, 52)})
    window = load_window(record_from_path(path))
    assert window.amplitude.shape == (950, 52)
    assert window.phase is None
    assert window.sample_rate_hz is None
    assert window.metadata["dataset_label"] == "run"
    assert window.metadata["label_verified_by_folder"] is False
    assert window.metadata["readme_label_for_code"] == "run"

    folder = tmp_path / "run"
    folder.mkdir()
    transposed = folder / "3-2-1-4.mat"
    sio.savemat(transposed, {"CSIamp": np.ones((52, 950))})
    flipped = load_window(record_from_path(transposed))
    assert flipped.amplitude.shape == (950, 52)
    assert flipped.metadata["amplitude_transposed"] is True


def test_load_window_rejects_unexpected_shape(tmp_path: Path):
    path = tmp_path / "1-1-1-1.mat"
    sio.savemat(path, {"CSIamp": np.ones((10, 10))})
    with pytest.raises(DatasetError):
        load_window(record_from_path(path))


def test_sibling_csv_and_packet_rate(tmp_path: Path):
    mat_dir = tmp_path / "mat"
    csv_dir = tmp_path / "csv"
    mat_dir.mkdir()
    csv_dir.mkdir()
    mat_path = mat_dir / "1-1-1-1.mat"
    mat_path.write_bytes(b"")
    csv_path = csv_dir / "1-1-1-1.csv"
    csv_path.write_text(
        "type,timestamp,len\n"
        "CSI_DATA,2024-12-16 16:34:37.000,104\n"
        "CSI_DATA,2024-12-16 16:34:37.500,104\n"
        "CSI_DATA,2024-12-16 16:34:38.000,104\n"
    )
    assert sibling_csv(mat_path) == csv_path
    observed = observe_csv_packet_rate(csv_path)
    assert observed["packet_count"] == 3
    assert observed["observed_packet_rate_hz"] == pytest.approx(2.0)
    assert sibling_csv(tmp_path / "1-1-1-1.mat") is None
