from pathlib import Path
import csv
import json
import shutil
import uuid
from datetime import datetime


# =====================================================================
# PROJECT PATHS
# =====================================================================

ROOT = Path.cwd()

POWERBI = ROOT / "powerbi"

REPORT = (
    POWERBI /
    "Customer_360_Revenue_Growth_Dashboard.Report"
)

DATA = POWERBI / "data"

DOCS = ROOT / "docs" / "pbir_templates"

PAGES_ROOT = REPORT / "definition" / "pages"

PAGES_JSON = PAGES_ROOT / "pages.json"

CARD_TEMPLATE = DOCS / "card_template.json"

LINE_TEMPLATE = DOCS / "line_chart_template.json"


# =====================================================================
# BASIC VALIDATION
# =====================================================================

required_paths = [
    REPORT,
    DATA,
    PAGES_ROOT,
    PAGES_JSON,
    CARD_TEMPLATE,
    LINE_TEMPLATE,
]

for path in required_paths:
    if not path.exists():
        raise FileNotFoundError(
            f"Required file/folder missing: {path}"
        )


# =====================================================================
# JSON HELPERS
# Python UTF-8 writes DO NOT add a BOM.
# =====================================================================

def read_json(path: Path):
    return json.loads(
        path.read_text(
            encoding="utf-8-sig"
        )
    )


def write_json(path: Path, obj):
    path.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    path.write_text(
        json.dumps(
            obj,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )


# =====================================================================
# BACKUP REPORT BEFORE MODIFICATION
# =====================================================================

timestamp = datetime.now().strftime(
    "%Y%m%d_%H%M%S"
)

backup = (
    POWERBI /
    f"backup_before_pages_2_4_{timestamp}"
)

shutil.copytree(
    REPORT,
    backup
)

print()
print(
    "BACKUP CREATED:"
)
print(
    backup
)


# =====================================================================
# LOAD EXISTING SCHEMAS
# =====================================================================

card_template = read_json(
    CARD_TEMPLATE
)

line_template = read_json(
    LINE_TEMPLATE
)

VISUAL_SCHEMA = (
    line_template["$schema"]
)


# Find the existing Executive Overview page
existing_pages = {}

for folder in PAGES_ROOT.iterdir():

    if not folder.is_dir():
        continue

    page_file = (
        folder /
        "page.json"
    )

    if not page_file.exists():
        continue

    page = read_json(
        page_file
    )

    existing_pages[
        page.get("displayName")
    ] = {
        "folder": folder,
        "json": page
    }


if "Executive Overview" not in existing_pages:
    raise RuntimeError(
        "Executive Overview page not found."
    )


executive_info = existing_pages[
    "Executive Overview"
]

executive_page = executive_info[
    "json"
]

EXECUTIVE_ID = executive_page[
    "name"
]

PAGE_SCHEMA = executive_page[
    "$schema"
]

PAGE_WIDTH = executive_page.get(
    "width",
    1280
)

PAGE_HEIGHT = executive_page.get(
    "height",
    720
)


# =====================================================================
# CSV HEADER HELPERS
# =====================================================================

header_cache = {}


def csv_headers(table):

    if table in header_cache:
        return header_cache[table]

    path = (
        DATA /
        f"{table}.csv"
    )

    if not path.exists():
        header_cache[table] = []
        return []

    encodings = [
        "utf-8-sig",
        "cp1252",
        "latin-1"
    ]

    for enc in encodings:

        try:

            with open(
                path,
                "r",
                encoding=enc,
                newline=""
            ) as f:

                reader = csv.reader(f)

                headers = next(
                    reader
                )

                headers = [
                    x.strip()
                    for x in headers
                ]

                header_cache[
                    table
                ] = headers

                return headers

        except UnicodeDecodeError:
            continue

    return []


def pick(
    table,
    candidates
):

    headers = csv_headers(
        table
    )

    lookup = {
        h.lower(): h
        for h in headers
    }

    # Exact match first
    for candidate in candidates:

        key = candidate.lower()

        if key in lookup:
            return lookup[key]

    # Partial match second
    for candidate in candidates:

        key = candidate.lower()

        for header in headers:

            if key in header.lower():
                return header

    return None


# =====================================================================
# FIELD / PROJECTION HELPERS
# =====================================================================

AGG_NAMES = {
    0: "Sum",
    1: "Avg",
    2: "Min",
    3: "Max",
    4: "Count",
}


def column_projection(
    table,
    column,
    active=True
):

    projection = {
        "field": {
            "Column": {
                "Expression": {
                    "SourceRef": {
                        "Entity": table
                    }
                },
                "Property": column
            }
        },
        "queryRef": (
            f"{table}.{column}"
        ),
        "nativeQueryRef": column
    }

    if active:
        projection["active"] = True

    return projection


def aggregate_projection(
    table,
    column,
    function=0
):

    name = AGG_NAMES.get(
        function,
        "Sum"
    )

    return {
        "field": {
            "Aggregation": {
                "Expression": {
                    "Column": {
                        "Expression": {
                            "SourceRef": {
                                "Entity": table
                            }
                        },
                        "Property": column
                    }
                },
                "Function": function
            }
        },
        "queryRef": (
            f"{name}({table}.{column})"
        ),
        "nativeQueryRef": (
            f"{name} of {column}"
        )
    }


def aggregation_field(
    table,
    column,
    function=0
):

    return {
        "Aggregation": {
            "Expression": {
                "Column": {
                    "Expression": {
                        "SourceRef": {
                            "Entity": table
                        }
                    },
                    "Property": column
                }
            },
            "Function": function
        }
    }


def column_field(
    table,
    column
):

    return {
        "Column": {
            "Expression": {
                "SourceRef": {
                    "Entity": table
                }
            },
            "Property": column
        }
    }


# =====================================================================
# PBIR HELPERS
# =====================================================================

def new_id():
    return uuid.uuid4().hex[:20]


def title_objects(title):

    # Escape apostrophes for literal expression.
    safe = title.replace(
        "'",
        "''"
    )

    return {
        "title": [
            {
                "properties": {
                    "show": {
                        "expr": {
                            "Literal": {
                                "Value": "true"
                            }
                        }
                    },
                    "text": {
                        "expr": {
                            "Literal": {
                                "Value": (
                                    f"'{safe}'"
                                )
                            }
                        }
                    }
                }
            }
        ]
    }


def ensure_page(
    display_name
):

    # Reuse page if it already exists.
    for folder in PAGES_ROOT.iterdir():

        if not folder.is_dir():
            continue

        page_file = (
            folder /
            "page.json"
        )

        if not page_file.exists():
            continue

        page = read_json(
            page_file
        )

        if (
            page.get("displayName")
            == display_name
        ):

            visuals = (
                folder /
                "visuals"
            )

            if visuals.exists():
                shutil.rmtree(
                    visuals
                )

            visuals.mkdir(
                parents=True,
                exist_ok=True
            )

            return folder

    # Otherwise create page.
    page_id = new_id()

    folder = (
        PAGES_ROOT /
        page_id
    )

    visuals = (
        folder /
        "visuals"
    )

    visuals.mkdir(
        parents=True,
        exist_ok=True
    )

    page = {
        "$schema": PAGE_SCHEMA,
        "name": page_id,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": PAGE_HEIGHT,
        "width": PAGE_WIDTH
    }

    write_json(
        folder /
        "page.json",
        page
    )

    return folder


def add_visual(
    page_folder,
    visual_type,
    x,
    y,
    width,
    height,
    query_state,
    title,
    sort_definition=None,
    z=1
):

    visual_id = new_id()

    visual = {
        "$schema": VISUAL_SCHEMA,
        "name": visual_id,
        "position": {
            "x": x,
            "y": y,
            "z": z,
            "height": height,
            "width": width,
            "tabOrder": z
        },
        "visual": {
            "visualType": visual_type,
            "query": {
                "queryState": query_state
            },
            "visualContainerObjects":
                title_objects(title),
            "drillFilterOtherVisuals":
                True
        }
    }

    if sort_definition:
        visual[
            "visual"
        ][
            "query"
        ][
            "sortDefinition"
        ] = sort_definition

    path = (
        page_folder /
        "visuals" /
        visual_id /
        "visual.json"
    )

    write_json(
        path,
        visual
    )

    return visual_id


def add_category_chart(
    page_folder,
    visual_type,
    table,
    category,
    value,
    title,
    x,
    y,
    width,
    height,
    aggregation=0,
    sort="value_desc",
    z=1
):

    query_state = {
        "Category": {
            "projections": [
                column_projection(
                    table,
                    category
                )
            ]
        },
        "Y": {
            "projections": [
                aggregate_projection(
                    table,
                    value,
                    aggregation
                )
            ]
        }
    }

    sort_definition = None

    if sort == "value_desc":

        sort_definition = {
            "sort": [
                {
                    "field":
                        aggregation_field(
                            table,
                            value,
                            aggregation
                        ),
                    "direction":
                        "Descending"
                }
            ],
            "isDefaultSort": True
        }

    elif sort == "category_asc":

        sort_definition = {
            "sort": [
                {
                    "field":
                        column_field(
                            table,
                            category
                        ),
                    "direction":
                        "Ascending"
                }
            ],
            "isDefaultSort": True
        }

    return add_visual(
        page_folder=page_folder,
        visual_type=visual_type,
        x=x,
        y=y,
        width=width,
        height=height,
        query_state=query_state,
        title=title,
        sort_definition=sort_definition,
        z=z
    )


def add_aggregate_card(
    page_folder,
    table,
    value,
    title,
    x,
    y,
    width,
    height,
    aggregation=0,
    z=1
):

    # Clone Power BI's existing cardVisual
    card = json.loads(
        json.dumps(
            card_template
        )
    )

    visual_id = new_id()

    card["name"] = visual_id

    card["position"] = {
        "x": x,
        "y": y,
        "z": z,
        "height": height,
        "width": width,
        "tabOrder": z
    }

    card[
        "visual"
    ][
        "query"
    ] = {
        "queryState": {
            "Data": {
                "projections": [
                    aggregate_projection(
                        table,
                        value,
                        aggregation
                    )
                ]
            }
        }
    }

    card[
        "visual"
    ][
        "visualContainerObjects"
    ] = title_objects(
        title
    )

    path = (
        page_folder /
        "visuals" /
        visual_id /
        "visual.json"
    )

    write_json(
        path,
        card
    )

    return visual_id


# =====================================================================
# BUILD MANIFEST
# =====================================================================

manifest = []
warnings = []


def log_visual(
    page,
    title,
    field_type,
    details
):

    manifest.append(
        f"{page} | "
        f"{title} | "
        f"{field_type} | "
        f"{details}"
    )


def warn(message):

    warnings.append(
        message
    )

    print(
        "WARNING:",
        message
    )


# =====================================================================
# PAGE 2 — CUSTOMER & RETENTION
# =====================================================================

page2_name = (
    "Customer & Retention"
)

page2 = ensure_page(
    page2_name
)


RFM = (
    "rfm_segment_summary"
)

rfm_segment = pick(
    RFM,
    [
        "rfm_segment",
        "segment",
        "customer_segment"
    ]
)

rfm_customers = pick(
    RFM,
    [
        "customers",
        "customer_count",
        "number_of_customers"
    ]
)

rfm_revenue = pick(
    RFM,
    [
        "total_revenue",
        "revenue"
    ]
)

rfm_value = pick(
    RFM,
    [
        "avg_customer_value",
        "average_customer_value",
        "avg_revenue_per_customer"
    ]
)


# Chart 1
if rfm_segment and rfm_revenue:

    add_category_chart(
        page2,
        "clusteredBarChart",
        RFM,
        rfm_segment,
        rfm_revenue,
        "Revenue by RFM Customer Segment",
        20,
        20,
        610,
        320,
        aggregation=0,
        z=1
    )

    log_visual(
        page2_name,
        "Revenue by RFM Customer Segment",
        "COLUMN",
        (
            f"{RFM}[{rfm_segment}] + "
            f"SUM({RFM}[{rfm_revenue}])"
        )
    )

else:
    warn(
        "RFM revenue chart skipped."
    )


# Chart 2
if rfm_segment and rfm_customers:

    add_category_chart(
        page2,
        "clusteredColumnChart",
        RFM,
        rfm_segment,
        rfm_customers,
        "Customers by RFM Segment",
        650,
        20,
        610,
        320,
        aggregation=0,
        z=2
    )

    log_visual(
        page2_name,
        "Customers by RFM Segment",
        "COLUMN",
        (
            f"{RFM}[{rfm_segment}] + "
            f"SUM({RFM}[{rfm_customers}])"
        )
    )

else:
    warn(
        "RFM customer-count chart skipped."
    )


# Chart 3
if rfm_segment and rfm_value:

    add_category_chart(
        page2,
        "clusteredBarChart",
        RFM,
        rfm_segment,
        rfm_value,
        "Average Customer Value by RFM Segment",
        20,
        360,
        610,
        330,
        aggregation=1,
        z=3
    )

    log_visual(
        page2_name,
        "Average Customer Value by RFM Segment",
        "COLUMN",
        (
            f"{RFM}[{rfm_segment}] + "
            f"AVERAGE({RFM}[{rfm_value}])"
        )
    )

else:
    warn(
        "Average customer-value chart skipped."
    )


COHORT = (
    "cohort_retention"
)

cohort_period = pick(
    COHORT,
    [
        "period_number",
        "cohort_index",
        "month_number",
        "month_index",
        "months_since_first_purchase",
        "period"
    ]
)

cohort_retention = pick(
    COHORT,
    [
        "retention_pct",
        "retention_rate",
        "retention_percentage"
    ]
)

cohort_month = pick(
    COHORT,
    [
        "cohort_month",
        "cohort",
        "cohort_date"
    ]
)

cohort_retained = pick(
    COHORT,
    [
        "retained_customers",
        "retained_users",
        "active_customers",
        "active_users"
    ]
)


# Chart 4
if cohort_period and cohort_retention:

    add_category_chart(
        page2,
        "lineChart",
        COHORT,
        cohort_period,
        cohort_retention,
        "Average Cohort Retention by Period",
        650,
        360,
        610,
        330,
        aggregation=1,
        sort="category_asc",
        z=4
    )

    log_visual(
        page2_name,
        "Average Cohort Retention by Period",
        "COLUMN",
        (
            f"{COHORT}[{cohort_period}] + "
            f"AVERAGE({COHORT}[{cohort_retention}])"
        )
    )

elif cohort_month and cohort_retained:

    add_category_chart(
        page2,
        "clusteredColumnChart",
        COHORT,
        cohort_month,
        cohort_retained,
        "Retained Customers by Cohort",
        650,
        360,
        610,
        330,
        aggregation=0,
        sort="category_asc",
        z=4
    )

    log_visual(
        page2_name,
        "Retained Customers by Cohort",
        "COLUMN",
        (
            f"{COHORT}[{cohort_month}] + "
            f"SUM({COHORT}[{cohort_retained}])"
        )
    )

else:
    warn(
        "Cohort-retention chart skipped."
    )


# =====================================================================
# PAGE 3 — ACQUISITION & PRODUCT PERFORMANCE
# =====================================================================

page3_name = (
    "Acquisition & Product Performance"
)

page3 = ensure_page(
    page3_name
)


ACQ = (
    "acquisition_performance"
)

channel = pick(
    ACQ,
    [
        "source_medium",
        "acquisition_channel",
        "channel",
        "traffic_source",
        "source"
    ]
)

acq_revenue = pick(
    ACQ,
    [
        "revenue",
        "total_revenue"
    ]
)

acq_conversion = pick(
    ACQ,
    [
        "customer_conversion_pct",
        "conversion_rate_pct",
        "conversion_rate",
        "conversion_pct"
    ]
)

acq_revenue_per_user = pick(
    ACQ,
    [
        "revenue_per_user",
        "revenue_user"
    ]
)


# Chart 1
if channel and acq_revenue:

    add_category_chart(
        page3,
        "clusteredBarChart",
        ACQ,
        channel,
        acq_revenue,
        "Revenue by Acquisition Channel",
        20,
        20,
        610,
        320,
        aggregation=0,
        z=1
    )

    log_visual(
        page3_name,
        "Revenue by Acquisition Channel",
        "COLUMN",
        (
            f"{ACQ}[{channel}] + "
            f"SUM({ACQ}[{acq_revenue}])"
        )
    )

else:
    warn(
        "Acquisition revenue chart skipped."
    )


# Chart 2
if channel and acq_conversion:

    add_category_chart(
        page3,
        "clusteredBarChart",
        ACQ,
        channel,
        acq_conversion,
        "Conversion Rate by Acquisition Channel",
        650,
        20,
        610,
        320,
        aggregation=1,
        z=2
    )

    log_visual(
        page3_name,
        "Conversion Rate by Acquisition Channel",
        "COLUMN",
        (
            f"{ACQ}[{channel}] + "
            f"AVERAGE({ACQ}[{acq_conversion}])"
        )
    )

elif channel and acq_revenue_per_user:

    add_category_chart(
        page3,
        "clusteredBarChart",
        ACQ,
        channel,
        acq_revenue_per_user,
        "Revenue per User by Acquisition Channel",
        650,
        20,
        610,
        320,
        aggregation=1,
        z=2
    )

    log_visual(
        page3_name,
        "Revenue per User by Acquisition Channel",
        "COLUMN",
        (
            f"{ACQ}[{channel}] + "
            f"AVERAGE({ACQ}[{acq_revenue_per_user}])"
        )
    )

else:
    warn(
        "Acquisition efficiency chart skipped."
    )


DEVICE = (
    "device_conversion"
)

device = pick(
    DEVICE,
    [
        "device_category",
        "device",
        "category"
    ]
)

device_conversion = pick(
    DEVICE,
    [
        "customer_conversion_pct",
        "conversion_rate_pct",
        "conversion_rate",
        "conversion_pct"
    ]
)

device_revenue = pick(
    DEVICE,
    [
        "revenue",
        "total_revenue"
    ]
)


# Chart 3
if device and device_conversion:

    add_category_chart(
        page3,
        "clusteredColumnChart",
        DEVICE,
        device,
        device_conversion,
        "Conversion Rate by Device",
        20,
        360,
        610,
        330,
        aggregation=1,
        z=3
    )

    log_visual(
        page3_name,
        "Conversion Rate by Device",
        "COLUMN",
        (
            f"{DEVICE}[{device}] + "
            f"AVERAGE({DEVICE}[{device_conversion}])"
        )
    )

elif device and device_revenue:

    add_category_chart(
        page3,
        "clusteredColumnChart",
        DEVICE,
        device,
        device_revenue,
        "Revenue by Device",
        20,
        360,
        610,
        330,
        aggregation=0,
        z=3
    )

    log_visual(
        page3_name,
        "Revenue by Device",
        "COLUMN",
        (
            f"{DEVICE}[{device}] + "
            f"SUM({DEVICE}[{device_revenue}])"
        )
    )

else:
    warn(
        "Device chart skipped."
    )


PRODUCT = (
    "product_performance"
)

product = pick(
    PRODUCT,
    [
        "item_name",
        "product_name",
        "product",
        "item"
    ]
)

product_revenue = pick(
    PRODUCT,
    [
        "item_revenue",
        "product_revenue",
        "revenue",
        "total_revenue"
    ]
)

product_purchases = pick(
    PRODUCT,
    [
        "purchase_events",
        "purchases",
        "items_purchased",
        "quantity"
    ]
)


# Chart 4
if product and product_revenue:

    add_category_chart(
        page3,
        "clusteredBarChart",
        PRODUCT,
        product,
        product_revenue,
        "Product Revenue Performance",
        650,
        360,
        610,
        330,
        aggregation=0,
        z=4
    )

    log_visual(
        page3_name,
        "Product Revenue Performance",
        "COLUMN",
        (
            f"{PRODUCT}[{product}] + "
            f"SUM({PRODUCT}[{product_revenue}])"
        )
    )

elif product and product_purchases:

    add_category_chart(
        page3,
        "clusteredBarChart",
        PRODUCT,
        product,
        product_purchases,
        "Product Purchase Performance",
        650,
        360,
        610,
        330,
        aggregation=0,
        z=4
    )

    log_visual(
        page3_name,
        "Product Purchase Performance",
        "COLUMN",
        (
            f"{PRODUCT}[{product}] + "
            f"SUM({PRODUCT}[{product_purchases}])"
        )
    )

else:
    warn(
        "Product-performance chart skipped."
    )


# =====================================================================
# PAGE 4 — FORECASTING & EXPERIMENTATION
# =====================================================================

page4_name = (
    "Forecasting & Experimentation"
)

page4 = ensure_page(
    page4_name
)


FORECAST = (
    "revenue_forecast"
)

forecast_date = pick(
    FORECAST,
    [
        "forecast_date",
        "date",
        "ds"
    ]
)

forecast_value = pick(
    FORECAST,
    [
        "forecast_revenue",
        "predicted_revenue",
        "forecast",
        "prediction",
        "yhat"
    ]
)


AB = (
    "synthetic_ab_test"
)

ab_variant = pick(
    AB,
    [
        "variant",
        "experiment_group",
        "group"
    ]
)

ab_rate = pick(
    AB,
    [
        "conversion_rate_pct",
        "conversion_rate",
        "conversion_pct",
        "rate"
    ]
)

ab_conversions = pick(
    AB,
    [
        "conversions",
        "conversion_count"
    ]
)


CAMPAIGN = (
    "synthetic_marketing_campaign_performance"
)

campaign = pick(
    CAMPAIGN,
    [
        "campaign",
        "campaign_name"
    ]
)

spend = pick(
    CAMPAIGN,
    [
        "spend",
        "ad_spend"
    ]
)

campaign_revenue = pick(
    CAMPAIGN,
    [
        "revenue",
        "total_revenue"
    ]
)

roas = pick(
    CAMPAIGN,
    [
        "roas"
    ]
)

cpa = pick(
    CAMPAIGN,
    [
        "cpa",
        "cost_per_acquisition"
    ]
)


# ---------------------------------------------------------------------
# TOP KPI CARDS
# FIELD TYPE = COLUMN
# ---------------------------------------------------------------------

card_x = 20

if spend:

    add_aggregate_card(
        page4,
        CAMPAIGN,
        spend,
        "Synthetic Total Campaign Spend",
        card_x,
        20,
        300,
        115,
        aggregation=0,
        z=1
    )

    log_visual(
        page4_name,
        "Synthetic Total Campaign Spend",
        "COLUMN",
        f"SUM({CAMPAIGN}[{spend}])"
    )

    card_x += 315


if campaign_revenue:

    add_aggregate_card(
        page4,
        CAMPAIGN,
        campaign_revenue,
        "Synthetic Total Campaign Revenue",
        card_x,
        20,
        300,
        115,
        aggregation=0,
        z=2
    )

    log_visual(
        page4_name,
        "Synthetic Total Campaign Revenue",
        "COLUMN",
        (
            f"SUM("
            f"{CAMPAIGN}"
            f"[{campaign_revenue}]"
            f")"
        )
    )

    card_x += 315


if roas:

    add_aggregate_card(
        page4,
        CAMPAIGN,
        roas,
        "Synthetic Average Campaign ROAS",
        card_x,
        20,
        300,
        115,
        aggregation=1,
        z=3
    )

    log_visual(
        page4_name,
        "Synthetic Average Campaign ROAS",
        "COLUMN",
        (
            f"AVERAGE("
            f"{CAMPAIGN}[{roas}]"
            f")"
        )
    )


# ---------------------------------------------------------------------
# REAL GA4 FORECAST
# ---------------------------------------------------------------------

if forecast_date and forecast_value:

    add_category_chart(
        page4,
        "lineChart",
        FORECAST,
        forecast_date,
        forecast_value,
        "REAL GA4 — 14-Day Revenue Forecast",
        20,
        160,
        600,
        245,
        aggregation=0,
        sort="category_asc",
        z=4
    )

    log_visual(
        page4_name,
        "REAL GA4 — 14-Day Revenue Forecast",
        "COLUMN",
        (
            f"{FORECAST}[{forecast_date}] + "
            f"SUM({FORECAST}[{forecast_value}])"
        )
    )

else:
    warn(
        "Forecast chart skipped."
    )


# ---------------------------------------------------------------------
# SYNTHETIC A/B TEST
# ---------------------------------------------------------------------

if ab_variant and ab_rate:

    add_category_chart(
        page4,
        "clusteredColumnChart",
        AB,
        ab_variant,
        ab_rate,
        "SYNTHETIC — A/B Test Conversion Rate",
        650,
        160,
        610,
        245,
        aggregation=1,
        z=5
    )

    log_visual(
        page4_name,
        "SYNTHETIC — A/B Test Conversion Rate",
        "COLUMN",
        (
            f"{AB}[{ab_variant}] + "
            f"AVERAGE({AB}[{ab_rate}])"
        )
    )

elif ab_variant and ab_conversions:

    add_category_chart(
        page4,
        "clusteredColumnChart",
        AB,
        ab_variant,
        ab_conversions,
        "SYNTHETIC — A/B Test Conversions",
        650,
        160,
        610,
        245,
        aggregation=0,
        z=5
    )

    log_visual(
        page4_name,
        "SYNTHETIC — A/B Test Conversions",
        "COLUMN",
        (
            f"{AB}[{ab_variant}] + "
            f"SUM({AB}[{ab_conversions}])"
        )
    )

else:
    warn(
        "Synthetic A/B test chart skipped."
    )


# ---------------------------------------------------------------------
# SYNTHETIC CAMPAIGN ROAS
# ---------------------------------------------------------------------

if campaign and roas:

    add_category_chart(
        page4,
        "clusteredBarChart",
        CAMPAIGN,
        campaign,
        roas,
        "SYNTHETIC — ROAS by Campaign",
        20,
        435,
        600,
        250,
        aggregation=1,
        z=6
    )

    log_visual(
        page4_name,
        "SYNTHETIC — ROAS by Campaign",
        "COLUMN",
        (
            f"{CAMPAIGN}[{campaign}] + "
            f"AVERAGE({CAMPAIGN}[{roas}])"
        )
    )

else:
    warn(
        "Synthetic campaign ROAS chart skipped."
    )


# ---------------------------------------------------------------------
# SYNTHETIC CAMPAIGN CPA
# ---------------------------------------------------------------------

if campaign and cpa:

    add_category_chart(
        page4,
        "clusteredBarChart",
        CAMPAIGN,
        campaign,
        cpa,
        "SYNTHETIC — CPA by Campaign",
        650,
        435,
        610,
        250,
        aggregation=1,
        z=7
    )

    log_visual(
        page4_name,
        "SYNTHETIC — CPA by Campaign",
        "COLUMN",
        (
            f"{CAMPAIGN}[{campaign}] + "
            f"AVERAGE({CAMPAIGN}[{cpa}])"
        )
    )

else:
    warn(
        "Synthetic campaign CPA chart skipped."
    )


# =====================================================================
# UPDATE PAGE ORDER
# =====================================================================

pages_metadata = read_json(
    PAGES_JSON
)


def page_id_by_name(name):

    for folder in PAGES_ROOT.iterdir():

        if not folder.is_dir():
            continue

        page_file = (
            folder /
            "page.json"
        )

        if not page_file.exists():
            continue

        page = read_json(
            page_file
        )

        if (
            page.get("displayName")
            == name
        ):
            return page[
                "name"
            ]

    raise RuntimeError(
        f"Page not found: {name}"
    )


page2_id = page_id_by_name(
    page2_name
)

page3_id = page_id_by_name(
    page3_name
)

page4_id = page_id_by_name(
    page4_name
)


pages_metadata[
    "pageOrder"
] = [
    EXECUTIVE_ID,
    page2_id,
    page3_id,
    page4_id
]

pages_metadata[
    "activePageName"
] = EXECUTIVE_ID

write_json(
    PAGES_JSON,
    pages_metadata
)


# =====================================================================
# VALIDATE ALL GENERATED JSON
# =====================================================================

print()
print(
    "VALIDATING REPORT JSON FILES..."
)

errors = []

for path in REPORT.rglob(
    "*.json"
):

    try:
        read_json(
            path
        )

    except Exception as exc:

        errors.append(
            (
                path,
                str(exc)
            )
        )


if errors:

    print()
    print(
        "JSON VALIDATION ERRORS:"
    )

    for path, error in errors:

        print(
            path
        )

        print(
            error
        )

    raise RuntimeError(
        "JSON validation failed."
    )


# =====================================================================
# WRITE BUILD MANIFEST
# =====================================================================

manifest_path = (
    POWERBI /
    "dashboard_build_manifest.txt"
)

lines = [
    "CUSTOMER 360 & REVENUE GROWTH DASHBOARD",
    "CODE-FIRST PBIR BUILD MANIFEST",
    "=" * 72,
    "",
    "PAGE 1 — Executive Overview",
    "Existing working page retained.",
    "KPI cards use MEASURES.",
    "",
    "PAGE 2 — Customer & Retention",
    "Visuals primarily use COLUMNS.",
    "",
    "PAGE 3 — Acquisition & Product Performance",
    "Visuals primarily use COLUMNS.",
    "",
    "PAGE 4 — Forecasting & Experimentation",
    "Visuals use COLUMNS.",
    "Synthetic visuals are explicitly labelled SYNTHETIC.",
    "Forecast visual is explicitly labelled REAL GA4.",
    "",
    "GENERATED VISUALS",
    "-" * 72,
]

lines.extend(
    manifest
)

if warnings:

    lines.extend(
        [
            "",
            "WARNINGS / SKIPPED VISUALS",
            "-" * 72,
        ]
    )

    lines.extend(
        warnings
    )


lines.extend(
    [
        "",
        "DETECTED CSV HEADERS",
        "-" * 72
    ]
)


for table in [
    "rfm_segment_summary",
    "cohort_retention",
    "acquisition_performance",
    "device_conversion",
    "product_performance",
    "revenue_forecast",
    "synthetic_ab_test",
    "synthetic_marketing_campaign_performance",
]:

    lines.append(
        f"{table}: "
        + ", ".join(
            csv_headers(
                table
            )
        )
    )


manifest_path.write_text(
    "\n".join(lines) + "\n",
    encoding="utf-8"
)


# =====================================================================
# FINAL SUMMARY
# =====================================================================

print()
print(
    "=" * 72
)

print(
    "ALL DASHBOARD PAGES BUILT SUCCESSFULLY"
)

print(
    "=" * 72
)

print()

print(
    "PAGE ORDER:"
)

print(
    "1. Executive Overview"
)

print(
    "2. Customer & Retention"
)

print(
    "3. Acquisition & Product Performance"
)

print(
    "4. Forecasting & Experimentation"
)

print()

print(
    "FIELD TYPES:"
)

print(
    "Page 1 KPI cards = MEASURES"
)

print(
    "Pages 2–4 categories = COLUMNS"
)

print(
    "Pages 2–4 numeric values = COLUMNS aggregated with SUM/AVERAGE"
)

print()

print(
    "BUILD MANIFEST:"
)

print(
    manifest_path
)

if warnings:

    print()

    print(
        "Some optional visuals were skipped."
    )

    print(
        "Check dashboard_build_manifest.txt"
    )

print()

print(
    "READY TO OPEN POWER BI."
)