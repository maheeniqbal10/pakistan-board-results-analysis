"""Download FBISE result publications and extract their aggregate tables.

Inputs
    The official PDFs listed in ``SOURCES`` below (all hosted on fbise.edu.pk).

Outputs
    data/raw/_downloads/*.pdf          the original PDFs, unchanged (git-ignored)
    data/raw/source_manifest.csv       URL, size and SHA-256 of every PDF we used
    data/raw/fbise_gazette_all_areas.csv
        the "Salient Features of Result - All Areas" table from each result
        gazette, one row per printed line, labels exactly as printed
    data/raw/fbise_result_statistics_2013_2017.csv
        the tables from FBISE's "Result Statistics 2013-2017" summary PDF

Privacy
    A result gazette is one big PDF. Its first pages hold board-wide aggregate
    tables; later pages list position holders and institution results, which
    include student names and roll numbers. This module only ever reads the
    single page whose title is "SALIENT FEATURES OF RESULT ALL AREAS" (searched
    for in the first few pages). No other page is parsed or saved, and the PDFs
    themselves are never committed to git.

Run with:  python -m src.collect            (downloads missing PDFs, then extracts)
           python -m src.collect --offline  (extract only; fail if a PDF is missing)
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import re
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DOWNLOAD_DIR = RAW_DIR / "_downloads"
MANIFEST_PATH = RAW_DIR / "source_manifest.csv"
GAZETTE_CSV = RAW_DIR / "fbise_gazette_all_areas.csv"
STATISTICS_CSV = RAW_DIR / "fbise_result_statistics_2013_2017.csv"

FBISE = "https://www.fbise.edu.pk"


@dataclass(frozen=True)
class Source:
    source_id: str
    url: str
    kind: str  # "gazette" or "statistics"
    level: str = ""  # "SSC" (Matric) or "HSSC" (Intermediate); blank for statistics
    part: str = ""  # "II" = the final-year (certificate) examination
    year: int | None = None

    @property
    def path(self) -> Path:
        return DOWNLOAD_DIR / f"{self.source_id}.pdf"


# Every source used in the analysis. Each one is described in data/SOURCES.md.
# Only 1st-annual (main) Part-II examinations are used; supplementary exams
# have a very different candidate mix (mostly repeaters) and are excluded.
SOURCES: list[Source] = [
    Source("fbise_result_statistics_2013_2017",
           f"{FBISE}/news%20update%20notification/RESULT%20STATISTICS.pdf", "statistics"),
    Source("fbise_ssc2_2015", f"{FBISE}/notifications/ssc/SSC-II-A-RESULT%202015.pdf",
           "gazette", "SSC", "II", 2015),
    Source("fbise_ssc2_2016", f"{FBISE}/notifications/ssc/SSC-II-A-RESULT%202016.pdf",
           "gazette", "SSC", "II", 2016),
    Source("fbise_ssc2_2017", f"{FBISE}/notifications/ssc/SSC-II-A-RESULT%202017.pdf",
           "gazette", "SSC", "II", 2017),
    Source("fbise_ssc2_2018",
           f"{FBISE}/notifications/ssc/Result%20Gazette%20SSC-II%20A%202018.pdf",
           "gazette", "SSC", "II", 2018),
    Source("fbise_ssc2_2019",
           f"{FBISE}/notifications/ssc/Result%20Gazette%20SSC%20II%202019.pdf",
           "gazette", "SSC", "II", 2019),
    Source("fbise_ssc2_2020",
           f"{FBISE}/notifications/ssc/Result%20Gazette%20SSC%20A%202020.pdf",
           "gazette", "SSC", "II", 2020),
    Source("fbise_hssc2_2015",
           f"{FBISE}/notifications/hssc/Result%20gazette%20Hssc-II%202015%20A.pdf",
           "gazette", "HSSC", "II", 2015),
    Source("fbise_hssc2_2016",
           f"{FBISE}/notifications/hssc/Result%20gazette%20Hssc-II%202016%20A.pdf",
           "gazette", "HSSC", "II", 2016),
    Source("fbise_hssc2_2017",
           f"{FBISE}/notifications/hssc/Result%20gazette%20Hssc-II%202017%20A.pdf",
           "gazette", "HSSC", "II", 2017),
    Source("fbise_hssc2_2018",
           f"{FBISE}/notifications/hssc/Result-Gazette-HSSC-II-A-2018.pdf",
           "gazette", "HSSC", "II", 2018),
    # No HSSC-II 1st-annual 2019 gazette could be found on fbise.edu.pk, so
    # 2019 is missing for HSSC (see data/SOURCES.md). It is NOT filled in.
    Source("fbise_hssc2_2020",
           f"{FBISE}/notifications/hssc/Result%20Gazette%20HSSC%20A%202020.pdf",
           "gazette", "HSSC", "II", 2020),
]

MANIFEST_FIELDS = ["source_id", "url", "file", "bytes", "sha256", "first_downloaded"]


# --------------------------------------------------------------------------
# Downloading
# --------------------------------------------------------------------------

def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_manifest() -> dict[str, dict[str, str]]:
    if not MANIFEST_PATH.exists():
        return {}
    with MANIFEST_PATH.open(newline="", encoding="utf-8") as f:
        return {row["source_id"]: row for row in csv.DictReader(f)}


def write_manifest(manifest: dict[str, dict[str, str]]) -> None:
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, lineterminator="\n")
        writer.writeheader()
        for source in SOURCES:  # stable order
            if source.source_id in manifest:
                writer.writerow(manifest[source.source_id])


def download(source: Source) -> None:
    """Stream one PDF to disk, checking the byte count the server promised.

    The government server is slow and connections drop, so the file is written
    to a .part file first and only renamed once it is complete.
    """
    import requests  # imported here so --offline works without network libs

    DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    tmp = source.path.with_suffix(".part")
    with requests.get(source.url, stream=True, timeout=120,
                      headers={"User-Agent": "Mozilla/5.0 (research; aggregate statistics)"}) as r:
        r.raise_for_status()
        expected = int(r.headers.get("Content-Length", 0))
        with tmp.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)
    got = tmp.stat().st_size
    if expected and got != expected:
        tmp.unlink()
        raise OSError(f"{source.source_id}: expected {expected} bytes, got {got}")
    tmp.replace(source.path)


def ensure_downloaded(offline: bool) -> None:
    """Make sure every source PDF is present and matches the manifest checksum."""
    manifest = read_manifest()
    for source in SOURCES:
        if not source.path.exists():
            if offline:
                raise FileNotFoundError(
                    f"{source.path} is missing; run without --offline to download it")
            print(f"downloading {source.source_id} ...", flush=True)
            download(source)

        checksum = sha256_of(source.path)
        known = manifest.get(source.source_id)
        if known is None:
            manifest[source.source_id] = {
                "source_id": source.source_id,
                "url": source.url,
                "file": source.path.name,
                "bytes": str(source.path.stat().st_size),
                "sha256": checksum,
                "first_downloaded": date.today().isoformat(),
            }
        elif known["sha256"] != checksum:
            # The publisher changed the file, or the download is corrupt. Either
            # way the extracted numbers can no longer be trusted blindly.
            raise ValueError(
                f"{source.source_id}: SHA-256 differs from data/raw/source_manifest.csv. "
                "Delete the PDF and re-download; if it still differs, the source "
                "changed and the extraction must be re-checked by hand.")
    write_manifest(manifest)


# --------------------------------------------------------------------------
# Extracting the "Salient Features - All Areas" table from a gazette
# --------------------------------------------------------------------------

ALL_AREAS_TITLE = "SALIENT FEATURES OF RESULT ALL AREAS"
PAGES_TO_SEARCH = 15  # the table is always near the front of the gazette

# Column order printed in the gazette table header.
COUNT_COLUMNS = ["enrolled", "absent", "appeared", "result_later", "ufm", "fail", "passed",
                 "grade_a1", "grade_a", "grade_b", "grade_c", "grade_d", "grade_e"]
GAZETTE_FIELDS = (["source_id", "year", "level", "part", "page", "line_no", "candidate_type",
                   "group", "gender", "row_type"]
                  + COUNT_COLUMNS + ["pass_pct_published", "gpa_published"])

# A data line: optional leading group number, a label, 13 integers, then the
# pass percentage and GPA, e.g.
#   "MALE 1161 11 1150 0 2 571 577 12 32 113 221 188 11 50.17 1.51"
#   "1 Humanities Total : 7325 26 7299 0 2 2065 5232 40 400 1379 2201 1174 38 71.68 2.29"
DATA_LINE = re.compile(
    r"^(?:\d+\s+)?(?P<label>[A-Za-z][A-Za-z.\-/ ]*?)\s*:?\s+"
    r"(?P<counts>\d+(?:\s+\d+){12})\s+(?P<pct>\d+\.\d+)\s+(?P<gpa>\d+\.\d+)$"
)


def normalise_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def find_all_areas_page(pdf) -> int:
    """Return the 0-based index of the All Areas page; raise if not found."""
    for i, page in enumerate(pdf.pages[:PAGES_TO_SEARCH]):
        text = normalise_spaces(page.extract_text() or "").upper()
        if ALL_AREAS_TITLE in text:
            return i
    raise ValueError(f"'{ALL_AREAS_TITLE}' not found in the first {PAGES_TO_SEARCH} pages")


def parse_all_areas_text(text: str) -> list[dict]:
    """Turn the text of one All Areas page into one dict per printed data line.

    The table is laid out like this (group label comes AFTER its gender rows):

        REGULAR CANDIDATES
        Male   ...
        Female ...
        1 SCIENCE Total : ...      <- closes the Male/Female rows above
        ...
        Total : ...                <- all regular candidates
        EX/PRIVATE CANDIDATES
        ...
        Grand Total : ...          <- everyone

    Labels are kept exactly as printed; src/clean.py standardises them.
    """
    rows: list[dict] = []
    candidate_type: str | None = None
    pending: list[dict] = []  # gender rows waiting for their group label

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = normalise_spaces(raw_line)
        upper = line.upper()
        if upper.startswith("REGULAR CANDIDATES"):
            candidate_type = "REGULAR CANDIDATES"
            continue
        if "PRIVATE CANDIDATES" in upper:
            candidate_type = "EX/PRIVATE CANDIDATES"
            continue

        match = DATA_LINE.match(line)
        if not match:
            continue  # headings, page numbers, group index digits, etc.

        label = normalise_spaces(match["label"]).rstrip(" :")
        counts = [int(x) for x in match["counts"].split()]
        record = {
            "line_no": line_no,
            **dict(zip(COUNT_COLUMNS, counts, strict=True)),
            "pass_pct_published": match["pct"],  # keep the printed text exactly
            "gpa_published": match["gpa"],
        }
        label_upper = label.upper()

        if label_upper in ("MALE", "FEMALE"):
            if candidate_type is None:
                raise ValueError(f"line {line_no}: data row before any candidate heading")
            pending.append({**record, "candidate_type": candidate_type, "gender": label,
                            "row_type": "gender"})
        elif label_upper == "GRAND TOTAL":
            rows.append({**record, "candidate_type": "ALL", "group": "ALL", "gender": "ALL",
                         "row_type": "grand_total"})
        elif label_upper == "TOTAL":
            if pending:
                raise ValueError(f"line {line_no}: gender rows without a group total")
            rows.append({**record, "candidate_type": candidate_type, "group": "ALL",
                         "gender": "ALL", "row_type": "candidate_type_total"})
        elif label_upper.endswith(" TOTAL"):
            group = label[: -len(" TOTAL")].strip()
            for gender_row in pending:
                rows.append({**gender_row, "group": group})
            pending = []
            rows.append({**record, "candidate_type": candidate_type, "group": group,
                         "gender": "ALL", "row_type": "group_total"})
        else:
            raise ValueError(f"line {line_no}: unrecognised row label {label!r}")

    if pending:
        raise ValueError("table ended with gender rows that have no group total")
    if not any(r["row_type"] == "grand_total" for r in rows):
        raise ValueError("no 'Grand Total' row found; the page layout may have changed")
    return rows


def extract_gazette(source: Source) -> list[dict]:
    import pdfplumber

    with pdfplumber.open(source.path) as pdf:
        index = find_all_areas_page(pdf)
        text = pdf.pages[index].extract_text() or ""

    header = normalise_spaces(text).upper()
    expected = f"{source.level}-{source.part} ANNUAL EXAMINATION {source.year}"
    if expected not in header:
        raise ValueError(f"{source.source_id}: page header does not mention {expected!r}")

    rows = parse_all_areas_text(text)
    meta = {"source_id": source.source_id, "year": source.year, "level": source.level,
            "part": source.part, "page": index + 1}
    return [{**meta, **row} for row in rows]


# --------------------------------------------------------------------------
# Extracting the 2013-2017 "Result Statistics" summary PDF
# --------------------------------------------------------------------------

STATISTICS_FIELDS = ["source_id", "page", "year", "level", "part", "metric", "value"]


def parse_statistics_pages(page_texts: list[str]) -> list[dict]:
    """Parse the three small tables in the Result Statistics PDF.

    Page 1: pass % by year for SSC-I, SSC-II, HSSC-I, HSSC-II.
    Page 2: HSSC appeared and passed by year. Page 3: same for SSC.
    The page-2/3 counts are not labelled by part; they appear to cover Part I
    and Part II together (see DECISIONS.md ADR-003), so part is recorded as
    "I+II" rather than guessed.
    """
    rows: list[dict] = []
    year_line = re.compile(r"^(20\d\d)\s+(.+)$")

    def table_lines(text: str) -> list[str]:
        # Each page also has a chart whose x-axis prints "2013 2014 2015 ...",
        # which looks like a data row. Only lines after the table's "Year ..."
        # header are real data.
        lines = [ln.strip() for ln in text.splitlines()]
        starts = [i for i, ln in enumerate(lines) if ln.startswith("Year ")]
        if len(starts) != 1:
            raise ValueError("expected exactly one 'Year ...' table header on the page")
        return lines[starts[0] + 1:]

    for line in table_lines(page_texts[0]):
        m = year_line.match(line)
        if m:
            values = m[2].split()
            if len(values) != 4:
                raise ValueError(f"page 1: expected 4 values in {line!r}")
            for (level, part), value in zip(
                [("SSC", "I"), ("SSC", "II"), ("HSSC", "I"), ("HSSC", "II")], values,
                strict=True,
            ):
                rows.append({"page": 1, "year": int(m[1]), "level": level, "part": part,
                             "metric": "pass_pct", "value": value})

    for page_no, level in ((2, "HSSC"), (3, "SSC")):
        text = page_texts[page_no - 1]
        if f"{level} RESULT STATISTICS" not in text.upper():
            raise ValueError(f"page {page_no}: expected a {level} RESULT STATISTICS title")
        for line in table_lines(text):
            m = year_line.match(line)
            if m:
                values = m[2].split()
                if len(values) != 2:
                    raise ValueError(f"page {page_no}: expected 2 values in {line!r}")
                for metric, value in zip(("appeared", "passed"), values, strict=True):
                    rows.append({"page": page_no, "year": int(m[1]), "level": level,
                                 "part": "I+II", "metric": metric, "value": value})
    return rows


def extract_statistics(source: Source) -> list[dict]:
    import pdfplumber

    with pdfplumber.open(source.path) as pdf:
        texts = [page.extract_text() or "" for page in pdf.pages]
    rows = parse_statistics_pages(texts)
    return [{"source_id": source.source_id, **row} for row in rows]


# --------------------------------------------------------------------------

def write_csv(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--offline", action="store_true",
                        help="do not download; use PDFs already in data/raw/_downloads/")
    args = parser.parse_args(argv)

    ensure_downloaded(offline=args.offline)

    gazette_rows: list[dict] = []
    statistics_rows: list[dict] = []
    for source in SOURCES:
        if source.kind == "gazette":
            rows = extract_gazette(source)
            gazette_rows.extend(rows)
            print(f"{source.source_id}: {len(rows)} rows from page {rows[0]['page']}")
        else:
            rows = extract_statistics(source)
            statistics_rows.extend(rows)
            print(f"{source.source_id}: {len(rows)} values")

    write_csv(GAZETTE_CSV, GAZETTE_FIELDS, gazette_rows)
    write_csv(STATISTICS_CSV, STATISTICS_FIELDS, statistics_rows)
    print(f"wrote {GAZETTE_CSV.relative_to(ROOT)} and {STATISTICS_CSV.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
