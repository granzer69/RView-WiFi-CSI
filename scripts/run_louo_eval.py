#!/usr/bin/env python3
"""Run leave-one-user-out classical evaluation (logreg / RF)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from training.louo_experiment import run_louo_classical_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="LOUO classical evaluation on ESP-Fi HAR")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "louo_classical.yaml",
    )
    parser.add_argument("--run-id", type=str, default=None, help="Artifact run directory name")
    parser.add_argument("--artifacts-root", type=Path, default=None)
    parser.add_argument(
        "--fold",
        type=int,
        action="append",
        dest="folds",
        help="Held-out participant id (1-8). Repeat for multiple folds; default all eight.",
    )
    parser.add_argument(
        "--family",
        choices=("logreg", "rf"),
        action="append",
        dest="families",
        help="Model family to train (default: both from config).",
    )
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    if args.run_id:
        config["run_id"] = args.run_id
    artifacts_root = args.artifacts_root or ROOT / config.get("artifacts", {}).get("root", "artifacts/louo")

    manifest = run_louo_classical_experiment(
        config,
        artifacts_root=artifacts_root,
        families=args.families,
        folds=args.folds,
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
