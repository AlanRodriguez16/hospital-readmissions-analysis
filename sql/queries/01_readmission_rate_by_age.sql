-- Q1. What is the 30-day readmission rate overall and by age group?
-- Skills: CTE, GROUP BY, UNION ALL, view
WITH by_age AS (
    SELECT
        age_group,
        age_lo                                   AS sort_key,
        COUNT(*)                                 AS encounters,
        SUM(readmitted_30d)                      AS readmitted,
        ROUND(100.0 * AVG(readmitted_30d), 1)    AS rate_pct
    FROM v_eligible_encounters
    GROUP BY age_group, age_lo
),
overall AS (
    SELECT
        'ALL AGES',
        999,
        COUNT(*),
        SUM(readmitted_30d),
        ROUND(100.0 * AVG(readmitted_30d), 1)
    FROM v_eligible_encounters
)
SELECT age_group, encounters, readmitted, rate_pct
FROM (SELECT * FROM by_age UNION ALL SELECT * FROM overall)
ORDER BY sort_key;
