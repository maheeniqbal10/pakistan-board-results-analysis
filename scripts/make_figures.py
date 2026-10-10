"""Regenerate every figure and summary table from the tidy table.

Run from the repository root:  python -m scripts.make_figures

Outputs
    figures/q1_overall_trend.png ... q4_2020_vs_exam_years.png
    data/processed/summaries/*.csv   the exact numbers behind each figure,
                                     quoted in docs/findings.md
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # write image files only; no window needed

from src import analysis, plots  # noqa: E402

SUMMARY_DIR = Path(__file__).resolve().parents[1] / "data" / "processed" / "summaries"


def main() -> None:
    df = analysis.load_tidy()
    plots.apply_style()
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    tables = {
        "q1_overall_trend": analysis.overall_trend(df),
        "q1_candidate_mix": analysis.candidate_mix(df),
        "q2_gender_gaps": analysis.gender_gaps(df),
        "q2_overall_gender_gap": analysis.overall_gender_gap(df),
        "q3_group_pass_rates": analysis.group_pass_rates(df),
        "q4_candidate_type_trend": analysis.candidate_type_trend(df),
        "q4_compare_2020": analysis.compare_2020(df),
    }
    for name, table in tables.items():
        table.to_csv(SUMMARY_DIR / f"{name}.csv", index=False, float_format="%.2f",
                     lineterminator="\n")

    figures = {
        "q1_overall_trend.png": plots.plot_overall_trend(tables["q1_overall_trend"]),
        "q2_gender_gap.png": plots.plot_gender_gaps(tables["q2_gender_gaps"]),
        "q3_group_pass_rates.png": plots.plot_group_rates(tables["q3_group_pass_rates"]),
        "q4_2020_vs_exam_years.png": plots.plot_2020_comparison(
            tables["q4_candidate_type_trend"]),
    }
    for name, fig in figures.items():
        print("wrote", plots.save(fig, name).name)


if __name__ == "__main__":
    main()
