"""Run one logistic-regression experiment and write artifacts."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.metrics import classification_report_dict
from models.logreg import LogRegHarModel, train_logreg
from training.esp_fi import EspFiSplitBundle, assignment_sha256, bundle_summary, load_esp_fi_split_bundle
from preprocessing.pipeline import PreprocessConfig


def _git_commit() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def run_logreg_strategy(
    root: Path,
    artifacts_dir: Path,
    *,
    strategy: str,
    seed: int,
    preprocess_config: PreprocessConfig,
    model_params: dict[str, Any],
    dataset_config: dict[str, Any],
    verify_assignment_hash: bool = True,
) -> dict[str, Any]:
    started = time.perf_counter()
    bundle = load_esp_fi_split_bundle(
        root,
        strategy=strategy,
        seed=seed,
        preprocess=preprocess_config,
        verify_assignment_hash=verify_assignment_hash,
    )
    train_x, train_y = bundle.amplitudes_and_labels("train")
    val_x, val_y = bundle.amplitudes_and_labels("val")
    test_x, test_y = bundle.amplitudes_and_labels("test")

    model = train_logreg(
        train_x,
        train_y,
        random_state=seed,
        max_iter=int(model_params.get("max_iter", 2000)),
        C=float(model_params.get("C", 1.0)),
        class_weight=model_params.get("class_weight"),
        extra_config={
            "split_strategy": strategy,
            "dataset_id": dataset_config.get("dataset_id"),
            "preprocess": preprocess_config.to_dict(),
        },
    )

    val_metrics = model.evaluate(val_x, val_y)
    test_metrics = model.evaluate(test_x, test_y)
    train_metrics = classification_report_dict(train_y, model.predict(train_x))

    strategy_dir = artifacts_dir / strategy
    model.save(strategy_dir)
    metrics_payload = {
        "split_strategy": strategy,
        "assignment_sha256": assignment_sha256(bundle.assignment),
        "counts": bundle.assignment.counts(),
        "train": train_metrics,
        "val": val_metrics,
        "test": test_metrics,
        "training_duration_seconds": time.perf_counter() - started,
    }
    (strategy_dir / "metrics.json").write_text(json.dumps(metrics_payload, indent=2) + "\n")
    return metrics_payload


def run_logreg_experiment(config: dict[str, Any], *, artifacts_root: Path) -> dict[str, Any]:
    dataset = config["dataset"]
    root = Path(dataset["root"])
    seed = int(config.get("seed", 42))
    preprocess = PreprocessConfig(**config.get("preprocess", {}))
    model_params = dict(config.get("model", {}))
    run_id = config.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    artifacts_dir = artifacts_root / run_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    strategy_results: dict[str, Any] = {}
    for strategy in config["strategies"]:
        strategy_results[strategy] = run_logreg_strategy(
            root,
            artifacts_dir,
            strategy=strategy,
            seed=seed,
            preprocess_config=preprocess,
            model_params=model_params,
            dataset_config=dataset,
            verify_assignment_hash=bool(config.get("verify_assignment_hash", True)),
        )

    manifest = {
        "experiment": config.get("name", "v2_logreg_baseline"),
        "run_id": run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "git_commit": _git_commit(),
        "dataset": dataset,
        "seed": seed,
        "preprocess": preprocess.to_dict(),
        "model": model_params,
        "strategies": strategy_results,
        "label_map": "published_folder_codes_not_readme",
        "label_note": dataset.get("label_note"),
    }
    (artifacts_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
