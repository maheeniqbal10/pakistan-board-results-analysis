"""Tests for src/analysis.py, using the synthetic tables from conftest.py."""

import math

import pandas as pd
import pytest

from src import analysis
from src.clean import clean


@pytest.fixture
def tidy(gazette_raw, statistics_raw) -> pd.DataFrame:
    return clean(gazette_raw, statistics_raw)


def test_pooled_rate_weights_by_candidates_not_by_year():
    rows = pd.DataFrame({"appeared": [100, 900], "passed": [100, 450]})
    # Averaging the yearly rates would give (100% + 50%) / 2 = 75%.
    assert analysis.pooled_pass_rate(rows) == pytest.approx(55.0)


def test_pooled_rate_without_counts_is_undefined():
    rows = pd.DataFrame({"appeared": pd.array([pd.NA], dtype="Int64"),
                         "passed": pd.array([pd.NA], dtype="Int64")})
    assert math.isnan(analysis.pooled_pass_rate(rows))


def test_select_needs_every_label_so_totals_are_not_mixed_with_parts(tidy):
    rows = analysis.select(tidy, candidate_type="Regular", group="Science", gender="All")
    assert len(rows) == 1 and rows["appeared"].iloc[0] == 150


def test_gender_gap_is_female_minus_male_in_points(tidy):
    gaps = analysis.gender_gaps(tidy, years=[2099])
    science = gaps[gaps["group"] == "Science"].iloc[0]
    assert science["gap_pp"] == pytest.approx(90.0 - 80.0)


def test_small_cells_are_marked_not_comparable(tidy):
    # Synthetic Science cells have 100 male and 50 female candidates;
    # 50 is below the 100-candidate rule.
    gaps = analysis.gender_gaps(tidy, years=[2099])
    assert not gaps["comparable"].any()


def test_overall_gender_gap_sums_groups_before_dividing(tidy):
    gap = analysis.overall_gender_gap(tidy, years=[2099]).iloc[0]
    # Regular only: females 45/50 = 90%, males 80/100 = 80%.
    assert gap["gap_pp"] == pytest.approx(10.0)


def test_change_between_reports_percentage_points():
    trend = pd.DataFrame({"level": ["SSC", "SSC"], "population": ["All candidates"] * 2,
                          "year": [2015, 2019], "pass_rate": [60.0, 65.0]})
    # 60% -> 65% is +5 percentage points (a relative change would be +8.3%).
    assert analysis.change_between(trend, "SSC", "All candidates", 2015, 2019) == 5.0


def test_candidate_mix_share(tidy):
    mix = analysis.candidate_mix(tidy).iloc[0]
    assert mix["private_share_pct"] == pytest.approx(40 / 190 * 100)


def test_compare_2020_uses_only_exam_years(gazette_raw, statistics_raw):
    tidy = clean(gazette_raw.assign(year=2019, source_id="synthetic_2019"), statistics_raw)
    # A hand-built 2020 grand-total row: 180 of 190 passed.
    row_2020 = tidy[tidy["candidate_type"] == "All"].assign(
        year=2020, passed=180, fail=10, result_later=0, pass_rate=180 / 190 * 100,
        assessment="no_exam_promotion_policy")
    table = analysis.compare_2020(pd.concat([tidy, row_2020], ignore_index=True))
    total = table[table["candidate_type"] == "All"].iloc[0]
    assert total["exam_years"] == "2019"
    assert total["highest_exam_year_rate"] == pytest.approx(135 / 190 * 100)
    assert total["pp_above_highest_exam_year"] == pytest.approx((180 - 135) / 190 * 100)
