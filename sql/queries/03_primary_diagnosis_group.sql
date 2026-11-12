-- Q3. Which primary-diagnosis groups have the highest readmission rates?
-- Groups with fewer than 50 encounters are dropped because their rates are too noisy to trust.
-- Skills: JOIN across tables, view, HAVING
SELECT
    d.dx_group,
    COUNT(*)                                AS encounters,
    ROUND(100.0 * AVG(e.readmitted_30d), 1) AS rate_pct,
    ROUND(AVG(e.time_in_hospital), 1)       AS avg_days_in_hospital
FROM v_eligible_encounters AS e
JOIN v_diagnosis_groups    AS d
  ON d.encounter_id = e.encounter_id
 AND d.position = 1                         -- primary diagnosis only
GROUP BY d.dx_group
HAVING COUNT(*) >= 50
ORDER BY rate_pct DESC;
