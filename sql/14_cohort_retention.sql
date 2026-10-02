WITH user_months AS (

    SELECT DISTINCT

        user_pseudo_id,

        DATE_TRUNC(
            PARSE_DATE('%Y%m%d', event_date),
            MONTH
        ) AS activity_month

    FROM
        `bigquery-public-data.ga4_obfuscated_sample_ecommerce.events_*`

    WHERE
        user_pseudo_id IS NOT NULL
),

first_seen AS (

    SELECT

        user_pseudo_id,

        MIN(activity_month) AS cohort_month

    FROM user_months

    GROUP BY
        user_pseudo_id
),

cohort_sizes AS (

    SELECT

        cohort_month,

        COUNT(*) AS cohort_size

    FROM first_seen

    GROUP BY
        cohort_month
),

retention AS (

    SELECT

        f.cohort_month,

        u.activity_month,

        DATE_DIFF(
            u.activity_month,
            f.cohort_month,
            MONTH
        ) AS months_since_acquisition,

        COUNT(
            DISTINCT u.user_pseudo_id
        ) AS active_users

    FROM user_months u

    INNER JOIN first_seen f
        USING (user_pseudo_id)

    GROUP BY
        f.cohort_month,
        u.activity_month,
        months_since_acquisition
)

SELECT

    r.cohort_month,
    r.activity_month,
    r.months_since_acquisition,

    c.cohort_size,
    r.active_users,

    ROUND(
        SAFE_DIVIDE(
            r.active_users,
            c.cohort_size
        ) * 100,
        2
    ) AS retention_rate_pct

FROM retention r

INNER JOIN cohort_sizes c
    USING (cohort_month)

ORDER BY
    cohort_month,
    months_since_acquisition;
