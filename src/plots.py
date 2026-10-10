"""Chart functions with one consistent style.

Each function takes a small DataFrame produced by src/analysis.py and
returns a matplotlib Figure. They draw; they do not compute findings.

Style rules used throughout:
- every chart has a title, labelled axes with units, and a source line;
- pass-rate axes run from 0 to 100 % so differences are not exaggerated;
- 2020 (no examination, promotion policy) is always drawn differently from
  exam years and never joined to them by a line;
- colours follow the entity (Regular is always blue, Private always orange),
  and identity is never shown by colour alone (direct labels or axis labels).
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

from src.analysis import GROUP_ORDER, LEVEL_NAMES

FIGURES_DIR = Path(__file__).resolve().parents[1] / "figures"

# Colours: a colour-blind-checked categorical palette (validated for adjacent
# pairs), plus neutral inks for text, grid and the "all candidates" reference.
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"
NO_EXAM_SHADE = "#f0efec"
CANDIDATE_COLOURS = {"Regular": "#2a78d6", "Private": "#eb6834", "All": INK_SECONDARY}
# One blue ramp, light -> dark, for the exam years 2015 -> 2019.
YEAR_COLOURS = {2015: "#86b6ef", 2016: "#5598e7", 2017: "#2a78d6", 2018: "#1c5cab",
                2019: "#104281"}

SOURCE_NOTE = ("Source: FBISE result gazettes, SSC-II and HSSC-II annual examinations "
               "(fbise.edu.pk). Details: data/SOURCES.md")


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.edgecolor": "#c3c2b7", "axes.labelcolor": INK_SECONDARY,
        "xtick.color": INK_SECONDARY, "ytick.color": INK_SECONDARY, "text.color": INK,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8,
        "lines.linewidth": 2, "lines.markersize": 6, "legend.frameon": False,
    })


def _finish(fig: plt.Figure, title: str, note: str = "") -> plt.Figure:
    fig.suptitle(title, x=0.01, ha="left", fontsize=13, fontweight="bold")
    width = int(fig.get_figwidth() * 15)  # roughly the characters per line at 8 pt
    footer = "\n".join([SOURCE_NOTE, *textwrap.wrap(note, width)])
    fig.text(0.01, 0.01, footer, fontsize=8, color=INK_MUTED, ha="left", va="bottom")
    return fig


def _shade_2020(ax: plt.Axes, label: bool) -> None:
    ax.axvspan(2019.5, 2020.5, color=NO_EXAM_SHADE, zorder=0)
    if label:
        ax.text(2020, 3, "2020:\nno exam,\npromotion\npolicy", ha="center", va="bottom",
                fontsize=7.5, color=INK_SECONDARY)


def _year_axis(ax: plt.Axes, years: list[int]) -> None:
    ax.set_xticks(years)
    ax.set_xlim(min(years) - 0.5, max(years) + 0.5)
    ax.grid(axis="x", visible=False)


def _line_with_2020_apart(ax, rows: pd.DataFrame, colour: str, label: str, **kwargs) -> None:
    """Draw exam years as a connected line and 2020 as a separate hollow marker.

    Missing years are reindexed to NaN so the line breaks instead of
    silently joining across the gap.
    """
    exam = rows[rows["assessment"] == "examination"].set_index("year")["pass_rate"]
    if not exam.empty:
        exam = exam.reindex(range(int(exam.index.min()), int(exam.index.max()) + 1))
        ax.plot(exam.index, exam.values, color=colour, marker="o", label=label, **kwargs)
    promo = rows[rows["assessment"] != "examination"]
    if not promo.empty:
        ax.plot(promo["year"], promo["pass_rate"], linestyle="none", marker="o",
                markerfacecolor=SURFACE, markeredgecolor=colour, markeredgewidth=2, markersize=8)


def plot_overall_trend(trend: pd.DataFrame) -> plt.Figure:
    """Q1: overall pass rate by year, SSC and HSSC side by side."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    years = list(range(2013, 2021))
    for ax, level in zip(axes, ["SSC", "HSSC"], strict=True):
        _shade_2020(ax, label=True)
        for population, colour in [("All candidates", CANDIDATE_COLOURS["All"]),
                                   ("Regular candidates", CANDIDATE_COLOURS["Regular"])]:
            rows = trend[(trend["level"] == level) & (trend["population"] == population)]
            _line_with_2020_apart(ax, rows, colour, population)
            last_exam = rows[rows["assessment"] == "examination"].iloc[-1]
            ax.annotate(population.split()[0], (last_exam["year"], last_exam["pass_rate"]),
                        xytext=(-4, 9 if population.startswith("Regular") else -14),
                        textcoords="offset points", ha="right", fontsize=8.5, color=colour)
        if level == "HSSC":
            ax.text(2019, 50, "2019:\nno gazette\nfound", ha="center", fontsize=7.5,
                    color=INK_MUTED)
        _year_axis(ax, years)
        ax.set_ylim(0, 100)
        ax.set_title(LEVEL_NAMES[level], loc="left")
        ax.set_xlabel("Examination year")
    axes[0].set_ylabel("Pass rate (% of candidates who appeared)")
    handles = [Line2D([], [], color=CANDIDATE_COLOURS["All"], marker="o", label="All candidates"),
               Line2D([], [], color=CANDIDATE_COLOURS["Regular"], marker="o",
                      label="Regular candidates only (2015 onward)"),
               Line2D([], [], color=INK_SECONDARY, marker="o", linestyle="none",
                      markerfacecolor=SURFACE, markersize=8, label="2020 (not an exam result)")]
    fig.legend(handles=handles, loc="upper right", ncol=3, fontsize=8.5,
               bbox_to_anchor=(0.99, 0.95))
    fig.subplots_adjust(top=0.80, bottom=0.2, wspace=0.08)
    return _finish(fig, "Q1. FBISE Part-II pass rates by year, 2013–2020",
                   "2013–14: overall rate from FBISE 'Result Statistics 2013–2017' (no breakdown "
                   "available). Breaks in a line are missing years, not zero.")


def _strip_panels(data: pd.DataFrame, value: str, xlabel: str, xlim: tuple[float, float],
                  marker_column: str | None, title: str, note: str,
                  zero_line: bool) -> plt.Figure:
    """Shared layout for Q2 and Q3: one row per group, one dot per exam year."""
    heights = [len(GROUP_ORDER["SSC"]), len(GROUP_ORDER["HSSC"])]
    fig, axes = plt.subplots(2, 1, figsize=(9, 6.4), sharex=True,
                             gridspec_kw={"height_ratios": heights})
    for ax, level in zip(axes, ["SSC", "HSSC"], strict=True):
        groups = [g for g in GROUP_ORDER[level] if g in set(data.loc[data["level"] == level,
                                                                      "group"])]
        for i, group in enumerate(groups):
            rows = data[(data["level"] == level) & (data["group"] == group)]
            y = len(groups) - 1 - i
            ax.hlines(y, rows[value].min(), rows[value].max(), color=GRID, linewidth=6,
                      zorder=1)
            for year, colour in YEAR_COLOURS.items():
                point = rows[rows["year"] == year]
                if not point.empty:
                    ax.plot(point[value], [y] * len(point), "o", color=colour, markersize=8,
                            markeredgecolor=SURFACE, markeredgewidth=1.5, zorder=3)
            if marker_column:
                pooled = rows[marker_column].iloc[0]
                ax.plot([pooled], [y], marker="|", color=INK, markersize=18,
                        markeredgewidth=2.5, zorder=4)
        ax.set_yticks(range(len(groups)))
        ax.set_yticklabels(list(reversed(groups)))
        ax.set_ylim(-0.6, len(groups) - 0.4)
        ax.grid(axis="y", visible=False)
        if zero_line:
            ax.axvline(0, color=INK_SECONDARY, linewidth=1, zorder=2)
        ax.set_title(LEVEL_NAMES[level] + " — regular candidates", loc="left")
    axes[-1].set_xlim(*xlim)
    axes[-1].set_xlabel(xlabel)
    handles = [Line2D([], [], marker="o", linestyle="none", color=c, markersize=8, label=str(y))
               for y, c in YEAR_COLOURS.items()]
    if marker_column:
        handles.append(Line2D([], [], marker="|", linestyle="none", color=INK, markersize=14,
                              markeredgewidth=2.5, label="2015–19 pooled"))
    fig.legend(handles=handles, loc="upper right", ncol=len(handles), fontsize=8.5,
               bbox_to_anchor=(0.99, 0.95), handletextpad=0.2, columnspacing=1.0)
    fig.subplots_adjust(top=0.84, bottom=0.2, left=0.2, hspace=0.35)
    return _finish(fig, title, note)


def plot_gender_gaps(gaps: pd.DataFrame) -> plt.Figure:
    """Q2: female minus male pass rate, per group, one dot per year."""
    data = gaps[gaps["comparable"]]
    excluded = gaps.loc[~gaps["comparable"], ["level", "group"]].drop_duplicates()
    note = "Gap = female pass rate minus male pass rate, in percentage points (pp). "
    note += "Right of 0: female rate higher. "
    if not excluded.empty:
        names = ", ".join(f"{r.level} {r.group}" for r in excluded.itertuples())
        note += f"Omitted (fewer than 100 candidates of one gender in some year): {names}."
    # Always include 0 (no gap) so the reference line is visible.
    xlim = (min(-5.0, data["gap_pp"].min() - 3), max(5.0, data["gap_pp"].max() + 3))
    return _strip_panels(data, "gap_pp", "Female minus male pass rate (percentage points)",
                         xlim, None,
                         "Q2. Gender gap in reported pass rates within subject groups, 2015–2019",
                         note, zero_line=True)


def plot_group_rates(rates: pd.DataFrame) -> plt.Figure:
    """Q3: pass rate per subject group, one dot per year plus the pooled rate."""
    data = rates[rates["comparable"]]
    excluded = rates.loc[~rates["comparable"], ["level", "group"]].drop_duplicates()
    note = ("Pooled = all passes ÷ all candidates who appeared over 2015–19 "
            "(HSSC: 2015–18; no 2019 gazette). ")
    if not excluded.empty:
        names = ", ".join(f"{r.level} {r.group}" for r in excluded.itertuples())
        note += f"Omitted (under 100 candidates or not present every year): {names}."
    return _strip_panels(data, "pass_rate", "Pass rate (% of candidates who appeared)", (0, 100),
                         "pooled_pass_rate",
                         "Q3. Reported pass rates by subject group, 2015–2019", note,
                         zero_line=False)


def plot_2020_comparison(trend: pd.DataFrame) -> plt.Figure:
    """Q4: regular / private / all candidates by year, 2020 drawn apart."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)
    years = list(range(2015, 2021))
    for ax, level in zip(axes, ["SSC", "HSSC"], strict=True):
        _shade_2020(ax, label=True)
        for candidate_type in ["Regular", "All", "Private"]:
            rows = trend[(trend["level"] == level) & (trend["candidate_type"] == candidate_type)]
            colour = CANDIDATE_COLOURS[candidate_type]
            _line_with_2020_apart(ax, rows, colour, candidate_type)
            first = rows.iloc[0]
            # "All" lies between the other two lines, so label it underneath.
            offset = -15 if candidate_type == "All" else 8
            ax.annotate(candidate_type, (first["year"], first["pass_rate"]),
                        xytext=(0, offset), textcoords="offset points", fontsize=8.5,
                        color=colour, ha="left")
        _year_axis(ax, years)
        ax.set_ylim(0, 100)
        ax.set_title(LEVEL_NAMES[level], loc="left")
        ax.set_xlabel("Examination year")
    axes[0].set_ylabel("Pass rate (% of candidates who appeared)")
    handles = [Line2D([], [], color=CANDIDATE_COLOURS[t], marker="o", label=f"{t} candidates")
               for t in ["Regular", "Private", "All"]]
    fig.legend(handles=handles, loc="upper right", ncol=3, fontsize=8.5,
               bbox_to_anchor=(0.99, 0.95))
    fig.subplots_adjust(top=0.80, bottom=0.2, wspace=0.08)
    return _finish(fig, "Q4. 2020 (no examination) compared with exam years, by candidate type",
                   "Hollow markers: 2020 results prepared under the Federal Government promotion "
                   "policy (HSSC-II 2020 gazette, p.1), not an exam. HSSC 2019 missing.")


def save(fig: plt.Figure, name: str) -> Path:
    FIGURES_DIR.mkdir(exist_ok=True)
    path = FIGURES_DIR / name
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
