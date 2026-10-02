SELECT
    PARSE_DATE('%Y%m%d', event_date) AS date,

    COUNTIF(
        event_name = 'purchase'
    ) AS purchases,

    COUNT(
        DISTINCT IF(
            event_name = 'purchase',
            user_pseudo_id,
            NULL
        )
    ) AS purchasing_users,

    ROUND(
        SUM(
            IF(
                event_name = 'purchase',
                COALESCE(ecommerce.purchase_revenue, 0),
                0
            )
        ),
        2
    ) AS revenue

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

GROUP BY
    date

ORDER BY
    date;
