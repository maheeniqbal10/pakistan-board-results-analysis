"""Tests for src/clean.py using small synthetic tables (see conftest.py)."""

import math

import pandas as pd
import pytest

from src.clean import GROUPS, DataValidationError, clean, pass_rate, standardise_label


def test_clean_produces_standard_labels(gazette_raw, statistics_raw):
    tidy = clean(gazette_raw, statistics_raw)
    assert set(tidy["candidate_type"]) == {"Regular", "Private", "All"}
    assert set(tidy["gender"]) == {"Male", "Female", "All"}  # "MALE" and "Male" merged
    assert set(tidy["group"]) == {"Science", "Humanities", "All"}


def test_pass_rate_uses_appeared_as_denominator(gazette_raw, statistics_raw):
    tidy = clean(gazette_raw, statistics_raw)
    male = tidy[(tidy["gender"] == "Male") & (tidy["group"] == "Science")].iloc[0]
    # 80 passed out of 100 appeared (102 enrolled - 2 absent), not out of 102 enrolled
    assert male["appeared"] == 100
    assert male["pass_rate"] == pytest.approx(80.0)


def test_pass_rate_zero_or_missing_denominator_is_undefined():
    rates = pass_rate(pd.Series([0, 5, None]), pd.Series([0, None, 10]))
    assert all(math.isnan(r) for r in rates)


def test_pass_rate_is_not_rounded():
    rate = pass_rate(pd.Series([1]), pd.Series([3]))[0]
    assert rate == pytest.approx(33.333333, rel=1e-6)


def test_statistics_rows_only_fill_years_without_a_gazette(gazette_raw, statistics_raw):
    tidy = clean(gazette_raw, statistics_raw)
    published_only = tidy[tidy["pass_rate_method"] == "published_only"]
    assert list(published_only["year"]) == [2098]  # 2099 has a gazette; Part I is ignored
    assert published_only["pass_rate"].iloc[0] == pytest.approx(70.5)


def test_missing_counts_stay_missing_not_zero(gazette_raw, statistics_raw):
    tidy = clean(gazette_raw, statistics_raw)
    row = tidy[tidy["pass_rate_method"] == "published_only"].iloc[0]
    for column in ["enrolled", "appeared", "passed"]:
        assert pd.isna(row[column])


def test_absent_cells_are_not_invented(gazette_raw, statistics_raw):
    # The synthetic gazette has no private female row; clean() must not add one.
    tidy = clean(gazette_raw, statistics_raw)
    private = tidy[(tidy["candidate_type"] == "Private") & (tidy["gender"] == "Female")]
    assert private.empty


def test_2020_is_flagged_as_no_exam_year(gazette_raw, statistics_raw):
    raw = gazette_raw.assign(year=2020, source_id="synthetic_ssc_2020")
    tidy = clean(raw, statistics_raw)
    exam_rows = tidy[tidy["pass_rate_method"] == "computed_from_counts"]
    assert set(exam_rows["assessment"]) == {"no_exam_promotion_policy"}


def test_cleaning_is_deterministic(gazette_raw, statistics_raw):
    first = clean(gazette_raw, statistics_raw)
    second = clean(gazette_raw.sample(frac=1, random_state=1), statistics_raw)
    pd.testing.assert_frame_equal(first, second)


def test_unknown_label_is_rejected():
    with pytest.raises(DataValidationError, match="unknown group"):
        standardise_label("Arts & Crafts", GROUPS, "group")


def test_label_matching_ignores_case_and_spacing():
    assert standardise_label("  pre-med. ", GROUPS, "group") == "Pre-Medical"


# --- each validation rule must actually fire --------------------------------

def test_empty_input_fails_clearly(statistics_raw):
    with pytest.raises(DataValidationError, match="empty"):
        clean(pd.DataFrame(), statistics_raw)


def test_missing_column_fails_clearly(gazette_raw, statistics_raw):
    with pytest.raises(DataValidationError, match="missing columns"):
        clean(gazette_raw.drop(columns=["passed"]), statistics_raw)


def test_non_numeric_count_is_rejected(gazette_raw, statistics_raw):
    raw = gazette_raw.astype({"passed": object})
    raw.loc[0, "passed"] = "8O"  # letter O, a typical OCR/typing error
    with pytest.raises(DataValidationError, match="non-numeric"):
        clean(raw, statistics_raw)


def test_negative_count_is_rejected(gazette_raw, statistics_raw):
    raw = gazette_raw.copy()
    raw.loc[0, "absent"] = -1
    raw.loc[0, "enrolled"] = 99  # keep appeared = enrolled - absent true
    with pytest.raises(DataValidationError, match="negative absent"):
        clean(raw, statistics_raw)


def test_passed_greater_than_appeared_is_rejected(gazette_raw, statistics_raw):
    raw = gazette_raw.copy()
    raw.loc[0, "passed"] = 101
    with pytest.raises(DataValidationError, match="passed > appeared"):
        clean(raw, statistics_raw)


def test_appeared_must_equal_enrolled_minus_absent(gazette_raw, statistics_raw):
    raw = gazette_raw.copy()
    raw.loc[0, "appeared"] = 99
    with pytest.raises(DataValidationError, match="enrolled - absent"):
        clean(raw, statistics_raw)


def test_published_pass_rate_mismatch_is_flagged(gazette_raw, statistics_raw):
    raw = gazette_raw.copy()
    raw.loc[0, "pass_pct_published"] = "80.02"  # recomputed value is exactly 80.00
    with pytest.raises(DataValidationError, match="differs from published"):
        clean(raw, statistics_raw)


def test_rounding_within_tolerance_is_accepted(gazette_raw, statistics_raw):
    # 125/150 = 83.333..., printed as 83.33 — a normal rounding difference.
    tidy = clean(gazette_raw, statistics_raw)
    total = tidy[(tidy["candidate_type"] == "Regular") & (tidy["group"] == "All")].iloc[0]
    assert total["pass_rate_published"] == pytest.approx(83.33)
    assert total["passed"] == 125  # source counts are never altered by rounding


def test_totals_that_do_not_add_up_are_rejected(gazette_raw, statistics_raw):
    raw = gazette_raw.copy()
    # Change the male row consistently (so row-level checks pass) but leave the
    # group total alone, as a misaligned PDF row would.
    raw.loc[0, ["enrolled", "appeared", "passed"]] = [112, 110, 88]
    raw.loc[0, "pass_pct_published"] = "80.00"
    with pytest.raises(DataValidationError, match="do not add up"):
        clean(raw, statistics_raw)


def test_duplicate_keys_are_rejected(gazette_raw, statistics_raw):
    raw = pd.concat([gazette_raw, gazette_raw.iloc[[0]]], ignore_index=True)
    with pytest.raises(DataValidationError, match="duplicate keys"):
        clean(raw, statistics_raw)
