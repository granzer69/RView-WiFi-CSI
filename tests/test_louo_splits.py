import pytest

from common.errors import SplitError
from datasets.splits import LOUO_PARTICIPANTS, assign_louo_splits, louo_strategy_name
from test_splits import full_grid
from training.esp_fi import assignment_sha256
from training.louo import EXPECTED_LOUO_ASSIGNMENT_SHA256


def test_louo_counts_and_locked_hashes():
    records = full_grid()
    for participant in LOUO_PARTICIPANTS:
        assignment = assign_louo_splits(records, held_out_participant=participant, seed=42)
        assert assignment.strategy == louo_strategy_name(participant)
        assert assignment.counts() == {"train": 1680, "val": 280, "test": 280}
        digest = assignment_sha256(assignment)
        assert digest == EXPECTED_LOUO_ASSIGNMENT_SHA256[participant]


def test_louo_no_session_leakage_and_stable_draw():
    records = full_grid()
    for participant in LOUO_PARTICIPANTS:
        first = assign_louo_splits(records, held_out_participant=participant, seed=42)
        second = assign_louo_splits(list(reversed(records)), held_out_participant=participant, seed=42)
        assert first.session_to_split == second.session_to_split

        by_participant: dict[int, set[str]] = {}
        for record in records:
            by_participant.setdefault(record.participant_id, set()).add(
                first.session_to_split[record.session_id]
            )
        assert all(len(splits) == 1 for splits in by_participant.values())
        assert by_participant[participant] == {"test"}


def test_louo_rejects_invalid_participant():
    with pytest.raises(SplitError):
        assign_louo_splits(full_grid(), held_out_participant=9, seed=42)
