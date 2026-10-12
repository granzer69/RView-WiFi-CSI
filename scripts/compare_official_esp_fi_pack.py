#!/usr/bin/env python3
"""Train a fresh classical model on ESP-Fi train_amp / test_amp folders (if present).

Authors' published split: scenario 3, participant 1 holdout, typically z-scored CSI.
R-View thesis metrics use session-grouped strategies instead — see docs/esp-fi-official-split-comparison.md.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datasets.esp_fi import discover_trials, load_window
from evaluation.metrics import classification_report_dict
from ingestion.ml_contract import NORMALIZED_LABELS
from models.logreg import train_logreg
from models.rf import train_random_forest


def _find_pack_root(root: Path, folder_name: str) -> Path | None:
    mats = sorted(root.rglob(f"{folder_name}/mat/*.mat"))
    if not mats:
        return None
    pack_roots = sorted({p.parent.parent for p in mats})
    if len(pack_roots) > 1:
        print(f"warning: multiple {folder_name} dirs; using {pack_roots[0]}")
    return pack_roots[0]


def _load_split_tensors(mat_root: Path) -> tuple[np.ndarray, np.ndarray]:
    records = discover_trials(mat_root)
    amplitudes: list[np.ndarray] = []
    labels: list[int] = []
    label_to_id = {name: idx for idx, name in enumerate(NORMALIZED_LABELS)}
    for record in records:
        window = load_window(record)
        amplitudes.append(window.amplitude)
        label_id = label_to_id.get(record.normalized_label)
        if label_id is None:
            raise ValueError(f"unknown label {record.normalized_label}")
        labels.append(label_id)
    return np.stack(amplitudes, axis=0), np.asarray(labels, dtype=np.int64)


def _per_subcarrier_zscore_fit(train: np.ndarray, data: np.ndarray) -> np.ndarray:
    mean = train.mean(axis=(0, 1), keepdims=True)
    std = train.std(axis=(0, 1), keepdims=True)
    std = np.where(std < 1e-8, 1.0, std)
    return (data - mean) / std


def _load_model_config(family: str) -> dict:
    path = ROOT / "configs" / "experiments" / f"v2_{family}_esp_fi.yaml"
    if not path.is_file():
        raise FileNotFoundError(path)
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--data-root",
        type=Path,
        default=ROOT / "data" / "raw" / "esp-fi-har",
    )
    parser.add_argument("--family", choices=("rf", "logreg"), default="rf")
    args = parser.parse_args()

    if not args.data_root.is_dir():
        print(json.dumps({"status": "skipped", "reason": f"data root missing: {args.data_root}"}))
        return

    train_dir = _find_pack_root(args.data_root, "train_amp")
    test_dir = _find_pack_root(args.data_root, "test_amp")
    if train_dir is None or test_dir is None:
        print(
            json.dumps(
                {
                    "status": "skipped",
                    "reason": "train_amp or test_amp mat folders not found under data root",
                    "train_amp_found": train_dir is not None,
                    "test_amp_found": test_dir is not None,
                },
                indent=2,
            )
        )
        return

    train_x, train_y = _load_split_tensors(train_dir)
    test_x, test_y = _load_split_tensors(test_dir)
    train_x = _per_subcarrier_zscore_fit(train_x, train_x)
    test_x = _per_subcarrier_zscore_fit(train_x, test_x)

    cfg = _load_model_config(args.family)
    model_cfg = cfg.get("model") or {}

    if args.family == "rf":
        model = train_random_forest(
            train_x,
            train_y,
            random_state=int(cfg.get("seed", 42)),
            n_estimators=int(model_cfg.get("n_estimators", 200)),
            max_depth=model_cfg.get("max_depth"),
            min_samples_leaf=int(model_cfg.get("min_samples_leaf", 1)),
            class_weight=model_cfg.get("class_weight"),
            n_jobs=int(model_cfg.get("n_jobs", -1)),
        )
        preds = np.asarray(model.predict(test_x), dtype=np.int64)
    else:
        model = train_logreg(train_x, train_y, random_state=int(cfg.get("seed", 42)))
        preds = np.asarray(model.predict(test_x), dtype=np.int64)

    report = classification_report_dict(test_y, preds, labels=NORMALIZED_LABELS)
    out = {
        "status": "ok",
        "family": args.family,
        "train_amp_dir": str(train_dir),
        "test_amp_dir": str(test_dir),
        "train_trials": int(train_x.shape[0]),
        "test_trials": int(test_x.shape[0]),
        "preprocess": "per_subcarrier_zscore_fit_on_train_amp",
        "test_macro_f1": report["macro_f1"],
        "test_accuracy": report["accuracy"],
        "note": "Fresh fit on official folders; not comparable to frozen session-grouped artifacts.",
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
