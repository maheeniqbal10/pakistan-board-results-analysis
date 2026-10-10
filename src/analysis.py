"""Small, tested summary functions used by the notebook and the figures.

Every function takes the tidy table (see src/clean.py) and returns a small
DataFrame. Nothing here reads or writes files except load_tidy().
The rules (minimum cell size, exam years only, ...) come from DECISIONS.md
ADR-002 and were fixed before any outcome was looked at.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TIDY_CSV = ROOT / "data" / "processed" / "results_tidy.csv"

EXAM_YEARS_2015_2019 = [2015, 2016, 2017, 2018, 2019]
MIN_APPEARED = 100  # ADR-002: smaller cells are listed, never compared
LEVEL_NAMES = {"SSC": "SSC-II (Matric)", "HSSC": "HSSC-II (Intermediate)"}
GROUP_ORDER = {
    "SSC": ["Science", "Humanities"],
    "HSSC": ["Pre-Medical", "Pre-Engineering", "General Science", "Commerce", "Humanities",
             "Medical Technology"],
}

COUNT_COLUMNS = ["enrolled", "absent", "appeared", "result_later", "ufm", "fail", "passed"]


def load_tidy(path: Path = TIDY_CSV) -> pd.DataFrame:
    """Read the tidy table with explicit types (counts stay nullable integers)."""
    df = pd.read_csv(path)
    for column in COUNT_COLUMNS:
        df[column] = df[column].astype("Int64")
    return df


def select(df: pd.DataFrame, *, candidate_type: str, group: str, gender: str,
           level: str | None = None) -> pd.DataFrame:
    """Pick one kind of cell. All three labels are required on purpose, so a
    total row can never be summed together with its own parts by accident."""
    mask = ((df["candidate_type"] == candidate_type) & (df["group"] == group)
            & (df["gender"] == gender))
    if level is not None:
        mask &= df["level"] == level
    return df[mask]


def pooled_pass_rate(rows: pd.DataFrame) -> float:
    """Total passed / total appeared over several rows (e.g. several years).

    This weights each year by its number of candidates, unlike averaging the
    yearly percentages. Returns NaN if no counts are available.
    """
    appeared = rows["appeared"].sum(min_count=1)
    if pd.isna(appeared) or appeared == 0:
        return float("nan")
    return float(rows["passed"].sum() / appeared * 100)


def overall_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Q1: overall and regular-only pass rate per level and year."""
    overall = select(df, candidate_type="All", group="All", gender="All")
    regular = select(df, candidate_type="Regular", group="All", gender="All")
    out = pd.concat([
        overall.assign(population="All candidates"),
        regular.assign(population="Regular candidates"),
    ])
    columns = ["level", "year", "population", "appeared", "passed", "pass_rate",
               "pass_rate_method", "assessment"]
    return out[columns].sort_values(["level", "population", "year"]).reset_index(drop=True)


def candidate_mix(df: pd.DataFrame) -> pd.DataFrame:
    """Q1 context: share of candidates who appeared as private candidates, per year.

    Private candidates pass at much lower rates than regular ones, so a change
    in their share moves the overall rate even if neither group's rate changes.
    """
    rows = df[(df["group"] == "All") & (df["gender"] == "All")
              & (df["candidate_type"].isin(["Regular", "Private"]))]
    wide = rows.pivot(index=["level", "year"], columns="candidate_type", values="appeared")
    wide["private_share_pct"] = wide["Private"] / (wide["Private"] + wide["Regular"]) * 100
    return wide.reset_index().rename(columns={"Private": "appeared_private",
                                              "Regular": "appeared_regular"})


def change_between(trend: pd.DataFrame, level: str, population: str,
                   start: int, end: int) -> float:
    """Percentage-point change in pass rate between two years (end - start)."""
    rows = trend[(trend["level"] == level) & (trend["population"] == population)]
    rates = rows.set_index("year")["pass_rate"]
    return float(rates[end] - rates[start])


def gender_gaps(df: pd.DataFrame, candidate_type: str = "Regular",
                years: list[int] = EXAM_YEARS_2015_2019) -> pd.DataFrame:
    """Q2: female minus male pass rate (pp) within each level x group x year.

    Rows where either gender has fewer than MIN_APPEARED candidates are kept
    but marked comparable=False, so they can be listed and left out of charts.
    """
    cells = df[(df["candidate_type"] == candidate_type) & (df["gender"].isin(["Female", "Male"]))
               & (df["group"] != "All") & (df["year"].isin(years))]
    wide = cells.pivot_table(index=["level", "group", "year"], columns="gender",
                             values=["pass_rate", "appeared"], aggfunc="first")
    wide.columns = [f"{value}_{gender.lower()}" for value, gender in wide.columns]
    wide = wide.reset_index()
    wide["gap_pp"] = wide["pass_rate_female"] - wide["pass_rate_male"]
    wide["comparable"] = ((wide["appeared_female"] >= MIN_APPEARED)
                          & (wide["appeared_male"] >= MIN_APPEARED))
    return wide.sort_values(["level", "group", "year"]).reset_index(drop=True)


def overall_gender_gap(df: pd.DataFrame, candidate_type: str = "Regular",
                       years: list[int] = EXAM_YEARS_2015_2019) -> pd.DataFrame:
    """Q2 (for transparency): the gap across all groups combined, per year.

    Built by summing the group-level gender rows, since the gazette does not
    print a gender total across groups.
    """
    cells = df[(df["candidate_type"] == candidate_type) & (df["gender"].isin(["Female", "Male"]))
               & (df["group"] != "All") & (df["year"].isin(years))]
    sums = cells.groupby(["level", "year", "gender"])[["appeared", "passed"]].sum().reset_index()
    sums["pass_rate"] = sums["passed"] / sums["appeared"] * 100
    wide = sums.pivot(index=["level", "year"], columns="gender", values="pass_rate")
    wide["gap_pp"] = wide["Female"] - wide["Male"]
    return wide.reset_index().rename(columns={"Female": "pass_rate_female",
                                              "Male": "pass_rate_male"})


def group_pass_rates(df: pd.DataFrame, candidate_type: str = "Regular",
                     years: list[int] = EXAM_YEARS_2015_2019) -> pd.DataFrame:
    """Q3: pass rate per level x group x year, plus the pooled rate over `years`.

    A group is comparable only if at least MIN_APPEARED candidates appeared in
    every one of the years.
    """
    rows = df[(df["candidate_type"] == candidate_type) & (df["gender"] == "All")
              & (df["group"] != "All") & (df["year"].isin(years))]
    summary = []
    for (level, group), g in rows.groupby(["level", "group"]):
        summary.append({
            "level": level, "group": group,
            "years_present": int(g["year"].nunique()),
            "min_appeared": int(g["appeared"].min()),
            "pooled_pass_rate": pooled_pass_rate(g),
            "lowest_year_rate": float(g["pass_rate"].min()),
            "highest_year_rate": float(g["pass_rate"].max()),
        })
    summary = pd.DataFrame(summary)
    expected_years = rows.groupby("level")["year"].nunique()
    summary["comparable"] = ((summary["min_appeared"] >= MIN_APPEARED)
                             & (summary["years_present"]
                                == summary["level"].map(expected_years)))
    yearly = rows[["level", "group", "year", "appeared", "passed", "pass_rate"]]
    return summary.merge(yearly, on=["level", "group"]).sort_values(
        ["level", "group", "year"]).reset_index(drop=True)


def candidate_type_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Q4: yearly pass rate for regular, private and all candidates (gazette years)."""
    rows = df[(df["group"] == "All") & (df["gender"] == "All")
              & (df["pass_rate_method"] == "computed_from_counts")]
    columns = ["level", "year", "candidate_type", "appeared", "passed", "pass_rate", "assessment"]
    return rows[columns].sort_values(["level", "candidate_type", "year"]).reset_index(drop=True)


def compare_2020(df: pd.DataFrame, years: list[int] = EXAM_YEARS_2015_2019) -> pd.DataFrame:
    """Q4: 2020 pass rate next to the lowest and highest exam-year rate."""
    out = []
    for candidate_type in ["Regular", "Private", "All"]:
        rows = select(df, candidate_type=candidate_type, group="All", gender="All")
        for level, g in rows.groupby("level"):
            exam = g[g["year"].isin(years) & (g["pass_rate_method"] == "computed_from_counts")]
            y2020 = g[g["year"] == 2020]
            if exam.empty or y2020.empty:
                continue
            rate_2020 = float(y2020["pass_rate"].iloc[0])
            out.append({
                "level": level, "candidate_type": candidate_type,
                "exam_years": ", ".join(str(y) for y in sorted(exam["year"])),
                "lowest_exam_year_rate": float(exam["pass_rate"].min()),
                "highest_exam_year_rate": float(exam["pass_rate"].max()),
                "rate_2020": rate_2020,
                "pp_above_highest_exam_year": rate_2020 - float(exam["pass_rate"].max()),
                "fail_2020": int(y2020["fail"].iloc[0]),
                "result_later_2020": int(y2020["result_later"].iloc[0]),
                "appeared_2020": int(y2020["appeared"].iloc[0]),
            })
    return pd.DataFrame(out)
