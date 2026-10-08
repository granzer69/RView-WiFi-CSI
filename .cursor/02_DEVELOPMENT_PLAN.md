# WiFi CSI Human Activity Sensing --- Development Plan

## 1. Development rule

Work in small, verifiable phases.

Every phase must produce a runnable artifact.

Do not start a later phase merely because the code for the previous
phase exists. The previous phase must satisfy its acceptance criteria.

Before major architectural changes, stop and ask the user for approval.

## 2. Target repository structure

Use this as the intended direction. Adjust only when implementation
evidence justifies a change.

``` text
wifi-csi-human-sensing/
├── .cursor/
│   ├── 01_PROJECT_VISION.md
│   ├── 02_DEVELOPMENT_PLAN.md
│   ├── 03_VERSION_ROADMAP.md
│   ├── 04_SYSTEM_ARCHITECTURE.md
│   ├── 05_AGENT_WORKFLOW.md
│   └── 06_REPO_AND_DATASET_RESEARCH.md
│
├── data/
│   ├── raw/
│   ├── interim/
│   ├── processed/
│   ├── metadata/
│   └── README.md
│
├── configs/
│   ├── datasets/
│   ├── preprocessing/
│   ├── models/
│   └── experiments/
│
├── src/
│   ├── ingestion/
│   ├── datasets/
│   ├── csi/
│   ├── preprocessing/
│   ├── features/
│   ├── models/
│   ├── training/
│   ├── evaluation/
│   ├── inference/
│   ├── streaming/
│   ├── api/
│   └── common/
│
├── frontend/
│
├── scripts/
├── tests/
├── notebooks/
├── experiments/
├── reports/
├── artifacts/
├── docker/
├── requirements/
├── pyproject.toml
└── README.md
```

Do not create all directories blindly on day one. Create them when the
relevant phase begins.

## 3. Phase 0 --- Project reconnaissance

### Actions

1.  Read every `.cursor/*.md` file.
2.  Inspect the current repository.
3.  Search GitHub and research sources for relevant implementations.
4.  Identify candidate datasets.
5.  Inspect licenses.
6.  Identify reusable preprocessing/model code.
7.  Identify incompatible assumptions.
8.  Produce a short implementation proposal.
9.  Ask the user for approval before major implementation.

### Deliverable

`reports/reconnaissance.md`

It must contain:

-   candidate datasets
-   candidate repositories
-   what each repository provides
-   license
-   relevance
-   code quality
-   whether to reuse, adapt, reference, or avoid
-   proposed dataset
-   proposed model shortlist
-   risks

## 4. Phase 1 --- Dataset foundation

### Actions

-   Select at least one primary real CSI dataset.
-   Create a dataset adapter interface.
-   Parse the dataset.
-   Validate metadata.
-   Normalize labels.
-   Implement deterministic splits.
-   Store preprocessing configuration.
-   Create dataset statistics.
-   Build CSI visualization tools.

### Acceptance criteria

-   One command loads the dataset.
-   One command prints dataset statistics.
-   One command visualizes representative CSI samples.
-   Labels are mapped correctly.
-   Split logic is documented.
-   Tests exist for parsing and label mapping.

## 5. Phase 2 --- CSI preprocessing

Implement modular preprocessing:

``` text
raw CSI
→ validation
→ packet/sample cleaning
→ outlier handling
→ optional interpolation
→ amplitude/phase representation
→ normalization
→ temporal segmentation
→ optional PCA
→ optional time-frequency representation
```

Every transformation must be configurable.

Never hide preprocessing inside the model.

### Acceptance criteria

-   Same raw input + same configuration = same processed output.
-   Each transformation can be enabled/disabled.
-   Intermediate representations can be inspected.
-   Unit tests exist for critical transformations.

## 6. Phase 3 --- Classical ML baselines

Start with simple models.

Recommended order:

1.  Logistic Regression where suitable
2.  SVM
3.  Random Forest
4.  Gradient boosting/XGBoost if justified

Use meaningful features such as:

-   mean
-   standard deviation
-   variance
-   RMS
-   entropy
-   energy
-   range
-   skewness
-   kurtosis
-   correlation
-   frequency-domain statistics

Do not assume hand-crafted features will beat deep learning.

### Acceptance criteria

-   Baseline metrics are recorded.
-   Confusion matrices are generated.
-   Training configuration is reproducible.
-   No data leakage exists.

## 7. Phase 4 --- Deep learning

Recommended progression:

1.  1D CNN
2.  LSTM/GRU
3.  CNN-LSTM
4.  Attention/Transformer time-series model

Only add a more complex model when the dataset representation justifies
it.

Track:

-   accuracy
-   macro F1
-   weighted F1
-   precision
-   recall
-   per-class performance
-   confusion matrix
-   training time
-   inference latency
-   parameter count
-   model size

## 8. Phase 5 --- Generalization experiments

This is an important research component.

Where dataset metadata permits, evaluate:

-   random/session split
-   cross-user split
-   cross-environment split
-   cross-device split

Do not compare numbers from incompatible splits as if they were
equivalent.

Report:

``` text
In-domain performance
vs
Cross-user performance
vs
Cross-environment performance
vs
Cross-device performance
```

## 9. Phase 6 --- Inference engine

Create a stable interface:

``` python
prediction = inference_engine.predict(csi_window)
```

The inference engine must:

-   load a versioned model
-   load matching preprocessing
-   validate input shape
-   preprocess
-   infer
-   return normalized prediction output
-   report confidence
-   optionally return intermediate diagnostics

No training should happen during inference.

## 10. Phase 7 --- Real-time replay

Build a replay adapter:

``` text
recorded CSI
→ timing controller
→ stream interface
→ inference engine
```

Support:

-   original timing
-   accelerated replay
-   paused replay
-   repeat sessions

This gives the project a live-demo path before hardware arrives.

## 11. Phase 8 --- Backend

FastAPI endpoints should include only useful APIs.

Examples:

``` text
GET  /health
GET  /models
GET  /datasets
POST /predict
POST /sessions
GET  /sessions/{id}
WS   /stream
```

Do not over-engineer.

## 12. Phase 9 --- Frontend

React + TypeScript dashboard.

Minimum screens:

-   Overview
-   Live sensing
-   CSI signal visualization
-   Prediction history
-   Model information
-   Experiment/evaluation summary

The frontend must consume backend APIs instead of directly reading ML
internals.

## 13. Phase 10 --- Hardware adapter

When ESP32 arrives:

``` text
ESP32 CSI
→ serial/UDP receiver
→ raw packet parser
→ canonical CSI schema
→ existing preprocessing
→ existing inference
```

The adapter must satisfy the same ingestion contract used by
datasets/replay.

## 14. Testing strategy

Every phase requires tests.

### Unit tests

-   parsers
-   label mapping
-   preprocessing
-   feature extraction
-   tensor shapes
-   model loading
-   API validation

### Integration tests

-   dataset → preprocessing
-   preprocessing → model
-   model → inference API
-   replay → WebSocket → frontend

### Regression tests

After each major change:

-   existing tests
-   representative inference
-   benchmark comparison
-   API smoke test

## 15. Experiment discipline

Every experiment must have:

-   dataset
-   dataset version
-   preprocessing configuration
-   model
-   hyperparameters
-   seed
-   split strategy
-   metrics
-   timestamp
-   output artifact location

Avoid undocumented notebook-only experiments.

## 16. Definition of done

A phase is not done when the code compiles.

A phase is done when:

-   implementation exists
-   tests pass
-   example command works
-   output is inspectable
-   documentation is updated
-   limitations are recorded
-   Git commit is clean and understandable

## 17. Decision gates

Cursor must ask the user before:

-   changing the core project scope
-   replacing the primary dataset
-   introducing a major framework
-   changing the architecture
-   adding a large cloud dependency
-   deleting a working subsystem
-   switching the primary ML representation
-   committing to hardware assumptions that cannot yet be tested
-   copying a significant amount of external code

Cursor may make routine implementation decisions independently.
