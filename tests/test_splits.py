import pytest

from common.errors import SplitError
from datasets.esp_fi import ACTIVITY_CODE_TO_DATASET_LABEL, DATASET_TO_NORMALIZED, TrialRecord
from datasets.splits import assign_splits


def full_grid() -> list[TrialRecord]:
    records = []
    for scenario_id in range(1, 5):
        for participant_id in range(1, 9):
            for activity_code in range(1, 8):
                label = ACTIVITY_CODE_TO_DATASET_LABEL[activity_code]
                for trial_id in range(1, 11):
                    session_id = f"{scenario_id}-{participant_id}-{activity_code}-{trial_id}"
                    records.append(
                        TrialRecord(
                            session_id=session_id,
                            scenario_id=scenario_id,
                            participant_id=participant_id,
                            activity_code=activity_code,
                            trial_id=trial_id,
                            dataset_label=label,
                            normalized_label=DATASET_TO_NORMALIZED[label],
                            path=f"mat/{session_id}.mat",
                            label_verified_by_folder=False,
                            scenario_dirname=f"env{scenario_id}",
                        )
                    )
    return records


def test_grouped_counts_and_locked_draw():
    records = full_grid()
    in_domain = assign_splits(records, strategy="in_domain", seed=42)
    assert in_domain.counts() == {"train": 1792, "val": 224, "test": 224}
    cell = [f"1-1-1-{trial}" for trial in range(1, 11)]
    assert {session: in_domain.session_to_split[session] for session in cell} == {
        "1-1-1-1": "train",
        "1-1-1-2": "train",
        "1-1-1-3": "train",
        "1-1-1-4": "train",
        "1-1-1-5": "train",
        "1-1-1-6": "test",
        "1-1-1-7": "train",
        "1-1-1-8": "train",
        "1-1-1-9": "train",
        "1-1-1-10": "val",
    }

    cross_user = assign_splits(records, strategy="cross_user", seed=42)
    assert cross_user.counts() == {"train": 1680, "val": 280, "test": 280}
    assert {cross_user.session_to_split[f"1-{participant}-1-1"] for participant in (1, 2, 3, 6, 7, 8)} == {"train"}
    assert cross_user.session_to_split["2-5-3-7"] == "val"
    assert cross_user.session_to_split["4-4-7-10"] == "test"

    cross_env = assign_splits(records, strategy="cross_environment", seed=42)
    assert cross_env.counts() == {"train": 1120, "val": 560, "test": 560}
    assert cross_env.session_to_split["1-8-7-10"] == "train"
    assert cross_env.session_to_split["2-1-1-1"] == "train"
    assert cross_env.session_to_split["3-3-3-3"] == "val"
    assert cross_env.session_to_split["4-4-4-4"] == "test"


def test_groups_do_not_cross_splits_and_draw_is_stable():
    records = full_grid()
    first = assign_splits(records, strategy="cross_user", seed=42)
    second = assign_splits(list(reversed(records)), strategy="cross_user", seed=42)
    assert first.session_to_split == second.session_to_split
    by_participant: dict[int, set[str]] = {}
    for record in records:
        by_participant.setdefault(record.participant_id, set()).add(first.session_to_split[record.session_id])
    assert all(len(splits) == 1 for splits in by_participant.values())


def test_random_window_split_is_rejected():
    with pytest.raises(SplitError):
        assign_splits(full_grid(), strategy="random")
    tiny = full_grid()[:2]
    with pytest.raises(SplitError):
        assign_splits(tiny, strategy="in_domain")
