"""Experiment workbench: validate configs, async runs, filesystem registry."""

from __future__ import annotations

import json
import threading
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import yaml

from common.errors import DatasetError
from preprocessing.pipeline import PreprocessConfig
<<<<<<< HEAD
from training.deep_experiment import run_cnn1d_experiment, run_gru_experiment, run_tcn_experiment
from training.experiment import (
    run_gbdt_experiment,
    run_logreg_experiment,
    run_mlp_experiment,
    run_rf_experiment,
)

Family = Literal["logreg", "rf", "mlp", "gbdt", "cnn1d", "gru", "tcn"]
SplitStrategy = Literal["in_domain", "cross_user", "cross_environment"]

SUPPORTED_FAMILIES: tuple[Family, ...] = ("logreg", "rf", "mlp", "gbdt", "cnn1d", "gru", "tcn")
=======
from training.deep_experiment import run_cnn1d_experiment, run_gru_experiment
from training.experiment import run_logreg_experiment, run_rf_experiment

Family = Literal["logreg", "rf", "cnn1d", "gru"]
SplitStrategy = Literal["in_domain", "cross_user", "cross_environment"]

SUPPORTED_FAMILIES: tuple[Family, ...] = ("logreg", "rf", "cnn1d", "gru")
>>>>>>> origin/main
SUPPORTED_STRATEGIES: tuple[SplitStrategy, ...] = ("in_domain", "cross_user", "cross_environment")

HYPERPARAM_SCHEMA: dict[str, dict[str, Any]] = {
    "logreg": {
        "C": {"type": "float", "default": 1.0, "min": 1e-4, "max": 100.0},
        "max_iter": {"type": "int", "default": 2000, "min": 100, "max": 10000},
        "class_weight": {"type": "string_or_null", "default": None},
    },
    "rf": {
        "n_estimators": {"type": "int", "default": 200, "min": 10, "max": 2000},
        "max_depth": {"type": "int_or_null", "default": None, "min": 1, "max": 200},
        "min_samples_leaf": {"type": "int", "default": 1, "min": 1, "max": 50},
        "class_weight": {"type": "string_or_null", "default": None},
    },
    "cnn1d": {
        "epochs": {"type": "int", "default": 8, "min": 1, "max": 100},
        "batch_size": {"type": "int", "default": 32, "min": 4, "max": 256},
        "learning_rate": {"type": "float", "default": 1e-3, "min": 1e-6, "max": 1.0},
        "device": {"type": "string", "default": "cpu"},
    },
    "gru": {
        "epochs": {"type": "int", "default": 8, "min": 1, "max": 100},
        "batch_size": {"type": "int", "default": 32, "min": 4, "max": 256},
        "learning_rate": {"type": "float", "default": 1e-3, "min": 1e-6, "max": 1.0},
        "hidden_size": {"type": "int", "default": 64, "min": 8, "max": 512},
        "device": {"type": "string", "default": "cpu"},
    },
<<<<<<< HEAD
    "mlp": {
        "hidden_layer_sizes": {"type": "int_list", "default": [128, 64]},
        "max_iter": {"type": "int", "default": 300, "min": 50, "max": 2000},
        "alpha": {"type": "float", "default": 1e-4, "min": 1e-8, "max": 10.0},
        "learning_rate_init": {"type": "float", "default": 1e-3, "min": 1e-6, "max": 1.0},
    },
    "gbdt": {
        "max_iter": {"type": "int", "default": 200, "min": 10, "max": 2000},
        "max_depth": {"type": "int_or_null", "default": 8, "min": 1, "max": 64},
        "learning_rate": {"type": "float", "default": 0.1, "min": 1e-4, "max": 1.0},
        "min_samples_leaf": {"type": "int", "default": 20, "min": 1, "max": 200},
    },
    "tcn": {
        "epochs": {"type": "int", "default": 8, "min": 1, "max": 100},
        "batch_size": {"type": "int", "default": 32, "min": 4, "max": 256},
        "learning_rate": {"type": "float", "default": 1e-3, "min": 1e-6, "max": 1.0},
        "channels": {"type": "int", "default": 64, "min": 16, "max": 256},
        "device": {"type": "string", "default": "cpu"},
    },
=======
>>>>>>> origin/main
}

PREPROCESS_SCHEMA = {
    "clip_mad": {"type": "bool", "default": False},
    "mad_k": {"type": "float", "default": 5.0},
    "normalize": {"type": "string", "default": "none", "choices": ["none", "per_window_zscore"]},
    "window_length": {"type": "int_or_null", "default": None},
    "hop": {"type": "int_or_null", "default": None},
}

_REGISTRY_LOCK = threading.Lock()
_ACTIVE_RUNS = 0
_MAX_CONCURRENT = 1


def workbench_root(repo_root: Path) -> Path:
    return repo_root / "artifacts" / "workbench"


def registry_path(repo_root: Path) -> Path:
    return workbench_root(repo_root) / "registry.json"


def experiment_schema() -> dict[str, Any]:
    return {
        "families": list(SUPPORTED_FAMILIES),
        "split_strategies": list(SUPPORTED_STRATEGIES),
        "hyperparameters": HYPERPARAM_SCHEMA,
        "preprocess": PREPROCESS_SCHEMA,
        "defaults": {
            "seed": 42,
            "verify_assignment_hash": True,
            "strategies": list(SUPPORTED_STRATEGIES),
        },
        "artifacts_root": "artifacts/workbench/<family>/<run_id>/",
        "baseline_note": "Frozen v2_* baseline run IDs under artifacts/v2_* are never written by the workbench.",
    }


def _load_registry(repo_root: Path) -> dict[str, Any]:
    path = registry_path(repo_root)
    if not path.is_file():
        return {"runs": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_registry(repo_root: Path, payload: dict[str, Any]) -> None:
    path = registry_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def list_runs(repo_root: Path) -> list[dict[str, Any]]:
    with _REGISTRY_LOCK:
        return list(_load_registry(repo_root).get("runs", []))


def get_run(repo_root: Path, run_id: str) -> dict[str, Any] | None:
    for item in list_runs(repo_root):
        if item.get("run_id") == run_id:
            return item
    return None


def validate_run_request(
    body: dict[str, Any],
    *,
    data_root: Path,
    repo_root: Path,
) -> dict[str, Any]:
    family = body.get("family")
    if family not in SUPPORTED_FAMILIES:
        raise DatasetError(f"unsupported family: {family}")
    strategies = body.get("strategies") or list(SUPPORTED_STRATEGIES)
    for strategy in strategies:
        if strategy not in SUPPORTED_STRATEGIES:
            raise DatasetError(f"unsupported split strategy: {strategy}")
    seed = int(body.get("seed", 42))
    preprocess_raw = body.get("preprocess") or {}
    preprocess = PreprocessConfig(**{**{k: v["default"] for k, v in PREPROCESS_SCHEMA.items()}, **preprocess_raw})
    model_params = _validate_hyperparams(family, body.get("model") or {})
    if not data_root.is_dir():
        raise DatasetError(f"ESP-Fi data root not found: {data_root}")
    run_id = body.get("run_id") or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = body.get("name") or f"workbench_{family}"
    dataset_root = body.get("dataset_root")
    if dataset_root:
        root = Path(dataset_root)
        if not root.is_absolute():
            root = repo_root / root
    else:
        root = data_root
    config = {
        "name": name,
        "seed": seed,
        "verify_assignment_hash": bool(body.get("verify_assignment_hash", True)),
        "dataset": {
            "dataset_id": "esp-fi-har",
            "root": str(root),
            "label_map": "published_folder_codes_not_readme",
            "label_note": body.get(
                "label_note",
                "Scenarios 1, 2, and 4 have no class folders; labels follow the scenario-3 folder map "
                "(INFERRED — NOT INDEPENDENTLY VERIFIED).",
            ),
        },
        "preprocess": preprocess.to_dict(),
        "model": model_params,
        "strategies": list(strategies),
        "run_id": run_id,
    }
    artifacts_root = workbench_root(repo_root) / family
    return {
        "config": config,
        "family": family,
        "run_id": run_id,
        "artifacts_root": artifacts_root,
    }


def _validate_hyperparams(family: Family, params: dict[str, Any]) -> dict[str, Any]:
    schema = HYPERPARAM_SCHEMA[family]
    cleaned: dict[str, Any] = {}
    for key, spec in schema.items():
        if key in params:
            cleaned[key] = params[key]
        else:
            cleaned[key] = spec["default"]
    unknown = set(params) - set(schema)
    if unknown:
        raise DatasetError(f"unsupported hyperparameters for {family}: {sorted(unknown)}")
    return cleaned


def preview_config(validated: dict[str, Any]) -> dict[str, Any]:
    return {
        "family": validated["family"],
        "run_id": validated["run_id"],
        "artifacts_dir": str(validated["artifacts_root"] / validated["run_id"]),
        "config": validated["config"],
        "cli_export": _cli_command(validated),
    }


def _cli_command(validated: dict[str, Any]) -> str:
    family = validated["family"]
    script = {
        "logreg": "scripts/train_logreg.py",
        "rf": "scripts/train_rf.py",
<<<<<<< HEAD
        "mlp": "scripts/train_mlp.py",
        "gbdt": "scripts/train_gbdt.py",
        "cnn1d": "scripts/train_cnn1d.py",
        "gru": "scripts/train_gru.py",
        "tcn": "scripts/train_tcn.py",
=======
        "cnn1d": "scripts/train_cnn1d.py",
        "gru": "scripts/train_gru.py",
>>>>>>> origin/main
    }[family]
    run_id = validated["run_id"]
    root = validated["artifacts_root"]
    return (
        f"python3 {script} --run-id {run_id} "
        f"--artifacts-root {root} --config <exported_config.yaml>"
    )


def export_config_yaml(validated: dict[str, Any]) -> str:
    payload = {
        **validated["config"],
        "artifacts": {"root": str(validated["artifacts_root"])},
    }
    return yaml.safe_dump(payload, sort_keys=False)


def _execute_run(validated: dict[str, Any]) -> dict[str, Any]:
    family = validated["family"]
    config = validated["config"]
    artifacts_root = validated["artifacts_root"]
    runners = {
        "logreg": run_logreg_experiment,
        "rf": run_rf_experiment,
<<<<<<< HEAD
        "mlp": run_mlp_experiment,
        "gbdt": run_gbdt_experiment,
        "cnn1d": run_cnn1d_experiment,
        "gru": run_gru_experiment,
        "tcn": run_tcn_experiment,
=======
        "cnn1d": run_cnn1d_experiment,
        "gru": run_gru_experiment,
>>>>>>> origin/main
    }
    return runners[family](config, artifacts_root=artifacts_root)


def start_run_async(
    repo_root: Path,
    validated: dict[str, Any],
    *,
    on_complete: Any | None = None,
) -> dict[str, Any]:
    global _ACTIVE_RUNS
    with _REGISTRY_LOCK:
        if _ACTIVE_RUNS >= _MAX_CONCURRENT:
            raise DatasetError("another experiment run is already in progress (concurrency limit 1)")
        _ACTIVE_RUNS += 1
        entry = {
            "run_id": validated["run_id"],
            "family": validated["family"],
            "status": "queued",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "artifacts_dir": str(validated["artifacts_root"] / validated["run_id"]),
            "config_path": str(validated["artifacts_root"] / validated["run_id"] / "workbench_config.yaml"),
            "error": None,
        }
        registry = _load_registry(repo_root)
        registry.setdefault("runs", []).append(entry)
        _save_registry(repo_root, registry)

    def worker() -> None:
        global _ACTIVE_RUNS
        run_id = validated["run_id"]
        try:
            _update_run_status(repo_root, run_id, "running")
            out_dir = validated["artifacts_root"] / run_id
            out_dir.mkdir(parents=True, exist_ok=True)
            (out_dir / "workbench_config.yaml").write_text(
                export_config_yaml(validated), encoding="utf-8"
            )
            manifest = _execute_run(validated)
            (out_dir / "workbench_manifest.json").write_text(
                json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
            )
            _update_run_status(repo_root, run_id, "completed", manifest=manifest)
        except Exception as exc:  # noqa: BLE001
            _update_run_status(
                repo_root,
                run_id,
                "failed",
                error=f"{exc}\n{traceback.format_exc()}",
            )
        finally:
            with _REGISTRY_LOCK:
                _ACTIVE_RUNS = max(0, _ACTIVE_RUNS - 1)
            if on_complete:
                on_complete()

    thread = threading.Thread(target=worker, name=f"workbench-{validated['run_id']}", daemon=True)
    thread.start()
    return entry


def _update_run_status(
    repo_root: Path,
    run_id: str,
    status: str,
    *,
    error: str | None = None,
    manifest: dict[str, Any] | None = None,
) -> None:
    with _REGISTRY_LOCK:
        registry = _load_registry(repo_root)
        for item in registry.get("runs", []):
            if item.get("run_id") == run_id:
                item["status"] = status
                item["updated_at"] = datetime.now(timezone.utc).isoformat()
                if error:
                    item["error"] = error
                if manifest:
                    item["manifest_summary"] = {
                        strategy: manifest["strategies"][strategy]["test"].get("macro_f1")
                        for strategy in manifest.get("strategies", {})
                    }
                break
        _save_registry(repo_root, registry)


def load_run_metrics(repo_root: Path, run_id: str, strategy: str) -> dict[str, Any]:
    run = get_run(repo_root, run_id)
    if not run:
        raise DatasetError(f"unknown run_id: {run_id}")
    metrics_path = Path(run["artifacts_dir"]) / strategy / "metrics.json"
    if not metrics_path.is_file():
        raise DatasetError(f"metrics missing for {run_id}/{strategy}")
    return json.loads(metrics_path.read_text(encoding="utf-8"))


def compare_runs(repo_root: Path, run_ids: list[str], strategy: str) -> dict[str, Any]:
    if strategy not in SUPPORTED_STRATEGIES:
        raise DatasetError(f"unsupported strategy: {strategy}")
    rows = []
    assignment_hashes: set[str] = set()
    for run_id in run_ids:
        run = get_run(repo_root, run_id)
        if not run:
            raise DatasetError(f"unknown run_id: {run_id}")
        metrics = load_run_metrics(repo_root, run_id, strategy)
        assignment_hashes.add(metrics.get("assignment_sha256", ""))
        rows.append(
            {
                "run_id": run_id,
                "family": run.get("family"),
                "status": run.get("status"),
                "test_macro_f1": metrics.get("test", {}).get("macro_f1"),
                "test_accuracy": metrics.get("test", {}).get("accuracy"),
            }
        )
    compatible = len(assignment_hashes) <= 1
    return {
        "strategy": strategy,
        "compatible_splits": compatible,
        "assignment_sha256_values": sorted(assignment_hashes),
        "runs": rows,
    }
