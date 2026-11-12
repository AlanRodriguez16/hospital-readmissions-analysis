-- Q5. Do patients on more medications get readmitted more often?
-- Groups encounters by fixed medication-count ranges so the groups never overlap.
-- (An earlier version used NTILE quartiles, but NTILE splits tied values across groups,
-- so encounters with the same count could land in different quartiles.)
-- Caution: medication count rises with length of stay and illness severity, so it partly
-- reflects how sick the patient was, not just treatment.
-- Skills: CASE bucketing, aggregation, ordering by bucket
WITH bucketed AS (
    SELECT
        num_medications,
        readmitted_30d,
        CASE WHEN num_medications <= 5  THEN 1
             WHEN num_medications <= 10 THEN 2
             WHEN num_medications <= 15 THEN 3
             WHEN num_medications <= 20 THEN 4
             ELSE 5 END AS bucket_order,
        CASE WHEN num_medications <= 5  THEN '1-5'
             WHEN num_medications <= 10 THEN '6-10'
             WHEN num_medications <= 15 THEN '11-15'
             WHEN num_medications <= 20 THEN '16-20'
             ELSE '21+' END AS medication_group
    FROM v_eligible_encounters
    WHERE num_medications IS NOT NULL
)
SELECT
    medication_group,
    COUNT(*)                               AS encounters,
    ROUND(100.0 * AVG(readmitted_30d), 1)  AS rate_pct
FROM bucketed
GROUP BY bucket_order, medication_group
ORDER BY bucket_order;
