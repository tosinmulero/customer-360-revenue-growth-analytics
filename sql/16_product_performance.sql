SELECT

    COALESCE(
        item.item_name,
        'Unknown'
    ) AS item_name,

    COALESCE(
        item.item_category,
        'Unknown'
    ) AS item_category,

    COUNT(
        DISTINCT user_pseudo_id
    ) AS buyers,

    SUM(
        COALESCE(item.quantity, 0)
    ) AS units_sold,

    ROUND(
        SUM(
            COALESCE(
                item.item_revenue,
                item.price * item.quantity,
                0
            )
        ),
        2
    ) AS product_revenue

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`,
    UNNEST(items) AS item

WHERE
    event_name = 'purchase'

GROUP BY
    item_name,
    item_category

ORDER BY
    product_revenue DESC;
