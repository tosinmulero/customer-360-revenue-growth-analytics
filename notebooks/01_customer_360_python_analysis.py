from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# PATHS
# ============================================================

ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = ROOT / "data" / "processed"
IMAGE_DIR = ROOT / "images"
REPORT_DIR = ROOT / "reports"

IMAGE_DIR.mkdir(parents=True, exist_ok=True)
REPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def load_csv(filename):
    path = DATA_DIR / filename

    if not path.exists():
        raise FileNotFoundError(f"Missing file: {path}")

    df = pd.read_csv(path)

    print(f"Loaded {filename}: {df.shape[0]:,} rows x {df.shape[1]} columns")

    return df


def save_figure(filename):
    path = IMAGE_DIR / filename
    plt.tight_layout()
    plt.savefig(path, dpi=180, bbox_inches="tight")
    plt.close()

    print(f"Saved chart: {path.name}")


def safe_numeric(df, columns):
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce"
            )

    return df


# ============================================================
# LOAD DATA
# ============================================================

dataset_profile = load_csv("01_dataset_profile.csv")
event_types = load_csv("02_event_types.csv")
daily_activity = load_csv("03_daily_activity.csv")
traffic = load_csv("04_traffic_acquisition.csv")
device = load_csv("05_device_analysis.csv")
countries = load_csv("06_country_analysis.csv")
initial_funnel = load_csv("07_ecommerce_funnel.csv")
revenue_summary = load_csv("08_revenue_summary.csv")
monthly_revenue = load_csv("09_monthly_revenue.csv")
top_products_initial = load_csv("10_top_products.csv")

customer_360 = load_csv("11_customer_360.csv")
funnel = load_csv("12_conversion_funnel.csv")
acquisition = load_csv("13_acquisition_performance.csv")
cohort = load_csv("14_cohort_retention.csv")
rfm = load_csv("15_rfm_segmentation.csv")
products = load_csv("16_product_performance.csv")
monthly_kpis = load_csv("17_monthly_business_kpis.csv")
device_conversion = load_csv("18_device_conversion.csv")


# ============================================================
# DATA VALIDATION
# ============================================================

validation_lines = []

validation_lines.append(
    "CUSTOMER 360 & REVENUE GROWTH ANALYTICS - VALIDATION REPORT"
)

validation_lines.append("=" * 65)
validation_lines.append("")


# ------------------------------------------------------------
# Customer 360 checks
# ------------------------------------------------------------

validation_lines.append("CUSTOMER 360 DATA")
validation_lines.append("-" * 40)

validation_lines.append(
    f"Rows: {len(customer_360):,}"
)

validation_lines.append(
    f"Columns: {customer_360.shape[1]}"
)

if "user_pseudo_id" in customer_360.columns:

    duplicate_users = customer_360[
        "user_pseudo_id"
    ].duplicated().sum()

    missing_users = customer_360[
        "user_pseudo_id"
    ].isna().sum()

    validation_lines.append(
        f"Duplicate user IDs: {duplicate_users:,}"
    )

    validation_lines.append(
        f"Missing user IDs: {missing_users:,}"
    )


validation_lines.append("")
validation_lines.append("MISSING VALUES")
validation_lines.append("-" * 40)

missing = customer_360.isna().sum()

for column, count in missing.items():

    if count > 0:
        validation_lines.append(
            f"{column}: {count:,}"
        )


# ============================================================
# CUSTOMER 360 SUMMARY
# ============================================================

customer_360 = safe_numeric(
    customer_360,
    [
        "total_events",
        "sessions",
        "product_views",
        "add_to_carts",
        "checkouts",
        "purchases",
        "total_revenue",
        "avg_order_value"
    ]
)


total_customers = customer_360["user_pseudo_id"].nunique()

purchasing_customers = (
    customer_360["purchases"] > 0
).sum()

repeat_customers = (
    customer_360["purchases"] > 1
).sum()

customer_revenue = customer_360[
    "total_revenue"
].sum()

avg_revenue_per_customer = (
    customer_360["total_revenue"].mean()
)


customer_summary = pd.DataFrame({
    "metric": [
        "Total Customers",
        "Purchasing Customers",
        "Repeat Purchasing Customers",
        "Total Revenue",
        "Average Revenue per Customer"
    ],
    "value": [
        total_customers,
        purchasing_customers,
        repeat_customers,
        round(customer_revenue, 2),
        round(avg_revenue_per_customer, 2)
    ]
})

customer_summary.to_csv(
    DATA_DIR / "19_customer_summary.csv",
    index=False
)


# ============================================================
# RFM SEGMENT SUMMARY
# ============================================================

rfm = safe_numeric(
    rfm,
    [
        "recency_days",
        "frequency",
        "monetary_value"
    ]
)

rfm_summary = (
    rfm
    .groupby(
        "customer_segment",
        dropna=False
    )
    .agg(
        customers=("user_pseudo_id", "nunique"),
        avg_recency_days=("recency_days", "mean"),
        avg_frequency=("frequency", "mean"),
        total_revenue=("monetary_value", "sum"),
        avg_customer_value=("monetary_value", "mean")
    )
    .reset_index()
)

rfm_summary[
    "customer_share_pct"
] = (
    rfm_summary["customers"]
    / rfm_summary["customers"].sum()
    * 100
)

rfm_summary = rfm_summary.sort_values(
    "total_revenue",
    ascending=False
)

rfm_summary.to_csv(
    DATA_DIR / "20_rfm_segment_summary.csv",
    index=False
)


# ============================================================
# ACQUISITION SUMMARY
# ============================================================

acquisition = safe_numeric(
    acquisition,
    [
        "users",
        "purchasing_users",
        "purchase_events",
        "revenue",
        "conversion_rate_pct",
        "revenue_per_user"
    ]
)

acquisition["channel"] = (
    acquisition["source"].astype(str)
    + " / "
    + acquisition["medium"].astype(str)
)

acquisition_top = acquisition.sort_values(
    "revenue",
    ascending=False
).head(15)

acquisition_top.to_csv(
    DATA_DIR / "21_top_acquisition_channels.csv",
    index=False
)


# ============================================================
# MONTHLY KPI PREPARATION
# ============================================================

monthly_kpis["month"] = pd.to_datetime(
    monthly_kpis["month"],
    errors="coerce"
)

monthly_kpis = safe_numeric(
    monthly_kpis,
    [
        "users",
        "purchasing_users",
        "purchases",
        "revenue",
        "customer_conversion_pct",
        "avg_order_value"
    ]
)

monthly_kpis = monthly_kpis.sort_values(
    "month"
)

monthly_kpis.to_csv(
    DATA_DIR / "22_monthly_kpis_clean.csv",
    index=False
)


# ============================================================
# DEVICE PERFORMANCE
# ============================================================

device_conversion = safe_numeric(
    device_conversion,
    [
        "users",
        "purchasing_users",
        "purchases",
        "revenue",
        "conversion_rate_pct"
    ]
)

device_conversion.to_csv(
    DATA_DIR / "23_device_conversion_clean.csv",
    index=False
)


# ============================================================
# PRODUCT PERFORMANCE
# ============================================================

products = safe_numeric(
    products,
    [
        "buyers",
        "units_sold",
        "product_revenue"
    ]
)

products = products.sort_values(
    "product_revenue",
    ascending=False
)

products.to_csv(
    DATA_DIR / "24_product_performance_clean.csv",
    index=False
)


# ============================================================
# CHART 1 - MONTHLY REVENUE
# ============================================================

plt.figure(figsize=(11, 6))

plt.plot(
    monthly_kpis["month"],
    monthly_kpis["revenue"],
    marker="o",
    linewidth=2
)

plt.title(
    "Monthly E-commerce Revenue"
)

plt.xlabel("Month")
plt.ylabel("Revenue")

plt.xticks(rotation=45)

save_figure(
    "01_monthly_revenue_trend.png"
)


# ============================================================
# CHART 2 - CUSTOMER CONVERSION
# ============================================================

plt.figure(figsize=(11, 6))

plt.plot(
    monthly_kpis["month"],
    monthly_kpis["customer_conversion_pct"],
    marker="o",
    linewidth=2
)

plt.title(
    "Monthly Customer Conversion Rate"
)

plt.xlabel("Month")
plt.ylabel("Conversion Rate (%)")

plt.xticks(rotation=45)

save_figure(
    "02_monthly_conversion_rate.png"
)


# ============================================================
# CHART 3 - E-COMMERCE FUNNEL
# ============================================================

funnel_row = funnel.iloc[0]

funnel_stages = [
    "Sessions",
    "Product Views",
    "Add to Cart",
    "Checkout",
    "Purchase"
]

funnel_values = [
    funnel_row["session_users"],
    funnel_row["product_view_users"],
    funnel_row["cart_users"],
    funnel_row["checkout_users"],
    funnel_row["purchasing_users"]
]

plt.figure(figsize=(10, 6))

plt.bar(
    funnel_stages,
    funnel_values
)

plt.title(
    "E-commerce Customer Funnel"
)

plt.ylabel("Unique Users")

plt.xticks(rotation=20)

save_figure(
    "03_ecommerce_conversion_funnel.png"
)


# ============================================================
# CHART 4 - TOP ACQUISITION CHANNELS
# ============================================================

top_channels_chart = (
    acquisition_top
    .head(10)
    .sort_values("revenue")
)

plt.figure(figsize=(11, 7))

plt.barh(
    top_channels_chart["channel"],
    top_channels_chart["revenue"]
)

plt.title(
    "Top Acquisition Channels by Revenue"
)

plt.xlabel("Revenue")
plt.ylabel("Source / Medium")

save_figure(
    "04_top_acquisition_channels.png"
)


# ============================================================
# CHART 5 - RFM SEGMENTS
# ============================================================

rfm_chart = rfm_summary.sort_values(
    "customers"
)

plt.figure(figsize=(11, 7))

plt.barh(
    rfm_chart["customer_segment"],
    rfm_chart["customers"]
)

plt.title(
    "Customer Segments by RFM Analysis"
)

plt.xlabel("Customers")
plt.ylabel("Segment")

save_figure(
    "05_rfm_customer_segments.png"
)


# ============================================================
# CHART 6 - DEVICE CONVERSION
# ============================================================

device_chart = device_conversion.sort_values(
    "conversion_rate_pct",
    ascending=False
)

plt.figure(figsize=(9, 6))

plt.bar(
    device_chart["device_category"],
    device_chart["conversion_rate_pct"]
)

plt.title(
    "Conversion Rate by Device"
)

plt.xlabel("Device")
plt.ylabel("Conversion Rate (%)")

save_figure(
    "06_device_conversion_rate.png"
)


# ============================================================
# CHART 7 - TOP PRODUCTS
# ============================================================

top_products = (
    products
    .head(10)
    .sort_values("product_revenue")
)

plt.figure(figsize=(11, 7))

plt.barh(
    top_products["item_name"],
    top_products["product_revenue"]
)

plt.title(
    "Top 10 Products by Revenue"
)

plt.xlabel("Product Revenue")
plt.ylabel("Product")

save_figure(
    "07_top_products_by_revenue.png"
)


# ============================================================
# CHART 8 - COHORT RETENTION HEATMAP
# ============================================================

cohort["cohort_month"] = pd.to_datetime(
    cohort["cohort_month"],
    errors="coerce"
)

cohort = safe_numeric(
    cohort,
    [
        "months_since_acquisition",
        "retention_rate_pct"
    ]
)

cohort_matrix = cohort.pivot_table(
    index="cohort_month",
    columns="months_since_acquisition",
    values="retention_rate_pct",
    aggfunc="mean"
)

plt.figure(figsize=(12, 7))

image = plt.imshow(
    cohort_matrix,
    aspect="auto"
)

plt.colorbar(
    image,
    label="Retention Rate (%)"
)

plt.title(
    "Monthly Customer Cohort Retention"
)

plt.xlabel(
    "Months Since Acquisition"
)

plt.ylabel(
    "Acquisition Cohort"
)

plt.yticks(
    range(len(cohort_matrix.index)),
    [
        d.strftime("%Y-%m")
        for d in cohort_matrix.index
    ]
)

plt.xticks(
    range(len(cohort_matrix.columns)),
    cohort_matrix.columns
)

save_figure(
    "08_cohort_retention_heatmap.png"
)


# ============================================================
# WRITE ANALYSIS REPORT
# ============================================================

validation_lines.append("")
validation_lines.append("CUSTOMER SUMMARY")
validation_lines.append("-" * 40)

validation_lines.append(
    f"Total customers: {total_customers:,}"
)

validation_lines.append(
    f"Purchasing customers: {purchasing_customers:,}"
)

validation_lines.append(
    f"Repeat purchasing customers: {repeat_customers:,}"
)

validation_lines.append(
    f"Total revenue: {customer_revenue:,.2f}"
)

validation_lines.append(
    f"Average revenue per customer: "
    f"{avg_revenue_per_customer:,.2f}"
)


if not monthly_kpis.empty:

    highest_revenue_month = (
        monthly_kpis
        .sort_values(
            "revenue",
            ascending=False
        )
        .iloc[0]
    )

    validation_lines.append("")

    validation_lines.append(
        "TOP MONTH"
    )

    validation_lines.append(
        "-" * 40
    )

    validation_lines.append(
        "Highest revenue month: "
        f"{highest_revenue_month['month'].strftime('%Y-%m')}"
    )

    validation_lines.append(
        "Revenue: "
        f"{highest_revenue_month['revenue']:,.2f}"
    )


if not acquisition_top.empty:

    best_channel = acquisition_top.iloc[0]

    validation_lines.append("")
    validation_lines.append(
        "TOP ACQUISITION CHANNEL"
    )

    validation_lines.append(
        "-" * 40
    )

    validation_lines.append(
        f"Channel: {best_channel['channel']}"
    )

    validation_lines.append(
        f"Revenue: {best_channel['revenue']:,.2f}"
    )

    validation_lines.append(
        "Conversion rate: "
        f"{best_channel['conversion_rate_pct']:.2f}%"
    )


if not products.empty:

    best_product = products.iloc[0]

    validation_lines.append("")
    validation_lines.append(
        "TOP PRODUCT"
    )

    validation_lines.append(
        "-" * 40
    )

    validation_lines.append(
        f"Product: {best_product['item_name']}"
    )

    validation_lines.append(
        "Revenue: "
        f"{best_product['product_revenue']:,.2f}"
    )


report_path = (
    REPORT_DIR
    / "python_analysis_summary.txt"
)

report_path.write_text(
    "\n".join(validation_lines),
    encoding="utf-8"
)


print("")
print("=" * 65)
print("PYTHON ANALYSIS COMPLETE")
print("=" * 65)

print("")
print(
    customer_summary.to_string(
        index=False
    )
)

print("")
print("RFM SEGMENTS")
print(
    rfm_summary[
        [
            "customer_segment",
            "customers",
            "total_revenue",
            "customer_share_pct"
        ]
    ].to_string(
        index=False
    )
)

print("")
print(
    f"Report saved to: {report_path}"
)

print("")
print(
    f"Charts saved to: {IMAGE_DIR}"
)
