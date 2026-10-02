SELECT

    COALESCE(
        traffic_source.source,
        'Unknown'
    ) AS source,

    COALESCE(
        traffic_source.medium,
        'Unknown'
    ) AS medium,

    COUNT(
        DISTINCT user_pseudo_id
    ) AS users,

    COUNT(
        DISTINCT IF(
            event_name = 'purchase',
            user_pseudo_id,
            NULL
        )
    ) AS purchasing_users,

    COUNTIF(
        event_name = 'purchase'
    ) AS purchase_events,

    ROUND(
        SUM(
            IF(
                event_name = 'purchase',
                COALESCE(ecommerce.purchase_revenue, 0),
                0
            )
        ),
        2
    ) AS revenue,

    ROUND(
        SAFE_DIVIDE(
            COUNT(
                DISTINCT IF(
                    event_name = 'purchase',
                    user_pseudo_id,
                    NULL
                )
            ),
            COUNT(DISTINCT user_pseudo_id)
        ) * 100,
        2
    ) AS conversion_rate_pct,

    ROUND(
        SAFE_DIVIDE(
            SUM(
                IF(
                    event_name = 'purchase',
                    COALESCE(ecommerce.purchase_revenue, 0),
                    0
                )
            ),
            COUNT(DISTINCT user_pseudo_id)
        ),
        2
    ) AS revenue_per_user

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

WHERE
    user_pseudo_id IS NOT NULL

GROUP BY
    source,
    medium

ORDER BY
    revenue DESC;
