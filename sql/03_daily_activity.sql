SELECT
    PARSE_DATE('%Y%m%d', event_date) AS event_date,
    COUNT(*) AS total_events,
    COUNT(DISTINCT user_pseudo_id) AS active_users
FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
GROUP BY
    event_date
ORDER BY
    event_date;
