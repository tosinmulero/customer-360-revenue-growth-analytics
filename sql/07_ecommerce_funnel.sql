SELECT
    COUNT(DISTINCT CASE
        WHEN event_name = 'session_start'
        THEN user_pseudo_id
    END) AS session_users,

    COUNT(DISTINCT CASE
        WHEN event_name = 'view_item'
        THEN user_pseudo_id
    END) AS product_view_users,

    COUNT(DISTINCT CASE
        WHEN event_name = 'add_to_cart'
        THEN user_pseudo_id
    END) AS add_to_cart_users,

    COUNT(DISTINCT CASE
        WHEN event_name = 'begin_checkout'
        THEN user_pseudo_id
    END) AS checkout_users,

    COUNT(DISTINCT CASE
        WHEN event_name = 'purchase'
        THEN user_pseudo_id
    END) AS purchasing_users

FROM
    `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`;
