# CHANGELOG.md

Follows [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Data collection from 12 official FBISE PDFs (11 SSC-II/HSSC-II annual
  result gazettes, 2015–2020, plus the 2013–2017 result statistics summary),
  with download size checks and SHA-256 manifest (`src/collect.py`).
- Extraction of the board-wide "Salient Features — All Areas" table only;
  student-level pages are never parsed and PDFs are not committed.
- Cleaning and validation into one tidy table (`src/clean.py`): label
  standardisation, recomputed pass rates checked against printed values,
  totals reconciliation, 2020 flagged as a no-exam year.
- Research questions fixed before analysis (`DECISIONS.md` ADR-002).
- Summary functions (`src/analysis.py`), chart style (`src/plots.py`), four
  figures and their summary tables (`scripts/make_figures.py`).
- Analysis notebook (`notebooks/analysis.ipynb`), findings
  (`docs/findings.md`), code walkthrough, Kaggle publishing guide.
- 45 tests (parsing, cleaning, analysis, committed-data integrity and a privacy
  column allow-list); CI runs ruff, pytest, a reproducibility check and the
  notebook.

### Not done yet
- Kaggle notebook not published (needs the owner's account).
- CI has not run on GitHub yet (repository not pushed).

## [0.1.0] — Scaffold
### Added
- Project specification documents, folder structure, MIT License
