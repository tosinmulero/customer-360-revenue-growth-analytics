# Customer 360 & Revenue Growth Analytics

**SQL · Python · Power BI · DAX · Power Query · PBIP · PBIR · TMDL · Forecasting · Experimentation**

An end-to-end customer and commercial analytics portfolio project that transforms e-commerce behavioural data into decision-ready insights across customer acquisition, retention, product performance, revenue, forecasting and marketing efficiency.

> **Data disclosure:** Customer, acquisition, product, revenue and forecasting analysis use Google GA4 public sample e-commerce data. The A/B experiment observations and marketing campaign-spend layer are synthetic and are explicitly identified as synthetic throughout the project.

## Business Problem

This project creates a unified Customer 360 analytical layer to answer key commercial questions:

- How many customers convert and make repeat purchases?
- Which acquisition channels generate the most revenue?
- Which products contribute most strongly to performance?
- How do customer segments and cohorts behave?
- How does conversion vary by device?
- What does short-term revenue forecasting indicate?
- How can experimentation and campaign-efficiency metrics support growth decisions?

## Key Results

| Metric | Result |
| --- | ---: |
| Customers analysed | 270,154 |
| Purchasing customers | 4,419 |
| Repeat purchasing customers | 775 |
| Total GA4 revenue | 362,165 |
| Average revenue per customer | 1.34 |
| Highest-revenue month | December 2020 - 160,555 |
| Highest-revenue acquisition channel | google / organic - 95,775 |
| Top product | Google Zip Hoodie F/C - 13,692 |
| Forecast holdout MAE | 1,809.72 |
| Forecast holdout RMSE | 2,278.03 |

## Power BI Dashboard

### Executive Overview

![Executive Overview](images/powerbi/01_executive_overview.png)

### Customer & Retention

![Customer & Retention](images/powerbi/02_customer_retention.png)

### Acquisition & Product Performance

![Acquisition & Product Performance](images/powerbi/03_acquisition_product_performance.png)

### Forecasting & Experimentation

![Forecasting & Experimentation](images/powerbi/04_forecasting_experimentation.png)

### Marketing Performance

![Marketing Performance](images/powerbi/05_marketing_performance.png)

## Revenue Forecasting

The advanced modelling workflow uses Holt's damped-trend method on real GA4 daily revenue data.

| Forecast Metric | Result |
| --- | ---: |
| Historical days analysed | 92 |
| Forecast horizon | 14 days |
| Holdout MAE | 1,809.72 |
| Holdout RMSE | 2,278.03 |

## Synthetic A/B Experiment

A reproducible synthetic A/B experiment was created using the real GA4 conversion rate as the baseline.

| Metric | Control | Variant |
| --- | ---: | ---: |
| Users | 20,000 | 20,000 |
| Conversions | 322 | 384 |
| Conversion rate | 1.61% | 1.92% |

- Relative lift: **19.25%**
- P-value: **0.0186**
- Result: **statistically significant at the 5% level**

The experiment observations are synthetic and are included to demonstrate two-proportion hypothesis-testing methodology.

## Synthetic Marketing Performance

| KPI | Result |
| --- | ---: |
| Marketing spend | GBP 40,000 |
| Attributed revenue | GBP 166,000 |
| Marketing profit | GBP 126,000 |
| Acquisitions | 2,430 |
| Overall ROAS | 4.15x |
| Blended CPA | GBP 16.46 |
| Marketing ROI | 315% |

- Email Retargeting: strongest ROAS at 16.00x and lowest CPA.
- Google Search: highest absolute attributed revenue at GBP 52,000.
- Affiliate: 5.25x ROAS.
- Display Prospecting: weakest ROAS and highest CPA.

These marketing observations are synthetic and are not presented as observed GA4 campaign-spend data.

## SQL Analytics Layer

The `sql/` directory contains analytical transformations for Customer 360 modelling, conversion funnels, acquisition performance, cohort retention, RFM segmentation, product performance, monthly KPIs, device conversion and revenue analysis.

## Python Analysis

`notebooks/01_customer_360_python_analysis.py` performs data validation, KPI preparation, RFM analysis, acquisition analysis, cohort analysis, product analysis and exploratory visualisation.

`notebooks/02_advanced_modelling.py` performs revenue forecasting, holdout evaluation, synthetic A/B testing, two-proportion z-testing and synthetic campaign CPA/ROAS analysis.

## Power BI Engineering

The dashboard is stored as a Power BI Project and includes PBIP, PBIR, TMDL, DAX measures, Power Query transformations and five analytical report pages.

## Technology Stack

| Area | Technologies |
| --- | --- |
| Data Analysis | SQL, Python, pandas, NumPy |
| Statistics & Modelling | SciPy, statsmodels, scikit-learn |
| Business Intelligence | Microsoft Power BI, DAX, Power Query |
| Power BI Engineering | PBIP, PBIR, TMDL |
| Development | Visual Studio Code, Git, GitHub |

## Repository Structure

```text
data/
docs/
images/
notebooks/
powerbi/
reports/
sql/
customer360_FINAL_BUILD.py
requirements.txt
README.md
```

## Run the Python Analysis

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python .\notebooks\01_customer_360_python_analysis.py
python .\notebooks\02_advanced_modelling.py
```

## Open the Power BI Project

Open:

```text
powerbi/Customer_360_Revenue_Growth_Dashboard.pbip
```

in Power BI Desktop.

## Methodology & Limitations

The behavioural and revenue analysis uses a public GA4 e-commerce sample and therefore reflects the users, products and period contained in that sample.

The forecasting evaluation uses 92 historical daily observations and a 14-day horizon.

A/B experiment observations are synthetic.

Marketing spend, impressions, clicks and campaign-performance observations are synthetic.

These synthetic components demonstrate experimentation, statistical testing and marketing-performance methodology and are not represented as observed campaign outcomes.

## Skills Demonstrated

Customer analytics · Revenue analytics · Commercial analytics · SQL transformation · Data validation · KPI development · RFM segmentation · Cohort analysis · Acquisition analysis · Product analytics · Time-series forecasting · Statistical testing · A/B experimentation · Marketing analytics · DAX · Power Query · Semantic modelling · Power BI dashboard engineering · PBIP · PBIR · TMDL · Python · Git · GitHub

## Supporting Documentation

- `docs/RECRUITER_PROJECT_SUMMARY.md`
- `docs/MARKETING_PERFORMANCE.md`
- `docs/pbir_templates/`
- `reports/python_analysis_summary.txt`
- `reports/advanced_modelling_summary.txt`

## Author

**Oluwatosin Oluwaseun Mulero**

Data Analyst | Data Scientist
