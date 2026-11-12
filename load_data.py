"""
Load the UCI "Diabetes 130-US hospitals for years 1999-2008" data into a SQLite database.

Usage:
    python load_data.py                      # reads data/raw/, writes data/readmissions.db
    python load_data.py --raw data/synthetic # use a different folder (e.g. the test fixture)

Expects diabetic_data.csv (required) and IDs_mapping.csv (optional) in the raw folder.
See data/README.md for where to download them.
"""

import argparse
import csv
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent

REQUIRED_COLUMNS = [
    "encounter_id", "patient_nbr", "race", "gender", "age",
    "admission_type_id", "discharge_disposition_id", "admission_source_id",
    "time_in_hospital", "payer_code", "medical_specialty",
    "num_lab_procedures", "num_procedures", "num_medications",
    "number_outpatient", "number_emergency", "number_inpatient",
    "diag_1", "diag_2", "diag_3", "number_diagnoses",
    "max_glu_serum", "A1Cresult", "change", "diabetesMed", "readmitted",
]

MEDICATION_COLUMNS = [
    "metformin", "repaglinide", "nateglinide", "chlorpropamide", "glimepiride",
    "acetohexamide", "glipizide", "glyburide", "tolbutamide", "pioglitazone",
    "rosiglitazone", "acarbose", "miglitol", "troglitazone", "tolazamide",
    "examide", "citoglipton", "insulin", "glyburide-metformin",
    "glipizide-metformin", "glimepiride-pioglitazone", "metformin-rosiglitazone",
    "metformin-pioglitazone",
]

# Discharge dispositions where the patient died or went to hospice. They cannot be
# readmitted, so they are excluded from readmission rates. Verify against IDs_mapping.csv:
# 11 Expired, 13/14 Hospice, 19/20/21 Expired (various settings).
NON_READMITTABLE_DISPOSITIONS = {11, 13, 14, 19, 20, 21}

INT_COLUMNS = [
    "encounter_id", "patient_nbr", "admission_type_id", "discharge_disposition_id",
    "admission_source_id", "time_in_hospital", "num_lab_procedures", "num_procedures",
    "num_medications", "number_outpatient", "number_emergency", "number_inpatient",
    "number_diagnoses",
]


def read_raw(raw_dir: Path) -> pd.DataFrame:
    path = raw_dir / "diabetic_data.csv"
    if not path.exists():
        sys.exit(f"Could not find {path}\nSee data/README.md for download steps.")

    # '?' marks missing values. keep_default_na=False matters: pandas would otherwise
    # turn the string 'None' into NaN, but in A1Cresult / max_glu_serum 'None' means
    # "test not performed", which is a real category we want to keep.
    df = pd.read_csv(
        path,
        na_values=["?", ""],
        keep_default_na=False,
        dtype={"diag_1": str, "diag_2": str, "diag_3": str},
    )

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        sys.exit(f"{path.name} is missing expected columns: {missing}\n"
                 f"Found columns: {list(df.columns)}")
    return df


def parse_id_mapping(path: Path) -> dict:
    """IDs_mapping.csv holds three small tables separated by blank lines, each starting
    with a header like 'admission_type_id,description'."""
    wanted = {"admission_type_id", "discharge_disposition_id", "admission_source_id"}
    tables, current = {}, None
    with open(path, newline="", encoding="utf-8-sig") as f:
        for row in csv.reader(f):
            if not row or all(not cell.strip() for cell in row):
                current = None
                continue
            if row[0].strip() in wanted:
                current = row[0].strip()
                tables[current] = []
                continue
            if current and len(row) >= 2:
                try:
                    tables[current].append((int(row[0]), ",".join(row[1:]).strip()))
                except ValueError:
                    pass  # skip malformed rows rather than fail
    return tables


def build_frames(df: pd.DataFrame) -> dict:
    if df["encounter_id"].duplicated().any():
        sys.exit("encounter_id is not unique in the raw file; refusing to load.")

    for col in INT_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Patients: one row per patient. Race/gender should not change; take the first non-null.
    patients = df.groupby("patient_nbr", as_index=False).agg(
        race=("race", "first"), gender=("gender", "first")
    )

    enc = df.rename(columns={
        "A1Cresult": "a1c_result", "change": "med_change", "diabetesMed": "diabetes_med",
    }).copy()
    enc["age_group"] = enc["age"]
    enc["age_lo"] = enc["age"].str.extract(r"\[(\d+)-")[0].astype("Int64")
    enc["readmitted_raw"] = enc["readmitted"]
    enc["readmitted_30d"] = (enc["readmitted"] == "<30").astype(int)
    enc["readmission_eligible"] = (
        ~enc["discharge_disposition_id"].isin(NON_READMITTABLE_DISPOSITIONS)
    ).astype(int)

    enc = enc[[
        "encounter_id", "patient_nbr", "age_group", "age_lo",
        "admission_type_id", "discharge_disposition_id", "admission_source_id",
        "time_in_hospital", "payer_code", "medical_specialty",
        "num_lab_procedures", "num_procedures", "num_medications",
        "number_outpatient", "number_emergency", "number_inpatient", "number_diagnoses",
        "max_glu_serum", "a1c_result", "med_change", "diabetes_med",
        "readmitted_raw", "readmitted_30d", "readmission_eligible",
    ]]

    dx = df[["encounter_id", "diag_1", "diag_2", "diag_3"]].melt(
        id_vars="encounter_id", var_name="position", value_name="icd9_code"
    )
    dx["position"] = dx["position"].str[-1].astype(int)
    dx = dx.dropna(subset=["icd9_code"])

    present_meds = [c for c in MEDICATION_COLUMNS if c in df.columns]
    absent = sorted(set(MEDICATION_COLUMNS) - set(present_meds))
    if absent:
        print(f"Note: medication columns not found in the file: {absent}")
    meds = df[["encounter_id"] + present_meds].melt(
        id_vars="encounter_id", var_name="drug", value_name="status"
    )
    meds = meds[meds["status"].notna() & (meds["status"] != "No")]

    return {"patients": patients, "encounters": enc, "diagnoses": dx, "medications": meds}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("--raw", type=Path, default=ROOT / "data" / "raw", help="folder with the raw CSV files")
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "readmissions.db", help="SQLite file to create")
    args = parser.parse_args()

    df = read_raw(args.raw)
    print(f"Read {len(df):,} rows from {args.raw / 'diabetic_data.csv'}")
    frames = build_frames(df)

    args.db.parent.mkdir(parents=True, exist_ok=True)
    if args.db.exists():
        args.db.unlink()

    conn = sqlite3.connect(args.db)
    try:
        conn.executescript((ROOT / "sql" / "schema.sql").read_text(encoding="utf-8"))

        frames["patients"].to_sql("patients", conn, if_exists="append", index=False)
        frames["encounters"].to_sql("encounters", conn, if_exists="append", index=False)
        frames["diagnoses"].to_sql("diagnoses", conn, if_exists="append", index=False)
        frames["medications"].to_sql("medications", conn, if_exists="append", index=False)

        mapping_path = args.raw / "IDs_mapping.csv"
        if mapping_path.exists():
            tables = parse_id_mapping(mapping_path)
            targets = {
                "admission_type_id": "admission_types",
                "discharge_disposition_id": "discharge_dispositions",
                "admission_source_id": "admission_sources",
            }
            for key, table in targets.items():
                conn.executemany(f"INSERT INTO {table} (id, description) VALUES (?, ?)", tables.get(key, []))
        else:
            print("IDs_mapping.csv not found; lookup tables left empty.")

        conn.executescript((ROOT / "sql" / "views.sql").read_text(encoding="utf-8"))
        conn.commit()

        print("\nRows loaded:")
        for table in ["patients", "encounters", "diagnoses", "medications",
                      "admission_types", "discharge_dispositions", "admission_sources"]:
            n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table:<24}{n:>10,}")

        eligible, rate = conn.execute(
            "SELECT COUNT(*), ROUND(100.0 * AVG(readmitted_30d), 2) FROM v_eligible_encounters"
        ).fetchone()
        print(f"\nReadmission-eligible encounters: {eligible:,} (30-day readmission rate {rate}%)")
        print(f"Database written to {args.db}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
