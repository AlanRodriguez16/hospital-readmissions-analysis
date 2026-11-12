"""
Generate a SYNTHETIC stand-in for the UCI diabetes readmissions files, for testing the
loader and SQL queries without downloading anything.

THE DATA THIS PRODUCES IS RANDOM. Any "finding" from it is meaningless. Never report
results from the fixture. It only checks that the code runs.

Usage:
    python tests/make_synthetic_fixture.py --out data/synthetic
    python load_data.py --raw data/synthetic --db data/synthetic/test.db
"""

import argparse
import csv
from pathlib import Path

import numpy as np

MEDS = [
    "metformin", "repaglinide", "nateglinide", "chlorpropamide", "glimepiride",
    "acetohexamide", "glipizide", "glyburide", "tolbutamide", "pioglitazone",
    "rosiglitazone", "acarbose", "miglitol", "troglitazone", "tolazamide",
    "examide", "citoglipton", "insulin", "glyburide-metformin",
    "glipizide-metformin", "glimepiride-pioglitazone", "metformin-rosiglitazone",
    "metformin-pioglitazone",
]
HEADER = (
    ["encounter_id", "patient_nbr", "race", "gender", "age", "weight",
     "admission_type_id", "discharge_disposition_id", "admission_source_id",
     "time_in_hospital", "payer_code", "medical_specialty",
     "num_lab_procedures", "num_procedures", "num_medications",
     "number_outpatient", "number_emergency", "number_inpatient",
     "diag_1", "diag_2", "diag_3", "number_diagnoses",
     "max_glu_serum", "A1Cresult"] + MEDS + ["change", "diabetesMed", "readmitted"]
)
AGES = [f"[{a}-{a + 10})" for a in range(0, 100, 10)]
DX = ["250.83", "250", "414", "428", "427", "486", "585", "V57", "E909", "786",
      "401", "715", "574", "820", "157", "599", "788", "276", "682", "560"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("data/synthetic"))
    parser.add_argument("--rows", type=int, default=6000)
    args = parser.parse_args()

    rng = np.random.default_rng(42)
    n = args.rows
    args.out.mkdir(parents=True, exist_ok=True)

    def pick(values, p=None):
        return values[rng.choice(len(values), p=p)]

    with open(args.out / "diabetic_data.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        for i in range(n):
            row = [
                2_000_000 + i,                                   # encounter_id
                1_000_000 + int(rng.integers(0, n * 7 // 10)),   # patient_nbr (repeats)
                pick(["Caucasian", "AfricanAmerican", "Hispanic", "Asian", "Other", "?"],
                     [.7, .18, .02, .01, .01, .08]),
                pick(["Female", "Male"]),
                pick(AGES, [.005, .005, .02, .05, .1, .17, .22, .25, .15, .03]),
                "?" if rng.random() < .95 else "[75-100)",
                int(rng.choice([1, 2, 3, 6], p=[.53, .18, .19, .1])),
                int(rng.choice([1, 2, 3, 6, 11, 13, 14, 22], p=[.55, .02, .1, .12, .03, .01, .01, .16])),
                int(rng.choice([1, 4, 7, 17], p=[.28, .06, .56, .1])),
                int(rng.integers(1, 15)),
                pick(["MC", "HM", "SP", "BC", "MD", "?"], [.3, .06, .04, .04, .03, .53]),
                pick(["?", "InternalMedicine", "Cardiology", "Emergency/Trauma",
                      "Family/GeneralPractice", "Surgery-General", "Orthopedics", "Nephrology"],
                     [.49, .14, .05, .07, .07, .03, .01, .14]),
                int(rng.integers(1, 100)),
                int(rng.integers(0, 7)),
                int(rng.integers(1, 40)),
                int(rng.poisson(.4)),
                int(rng.poisson(.2)),
                int(rng.poisson(.6)),
                pick(DX),
                "?" if rng.random() < .01 else pick(DX),
                "?" if rng.random() < .1 else pick(DX),
                int(rng.integers(1, 17)),
                pick(["None", "Norm", ">200", ">300"], [.95, .03, .01, .01]),
                pick(["None", "Norm", ">7", ">8"], [.8, .05, .05, .1]),
            ]
            row += [pick(["No", "Steady", "Up", "Down"], [.8, .15, .025, .025]) for _ in MEDS]
            row += [pick(["No", "Ch"]), pick(["Yes", "No"], [.77, .23]),
                    pick(["NO", ">30", "<30"], [.54, .35, .11])]
            w.writerow(row)

    with open(args.out / "IDs_mapping.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows([["admission_type_id", "description"], [1, "Emergency"], [2, "Urgent"],
                     [3, "Elective"], [6, "NULL"], [], ["discharge_disposition_id", "description"],
                     [1, "Discharged to home"], [2, "Discharged/transferred to another short term hospital"],
                     [3, "Discharged/transferred to SNF"], [6, "Discharged/transferred to home with home health service"],
                     [11, "Expired"], [13, "Hospice / home"], [14, "Hospice / medical facility"],
                     [22, "Discharged/transferred to another rehab fac including rehab units of a hospital"],
                     [], ["admission_source_id", "description"], [1, " Physician Referral"],
                     [4, "Transfer from a hospital"], [7, " Emergency Room"], [17, "NULL"]])

    print(f"Wrote synthetic fixture ({n:,} rows) to {args.out}. RANDOM DATA, for testing only.")


if __name__ == "__main__":
    main()
