# TASKS.md — pakistan-board-results-analysis

Work top to bottom. Commit after each phase.

## Phase 0 — Setup
- [x] `.gitignore`, `requirements.txt`, `pyproject.toml`, `LICENSE`
- [x] Folder structure per `PROJECT.md` §8
- [x] git repository initialised and first commit

## Phase 1 — Find the data
- [x] Search sources in the priority order of `PROJECT.md` §3
- [x] Record what was found (and not found) in `DECISIONS.md` ADR-001
- [x] `data/SOURCES.md`: URL, access date, publisher, what it covers
- [x] Confirm: aggregate statistics only — no names, roll numbers, or
      individual marks anywhere (ADR-004; allow-list test)

## Phase 2 — Collect
- [x] `src/collect.py`: download PDFs, extract aggregate tables into `data/raw/`
- [x] Spot-check extracted numbers against the original source by eye
      (SSC-II 2015 page 3) plus automated cross-checks

## Phase 3 — Clean
- [x] `src/clean.py`: one tidy table
- [x] Standardise labels, handle missing values explicitly (never invent)
- [x] Log every cleaning decision in `DECISIONS.md` ADR-003
- [x] Tests: pass_rate within 0–100, passed <= appeared, no duplicate keys,
      and more (`tests/`)

## Phase 4 — Fix the questions
- [x] Coverage reviewed; 4 questions written in `DECISIONS.md` ADR-002 before
      plotting results

## Phase 5 — Analyze and visualize
- [x] `src/plots.py`: consistent style (title, axis labels, units, source line)
- [x] `notebooks/analysis.ipynb`: question → chart → interpretation → limitation
- [x] Key charts exported to `figures/`

## Phase 6 — Findings
- [x] `docs/findings.md`: 4 findings with numbers, charts and caveats
- [x] Each finding checked against the generated tables; no causal claims

## Phase 7 — Interview readiness
- [x] `docs/CODE_WALKTHROUGH.md`
- [ ] Owner reads the walkthrough and can explain each decision

## Phase 8 — CI + README
- [x] `.github/workflows/ci.yml`: ruff + pytest + reproducibility + notebook
- [x] README: questions, data, method, findings with charts, limitations, how to run
- [x] CI confirmed green on GitHub
- [ ] `CHANGELOG.md` v1.0.0 (after the owner's review and Kaggle publication)

## Phase 9 — Kaggle (owner step)
- [x] Notebook runs top-to-bottom locally and looks for the code on Kaggle
- [x] `docs/KAGGLE_PUBLISHING.md` with exact steps
- [ ] Publish on Kaggle (owner's account)

## Definition of Done
See `PROJECT.md` §9.
