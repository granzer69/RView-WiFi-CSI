"""CSI-Bench HAR is a secondary validation set that is not local yet.

The Kaggle dataset is CC BY-NC-ND 4.0. The benchmark code repository has an
MIT LICENSE file and a README that also says CC BY-NC-ND. Approved policy:
code is reference-only, data stays local, and nothing is redistributed.
This environment has no Kaggle credential, so the files were not downloaded.
"""

from __future__ import annotations

from common.errors import LicenseError

DATASET_LICENSE = "CC-BY-NC-ND-4.0"
CODE_POLICY = "reference_only"
ACQUISITION = "blocked_no_kaggle_credentials"
SOURCE_DATA = "https://www.kaggle.com/datasets/guozhenjennzhu/csi-bench"
SOURCE_CODE = "https://github.com/guozhen-jenn-zhu/CSI-Bench-Real-WiFi-Sensing-Benchmark"


def assert_cleared_for_experiment() -> None:
    raise LicenseError(
        "CSI-Bench HAR is not available for experiments. It was not downloaded "
        f"({ACQUISITION}). When a local copy exists, use only the HAR subset, "
        "cite CC BY-NC-ND 4.0, do not redistribute the files or derivatives, "
        "and do not copy the benchmark code. "
        f"Code policy: {CODE_POLICY}."
    )


def status() -> dict[str, str]:
    return {
        "acquisition": ACQUISITION,
        "dataset_license": DATASET_LICENSE,
        "code_policy": CODE_POLICY,
        "data_url": SOURCE_DATA,
        "code_url": SOURCE_CODE,
        "experiment_use": "blocked",
    }
