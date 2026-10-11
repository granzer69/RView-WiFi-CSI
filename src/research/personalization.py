"""In-domain personalization A/B (global frozen model vs participant calibrator)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

import numpy as np
from sklearn.linear_model import LogisticRegression

from evaluation.metrics import classification_report_dict
from ingestion.ml_contract import NORMALIZED_LABELS, HarSample
from models.logreg import LogRegHarModel
from models.rf import RandomForestHarModel
from research.generalization import BASELINE_RUN_IDS, baseline_artifact_dir
from research.leakage import calib_eval_session_sets_disjoint
from research.participant import check_esp_fi_available, esp_fi_data_root
from training.esp_fi import load_esp_fi_split_bundle

PersonalizationStatus = Literal["completed", "blocked", "not_evaluated", "failed"]

SUPPORTED_FAMILIES = ("logreg", "rf")
STRATEGY = "in_domain"
CALIBRATOR_SEED = 42


@dataclass(frozen=True)
class ClassicalBackend:
    """Wrapper for logreg or rf baseline with classical features."""

    model: LogRegHarModel | RandomForestHarModel

    @property
    def label_names(self) -> tuple[str, ...]:
        return self.model.label_names

    def features(self, amplitudes: np.ndarray) -> np.ndarray:
        return self.model.feature_extractor.transform(amplitudes)

    def predict(self, amplitudes: np.ndarray) -> np.ndarray:
        return np.asarray(self.model.predict(amplitudes), dtype=np.int64)


def _load_classical_backend(family: str, artifact_dir: Path) -> ClassicalBackend:
    if family == "logreg":
        return ClassicalBackend(LogRegHarModel.load(artifact_dir))
    if family == "rf":
        return ClassicalBackend(RandomForestHarModel.load(artifact_dir))
    raise ValueError(f"unsupported family for personalization: {family}")


def _samples_for_user(
    samples: tuple[HarSample, ...],
    user_id: int,
    split: str,
) -> list[HarSample]:
    return [s for s in samples if int(s.user_id) == user_id and s.split == split]


def _stack(samples: list[HarSample]) -> tuple[np.ndarray, np.ndarray, set[str]]:
    if not samples:
        raise ValueError("empty sample list")
    amps = np.stack([s.amplitude for s in samples], axis=0)
    labels = np.asarray([s.label_id for s in samples], dtype=np.int64)
    sessions = {s.session_id for s in samples}
    return amps, labels, sessions


def _fit_participant_calibrator(
    features: np.ndarray,
    labels: np.ndarray,
    n_classes: int,
) -> LogisticRegression:
    """Train a small calibrator on one participant's train features only."""
    calibrator = LogisticRegression(
        max_iter=2000,
        random_state=CALIBRATOR_SEED,
        solver="lbfgs",
    )
    calibrator.fit(features, labels)
    return calibrator


def run_in_domain_personalization_ab(
    repo_root: Path,
    *,
    families: tuple[str, ...] = SUPPORTED_FAMILIES,
    verify_assignment_hash: bool = True,
) -> dict[str, Any]:
    """
    Compare global frozen baseline vs participant-specific logistic calibrator.

    Protocol:
    - Split: in_domain only.
    - Per participant: calibration = train-split sessions; evaluation = test-split sessions.
    - Feature extractor and global classifier are frozen from baseline artifacts (trained on full train).
    - Personalization: LogisticRegression fit on participant train features (from frozen extractor).
    - cross_user personalization is not run (blocked).
    """
    availability = check_esp_fi_available(repo_root)
    timestamp = datetime.now(timezone.utc).isoformat()
    if not availability.present:
        return {
            "generated_at": timestamp,
            "status": "blocked",
            "reason": availability.reason,
            "cross_user_personalization": "blocked",
            "in_domain_personalization": "blocked",
        }

    bundle = load_esp_fi_split_bundle(
        esp_fi_data_root(repo_root),
        strategy=STRATEGY,
        verify_assignment_hash=verify_assignment_hash,
    )
    all_samples = (
        bundle.samples_by_split["train"]
        + bundle.samples_by_split["val"]
        + bundle.samples_by_split["test"]
    )
    user_ids = sorted({int(s.user_id) for s in all_samples})

    experiments: list[dict[str, Any]] = []
    for family in families:
        run_id = BASELINE_RUN_IDS.get(family)
        if not run_id:
            continue
        artifact_dir = baseline_artifact_dir(repo_root, family, run_id, STRATEGY)
        if not artifact_dir.is_dir():
            continue
        backend = _load_classical_backend(family, artifact_dir)
        label_names = backend.label_names or NORMALIZED_LABELS

        participant_rows: list[dict[str, Any]] = []
        for user_id in user_ids:
            train_items = _samples_for_user(bundle.samples_by_split["train"], user_id, "train")
            test_items = _samples_for_user(bundle.samples_by_split["test"], user_id, "test")
            if not train_items or not test_items:
                participant_rows.append(
                    {
                        "user_id": user_id,
                        "status": "insufficient_data",
                        "calibration_session_count": len(train_items),
                        "evaluation_session_count": len(test_items),
                    }
                )
                continue

            train_x, train_y, calib_sessions = _stack(train_items)
            test_x, test_y, eval_sessions = _stack(test_items)
            if not calib_eval_session_sets_disjoint(calib_sessions, eval_sessions):
                return {
                    "generated_at": timestamp,
                    "status": "failed",
                    "reason": f"calib/eval session overlap for user {user_id}",
                }

            train_feat = backend.features(train_x)
            test_feat = backend.features(test_x)

            general_pred = backend.predict(test_x)
            general_report = classification_report_dict(
                test_y, general_pred, labels=label_names
            )

            calibrator = _fit_participant_calibrator(
                train_feat,
                train_y,
                n_classes=len(label_names),
            )
            personalized_pred = calibrator.predict(test_feat)
            personalized_report = classification_report_dict(
                test_y,
                personalized_pred,
                labels=label_names,
            )

            participant_rows.append(
                {
                    "user_id": user_id,
                    "status": "ok",
                    "calibration_session_count": len(calib_sessions),
                    "evaluation_session_count": len(eval_sessions),
                    "general": {
                        "macro_f1": general_report["macro_f1"],
                        "accuracy": general_report["accuracy"],
                    },
                    "personalized": {
                        "macro_f1": personalized_report["macro_f1"],
                        "accuracy": personalized_report["accuracy"],
                    },
                    "macro_f1_delta": round(
                        personalized_report["macro_f1"] - general_report["macro_f1"],
                        6,
                    ),
                    "adaptation_method": (
                        "logistic_regression on frozen classical features "
                        f"(baseline family={family}, extractor not refit)"
                    ),
                }
            )

        ok_rows = [r for r in participant_rows if r.get("status") == "ok"]
        if ok_rows:
            mean_general = float(np.mean([r["general"]["macro_f1"] for r in ok_rows]))
            mean_personal = float(np.mean([r["personalized"]["macro_f1"] for r in ok_rows]))
        else:
            mean_general = mean_personal = None

        experiments.append(
            {
                "family": family,
                "run_id": run_id,
                "split_strategy": STRATEGY,
                "artifact_dir": str(artifact_dir.relative_to(repo_root)),
                "aggregate": {
                    "mean_macro_f1_general": mean_general,
                    "mean_macro_f1_personalized": mean_personal,
                    "mean_macro_f1_delta": (
                        round(mean_personal - mean_general, 6)
                        if mean_general is not None and mean_personal is not None
                        else None
                    ),
                    "participants_evaluated": len(ok_rows),
                },
                "participants": participant_rows,
            }
        )

    status: PersonalizationStatus = "completed" if experiments else "failed"
    return {
        "generated_at": timestamp,
        "status": status,
        "protocol": (
            "In-domain: per participant, fit LogisticRegression on train-split sessions "
            "(features from frozen baseline extractor); evaluate on test-split sessions. "
            "Compare to frozen global baseline classifier on the same test sessions."
        ),
        "cross_user_personalization": "blocked",
        "in_domain_personalization": status,
        "calibrator_seed": CALIBRATOR_SEED,
        "experiments": experiments,
        "limitations": (
            "Classical families (logreg, rf) only; deep models not adapted. "
            "Aggregate means are unweighted across participants. "
            "Not a biometric identification claim."
        ),
    }
