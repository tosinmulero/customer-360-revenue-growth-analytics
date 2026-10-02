WITH base AS (

    SELECT
        user_pseudo_id,
        PARSE_DATE('%Y%m%d', event_date) AS event_date,
        event_timestamp,
        event_name,

        (
            SELECT value.int_value
            FROM UNNEST(event_params)
            WHERE key = 'ga_session_id'
        ) AS ga_session_id,

        COALESCE(ecommerce.purchase_revenue, 0) AS purchase_revenue,

        COALESCE(traffic_source.source, 'Unknown') AS source,
        COALESCE(traffic_source.medium, 'Unknown') AS medium,
        COALESCE(device.category, 'Unknown') AS device_category,
        COALESCE(geo.country, 'Unknown') AS country

    FROM
        `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

    WHERE
        user_pseudo_id IS NOT NULL
),

user_metrics AS (

    SELECT
        user_pseudo_id,

        MIN(event_date) AS first_seen_date,
        MAX(event_date) AS last_seen_date,

        COUNT(*) AS total_events,

        COUNT(
            DISTINCT IF(
                ga_session_id IS NOT NULL,
                CONCAT(
                    user_pseudo_id,
                    '-',
                    CAST(ga_session_id AS STRING)
                ),
                NULL
            )
        ) AS sessions,

        COUNTIF(event_name = 'view_item') AS product_views,
        COUNTIF(event_name = 'add_to_cart') AS add_to_carts,
        COUNTIF(event_name = 'begin_checkout') AS checkouts,
        COUNTIF(event_name = 'purchase') AS purchases,

        ROUND(
            SUM(
                IF(
                    event_name = 'purchase',
                    purchase_revenue,
                    0
                )
            ),
            2
        ) AS total_revenue

    FROM base

    GROUP BY
        user_pseudo_id
),

first_touch AS (

    SELECT
        user_pseudo_id,

        ARRAY_AGG(
            source
            ORDER BY event_timestamp
            LIMIT 1
        )[OFFSET(0)] AS acquisition_source,

        ARRAY_AGG(
            medium
            ORDER BY event_timestamp
            LIMIT 1
        )[OFFSET(0)] AS acquisition_medium,

        ARRAY_AGG(
            device_category
            ORDER BY event_timestamp
            LIMIT 1
        )[OFFSET(0)] AS first_device,

        ARRAY_AGG(
            country
            ORDER BY event_timestamp
            LIMIT 1
        )[OFFSET(0)] AS first_country

    FROM base

    GROUP BY
        user_pseudo_id
)

SELECT
    m.*,
    f.acquisition_source,
    f.acquisition_medium,
    f.first_device,
    f.first_country,

    ROUND(
        SAFE_DIVIDE(
            m.total_revenue,
            NULLIF(m.purchases, 0)
        ),
        2
    ) AS avg_order_value

FROM user_metrics m

LEFT JOIN first_touch f
    USING (user_pseudo_id)

ORDER BY
    total_revenue DESC;
