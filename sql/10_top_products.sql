SELECT
    item.item_name,

    SUM(item.quantity) AS units_sold,

    ROUND(
        SUM(item.item_revenue),
        2
    ) AS item_revenue

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item

WHERE
    event_name = 'purchase'

GROUP BY
    item.item_name

ORDER BY
    item_revenue DESC

LIMIT 20;
