"""Compare the published ESP-Fi folders with a session-safe reading.

The folders are not an evaluation split. This module only reports whether
they share sessions, participants, or scenarios.
"""

from __future__ import annotations

from typing import Any


def published_folder_report(records: list[dict[str, Any]]) -> dict[str, Any]:
    train = [row for row in records if row["split"] == "train_amp"]
    test = [row for row in records if row["split"] == "test_amp"]
    other = [row for row in records if row["split"] not in {"train_amp", "test_amp"}]
    if other:
        raise ValueError("published manifest contains a split other than train_amp/test_amp")

    def values(rows: list[dict[str, Any]], key: str) -> set[Any]:
        return {row[key] for row in rows}

    shared_sessions = sorted(values(train, "stem") & values(test, "stem"))
    shared_participants = sorted(values(train, "participant_id") & values(test, "participant_id"))
    shared_scenarios = sorted(values(train, "scenario_id") & values(test, "scenario_id"))
    return {
        "train_count": len(train),
        "test_count": len(test),
        "train_participants": sorted(values(train, "participant_id")),
        "test_participants": sorted(values(test, "participant_id")),
        "train_scenarios": sorted(values(train, "scenario_id")),
        "test_scenarios": sorted(values(test, "scenario_id")),
        "shared_session_ids": shared_sessions,
        "shared_participant_ids": shared_participants,
        "shared_scenario_ids": shared_scenarios,
        "session_leakage": bool(shared_sessions),
        "participant_leakage": bool(shared_participants),
        "single_scenario": shared_scenarios == sorted(values(train, "scenario_id") | values(test, "scenario_id"))
        and len(shared_scenarios) == 1,
    }
