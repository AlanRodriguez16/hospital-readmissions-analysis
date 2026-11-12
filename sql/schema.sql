-- Schema for the UCI "Diabetes 130-US hospitals (1999-2008)" readmissions data.
--
-- The raw file is one wide table (50 columns, one row per hospital encounter).
-- This splits it into related tables so the analysis queries need real JOINs:
--
--   patients ----< encounters ----< diagnoses
--                       |-----------< medications
--   (plus three small lookup tables built from IDs_mapping.csv)

PRAGMA foreign_keys = ON;

DROP VIEW  IF EXISTS v_diagnosis_groups;
DROP VIEW  IF EXISTS v_eligible_encounters;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS diagnoses;
DROP TABLE IF EXISTS encounters;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS admission_types;
DROP TABLE IF EXISTS discharge_dispositions;
DROP TABLE IF EXISTS admission_sources;

CREATE TABLE patients (
    patient_nbr  INTEGER PRIMARY KEY,
    race         TEXT,          -- NULL where the source had '?'
    gender       TEXT
);

CREATE TABLE admission_types (
    id           INTEGER PRIMARY KEY,
    description  TEXT
);

CREATE TABLE discharge_dispositions (
    id           INTEGER PRIMARY KEY,
    description  TEXT
);

CREATE TABLE admission_sources (
    id           INTEGER PRIMARY KEY,
    description  TEXT
);

CREATE TABLE encounters (
    encounter_id              INTEGER PRIMARY KEY,
    patient_nbr               INTEGER NOT NULL REFERENCES patients(patient_nbr),
    age_group                 TEXT,       -- e.g. '[70-80)'
    age_lo                    INTEGER,    -- lower bound of the age group, e.g. 70
    admission_type_id         INTEGER,
    discharge_disposition_id  INTEGER,
    admission_source_id       INTEGER,
    time_in_hospital          INTEGER,    -- days
    payer_code                TEXT,
    medical_specialty         TEXT,       -- ~half missing in the source
    num_lab_procedures        INTEGER,
    num_procedures            INTEGER,
    num_medications           INTEGER,
    number_outpatient         INTEGER,    -- visits in the prior year
    number_emergency          INTEGER,    -- visits in the prior year
    number_inpatient          INTEGER,    -- visits in the prior year
    number_diagnoses          INTEGER,
    max_glu_serum             TEXT,       -- 'None' means NOT MEASURED (a real category)
    a1c_result                TEXT,       -- 'None' means NOT MEASURED (a real category)
    med_change                TEXT,       -- 'Ch' = a diabetes medication was changed
    diabetes_med              TEXT,       -- 'Yes' / 'No'
    readmitted_raw            TEXT,       -- original label: '<30', '>30', 'NO'
    readmitted_30d            INTEGER NOT NULL CHECK (readmitted_30d IN (0, 1)),
    readmission_eligible      INTEGER NOT NULL CHECK (readmission_eligible IN (0, 1))
        -- 0 for patients who died or went to hospice at discharge: they cannot be readmitted,
        -- so including them would make hospitals look better than they are.
);

-- One row per (encounter, diagnosis slot). Source has diag_1, diag_2, diag_3.
CREATE TABLE diagnoses (
    encounter_id  INTEGER NOT NULL REFERENCES encounters(encounter_id),
    position      INTEGER NOT NULL CHECK (position IN (1, 2, 3)),  -- 1 = primary diagnosis
    icd9_code     TEXT NOT NULL,
    PRIMARY KEY (encounter_id, position)
);

-- One row per (encounter, drug) where the drug was actually used.
-- The source's 'No' (not prescribed) rows are dropped to keep the table small.
CREATE TABLE medications (
    encounter_id  INTEGER NOT NULL REFERENCES encounters(encounter_id),
    drug          TEXT NOT NULL,
    status        TEXT NOT NULL,   -- 'Steady', 'Up' (dose raised), 'Down' (dose lowered)
    PRIMARY KEY (encounter_id, drug)
);

CREATE INDEX idx_encounters_patient    ON encounters(patient_nbr);
CREATE INDEX idx_encounters_readmit    ON encounters(readmitted_30d);
CREATE INDEX idx_diagnoses_icd9        ON diagnoses(icd9_code);
CREATE INDEX idx_medications_drug      ON medications(drug);
