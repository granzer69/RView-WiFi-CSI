"""Research lab exports: generalization gaps, participant profiling, experiment records."""

from research.experiment_record import ExperimentRecord, ExperimentStatus
from research.generalization import (
    BASELINE_RUN_IDS,
    baseline_metrics_entries,
    compute_generalization_gap,
    confused_pairs_from_matrix,
    load_metrics_json,
)

__all__ = [
    "BASELINE_RUN_IDS",
    "ExperimentRecord",
    "ExperimentStatus",
    "baseline_metrics_entries",
    "compute_generalization_gap",
    "confused_pairs_from_matrix",
    "load_metrics_json",
]
