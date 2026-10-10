"""Shared test fixtures.

All numbers in this file are SYNTHETIC — invented to exercise the code. They
are never written to data/ and never used in the analysis. Tests that check
the real dataset live in tests/test_dataset.py and read data/processed/.
"""

import pandas as pd
import pytest

COUNTS = ["enrolled", "absent", "appeared", "result_later", "ufm", "fail", "passed",
          "grade_a1", "grade_a", "grade_b", "grade_c", "grade_d", "grade_e"]


def raw_row(candidate_type, group, gender, row_type, enrolled, absent, passed, fail,
            pct, year=2099, level="SSC"):
    appeared = enrolled - absent
    values = {
        "source_id": f"synthetic_{level.lower()}_{year}", "year": year, "level": level,
        "part": "II", "page": 3, "line_no": 0, "candidate_type": candidate_type,
        "group": group, "gender": gender, "row_type": row_type,
        "enrolled": enrolled, "absent": absent, "appeared": appeared, "result_later": 0,
        "ufm": appeared - passed - fail, "fail": fail, "passed": passed,
        "grade_a1": 0, "grade_a": 0, "grade_b": 0, "grade_c": 0, "grade_d": 0, "grade_e": 0,
        "pass_pct_published": pct, "gpa_published": "0.00",
    }
    return values


@pytest.fixture
def gazette_raw() -> pd.DataFrame:
    """A tiny, internally consistent synthetic gazette: one year, one group."""
    rows = [
        raw_row("REGULAR CANDIDATES", "SCIENCE", "Male", "gender", 102, 2, 80, 20, "80.00"),
        raw_row("REGULAR CANDIDATES", "SCIENCE", "Female", "gender", 51, 1, 45, 5, "90.00"),
        raw_row("REGULAR CANDIDATES", "SCIENCE", "ALL", "group_total", 153, 3, 125, 25,
                "83.33"),
        raw_row("REGULAR CANDIDATES", "ALL", "ALL", "candidate_type_total", 153, 3, 125, 25,
                "83.33"),
        raw_row("EX/PRIVATE CANDIDATES", "HUMANITIES", "MALE", "gender", 40, 0, 10, 30,
                "25.00"),
        raw_row("EX/PRIVATE CANDIDATES", "HUMANITIES", "ALL", "group_total", 40, 0, 10, 30,
                "25.00"),
        raw_row("EX/PRIVATE CANDIDATES", "ALL", "ALL", "candidate_type_total", 40, 0, 10, 30,
                "25.00"),
        raw_row("ALL", "ALL", "ALL", "grand_total", 193, 3, 135, 55, "71.05"),
    ]
    return pd.DataFrame(rows)


@pytest.fixture
def statistics_raw() -> pd.DataFrame:
    return pd.DataFrame([
        {"source_id": "synthetic_stats", "page": 1, "year": 2098, "level": "SSC", "part": "II",
         "metric": "pass_pct", "value": "70.5"},
        {"source_id": "synthetic_stats", "page": 1, "year": 2098, "level": "SSC", "part": "I",
         "metric": "pass_pct", "value": "60.0"},
        # same year as the synthetic gazette -> must be skipped, not duplicated
        {"source_id": "synthetic_stats", "page": 1, "year": 2099, "level": "SSC", "part": "II",
         "metric": "pass_pct", "value": "71.05"},
        {"source_id": "synthetic_stats", "page": 3, "year": 2098, "level": "SSC",
         "part": "I+II", "metric": "appeared", "value": "1000"},
    ])
