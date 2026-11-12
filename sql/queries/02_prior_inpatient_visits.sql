-- Q2. Do patients with more inpatient visits in the prior year get readmitted more often?
-- Shows the rate for each group and how it compares to patients with zero prior visits.
-- Skills: CASE bucketing, CTEs, window function (FIRST_VALUE)
WITH bucketed AS (
    SELECT
        CASE WHEN number_inpatient >= 3 THEN 3 ELSE number_inpatient END AS bucket_order,
        CASE WHEN number_inpatient >= 3 THEN '3+' ELSE CAST(number_inpatient AS TEXT) END AS prior_inpatient_visits,
        readmitted_30d
    FROM v_eligible_encounters
    WHERE number_inpatient IS NOT NULL
),
rates AS (
    SELECT
        bucket_order,
        prior_inpatient_visits,
        COUNT(*)            AS encounters,
        AVG(readmitted_30d) AS rate
    FROM bucketed
    GROUP BY bucket_order, prior_inpatient_visits
)
SELECT
    prior_inpatient_visits,
    encounters,
    ROUND(100.0 * rate, 1)                                           AS rate_pct,
    ROUND(rate / FIRST_VALUE(rate) OVER (ORDER BY bucket_order), 2)  AS relative_to_zero_visits
FROM rates
ORDER BY bucket_order;
