"""
Export summary tables for the dashboard (Tableau Public, Power BI, or Excel).

Reads data/readmissions.db and writes two small CSV files to dashboard/data/:

  readmission_rates_by_group.csv   one row per group, with a 95% confidence interval
  overall_kpis.csv                 one row of headline numbers

Only aggregated counts and rates are exported, never patient- or encounter-level rows.
That keeps the dashboard small and avoids republishing the raw dataset.

The group definitions match the SQL files in sql/queries/, so the dashboard numbers
match the Findings in the README.

Usage:
    python export_dashboard_data.py
    python export_dashboard_data.py --db some.db --out some_folder
"""

import argparse
import csv
import math
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SMALL_GROUP_THRESHOLD = 100  # groups below this many encounters are flagged as noisy

# Each query returns: group_label, sort_order, encounters, readmitted
QUERIES = {
    "Age group": """
        SELECT age_group, age_lo, COUNT(*), SUM(readmitted_30d)
        FROM v_eligible_encounters
        WHERE age_group IS NOT NULL
        GROUP BY age_group, age_lo
    """,
    "Prior-year inpatient visits": """
        SELECT
            CASE WHEN number_inpatient >= 3 THEN '3+' ELSE CAST(number_inpatient AS TEXT) END,
            CASE WHEN number_inpatient >= 3 THEN 3 ELSE number_inpatient END,
            COUNT(*), SUM(readmitted_30d)
        FROM v_eligible_encounters
        WHERE number_inpatient IS NOT NULL
        GROUP BY 1, 2
    """,
    "Primary diagnosis group": """
        SELECT d.dx_group, 0, COUNT(*), SUM(e.readmitted_30d)
        FROM v_eligible_encounters AS e
        JOIN v_diagnosis_groups    AS d
          ON d.encounter_id = e.encounter_id AND d.position = 1
        GROUP BY d.dx_group
        HAVING COUNT(*) >= 50
    """,
    "Medication count": """
        SELECT
            CASE WHEN num_medications <= 5  THEN '1-5'
                 WHEN num_medications <= 10 THEN '6-10'
                 WHEN num_medications <= 15 THEN '11-15'
                 WHEN num_medications <= 20 THEN '16-20'
                 ELSE '21+' END,
            CASE WHEN num_medications <= 5  THEN 1
                 WHEN num_medications <= 10 THEN 2
                 WHEN num_medications <= 15 THEN 3
                 WHEN num_medications <= 20 THEN 4
                 ELSE 5 END,
            COUNT(*), SUM(readmitted_30d)
        FROM v_eligible_encounters
        WHERE num_medications IS NOT NULL
        GROUP BY 1, 2
    """,
    "Insulin status": """
        SELECT
            COALESCE(m.status, 'No'),
            CASE COALESCE(m.status, 'No')
                 WHEN 'No' THEN 1 WHEN 'Steady' THEN 2 WHEN 'Down' THEN 3 ELSE 4 END,
            COUNT(*), SUM(e.readmitted_30d)
        FROM v_eligible_encounters AS e
        LEFT JOIN medications      AS m
               ON m.encounter_id = e.encounter_id AND m.drug = 'insulin'
        GROUP BY 1, 2
    """,
}


def wilson_interval(readmitted: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """95% Wilson score interval for a proportion, returned as percentages."""
    if n == 0:
        return (0.0, 0.0)
    p = readmitted / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (100 * (centre - half), 100 * (centre + half))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "readmissions.db")
    parser.add_argument("--out", type=Path, default=ROOT / "dashboard" / "data")
    args = parser.parse_args()

    if not args.db.exists():
        sys.exit(f"Database not found: {args.db}\nRun `python load_data.py` first.")

    args.out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    try:
        total_encounters = conn.execute("SELECT COUNT(*) FROM encounters").fetchone()[0]
        patients = conn.execute("SELECT COUNT(*) FROM patients").fetchone()[0]
        eligible, readmitted = conn.execute(
            "SELECT COUNT(*), SUM(readmitted_30d) FROM v_eligible_encounters"
        ).fetchone()
        overall_rate = 100.0 * readmitted / eligible

        rows = []
        for dimension, sql in QUERIES.items():
            results = conn.execute(sql).fetchall()
            if dimension == "Primary diagnosis group":
                # No natural order, so rank by readmission rate (highest first).
                results = sorted(results, key=lambda r: r[3] / r[2], reverse=True)
                results = [(label, i + 1, n, x) for i, (label, _, n, x) in enumerate(results)]
            for label, sort_order, n, x in sorted(results, key=lambda r: r[1]):
                low, high = wilson_interval(x, n)
                rows.append({
                    "dimension": dimension,
                    "group_label": label,
                    "sort_order": sort_order,
                    "encounters": n,
                    "readmitted": x,
                    "rate_pct": round(100.0 * x / n, 1),
                    "ci_low_pct": round(low, 1),
                    "ci_high_pct": round(high, 1),
                    "small_group": int(n < SMALL_GROUP_THRESHOLD),
                    "overall_rate_pct": round(overall_rate, 1),
                })
    finally:
        conn.close()

    rates_path = args.out / "readmission_rates_by_group.csv"
    with rates_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    kpi_path = args.out / "overall_kpis.csv"
    with kpi_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["total_encounters", "patients", "eligible_encounters",
                         "excluded_died_or_hospice", "readmitted_30d", "overall_rate_pct"])
        writer.writerow([total_encounters, patients, eligible,
                         total_encounters - eligible, readmitted, round(overall_rate, 1)])

    print(f"Wrote {len(rows)} group rows to {rates_path}")
    print(f"Wrote headline numbers to {kpi_path}")
    print(f"Overall: {eligible:,} eligible encounters, {overall_rate:.1f}% readmitted within 30 days")


if __name__ == "__main__":
    main()
