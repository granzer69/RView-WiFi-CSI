#!/usr/bin/env python3
"""Plot test macro-F1 by model family and split strategy from V2 artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from research.generalization import build_generalization_rows, extended_metrics_entries

STRATEGY_ORDER = ("in_domain", "cross_user", "cross_environment")
STRATEGY_LABELS = {
    "in_domain": "In-domain",
    "cross_user": "Cross-user",
    "cross_environment": "Cross-env",
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "reports" / "figures" / "generalization_gaps.png",
    )
    parser.add_argument("--repo-root", type=Path, default=ROOT)
    args = parser.parse_args()

    rows = build_generalization_rows(extended_metrics_entries(args.repo_root))
    families = sorted({row["family"] for row in rows})
    if not families:
        raise SystemExit("No metrics rows found under artifacts/v2_*")

    x = range(len(families))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 5))
    for i, strategy in enumerate(STRATEGY_ORDER):
        values = []
        for family in families:
            match = next(
                (r for r in rows if r["family"] == family and r["split_strategy"] == strategy),
                None,
            )
            values.append(match["macro_f1"] if match and match["macro_f1"] is not None else 0.0)
        offset = (i - 1) * width
        ax.bar([xi + offset for xi in x], values, width=width, label=STRATEGY_LABELS[strategy])

    ax.set_xticks(list(x))
    ax.set_xticklabels(families)
    ax.set_ylabel("Test macro-F1")
    ax.set_title("ESP-Fi HAR — test macro-F1 by family and split")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 1.0)
    fig.tight_layout()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
