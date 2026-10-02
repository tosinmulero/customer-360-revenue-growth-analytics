SELECT
    geo.country AS country,
    COUNT(DISTINCT user_pseudo_id) AS users,
    COUNT(*) AS events
FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
GROUP BY
    country
ORDER BY
    users DESC
LIMIT 25;
