WITH funnel AS (

    SELECT

        COUNT(
            DISTINCT IF(
                event_name = 'session_start',
                user_pseudo_id,
                NULL
            )
        ) AS session_users,

        COUNT(
            DISTINCT IF(
                event_name = 'view_item',
                user_pseudo_id,
                NULL
            )
        ) AS product_view_users,

        COUNT(
            DISTINCT IF(
                event_name = 'add_to_cart',
                user_pseudo_id,
                NULL
            )
        ) AS cart_users,

        COUNT(
            DISTINCT IF(
                event_name = 'begin_checkout',
                user_pseudo_id,
                NULL
            )
        ) AS checkout_users,

        COUNT(
            DISTINCT IF(
                event_name = 'purchase',
                user_pseudo_id,
                NULL
            )
        ) AS purchasing_users

    FROM
        `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`
)

SELECT
    *,

    ROUND(
        SAFE_DIVIDE(product_view_users, session_users) * 100,
        2
    ) AS session_to_product_view_pct,

    ROUND(
        SAFE_DIVIDE(cart_users, product_view_users) * 100,
        2
    ) AS view_to_cart_pct,

    ROUND(
        SAFE_DIVIDE(checkout_users, cart_users) * 100,
        2
    ) AS cart_to_checkout_pct,

    ROUND(
        SAFE_DIVIDE(purchasing_users, checkout_users) * 100,
        2
    ) AS checkout_to_purchase_pct,

    ROUND(
        SAFE_DIVIDE(purchasing_users, session_users) * 100,
        2
    ) AS overall_conversion_pct

FROM funnel;
