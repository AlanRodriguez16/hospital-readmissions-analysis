-- Views used by the analysis queries. Created after the data is loaded.

DROP VIEW IF EXISTS v_diagnosis_groups;
DROP VIEW IF EXISTS v_eligible_encounters;

-- Encounters where a 30-day readmission is actually possible.
CREATE VIEW v_eligible_encounters AS
SELECT *
FROM encounters
WHERE readmission_eligible = 1;

-- Maps each ICD-9 code to a broad diagnosis group, using the grouping from the
-- dataset's source paper (Strack et al., 2014). Ranges are floors, so 785.4 is in "785".
CREATE VIEW v_diagnosis_groups AS
SELECT
    encounter_id,
    position,
    icd9_code,
    CASE
        WHEN icd9_code LIKE 'V%' OR icd9_code LIKE 'E%'            THEN 'Other'
        WHEN code_num >= 250 AND code_num < 251                    THEN 'Diabetes'
        WHEN (code_num >= 390 AND code_num < 460)
          OR (code_num >= 785 AND code_num < 786)                  THEN 'Circulatory'
        WHEN (code_num >= 460 AND code_num < 520)
          OR (code_num >= 786 AND code_num < 787)                  THEN 'Respiratory'
        WHEN (code_num >= 520 AND code_num < 580)
          OR (code_num >= 787 AND code_num < 788)                  THEN 'Digestive'
        WHEN code_num >= 800 AND code_num < 1000                   THEN 'Injury'
        WHEN code_num >= 710 AND code_num < 740                    THEN 'Musculoskeletal'
        WHEN (code_num >= 580 AND code_num < 630)
          OR (code_num >= 788 AND code_num < 789)                  THEN 'Genitourinary'
        WHEN code_num >= 140 AND code_num < 240                    THEN 'Neoplasms'
        ELSE 'Other'
    END AS dx_group
FROM (
    SELECT encounter_id, position, icd9_code, CAST(icd9_code AS REAL) AS code_num
    FROM diagnoses
);
