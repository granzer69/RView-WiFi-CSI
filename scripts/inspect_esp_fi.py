"""Load ESP-Fi, print statistics, and write the split report.

The published train_amp/test_amp folders are compared for leakage. They are
not the evaluation split. Run from the repository root:

    python scripts/inspect_esp_fi.py --plots artifacts/figures
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from csi.visualize import save_amplitude_plot, save_heatmap
from datasets.esp_fi import (
    ACTIVITY_CODE_TO_DATASET_LABEL,
    DATASET_ID,
    DATASET_VERSION,
    README_ACTIVITY_CODE_TO_DATASET_LABEL,
    SCENARIO_NAMES,
    discover_trials,
    load_window,
    observe_csv_packet_rate,
    sibling_csv,
)
from datasets.audit import audit_numeric, audit_split_assignment
from datasets.leakage import published_folder_report
from datasets.splits import assign_splits
from ingestion.schema import CsiWindow
from preprocessing.pipeline import PreprocessConfig, process, processed_hash


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect the local ESP-Fi HAR archive")
    parser.add_argument("--root", type=Path, default=ROOT / "data" / "raw" / "esp-fi-har")
    parser.add_argument(
        "--published",
        type=Path,
        default=ROOT / "configs" / "datasets" / "esp_fi_published_split.json",
    )
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports")
    parser.add_argument("--metadata", type=Path, default=ROOT / "data" / "metadata" / "esp-fi-har.json")
    parser.add_argument("--plots", type=Path, default=None, help="Directory for representative figures")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    records = discover_trials(args.root)
    summary = summarize(records)
    summary["shapes"] = audit_shapes(records)
    summary["numeric_audit"] = audit_numeric(records).to_dict()
    summary["csv_rate_observations"] = csv_observations(records)
    summary["splits"] = {
        name: split_summary(records, name, args.seed, include_audit=True) for name in ("in_domain", "cross_user", "cross_environment")
    }
    summary["published_folders"] = load_published(args.published)
    summary["default_preprocess"] = default_preprocess_check(records)
    if args.plots is not None:
        summary["plots"] = write_plots(records, args.plots)

    args.report_dir.mkdir(parents=True, exist_ok=True)
    inspection_path = args.report_dir / "esp_fi_inspection.json"
    methodology_path = args.report_dir / "esp_fi_split_methodology.md"
    inspection_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    methodology_path.write_text(render_methodology(summary))
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata_document(summary), indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "trials": summary["trial_count"],
        "shapes": summary["shapes"]["unique_shapes"],
        "splits": {name: summary["splits"][name]["counts"] for name in summary["splits"]},
        "published_session_leakage": summary["published_folders"]["session_leakage"],
        "published_participant_leakage": summary["published_folders"]["participant_leakage"],
        "report": str(methodology_path),
    }, indent=2))


def summarize(records: list[Any]) -> dict[str, Any]:
    expected = {(s, p, z, m) for s in range(1, 5) for p in range(1, 9) for z in range(1, 8) for m in range(1, 11)}
    found = {(r.scenario_id, r.participant_id, r.activity_code, r.trial_id) for r in records}
    return {
        "dataset_id": DATASET_ID,
        "dataset_version": DATASET_VERSION,
        "trial_count": len(records),
        "unique_sessions": len({r.session_id for r in records}),
        "complete_grid": found == expected,
        "missing_cells": ["-".join(str(part) for part in cell) for cell in sorted(expected - found)],
        "extra_cells": ["-".join(str(part) for part in cell) for cell in sorted(found - expected)],
        "by_scenario": dict(sorted(Counter(SCENARIO_NAMES[r.scenario_id] for r in records).items())),
        "by_participant": {str(key): value for key, value in sorted(Counter(r.participant_id for r in records).items())},
        "by_dataset_label": dict(sorted(Counter(r.dataset_label for r in records).items())),
        "by_normalized_label": dict(sorted(Counter(r.normalized_label for r in records).items())),
        "by_trial_id": {str(key): value for key, value in sorted(Counter(r.trial_id for r in records).items())},
        "folder_verified_labels": sum(r.label_verified_by_folder for r in records),
        "folder_unverified_labels": sum(not r.label_verified_by_folder for r in records),
        "activity_code_map": {str(code): label for code, label in ACTIVITY_CODE_TO_DATASET_LABEL.items()},
        "readme_activity_code_map": {str(code): label for code, label in README_ACTIVITY_CODE_TO_DATASET_LABEL.items()},
        "codes_disagreeing_with_readme": sorted(
            code for code, label in ACTIVITY_CODE_TO_DATASET_LABEL.items()
            if README_ACTIVITY_CODE_TO_DATASET_LABEL[code] != label
        ),
    }


def audit_shapes(records: list[Any]) -> dict[str, Any]:
    shapes: Counter[str] = Counter()
    amin = None
    amax = None
    total = 0.0
    count = 0
    for record in records:
        window = load_window(record)
        shapes[str(tuple(window.amplitude.shape))] += 1
        values = window.amplitude
        batch_min = float(values.min())
        batch_max = float(values.max())
        amin = batch_min if amin is None else min(amin, batch_min)
        amax = batch_max if amax is None else max(amax, batch_max)
        total += float(values.sum())
        count += int(values.size)
    return {
        "files_read": sum(shapes.values()),
        "unique_shapes": dict(shapes),
        "amplitude_min": amin,
        "amplitude_max": amax,
        "amplitude_mean": None if count == 0 else total / count,
        "phase": "absent",
        "sample_rate_hz": None,
        "antennas": None,
    }


def csv_observations(records: list[Any]) -> list[dict[str, Any]]:
    observations = []
    for scenario_id in sorted({record.scenario_id for record in records}):
        chosen = sorted((record for record in records if record.scenario_id == scenario_id), key=lambda record: record.session_id)[0]
        csv_path = sibling_csv(Path(chosen.path))
        if csv_path is None:
            observations.append({"scenario_id": scenario_id, "error": f"no sibling csv for {chosen.session_id}"})
            continue
        observed = observe_csv_packet_rate(csv_path)
        observed["path"] = _relative(Path(observed["path"]))
        observed["scenario_id"] = scenario_id
        observed["scenario_name"] = SCENARIO_NAMES[scenario_id]
        observed["session_id"] = chosen.session_id
        observations.append(observed)
    return observations


def split_summary(records: list[Any], strategy: str, seed: int, *, include_audit: bool = False) -> dict[str, Any]:
    assignment = assign_splits(records, strategy=strategy, seed=seed)
    groups: dict[str, set[str]] = {"train": set(), "val": set(), "test": set()}
    for record in records:
        groups[assignment.session_to_split[record.session_id]].add(record.group_value(strategy))
    lines = [f"{session}\t{split}" for session, split in sorted(assignment.session_to_split.items())]
    payload: dict[str, Any] = {
        "strategy": strategy,
        "seed": assignment.seed,
        "test_fraction": assignment.test_fraction,
        "val_fraction": assignment.val_fraction,
        "counts": assignment.counts(),
        "group_ids": {name: sorted(values, key=_group_sort) for name, values in groups.items()},
        "assignment_sha256": hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest(),
    }
    if include_audit:
        payload["audit"] = audit_split_assignment(records, assignment)
    return payload


def load_published(path: Path) -> dict[str, Any]:
    document = json.loads(path.read_text())
    report = published_folder_report(document["records"])
    report["source_commit"] = document["source_commit"]
    report["source_repo"] = document["source_repo"]
    report["role"] = "leakage_check_only"
    return report


def default_preprocess_check(records: list[Any]) -> dict[str, Any]:
    window = load_window(sorted(records, key=lambda record: record.session_id)[0])
    result = process(window, PreprocessConfig())
    return {
        "session_id": window.session_id,
        "config": PreprocessConfig().to_dict(),
        "segment_count": len(result.windows),
        "dropped_tail": result.dropped_tail,
        "unchanged": bool((result.windows[0].amplitude == window.amplitude).all()),
        "processed_sha256": processed_hash(result),
    }


def write_plots(records: list[Any], directory: Path) -> list[str]:
    written: list[str] = []
    by_label: dict[str, Any] = {}
    for record in sorted(records, key=lambda item: item.session_id):
        by_label.setdefault(record.normalized_label, record)
    for label in sorted(by_label):
        window: CsiWindow = load_window(by_label[label])
        amplitude_path = directory / f"{label}_{window.session_id}_amplitude.png"
        heatmap_path = directory / f"{label}_{window.session_id}_heatmap.png"
        save_amplitude_plot(window, amplitude_path)
        save_heatmap(window, heatmap_path)
        written.extend([str(amplitude_path), str(heatmap_path)])
    return written


def metadata_document(summary: dict[str, Any]) -> dict[str, Any]:
    return {
        "dataset_id": summary["dataset_id"],
        "dataset_version": summary["dataset_version"],
        "license": "CC-BY-4.0",
        "trial_count": summary["trial_count"],
        "complete_grid": summary["complete_grid"],
        "shape": summary["shapes"]["unique_shapes"],
        "phase": "absent",
        "sample_rate_hz": None,
        "label_map": "published_folder_codes_not_readme",
        "folder_unverified_labels": summary["folder_unverified_labels"],
        "codes_disagreeing_with_readme": summary["codes_disagreeing_with_readme"],
    }


def render_methodology(summary: dict[str, Any]) -> str:
    splits = summary["splits"]
    published = summary["published_folders"]
    lines = [
        "# ESP-Fi split methodology",
        "",
        "Evaluation uses session-grouped splits. The git-published `train_amp` and `test_amp` folders are a leakage check, not the split used for metrics. The three strategies below are reported separately and are not averaged.",
        "",
        "## Session leakage question",
        "",
        "**Can information from the same recording leak between train and test?** **NO** for this protocol.",
        "",
        "- One recording is one trial file named `X-Y-Z-M`. Its `session_id` is that stem.",
        "- Each `session_id` is assigned to exactly one of `train`, `val`, or `test`.",
        "- A trial file is never cut so that part of its samples are in train and part in test.",
        "- Preprocessing segments (when enabled) stay inside a single session window; they do not mix sessions.",
        "",
        "Published `train_amp` / `test_amp` folders also have **no shared session ids** (measured). They are still not used as the evaluation split because they only cover scenario 3 and implement a single-participant holdout, not the three session-grouped strategies below.",
        "",
        "## Rules",
        "",
        "- The split unit is one recording session, which is one trial file named `X-Y-Z-M`. A file is never cut so that part of it is in train and part of it is in test.",
        "- `in_domain`: the group is the session. The stratum is `scenario:participant:activity`. Holdout is drawn inside each cell, so every activity, participant, and scenario can appear in every split.",
        "- `cross_user`: the group is the participant id. Every session from that participant moves together. There is one stratum.",
        "- `cross_environment`: the group is the scenario id. Every session from that scenario moves together. There is one stratum.",
        "- Holdout size is `max(1, floor(n_groups * 0.15))` for test and the same rule for validation. The rest is train. A cell needs at least three groups, and the two holdouts must leave at least one training group.",
        "- The generator is `numpy.random.Generator` with seed 42. Strata are visited in sorted order. Group ids inside a stratum are sorted, then permuted. File listing order does not change the draw.",
        "- For a complete cell of 10 trials, `floor(10 * 0.15) = 1`, so the cell contributes 1 test session, 1 validation session, and 8 training sessions.",
        "",
        "## Measured assignment",
        "",
        f"Trials read: {summary['trial_count']}. Unique sessions: {summary['unique_sessions']}. Complete 4×8×7×10 grid: {summary['complete_grid']}.",
        "",
        "| Strategy | Train sessions | Validation sessions | Test sessions | Assignment SHA-256 |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for name in ("in_domain", "cross_user", "cross_environment"):
        counts = splits[name]["counts"]
        lines.append(
            f"| {name} | {counts['train']} | {counts['val']} | {counts['test']} | `{splits[name]['assignment_sha256']}` |"
        )
    cross_user = splits["cross_user"]["group_ids"]
    cross_env = splits["cross_environment"]["group_ids"]
    lines.extend([
        "",
        f"Cross-user groups (participant ids). Train: {cross_user['train']}. Validation: {cross_user['val']}. Test: {cross_user['test']}.",
        f"Cross-environment groups (scenario ids). Train: {cross_env['train']}. Validation: {cross_env['val']}. Test: {cross_env['test']}.",
        "In-domain groups are the session ids. Train, validation, and test id lists are in `reports/esp_fi_inspection.json` under `splits.in_domain.group_ids`.",
        "",
        "## Published folders",
        "",
        f"Source commit `{published['source_commit']}`. This comparison does not load CSI.",
        "",
        f"- `train_amp` files: {published['train_count']}. Participants: {published['train_participants']}. Scenarios: {published['train_scenarios']}.",
        f"- `test_amp` files: {published['test_count']}. Participants: {published['test_participants']}. Scenarios: {published['test_scenarios']}.",
        f"- Shared session ids: {published['shared_session_ids'] or 'none'}. Session leakage: {published['session_leakage']}.",
        f"- Shared participant ids: {published['shared_participant_ids'] or 'none'}. Participant leakage: {published['participant_leakage']}.",
        f"- Shared scenario ids: {published['shared_scenario_ids']}. Single scenario: {published['single_scenario']}.",
        "",
        "The published folders hold out participant 1 on scenario 3 only. They do not share sessions or participants. They are one subject holdout in one room, so they are not a cross-environment result and they are not this project's evaluation split.",
        "",
        "## Labels",
        "",
        "Activity codes follow the class folders measured in the published scenario-3 tree. The README id table disagrees. Codes that differ: "
        + ", ".join(str(code) for code in summary["codes_disagreeing_with_readme"])
        + ".",
        "",
        f"This extracted archive stores trials under `mat/`, so a class-folder check on these paths succeeds for {summary['folder_verified_labels']} of {summary['trial_count']} files. The map itself was measured on the published scenario-3 folders. Scenarios 1, 2, and 4 have no class folders, so their labels stay inferred.",
        "",
        "The matrix sample rate is unknown. Raw CSV packet rates below are single-file observations and are not applied to `CsiWindow.sample_rate_hz`.",
        "",
    ])
    for observed in summary["csv_rate_observations"]:
        if "error" in observed:
            lines.append(f"- Scenario {observed['scenario_id']}: {observed['error']}")
            continue
        lines.append(
            f"- Scenario {observed['scenario_id']} ({observed['scenario_name']}), session {observed['session_id']}: "
            f"{observed['packet_count']} packets over {observed['span_seconds']:.6f} s, "
            f"observed rate {observed['observed_packet_rate_hz']:.6f} Hz. {observed['note']}"
        )
    lines.append("")
    return "\n".join(lines)


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _group_sort(value: str) -> tuple[int, str]:
    return (int(value), value) if value.isdigit() else (10**9, value)


if __name__ == "__main__":
    main()
