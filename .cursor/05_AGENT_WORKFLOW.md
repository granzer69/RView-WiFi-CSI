# Cursor Agent Workflow --- WiFi CSI Human Activity Sensing

## 1. Purpose

This file controls how Cursor should use AI models and agents while
building the project.

The user has a **Cursor Pro / \$20-class plan** and wants high-quality
results while avoiding wasteful use of expensive third-party models.

Current Cursor documentation distinguishes a Cursor Models pool
(including Grok 4.7/4.6/4.5 and Composer 2.5) from an Other Models pool
containing third-party models. Cursor describes Grok 4.7 as its flagship
model and Composer 2.5 as a fast, cost-efficient agentic coding model.

Therefore:

> **Use Composer aggressively for routine implementation. Reserve Grok
> 4.7 and third-party frontier models for genuinely difficult
> reasoning/review tasks.**

Do not burn expensive model usage on trivial edits.

## 2. Model hierarchy

### Tier 0 --- Human approval

The user is the final decision maker.

Ask before:

-   major architecture changes
-   dataset replacement
-   scope changes
-   destructive refactors
-   deleting working systems
-   adding major infrastructure
-   adopting a major external repository
-   changing the core research question

### Tier 1 --- Composer 2.5

**Default implementation model.**

Use for:

-   routine coding
-   file creation
-   boilerplate
-   tests
-   API routes
-   React components
-   styling
-   refactoring
-   simple bug fixes
-   documentation
-   repetitive dataset adapters
-   command/script creation
-   straightforward debugging

Do NOT escalate just because a task is long.

Composer should be the workhorse.

### Tier 2 --- Grok 4.7

Use for high-value reasoning.

Use for:

-   project-wide planning
-   architecture decisions
-   difficult CSI pipeline reasoning
-   dataset suitability analysis
-   complicated ML design
-   cross-module debugging
-   difficult performance problems
-   reviewing a large implementation
-   determining why experiments disagree
-   research synthesis
-   evaluating competing approaches

Use standard/normal Grok before fast variants when deep reasoning is
needed.

Do not use Grok for a one-line bug fix.

### Tier 3 --- Other frontier models

Third-party models are an escalation tier.

Use only when:

-   an independent second opinion is valuable
-   a difficult research/ML design decision remains unresolved
-   a major code review needs adversarial checking
-   the user explicitly requests a second-model review

Preferred uses:

-   independent architecture critique
-   independent research synthesis
-   difficult scientific reasoning
-   final pre-release audit

Do not use third-party models for routine coding.

## 3. Model allocation philosophy

Default:

``` text
~70–85% of coding work
→ Composer

~10–20% of difficult reasoning
→ Grok

~0–10% exceptional second opinions
→ third-party frontier model
```

These are workflow targets, not billing guarantees.

The exact usage should be adapted based on actual Cursor usage
dashboards.

## 4. Do not use expensive models sequentially for the same trivial task

Bad:

``` text
Grok writes code
→ Claude rewrites it
→ GPT rewrites it
→ Composer formats it
```

Good:

``` text
Grok plans
→ Composer implements
→ Composer tests/fixes
→ Grok reviews only if risk is high
```

## 5. Standard task loop

For each implementation task:

### Step 1 --- Understand

Read:

-   relevant `.cursor` files
-   existing code
-   tests
-   configuration
-   relevant research notes

Do not start coding immediately.

### Step 2 --- Plan

For small tasks, create a short plan internally.

For medium/large tasks, write a concise implementation plan before
editing.

### Step 3 --- Implement

Use Composer unless the task clearly requires deeper reasoning.

### Step 4 --- Test

Run:

-   unit tests
-   type checks
-   lint
-   relevant integration tests

### Step 5 --- Inspect

Read actual failures.

Do not guess.

### Step 6 --- Fix

Use Composer for normal fixes.

Escalate to Grok when:

-   the same bug survives two reasonable fixes
-   the problem crosses multiple modules
-   the root cause is architectural
-   scientific/data leakage concerns appear

### Step 7 --- Document

Update the relevant documentation.

### Step 8 --- Commit

Create a meaningful commit.

## 6. Parallel agents

Use parallel agents only when tasks are genuinely independent.

Good:

``` text
Agent A → dataset research
Agent B → repository research
Agent C → preprocessing design
```

Bad:

``` text
Agent A edits preprocessing.py
Agent B edits preprocessing.py
Agent C edits preprocessing.py
```

Never allow multiple agents to modify the same critical files
concurrently unless the merge strategy is explicit.

## 7. Recommended agent roles

### Research Scout

Find:

-   datasets
-   papers
-   GitHub repositories
-   implementations
-   licenses
-   benchmark information

Model: Composer for broad search; Grok for synthesis.

### Data Engineer

Build:

-   dataset adapters
-   parsers
-   validation
-   canonical representation

Model: Composer.

### Signal Processing Engineer

Build:

-   filtering
-   normalization
-   segmentation
-   FFT/STFT
-   PCA
-   feature extraction

Model: Composer for implementation; Grok for difficult signal-processing
decisions.

### ML Engineer

Build:

-   training
-   evaluation
-   classical baselines
-   deep models
-   experiment tracking

Model: Composer for implementation; Grok for model/experiment strategy.

### Backend Engineer

Build:

-   FastAPI
-   WebSockets
-   session services
-   inference API

Model: Composer.

### Frontend Engineer

Build:

-   React
-   TypeScript
-   dashboard
-   charts

Model: Composer.

### QA/Reviewer

Review:

-   correctness
-   leakage
-   reproducibility
-   API contracts
-   tests
-   architecture drift

Model: Composer for normal QA; Grok for final/high-risk review.

## 8. Research-first rule

Before implementing a major component, search for existing solutions.

Search:

1.  GitHub
2.  Papers
3.  Official documentation
4.  Dataset documentation
5.  Reference implementations

Do not reinvent:

-   ESP32 CSI acquisition
-   CSI parsers
-   dataset loaders
-   benchmark evaluation code
-   standard ML architectures

unless there is a good reason.

## 9. Repository reuse protocol

For every useful repository:

1.  Find the original repository.
2.  Read README.
3.  Inspect directory structure.
4.  Inspect license.
5.  Identify active/maintained status.
6.  Identify dependencies.
7.  Inspect relevant code.
8.  Determine exactly what can be reused.
9.  Record attribution.
10. Prefer adaptation over blind copying.

Classify:

``` text
USE DIRECTLY
ADAPT
REFERENCE ONLY
AVOID
```

Never copy an entire repository into this project just because it works.

## 10. Important candidate repositories

Initial research has identified these useful starting points.

### Espressif ESP-CSI

Official ESP32 CSI ecosystem.

Useful for:

-   CSI acquisition
-   receiver/sender examples
-   parsing tools
-   human detection examples
-   future hardware integration

Repository: https://github.com/espressif/esp-csi

This should be the primary reference for ESP32 CSI acquisition rather
than an unofficial firmware stack.

### CSI-Bench

Useful for:

-   heterogeneous CSI data
-   Human Activity Recognition
-   cross-user/environment/device evaluation
-   benchmark training/evaluation
-   model comparison

Repository:
https://github.com/guozhen-jenn-zhu/CSI-Bench-Real-WiFi-Sensing-Benchmark

Important: The repository's code is MIT licensed, but the project
repository also identifies the dataset/code release terms separately.
Verify the exact dataset license before redistribution. Do not assume
code license equals dataset license.

### ESP-Fi HAR

Useful for:

-   ESP32-derived CSI HAR
-   public activity dataset
-   PyTorch benchmark
-   CNN
-   ResNet
-   LSTM
-   GRU
-   Transformer
-   MobileNetV3
-   EfficientNetLite
-   CPU latency evaluation

Repository: https://github.com/AutoSmartGroup/ESP-Fi-HAR

The repository states that its code is MIT licensed and the dataset is
CC BY 4.0. Preserve attribution/citation requirements.

### Embedded WiFi Sensing

Useful for:

-   ESP32 CSI collection
-   preprocessing scripts
-   datasets
-   embedded model examples
-   TensorFlow Lite Micro deployment

Repository: https://github.com/AlbanyArmenta0711/Embedded_WiFi_Sensing

Use as a reference for the future hardware phase.

### RuView

Useful as a conceptual/reference project because it targets:

-   WiFi sensing
-   presence
-   activity recognition
-   spatial intelligence
-   edge deployment

Repository: https://github.com/ruvnet/RuView

Important: RuView is a large project with its own architecture and
assumptions. Do not turn this project into a clone of RuView. Extract
useful ideas only.

### Approximate ESP32 human-sensing project

Repository:
https://github.com/everythingfreee/ESP32-WiFi-CSI-Human-Sensing

Useful for:

-   end-to-end architecture ideas
-   CSI parsing
-   dataset collection
-   feature extraction
-   presence + movement + approximate position
-   session-based data splitting

Use especially as a reference for avoiding row-level leakage.

### wifi_sense

Repository: https://github.com/francose/wifi_sense

Useful for:

-   CSI receiver ideas
-   signal visualization
-   spectral analysis
-   ESP32-S3 CSI integration concepts

Treat hardware compatibility carefully.

## 11. Dataset selection rule

Do not select a dataset simply because it has the highest reported
accuracy.

Score candidate datasets on:

``` text
Activity coverage
+
Subject diversity
+
Environment diversity
+
Device diversity
+
Metadata quality
+
Accessibility
+
License
+
Reproducibility
+
Compatibility with future ESP32 integration
```

A slightly less convenient but more diverse dataset may be more
scientifically valuable.

## 12. Current dataset candidates

At minimum investigate:

-   CSI-Bench
-   ESP-Fi HAR
-   SignFi
-   ARIL
-   StanWiFi
-   WiFall
-   any additional dataset discovered during research

Do not download every dataset.

Start with one primary dataset and one secondary validation dataset.

## 13. Literature-to-code rule

The uploaded literature survey identifies:

-   CSI preprocessing
-   PCA
-   FFT/STFT
-   spectrograms
-   statistical features
-   CNN
-   LSTM
-   attention
-   transformers
-   few-shot/generalization
-   cross-user/environment/device evaluation

Use these as candidate approaches, not mandatory components.

The literature specifically emphasizes that high benchmark accuracy may
not transfer across users, environments and devices. Therefore the
implementation should make generalization experiments first-class.

## 14. Research claims rule

Never write:

> "Our model is state-of-the-art."

unless the evidence supports it.

Prefer:

> "Our model achieved X on dataset Y under split Z."

Always state:

-   dataset
-   split
-   preprocessing
-   model
-   metric
-   seed where relevant

## 15. Model escalation rules

### Stay on Composer when:

-   implementing a known architecture
-   writing tests
-   fixing normal bugs
-   writing API routes
-   writing React components
-   creating dataset loaders
-   refactoring

### Escalate to Grok when:

-   model architecture selection is unclear
-   data leakage is suspected
-   preprocessing is scientifically questionable
-   several approaches produce contradictory results
-   cross-domain performance collapses
-   a major architecture decision is needed
-   a difficult bug crosses multiple subsystems

### Escalate to third-party frontier model when:

-   Grok + Composer cannot resolve a major issue
-   independent review is scientifically valuable
-   user requests an adversarial review
-   final architecture/research audit is needed

## 16. User approval protocol

The user wants approval before major decisions.

Therefore use:

``` text
PROPOSAL
Problem:
Options:
Recommendation:
Why:
Risks:
Expected files affected:
```

Then wait for approval.

Do not continue with the major decision until the user approves.

## 17. Autonomy boundary

Cursor may independently:

-   inspect code
-   run tests
-   fix routine bugs
-   create tests
-   refactor locally
-   update documentation
-   improve error handling
-   implement approved plans

Cursor must ask before:

-   changing scope
-   replacing datasets
-   changing major architecture
-   adopting a major external project
-   deleting major functionality
-   changing evaluation methodology
-   changing the research objective

## 18. Final principle

> **Cheap model for execution. Strong model for thinking. Human for
> major decisions.**

The objective is not to maximize AI usage.

The objective is to maximize project progress per unit of model usage.
