# ESP-Fi split methodology

Evaluation uses session-grouped splits. The git-published `train_amp` and `test_amp` folders are a leakage check, not the split used for metrics. The three strategies below are reported separately and are not averaged.

## Rules

- The split unit is one recording session, which is one trial file named `X-Y-Z-M`. A file is never cut so that part of it is in train and part of it is in test.
- `in_domain`: the group is the session. The stratum is `scenario:participant:activity`. Holdout is drawn inside each cell, so every activity, participant, and scenario can appear in every split.
- `cross_user`: the group is the participant id. Every session from that participant moves together. There is one stratum.
- `cross_environment`: the group is the scenario id. Every session from that scenario moves together. There is one stratum.
- Holdout size is `max(1, floor(n_groups * 0.15))` for test and the same rule for validation. The rest is train. A cell needs at least three groups, and the two holdouts must leave at least one training group.
- The generator is `numpy.random.Generator` with seed 42. Strata are visited in sorted order. Group ids inside a stratum are sorted, then permuted. File listing order does not change the draw.
- For a complete cell of 10 trials, `floor(10 * 0.15) = 1`, so the cell contributes 1 test session, 1 validation session, and 8 training sessions.

## Measured assignment

Trials read: 2240. Unique sessions: 2240. Complete 4×8×7×10 grid: True.

| Strategy | Train sessions | Validation sessions | Test sessions | Assignment SHA-256 |
| --- | ---: | ---: | ---: | --- |
| in_domain | 1792 | 224 | 224 | `6304085ccf8260d560232088d9d0b5e7013dbe6583d164e7e46fb52f3a6753da` |
| cross_user | 1680 | 280 | 280 | `ff148c7c7b28c78d17553832bae15d380b11ce3266d165d2c6d3ea87cb38fb72` |
| cross_environment | 1120 | 560 | 560 | `00d03230dcaf901996550b4716e81ef91fbe97c0ddde776df6607c27308d73f8` |

Cross-user groups (participant ids). Train: ['1', '2', '3', '6', '7', '8']. Validation: ['5']. Test: ['4'].
Cross-environment groups (scenario ids). Train: ['1', '2']. Validation: ['3']. Test: ['4'].
In-domain groups are the session ids. Train, validation, and test id lists are in `reports/esp_fi_inspection.json` under `splits.in_domain.group_ids`.

## Published folders

Source commit `c8bf6aa0d680fa02695c85a82b05e79b3ebb10c4`. This comparison does not load CSI.

- `train_amp` files: 490. Participants: [2, 3, 4, 5, 6, 7, 8]. Scenarios: [3].
- `test_amp` files: 70. Participants: [1]. Scenarios: [3].
- Shared session ids: none. Session leakage: False.
- Shared participant ids: none. Participant leakage: False.
- Shared scenario ids: [3]. Single scenario: True.

The published folders hold out participant 1 on scenario 3 only. They do not share sessions or participants. They are one subject holdout in one room, so they are not a cross-environment result and they are not this project's evaluation split.

## Labels

Activity codes follow the class folders measured in the published scenario-3 tree. The README id table disagrees. Codes that differ: 2, 3, 4, 5, 6, 7.

This extracted archive stores trials under `mat/`, so a class-folder check on these paths succeeds for 0 of 2240 files. The map itself was measured on the published scenario-3 folders. Scenarios 1, 2, and 4 have no class folders, so their labels stay inferred.

The matrix sample rate is unknown. Raw CSV packet rates below are single-file observations and are not applied to `CsiWindow.sample_rate_hz`.

- Scenario 1 (corridor), session 1-1-1-1: 983 packets over 9.972000 s, observed rate 98.475732 Hz. Single-file observation of the raw CSV. The MAT grid is 950 steps and is not this packet count.
- Scenario 2 (office), session 2-1-1-1: 959 packets over 9.988000 s, observed rate 95.915098 Hz. Single-file observation of the raw CSV. The MAT grid is 950 steps and is not this packet count.
- Scenario 3 (boardroom), session 3-1-1-1: 994 packets over 9.994000 s, observed rate 99.359616 Hz. Single-file observation of the raw CSV. The MAT grid is 950 steps and is not this packet count.
- Scenario 4 (laboratory), session 4-1-1-1: 955 packets over 10.256000 s, observed rate 93.018721 Hz. Single-file observation of the raw CSV. The MAT grid is 950 steps and is not this packet count.
