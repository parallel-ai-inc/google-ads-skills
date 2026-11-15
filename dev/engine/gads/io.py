"""Read Google Ads report exports (CSV, TSV, XLSX) into clean rows.

Google Ads downloads put a report title and a date range above the header,
append "Total" rows below the data, write "--" for empty cells and format
numbers with currency symbols, thousands separators and percent signs. This
module handles all of that and returns plain dictionaries.

Standard library only.
"""
import csv
import io as _io
import re
import zipfile
from xml.etree import ElementTree as ET

# Header text (lowercase, trimmed) -> canonical column name.
ALIASES = {
    "search term": "search_term",
    "match type": "match_type",
    "search terms match type": "match_type",
    "added/excluded": "added_excluded",
    "campaign": "campaign",
    "campaign name": "campaign",
    "ad group": "ad_group",
    "ad group name": "ad_group",
    "keyword": "keyword",
    "search keyword": "keyword",
    "source": "source",
    "day": "day",
    "date": "day",
    "campaign status": "campaign_status",
    "campaign state": "campaign_status",
    "campaign type": "campaign_type",
    "bid strategy type": "bid_strategy",
    "currency code": "currency",
    "currency": "currency",
    "budget": "budget",
    "clicks": "clicks",
    "impr.": "impressions",
    "impressions": "impressions",
    "cost": "cost",
    "conversions": "conversions",
    "conv. value": "conv_value",
    "conversion value": "conv_value",
    "search lost is (budget)": "lost_is_budget",
    "search lost is (rank)": "lost_is_rank",
    "search impr. share": "impr_share",
    "date & time": "changed_at",
    "user": "user",
    "changes": "changes",
    "account": "account",
}
NUMERIC = {
    "clicks", "impressions", "cost", "conversions", "conv_value", "budget",
}
PERCENT = {"lost_is_budget", "lost_is_rank", "impr_share"}
# A header row must contain at least this many known columns.
MIN_KNOWN_HEADERS = 3


def to_number(value):
    """'$1,234.50' -> 1234.5, '12.3%' -> 12.3, '--' or '' -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if text in ("", "--", "-", "—"):
        return None
    if text.startswith("<"):
        # Google writes "< 10%" when a share is below what it reports. That is
        # "small, exact value unknown", so no number is invented for it.
        return None
    negative = text.startswith("(") and text.endswith(")")
    text = re.sub(r"^>\s*", "", text.strip("()"))
    text = re.sub(r"[^0-9.,\-]", "", text)
    if text in ("", "-", ".", ","):
        return None
    if "," in text and "." in text:
        # The last separator is the decimal mark.
        if text.rfind(",") > text.rfind("."):
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", "")
    elif "," in text:
        head, _, tail = text.rpartition(",")
        # '1,234' is a thousands separator; '12,5' is a decimal comma.
        text = head.replace(",", "") + tail if len(tail) == 3 else head.replace(",", "") + "." + tail
    try:
        number = float(text)
    except ValueError:
        return None
    return -number if negative else number


def _decode(raw):
    for bom, encoding in ((b"\xff\xfe", "utf-16"), (b"\xfe\xff", "utf-16"), (b"\xef\xbb\xbf", "utf-8-sig")):
        if raw.startswith(bom):
            return raw.decode(encoding)
    for encoding in ("utf-8", "utf-16", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _grid_from_text(text):
    sample = "\n".join(text.splitlines()[:25])
    delimiter = "\t" if sample.count("\t") > sample.count(",") else ","
    return [row for row in csv.reader(_io.StringIO(text), delimiter=delimiter)]


def _grid_from_xlsx(path):
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as archive:
        shared = []
        if "xl/sharedStrings.xml" in archive.namelist():
            for item in ET.fromstring(archive.read("xl/sharedStrings.xml")).findall("m:si", ns):
                shared.append("".join(t.text or "" for t in item.iter("{%s}t" % ns["m"])))
        sheets = sorted(n for n in archive.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
        if not sheets:
            return []
        grid = []
        for row in ET.fromstring(archive.read(sheets[0])).iter("{%s}row" % ns["m"]):
            cells = {}
            for cell in row.findall("m:c", ns):
                letters = re.match(r"[A-Z]+", cell.get("r", "A")).group(0)
                index = 0
                for ch in letters:
                    index = index * 26 + (ord(ch) - 64)
                kind = cell.get("t")
                node = cell.find("m:v", ns)
                if kind == "s" and node is not None:
                    value = shared[int(node.text)]
                elif kind == "inlineStr":
                    value = "".join(t.text or "" for t in cell.iter("{%s}t" % ns["m"]))
                else:
                    value = node.text if node is not None else ""
                cells[index - 1] = value
            width = max(cells) + 1 if cells else 0
            grid.append([cells.get(i, "") for i in range(width)])
        return grid


def _canonical(header, aliases=ALIASES):
    return aliases.get(re.sub(r"\s+", " ", str(header).strip().lower()))


def read_report(path, extra_aliases=None, extra_numeric=(), extra_percent=()):
    """Return (meta, rows) for one Google Ads export.

    meta: title_rows, columns (canonical name -> original header), unknown
    headers, totals (label -> numeric values) and row_count.
    rows: one dict per data row, canonical keys, numbers already parsed.

    A skill that reads a report with columns this module does not know passes
    them in: extra_aliases maps a lowercase header to a canonical name, and
    extra_numeric and extra_percent name the canonical columns to parse as
    numbers.
    """
    aliases = dict(ALIASES)
    aliases.update({str(k).strip().lower(): v for k, v in (extra_aliases or {}).items()})
    numeric = NUMERIC | set(extra_numeric)
    percent = PERCENT | set(extra_percent)
    if str(path).lower().endswith(".xlsx"):
        grid = _grid_from_xlsx(path)
    else:
        with open(path, "rb") as handle:
            grid = _grid_from_text(_decode(handle.read()))
    grid = [[str(c).strip() for c in row] for row in grid if any(str(c).strip() for c in row)]

    header_index = None
    for index, row in enumerate(grid[:20]):
        if sum(1 for cell in row if _canonical(cell, aliases)) >= MIN_KNOWN_HEADERS:
            header_index = index
            break
    if header_index is None:
        raise ValueError(
            "I can't find a Google Ads header row in this file. Download the report "
            "again from Google Ads as CSV and keep the column headers."
        )

    header = grid[header_index]
    columns, unknown, positions = {}, [], {}
    for position, name in enumerate(header):
        key = _canonical(name, aliases)
        if key and key not in positions:
            positions[key] = position
            columns[key] = name
        elif name:
            unknown.append(name)

    rows, totals, total_rows = [], {}, []
    for raw in grid[header_index + 1:]:
        # A total row says "Total: ..." in its first cell, or in the second or
        # third when the report is segmented and a date comes first.
        # Google writes "Total: ..." on every total row. Matching the colon keeps a product
        # or campaign whose name starts with "Total" in the data.
        total_label = next((c for c in raw[:3] if c.lower().startswith("total:") or c.strip().lower() == "total"), None)
        record = {}
        for key, position in positions.items():
            value = raw[position] if position < len(raw) else ""
            if key in numeric or key in percent:
                record[key] = to_number(value)
            else:
                record[key] = "" if value in ("--", " --") else value
        if total_label:
            # A segmented report repeats each total for every date. Keep the date in the
            # label wherever it sits, so no total overwrites another.
            day = next((c for c in raw[:3] if c != total_label and _looks_like_date(c)), "")
            label = "%s, %s" % (total_label, day) if day else total_label
            values = {k: v for k, v in record.items() if k in numeric and v is not None}
            totals[label] = values
            total_rows.append({"label": total_label, "day": day, "values": values})
            continue
        rows.append(record)

    title_rows = [" ".join(c for c in row if c) for row in grid[:header_index]]
    meta = {
        "title_rows": title_rows,
        "date_range": _date_range(title_rows),
        "total_rows": total_rows,
        "columns": columns,
        "unknown_headers": unknown,
        "totals": totals,
        "row_count": len(rows),
    }
    return meta, rows


def _looks_like_date(text):
    return bool(re.match(r"^\d{4}-\d{2}-\d{2}$", text or "")) or bool(re.match(r"^[A-Za-z]{3,9} \d{1,2}, \d{4}$", text or ""))


def _date_range(title_rows):
    """The report's own date range from its title rows, as two ISO dates, or None."""
    from .dates import parse_day
    for row in title_rows:
        parts = [part.strip().strip('"') for part in re.split(r"\s+[-\u2013]\s+", row)]
        if len(parts) == 2:
            start, end = parse_day(parts[0]), parse_day(parts[1])
            if start and end:
                return [start.isoformat(), end.isoformat()]
    return None


def require(meta, needed, report_name, labels=None):
    """Stop with a plain message when a needed column is missing.

    labels maps a canonical name to the header as Google Ads shows it, for
    columns a skill added through extra_aliases.
    """
    missing = [n for n in needed if n not in meta["columns"]]
    if missing:
        known = {v: k.title() for k, v in ALIASES.items()}
        known.update(labels or {})
        names = ", ".join(sorted({known.get(m, m) for m in missing}))
        raise SystemExit(
            "I can't find these columns in the %s: %s. Download the report again "
            "with those columns added." % (report_name, names)
        )
