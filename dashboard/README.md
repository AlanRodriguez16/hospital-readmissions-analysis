# Dashboard (Phase 2)

A one-page dashboard built in **Tableau Public** from the summary tables this repo exports. It answers one question for a non-technical reader: *which diabetic patients are most likely to be readmitted within 30 days?*

> **Live dashboard:** [Hospital Readmissions: Diabetic Inpatients (1999-2008) on Tableau Public](https://public.tableau.com/app/profile/alan.rodriguez2100/viz/HospitalReadmissionsDiabeticInpatients1999-2008/Dashboard1)

## Data files

Created by `python export_dashboard_data.py` (run it after `load_data.py`). Only aggregated counts and rates are exported, never patient- or encounter-level rows.

| File | What it holds |
|---|---|
| `data/readmission_rates_by_group.csv` | One row per group across five breakdowns (age, prior-year inpatient visits, primary diagnosis group, medication count, insulin status): `encounters`, `readmitted`, `rate_pct`, a 95% confidence interval (`ci_low_pct`, `ci_high_pct`), a `small_group` flag (under 100 encounters), and the overall rate for a reference line |
| `data/overall_kpis.csv` | One row of headline numbers: total encounters, patients, eligible encounters, readmitted, overall rate |

## Planned layout

1. **Title and one-line takeaway** (for example, "Patients with 3+ prior-year admissions are readmitted about 3x as often as patients with none").
2. **Headline numbers** from `overall_kpis.csv`: eligible encounters and overall 30-day rate.
3. **Main chart:** readmission rate by prior-year inpatient visits (the strongest pattern), with a reference line at the overall rate. This gets the one highlight color.
4. **Four smaller charts** in grey: age group, primary diagnosis group, medication count, insulin status.
5. **Footnote:** data source (UCI Diabetes 130-US hospitals, 1999-2008), diabetic inpatients only, associations not causes, small groups flagged.

## How to build it (Tableau Public, free)

1. Download **Tableau Public** from public.tableau.com and make a free account.
2. Open it, choose **Text file**, and select `readmission_rates_by_group.csv`.
3. **One sheet per breakdown.** For each sheet:
   - Drag `dimension` to **Filters**, pick a single value (for example, "Prior-year inpatient visits").
   - Put `group_label` on **Columns** and `rate_pct` on **Rows** (a bar chart).
   - Sort the groups by `sort_order` (right-click the axis label, Sort, choose the field `sort_order`, minimum).
   - Put `rate_pct` on **Label** so the numbers show on the bars.
   - Put `small_group` on **Color** to flag the noisy groups in a lighter shade.
   - Drag `overall_rate_pct`, `encounters`, `readmitted`, `ci_low_pct`, and `ci_high_pct` onto **Tooltip** so hovering shows the counts and interval.
   - In the Analytics pane, add a **Reference Line** at the average of `overall_rate_pct`.
4. **Headline numbers:** add `overall_kpis.csv` as a second data source (Data menu, New Data Source) and make a sheet with big text for the eligible encounters and the overall rate.
5. **Combine on a Dashboard:** create a new dashboard, drag the sheets on, use the layout above, and write a chart title that states the finding, not just the field name.
6. **Publish:** File, Save to Tableau Public. Copy the link into this file and into the main README. Save a screenshot as `dashboard/dashboard.png` and add it to the main README.

**Optional, to show uncertainty on the bars:** the 95% interval is in the data. In Tableau you can draw it as a range with a Gantt mark on a second axis. If that gets fiddly, the tooltip already carries it, and that is enough.

## Design choices to explain in an interview

- Bars start at zero, so differences are not exaggerated.
- One highlight color for the main finding, grey for context.
- Small groups are flagged because their rates are noisy, not hidden.
- The reference line shows the overall rate so every bar is read against a baseline.
