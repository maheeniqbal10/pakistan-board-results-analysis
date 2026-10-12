# Pakistan Board Exam Results — What the Numbers Actually Show

[![CI](https://github.com/maheeniqbal10/pakistan-board-results-analysis/actions/workflows/ci.yml/badge.svg)](https://github.com/maheeniqbal10/pakistan-board-results-analysis/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A descriptive analysis of **public, aggregate** results published by the
Federal Board of Intermediate and Secondary Education (**FBISE**, Islamabad)
for its final-year **SSC-II (Matric)** and **HSSC-II (Intermediate)** annual
examinations, 2013–2020: how pass rates changed over time, and how they differ by
gender, subject group and candidate type.

**Kaggle notebook:** not yet published. The notebook is in
[`notebooks/analysis.ipynb`](notebooks/analysis.ipynb).

![Overall pass rate by year](figures/q1_overall_trend.png)

---

## The questions

Fixed before any result was plotted ([`DECISIONS.md`](DECISIONS.md), ADR-002):

1. **Trend:** How did FBISE's reported overall pass rate change from 2013 to 2019?
2. **Gender:** Within the same subject group, how do female and male pass rates
   differ, and is the gap stable across years?
3. **Subject groups:** How do pass rates differ across subject groups?
4. **2020:** How did the 2020 results, produced without an exam under the
   COVID-19 promotion policy, compare with the exam years?

A comparison *between* boards was planned but dropped: only FBISE data could
be verified from official sources.

## The data

| | SSC-II (Matric) | HSSC-II (Intermediate) |
|---|---|---|
| Full breakdown (regular/private × group × gender, with counts) | 2015–2020 | 2015–2018, 2020 |
| Overall pass % only | 2013–2014 | 2013–2014 |
| Missing | — | 2019 (no gazette found) |

- **Source:** 12 official FBISE PDFs from fbise.edu.pk: 11 annual result
  gazettes and one 2013–2017 summary. Each is listed with URL, access date,
  pages used and checksum in [`data/SOURCES.md`](data/SOURCES.md).
- **One board only.** The results describe FBISE candidates, not Pakistan as a
  whole.

### Privacy

Only aggregate tables are used: counts of candidates who enrolled, appeared and
passed. The gazette PDFs also contain student names and roll numbers on other
pages. Those pages are never read, and the PDFs are not stored in this
repository ([ADR-004](DECISIONS.md)). No individual student data was
collected, stored or published.

## Method

1. **Collect** — [`src/collect.py`](src/collect.py) downloads the PDFs, checks
   their SHA-256, and extracts only the "Salient Features of Result — All Areas"
   table from each gazette.
2. **Clean and validate** — [`src/clean.py`](src/clean.py) standardises labels
   and recomputes every pass rate (passed ÷ appeared × 100). It checks that the
   result matches FBISE's printed figure and that all printed totals add up. Any
   failure stops the pipeline.
3. **Cross-check** — for 2015–2017, the gazette totals match FBISE's separate
   summary PDF exactly.
4. **Analyse** — [`src/analysis.py`](src/analysis.py) and
   [`src/plots.py`](src/plots.py); one chart per question, then an
   interpretation and its limitations in the notebook.

Every cleaning rule is logged in [`DECISIONS.md`](DECISIONS.md) (ADR-003).

## Findings

Details, exact numbers and caveats: [`docs/findings.md`](docs/findings.md).

1. **The overall SSC-II pass rate rose about 6–7 pp (2013/2015 → 2019), but the
   regular-candidate rate barely moved** (91.10% → 91.87%). Over the same years
   the share of private candidates fell from 27% to 17% and their pass rate
   rose. HSSC-II rose 5.11 pp from 2013 to 2018.
2. **Female candidates had higher reported pass rates than male candidates in
   all 30 comparable group-year cells.** The gap was small in Science,
   Pre-Medical and Pre-Engineering (about 2–6 pp) and large in Humanities,
   Commerce and General Science (about 14–31 pp).
   ![Gender gap](figures/q2_gender_gap.png)
3. **Science-track groups had the highest reported pass rates**: SSC Science
   92.6% and HSSC Pre-Medical 91.8% pooled, against 65–74% for HSSC Humanities,
   General Science, Commerce and Medical Technology.
   ![Subject groups](figures/q3_group_pass_rates.png)
4. **The 2020 no-exam results were above every exam year**, by +5.8 pp (SSC
   regular) up to +22.7 pp (HSSC private). Only about 1% of candidates were
   recorded as failing, against 16–26% in exam years.
   ![2020 vs exam years](figures/q4_2020_vs_exam_years.png)

## Limitations

- **One board, a particular population.** FBISE candidates come from
  federal-area and FBISE-affiliated institutions across Pakistan and overseas,
  plus private candidates. They are not representative of the provincial boards.
- **Short and incomplete.** Full breakdowns exist only for 2015–2019, and HSSC
  2019 is missing. Gaps are shown as gaps, never filled in.
- **Pass rates are not learning.** Papers, marking and grading rules can change
  between years without appearing in the gazettes.
- **2020 is not comparable.** Results were produced by policy, not exams, and
  many private candidates' results were still pending ("result later").
- **Descriptive only.** Differences between genders, groups or years are not
  explained by this data, and no causal claims are made.
- **Licensing.** FBISE publishes no data licence. Only small extracted
  aggregate tables are included, with attribution ([ADR-005](DECISIONS.md)).

## Run it yourself

Requires Python 3.11+.

```bash
git clone https://github.com/maheeniqbal10/pakistan-board-results-analysis.git
cd pakistan-board-results-analysis
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

bash scripts/run_all.sh             # clean -> figures -> tests (no network needed)
bash scripts/run_all.sh --download  # also re-download the PDFs (~95 MB) and re-extract
jupyter notebook notebooks/analysis.ipynb
```

The committed CSVs in `data/raw/` let everything after extraction run offline.
`--download` rebuilds those CSVs from the official PDFs. If FBISE has changed a
file, the stored checksum no longer matches and the pipeline stops rather than
silently using a different document.

## Repository guide

| Path | What it is |
|---|---|
| [`PROJECT.md`](PROJECT.md) | Project specification |
| [`DECISIONS.md`](DECISIONS.md) | Sources, research questions, cleaning and privacy decisions |
| [`data/SOURCES.md`](data/SOURCES.md) | Every source, URL, page and checksum |
| `data/raw/` | Extracted aggregate tables (labels as printed) and the source manifest |
| `data/processed/` | The tidy table and the summary tables behind each chart |
| `src/` | `collect.py` → `clean.py` → `analysis.py` / `plots.py` |
| `tests/` | Tests for parsing, cleaning, analysis and the committed data |
| [`docs/findings.md`](docs/findings.md) | Findings with numbers and caveats |
| [`docs/CODE_WALKTHROUGH.md`](docs/CODE_WALKTHROUGH.md) | Plain-language explanation of every file |

Dataset: https://www.kaggle.com/datasets/maheeniqbal10/pakistan-board-results-analysis
Notebook: https://www.kaggle.com/code/maheeniqbal10/notebook1d6b6b19fb

## License

Code: MIT — see [`LICENSE`](LICENSE). Data: © FBISE; see
[`data/SOURCES.md`](data/SOURCES.md).
