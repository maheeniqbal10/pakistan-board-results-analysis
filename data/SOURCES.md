# Data Sources

Aggregate statistics only. Every number in `data/processed/` traces to one of
the sources below via the `source_id` and `source_page` columns.

**Publisher of all sources:** Federal Board of Intermediate and Secondary
Education (FBISE), Islamabad. **All accessed:** 2026-10-10.
**Integrity:** SHA-256 and byte size of each file are recorded in
[`raw/source_manifest.csv`](raw/source_manifest.csv); `src/collect.py`
refuses to extract from a file whose checksum has changed.

## 1. FBISE "Result Statistics 2013–2017"

| Field | Value |
|---|---|
| Title | "Percentage of Results 2013–2017" / "HSSC Result Statistics" / "SSC Result Statistics" (3 pages) |
| URL | <https://www.fbise.edu.pk/news%20update%20notification/RESULT%20STATISTICS.pdf> |
| Published | File created 2017-08-23 (PDF metadata); no printed date |
| Covers | FBISE, 2013–2017; pass % for SSC-I, SSC-II, HSSC-I, HSSC-II (p.1); appeared & passed counts for HSSC (p.2) and SSC (p.3) |
| Extracted | All values on the 3 pages → `raw/fbise_result_statistics_2013_2017.csv` |
| Used in analysis | **Only the Part-II pass % for 2013 and 2014** (years with no gazette) |
| Units / definitions | Pass % (2 dp or fewer); counts of candidates. The counts are not labelled by part and appear to combine Part I and Part II (see `DECISIONS.md` ADR-003, item 9), so they are not used |
| Method | Programmatic (`pdfplumber` text layer), `src/collect.py::parse_statistics_pages` |
| Verification | For 2015–2017 its Part-II pass % equals the gazette totals exactly for both SSC and HSSC (`tests/test_dataset.py`) |
| Limitations | No breakdown by group, gender or candidate type; no definition text |

## 2. FBISE result gazettes, SSC-II and HSSC-II 1st annual examinations

Each gazette is one large PDF. Only the table titled **"Salient Features of
Result — All Areas"** is extracted; it covers the whole board. The same PDF
also contains position-holder lists and institution results with student
names and roll numbers. Those pages are never parsed, and the PDFs are not
committed (see `DECISIONS.md` ADR-004).

| source_id | Exam | URL | Pages | File created (PDF metadata) | Table page |
|---|---|---|---|---|---|
| `fbise_ssc2_2015` | SSC-II Annual 2015 | <https://www.fbise.edu.pk/notifications/ssc/SSC-II-A-RESULT%202015.pdf> | 1,115 | 2015-07-03 | 3 |
| `fbise_ssc2_2016` | SSC-II Annual 2016 | <https://www.fbise.edu.pk/notifications/ssc/SSC-II-A-RESULT%202016.pdf> | 1,165 | 2016-07-11 | 3 |
| `fbise_ssc2_2017` | SSC-II Annual 2017 | <https://www.fbise.edu.pk/notifications/ssc/SSC-II-A-RESULT%202017.pdf> | 1,193 | 2017-06-20 | 3 |
| `fbise_ssc2_2018` | SSC-II Annual 2018 | <https://www.fbise.edu.pk/notifications/ssc/Result%20Gazette%20SSC-II%20A%202018.pdf> | 1,258 | 2018-07-05 | 3 |
| `fbise_ssc2_2019` | SSC-II Annual 2019 | <https://www.fbise.edu.pk/notifications/ssc/Result%20Gazette%20SSC%20II%202019.pdf> | 1,233 | 2019-07-01 | 3 |
| `fbise_ssc2_2020` | SSC-II Annual 2020 | <https://www.fbise.edu.pk/notifications/ssc/Result%20Gazette%20SSC%20A%202020.pdf> | 1,159 | 2020-07-18 | 3 |
| `fbise_hssc2_2015` | HSSC-II Annual 2015 | <https://www.fbise.edu.pk/notifications/hssc/Result%20gazette%20Hssc-II%202015%20A.pdf> | 814 | 2015-08-12 | 3 |
| `fbise_hssc2_2016` | HSSC-II Annual 2016 | <https://www.fbise.edu.pk/notifications/hssc/Result%20gazette%20Hssc-II%202016%20A.pdf> | 836 | 2016-08-16 | 3 |
| `fbise_hssc2_2017` | HSSC-II Annual 2017 | <https://www.fbise.edu.pk/notifications/hssc/Result%20gazette%20Hssc-II%202017%20A.pdf> | 827 | 2017-07-30 | 3 |
| `fbise_hssc2_2018` | HSSC-II Annual 2018 | <https://www.fbise.edu.pk/notifications/hssc/Result-Gazette-HSSC-II-A-2018.pdf> | 861 | 2018-08-20 | 3 |
| `fbise_hssc2_2020` | HSSC-II Annual 2020 | <https://www.fbise.edu.pk/notifications/hssc/Result%20Gazette%20HSSC%20A%202020.pdf> | 906 | 2020-07-29 | 2 |

| Field | Value |
|---|---|
| Covers | Whole board ("All Areas"); regular and ex/private candidates; SSC groups Science, Humanities (Technical in 2018); HSSC groups Humanities, Pre-Medical, Pre-Engineering, General Science, Commerce, Medical Technology; male and female |
| Statistics extracted | Enrolled, Absent, Appeared, R.L. (result later), UFM (unfair means), Fail, Pass, grade counts A1–E, Pass %age, G.P.A. — every printed data line, labels as printed → `raw/fbise_gazette_all_areas.csv` |
| Used in analysis | Enrolled, absent, appeared, result later, UFM, fail, passed; pass % (to verify our recomputation). Grade counts and GPA are stored but not analysed (GPA's computation is not documented) |
| Units / definitions | Counts of candidates. Pass % = Pass ÷ Appd. × 100 (verified on all 286 rows to within rounding). Appd. = Enrolled − Absent (verified on all rows) |
| Method | Programmatic: `pdfplumber` text of the one page found by its title, parsed by `src/collect.py::parse_all_areas_text` |
| Verification | (a) Totals reconcile: gender rows sum to group totals, groups to candidate-type totals, types to the grand total (every row, every year). (b) Recomputed pass % matches printed % on every row. (c) 2015–2017 totals equal source 1. (d) Visual spot-check: SSC-II 2015 page 3 rendered and compared by eye with the extracted rows (several rows, including the grand total). |
| 2020 | Page 1 of the HSSC-II 2020 gazette states the examination "was not conducted due to COVID-19" and the result was "prepared under the Promotion Policy of Federal Government". 2020 rows are flagged `assessment = no_exam_promotion_policy` |
| Limitations | One board only. HSSC-II 2019 gazette not found (missing). Supplementary exams not included. Small cells exist (e.g. 2 candidates in SSC "Technical" 2018) |

## Considered but not used

See `DECISIONS.md` ADR-001 for the full list and reasons: a Kaggle dataset of
BISE Faisalabad gazettes (contains student-level records; excluded without
download), an unlicensed GitHub compilation of 15 boards (2024–2026),
Pakistan Education Statistics 2021-22, third-party mirrors of FBISE gazettes for
2021 onwards, and BISE Lahore statistics PDFs (404).

## Licence and redistribution

fbise.edu.pk states "© FBISE. All rights reserved" and publishes no data
licence. This repository does **not** redistribute the PDFs. It does contain
small CSVs of aggregate figures extracted from them, with attribution, so the
analysis can be checked and re-run. See `DECISIONS.md` ADR-005. To regenerate
the CSVs from the official PDFs: `python -m src.collect`.
