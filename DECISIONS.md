# DECISIONS.md — Decision Records

Format: Context / Decision / Consequences. Records are added as real decisions
are made; later changes are recorded as new entries rather than silent edits.

---

## ADR-001: Data sources

**Status:** Accepted (2026-10-10)

**Context.** Aggregate board results are scattered across datasets, PDFs and
news reports. Individual-level data is off-limits (`PROJECT.md` §3). The
budget is $0.

**What was searched** (in the priority order of `PROJECT.md` §3):

| Searched for | Found | Used? | Why |
|---|---|---|---|
| Compiled public datasets (Kaggle, GitHub) | Kaggle "BISE Faisalabad Exam Result Gazettes" | **No** | Its own description says it contains student names, roll numbers and marks. Excluded on privacy grounds without downloading. |
| | A GitHub dashboard compiling 15 boards' gazettes, 2024–2026 | **No** | No licence (redistribution not permitted by default), created 2026-10-09, authorship and extraction method could not be verified. |
| Pakistan Education Statistics (Pakistan Institute of Education) | PES 2021-22 report (PDF) | **No** | A keyword scan for examination-result tables found none before the PDF parser hit a malformed page; the report focuses on enrolment and facilities. Not pursued further. |
| Official board publications | **FBISE "Result Statistics 2013–2017"** (3-page summary PDF) | **Yes** | Official, aggregate only. |
| | **FBISE SSC-II and HSSC-II annual result gazettes**, 2015–2020 | **Yes** | Official; the first pages are board-wide aggregate tables. See ADR-004 for how the student-level pages in the same PDF are handled. |
| | HSSC-II annual gazette 2019 | Not found | Not on fbise.edu.pk under any URL pattern tried; the 2019 declaration page only shows images. Left missing. |
| | FBISE gazettes 2021 onwards | Only third-party mirrors (news sites) | Not hosted by FBISE; integrity cannot be checked against an official copy. Excluded from this version (possible future extension). |
| | BISE Lahore "preamble" (statistics) PDFs | 404 Not Found | — |
| News reports | Many | Not used | Official primary sources were available for every year analysed. |

**Decision.** Use only the 12 FBISE PDFs listed in `data/SOURCES.md` and
`src/collect.py`. All are downloaded from `fbise.edu.pk`; their SHA-256
checksums are recorded in `data/raw/source_manifest.csv`.

**Consequences.**
- The analysis covers **one board (FBISE, the Federal Board)**. It says
  nothing about Punjab, Sindh, KP or Balochistan boards and is not nationally
  representative.
- Years: SSC-II 2013–2020; HSSC-II 2013–2018 and 2020 (2019 missing).
  2013–2014 have only an overall pass percentage (no counts or breakdowns).
- FBISE candidates are a particular population. The gazettes report results
  for FBISE-affiliated institutions in the federal area, all four provinces,
  Gilgit-Baltistan, AJK and overseas, plus private candidates; they are not a
  sample of Pakistani students in general.

---

## ADR-002: Research questions (fixed before outcome charts)

**Status:** Accepted (2026-10-10) — written after extraction and validation,
before any outcome chart or summary was produced.

**Disclosure.** Checking the extraction meant reading some printed totals
(e.g. that the 2015–2017 gazette pass rates equal the summary PDF's). No
comparison between years, genders, groups or candidate types had been
computed or plotted. The questions below are the `PROJECT.md` candidates,
kept or dropped **only on coverage**.

**Coverage that drove the choice**

| | SSC-II (Matric) | HSSC-II (Intermediate) |
|---|---|---|
| Overall pass % only | 2013, 2014 | 2013, 2014 |
| Full breakdown (candidate type × group × gender, with counts) | 2015–2020 | 2015–2018, 2020 |
| Missing | — | 2019 |
| Subject groups | Science, Humanities (+ "Technical", 2018 only, 2 candidates) | Humanities, Pre-Medical, Pre-Engineering, General Science, Commerce, Medical Technology |
| No-exam year | 2020 | 2020 |

**Rules shared by all questions**
- Metric: **pass rate = passed ÷ appeared × 100**, FBISE's own definition
  (appeared = enrolled − absent; candidates whose result was declared later
  remain in the denominator, as in the gazette).
- Differences are reported in **percentage points (pp)**, never as relative %.
- **Minimum cell size:** a cell is used in a comparison only if at least
  **100 candidates appeared** in it. Smaller cells are listed, not compared.
  (Set before looking at results; it removes e.g. SSC "Technical".)
- 2020 results were produced under a promotion policy, not an examination
  (stated on page 1 of the HSSC-II 2020 gazette). 2020 is **never pooled with
  exam years** and is only discussed in Q4.
- Missing years are shown as gaps, never interpolated.

**Q1 — Trend.** How did FBISE's reported overall Part-II pass rate change
from 2013 to 2019, for SSC and HSSC?
- Population: all candidates (regular + private), annual exam.
- Comparison: year to year; first vs last exam year, in pp.
- Comparability: the overall rate mixes regular and private candidates, whose
  share can change; the regular-only rate (2015–2019) is shown alongside as a
  check. 2013–2014 come from the summary PDF (published % only).
- Output: line chart `figures/q1_overall_trend.png`.

**Q2 — Gender.** Within the same candidate type and subject group, how do
reported female and male pass rates differ, and is the gap similar across
2015–2019?
- Population: regular candidates (primary); private candidates in a table.
- Metric: female pass rate − male pass rate (pp), per group and year.
- Why within groups: men and women are distributed very differently across
  groups, so an overall gap mixes gender with group choice. The overall gap is
  also reported, for transparency.
- Output: `figures/q2_gender_gap.png` (gap by year, one line per group,
  panels for SSC and HSSC).

**Q3 — Subject groups.** How do reported pass rates differ across subject
groups among regular candidates, 2015–2019?
- Metric: pass rate per group per year, plus the pooled 2015–2019 rate
  (total passed ÷ total appeared across those years).
- Comparability: groups have different papers and attract different
  students; a lower rate does not mean a group is "harder".
- Output: `figures/q3_group_pass_rates.png` (each year as a dot, pooled rate
  marked).

**Q4 — 2020 no-exam year.** How did reported 2020 results, produced under
the promotion policy, compare with the 2015–2019 exam years?
- Metric: pass rate by level and candidate type; 2020 vs the 2015–2019 range.
- Descriptive only: the comparison shows how different the reported numbers
  are. It does not estimate any "effect" of COVID-19 or the policy on
  learning.
- Output: `figures/q4_2020_vs_exam_years.png`.

**Dropped or narrowed candidate questions**
- **Board comparison** (`PROJECT.md` Q2): dropped. Only FBISE data was
  verified. The gazettes also show results by region (Punjab, Sindh, …), but
  these are FBISE-affiliated institutions in those regions, not the provincial
  boards, so they cannot answer the board question and are not used.
- **Average marks**: not published in the gazettes (only a GPA whose
  computation is not documented), so not used.

---

## ADR-003: Cleaning decisions

**Status:** Accepted (2026-10-10)

1. **Raw labels are preserved** in `data/raw/fbise_gazette_all_areas.csv`
   exactly as printed (`MALE`/`Male`, `Pre-Med.` …). Standardisation happens
   only in `src/clean.py` via explicit maps; an unknown label is an error.
2. **Label mapping:** `Pre-Med.` → Pre-Medical, `Pre-Engg.` → Pre-Engineering,
   `Sc. General` → General Science, `Med. Tech.` → Medical Technology,
   `EX/PRIVATE CANDIDATES` → Private. No two printed groups are merged.
3. **Totals kept as rows** labelled `All`, so published totals can be used
   directly and checked against the sum of their parts.
4. **Unprinted cells are not created.** Where a gender row is absent (e.g.
   2018 SSC private "Technical" has no female row) the printed totals equal the
   sum of printed rows, i.e. the cell had no candidates. No zero row is
   invented; a pass rate for zero candidates would be undefined anyway.
5. **Missing stays missing.** 2013–2014 rows have counts as empty (`NA`), and
   `pass_rate_method = published_only`; they are never filled with zeros.
6. **Pass rate is recomputed** from counts and compared with the printed
   value. Printed values are rounded to 2 dp, so the tolerance is 0.006 pp.
   All 286 gazette rows agree.
7. **Integrity checks** (all must pass or cleaning stops): no duplicate keys;
   counts non-negative integers; passed ≤ appeared ≤ enrolled; appeared =
   enrolled − absent; gender rows sum to group totals, groups to candidate-type
   totals, candidate types to the grand total.
8. **Summary-PDF rows are used only for years without a gazette** (2013–2014).
   For 2015–2017 both sources exist and agree exactly (tested), so the gazette
   is used to avoid duplicates.
9. **The summary PDF's appeared/passed counts are not used.** They do not
   match the Part-II pass rates (e.g. HSSC 2013: 61,880 ÷ 102,080 = 60.6%,
   neither Part I's 48.5% nor Part II's 72.3%), which suggests they combine
   Part I and Part II. They are stored with `part = I+II` and left out.
10. **Supplementary examinations are excluded**: their candidates are mostly
    repeaters, a different population from the annual exam.

**Consequences.** Every number in the tidy table traces to one PDF page
(`source_id`, `source_page`). Comparisons across years assume FBISE's pass
definition did not change between 2015 and 2019; no change was found in the
gazette layouts, but grading policy changes outside the gazettes cannot be
ruled out.

---

## ADR-004: Using gazettes that also contain student-level pages

**Status:** Accepted (2026-10-10) — approved by the project owner

**Context.** FBISE publishes each result gazette as a single PDF (850–1,250
pages). The first ~11 pages hold aggregate tables; from about page 12 onward the PDF
lists position holders and institution results, which include student names
and roll numbers. FBISE publishes no aggregate-only version for 2015–2020.

**Decision.**
- The aggregate tables sit on separate pages from the individual records,
  so they can be separated reliably (`PROJECT.md` §3 allows extracting only
  the aggregate tables in that case).
- `src/collect.py` opens only the page titled "SALIENT FEATURES OF RESULT
  ALL AREAS" (found by searching the first 15 pages). No other page is
  parsed, printed or saved.
- The PDFs are stored in `data/raw/_downloads/`, which is git-ignored, so the
  repository never contains or redistributes them.
- A test (`tests/test_dataset.py`) enforces an allow-list of aggregate-only
  column names on every committed CSV.

**Consequences.** Running `src/collect.py` downloads the full PDFs to the local
machine, as any visitor to fbise.edu.pk would. The owner may delete
`data/raw/_downloads/` after extraction; `python -m src.clean` and everything
downstream only need the committed CSVs.

---

## ADR-005: Redistribution of extracted figures

**Status:** Accepted (2026-10-10) — approved by the project owner

**Context.** fbise.edu.pk carries "© FBISE. All rights reserved" and no
data licence. The repository commits small CSVs of figures extracted from
FBISE publications (not the PDFs).

**Decision.** Commit only the extracted aggregate figures, with full
attribution and links to the originals in `data/SOURCES.md`; never commit the
PDFs. Factual statistics are generally not protected the way documents are;
this is a judgement, not legal advice.

**Consequences.** If the owner prefers not to redistribute the figures, the
CSVs can be removed from git; `python -m src.collect` regenerates them from
the official PDFs.
