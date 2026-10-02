WITH purchases AS (

    SELECT

        user_pseudo_id,

        PARSE_DATE(
            '%Y%m%d',
            event_date
        ) AS purchase_date,

        COALESCE(
            ecommerce.purchase_revenue,
            0
        ) AS revenue

    FROM
        `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

    WHERE
        event_name = 'purchase'
        AND user_pseudo_id IS NOT NULL
),

reference_date AS (

    SELECT

        DATE_ADD(
            MAX(purchase_date),
            INTERVAL 1 DAY
        ) AS analysis_date

    FROM purchases
),

rfm AS (

    SELECT

        p.user_pseudo_id,

        DATE_DIFF(
            r.analysis_date,
            MAX(p.purchase_date),
            DAY
        ) AS recency_days,

        COUNT(*) AS frequency,

        ROUND(
            SUM(p.revenue),
            2
        ) AS monetary_value

    FROM purchases p

    CROSS JOIN reference_date r

    GROUP BY
        p.user_pseudo_id,
        r.analysis_date
),

scored AS (

    SELECT
        *,

        NTILE(5) OVER (
            ORDER BY recency_days DESC
        ) AS recency_score,

        NTILE(5) OVER (
            ORDER BY frequency ASC
        ) AS frequency_score,

        NTILE(5) OVER (
            ORDER BY monetary_value ASC
        ) AS monetary_score

    FROM rfm
)

SELECT
    *,

    CASE

        WHEN recency_score >= 4
             AND frequency_score >= 4
        THEN 'Champions'

        WHEN frequency_score >= 4
        THEN 'Loyal Customers'

        WHEN recency_score >= 4
             AND frequency_score BETWEEN 2 AND 3
        THEN 'Potential Loyalists'

        WHEN recency_score <= 2
             AND frequency_score >= 3
        THEN 'At Risk'

        WHEN recency_score <= 2
             AND frequency_score <= 2
        THEN 'Hibernating'

        ELSE 'Need Attention'

    END AS customer_segment

FROM scored

ORDER BY
    monetary_value DESC;
