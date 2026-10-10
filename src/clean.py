"""Turn the extracted FBISE tables into one validated, tidy table.

Input
    data/raw/fbise_gazette_all_areas.csv            (written by src/collect.py)
    data/raw/fbise_result_statistics_2013_2017.csv  (written by src/collect.py)

Output
    data/processed/results_tidy.csv

One row of the output = one (level, year, candidate_type, group, gender) cell.
Totals printed in the gazette are kept as rows whose label is "All", e.g.
gender == "All" is the printed group total. To avoid double counting, always
filter on all three of candidate_type, group and gender before summing.

Every rule applied here is explained in DECISIONS.md (ADR-003).

Run with:  python -m src.clean
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
GAZETTE_CSV = ROOT / "data" / "raw" / "fbise_gazette_all_areas.csv"
STATISTICS_CSV = ROOT / "data" / "raw" / "fbise_result_statistics_2013_2017.csv"
TIDY_CSV = ROOT / "data" / "processed" / "results_tidy.csv"

BOARD = "FBISE"

# Printed label -> standard label. Anything not listed here is an error rather
# than a silent guess, so a new label in a future gazette forces a human look.
CANDIDATE_TYPES = {
    "REGULAR CANDIDATES": "Regular",
    "EX/PRIVATE CANDIDATES": "Private",
    "ALL": "All",
}
GENDERS = {"MALE": "Male", "FEMALE": "Female", "ALL": "All"}
GROUPS = {
    # SSC (Matric)
    "SCIENCE": "Science",
    "HUMANITIES": "Humanities",
    "TECHNICAL": "Technical",
    # HSSC (Intermediate)
    "PRE-MED.": "Pre-Medical",
    "PRE-ENGG.": "Pre-Engineering",
    "SC. GENERAL": "General Science",
    "COMMERCE": "Commerce",
    "MED. TECH.": "Medical Technology",
    "ALL": "All",
}

# 2020 results were not based on an examination. The HSSC-II 2020 gazette
# states the exam "was not conducted due to COVID-19" and results were
# "prepared under the Promotion Policy of Federal Government".
NO_EXAM_YEARS = {2020}

COUNT_COLUMNS = ["enrolled", "absent", "appeared", "result_later", "ufm", "fail", "passed"]
KEY_COLUMNS = ["board", "level", "part", "year", "candidate_type", "group", "gender"]
OUTPUT_COLUMNS = KEY_COLUMNS + [
    "assessment", *COUNT_COLUMNS, "pass_rate", "pass_rate_published",
    "pass_rate_method", "source_id", "source_page",
]

# The gazette prints pass % to 2 decimal places, so a correct recomputation can
# differ from it by at most 0.005 points. Allow a little float slack on top.
PASS_RATE_TOLERANCE = 0.006


class DataValidationError(ValueError):
    """Raised when the data breaks a rule it must satisfy. Lists every problem."""


def standardise_label(value: str, mapping: dict[str, str], what: str) -> str:
    key = " ".join(str(value).split()).upper()
    if key not in mapping:
        raise DataValidationError(f"unknown {what} label {value!r}; add it to clean.py on purpose")
    return mapping[key]


def pass_rate(passed: pd.Series, appeared: pd.Series) -> pd.Series:
    """passed / appeared * 100, the definition FBISE uses for its printed pass %.

    A zero or missing denominator gives NaN (undefined), never 0 or an error.
    """
    passed = pd.to_numeric(passed, errors="coerce").astype("Float64")
    appeared = pd.to_numeric(appeared, errors="coerce").astype("Float64")
    rate = passed / appeared.where(appeared > 0) * 100
    return rate.astype("float64")


def to_counts(series: pd.Series, column: str) -> pd.Series:
    """Parse a count column. Blank stays missing (<NA>); junk text is an error."""
    numeric = pd.to_numeric(series, errors="coerce")
    bad = series.notna() & numeric.isna()
    if bad.any():
        raise DataValidationError(f"non-numeric values in {column}: {series[bad].tolist()}")
    if (numeric.dropna() % 1 != 0).any():
        raise DataValidationError(f"non-integer counts in {column}")
    return numeric.astype("Int64")


def build_gazette_rows(raw: pd.DataFrame) -> pd.DataFrame:
    if raw.empty:
        raise DataValidationError("gazette table is empty")
    required = {"source_id", "year", "level", "part", "page", "candidate_type", "group",
                "gender", "row_type", "pass_pct_published", *COUNT_COLUMNS}
    missing = required - set(raw.columns)
    if missing:
        raise DataValidationError(f"gazette table is missing columns: {sorted(missing)}")

    df = pd.DataFrame({
        "board": BOARD,
        "level": raw["level"].astype(str),
        "part": raw["part"].astype(str),
        "year": to_counts(raw["year"], "year"),
        "candidate_type": [standardise_label(v, CANDIDATE_TYPES, "candidate type")
                           for v in raw["candidate_type"]],
        "group": [standardise_label(v, GROUPS, "group") for v in raw["group"]],
        "gender": [standardise_label(v, GENDERS, "gender") for v in raw["gender"]],
    })
    for column in COUNT_COLUMNS:
        df[column] = to_counts(raw[column], column)
    df["pass_rate_published"] = pd.to_numeric(raw["pass_pct_published"], errors="raise")
    df["pass_rate"] = pass_rate(df["passed"], df["appeared"])
    df["pass_rate_method"] = "computed_from_counts"
    df["source_id"] = raw["source_id"].astype(str)
    df["source_page"] = to_counts(raw["page"], "page")
    df["row_type"] = raw["row_type"].astype(str)  # used by validation only
    return df


def build_statistics_rows(raw: pd.DataFrame, gazette_years: dict[str, set[int]]) -> pd.DataFrame:
    """Overall Part-II pass % from the 2013-2017 summary, for years with no gazette.

    Only the Part-II pass % is used (Part I is a different exam, and the
    appeared/passed counts in that PDF mix Part I and II). Years that also
    have a gazette are skipped, so nothing is double counted; those years are
    used instead to cross-check the two sources (see tests).
    """
    part2 = raw[(raw["metric"] == "pass_pct") & (raw["part"] == "II")]
    rows = []
    for record in part2.itertuples(index=False):
        if int(record.year) in gazette_years.get(record.level, set()):
            continue
        rows.append({
            "board": BOARD, "level": record.level, "part": "II", "year": int(record.year),
            "candidate_type": "All", "group": "All", "gender": "All",
            "pass_rate_published": float(record.value),
            # No counts are published for these rows, so the counts stay
            # missing and the published percentage is the only figure we have.
            "pass_rate": float(record.value),
            "pass_rate_method": "published_only",
            "source_id": record.source_id, "source_page": int(record.page),
            "row_type": "grand_total",
        })
    df = pd.DataFrame(rows)
    for column in COUNT_COLUMNS:
        df[column] = pd.array([pd.NA] * len(df), dtype="Int64")
    df["year"] = df["year"].astype("Int64")
    df["source_page"] = df["source_page"].astype("Int64")
    return df


def validate(df: pd.DataFrame) -> None:
    """Check every rule the tidy table must satisfy; raise listing all failures."""
    problems: list[str] = []
    if df.empty:
        raise DataValidationError("tidy table is empty")

    def report(mask: pd.Series, message: str) -> None:
        mask = mask.fillna(False).astype(bool)
        if mask.any():
            where = df.loc[mask, ["level", "year", "candidate_type", "group", "gender"]]
            problems.append(f"{message}: {where.to_dict('records')[:5]}")

    dupes = df.duplicated(KEY_COLUMNS, keep=False)
    report(dupes, "duplicate keys")

    for column in COUNT_COLUMNS:
        report(df[column] < 0, f"negative {column}")
    report(df["passed"] > df["appeared"], "passed > appeared")
    report(df["appeared"] > df["enrolled"], "appeared > enrolled")
    report(df["appeared"] != df["enrolled"] - df["absent"], "appeared != enrolled - absent")
    report((df["pass_rate"] < 0) | (df["pass_rate"] > 100), "pass_rate outside 0-100")

    # Our recomputed rate must agree with the rate FBISE printed.
    computed = df["pass_rate_method"] == "computed_from_counts"
    gap = (df["pass_rate"] - df["pass_rate_published"]).abs()
    report(computed & (gap > PASS_RATE_TOLERANCE), "recomputed pass rate differs from published")

    # Printed totals must equal the sum of their parts. This catches misread
    # columns or rows during PDF extraction.
    counted = df[computed]
    checks = [
        # (rows that are parts, rows that are the total, columns that identify a total)
        ("gender", "group_total", ["level", "year", "candidate_type", "group"]),
        ("group_total", "candidate_type_total", ["level", "year", "candidate_type"]),
        ("candidate_type_total", "grand_total", ["level", "year"]),
    ]
    for part_type, total_type, keys in checks:
        parts = counted[counted["row_type"] == part_type].groupby(keys)[COUNT_COLUMNS].sum()
        totals = counted[counted["row_type"] == total_type].set_index(keys)[COUNT_COLUMNS]
        parts, totals = parts.align(totals, join="outer")
        bad = (parts != totals).any(axis=1)
        if bad.any():
            problems.append(f"{part_type} rows do not add up to {total_type}: "
                            f"{list(bad[bad].index)[:5]}")

    if problems:
        raise DataValidationError("validation failed:\n- " + "\n- ".join(problems))


def clean(gazette_raw: pd.DataFrame, statistics_raw: pd.DataFrame) -> pd.DataFrame:
    gazette = build_gazette_rows(gazette_raw)
    gazette_years = gazette.groupby("level")["year"].apply(lambda s: set(s.astype(int))).to_dict()
    statistics = build_statistics_rows(statistics_raw, gazette_years)
    tidy = pd.concat([gazette, statistics], ignore_index=True)
    tidy["assessment"] = tidy["year"].map(
        lambda y: "no_exam_promotion_policy" if int(y) in NO_EXAM_YEARS else "examination")

    validate(tidy)

    # Stable, readable order so re-running gives a byte-identical file.
    order = {"Regular": 0, "Private": 1, "All": 2, "Male": 0, "Female": 1}
    tidy = tidy.assign(
        _ct=tidy["candidate_type"].map(order), _g=tidy["gender"].map(order),
        _grp=tidy["group"].eq("All"),
    ).sort_values(["level", "year", "_ct", "_grp", "group", "_g"], kind="stable")
    return tidy[OUTPUT_COLUMNS].reset_index(drop=True)


def main() -> int:
    tidy = clean(pd.read_csv(GAZETTE_CSV), pd.read_csv(STATISTICS_CSV))
    TIDY_CSV.parent.mkdir(parents=True, exist_ok=True)
    tidy.to_csv(TIDY_CSV, index=False, float_format="%.4f", lineterminator="\n")
    print(f"wrote {TIDY_CSV.relative_to(ROOT)}: {len(tidy)} rows, all checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
