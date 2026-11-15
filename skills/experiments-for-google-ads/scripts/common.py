"""Loading, names, periods and totals for the experiments skill scripts.

The scripts import this module; it is never run on its own.
"""
import datetime as dt
import difflib
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics  # noqa: E402

# Columns this skill reads beyond the engine's own. Google Ads names first,
# then the plain names a booking system or CRM export tends to use.
ALIASES = {
    "budget name": "budget_name",
    "budget type": "budget_type",
    "status": "serving_status",
    "search lost is (budget)": "lost_is_budget",
    "search lost top is (budget)": "lost_top_is_budget",
    "region": "region", "region (user location)": "region", "region (matched)": "region",
    "region (physical location)": "region", "state": "region", "province": "region",
    "city": "city", "city (user location)": "city", "city (matched)": "city", "city (physical location)": "city",
    "metro area": "metro", "metro area (user location)": "metro", "metro area (matched)": "metro", "dma region": "metro",
    "country/territory": "country", "country/territory (user location)": "country", "country/territory (matched)": "country",
    "location": "location", "user location": "location", "matched location": "location", "most specific location": "location",
    "postal code": "postal", "postal code (user location)": "postal", "zip code": "postal",
    "leads": "leads", "sales": "sales", "orders": "orders", "revenue": "revenue", "bookings": "bookings", "jobs": "jobs",
}
NUMERIC = ("leads", "sales", "orders", "revenue", "bookings", "jobs")
PERCENT = ("lost_top_is_budget",)
GROUP_COLUMNS = ("campaign", "region", "city", "metro", "country", "location", "postal")
LABELS = {"day": "Day", "campaign": "Campaign", "cost": "Cost", "conversions": "Conversions", "conv_value": "Conv. value",
          "clicks": "Clicks", "impressions": "Impr.", "leads": "Leads", "sales": "Sales", "orders": "Orders",
          "revenue": "Revenue", "bookings": "Bookings", "jobs": "Jobs", "campaign_status": "Campaign status"}
METRIC_NAMES = {"conversions": "conversions", "conv_value": "conversion value", "clicks": "clicks", "cost": "cost",
                "impressions": "impressions", "leads": "leads", "sales": "sales", "orders": "orders",
                "revenue": "revenue", "bookings": "bookings", "jobs": "jobs"}
COUNT_METRICS = ("conversions", "clicks", "impressions", "leads", "orders", "bookings", "jobs", "sales")


def load(path, report_name, extra_aliases=None, numeric=(), percent=()):
    """io.read_report with this skill's columns, and a plain sentence instead of a stack trace."""
    if not os.path.isfile(path):
        raise SystemExit("I can't find the file %s. Check the path, or download the %s again." % (path, report_name))
    aliases = dict(ALIASES)
    aliases.update(extra_aliases or {})
    try:
        return io.read_report(path, aliases, tuple(NUMERIC) + tuple(numeric), tuple(PERCENT) + tuple(percent))
    except ValueError as error:
        raise SystemExit(str(error))
    except (OSError, UnicodeError, zipfile.BadZipFile):
        raise SystemExit("I can't read %s. Download the %s again from Google Ads as CSV." % (path, report_name))


def require(meta, needed, report_name):
    io.require(meta, needed, report_name, labels=LABELS)


def split_names(values):
    """--test "A;B" --test C -> ["A", "B", "C"]."""
    names = []
    for value in values or []:
        names += [part.strip() for part in value.split(";") if part.strip()]
    return names


def match_names(wanted, available, what):
    """Check each name against the report. Refuse a wrong one with the nearest names."""
    lookup = {name.lower(): name for name in available}
    found = []
    for name in wanted:
        if name.lower() in lookup:
            found.append(lookup[name.lower()])
            continue
        near = difflib.get_close_matches(name, sorted(available), n=3, cutoff=0.5)
        hint = " Did you mean: %s?" % ", ".join(near) if near else " The report has: %s." % ", ".join(sorted(available)[:12])
        raise SystemExit("\"%s\" is not a %s in the report.%s" % (name, what, hint))
    return found


def group_column(meta, rows, wanted):
    """The column whose values hold the names the person gave (campaign, region, city...)."""
    present = [c for c in GROUP_COLUMNS if c in meta["columns"]]
    if not present:
        return None
    if not wanted:
        return present[0]
    lowered = [w.lower() for w in wanted]
    for column in present:
        values = {str(r.get(column, "")).lower() for r in rows}
        if all(w in values for w in lowered):
            return column
    for column in present:
        values = {str(r.get(column, "")).lower() for r in rows}
        if any(w in values for w in lowered):
            return column
    return present[0]


def span(text):
    start, _, end = (text or "").partition(":")
    a, b = dates.parse_day(start), dates.parse_day(end)
    if not a or not b or b < a:
        raise SystemExit("Write a period as START:END, for example 2026-10-22:2026-11-11.")
    return a, b


def daily_series(rows, column=None, names=None, metric="conversions", extra=()):
    """{day: {metric: total, ...}} for the rows whose group column matches one of the names."""
    keep = {n.lower() for n in names} if names else None
    series = {}
    for row in rows:
        day = dates.parse_day(row.get("day"))
        if not day:
            continue
        if keep is not None and str(row.get(column, "")).lower() not in keep:
            continue
        slot = series.setdefault(day, {})
        for key in sorted({metric} | set(extra)):
            slot[key] = slot.get(key, 0.0) + (row.get(key) or 0.0)
    return series


def fill_days(series, first, last, keys):
    """Every day from first to last, with zeros where the report has no row."""
    out, day = [], first
    while day <= last:
        values = series.get(day, {})
        out.append((day, {k: values.get(k, 0.0) for k in keys}))
        day += dt.timedelta(days=1)
    return out


def reconcile(meta, rows, keys=("cost", "conversions")):
    """Check the rows add up to the file's own total row.

    Prefers "Total: Filtered campaigns" (the rows a filtered download holds),
    then "Total: Account". In a report segmented by Day the dated total rows
    are added up. Returns what was compared and whether it matches.
    """
    keys = [k for k in keys if k in meta["columns"]]
    sums = {k: sum((r.get(k) or 0.0) for r in rows) for k in keys}
    result = {"checked": False, "matches": None, "rows_total": sums, "file_total": None, "label": None}
    for label in ("total: filtered campaigns", "total: account", "total"):
        found = [t for t in meta["total_rows"] if t["label"].strip().lower() == label]
        if not found:
            continue
        undated = [t for t in found if not t["day"]]
        chosen = undated[:1] or [t for t in found if t["day"]]
        file_total = {k: sum((t["values"].get(k) or 0.0) for t in chosen) for k in keys}
        tolerance = 0.006 * max(len(rows), 1) + 0.01
        result.update({"checked": True, "label": chosen[0]["label"] + (" (added up over %d days)" % len(chosen) if not undated else ""),
                       "file_total": file_total, "matches": all(abs(sums[k] - file_total[k]) <= tolerance for k in keys)})
        return result
    return result


def reconcile_line(check, name="the file"):
    if not check["checked"]:
        return "%s has no account total row, so the rows could not be checked against one." % name.capitalize()
    parts = ", ".join("%s %s" % (LABELS.get(k, k), "{:,.2f}".format(v)) for k, v in check["rows_total"].items())
    if check["matches"]:
        return "The rows add up to %s's own total (%s): %s." % (name, check["label"], parts)
    other = ", ".join("%s %s" % (LABELS.get(k, k), "{:,.2f}".format(v)) for k, v in check["file_total"].items())
    return "The rows (%s) do NOT add up to %s's own total (%s: %s). Some rows may be filtered out or the file cut short." % (
        parts, name, check["label"], other)


def signed(value, digits=1):
    return "n/a" if value is None else ("+" if value >= 0 else "") + metrics.pct(value, digits)


def number(value, digits=2):
    return "n/a" if value is None else "{:,.{d}f}".format(value, d=digits)


def currency_line(rows):
    codes = sorted({(r.get("currency") or "").strip() for r in rows if (r.get("currency") or "").strip()})
    return ("Amounts are in %s." % codes[0]) if len(codes) == 1 else ""


def finish(out, stem, text, payload, book):
    from gads import outputs
    outputs.write_json(os.path.join(out, stem + ".json"), payload)
    book.save(os.path.join(out, stem + ".xlsx"))
    with open(os.path.join(out, stem + ".md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote %s.json, %s.xlsx and %s.md to %s" % (stem, stem, stem, out))
