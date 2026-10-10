#!/usr/bin/env python3
"""Export session manifest and optional trial amplitude JSON for frontend replay."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from datasets.esp_fi import SCENARIO_NAMES, discover_trials, load_window
from simulator.sources.dataset_replay import session_meta_from_window_metadata

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ROOT = REPO_ROOT / "data" / "raw" / "esp-fi-har"
DEFAULT_OUT = REPO_ROOT / "frontend" / "public" / "replay"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument(
        "--export-trials",
        nargs="*",
        default=["1-1-2-1", "1-1-1-1"],
        help="session_ids to export full amplitude grids as JSON",
    )
    parser.add_argument(
        "--all-trials",
        action="store_true",
        help="export every discovered session (large; use for full offline replay)",
    )
    parser.add_argument("--nominal-replay-hz", type=float, default=95.0)
    args = parser.parse_args()

    records = discover_trials(args.root)
    sessions = []
    for record in sorted(records, key=lambda r: r.session_id):
        sessions.append(
            {
                "session_id": record.session_id,
                "scenario_id": record.scenario_id,
                "scenario_name": SCENARIO_NAMES[record.scenario_id],
                "environment_id": SCENARIO_NAMES[record.scenario_id],
                "participant_id": record.participant_id,
                "activity_code": record.activity_code,
                "normalized_label": record.normalized_label,
                "dataset_label": record.dataset_label,
                "label_verified_by_folder": record.label_verified_by_folder,
            }
        )

    args.out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "dataset_id": "esp-fi-har",
        "source": "dataset_replay",
        "nominal_replay_hz": args.nominal_replay_hz,
        "timing_note": "Matrix index replay at nominal Hz — not verified MAT capture clock.",
        "session_count": len(sessions),
        "sessions": sessions,
        "default_session_id": "1-1-2-1",
    }
    manifest_path = args.out / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {manifest_path} ({len(sessions)} sessions)")

    trials_dir = args.out / "trials"
    trials_dir.mkdir(parents=True, exist_ok=True)
    by_id = {r.session_id: r for r in records}
    export_ids = sorted(by_id) if args.all_trials else args.export_trials
    for session_id in export_ids:
        record = by_id.get(session_id)
        if record is None:
            print(f"skip missing trial {session_id}")
            continue
        window = load_window(record)
        meta = session_meta_from_window_metadata(window.metadata)
        payload = {
            "session_id": session_id,
            "meta": meta,
            "time_steps": int(window.amplitude.shape[0]),
            "subcarriers": int(window.amplitude.shape[1]),
            "amplitude": window.amplitude.tolist(),
            "data_tier": "real",
        }
        trial_path = trials_dir / f"{session_id}.json"
        trial_path.write_text(json.dumps(payload), encoding="utf-8")
        print(f"wrote {trial_path}")


if __name__ == "__main__":
    main()
