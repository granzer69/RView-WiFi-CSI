#!/usr/bin/env python3
"""Build LOUO result table and generalization figure from artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from research.louo import build_louo_export_payload, iter_louo_metrics, summarize_louo_macro_f1


def _markdown_table(entries: list[dict]) -> str:
    lines = [
        "| Family | Held-out user | Test macro-F1 | Test accuracy |",
        "| --- | ---: | ---: | ---: |",
    ]
    for entry in sorted(entries, key=lambda row: (row["family"], row["held_out_participant"])):
        test = entry.get("test") or {}
        macro = test.get("macro_f1")
        acc = test.get("accuracy")
        lines.append(
            f"| {entry['family']} | {entry['held_out_participant']} | "
            f"{macro:.4f} | {acc:.4f} |"
            if macro is not None and acc is not None
            else f"| {entry['family']} | {entry['held_out_participant']} | — | — |"
        )
    return "\n".join(lines) + "\n"


def _plot_per_fold(entries: list[dict], output_path: Path) -> None:
    families = sorted({entry["family"] for entry in entries})
    if not families:
        return

    fig, ax = plt.subplots(figsize=(8, 4.5))
    width = 0.35
    users = list(range(1, 9))
    for index, family in enumerate(families):
        by_user = {
            entry["held_out_participant"]: entry.get("test_macro_f1")
            for entry in entries
            if entry["family"] == family
        }
        values = [by_user.get(user) for user in users]
        offset = (index - (len(families) - 1) / 2) * width
        positions = [user + offset for user in users]
        ax.bar(
            positions,
            [value if value is not None else 0.0 for value in values],
            width=width,
            label=family,
            alpha=0.85,
        )

    ax.set_xlabel("Held-out participant")
    ax.set_ylabel("Test macro-F1")
    ax.set_title("LOUO generalization (classical families)")
    ax.set_xticks(users)
    ax.set_ylim(0, 1.0)
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=150)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "louo" / "reports",
    )
    args = parser.parse_args()

    entries = iter_louo_metrics(ROOT)
    summary = summarize_louo_macro_f1(entries)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_dir = args.output_dir / timestamp
    report_dir.mkdir(parents=True, exist_ok=True)

    table_md = _markdown_table(entries)
    (report_dir / "louo_results_table.md").write_text(table_md, encoding="utf-8")
    (report_dir / "summary.json").write_text(
        json.dumps(build_louo_export_payload(ROOT), indent=2) + "\n",
        encoding="utf-8",
    )
    _plot_per_fold(entries, report_dir / "louo_per_fold_macro_f1.png")

    latest = args.output_dir / "latest"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "louo_results_table.md").write_text(table_md, encoding="utf-8")
    (latest / "summary.json").write_text(
        json.dumps({"summary": summary, "generated_at": datetime.now(timezone.utc).isoformat()}, indent=2)
        + "\n",
        encoding="utf-8",
    )
    if (report_dir / "louo_per_fold_macro_f1.png").is_file():
        (latest / "louo_per_fold_macro_f1.png").write_bytes(
            (report_dir / "louo_per_fold_macro_f1.png").read_bytes()
        )

    print(json.dumps({"report_dir": str(report_dir), "fold_rows": len(entries)}, indent=2))


if __name__ == "__main__":
    main()
