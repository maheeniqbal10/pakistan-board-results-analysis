# ARCHITECTURE.md — pakistan-board-results-analysis

## Data flow

```
Official FBISE publications (statistics PDF + result gazette PDFs)
        |   documented in data/SOURCES.md
        v
src/collect.py  -> data/raw/_downloads/   (original PDFs, untouched, not committed)
                -> data/raw/*.csv          (aggregate tables only, committed)
        |
        v
src/clean.py    -> data/processed/results_tidy.csv
        |   one row = (year, board, level, part, group, gender, candidate_type)
        v
src/analysis.py (small summary helpers) + src/plots.py
        |
        +--> scripts/make_figures.py -> figures/*.png --> README
        +--> notebooks/analysis.ipynb (the narrative)
        +--> docs/findings.md
```

## Why this shape
- **Raw files stay untouched** so every number can be re-checked against the source.
- **Only aggregate tables are committed.** The full gazette PDFs also contain
  student names and roll numbers on later pages, so only one aggregate page is
  parsed and the PDFs are re-downloaded on demand, never committed
  (`DECISIONS.md` ADR-004).
- **Cleaning lives in `src/`, not only in the notebook**, so it can be tested
  and re-run, and the notebook stays a readable story.
- **One tidy table** makes every question a simple filter + group-by + plot.

## Components
| File | Does | Does not |
|---|---|---|
| `src/collect.py` | Download source PDFs, extract aggregate tables to `data/raw/` | Clean or analyze |
| `src/clean.py` | Validate and standardise into the tidy table | Plot |
| `src/analysis.py` | Load the tidy table; small, tested summary helpers (gaps, changes, pooled rates) | Write files or plot |
| `src/plots.py` | Consistent chart style, one function per chart type | Compute findings |
| `scripts/make_figures.py` | Regenerate every figure and the summary tables in `data/processed/summaries/` | Clean data |
| `notebooks/analysis.ipynb` | Tell the question → chart → finding story | Hide cleaning steps |
