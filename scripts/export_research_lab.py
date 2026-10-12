#!/usr/bin/env python3
"""Export generalization research JSON for the frontend and reports."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from research.experiment_record import ExperimentRecord, ExperimentStatus
from research.generalization import (
    BASELINE_RUN_IDS,
    EXTENDED_RUN_IDS,
    build_generalization_rows,
    extended_metrics_entries,
)


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def build_payload(repo_root: Path) -> dict:
    entries = extended_metrics_entries(repo_root)
    models = build_generalization_rows(entries)
    git_sha = _git_sha()
    timestamp = datetime.now(timezone.utc).isoformat()
    baseline_run_ids = {**BASELINE_RUN_IDS, **EXTENDED_RUN_IDS}

    experiments = []
    for entry in entries:
        experiments.append(
            ExperimentRecord(
                run_id=entry["run_id"],
                timestamp=timestamp,
                git_sha=git_sha,
                split_strategy=entry["split_strategy"],
                assignment_sha256=entry.get("assignment_sha256"),
                artifact_path=entry["artifact_dir"],
                family=entry["family"],
                status=ExperimentStatus.complete,
            ).to_dict()
        )

    return {
        "dataset_id": "esp-fi-har",
        "generated_at": timestamp,
        "git_sha": git_sha,
        "baseline_run_ids": baseline_run_ids,
        "provenance": {
            "source": "artifacts/v2_*/<run_id>/<strategy>/metrics.json",
            "note": (
                "Frozen baseline run IDs for logreg/rf/cnn1d/gru; extended families "
                f"{list(EXTENDED_RUN_IDS.keys())} pinned in EXTENDED_RUN_IDS when present."
            ),
        },
        "strategies": list({row["split_strategy"] for row in models}),
        "models": models,
        "experiments": experiments,
        "integrity_note": (
            "Offline ESP-Fi holdout evaluation. Generalization gaps compare each split "
            "strategy to the same family's in-domain test macro-F1."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--frontend-out",
        type=Path,
        default=ROOT / "frontend" / "public" / "research" / "generalization.json",
    )
    parser.add_argument(
        "--report-out",
        type=Path,
        default=ROOT / "reports" / "research" / "generalization_report.json",
    )
    args = parser.parse_args()

    payload = build_payload(ROOT)
    for path in (args.frontend_out, args.report_out):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} ({len(payload['models'])} models)")


if __name__ == "__main__":
    main()
