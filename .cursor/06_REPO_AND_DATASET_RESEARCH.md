# Repository and Dataset Research Registry

## Purpose

This document is a living registry of external repositories, datasets
and research implementations that may accelerate the WiFi CSI Human
Activity Sensing project.

Cursor must update this document whenever it discovers a significant new
resource.

## Rules

For every resource record:

-   URL
-   purpose
-   license
-   dataset/license distinction
-   relevant modules
-   compatibility
-   reuse classification
-   attribution requirement
-   risks
-   date checked

Never assume a repository's code license applies to its dataset.

## Initial repository registry

  --------------------------------------------------------------------------------------------------------------------------------------------
  Resource          URL                                                                         Primary value                Initial
                                                                                                                             classification
  ----------------- --------------------------------------------------------------------------- ---------------------------- -----------------
  Espressif ESP-CSI https://github.com/espressif/esp-csi                                        Official ESP32 CSI           USE/ADAPT for V4
                                                                                                acquisition, examples, tools 

  CSI-Bench         https://github.com/guozhen-jenn-zhu/CSI-Bench-Real-WiFi-Sensing-Benchmark   Large heterogeneous          ADAPT/REFERENCE
                                                                                                benchmark and                
                                                                                                training/evaluation code     

  ESP-Fi HAR        https://github.com/AutoSmartGroup/ESP-Fi-HAR                                ESP32 CSI HAR dataset +      ADAPT/REFERENCE
                                                                                                PyTorch model suite          

  Embedded WiFi     https://github.com/AlbanyArmenta0711/Embedded_WiFi_Sensing                  ESP32 collection +           ADAPT for V4
  Sensing                                                                                       preprocessing + embedded     
                                                                                                models                       

  RuView            https://github.com/ruvnet/RuView                                            Large WiFi sensing           REFERENCE ONLY
                                                                                                architecture/reference       initially

  ESP32 WiFi CSI    https://github.com/everythingfreee/ESP32-WiFi-CSI-Human-Sensing             End-to-end                   REFERENCE
  Human Sensing                                                                                 presence/movement/position   
                                                                                                example                      

  wifi_sense        https://github.com/francose/wifi_sense                                      CSI receiver/spectral        REFERENCE
                                                                                                analysis concepts            

  CSI Tool          https://github.com/oh-my-physec/esp32-csi-tool                              ESP32 CSI extraction and     REFERENCE
                                                                                                analysis                     
  --------------------------------------------------------------------------------------------------------------------------------------------

## Initial dataset candidates

### CSI-Bench

Why investigate:

-   heterogeneous real-world sensing
-   multiple tasks
-   Human Activity Recognition
-   cross-user/environment/device evaluation
-   useful benchmark infrastructure

The literature survey describes CSI-Bench as a large heterogeneous
benchmark spanning users, environments and device configurations, making
it particularly relevant to the project's generalization objective.

Repository:
https://github.com/guozhen-jenn-zhu/CSI-Bench-Real-WiFi-Sensing-Benchmark

Important: Verify current dataset access and license before use.

### ESP-Fi HAR

Why investigate:

-   ESP32-derived CSI
-   seven activities
-   four indoor environments
-   PyTorch benchmark suite
-   multiple model families
-   directly relevant to future hardware integration

Repository: https://github.com/AutoSmartGroup/ESP-Fi-HAR

The repository states:

-   code: MIT
-   dataset: CC BY 4.0

Preserve attribution and paper citation.

### SignFi

Why investigate:

-   fine-grained gesture recognition
-   CNN-based CSI classification
-   historically important HAR benchmark

Use when gesture recognition is implemented.

### ARIL / StanWiFi

Investigate as benchmark datasets because the literature survey
identifies them in CSITime evaluation.

Do not hard-code assumptions about their exact format until their
original dataset documentation is inspected.

### WiFall

Investigate for fall detection.

Use only if fall detection is included in the implemented scope.

## Dataset selection algorithm

For each candidate:

``` text
1. Is it real CSI?
2. Does it contain human activity data?
3. Are labels trustworthy?
4. Is metadata available?
5. Are subject/environment IDs available?
6. Can we perform leakage-free splits?
7. Is the dataset accessible?
8. Is its license compatible?
9. Is preprocessing reproducible?
10. Does it help future ESP32 integration?
```

Score each criterion.

## Repository reuse algorithm

``` text
DISCOVER
   ↓
READ README
   ↓
CHECK LICENSE
   ↓
INSPECT STRUCTURE
   ↓
IDENTIFY RELEVANT MODULES
   ↓
RUN/VERIFY SMALL EXAMPLE
   ↓
UNDERSTAND ASSUMPTIONS
   ↓
ADAPT ONLY WHAT WE NEED
   ↓
ATTRIBUTE
   ↓
TEST INSIDE OUR SYSTEM
```

## Do not blindly fork

A repository should be forked only if:

-   it is genuinely the correct foundation for a subsystem
-   its license permits the intended use
-   its architecture matches our project
-   maintaining the fork is cheaper than adapting components

Otherwise:

> learn from it, cite it, and implement the required interface in our
> repository.

## Research search queries

When searching for additional resources, use combinations of:

``` text
WiFi CSI human activity recognition GitHub
WiFi CSI HAR dataset GitHub
ESP32 CSI human activity recognition GitHub
ESP32 CSI dataset HAR
WiFi sensing benchmark CSI
CSI preprocessing Python WiFi sensing
CSI spectrogram human activity recognition
CSI cross environment generalization
CSI cross user activity recognition
ESP32 CSI receiver parser
ESP32 CSI WebSocket
WiFi CSI transformer HAR
WiFi CSI CNN LSTM HAR
```

Search both recent and foundational implementations.

## Evaluation resources

Prioritize repositories that contain:

-   reproducible splits
-   preprocessing scripts
-   benchmark models
-   evaluation scripts
-   latency benchmarks
-   metadata
-   session/user/environment IDs

Avoid repositories that only show a screenshot and an unexplained
accuracy number.

## Research integrity

External code may accelerate implementation, but the final project must
remain understandable by the student.

For every reused component, maintain a note:

``` text
What we reused:
Why:
Source:
License:
What we changed:
Why we changed it:
How we tested it:
```

Store these notes under:

``` text
reports/external_reuse/
```

## Current research direction

The literature survey emphasizes that generalization is a stronger
unresolved problem than basic detectability.

Therefore, repository/dataset selection should favor resources that
allow:

-   cross-user testing
-   cross-environment testing
-   cross-device testing
-   realistic indoor variation

This is more valuable than choosing a dataset only because it produces a
high in-domain accuracy.
