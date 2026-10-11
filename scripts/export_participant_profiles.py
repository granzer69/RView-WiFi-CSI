#!/usr/bin/env python3
"""Export participant profiling and personalization status JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from research.generalization import BASELINE_RUN_IDS
from research.participant import (
    build_all_participant_model_metrics,
    build_participant_overview,
    check_esp_fi_available,
)
from research.personalization import run_in_domain_personalization_ab


def _git_sha() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
            cwd=ROOT,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


PERSONALIZATION_PROTOCOL = (
    "In-domain personalization (when evaluated): calibrate on each participant's train "
    "sessions only; evaluate on that participant's test sessions. cross_user "
    "personalization is blocked because held-out users do not appear in training."
)


def build_participants_payload(repo_root: Path) -> dict:
    availability = check_esp_fi_available(repo_root)
    timestamp = datetime.now(timezone.utc).isoformat()
    git_sha = _git_sha()

    if not availability.present:
        return {
            "generated_at": timestamp,
            "git_sha": git_sha,
            "status": "blocked",
            "reason": availability.reason,
            "baseline_run_ids": dict(BASELINE_RUN_IDS),
            "overview": {"status": "blocked", "participants": []},
            "model_metrics": {"status": "blocked", "models": []},
            "methodology": (
                "Participant metrics require ESP-Fi under data/raw/esp-fi-har. "
                "Exports use test-split sessions only."
            ),
        }

    overview = build_participant_overview(repo_root, strategy="in_domain")
    model_metrics = build_all_participant_model_metrics(
        repo_root,
        strategies=("in_domain",),
    )

    return {
        "generated_at": timestamp,
        "git_sha": git_sha,
        "status": model_metrics.get("status", "ok"),
        "baseline_run_ids": dict(BASELINE_RUN_IDS),
        "overview": overview,
        "model_metrics": model_metrics,
        "methodology": model_metrics.get("methodology"),
    }


def build_personalization_payload(repo_root: Path) -> dict:
    payload = run_in_domain_personalization_ab(repo_root)
    git_sha = _git_sha()
    payload["git_sha"] = git_sha
    payload["baseline_run_ids"] = dict(BASELINE_RUN_IDS)
    if "protocol" not in payload or len(payload.get("protocol", "")) < 20:
        payload["protocol"] = PERSONALIZATION_PROTOCOL
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--participants-out",
        type=Path,
        default=ROOT / "frontend" / "public" / "research" / "participants.json",
    )
    parser.add_argument(
        "--personalization-out",
        type=Path,
        default=ROOT / "frontend" / "public" / "research" / "personalization.json",
    )
    args = parser.parse_args()

    participants = build_participants_payload(ROOT)
    personalization = build_personalization_payload(ROOT)

    for path, payload in (
        (args.participants_out, participants),
        (args.personalization_out, personalization),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {path} (status={payload.get('status')})")


if __name__ == "__main__":
    main()
