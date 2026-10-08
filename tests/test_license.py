from pathlib import Path

import pytest

from common.errors import DatasetError, LicenseError
from datasets.csi_bench import assert_cleared_for_experiment as bench_gate
from datasets.csi_bench import status
from datasets.embedded import assert_cleared_for_experiment as embedded_gate
from datasets.embedded import parse_activity_path, read_raw_capture


def test_experiment_gates_stay_closed():
    with pytest.raises(LicenseError):
        embedded_gate()
    with pytest.raises(LicenseError):
        bench_gate()
    assert status()["experiment_use"] == "blocked"
    assert status()["acquisition"] == "blocked_no_kaggle_credentials"
    assert status()["code_policy"] == "reference_only"


def test_embedded_reader_on_a_synthetic_capture(tmp_path: Path):
    path = tmp_path / "Activity" / "FA" / "s1" / "csi_data_1.txt"
    path.parent.mkdir(parents=True)
    pairs = ",".join(["1,2"] * 64)
    path.write_text(f"100,{pairs}\n110,{pairs}\n")
    timestamps, csi = read_raw_capture(path)
    assert timestamps.tolist() == [100, 110]
    assert csi.shape == (2, 64)
    assert csi[0, 0] == 2 + 1j
    meta = parse_activity_path(path)
    assert meta["normalized_label"] == "falling"
    assert meta["license_status"].startswith("academic_consent")
    with pytest.raises(DatasetError):
        parse_activity_path(tmp_path / "Activity" / "NO" / "s1" / "x.txt")
