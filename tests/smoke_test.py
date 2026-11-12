"""
End-to-end check that the pipeline runs: generate synthetic data -> load -> run all queries.

    python tests/smoke_test.py

This verifies the CODE works. It says nothing about real readmission patterns,
because the fixture data is random.
"""

import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROWS = 2000


def run(*args) -> None:
    subprocess.run([sys.executable, *[str(a) for a in args]], check=True, cwd=ROOT)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        run(ROOT / "tests" / "make_synthetic_fixture.py", "--out", tmp, "--rows", ROWS)
        run(ROOT / "load_data.py", "--raw", tmp, "--db", tmp / "test.db")
        run(ROOT / "run_queries.py", "--db", tmp / "test.db", "--out", tmp / "results")

        conn = sqlite3.connect(tmp / "test.db")
        try:
            n_encounters = conn.execute("SELECT COUNT(*) FROM encounters").fetchone()[0]
            fk_problems = conn.execute("PRAGMA foreign_key_check").fetchall()
        finally:
            conn.close()

        n_queries = len(list((ROOT / "sql" / "queries").glob("*.sql")))
        n_outputs = len(list((tmp / "results").glob("*.csv")))

        assert n_encounters == ROWS, f"expected {ROWS} encounters, got {n_encounters}"
        assert not fk_problems, f"foreign key violations: {fk_problems[:3]}"
        assert n_outputs == n_queries, f"{n_queries} queries but {n_outputs} result files"

    print(f"\nSMOKE TEST PASSED: {ROWS} synthetic encounters loaded, {n_queries} queries ran.")


if __name__ == "__main__":
    main()
