from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from datasets.esp_fi import SUBCARRIERS, TIME_STEPS
from datasets.splits import assign_louo_splits
from ingestion.ml_contract import har_sample_from_window
from ingestion.schema import CsiWindow
from preprocessing.pipeline import PreprocessConfig
from test_splits import full_grid
from training.esp_fi import EspFiSplitBundle
from training.louo_experiment import run_louo_classical_experiment

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "esp-fi-har"


def _synthetic_bundle(held_out: int) -> EspFiSplitBundle:
    records = full_grid()
    assignment = assign_louo_splits(records, held_out_participant=held_out, seed=42)
    rng = np.random.default_rng(held_out)
    by_split: dict[str, list] = {"train": [], "val": [], "test": []}
    for record in records:
        split_name = assignment.session_to_split[record.session_id]
        amplitude = rng.normal(size=(TIME_STEPS, SUBCARRIERS))
        window = CsiWindow(
            amplitude=amplitude,
            phase=None,
            sample_rate_hz=None,
            timestamp=None,
            subcarriers=SUBCARRIERS,
            antennas=None,
            metadata={
                "dataset_id": "esp-fi-har",
                "normalized_label": record.normalized_label,
                "session_id": record.session_id,
                "participant_id": record.participant_id,
                "scenario_id": record.scenario_id,
                "activity_code": record.activity_code,
                "trial_id": record.trial_id,
            },
        )
        sample = har_sample_from_window(
            window,
            split=split_name,
            split_strategy=assignment.strategy,
        )
        by_split[split_name].append(sample)
    return EspFiSplitBundle(
        strategy=assignment.strategy,
        assignment=assignment,
        samples_by_split={name: tuple(items) for name, items in by_split.items()},
    )


def test_louo_classical_experiment_writes_manifest_and_metrics(tmp_path):
    config = {
        "name": "test_louo",
        "seed": 42,
        "verify_assignment_hash": True,
        "dataset": {"dataset_id": "esp-fi-har", "root": str(DATA)},
        "preprocess": PreprocessConfig().to_dict(),
        "logreg": {"C": 1.0, "max_iter": 200, "class_weight": None},
        "families": ["logreg"],
        "folds": [1],
        "run_id": "pytest_louo",
    }

    def _fake_loader(root, *, held_out_participant, **kwargs):
        return _synthetic_bundle(held_out_participant)

    with patch("training.louo_experiment.load_esp_fi_louo_bundle", side_effect=_fake_loader):
        manifest = run_louo_classical_experiment(
            config,
            artifacts_root=tmp_path,
            families=["logreg"],
            folds=[1],
        )

    run_dir = tmp_path / "louo_logreg" / "pytest_louo"
    assert (run_dir / "manifest.json").is_file()
    assert (run_dir / "user_1" / "metrics.json").is_file()
    assert manifest["families"]["logreg"]["folds"]["1"]["test"]["macro_f1"] >= 0.0


@pytest.mark.skipif(not DATA.is_dir(), reason="ESP-Fi not present")
def test_louo_real_data_fold_one_logreg(tmp_path):
    config = {
        "name": "test_louo_real",
        "seed": 42,
        "dataset": {"dataset_id": "esp-fi-har", "root": str(DATA)},
        "preprocess": {},
        "logreg": {"C": 1.0, "max_iter": 500, "class_weight": None},
        "run_id": "pytest_real_louo",
    }
    run_louo_classical_experiment(config, artifacts_root=tmp_path, families=["logreg"], folds=[1])
