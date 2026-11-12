"""
Run every SQL file in sql/queries/ against the database, print the results,
and save each one as a CSV.

Usage:
    python run_queries.py                       # uses data/readmissions.db, writes results/
    python run_queries.py --db some.db --out some_folder
"""

import argparse
import sqlite3
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=ROOT / "data" / "readmissions.db")
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    if not args.db.exists():
        sys.exit(f"Database not found: {args.db}\nRun `python load_data.py` first.")

    args.out.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(args.db)
    try:
        for sql_path in sorted((ROOT / "sql" / "queries").glob("*.sql")):
            sql = sql_path.read_text(encoding="utf-8")
            title = next((line[3:].strip() for line in sql.splitlines() if line.startswith("-- Q")), sql_path.stem)
            df = pd.read_sql_query(sql, conn)
            print(f"\n=== {sql_path.name} ===\n{title}\n")
            print(df.to_string(index=False) if len(df) else "(no rows)")
            df.to_csv(args.out / f"{sql_path.stem}.csv", index=False)
    finally:
        conn.close()
    print(f"\nSaved CSVs to {args.out}")


if __name__ == "__main__":
    main()
