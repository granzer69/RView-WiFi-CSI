# WiFi CSI Human Activity Sensing --- Project Vision

## 1. Purpose

This repository is the engineering implementation of a B.Tech final-year
project on **Wi-Fi Channel State Information (CSI)-based Human Activity
Sensing**.

The primary goal is to build a serious, research-grounded software
system that can ingest real CSI data, process it, train and compare
multiple machine-learning/deep-learning approaches, perform inference,
expose the inference engine through an API, visualize results in a web
dashboard, and finally accept live CSI from ESP32 hardware.

The project must be built **software-first**.

Hardware is deliberately postponed until the software pipeline is
stable. The final ESP32 integration must plug into the already-tested
ingestion interface instead of forcing a rewrite of the
ML/backend/frontend layers.

## 2. Core problem

Wi-Fi CSI contains information about changes in the wireless propagation
environment. Human movement changes multipath propagation, producing
measurable changes in CSI amplitude and, when properly calibrated,
phase.

The project focuses primarily on **Human Activity Recognition (HAR)**.

The broader sensing capability is treated as an extensible architecture:

-   Human presence / occupancy
-   Human activity recognition
-   Gesture recognition
-   Fall detection
-   Basic movement state recognition
-   Optional localization/tracking research module
-   Optional future vital-sign sensing module

The primary final deliverable is HAR. Tracking/localization is an
advanced extension and must not be allowed to block the core project.

## 3. Intended activity classes

The initial activity taxonomy should be designed to support:

-   No person / empty
-   Standing
-   Sitting
-   Walking
-   Running
-   Lying
-   Bending
-   Falling
-   Hand/arm movement
-   Gesture classes where the selected dataset supports them

Do not assume that every dataset contains every class. The data layer
must use dataset-specific label mappings and a normalized internal
taxonomy.

The system must support adding activities without rewriting the
pipeline.

## 4. Research philosophy

The project is not simply an accuracy-maximization exercise.

The literature repeatedly identifies generalization as a major
unresolved problem: CSI distributions change across users, environments,
devices, hardware configurations, and signal conditions.

Therefore, the system should prioritize:

1.  Correct dataset handling
2.  Leakage-free evaluation
3.  Cross-user evaluation where available
4.  Cross-environment evaluation where available
5.  Cross-device evaluation where available
6.  Reproducibility
7.  Robust preprocessing
8.  Model comparison
9.  Latency and computational-cost measurement
10. Honest reporting of limitations

Accuracy alone is insufficient.

## 5. Software-first strategy

### V1 --- Data foundation

Use public real CSI datasets.

Build:

-   dataset registry
-   download/import instructions
-   dataset adapters
-   metadata validation
-   label normalization
-   CSI tensor representation
-   preprocessing primitives
-   visualization
-   reproducible train/validation/test splitting

### V2 --- ML/HAR engine

Build and compare multiple models.

Classical baselines:

-   Logistic Regression where appropriate
-   SVM
-   Random Forest
-   XGBoost or equivalent gradient boosting

Deep models:

-   1D CNN
-   LSTM
-   GRU
-   CNN-LSTM
-   Transformer/time-series attention model

The exact final shortlist must be determined after inspecting dataset
shape and literature/repository implementations.

### V3 --- Real-time software platform

Build:

-   inference engine
-   model registry
-   FastAPI backend
-   WebSocket streaming
-   session management
-   React + TypeScript dashboard
-   CSI visualization
-   live prediction visualization
-   metrics/reporting
-   dataset replay engine

The replay engine must make prerecorded CSI behave like a live stream.

### V4 --- Hardware integration

When ESP32 hardware becomes available:

ESP32 CSI capture → receiver adapter → normalized CSI schema → existing
preprocessing → existing inference engine → existing FastAPI/WebSocket
layer → existing dashboard.

Hardware integration must be an adapter, not a new application.

## 6. What this project is NOT

Do not:

-   fabricate experimental results
-   claim synthetic CSI results as real-world performance
-   train and test on correlated samples split randomly by row if this
    causes leakage
-   copy an entire external repository without understanding it
-   blindly fork a project and call it our contribution
-   claim exact localization without ground-truth validation
-   claim medical diagnosis or clinical capability
-   make hardware the dependency for initial development
-   optimize the frontend before the data/ML pipeline is correct
-   chase the newest model simply because it exists
-   add unnecessary microservices
-   introduce cloud infrastructure unless it provides a clear project
    benefit

## 7. Engineering objective

The final repository should look like a serious research-engineering
system:

-   modular
-   reproducible
-   testable
-   documented
-   versioned
-   measurable
-   explainable
-   easy to extend
-   honest about limitations

## 8. Success criteria

The project is considered successful when:

### Minimum

-   A public real CSI dataset can be loaded.
-   CSI can be visualized and preprocessed.
-   At least one classical ML baseline works.
-   At least two deep-learning models work.
-   Evaluation is reproducible.
-   Predictions can be exposed through an API.
-   A web dashboard can display predictions.

### Strong

-   Multiple model families are compared.
-   Session/user/environment-aware splits are implemented.
-   Cross-domain evaluation is included where dataset structure allows.
-   Real-time dataset replay works through WebSockets.
-   Model artifacts and preprocessing configuration are versioned.
-   Hardware can later be connected through a documented adapter.

### Excellent

-   Multiple datasets are evaluated.
-   A model/generalization strategy is tested across datasets or
    domains.
-   Hardware integration works with ESP32 CSI.
-   Live inference is demonstrated.
-   Latency and resource usage are measured.
-   The final report distinguishes benchmark performance from real-world
    claims.

## 9. Research basis

The project's literature survey identifies the general CSI pipeline as:

CSI acquisition → signal conditioning → feature/representation
extraction → ML/DL inference.

It also identifies denoising, outlier removal, interpolation,
normalization, PCA, time-frequency transformation, Doppler/spectrogram
representations and temporal segmentation as common processing
approaches.

Recent work emphasizes CNNs, LSTMs, attention and transformer-style
temporal models, while cross-user, cross-environment and cross-device
generalization remain major challenges.

Use the literature survey in this repository as a research starting
point, but verify technical details against original papers/repositories
before implementing or citing them.

## 10. Primary design principle

> **Build the stable interfaces first. Improve the intelligence behind
> those interfaces second.**

The ingestion layer, preprocessing layer, inference interface, API
contract and dashboard contract must remain stable as models and
datasets change.
