-- Q6. How does readmission differ by insulin status during the stay?
-- The medications table only stores drugs that were used, so patients with no insulin
-- row are labelled 'No' using LEFT JOIN + COALESCE.
-- Note: this is an association, not a causal effect. Sicker patients are more likely to
-- be on insulin or have it adjusted.
-- Skills: LEFT JOIN, COALESCE
SELECT
    COALESCE(m.status, 'No')                AS insulin_status,   -- No / Steady / Up / Down
    COUNT(*)                                AS encounters,
    ROUND(100.0 * AVG(e.readmitted_30d), 1) AS rate_pct
FROM v_eligible_encounters AS e
LEFT JOIN medications      AS m
       ON m.encounter_id = e.encounter_id
      AND m.drug = 'insulin'
GROUP BY COALESCE(m.status, 'No')
ORDER BY rate_pct DESC;
