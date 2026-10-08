"""Session-grouped splits.

The split unit is a group id. For in-domain evaluation the group is one
recording session, and sessions are held out inside each
scenario/participant/activity cell. Cross-user and cross-environment
evaluation move the whole participant or scenario together.

Counts use floor(n * fraction), with at least one group in validation and
test when the fraction is positive and at least three groups exist. A
trial file is never cut across train and test.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np

from common.errors import SplitError
from datasets.esp_fi import TrialRecord

SPLIT_NAMES = ("train", "val", "test")


@dataclass(frozen=True)
class SplitAssignment:
    strategy: str
    seed: int
    test_fraction: float
    val_fraction: float
    session_to_split: dict[str, str]

    def sessions(self, name: str) -> list[str]:
        return sorted(session for session, split in self.session_to_split.items() if split == name)

    def counts(self) -> dict[str, int]:
        return {name: len(self.sessions(name)) for name in SPLIT_NAMES}


def _allocate(n_groups: int, test_fraction: float, val_fraction: float) -> tuple[int, int]:
    if n_groups < 3:
        raise SplitError(f"need at least 3 groups to hold out val and test, got {n_groups}")
    if not 0 < test_fraction < 1 or not 0 < val_fraction < 1:
        raise SplitError("fractions must be between 0 and 1")
    n_test = max(1, int(n_groups * test_fraction))
    n_val = max(1, int(n_groups * val_fraction))
    if n_test + n_val >= n_groups:
        raise SplitError(
            f"fractions leave no training group ({n_test} test, {n_val} val, {n_groups} groups)"
        )
    return n_test, n_val


def _assign_groups(group_ids: list[str], rng: np.random.Generator, n_test: int, n_val: int) -> dict[str, str]:
    ordered = sorted(group_ids)
    permuted = [ordered[int(index)] for index in rng.permutation(len(ordered))]
    assigned: dict[str, str] = {}
    for group_id in permuted[:n_test]:
        assigned[group_id] = "test"
    for group_id in permuted[n_test : n_test + n_val]:
        assigned[group_id] = "val"
    for group_id in permuted[n_test + n_val :]:
        assigned[group_id] = "train"
    return assigned


def assign_splits(
    records: list[TrialRecord],
    *,
    strategy: str,
    seed: int = 42,
    test_fraction: float = 0.15,
    val_fraction: float = 0.15,
) -> SplitAssignment:
    """Assign every session to train, val, or test.

    Groups are shuffled with ``numpy.random.Generator(seed)``. Strata are
    visited in sorted order, so the draw does not depend on file order.
    """
    if strategy not in {"in_domain", "cross_user", "cross_environment"}:
        raise SplitError(f"unknown strategy {strategy}")
    if not records:
        raise SplitError("no records to split")

    strata: dict[str, dict[str, list[TrialRecord]]] = defaultdict(lambda: defaultdict(list))
    for record in records:
        strata[record.stratum_value(strategy)][record.group_value(strategy)].append(record)

    rng = np.random.default_rng(seed)
    group_to_split: dict[str, str] = {}
    for stratum in sorted(strata):
        groups = list(strata[stratum])
        n_test, n_val = _allocate(len(groups), test_fraction, val_fraction)
        assigned = _assign_groups(groups, rng, n_test, n_val)
        overlap = set(assigned) & set(group_to_split)
        if overlap:
            raise SplitError(f"group ids repeated across strata: {sorted(overlap)[:5]}")
        group_to_split.update(assigned)

    session_to_split: dict[str, str] = {}
    for record in records:
        split_name = group_to_split[record.group_value(strategy)]
        previous = session_to_split.get(record.session_id)
        if previous is not None and previous != split_name:
            raise SplitError(f"session {record.session_id} landed in two splits")
        session_to_split[record.session_id] = split_name

    _assert_group_integrity(records, session_to_split, strategy)
    return SplitAssignment(
        strategy=strategy,
        seed=seed,
        test_fraction=test_fraction,
        val_fraction=val_fraction,
        session_to_split=session_to_split,
    )


def _assert_group_integrity(
    records: list[TrialRecord],
    session_to_split: dict[str, str],
    strategy: str,
) -> None:
    group_splits: dict[str, set[str]] = defaultdict(set)
    for record in records:
        group_splits[record.group_value(strategy)].add(session_to_split[record.session_id])
    leaked = {group: splits for group, splits in group_splits.items() if len(splits) != 1}
    if leaked:
        raise SplitError(f"groups crossed splits: {list(leaked)[:5]}")
