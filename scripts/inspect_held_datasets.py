"""Write inspection notes for datasets that are not cleared for experiments.

Embedded WiFi Sensing files may be counted. CSI-Bench is reported as not
downloaded. Neither report is a model result.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datasets.csi_bench import status
from datasets.embedded import LICENSE_STATUS, census


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect held datasets without running experiments")
    parser.add_argument(
        "--embedded",
        type=Path,
        default=ROOT / "data" / "raw" / "embedded-wifi-sensing" / "Datasets" / "Activity",
    )
    parser.add_argument("--report-dir", type=Path, default=ROOT / "reports")
    args = parser.parse_args()
    args.report_dir.mkdir(parents=True, exist_ok=True)

    embedded = census(args.embedded)
    embedded["sample_file"] = _relative(Path(str(embedded["sample_file"])))
    embedded_json = args.report_dir / "embedded_inspection.json"
    embedded_md = args.report_dir / "embedded_inspection.md"
    embedded_json.write_text(json.dumps(embedded, indent=2, sort_keys=True) + "\n")
    embedded_md.write_text(render_embedded(embedded))

    bench = status()
    bench_json = args.report_dir / "csi_bench_status.json"
    bench_md = args.report_dir / "csi_bench_status.md"
    bench_json.write_text(json.dumps(bench, indent=2, sort_keys=True) + "\n")
    bench_md.write_text(render_bench(bench))
    print(json.dumps({
        "embedded_files": embedded["file_count"],
        "embedded_experiment_use": embedded["experiment_use"],
        "csi_bench": bench["acquisition"],
    }, indent=2))


def _relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def render_embedded(census_result: dict[str, object]) -> str:
    counts = census_result["activity_counts"]
    assert isinstance(counts, dict)
    subjects = census_result["subject_ids"]
    per_subject = census_result["files_per_subject"]
    assert isinstance(per_subject, dict)
    sizes = sorted(set(per_subject.values()))
    lines = [
        "# Embedded WiFi Sensing HAR — inspection only",
        "",
        "License status: **" + LICENSE_STATUS + "**.",
        "",
        "This note does not authorize experiments or publication. The repository code is MIT. The paper is CC BY 4.0. The recordings themselves were collected from volunteers under an academic-research consent statement. This project does not treat that consent as a commercial-use grant. `assert_cleared_for_experiment()` stays closed.",
        "",
        "NumPy arrays stored next to `Datasets/Activity` are not used as raw CSI.",
        "",
        "## Census",
        "",
        f"Text files: {census_result['file_count']}.",
        "",
        "| Activity code | Files |",
        "| --- | ---: |",
    ]
    for code in sorted(counts):
        lines.append(f"| {code} | {counts[code]} |")
    lines.extend([
        "",
        f"Subject ids present: {', '.join(str(subject) for subject in subjects)}.",
        f"Files per subject range from {sizes[0]} to {sizes[-1]}.",
        f"Sample file `{census_result['sample_file']}` has {census_result['sample_packets']} packets and {census_result['sample_subcarriers']} subcarriers.",
        "",
        str(census_result["note"]),
        "",
    ])
    return "\n".join(lines)


def render_bench(bench: dict[str, str]) -> str:
    return "\n".join([
        "# CSI-Bench HAR — not acquired",
        "",
        "This dataset is the approved secondary validation set. It is not on disk in this environment.",
        "",
        f"- Acquisition: `{bench['acquisition']}`.",
        f"- Dataset license: `{bench['dataset_license']}`.",
        f"- Code policy: `{bench['code_policy']}`. The benchmark repository's README also says CC BY-NC-ND, while its LICENSE file says MIT. Code stays reference-only. It is not copied into this repository.",
        f"- Experiment use: `{bench['experiment_use']}`.",
        "",
        "When a local HAR subset exists, use only that subset, keep it local, and do not redistribute the files or derivatives. Published CSI-Bench scores are not results of this project.",
        "",
        f"Data: {bench['data_url']}",
        "",
        f"Code: {bench['code_url']}",
        "",
    ])


if __name__ == "__main__":
    main()
