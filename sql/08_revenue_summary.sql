SELECT
    COUNT(*) AS purchase_events,
    COUNT(DISTINCT user_pseudo_id) AS purchasing_users,
    ROUND(SUM(ecommerce.purchase_revenue), 2) AS total_revenue,
    ROUND(AVG(ecommerce.purchase_revenue), 2) AS avg_purchase_revenue
FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
WHERE
    event_name = 'purchase';
