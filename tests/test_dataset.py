"""Integrity checks on the REAL committed data (data/raw and data/processed).

These need no network: they read the CSVs that src/collect.py and
src/clean.py wrote and that are committed to the repository.
"""

from pathlib import Path

import pandas as pd
import pytest

from src.clean import clean

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
TIDY = ROOT / "data" / "processed" / "results_tidy.csv"


@pytest.fixture(scope="module")
def tidy() -> pd.DataFrame:
    return pd.read_csv(TIDY)


def test_committed_tidy_table_matches_a_fresh_clean(tidy, tmp_path):
    fresh = clean(pd.read_csv(RAW / "fbise_gazette_all_areas.csv"),
                  pd.read_csv(RAW / "fbise_result_statistics_2013_2017.csv"))
    fresh.to_csv(tmp_path / "fresh.csv", index=False, float_format="%.4f")
    pd.testing.assert_frame_equal(pd.read_csv(tmp_path / "fresh.csv"), tidy)


def test_gazette_totals_agree_with_independent_statistics_pdf(tidy):
    """FBISE's 2013-2017 summary PDF and the gazettes are separate documents.
    For the overlapping years their Part-II pass rates must match exactly."""
    stats = pd.read_csv(RAW / "fbise_result_statistics_2013_2017.csv")
    stats = stats[(stats["metric"] == "pass_pct") & (stats["part"] == "II")]
    totals = tidy[(tidy["candidate_type"] == "All")
                  & (tidy["pass_rate_method"] == "computed_from_counts")]
    merged = totals.merge(stats, on=["level", "year"])
    assert len(merged) == 6  # SSC and HSSC, 2015-2017
    assert (merged["pass_rate_published"] - merged["value"]).abs().max() < 1e-9


def test_expected_coverage(tidy):
    years = tidy.groupby("level")["year"].apply(lambda s: sorted(set(s))).to_dict()
    assert years["SSC"] == [2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020]
    # HSSC-II 2019 is genuinely missing (no gazette found) and must stay missing.
    assert years["HSSC"] == [2013, 2014, 2015, 2016, 2017, 2018, 2020]


def test_only_2020_is_flagged_as_no_exam(tidy):
    flagged = set(tidy.loc[tidy["assessment"] != "examination", "year"])
    assert flagged == {2020}


ALLOWED_COLUMNS = {
    # identifiers of a table cell, never of a person
    "board", "level", "part", "year", "candidate_type", "group", "gender", "row_type",
    "assessment", "metric",
    # aggregate counts and rates
    "enrolled", "absent", "appeared", "result_later", "ufm", "fail", "passed",
    "grade_a1", "grade_a", "grade_b", "grade_c", "grade_d", "grade_e",
    "pass_rate", "pass_rate_published", "pass_rate_method", "pass_pct_published",
    "gpa_published", "value",
    # provenance
    "source_id", "source_page", "page", "line_no", "url", "file", "bytes", "sha256",
    "first_downloaded",
}


def test_committed_data_has_only_aggregate_columns():
    """Privacy guard: an allow-list (not a block-list) of columns, so a new
    column such as a name or roll number can never slip in unnoticed."""
    for path in [*RAW.glob("*.csv"), TIDY]:
        columns = set(pd.read_csv(path, nrows=0).columns)
        assert columns <= ALLOWED_COLUMNS, f"{path.name}: unexpected {columns - ALLOWED_COLUMNS}"


def test_smallest_cells_are_still_aggregates(tidy):
    # Every gender-level row is a count of candidates, never a single person's
    # result with marks. A cell can be small (e.g. 2 candidates) - that is
    # documented - but it must still be a count row.
    gender_rows = tidy[tidy["gender"] != "All"]
    assert gender_rows["appeared"].notna().all()
