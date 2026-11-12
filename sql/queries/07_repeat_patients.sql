-- Q7. How concentrated are readmissions among patients who show up repeatedly?
-- Rolls encounters up to the patient level, then groups patients by how many times they appear.
-- Caution: patients with more encounters have more chances to be readmitted, so part of
-- this pattern is mechanical. It describes the data but does not show that repeat patients
-- are higher risk per stay.
-- Skills: patient-level rollup with CTEs, nested aggregation
WITH per_patient AS (
    SELECT
        patient_nbr,
        COUNT(*)            AS n_encounters,
        MAX(readmitted_30d) AS ever_readmitted_30d
    FROM v_eligible_encounters
    GROUP BY patient_nbr
),
bucketed AS (
    SELECT
        n_encounters,
        ever_readmitted_30d,
        CASE WHEN n_encounters = 1 THEN '1 encounter'
             WHEN n_encounters = 2 THEN '2 encounters'
             WHEN n_encounters <= 4 THEN '3-4 encounters'
             ELSE '5+ encounters' END AS encounter_bucket
    FROM per_patient
)
SELECT
    encounter_bucket,
    COUNT(*)                                       AS patients,
    ROUND(100.0 * AVG(ever_readmitted_30d), 1)     AS pct_with_a_30d_readmission
FROM bucketed
GROUP BY encounter_bucket
ORDER BY MIN(n_encounters);
