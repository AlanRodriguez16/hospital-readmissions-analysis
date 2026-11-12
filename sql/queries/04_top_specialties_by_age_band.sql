-- Q4. Within each age band, which three medical specialties have the highest readmission rates?
-- Specialties with fewer than 30 encounters in a band are dropped. Rows with a missing
-- specialty (about half of the real data) are excluded, so treat this as a partial view.
-- Skills: multi-step CTEs, RANK() with PARTITION BY
WITH banded AS (
    SELECT
        CASE WHEN age_lo < 50 THEN 'Under 50'
             WHEN age_lo < 70 THEN '50-69'
             ELSE '70+' END AS age_band,
        medical_specialty,
        readmitted_30d
    FROM v_eligible_encounters
    WHERE medical_specialty IS NOT NULL
      AND age_lo IS NOT NULL
),
rates AS (
    SELECT
        age_band,
        medical_specialty,
        COUNT(*)            AS encounters,
        AVG(readmitted_30d) AS rate
    FROM banded
    GROUP BY age_band, medical_specialty
    HAVING COUNT(*) >= 30
),
ranked AS (
    SELECT
        *,
        RANK() OVER (PARTITION BY age_band ORDER BY rate DESC) AS rnk
    FROM rates
)
SELECT
    age_band,
    rnk AS rank_in_band,
    medical_specialty,
    encounters,
    ROUND(100.0 * rate, 1) AS rate_pct
FROM ranked
WHERE rnk <= 3
ORDER BY age_band, rnk;
