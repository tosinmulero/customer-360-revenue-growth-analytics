SELECT
    device.category AS device_category,
    COUNT(DISTINCT user_pseudo_id) AS users,
    COUNT(*) AS events
FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
GROUP BY
    device_category
ORDER BY
    users DESC;
