SELECT
    COALESCE(traffic_source.source, 'Unknown') AS source,
    COALESCE(traffic_source.medium, 'Unknown') AS medium,
    COUNT(DISTINCT user_pseudo_id) AS users,
    COUNT(*) AS events
FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
GROUP BY
    source,
    medium
ORDER BY
    users DESC;
