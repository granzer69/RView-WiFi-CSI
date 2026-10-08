# WiFi CSI Human Activity Sensing --- Version Roadmap

## Overview

The project is intentionally divided into versions so that every stage
is independently useful.

``` text
V1
Data Foundation
      ↓
V2
ML/HAR Engine
      ↓
V3
Real-Time Software Platform
      ↓
V4
ESP32 Hardware Integration
      ↓
V5 (Optional)
Advanced Sensing / Tracking / Robustness
```

------------------------------------------------------------------------

# V1 --- CSI DATA FOUNDATION

## Goal

Build a reliable software foundation using real public CSI data.

## V1.1 Research and dataset discovery

-   Search public CSI datasets.
-   Prefer datasets with:
    -   real recordings
    -   human activity labels
    -   subject/environment metadata
    -   permissive research-use conditions
    -   reproducible access
-   Record dataset licenses.
-   Record dataset shape and sampling information.
-   Do not download huge datasets blindly.

## V1.2 Dataset adapters

Create:

``` python
DatasetAdapter
```

with operations conceptually equivalent to:

``` python
load()
metadata()
labels()
sample()
statistics()
```

Each dataset gets its own adapter.

## V1.3 Canonical CSI representation

Create an internal representation that can support:

-   batch dimension
-   temporal dimension
-   subcarrier dimension
-   antenna/link dimensions where available
-   amplitude
-   phase
-   metadata

Do not force every dataset into an identical physical format if
information would be lost.

## V1.4 Visualization

Build:

-   raw amplitude plots
-   phase plots when meaningful
-   subcarrier heatmaps
-   temporal windows
-   spectrograms
-   class examples

## V1.5 V1 acceptance

V1 is complete when a new developer can:

1.  install dependencies
2.  load the selected dataset
3.  inspect statistics
4.  visualize samples
5.  create a reproducible split
6.  save processed data

------------------------------------------------------------------------

# V2 --- ML/HAR ENGINE

## Goal

Create a credible model comparison system.

## V2.1 Feature pipeline

Implement configurable feature extraction.

## V2.2 Classical baselines

Run:

-   SVM
-   Random Forest
-   gradient boosting where justified

## V2.3 Deep learning

Run:

-   1D CNN
-   LSTM
-   GRU
-   CNN-LSTM
-   attention/Transformer

Do not assume all models are equally appropriate for all datasets.

## V2.4 Evaluation

Required:

-   accuracy
-   macro F1
-   weighted F1
-   precision
-   recall
-   confusion matrix
-   per-class metrics

Strongly recommended:

-   parameter count
-   inference latency
-   model size
-   training duration

## V2.5 Generalization

Where metadata allows:

-   cross-user
-   cross-environment
-   cross-device

This is a major project differentiator.

## V2.6 Model registry

Store:

``` text
model/
preprocessing/
label_map/
dataset_version/
training_config/
metrics/
```

as one reproducible artifact.

## V2 acceptance

At least:

-   3 classical/deep model families evaluated
-   leakage-free evaluation
-   reproducible training
-   saved best model
-   evaluation report generated automatically

------------------------------------------------------------------------

# V3 --- REAL-TIME SOFTWARE PLATFORM

## Goal

Turn the ML project into an actual application.

## V3.1 Inference service

Stable inference API.

## V3.2 Dataset replay

Replay recorded CSI as if it were a live stream.

## V3.3 Backend

FastAPI.

## V3.4 Streaming

WebSocket-based prediction stream.

Example event:

``` json
{
  "timestamp": 0,
  "activity": "walking",
  "confidence": 0.94,
  "presence": true,
  "model_version": "cnn_lstm_v1"
}
```

## V3.5 Frontend

React + TypeScript.

Display:

-   current activity
-   confidence
-   presence
-   signal plots
-   recent predictions
-   session timeline
-   model status

## V3.6 Evaluation dashboard

Show:

-   confusion matrix
-   class metrics
-   latency
-   model size
-   experiment summary

## V3 acceptance

A user can start a replay session and see live predictions in the
browser without hardware.

------------------------------------------------------------------------

# V4 --- ESP32 HARDWARE INTEGRATION

## Goal

Replace the replay/data source with real CSI captured from ESP32.

## V4.1 Firmware

Use the official Espressif CSI ecosystem as the starting point.

Do not write a custom CSI stack unless required.

## V4.2 Receiver adapter

Convert ESP32 output to the canonical CSI schema.

## V4.3 Data validation

Measure:

-   packet rate
-   packet loss
-   CSI shape
-   missing samples
-   signal stability

## V4.4 Hardware dataset

Collect controlled sessions.

Record:

-   subject
-   activity
-   environment
-   device placement
-   router/AP conditions
-   date/time
-   session ID

## V4.5 Hardware model evaluation

Do not assume the public-dataset model transfers perfectly.

Evaluate:

``` text
Public dataset model
        ↓
ESP32 real data
        ↓
performance
```

If necessary:

``` text
public data
+
ESP32 calibration data
        ↓
fine-tuned/adapted model
```

## V4.6 Live demonstration

Final path:

``` text
ESP32
 ↓
CSI receiver
 ↓
Preprocessing
 ↓
ML inference
 ↓
FastAPI
 ↓
WebSocket
 ↓
React dashboard
```

## V4 acceptance

A live ESP32 CSI stream reaches the same inference engine used by V3 and
produces a live dashboard prediction.

------------------------------------------------------------------------

# V5 --- OPTIONAL ADVANCED RESEARCH

Only start after V4 is stable.

Possible modules:

-   tracking/localization
-   multi-person sensing
-   cross-environment adaptation
-   few-shot adaptation
-   model compression
-   edge inference
-   fall-detection robustness
-   domain adaptation
-   uncertainty estimation

## Priority rule

Never sacrifice V1--V4 completion for V5 features.

A complete HAR system is more valuable than a half-built tracking
system.

------------------------------------------------------------------------

# Version dependency rule

``` text
V1 must work before V2.
V2 must work before V3.
V3 must work before V4.
V4 must work before V5.
```

Exceptions require explicit user approval.
