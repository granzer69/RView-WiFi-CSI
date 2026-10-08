"""ESP-Fi HAR adapter.

Archive layout (RAR, CC BY 4.0): one trial is ``X-Y-Z-M.mat`` with key
``CSIamp`` and shape ``(950, 52)``, plus a sibling raw ``CSI_DATA`` CSV.
``X`` is the scenario, ``Y`` the participant, ``Z`` the activity code, and
``M`` the trial.

The activity-code map was measured on the git-published class folders at
commit ``c8bf6aa`` (scenario 3 only, 80 files per folder, no exceptions).
It disagrees with the README id table. Scenarios 1, 2, and 4 have no class
folders, so those labels use the measured map and are marked unverified.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import scipy.io as sio

from common.errors import DatasetError, LabelMapError
from ingestion.schema import CsiWindow

# Measured from published folders. Do not "correct" this toward the README.
ACTIVITY_CODE_TO_DATASET_LABEL: dict[int, str] = {
    1: "run",
    2: "walk",
    3: "jump",
    4: "squat",
    5: "arm_wave",
    6: "turn",
    7: "fall",
}

# README table. Kept so the disagreement is testable and visible.
README_ACTIVITY_CODE_TO_DATASET_LABEL: dict[int, str] = {
    1: "run",
    2: "fall",
    3: "walk",
    4: "turn",
    5: "jump",
    6: "squat",
    7: "arm_wave",
}

DATASET_TO_NORMALIZED: dict[str, str] = {
    "run": "running",
    "walk": "walking",
    "jump": "jumping",
    "squat": "squatting",
    "arm_wave": "arm_wave",
    "turn": "turning",
    "fall": "falling",
}

SCENARIO_NAMES: dict[int, str] = {
    1: "corridor",
    2: "office",
    3: "boardroom",
    4: "laboratory",
}

README_SCENARIO_NAMES: dict[int, str] = {
    1: "corridor",
    2: "office",
    3: "meeting_room",
    4: "laboratory",
}

CLASS_FOLDERS = set(ACTIVITY_CODE_TO_DATASET_LABEL.values())
TIME_STEPS = 950
SUBCARRIERS = 52
DATASET_ID = "esp-fi-har"
DATASET_VERSION = "rar-sha256-85f3df633c5b1a48ca4b1423467fce22821b21eeb3eed085a8d9f983dc156660"


@dataclass(frozen=True)
class TrialRecord:
    """Metadata for one ESP-Fi trial. The amplitude stays on disk."""

    session_id: str
    scenario_id: int
    participant_id: int
    activity_code: int
    trial_id: int
    dataset_label: str
    normalized_label: str
    path: str
    label_verified_by_folder: bool
    scenario_dirname: str

    def group_value(self, strategy: str) -> str:
        if strategy == "in_domain":
            return self.session_id
        if strategy == "cross_user":
            return str(self.participant_id)
        if strategy == "cross_environment":
            return str(self.scenario_id)
        raise DatasetError(f"unknown split strategy: {strategy}")

    def stratum_value(self, strategy: str) -> str:
        if strategy == "in_domain":
            return f"{self.scenario_id}:{self.participant_id}:{self.dataset_label}"
        return "all"


def parse_stem(stem: str) -> tuple[int, int, int, int]:
    parts = stem.split("-")
    if len(parts) != 4 or any(not part.isdigit() for part in parts):
        raise DatasetError(f"expected trial name X-Y-Z-M, got {stem!r}")
    scenario_id, participant_id, activity_code, trial_id = (int(part) for part in parts)
    if activity_code not in ACTIVITY_CODE_TO_DATASET_LABEL:
        raise DatasetError(f"activity code {activity_code} is not in 1..7 ({stem})")
    if scenario_id not in SCENARIO_NAMES:
        raise DatasetError(f"scenario id {scenario_id} is not in 1..4 ({stem})")
    if participant_id < 1 or trial_id < 1:
        raise DatasetError(f"participant and trial ids must be positive ({stem})")
    return scenario_id, participant_id, activity_code, trial_id


def record_from_path(path: Path) -> TrialRecord:
    scenario_id, participant_id, activity_code, trial_id = parse_stem(path.stem)
    dataset_label = ACTIVITY_CODE_TO_DATASET_LABEL[activity_code]
    folder = path.parent.name
    verified = folder in CLASS_FOLDERS
    if verified and folder != dataset_label:
        raise LabelMapError(
            f"{path.name} is in folder {folder!r} but activity code "
            f"{activity_code} maps to {dataset_label!r}"
        )
    scenario_dirname = path.parent.name if verified else path.parent.parent.name
    return TrialRecord(
        session_id=path.stem,
        scenario_id=scenario_id,
        participant_id=participant_id,
        activity_code=activity_code,
        trial_id=trial_id,
        dataset_label=dataset_label,
        normalized_label=DATASET_TO_NORMALIZED[dataset_label],
        path=str(path),
        label_verified_by_folder=verified,
        scenario_dirname=scenario_dirname,
    )


def discover_trials(root: Path) -> list[TrialRecord]:
    paths = sorted(root.rglob("*.mat"))
    if not paths:
        raise DatasetError(f"no .mat files under {root}")
    records = [record_from_path(path) for path in paths]
    ids = [record.session_id for record in records]
    if len(ids) != len(set(ids)):
        raise DatasetError("duplicate ESP-Fi session ids")
    return records


def load_window(record: TrialRecord) -> CsiWindow:
    path = Path(record.path)
    try:
        mat = sio.loadmat(path)
    except Exception as exc:  # scipy raises several file-format errors
        raise DatasetError(f"could not read {path}: {exc}") from exc
    if "CSIamp" not in mat:
        raise DatasetError(f"{path} has no CSIamp key")
    amplitude = np.asarray(mat["CSIamp"], dtype=np.float64)
    transposed = False
    if amplitude.shape == (SUBCARRIERS, TIME_STEPS):
        amplitude = amplitude.T
        transposed = True
    elif amplitude.shape != (TIME_STEPS, SUBCARRIERS):
        raise DatasetError(f"{path} CSIamp shape {amplitude.shape} is not {(TIME_STEPS, SUBCARRIERS)}")
    header = mat.get("__header__")
    metadata: dict[str, Any] = {
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "session_id": record.session_id,
        "scenario_id": record.scenario_id,
        "scenario_name": SCENARIO_NAMES[record.scenario_id],
        "readme_scenario_name": README_SCENARIO_NAMES[record.scenario_id],
        "scenario_dirname": record.scenario_dirname,
        "participant_id": record.participant_id,
        "activity_code": record.activity_code,
        "trial_id": record.trial_id,
        "dataset_label": record.dataset_label,
        "normalized_label": record.normalized_label,
        "label_verified_by_folder": record.label_verified_by_folder,
        "label_map": "published_folder_codes_not_readme",
        "readme_label_for_code": README_ACTIVITY_CODE_TO_DATASET_LABEL[record.activity_code],
        "source_path": record.path,
        "amplitude_transposed": transposed,
        "phase_present": False,
        "antenna_axis_present": False,
        "license": "CC-BY-4.0",
        "citation": "Wen et al., Ad Hoc Networks, 2026, DOI 10.1016/j.adhoc.2026.104192",
    }
    if header is not None:
        metadata["mat_export_header"] = bytes(header).decode("latin1", errors="replace").strip("\x00")
    return CsiWindow(
        amplitude=amplitude,
        phase=None,
        sample_rate_hz=None,
        timestamp=None,
        subcarriers=SUBCARRIERS,
        antennas=None,
        metadata=metadata,
    )


def sibling_csv(mat_path: Path) -> Path | None:
    """Return the raw CSV that sits next to a ``mat/`` file, if it exists."""
    if mat_path.parent.name != "mat":
        return None
    candidate = mat_path.parent.parent / "csv" / f"{mat_path.stem}.csv"
    return candidate if candidate.is_file() else None


def observe_csv_packet_rate(csv_path: Path) -> dict[str, Any]:
    """Describe one raw capture. This is not a dataset-wide sample rate."""
    with csv_path.open(newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row.get("timestamp")]
    if len(rows) < 2:
        raise DatasetError(f"{csv_path} does not contain two timestamped packets")
    stamps = [
        datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S.%f") for row in rows
    ]
    span_s = (stamps[-1] - stamps[0]).total_seconds()
    if span_s <= 0:
        raise DatasetError(f"{csv_path} timestamps are not increasing")
    lengths = sorted({row.get("len", "") for row in rows})
    return {
        "path": str(csv_path),
        "packet_count": len(rows),
        "span_seconds": span_s,
        "observed_packet_rate_hz": (len(rows) - 1) / span_s,
        "first_timestamp": stamps[0].isoformat(sep=" "),
        "last_timestamp": stamps[-1].isoformat(sep=" "),
        "csi_len_values": lengths,
        "note": "Single-file observation of the raw CSV. The MAT grid is 950 steps and is not this packet count.",
    }
