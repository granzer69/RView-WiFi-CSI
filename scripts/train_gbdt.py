#!/usr/bin/env python3
"""Train the V2 histogram GBDT baseline on ESP-Fi."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from training.experiment import run_gbdt_experiment


def main() -> None:
    parser = argparse.ArgumentParser(description="Train HistGradientBoosting on ESP-Fi HAR")
    parser.add_argument(
        "--config",
        type=Path,
        default=ROOT / "configs" / "experiments" / "v2_gbdt_esp_fi.yaml",
    )
    parser.add_argument("--run-id", type=str, default=None, help="Override artifact run directory name")
    parser.add_argument("--artifacts-root", type=Path, default=None)
    args = parser.parse_args()

    config = yaml.safe_load(args.config.read_text())
    if args.run_id:
        config["run_id"] = args.run_id
    artifacts_root = args.artifacts_root or ROOT / config.get("artifacts", {}).get("root", "artifacts/v2_gbdt")
    manifest = run_gbdt_experiment(config, artifacts_root=artifacts_root)
    print(
        json.dumps(
            {
                "run_id": manifest["run_id"],
                "artifacts": str(artifacts_root / manifest["run_id"]),
                "test_accuracy": {
                    strategy: manifest["strategies"][strategy]["test"]["accuracy"]
                    for strategy in manifest["strategies"]
                },
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
