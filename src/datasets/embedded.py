"""Reader for the Embedded WiFi Sensing activity files.

The files were downloaded for inspection. Volunteer consent in the paper
authorizes academic research use. The repository code is MIT. Those are
not a commercial-use grant for the recordings. Experiment and publication
entry points call :func:`assert_cleared_for_experiment`, which stays closed.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from common.errors import DatasetError, LicenseError

LICENSE_STATUS = "academic_consent_only_not_cleared_for_experiments"
N_SUBCARRIERS = 64
ACTIVITY_LABELS = {
    "FA": "falling",
    "GU": "get_up",
    "LD": "lying_down",
    "SD": "sitting_down",
    "WA": "walking",
}


def assert_cleared_for_experiment() -> None:
    raise LicenseError(
        "Embedded WiFi Sensing HAR is not cleared for experiments or publication. "
        "Local files may be inspected. The paper's consent text is academic research, "
        "and this project does not assume commercial rights. "
        f"Status: {LICENSE_STATUS}."
    )


def read_raw_capture(path: Path) -> tuple[np.ndarray, np.ndarray]:
    """Return timestamps and complex CSI shaped (packets, 64).

    The README states the row is a microcontroller timestamp followed by
    imaginary/real pairs for 64 subcarriers. Null and pilot bins are kept.
    """
    timestamps: list[int] = []
    frames: list[list[complex]] = []
    for line_number, line in enumerate(path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        cells = line.split(",")
        if len(cells) != 1 + N_SUBCARRIERS * 2:
            raise DatasetError(
                f"{path}:{line_number} has {len(cells)} columns, expected {1 + N_SUBCARRIERS * 2}"
            )
        timestamps.append(int(cells[0]))
        values = [int(cell) for cell in cells[1:]]
        frames.append(
            [
                values[2 * index + 1] + 1j * values[2 * index]
                for index in range(N_SUBCARRIERS)
            ]
        )
    if not frames:
        raise DatasetError(f"{path} is empty")
    return np.asarray(timestamps, dtype=np.int64), np.asarray(frames, dtype=np.complex128)


def census(activity_root: Path) -> dict[str, object]:
    """Count local activity files. This does not clear the dataset for experiments."""
    if not activity_root.is_dir():
        raise DatasetError(f"activity directory not found: {activity_root}")
    files = sorted(path for path in activity_root.rglob("*.txt") if path.is_file())
    if not files:
        raise DatasetError(f"no activity text files under {activity_root}")
    by_activity: dict[str, int] = {code: 0 for code in ACTIVITY_LABELS}
    by_subject: dict[str, int] = {}
    for path in files:
        meta = parse_activity_path(path)
        by_activity[meta["activity_code"]] += 1
        by_subject[meta["subject_id"]] = by_subject.get(meta["subject_id"], 0) + 1
    sample = files[0]
    timestamps, csi = read_raw_capture(sample)
    return {
        "license_status": LICENSE_STATUS,
        "experiment_use": "blocked",
        "file_count": len(files),
        "activity_counts": by_activity,
        "subject_ids": sorted(by_subject, key=lambda name: int(name[1:])),
        "files_per_subject": {subject: by_subject[subject] for subject in sorted(by_subject, key=lambda name: int(name[1:]))},
        "sample_file": str(sample),
        "sample_packets": int(timestamps.shape[0]),
        "sample_subcarriers": int(csi.shape[1]),
        "note": (
            "Inspection only. Volunteer consent in the paper is academic research. "
            "Commercial rights are not assumed. NumPy arrays shipped beside Activity/ "
            "are not treated as raw CSI."
        ),
    }


def parse_activity_path(path: Path) -> dict[str, str]:
    """Read ``Activity/<code>/s<id>/file.txt`` metadata. Does not clear experiments."""
    activity_code = path.parent.parent.name
    subject = path.parent.name
    if activity_code not in ACTIVITY_LABELS:
        raise DatasetError(f"unexpected activity directory {activity_code!r} in {path}")
    if not subject.startswith("s") or not subject[1:].isdigit():
        raise DatasetError(f"unexpected subject directory {subject!r} in {path}")
    return {
        "activity_code": activity_code,
        "normalized_label": ACTIVITY_LABELS[activity_code],
        "subject_id": subject,
        "session_id": path.stem,
        "license_status": LICENSE_STATUS,
    }
