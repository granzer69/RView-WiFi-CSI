# Data

Raw recordings stay on disk and out of git. `data/raw/`, `data/interim/`, and `data/processed/` are ignored. `data/metadata/` holds measured provenance and is committed.

**How to download and run the app:** see **[`docs/SETUP.md`](../docs/SETUP.md)** (section 5 — ESP-Fi HAR).

## ESP-Fi HAR (primary)

| Item | Value |
| --- | --- |
| Local path | `data/raw/esp-fi-har/` |
| License | CC BY 4.0 |
| Archive SHA-256 | `85f3df633c5b1a48ca4b1423467fce22821b21eeb3eed085a8d9f983dc156660` |
| Source repository | https://github.com/AutoSmartGroup/ESP-Fi-HAR |
| Source commit used for the folder map | `c8bf6aa0d680fa02695c85a82b05e79b3ebb10c4` |
| Expected grid | 4 scenarios × 8 participants × 7 activities × 10 trials = 2240 matrices and 2240 raw CSVs |
| Matrix | `CSIamp`, shape `(950, 52)`, amplitude only |

The MAT file does not store a sample rate, a phase array, or an antenna axis. Those fields stay empty on `CsiWindow`. A raw CSV can be used to observe one capture's packet rate. That observation is not copied onto the matrix.

Label map used by this repository, measured from the published class folders:

| Code | Folder label | README label |
| --- | --- | --- |
| 1 | run | run |
| 2 | walk | fall |
| 3 | jump | walk |
| 4 | squat | turn |
| 5 | arm_wave | jump |
| 6 | turn | squat |
| 7 | fall | arm wave |

Only scenario 3 was published as class folders. Labels for scenarios 1, 2, and 4 use this table and are unverified. Scenario 3's archive directory is named boardrooms; the README calls it a meeting room.

The published `train_amp` (490 files, participants 2–8) and `test_amp` (70 files, participant 1) folders are scenario 3 only. They do not share sessions or participants. They are a leakage check, not the evaluation split. Evaluation splits are described in `reports/esp_fi_split_methodology.md`.

## CSI-Bench HAR (secondary, not acquired)

No Kaggle credential was available, so the files were not downloaded. Dataset license: CC BY-NC-ND 4.0. The benchmark code is reference-only and is not vendored. Do not redistribute the data or derivatives. Experiments stay blocked until a local HAR subset is present and the non-commercial, no-derivatives terms are still respected. Status: `reports/csi_bench_status.md`.

## Embedded WiFi Sensing HAR (optional, inspection only)

Local activity text files, when present, live under `data/raw/embedded-wifi-sensing/Datasets/Activity/`. The repository code is MIT and the paper is CC BY 4.0. Volunteer consent described by the authors is for academic research. This project does not assume commercial rights to the recordings. Counting files is allowed. Training, reported metrics, and publication use are not. `assert_cleared_for_experiment()` raises. Status: `reports/embedded_inspection.md`.
