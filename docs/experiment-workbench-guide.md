# Experiment Workbench — User Guide

## Overview

The workbench runs the same training code as `scripts/train_*.py`, but stores outputs under **`artifacts/workbench/<family>/<run_id>/`** instead of frozen `artifacts/v2_*` baselines.

## Configure a run

1. Open **Experiments** (`/experiments`).
2. Choose **family** (logreg, rf, cnn1d, gru), **seed**, and **split strategies**.
3. Edit only hyperparameters listed for that family (unknown keys are rejected).
4. Click **Preview config** to see the resolved YAML and CLI export hint.
5. Click **Start run** — only one run executes at a time.

## Monitor results

The run registry polls every few seconds. When status is **completed**, open **Metrics** to read `metrics.json` for `in_domain` test scores.

## Reproduce from CLI

Each run writes `artifacts/workbench/<family>/<run_id>/workbench_config.yaml`. Example:

```bash
python3 scripts/train_logreg.py \
  --run-id <run_id> \
  --artifacts-root artifacts/workbench/logreg \
  --config artifacts/workbench/logreg/<run_id>/workbench_config.yaml
```

## Compare runs

Use `POST /experiments/compare` with `run_ids` and `strategy`. The API checks that `assignment_sha256` matches across runs before treating comparisons as split-compatible.
