# WiFi CSI Human Activity Sensing --- System Architecture

## 1. Architecture principle

The system must separate **data source**, **signal processing**, **ML
inference**, **application services**, and **presentation**.

The same inference pipeline must accept:

-   public dataset input
-   replayed dataset input
-   future ESP32 live input

without changing the model contract.

## 2. High-level architecture

``` text
                         DATA SOURCES
                              │
              ┌───────────────┼────────────────┐
              │               │                │
              ▼               ▼                ▼
       Public Dataset    Replay Engine     ESP32 Adapter
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                    ┌───────────────────┐
                    │ CSI INGESTION     │
                    │ Canonical Schema  │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ VALIDATION        │
                    │ Shape/Quality     │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ PREPROCESSING     │
                    │ Filter/Normalize  │
                    │ Window/PCA/etc.   │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ REPRESENTATION    │
                    │ Features / Raw    │
                    │ Spectrogram/TF    │
                    └─────────┬─────────┘
                              ▼
                    ┌───────────────────┐
                    │ ML INFERENCE      │
                    │ Model Registry    │
                    └─────────┬─────────┘
                              ▼
                 ┌────────────┴────────────┐
                 │                         │
                 ▼                         ▼
          REST API                    WebSocket
                 │                         │
                 └────────────┬────────────┘
                              ▼
                    ┌───────────────────┐
                    │ REACT DASHBOARD   │
                    └───────────────────┘
```

## 3. Canonical data contract

The ingestion layer should expose a normalized object conceptually like:

``` python
CsiWindow(
    samples=...,
    timestamp=...,
    sample_rate=...,
    subcarriers=...,
    antennas=...,
    amplitude=...,
    phase=...,
    metadata=...
)
```

Do not hard-code a fake schema before inspecting the selected datasets.

The exact implementation must be based on real dataset structures.

## 4. Data source abstraction

Use an adapter interface.

``` text
DatasetAdapter
ReplayAdapter
ESP32Adapter
```

All must eventually emit the same canonical representation.

### DatasetAdapter

Responsible for:

-   file reading
-   metadata
-   labels
-   dataset-specific parsing

### ReplayAdapter

Responsible for:

-   timing
-   streaming recorded windows
-   repeat/pause/speed controls

### ESP32Adapter

Responsible for:

-   serial/UDP input
-   ESP32-specific parsing
-   packet validation
-   conversion to canonical representation

It must NOT contain ML logic.

## 5. CSI processing architecture

``` text
Raw CSI
  ↓
Packet/sample validation
  ↓
Outlier handling
  ↓
Missing-value handling
  ↓
Amplitude/phase extraction
  ↓
Normalization
  ↓
Temporal windowing
  ↓
Optional PCA
  ↓
Optional FFT/STFT
  ↓
Model representation
```

Every operation should be modular.

## 6. Representation strategies

The architecture should support at least:

### A. Hand-crafted features

Suitable for classical ML.

Examples:

-   mean
-   variance
-   standard deviation
-   energy
-   entropy
-   correlation
-   skewness
-   kurtosis
-   frequency-domain statistics

### B. Raw/structured CSI

Suitable for deep neural networks.

### C. Spectrogram/time-frequency

Suitable for CNN-style models.

### D. Temporal sequences

Suitable for LSTM/GRU/Transformer models.

The project should compare representations rather than assuming one is
universally best.

## 7. ML architecture

``` text
                    CSI window
                        │
            ┌───────────┼───────────┐
            │           │           │
            ▼           ▼           ▼
       Features       1D CNN    Time-series
            │                       │
            ▼                       ▼
         SVM/RF              LSTM/GRU/CNN-LSTM
                                    │
                                    ▼
                               Transformer
```

Model selection must be experiment-driven.

## 8. Model registry

Each trained model must have:

``` text
model artifact
model type
dataset version
label mapping
preprocessing config
input shape
training config
random seed
metrics
creation timestamp
git commit
```

Never load a model without verifying that its preprocessing
configuration matches the input.

## 9. Inference contract

Conceptually:

``` python
result = inference_engine.predict(window)
```

Return:

``` json
{
  "activity": "walking",
  "confidence": 0.94,
  "presence": true,
  "probabilities": {},
  "model_version": "cnn_lstm_v1",
  "latency_ms": 12.4
}
```

The exact schema may evolve, but frontend code must not directly access
model internals.

## 10. Backend architecture

FastAPI handles:

-   model discovery
-   prediction
-   session lifecycle
-   replay control
-   WebSocket streaming
-   health checks
-   experiment/result access

Keep business logic outside route functions.

Recommended conceptual structure:

``` text
api/
├── routes/
├── schemas/
├── services/
└── websocket/
```

## 11. Frontend architecture

React + TypeScript.

Conceptual modules:

``` text
frontend/
├── pages/
├── components/
├── hooks/
├── services/
├── types/
└── charts/
```

The frontend should be data-driven.

It should not contain preprocessing or model logic.

## 12. Real-time flow

``` text
CSI source
   ↓
window buffer
   ↓
preprocessing
   ↓
inference
   ↓
prediction event
   ↓
WebSocket
   ↓
React state
   ↓
dashboard
```

Use bounded buffers to prevent memory growth.

## 13. Hardware integration architecture

When hardware arrives:

``` text
ESP32
  ↓
Wi-Fi CSI
  ↓
serial/UDP
  ↓
ESP32Adapter
  ↓
CsiWindow
  ↓
existing preprocessing
  ↓
existing inference
```

Do not create:

``` text
ESP32 → separate ML system
```

There must be one inference engine.

## 14. Database/storage

Use a database only where it adds value.

Potential PostgreSQL entities:

-   sessions
-   predictions
-   experiments
-   model_versions
-   datasets

Do not put raw CSI blobs into PostgreSQL by default.

Large/raw CSI data should remain in file/object storage or structured
dataset files.

## 15. Observability

Record:

-   inference latency
-   input quality
-   prediction confidence
-   model version
-   session ID
-   error state

Do not collect unnecessary personal information.

## 16. Security

Minimum:

-   input validation
-   bounded payloads
-   CORS configured deliberately
-   no secrets in Git
-   environment variables for credentials
-   dependency pinning
-   safe file handling

## 17. Research integrity

Every experiment must be traceable to:

``` text
dataset
→ preprocessing
→ split
→ model
→ seed
→ metrics
```

Never silently change preprocessing between experiments.

## 18. Architecture rule

The architecture should be simple enough for a B.Tech project but
rigorous enough to support research experiments.

Avoid microservices unless a real requirement appears.
