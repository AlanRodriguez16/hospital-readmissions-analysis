# Hospital Readmissions Analysis (SQL + Python)

Which diabetic patients are readmitted to the hospital within 30 days, and what do those patients have in common? This project loads a public hospital dataset into a relational SQLite database and answers business-style questions with SQL (joins, CTEs, window functions). Later phases add a dashboard and a predictive model.

> **Status: Phase 1 (database and SQL) is complete.** Phase 2 (dashboard) is in progress; Phases 3-4 (predictive model, polish) are planned. See the Roadmap.

## Why readmissions
Unplanned readmissions are a quality and cost problem for hospitals, and U.S. Medicare penalizes hospitals with excess readmissions for certain conditions. Understanding which patients come back, and why, is a typical healthcare analytics question.

## Data
**UCI "Diabetes 130-US hospitals for years 1999-2008"**: one row per hospital encounter for diabetic patients across 130 U.S. hospitals (~100,000 rows, 50 columns). Per the source paper, the extract covers inpatient encounters of 1-14 days. See `data/README.md` for how to download it (it is not stored in this repo).

Citation: Strack, B., DeShazo, J. P., Gennings, C., et al. (2014). *Impact of HbA1c Measurement on Hospital Readmission Rates: Analysis of 70,000 Clinical Database Patient Records.* BioMed Research International.

**Quirks handled in `load_data.py`:**
- `?` means missing and becomes `NULL`. But `None` in `A1Cresult` and `max_glu_serum` means "test not performed", a real category, so it is kept as text.
- Patients who died or went to hospice at discharge cannot be readmitted. They are flagged `readmission_eligible = 0` and excluded from every rate.
- The target is `readmitted_30d = 1` only for the source label `<30`. The `>30` label counts as not readmitted within 30 days.
- The same patient can appear in many encounters, which matters for modeling (see Roadmap).

## Database design
```
patients ----< encounters ----< diagnoses     (primary + 2 secondary ICD-9 codes)
                    |---------< medications   (23 drugs, only those actually used)
admission_types / discharge_dispositions / admission_sources   (lookups)
```
Two views: `v_eligible_encounters` (readmittable encounters only) and `v_diagnosis_groups` (ICD-9 codes grouped into broad categories, using the grouping from the source paper).

## Queries (`sql/queries/`)
| File | Question | SQL skills |
|---|---|---|
| `01_readmission_rate_by_age` | Overall and by-age 30-day readmission rate | CTE, UNION ALL, view |
| `02_prior_inpatient_visits` | Does prior-year utilization predict readmission? | CASE, `FIRST_VALUE` window |
| `03_primary_diagnosis_group` | Which diagnosis groups are readmitted most? | JOIN, HAVING |
| `04_top_specialties_by_age_band` | Top specialties per age band | `RANK() OVER (PARTITION BY ...)` |
| `05_medication_count_groups` | Readmission by medication load | `CASE` bucketing, aggregation |
| `06_insulin_status` | Readmission by insulin status | LEFT JOIN, COALESCE |
| `07_repeat_patients` | Concentration among repeat patients | Patient-level rollup |

## Run it
```bash
pip install -r requirements.txt

# 1. Verify the code works (uses random synthetic data, no download needed)
python tests/smoke_test.py

# 2. Real run: download the data first (see data/README.md), then
python load_data.py          # builds data/readmissions.db
python run_queries.py        # prints each result and saves CSVs to results/

# 3. Optional: export summary tables for the dashboard (see dashboard/README.md)
python export_dashboard_data.py   # writes dashboard/data/*.csv (aggregated only)
```
Open `data/readmissions.db` in [DB Browser for SQLite](https://sqlitebrowser.org/) if you want to write your own queries.

## Roadmap
| Phase | Work | Estimated effort |
|---|---|---|
| 1. SQL analysis | Run on real data, read the results, write up findings, add 3-5 of your own queries | 15-20 hrs |
| 2. Dashboard | Tableau Public, built from exported summary tables (export script done; see `dashboard/`) | 6-10 hrs |
| 3. Predictive model | Logistic regression vs. random forest for 30-day readmission | 8-15 hrs |
| 4. Polish | Findings, limitations, screenshots, clean README | 3-5 hrs |

**Modeling notes for Phase 3:** split train/test by `patient_nbr` (for example with `GroupKFold`), not by encounter, because the same patient appearing on both sides leaks information and inflates accuracy. Also expect a class imbalance, since only about 11% of encounters are `<30`, so accuracy alone is misleading; report ROC-AUC and precision/recall.

## Findings
Results from running the seven queries on the real data. All figures are 30-day readmission rates among readmission-eligible encounters.

- **Overall:** 101,766 encounters from 71,518 patients were loaded. After excluding 2,423 encounters where the patient died or went to hospice, 99,343 remain, and 11.4% (11,314) were readmitted within 30 days.
- **Prior-year inpatient visits is the strongest pattern (Q2).** The rate rises from 8.6% for patients with 0 prior visits to 13.3% (1 visit), 17.9% (2 visits), and 26.4% (3+ visits), about three times the baseline.
- **Primary diagnosis matters much less (Q3).** Rates range only from 9.5% (musculoskeletal) to 13.1% (diabetes as the primary diagnosis).
- **Age is not a straight line (Q1).** The rate is lowest around ages 50-60 (9.8%) and climbs to 12.6% at 80-90. Ages 20-30 are high (14.3%, 1,649 encounters). Groups under age 20 are too small to read.
- **Insulin changes (Q6).** The rate is 14.2% when the insulin dose was lowered and 13.3% when it was raised, versus 11.4% when steady and 10.2% with no insulin.
- **Medication count (Q5).** The rate rises steadily with the number of medications: 7.6% for 1-5 medications, 9.6% for 6-10, 11.1% for 11-15, 12.4% for 16-20, and 13.2% for 21 or more. Medication count also rises with length of stay and illness severity, so this partly reflects how sick the patient was.
- **Repeat patients (Q7).** 4.3% of single-encounter patients have a 30-day readmission, versus 80.8% of patients with 5 or more encounters. Much of this is mechanical: more encounters means more chances to be readmitted, so it does not show that repeat patients are higher risk per stay.
- **Medical specialty (Q4).** Hematology and oncology top the older age bands, but these groups are small (for example, about 37 hematology encounters for ages 50-69), so the rates are noisy and should not be over-read.

**Takeaway:** in this data, how often a patient was recently hospitalized tells you far more about 30-day readmission risk than their diagnosis group does. These are associations, not causes: patients who are sicker are more likely to have many prior visits, more medications, and insulin changes at the same time.

## Limitations
- The data covers 1999-2008 and diabetic inpatients only, so it does not represent current care or other conditions.
- The dataset has no dates, so encounters cannot be put in time order, and no cost data, so "cost of readmissions" cannot be measured directly here.
- Results are associations, not causes. Sicker patients differ from healthier ones in many ways at once.
- `medical_specialty` is missing for about half the encounters, so Q4 covers only part of the data.
- Rates for small groups are noisy; queries filter out groups under a minimum size.
- Synthetic test data (`tests/`) is random. It checks that the code runs, and no result from it should be reported. For example, Q7 shows rising readmission with encounter count even on random data, because more encounters means more chances to be readmitted.
