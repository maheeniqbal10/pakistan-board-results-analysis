# Code Walkthrough

A plain-language tour of every important file: what goes in, what comes out,
how it works, and why it was built that way. Each section ends with likely
interview questions and honest answers.

The pipeline in one line:

```
FBISE PDFs --collect.py--> data/raw/*.csv --clean.py--> results_tidy.csv
           --analysis.py + plots.py (via make_figures.py / the notebook)--> figures, findings
```

---

## `src/collect.py` — get the PDFs and pull out the aggregate tables

**Input.** The 12 FBISE PDF URLs listed in `SOURCES` at the top of the file.
**Output.** `data/raw/_downloads/*.pdf` (git-ignored), `data/raw/source_manifest.csv`,
`data/raw/fbise_gazette_all_areas.csv`, `data/raw/fbise_result_statistics_2013_2017.csv`.

**How it works, step by step**

1. `ensure_downloaded()` loops over `SOURCES`. A missing PDF is downloaded by
   `download()`, which streams it to a `.part` file. If the byte count differs
   from what the server promised (`Content-Length`), the file is thrown away.
   Only a complete file is renamed to `.pdf`. This was added after real
   downloads from the slow FBISE server came back corrupted.
2. It computes each PDF's **SHA-256 checksum** (a fingerprint of the file) and
   compares it with `source_manifest.csv`. A new file gets its fingerprint
   recorded. A changed fingerprint raises an error, because the numbers might
   no longer match what was checked by hand.
3. For each gazette, `find_all_areas_page()` searches the **first 15 pages** for
   the title "SALIENT FEATURES OF RESULT ALL AREAS" and returns that page
   number. `extract_gazette()` reads the text of that one page only. It also
   checks that the page header names the expected exam and year (e.g.
   "SSC-II ANNUAL EXAMINATION 2019"), so a wrong file cannot slip through.
4. `parse_all_areas_text()` reads the page line by line:
   - "REGULAR CANDIDATES" / "EX/PRIVATE CANDIDATES" set the current candidate type.
   - A regular expression (`DATA_LINE`) recognises a data line: a label, then
     exactly 13 whole numbers, then the pass % and the GPA.
   - `Male` / `Female` lines are **held back** in `pending`, because the gazette
     prints the group name *after* its gender rows ("SCIENCE Total : …").
     When the group-total line arrives, the held rows get that group name.
   - "Total :" closes a candidate type; "Grand Total :" is the whole board.
   - Any other label raises an error instead of being guessed.
5. `parse_statistics_pages()` reads the 3-page 2013–2017 summary. Each page
   also has a chart whose x-axis prints "2013 2014 2015 2016 2017", which
   looks exactly like a data row. So only lines **after** the table header
   ("Year …") are read. A test checks this.

**Why this way**
- *Only one page is read* because the same PDF contains student names and roll
  numbers on later pages (privacy rule, ADR-004).
- *Labels are kept exactly as printed* (`MALE`, `Pre-Med.`), so the raw CSV
  can be compared with the PDF by eye. Renaming happens in `clean.py`.
- *Text extraction instead of OCR* because these PDFs have a real text layer.
  A visual spot-check confirmed the text matches the printed page.

**Edge cases.** Gazettes omit a row when a cell has no candidates (e.g. 2018 SSC
private "Technical" has no female row). The parser simply has fewer rows; it
does not invent a zero row.

**Interview questions**
- *Why not scrape the board's result website?* That site shows individual
  students' results. This project uses only published aggregate tables (`PROJECT.md` §3).
- *How do you know the PDF parsing is right?* Four independent checks: printed
  totals must equal the sum of their parts; the recomputed pass % must match the
  printed %; the 2015–2017 totals match a separate FBISE summary PDF exactly; and
  one page was rendered as an image and compared by eye.
- *What if FBISE replaces a PDF?* The checksum changes, `collect.py` stops, and
  the new file has to be re-checked before it is used.
- *Why download the whole PDF if you only want one page?* FBISE publishes only
  the whole gazette. The file stays on the local machine (git-ignored), and only
  one page is ever parsed.

---

## `src/clean.py` — one validated, tidy table

**Input.** The two raw CSVs. **Output.** `data/processed/results_tidy.csv`
(290 rows).

**How it works**

1. `build_gazette_rows()` converts printed labels to standard ones through
   explicit dictionaries (`GROUPS`, `GENDERS`, `CANDIDATE_TYPES`).
   `standardise_label()` ignores case and spacing, but **raises an error for an
   unknown label** rather than guessing.
2. `to_counts()` turns count columns into nullable integers (`Int64`). Blank
   stays `<NA>` (missing); text such as `"8O"` raises an error.
3. `pass_rate()` = passed ÷ appeared × 100. If appeared is 0 or missing, the
   result is `NaN` (undefined), never 0. The value is not rounded.
4. `build_statistics_rows()` adds the overall Part-II % for **2013 and 2014
   only** (years without a gazette). Counts stay missing, and
   `pass_rate_method = "published_only"` records that.
5. `assessment` marks 2020 as `no_exam_promotion_policy`.
6. `validate()` checks everything and lists **all** problems at once:
   duplicates; negative counts; passed > appeared; appeared > enrolled;
   appeared ≠ enrolled − absent; pass rate outside 0–100; recomputed vs
   printed pass rate (tolerance 0.006 pp); and totals adding up (genders →
   group, groups → candidate type, types → grand total).
7. Rows are sorted in a fixed order, so re-running gives an identical file. CI
   checks this with `git diff --exit-code`.

**Why this way**
- *Totals kept as `All` rows*, so FBISE's own totals can be used and checked.
  The cost is that you must filter on all labels before summing, so
  `analysis.select()` requires all three.
- *Tolerance 0.006 pp*: FBISE prints 2 decimals, so a correct value can differ
  from the printed one by up to 0.005.

**Interview questions**
- *Why didn't you fill in HSSC 2019?* It isn't in any official source found, so
  it is missing. Estimating it would present a guess as data.
- *Zero vs missing?* An unprinted cell means no candidates, so no row is
  created. A missing year has no rows. 2013–14 counts are `NA`, not 0, because
  FBISE didn't publish them.
- *Why is "appeared" the denominator, not "enrolled"?* That is FBISE's printed
  definition, and the recomputation matches it on all 286 gazette rows.
  Enrolled includes absentees, who did not sit the exam.
- *What does "result later" do to the pass rate?* Those candidates stay in the
  denominator but are not counted as passed, as in the gazette. It matters in
  2020, when many private candidates were "result later".

---

## `src/analysis.py` — small summary functions

**Input.** The tidy table. **Output.** Small DataFrames, one per question.

| Function | Question | What it returns |
|---|---|---|
| `overall_trend` | Q1 | Overall and regular-only pass rate per level and year |
| `candidate_mix` | Q1 | Private candidates' share of those who appeared |
| `change_between` | Q1 | Change in **percentage points** between two years |
| `gender_gaps` | Q2 | Female − male pass rate per group/year, with a `comparable` flag |
| `overall_gender_gap` | Q2 | The gap with groups combined (sums counts first, then divides) |
| `group_pass_rates` | Q3 | Pass rate per group/year + pooled 2015–19 rate |
| `candidate_type_trend`, `compare_2020` | Q4 | 2020 vs lowest/highest exam-year rate |

**Key ideas**
- `MIN_APPEARED = 100`: cells with fewer than 100 candidates are flagged and
  left out of comparisons. The rule was fixed before results were seen.
- `pooled_pass_rate` = total passed ÷ total appeared. It weights each year by
  its size, unlike averaging the yearly percentages. A test shows the
  difference (55% vs 75%).

**Interview questions**
- *Why compare genders within groups?* Women and men choose groups very
  differently (e.g. about 6,000–7,200 women vs 1,040–1,440 men in regular
  Humanities each year, SSC and HSSC). An overall gap would mix gender with group choice.
- *Percentage points vs percent?* 60% → 65% is +5 percentage points, or +8.3%
  in relative terms. This project always reports pp.
- *Is a 5 pp gap "significant"?* No significance test was run, and none is
  claimed. These are complete board-wide counts, not a sample, so the question
  is whether a difference matters, not whether it is a sampling accident. The
  report gives sizes and how stable they are across years.

---

## `src/plots.py` and `scripts/make_figures.py` — the charts

**Input.** The DataFrames from `analysis.py`. **Output.** `figures/q1…q4*.png`,
plus `data/processed/summaries/*.csv` (the numbers behind each chart).

**Design choices**
- Pass-rate axes run **0–100%**, so differences are not exaggerated by a cut axis.
- **2020 is drawn as hollow markers in a grey band and never joined by a
  line** to exam years, because it is a different kind of number.
- Missing years break the line (the data is re-indexed to include the gap)
  instead of drawing across it.
- Q1 and Q4 are **line charts** (change over time). Q2 and Q3 are **dot-strip
  charts**: one row per group with one dot per year. This shows both the level
  and the year-to-year spread without a bar for every year.
- Colours: Regular is always blue, Private always orange. The palette was
  checked for colour-blind separation. Group identity is carried by the axis
  labels, not by colour.
- Every chart has a title, axis labels with units, and a source line.
- `make_figures.py` sets the "Agg" backend (files only). `plots.py` doesn't,
  so the notebook can show charts inline.

**Interview questions**
- *Why not a bar chart for subject groups?* Twenty-plus bars (six groups ×
  four years) would be crowded. Dots per year plus a pooled tick show the same
  information more clearly.
- *Were any charts made and not shown?* No. The four charts are the four
  pre-registered questions; there were no exploratory outcome charts.

---

## `notebooks/analysis.ipynb` — the narrative

Each question follows: question → definitions → method → chart → table →
interpretation → limitation. It imports from `src/`, so the notebook has no
cleaning code of its own. `find_project_root()` lets it run from `notebooks/`,
the repo root, or Kaggle. CI runs it top to bottom.

---

## `tests/`

| File | What it tests |
|---|---|
| `conftest.py` | Small **synthetic** tables (invented numbers, never used in results) |
| `test_collect.py` | Parsing: group label assigned back to gender rows, HSSC layout, chart axis ignored, errors on broken layouts |
| `test_clean.py` | Labels, denominator, NaN for zero denominator, missing stays missing, determinism, and that **each validation rule actually fires** |
| `test_analysis.py` | Pooled rate weighting, pp change, gap sign, small-cell flag, 2020 comparison |
| `test_dataset.py` | The **real** committed data: rebuilds the tidy table and compares; cross-source agreement for 2015–17; expected coverage (HSSC 2019 stays missing); privacy allow-list of column names |

*Why an allow-list for privacy?* A block-list of words like "roll" would
wrongly flag "enrolled". More importantly, a new column such as a student name
would slip past any block-list it doesn't happen to contain.

---

## `scripts/run_all.sh` and `.github/workflows/ci.yml`

`run_all.sh` runs clean → figures → ruff → pytest and stops at the first error
(`set -euo pipefail`). With `--download` it first re-downloads and re-extracts
(network needed). CI (GitHub Actions, Python 3.11) installs dependencies, runs
ruff and pytest, rebuilds the tidy table and fails if it differs from the
committed copy, and executes the notebook. **CI never touches the network for
data**, so a slow or offline FBISE website can't break it.

---

## General interview questions

- **Why only one board?** It was the only board whose official aggregate tables
  could be found and verified for several years. Narrowing the scope was better
  than mixing in unverified sources (ADR-001).
- **Does a rising pass rate mean better education?** Not on this evidence. Pass
  rates also change with papers, marking, grading rules and who sits the exam.
  Finding 1 shows how much the candidate mix alone matters.
- **Did COVID-19 or the promotion policy *cause* the 2020 jump?** The 2020
  numbers were *produced by* the policy (FBISE says so), so they are not exam
  results. The analysis shows how different they are. It does not estimate any
  effect on learning.
- **What would you do with more time?** Add other boards from official
  aggregate publications; add FBISE 2021 onward if official copies become
  available; add supplementary exams as a separate population.
