# PROJECT.md — Pakistan Board Exam Results: A Data Analysis

> **Status:** Analysis complete; published on GitHub with CI passing; Kaggle publication pending
> **Owner:** `maheeniqbal10`
> **Author:** Maheen Iqbal
> **Repo:** `pakistan-board-results-analysis`
> **License:** MIT
> **Audience:** undergraduate admission/scholarship reviewers and interviewers.
> This is one of three portfolio projects (with `crop-leaf-disease-classifier`
> and `ics-past-papers-bot`) meant to show the core data-science skill: asking
> a clear question and answering it with data.

This file is the canonical specification. If anything else conflicts with it,
this file wins. If something is ambiguous, make the most reasonable choice,
record it in `DECISIONS.md`, and keep going.

---

## 1. Purpose

Take a real, local dataset — Pakistan board (BISE) Matric/Intermediate exam
results — clean it, analyze it, visualize it, and end with **3–4 clear,
defensible findings**. Publish it as a Kaggle notebook and a GitHub repo.

The value is not fancy modeling. It is: a sharp question, careful cleaning,
honest charts, and conclusions that actually follow from the data.

## 2. Research questions (pick 3–4, refine after seeing the data)

Starting candidates — keep the ones the data can genuinely answer:

1. How have pass rates changed across years for one or more boards?
2. Do pass rates or average marks differ between boards (e.g. Lahore,
   Rawalpindi, Peshawar, Karachi, Federal)? By how much?
3. Is there a gap between male and female candidates, and has it changed?
4. Which subject groups (Science / Arts / Computer Science / General) have
   the highest and lowest pass rates?
5. Did a specific event (e.g. 2020 COVID "promotion" policy, smart syllabus)
   leave a visible mark in the numbers?

Write the final chosen questions in `DECISIONS.md` ADR-002 **before** doing the
analysis, so findings are not cherry-picked after looking at every chart.

*Outcome:* questions 1, 3, 4 and 5 were kept for one board (FBISE); question 2
was dropped because only one board's data could be verified (ADR-001, ADR-002).

## 3. Data — aggregate statistics only

**Privacy rule (non-negotiable):** use **aggregate** statistics only — pass
rates, counts, averages by board/year/gender/group. Board result websites
expose individual students' names, roll numbers and marks. **Never scrape,
store, or publish individual student records**, even if they are publicly
viewable. This is a firm line, not a judgment call.

Sourcing priority (budget: $0):
1. A public, already-compiled dataset (Kaggle, Pakistan Bureau of Statistics,
   Pakistan Education Statistics reports, Pakistan Institute of Education)
   that contains board-level aggregate results
2. Official BISE result gazettes/press releases (often PDFs) that publish
   aggregate pass-rate tables — extract the tables (e.g. `pdfplumber` or
   `camelot`) and document every source URL and extraction step
3. Reputable news reports of official aggregate figures, only as a
   cross-check or to fill a small documented gap — never as the sole source
   for a whole analysis

Every number must trace to a documented source in `data/SOURCES.md`.
**Never invent, estimate, or "fill in" missing values silently.** Missing
years/boards are shown as missing and mentioned in Limitations.

## 4. Success criteria (Definition of Done)

- [x] Data collected from documented public sources (§3), aggregate only
- [x] `data/SOURCES.md` lists every source URL, access date, and what it gave
- [x] Cleaning pipeline in `src/` (not only inside the notebook) that turns
      raw files into one tidy table; every cleaning decision logged
- [x] 3–4 research questions fixed in `DECISIONS.md` before analysis
- [x] Clear charts (matplotlib) — titled, labeled axes, units, source line
- [x] 3–4 findings, each one sentence + the chart that supports it +
      a caveat if needed
- [x] Honest Limitations section (missing years, definitions that changed,
      boards not comparable, correlation ≠ causation)
- [ ] Kaggle notebook published (owner step — see `docs/KAGGLE_PUBLISHING.md`)
- [ ] README with screenshots of key charts and a link to the Kaggle notebook
      (charts done; link after publication)
- [x] `docs/CODE_WALKTHROUGH.md` — plain-language explanation of every file
      (see §7)
- [x] Tests for the cleaning functions, CI green

## 5. Non-goals

- No machine learning or prediction — this is descriptive analysis
- No individual-level data, ever (§3)
- No causal claims the data can't support ("girls study harder" is not a
  finding; "female pass rate exceeded male by X points in 2019–2023 in
  board Y" is)

## 6. Tech stack

Python 3.11 · pandas · matplotlib · Jupyter · pdfplumber · pytest · ruff

## 7. Interview readiness

The applicant will be asked about any line of this project. So:
- Keep code simple and readable — plain functions, no clever abstractions
- Comment *why*, not *what*
- Write `docs/CODE_WALKTHROUGH.md`: for each file, what it does, how it works
  step by step, and 2–3 likely interview questions with honest answers
  (e.g. "Why did you drop these rows?", "Why a line chart here?")

## 8. Repository structure

```
pakistan-board-results-analysis/
├── PROJECT.md  TASKS.md  IMPLEMENTATION_PLAN.md  ARCHITECTURE.md
├── DECISIONS.md  CHANGELOG.md  README.md  LICENSE
├── requirements.txt  pyproject.toml  .gitignore
├── .github/workflows/ci.yml
├── data/
│   ├── SOURCES.md          # every source, URL, access date, checksum
│   ├── raw/                # extracted aggregate tables + source manifest
│   │   └── _downloads/     # original PDFs (git-ignored, re-downloadable)
│   └── processed/          # tidy table + summary tables behind each chart
├── src/
│   ├── collect.py          # download PDFs / extract aggregate tables
│   ├── clean.py            # raw -> validated tidy table
│   ├── analysis.py         # small summary functions per question
│   └── plots.py            # chart functions with consistent style
├── notebooks/
│   └── analysis.ipynb      # the story: question -> chart -> finding (also the Kaggle notebook)
├── figures/                # exported PNGs used in README
├── tests/                  # parsing, cleaning, analysis, data integrity
├── docs/
│   ├── findings.md
│   ├── CODE_WALKTHROUGH.md
│   └── KAGGLE_PUBLISHING.md
└── scripts/
    ├── run_all.sh
    └── make_figures.py
```

## 9. Definition of Done

All boxes in §4 checked, every number traceable to `data/SOURCES.md`, no
individual student data anywhere in the repo or its history, README shows
the findings with charts, CI green.
