"""Tests for the PDF-text parsers in src/collect.py.

The page texts below are SYNTHETIC but copy the exact layout pdfplumber
produces for the real FBISE pages, so no network or PDF is needed.
"""

import pytest

from src.collect import parse_all_areas_text, parse_statistics_pages

SSC_PAGE = """FBISE - Computer Section 3
FEDERAL BOARD OF INTERMEDIATE AND SECONDARY EDUCATION, ISLAMABAD
RESULT GAZETTE OF SSC-II ANNUAL EXAMINATION 2099
SALIENT FEATURES OF RESULT ALL AREAS
G r a d e W i s e D i s t r i b u t i o n Pass
Enrolled Absent Appd. R.L. UFM Fail Pass A1 A B C D E %age G.P.A
REGULAR CANDIDATES
Male 102 2 100 0 0 20 80 1 2 3 4 5 6 80.00 3.00
Female 51 1 50 0 0 5 45 1 2 3 4 5 6 90.00 3.50
1
SCIENCE Total : 153 3 150 0 0 25 125 2 4 6 8 10 12 83.33 3.17
Total : 153 3 150 0 0 25 125 2 4 6 8 10 12 83.33 3.17
EX/PRIVATE CANDIDATES
Male 40 0 40 0 0 30 10 0 0 0 0 0 10 25.00 0.50
2
HUMANITIES Total : 40 0 40 0 0 30 10 0 0 0 0 0 10 25.00 0.50
Total : 40 0 40 0 0 30 10 0 0 0 0 0 10 25.00 0.50
Grand Total : 193 3 190 0 0 55 135 2 4 6 8 10 22 71.05 2.50
"""

# HSSC layout: upper-case genders, group number and name on the Total line.
HSSC_LINES = """REGULAR CANDIDATES
MALE 10 0 10 0 0 5 5 0 0 0 0 0 5 50.00 1.00
FEMALE 10 0 10 0 0 2 8 0 0 0 0 0 8 80.00 1.60
2 Pre-Med. Total : 20 0 20 0 0 7 13 0 0 0 0 0 13 65.00 1.30
Total : 20 0 20 0 0 7 13 0 0 0 0 0 13 65.00 1.30
Grand Total : 20 0 20 0 0 7 13 0 0 0 0 0 13 65.00 1.30
"""


def test_parses_every_data_line_with_correct_labels():
    rows = parse_all_areas_text(SSC_PAGE)
    assert len(rows) == 8
    first = rows[0]
    assert (first["candidate_type"], first["group"], first["gender"]) == (
        "REGULAR CANDIDATES", "SCIENCE", "Male")
    assert first["appeared"] == 100 and first["passed"] == 80
    assert first["pass_pct_published"] == "80.00"  # kept as printed text


def test_group_label_after_gender_rows_is_assigned_back():
    rows = parse_all_areas_text(SSC_PAGE)
    private_male = [r for r in rows if r["candidate_type"].startswith("EX")
                    and r["row_type"] == "gender"]
    assert [r["group"] for r in private_male] == ["HUMANITIES"]


def test_row_types():
    types = [r["row_type"] for r in parse_all_areas_text(SSC_PAGE)]
    assert types.count("grand_total") == 1
    assert types.count("candidate_type_total") == 2
    assert types.count("group_total") == 2


def test_hssc_layout_with_group_number_prefix():
    rows = parse_all_areas_text(HSSC_LINES)
    assert rows[0]["gender"] == "MALE"
    assert rows[0]["group"] == "Pre-Med."
    assert rows[2]["row_type"] == "group_total"


def test_missing_grand_total_fails():
    text = SSC_PAGE.rsplit("Grand Total", 1)[0]
    with pytest.raises(ValueError, match="Grand Total"):
        parse_all_areas_text(text)


def test_gender_rows_without_group_total_fail():
    text = "REGULAR CANDIDATES\nMale 1 0 1 0 0 0 1 0 0 0 0 0 1 100.00 1.00\n"
    with pytest.raises(ValueError, match="no group total"):
        parse_all_areas_text(text)


def test_unknown_row_label_fails():
    text = SSC_PAGE.replace("Female 51", "Unknown 51")
    with pytest.raises(ValueError, match="unrecognised row label"):
        parse_all_areas_text(text)


STATS_PAGES = [
    "PERCENTAGE OF RESULTS 2013-2017\n90\n2013 2014 2015 2016\n"
    "Year SSC-I (%) SSC-II (%) HSSC-I (%) HSSC-II (%)\n"
    "2013 61.09 77.67 48.5 72.3\n2014 58.76 77.25 50.9 70.65\n",
    "HSSC RESULT STATISTICS\n2013 2014\nYear Appeared Passed\n2013 100 60\n",
    "SSC RESULT STATISTICS\n2013 2014\nYear Appeared Passed\n2013 200 150\n",
]


def test_statistics_parser_ignores_chart_axis_years():
    rows = parse_statistics_pages(STATS_PAGES)
    pct = [r for r in rows if r["metric"] == "pass_pct"]
    assert len(pct) == 8  # 2 years x 4 exams; the "2013 2014 2015 2016" axis line is ignored
    ssc2_2013 = [r for r in pct if r["year"] == 2013 and (r["level"], r["part"]) == ("SSC", "II")]
    assert ssc2_2013[0]["value"] == "77.67"


def test_statistics_counts_are_labelled_part_one_plus_two():
    rows = parse_statistics_pages(STATS_PAGES)
    counts = [r for r in rows if r["metric"] in ("appeared", "passed")]
    assert {r["part"] for r in counts} == {"I+II"}
    assert {(r["level"], r["metric"], r["value"]) for r in counts} == {
        ("HSSC", "appeared", "100"), ("HSSC", "passed", "60"),
        ("SSC", "appeared", "200"), ("SSC", "passed", "150")}
