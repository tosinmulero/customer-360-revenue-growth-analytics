from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from statsmodels.tsa.holtwinters import Holt
from statsmodels.stats.proportion import proportions_ztest


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

PROCESSED = ROOT / "data" / "processed"
SYNTHETIC = ROOT / "data" / "synthetic"
IMAGES = ROOT / "images"
REPORTS = ROOT / "reports"

SYNTHETIC.mkdir(parents=True, exist_ok=True)
IMAGES.mkdir(parents=True, exist_ok=True)
REPORTS.mkdir(parents=True, exist_ok=True)


# ============================================================
# IMPORTANT METHODOLOGY NOTE
# ============================================================

# REAL DATA:
# Google GA4 public sample e-commerce dataset.
#
# SYNTHETIC DATA:
# Marketing campaign spend and A/B experiment data created
# solely to demonstrate analytical methods.
#
# Synthetic results must NOT be described as observed GA4
# campaign or experimental performance.


# ============================================================
# PART A
# REAL REVENUE FORECASTING
# ============================================================

daily = pd.read_csv(
    PROCESSED / "25_daily_revenue.csv"
)

daily["date"] = pd.to_datetime(
    daily["date"]
)

daily["revenue"] = pd.to_numeric(
    daily["revenue"],
    errors="coerce"
).fillna(0)

daily = (
    daily
    .sort_values("date")
    .set_index("date")
)

# Ensure every calendar day exists
full_dates = pd.date_range(
    daily.index.min(),
    daily.index.max(),
    freq="D"
)

daily = daily.reindex(
    full_dates,
    fill_value=0
)

daily.index.name = "date"


# ------------------------------------------------------------
# TRAIN / TEST SPLIT
# ------------------------------------------------------------

test_days = 14

train = daily.iloc[:-test_days].copy()
test = daily.iloc[-test_days:].copy()


# ------------------------------------------------------------
# HOLT TREND MODEL
# ------------------------------------------------------------

model = Holt(
    train["revenue"],
    damped_trend=True,
    initialization_method="estimated"
)

fit = model.fit(
    optimized=True
)

test_forecast = fit.forecast(
    test_days
)


# ------------------------------------------------------------
# FORECAST ACCURACY
# ------------------------------------------------------------

actual = test["revenue"].to_numpy()
predicted = test_forecast.to_numpy()

mae = np.mean(
    np.abs(
        actual - predicted
    )
)

rmse = np.sqrt(
    np.mean(
        (actual - predicted) ** 2
    )
)


# ------------------------------------------------------------
# FINAL MODEL + 14 DAY FORECAST
# ------------------------------------------------------------

final_model = Holt(
    daily["revenue"],
    damped_trend=True,
    initialization_method="estimated"
)

final_fit = final_model.fit(
    optimized=True
)

forecast_days = 14

future_forecast = final_fit.forecast(
    forecast_days
)

future_dates = pd.date_range(
    daily.index.max()
    + pd.Timedelta(days=1),
    periods=forecast_days,
    freq="D"
)

forecast_df = pd.DataFrame({
    "date": future_dates,
    "forecast_revenue": future_forecast.values
})

forecast_df.to_csv(
    PROCESSED / "26_revenue_forecast.csv",
    index=False
)


# ------------------------------------------------------------
# FORECAST CHART
# ------------------------------------------------------------

plt.figure(
    figsize=(12, 6)
)

plt.plot(
    daily.index,
    daily["revenue"],
    label="Actual Revenue"
)

plt.plot(
    future_dates,
    future_forecast.values,
    linestyle="--",
    label="14-Day Forecast"
)

plt.title(
    "Daily Revenue and 14-Day Forecast"
)

plt.xlabel(
    "Date"
)

plt.ylabel(
    "Revenue"
)

plt.legend()

plt.tight_layout()

plt.savefig(
    IMAGES / "09_revenue_forecast.png",
    dpi=180,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# PART B
# SYNTHETIC A/B TEST
# ============================================================

# Baseline comes from the REAL GA4 conversion funnel.
# Experiment observations below are SYNTHETIC.

funnel = pd.read_csv(
    PROCESSED / "12_conversion_funnel.csv"
)

baseline_rate = (
    float(
        funnel.loc[
            0,
            "overall_conversion_pct"
        ]
    )
    / 100
)


# ------------------------------------------------------------
# REPRODUCIBLE SYNTHETIC EXPERIMENT
# ------------------------------------------------------------

rng = np.random.default_rng(
    42
)

control_users = 20000
variant_users = 20000

control_probability = baseline_rate

# Synthetic variant assumes a 12% relative improvement
variant_probability = (
    baseline_rate
    * 1.12
)

control_conversions = rng.binomial(
    control_users,
    control_probability
)

variant_conversions = rng.binomial(
    variant_users,
    variant_probability
)

control_rate = (
    control_conversions
    / control_users
)

variant_rate = (
    variant_conversions
    / variant_users
)

relative_lift = (
    variant_rate
    / control_rate
    - 1
) * 100


# ------------------------------------------------------------
# TWO-PROPORTION Z TEST
# ------------------------------------------------------------

counts = np.array([
    control_conversions,
    variant_conversions
])

observations = np.array([
    control_users,
    variant_users
])

z_stat, p_value = proportions_ztest(
    counts,
    observations
)


if p_value < 0.05:
    significance = "Statistically significant"
else:
    significance = "Not statistically significant"


ab_test = pd.DataFrame({
    "variant": [
        "Control",
        "Variant"
    ],
    "users": [
        control_users,
        variant_users
    ],
    "conversions": [
        control_conversions,
        variant_conversions
    ],
    "conversion_rate_pct": [
        control_rate * 100,
        variant_rate * 100
    ],
    "data_type": [
        "Synthetic",
        "Synthetic"
    ]
})

ab_test.to_csv(
    SYNTHETIC / "synthetic_ab_test.csv",
    index=False
)


# ------------------------------------------------------------
# A/B TEST CHART
# ------------------------------------------------------------

plt.figure(
    figsize=(8, 6)
)

plt.bar(
    ab_test["variant"],
    ab_test["conversion_rate_pct"]
)

plt.title(
    "Synthetic A/B Test Conversion Rate"
)

plt.ylabel(
    "Conversion Rate (%)"
)

plt.tight_layout()

plt.savefig(
    IMAGES / "10_synthetic_ab_test.png",
    dpi=180,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# PART C
# SYNTHETIC MARKETING CAMPAIGN DATA
# ============================================================

marketing = pd.DataFrame({

    "campaign": [
        "Google Search",
        "Meta Paid Social",
        "YouTube Video",
        "Display Prospecting",
        "Email Retargeting",
        "Affiliate"
    ],

    "spend": [
        12000,
        9000,
        7000,
        5500,
        2500,
        4000
    ],

    "impressions": [
        450000,
        600000,
        800000,
        1000000,
        160000,
        250000
    ],

    "clicks": [
        18000,
        15000,
        10000,
        7000,
        14000,
        9000
    ],

    "conversions": [
        650,
        430,
        220,
        120,
        700,
        310
    ],

    "revenue": [
        52000,
        29000,
        16000,
        8000,
        40000,
        21000
    ]
})


marketing["ctr_pct"] = (
    marketing["clicks"]
    / marketing["impressions"]
    * 100
)

marketing["cpc"] = (
    marketing["spend"]
    / marketing["clicks"]
)

marketing["conversion_rate_pct"] = (
    marketing["conversions"]
    / marketing["clicks"]
    * 100
)

marketing["cpa"] = (
    marketing["spend"]
    / marketing["conversions"]
)

marketing["roas"] = (
    marketing["revenue"]
    / marketing["spend"]
)

marketing["data_type"] = "Synthetic"

marketing.to_csv(
    SYNTHETIC /
    "synthetic_marketing_campaign_performance.csv",
    index=False
)


# ------------------------------------------------------------
# CAMPAIGN ROAS CHART
# ------------------------------------------------------------

marketing_chart = (
    marketing
    .sort_values(
        "roas"
    )
)

plt.figure(
    figsize=(11, 7)
)

plt.barh(
    marketing_chart["campaign"],
    marketing_chart["roas"]
)

plt.title(
    "Synthetic Marketing Campaign ROAS"
)

plt.xlabel(
    "Return on Ad Spend"
)

plt.ylabel(
    "Campaign"
)

plt.tight_layout()

plt.savefig(
    IMAGES / "11_synthetic_campaign_roas.png",
    dpi=180,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# MARKETING SUMMARY
# ============================================================

best_roas = (
    marketing
    .sort_values(
        "roas",
        ascending=False
    )
    .iloc[0]
)

lowest_cpa = (
    marketing
    .sort_values(
        "cpa"
    )
    .iloc[0]
)


# ============================================================
# WRITE ADVANCED MODELLING REPORT
# ============================================================

report = []

report.append(
    "CUSTOMER 360 & REVENUE GROWTH ANALYTICS"
)

report.append(
    "ADVANCED MODELLING REPORT"
)

report.append(
    "=" * 65
)

report.append("")

report.append(
    "SECTION 1 - REAL GA4 REVENUE FORECAST"
)

report.append(
    "-" * 65
)

report.append(
    f"Historical days analysed: {len(daily):,}"
)

report.append(
    f"Forecast horizon: {forecast_days} days"
)

report.append(
    f"Holdout MAE: {mae:,.2f}"
)

report.append(
    f"Holdout RMSE: {rmse:,.2f}"
)

report.append(
    "Forecast data source: REAL GA4 sample data"
)

report.append("")


report.append(
    "SECTION 2 - SYNTHETIC A/B TEST"
)

report.append(
    "-" * 65
)

report.append(
    "IMPORTANT: Experiment observations are synthetic."
)

report.append(
    f"GA4 baseline conversion used: "
    f"{baseline_rate * 100:.2f}%"
)

report.append(
    f"Control users: {control_users:,}"
)

report.append(
    f"Control conversions: "
    f"{control_conversions:,}"
)

report.append(
    f"Control conversion rate: "
    f"{control_rate * 100:.2f}%"
)

report.append(
    f"Variant users: {variant_users:,}"
)

report.append(
    f"Variant conversions: "
    f"{variant_conversions:,}"
)

report.append(
    f"Variant conversion rate: "
    f"{variant_rate * 100:.2f}%"
)

report.append(
    f"Relative lift: "
    f"{relative_lift:.2f}%"
)

report.append(
    f"Z statistic: "
    f"{z_stat:.4f}"
)

report.append(
    f"P-value: "
    f"{p_value:.4f}"
)

report.append(
    f"Result: {significance}"
)

report.append("")


report.append(
    "SECTION 3 - SYNTHETIC MARKETING ROI"
)

report.append(
    "-" * 65
)

report.append(
    "IMPORTANT: Campaign spend data are synthetic."
)

report.append(
    f"Total synthetic spend: "
    f"{marketing['spend'].sum():,.2f}"
)

report.append(
    f"Total synthetic revenue: "
    f"{marketing['revenue'].sum():,.2f}"
)

overall_roas = (
    marketing["revenue"].sum()
    / marketing["spend"].sum()
)

report.append(
    f"Overall synthetic ROAS: "
    f"{overall_roas:.2f}x"
)

report.append(
    f"Highest ROAS campaign: "
    f"{best_roas['campaign']} "
    f"({best_roas['roas']:.2f}x)"
)

report.append(
    f"Lowest CPA campaign: "
    f"{lowest_cpa['campaign']} "
    f"({lowest_cpa['cpa']:.2f})"
)

report.append("")

report.append(
    "METHODOLOGY DISCLOSURE"
)

report.append(
    "-" * 65
)

report.append(
    "Revenue forecasting uses real Google GA4 "
    "public sample e-commerce data."
)

report.append(
    "A/B testing observations are synthetic and are "
    "included only to demonstrate experimentation methods."
)

report.append(
    "Marketing spend, impressions, clicks and campaign "
    "metrics are synthetic and are included only to "
    "demonstrate CAC, CPA and ROAS analysis."
)


report_path = (
    REPORTS /
    "advanced_modelling_summary.txt"
)

report_path.write_text(
    "\n".join(report),
    encoding="utf-8"
)


# ============================================================
# OUTPUT
# ============================================================

print("")
print("=" * 65)
print("ADVANCED MODELLING COMPLETE")
print("=" * 65)

print("")
print("REAL FORECAST")
print(
    f"MAE: {mae:,.2f}"
)
print(
    f"RMSE: {rmse:,.2f}"
)

print("")
print("SYNTHETIC A/B TEST")
print(
    ab_test.to_string(
        index=False
    )
)

print("")
print(
    f"Relative lift: "
    f"{relative_lift:.2f}%"
)

print(
    f"P-value: "
    f"{p_value:.4f}"
)

print(
    f"Conclusion: "
    f"{significance}"
)

print("")
print("SYNTHETIC MARKETING PERFORMANCE")

print(
    marketing[
        [
            "campaign",
            "spend",
            "revenue",
            "cpa",
            "roas"
        ]
    ].to_string(
        index=False
    )
)

print("")
print(
    f"Report saved to: "
    f"{report_path}"
)
