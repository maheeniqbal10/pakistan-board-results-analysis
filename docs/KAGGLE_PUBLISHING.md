# Publishing the notebook on Kaggle

This must be done from the owner's own Kaggle account. Nothing has been
published yet.

## 1. Before you start

- Make sure the GitHub repository is public and up to date.
- The Kaggle dataset below contains the same aggregate CSVs as the repository;
  publishing them with attribution to FBISE was approved in `DECISIONS.md`
  ADR-005. Never upload the gazette PDFs.

## 2. Create a Kaggle dataset with the code and data

The notebook imports the project's `src/` modules and reads
`data/processed/results_tidy.csv`, so both must be attached.

1. Make a zip containing only:
   ```
   src/                       (all .py files)
   data/processed/results_tidy.csv
   data/SOURCES.md
   LICENSE
   ```
   For example, from the repository root:
   `zip -r kaggle_upload.zip src data/processed/results_tidy.csv data/SOURCES.md LICENSE`
   (do **not** include `data/raw/_downloads/`).
2. On Kaggle: **Datasets → New Dataset**, upload the zip, and name it, e.g.,
   `fbise-board-results-aggregate`.
3. In the dataset description, state: aggregate statistics only; source FBISE
   (link `data/SOURCES.md`); © FBISE, no data licence published; the code is
   MIT-licensed.
4. Choose a licence option that does not claim more rights than you have (e.g.
   "Other (specified in description)").

## 3. Create the notebook

1. **Code → New Notebook → File → Import Notebook**, and upload
   `notebooks/analysis.ipynb`.
2. **Add Input** → your dataset from step 2. It appears under
   `/kaggle/input/<dataset-name>/`.
3. Run all cells. The first code cell searches `/kaggle/input/*` for
   `src/analysis.py`, so no path edits should be needed. If Kaggle unpacked the
   zip into a sub-folder, the search still finds it as long as `src/` and
   `data/` sit side by side.
4. Check that all four charts appear and that the outputs match
   `docs/findings.md`.
5. Set the title, e.g. "What FBISE's published exam results show, 2013–2020",
   then **Save Version → Save & Run All** and make it public.

## 4. After publishing

- Replace "Kaggle notebook: not yet published" in `README.md` with the real link.
- Add the link to `CHANGELOG.md`.
