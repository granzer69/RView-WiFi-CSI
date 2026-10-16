"""Train classical models on LOUO folds and write artifacts."""

from __future__ import annotations

import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from evaluation.metrics import classification_report_dict
from models.logreg import train_logreg
from models.rf import train_random_forest
from preprocessing.pipeline import PreprocessConfig
from training.esp_fi import assignment_sha256
from training.louo import load_esp_fi_louo_bundle, louo_strategy_name


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


def _run_classical_fold(
    root: Path,
    artifacts_dir: Path,
    *,
    family: str,
    held_out_participant: int,
    seed: int,
    preprocess_config: PreprocessConfig,
    model_params: dict[str, Any],
    dataset_config: dict[str, Any],
    verify_assignment_hash: bool,
) -> dict[str, Any]:
    started = time.perf_counter()
    bundle = load_esp_fi_louo_bundle(
        root,
        held_out_participant=held_out_participant,
        seed=seed,
        preprocess=preprocess_config,
        verify_assignment_hash=verify_assignment_hash,
    )
    train_x, train_y = bundle.amplitudes_and_labels("train")
    val_x, val_y = bundle.amplitudes_and_labels("val")
    test_x, test_y = bundle.amplitudes_and_labels("test")

    strategy = louo_strategy_name(held_out_participant)
    extra_config = {
        "split_strategy": strategy,
        "held_out_participant": held_out_participant,
        "dataset_id": dataset_config.get("dataset_id"),
        "preprocess": preprocess_config.to_dict(),
    }

    if family == "logreg":
        model = train_logreg(
            train_x,
            train_y,
            random_state=seed,
            max_iter=int(model_params.get("max_iter", 2000)),
            C=float(model_params.get("C", 1.0)),
            class_weight=model_params.get("class_weight"),
            extra_config=extra_config,
        )
    elif family == "rf":
        model = train_random_forest(
            train_x,
            train_y,
            random_state=seed,
            n_estimators=int(model_params.get("n_estimators", 200)),
            max_depth=model_params.get("max_depth"),
            min_samples_leaf=int(model_params.get("min_samples_leaf", 1)),
            class_weight=model_params.get("class_weight"),
            n_jobs=int(model_params.get("n_jobs", -1)),
            extra_config=extra_config,
        )
    else:
        raise ValueError(f"unsupported LOUO family {family!r}")

    val_metrics = model.evaluate(val_x, val_y)
    test_metrics = model.evaluate(test_x, test_y)
    train_metrics = classification_report_dict(train_y, model.predict(train_x))

    fold_dir = artifacts_dir / f"user_{held_out_participant}"
    fold_dir.mkdir(parents=True, exist_ok=True)
    model.save(fold_dir)

    metrics_payload = {
        "split_strategy": strategy,
        "held_out_participant": held_out_participant,
        "assignment_sha256": assignment_sha256(bundle.assignment),
        "counts": bundle.assignment.counts(),
        "train": train_metrics,
        "val": val_metrics,
        "test": test_metrics,
        "training_duration_seconds": time.perf_counter() - started,
    }
    (fold_dir / "metrics.json").write_text(json.dumps(metrics_payload, indent=2) + "\n")
    return metrics_payload


def run_louo_classical_experiment(
    config: dict[str, Any],
    *,
    artifacts_root: Path,
    families: list[str] | None = None,
    folds: list[int] | None = None,
) -> dict[str, Any]:
    dataset = config["dataset"]
    root = Path(dataset["root"])
    seed = int(config.get("seed", 42))
    preprocess = PreprocessConfig(**config.get("preprocess", {}))
    run_id = config.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    verify = bool(config.get("verify_assignment_hash", True))
    family_list = families or list(config.get("families", ("logreg", "rf")))
    fold_list = folds or list(config.get("folds", range(1, 9)))

    results: dict[str, Any] = {}
    for family in family_list:
        model_params = dict(config.get(family, config.get("model", {})))
        family_dir = artifacts_root / f"louo_{family}" / run_id
        family_dir.mkdir(parents=True, exist_ok=True)
        fold_results: dict[str, Any] = {}
        for held_out in fold_list:
            fold_results[str(held_out)] = _run_classical_fold(
                root,
                family_dir,
                family=family,
                held_out_participant=int(held_out),
                seed=seed,
                preprocess_config=preprocess,
                model_params=model_params,
                dataset_config=dataset,
                verify_assignment_hash=verify,
            )
        manifest = {
            "experiment": config.get("name", "louo_classical"),
            "evaluation_protocol": "leave_one_user_out",
            "run_id": run_id,
            "family": family,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "git_commit": _git_commit(),
            "dataset": dataset,
            "seed": seed,
            "preprocess": preprocess.to_dict(),
            "model": model_params,
            "folds": fold_results,
            "label_map": "published_folder_codes_not_readme",
            "label_note": dataset.get("label_note"),
        }
        (family_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        results[family] = manifest
    return {"run_id": run_id, "families": results}
