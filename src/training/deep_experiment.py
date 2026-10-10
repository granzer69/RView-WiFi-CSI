"""Run PyTorch CNN / GRU experiments on ESP-Fi."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from evaluation.metrics import classification_report_dict
from models.cnn1d import train_cnn1d
from models.gru import train_gru
from preprocessing.pipeline import PreprocessConfig
from training.esp_fi import assignment_sha256, load_esp_fi_split_bundle
from training.experiment import _git_commit


def _run_deep_strategy(
    root: Path,
    artifacts_dir: Path,
    *,
    strategy: str,
    seed: int,
    preprocess_config: PreprocessConfig,
    model_params: dict[str, Any],
    dataset_config: dict[str, Any],
    train_fn: Callable[..., Any],
    model_label: str,
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

    device = str(model_params.get("device", "cpu"))
    common = {
        "random_state": seed,
        "epochs": int(model_params.get("epochs", 8)),
        "batch_size": int(model_params.get("batch_size", 32)),
        "learning_rate": float(model_params.get("learning_rate", 1e-3)),
        "device": device,
        "extra_config": {
            "split_strategy": strategy,
            "dataset_id": dataset_config.get("dataset_id"),
            "preprocess": preprocess_config.to_dict(),
        },
    }
    if model_label == "gru":
        common["hidden_size"] = int(model_params.get("hidden_size", 64))

    model = train_fn(train_x, train_y, val_x, val_y, **common)

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


def _run_deep_experiment(
    config: dict[str, Any],
    *,
    artifacts_root: Path,
    experiment_name: str,
    train_fn: Callable[..., Any],
    model_label: str,
) -> dict[str, Any]:
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
        strategy_results[strategy] = _run_deep_strategy(
            root,
            artifacts_dir,
            strategy=strategy,
            seed=seed,
            preprocess_config=preprocess,
            model_params=model_params,
            dataset_config=dataset,
            train_fn=train_fn,
            model_label=model_label,
            verify_assignment_hash=bool(config.get("verify_assignment_hash", True)),
        )

    manifest = {
        "experiment": config.get("name", experiment_name),
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


def run_cnn1d_experiment(config: dict[str, Any], *, artifacts_root: Path) -> dict[str, Any]:
    return _run_deep_experiment(
        config,
        artifacts_root=artifacts_root,
        experiment_name="v2_cnn1d",
        train_fn=train_cnn1d,
        model_label="cnn",
    )


def run_gru_experiment(config: dict[str, Any], *, artifacts_root: Path) -> dict[str, Any]:
    return _run_deep_experiment(
        config,
        artifacts_root=artifacts_root,
        experiment_name="v2_gru",
        train_fn=train_gru,
        model_label="gru",
    )
