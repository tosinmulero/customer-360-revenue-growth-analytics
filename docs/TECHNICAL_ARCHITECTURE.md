# 🏗️ Technical Architecture

## Overview

Customer 360 & Revenue Growth Analytics is structured as a layered analytical solution rather than a single dashboard file.

The design separates transformation, analysis, statistical modelling and presentation so each layer can be inspected independently.

## Architecture

```mermaid
flowchart TD
    A["Google GA4 public sample e-commerce data"]
    B["SQL transformation layer"]
    C["Processed analytical datasets"]
    D["Python customer analytics"]
    E["Revenue forecasting"]
    F["Synthetic A/B experiment"]
    G["Synthetic marketing campaign layer"]
    H["Statistical testing & campaign metrics"]
    I["Power BI semantic model"]
    J["Power BI report layer"]
    K["Executive / commercial decision support"]

    A --> B
    B --> C
    C --> D
    C --> E
    C --> I
    F --> H
    G --> H
    D --> I
    E --> I
    H --> I
    I --> J
    J --> K
```

## 🔵 SQL transformation
Covers customer, acquisition, conversion, retention, RFM, product, device, KPI and revenue analysis.

## 🟢 Processed analytical data
`data/processed/` contains reusable outputs for Python and Power BI.

## 🟣 Python customer analytics
Validation, KPIs, segmentation, cohorts, acquisition, product and device analysis.

## 🟠 Statistical modelling
Holt damped-trend forecasting, holdout evaluation, synthetic A/B testing and campaign-efficiency analysis.

## 🟡 Power BI semantic model
PBIP/PBIR/TMDL source-controlled definitions keep the BI implementation inspectable in Git.

## 🧭 Data provenance

Observed analytical data derive from Google GA4 public sample e-commerce data.

Synthetic components are limited to A/B experiment observations and campaign economics. They are explicitly labelled throughout the project.

## Engineering principles

- separation of concerns
- reusable analytical layers
- source control
- reproducibility
- explicit data provenance
- automated quality checks
- transparent limitations
