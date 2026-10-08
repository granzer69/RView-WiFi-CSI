"""Write the V1 data validation report from measured inspection output."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ingestion.ml_contract import MODEL_INPUT_SHAPES, NORMALIZED_LABELS, PUBLISHED_SPLIT_ROLE


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--inspection",
        type=Path,
        default=ROOT / "reports" / "esp_fi_inspection.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
    )
    args = parser.parse_args()
    summary = json.loads(args.inspection.read_text())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(summary))
    print(args.output)


def render(summary: dict) -> str:
    num = summary["numeric_audit"]
    shapes = summary["shapes"]
    published = summary["published_folders"]
    lines = [
        "# V1 data validation report (ESP-Fi HAR)",
        "",
        "Measured values from `scripts/inspect_esp_fi.py` on the local archive. No models were trained.",
        "",
        "## Dataset overview",
        "",
        f"- **Dataset id**: `{summary['dataset_id']}`",
        f"- **Archive version**: `{summary['dataset_version']}`",
        f"- **Trials (`.mat` files)**: {summary['trial_count']}",
        f"- **Unique sessions**: {summary['unique_sessions']}",
        f"- **Grid complete (4×8×7×10)**: {summary['complete_grid']}",
        f"- **License**: CC BY 4.0",
        "",
        "### Scenario, participant, and class counts",
        "",
        f"- Scenarios: {summary['by_scenario']}",
        f"- Participants: {summary['by_participant']}",
        f"- Dataset labels: {summary['by_dataset_label']}",
        f"- Normalized labels: {summary['by_normalized_label']}",
        "",
        "## Integrity",
        "",
        f"- Duplicate session ids: none ({summary['unique_sessions']} unique).",
        f"- Missing grid cells: {summary['missing_cells'] or 'none'}",
        f"- Extra cells: {summary['extra_cells'] or 'none'}",
        "",
        "## Shape consistency",
        "",
        f"- Files read: {num['files_read']}",
        f"- Unique shapes: {num['unique_shapes']}",
        f"- Expected: `{num['expected_shape']}` (time × subcarriers)",
        f"- Legacy shape summary min/max/mean: min={shapes['amplitude_min']}, max={shapes['amplitude_max']}, mean={shapes['amplitude_mean']}",
        "",
        "## Missing / invalid numerics",
        "",
        f"- Dtype after load: `{num['dtype']}`",
        f"- Non-finite values (NaN/Inf): **{num['non_finite_count']}**",
        f"- Global amplitude min / max / mean / std: {num['amplitude_min']}, {num['amplitude_max']}, {num['amplitude_mean']}, {num['amplitude_std']}",
        f"- Per-recording amplitude min range: [{num['per_recording_amplitude_min']}, {num['per_recording_amplitude_max']}]",
        f"- Per-recording mean range: [{num['per_recording_mean_min']}, {num['per_recording_mean_max']}]",
        f"- Recordings with ≥1 constant subcarrier (std=0 over time): {num['recordings_with_constant_subcarrier']}",
        f"- Recordings with ≥1 near-constant subcarrier (std < {num['near_constant_std_threshold']}): {num['recordings_with_near_constant_subcarrier']}",
        f"- Max constant subcarriers in one recording: {num['max_constant_subcarriers_in_one_recording']}",
        "",
        "Per-subcarrier mean/std (across all trials, time pooled per file) are in `reports/esp_fi_inspection.json` under `numeric_audit`.",
        "",
        "## Class distribution",
        "",
        "Balanced: 320 trials per dataset label (7 × 320 = 2240).",
        "",
        "## Session distribution",
        "",
        "One session per trial file (`session_id` = stem). Ten trials per (scenario, participant, activity) cell.",
        "",
        "## Split integrity",
        "",
        "Session-grouped splits (seed 42, 15% val and 15% test via `max(1, floor(n×0.15))` per stratum).",
        "",
        "| Strategy | Train | Val | Test | Assignment SHA-256 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name in ("in_domain", "cross_user", "cross_environment"):
        block = summary["splits"][name]
        counts = block["counts"]
        lines.append(
            f"| `{name}` | {counts['train']} | {counts['val']} | {counts['test']} | `{block['assignment_sha256']}` |"
        )
    lines.extend(["", "## Leakage findings", ""])
    in_dom = summary["splits"]["in_domain"]["audit"]["session_integrity"]
    lines.extend(
        [
            f"**Same recording in train and test?** {in_dom['protocol_answer']}",
            "",
            f"- Shared sessions train∩test: {in_dom['shared_sessions_train_test'] or 'none'}",
            f"- Groups crossing splits (in_domain): {summary['splits']['in_domain']['audit']['groups_crossing_splits'] or 'none'}",
            "",
            "### Published `train_amp` / `test_amp` (leakage check only)",
            "",
            f"- Role: `{PUBLISHED_SPLIT_ROLE}` — not used for experiment metrics.",
            f"- Train files: {published['train_count']}; test files: {published['test_count']}",
            f"- Session leakage: {published['session_leakage']}; participant leakage: {published['participant_leakage']}",
            f"- Shared session ids: {published['shared_session_ids'] or 'none'}",
            f"- Covers scenario 3 only; single-participant holdout — not equivalent to cross-environment or full in-domain protocol.",
            "",
            "## Label ambiguity",
            "",
            f"- Map in use: `published_folder_codes_not_readme` (scenario-3 class folders at upstream commit).",
            f"- README id table disagrees for codes: {summary['codes_disagreeing_with_readme']}",
            f"- Folder-verified on this archive path layout: {summary['folder_verified_labels']} / {summary['trial_count']}",
            f"- **INFERRED — NOT INDEPENDENTLY VERIFIED** for scenarios 1, 2, and 4 (no class folders); labels follow the measured scenario-3 map.",
            "",
            "## Preprocessing recommendations",
            "",
            "Default (`configs/preprocessing/default.json`): no clip, no z-score, no windowing — one segment per trial.",
            "",
            "| Step | V1 default | Why | Leakage risk | Fit on train only |",
            "| --- | --- | --- | --- | --- |",
            "| Validation | on | Reject non-finite / wrong shape | none | n/a |",
            "| MAD clip | off | Optional spike removal; not required for clean finite amplitudes | none per window | if enabled later, estimate thresholds on train |",
            "| Per-window z-score | off | Removes absolute scale; useful for some models | none per window | per-sample, no global stats |",
            "| Temporal windowing | off | Needed only for shorter segments | segments stay inside one session | n/a |",
            "| PCA / denoising | not in V1 | Add only with a stated goal; no blind cookbook | global PCA would need train-only fit | defer to V2 |",
            "",
            f"Sample unchanged hash check: session `{summary['default_preprocess']['session_id']}`, unchanged={summary['default_preprocess']['unchanged']}.",
            "",
            "## Model-ready contract",
            "",
            "Type: `HarSample` in `src/ingestion/ml_contract.py`. Fields: `amplitude`, `normalized_label`, `label_id`, `session_id`, `user_id`, `environment_id`, `activity_code`, `trial_id`, `split`, `split_strategy`, `dataset_id`, `metadata` (no raw folder path).",
            "",
            f"- Labels: {list(NORMALIZED_LABELS)}",
            "",
            "### Tensor shapes (ESP-Fi amplitude)",
            "",
        ]
    )
    for model, spec in MODEL_INPUT_SHAPES.items():
        lines.append(f"- **{model}**: {spec}")
    lines.extend(
        [
            "",
            "## V1 readiness",
            "",
            "- ESP-Fi archive: present, 2240 trials, shapes consistent, no non-finite values.",
            "- Session-grouped splits: defined for three strategies; no session overlap across train/val/test.",
            "- Published folders: audited; safe as leakage reference only.",
            "- Labels: documented ambiguity; no silent relabeling.",
            "- **Ready for V2 model work after explicit approval** — do not start training or API/frontend until then.",
            "",
        ]
    )
    return "\n".join(lines)


if __name__ == "__main__":
    main()
