# Getting the data

The raw data is not stored in this repo (it is ~19 MB, and the source site is the right place to get it).

1. Open the dataset page: https://archive.ics.uci.edu/dataset/296/diabetes-130-us-hospitals-for-years-1999-2008
2. Click **Download** and unzip the file.
3. Copy these two files into `data/raw/` (create the folder if needed):
   - `diabetic_data.csv`  (required)
   - `IDs_mapping.csv`    (optional; fills in the lookup tables for admission type, discharge disposition, and admission source)
4. From the repo root, run `python load_data.py`.

Check the dataset page for the current license and citation requirements before you redistribute anything derived from it.

## Folders created later

- `data/readmissions.db`: the SQLite database built by `load_data.py` (not committed)
- `data/synthetic/`: optional random test data from `tests/make_synthetic_fixture.py` (not committed)
