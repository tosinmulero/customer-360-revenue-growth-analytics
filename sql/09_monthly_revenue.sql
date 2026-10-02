SELECT
    FORMAT_DATE(
        '%Y-%m',
        PARSE_DATE('%Y%m%d', event_date)
    ) AS month,

    COUNT(*) AS purchase_events,

    COUNT(DISTINCT user_pseudo_id) AS purchasing_users,

    ROUND(
        SUM(ecommerce.purchase_revenue),
        2
    ) AS revenue

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

WHERE
    event_name = 'purchase'

GROUP BY
    month

ORDER BY
    month;
