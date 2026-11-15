#!/usr/bin/env python3
"""Turn a saved search result into a CSV in the layout of a Google Ads download:
the report name row, the date range row, the header with the names the Google
Ads interface uses, the rows, and a total row. Money comes out of micros,
ratios become percentages, and API values become the interface's words.
Then it reads the file back with the pack's own reader and checks it.

    python3 scripts/convert.py --query WORK/search-terms.query.json --out OUTPUT [--result FILE] [--currency USD]

The query file comes from queries.py. The result is read from the path the
query file names, unless --result is given. Writes OUTPUT/<report file>.csv,
OUTPUT/<report>.conversion.json and OUTPUT/<report>.conversion.md, and prints
the summary.
"""
import argparse
import csv
import datetime as dt
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livecore as lc  # noqa: E402
from gads import io, outputs  # noqa: E402

NUMERIC = ("int", "micros", "decimal", "percent", "share", "lost")
PARENT_WORDS = {"campaign.status": "Campaign", "ad_group.status": "Ad group"}


def present(rows, field):
    return any(field in row and row[field] not in (None, "") for row in rows)


def value_of(row, field, kind):
    """A raw number for a numeric kind, with a metric that is absent read as 0:
    results written as JSON leave out fields whose value is zero."""
    raw = row.get(field)
    if kind in NUMERIC:
        value = lc.number(raw)
        if value is None and field.startswith("metrics.") and (kind in ("int", "decimal") or field == "metrics.cost_micros"):
            return 0.0
        if value is not None and kind == "micros":
            return value / 1000000.0
        return value
    return raw


def keyword_cell(row, column):
    text = str(row.get(column["field"]) or "")
    match = lc.enum_name(row.get(column["inputs"][0])) or ""
    if not text:
        return lc.EMPTY
    return "[%s]" % text if match == "EXACT" else '"%s"' % text if match == "PHRASE" else text


def parents_cell(row, column):
    for field in [column["field"]] + column.get("inputs", []):
        state = lc.enum_name(row.get(field)) or ""
        if state in ("PAUSED", "REMOVED"):
            return "%s %s" % (PARENT_WORDS.get(field, "Parent"), state.lower())
    return lc.EMPTY


def ad_name_cell(row, column):
    headlines = row.get(column["field"])
    if isinstance(headlines, str):
        try:
            headlines = json.loads(headlines)
        except ValueError:
            headlines = [headlines]
    for item in headlines or []:
        text = item.get("text") if isinstance(item, dict) else item
        if text:
            return str(text)
    name = row.get(column["inputs"][0])
    if name:
        return str(name)
    ad_id = row.get(column["inputs"][1])
    return "Ad ID %s" % ad_id if ad_id not in (None, "") else lc.EMPTY


def first_cell(value):
    if isinstance(value, str):
        try:
            value = json.loads(value) if value.startswith("[") else [value]
        except ValueError:
            value = [value]
    for item in value or []:
        if item:
            return str(item)
    return lc.EMPTY


def change_cell(row, column):
    kind = lc.enum_words(column["field"], row.get(column["field"]))
    action = lc.enum_words(column["inputs"][0], row.get(column["inputs"][0]))
    text = "%s %s" % (kind if kind != lc.EMPTY else "Item", action.lower() if action != lc.EMPTY else "changed")
    fields = lc.readable_fields(row.get(column["inputs"][1]))
    return text + (": " + ", ".join(fields) if fields else "")


def lookup_cell(value, names):
    if value in (None, ""):
        return ""
    if value in names:
        return names[value]
    return "ID %s" % str(value).rstrip("/").split("/")[-1]


def auto_cell(value, field, unmapped):
    if value is None or value == "":
        return lc.EMPTY
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, (int, float)):
        return ("%d" % value) if float(value).is_integer() else ("%.2f" % value)
    if isinstance(value, list):
        return "; ".join(str(v.get("text", v)) if isinstance(v, dict) else str(v) for v in value) or lc.EMPTY
    if re.match(r"^[A-Z][A-Z0-9_]*$", str(value)):
        return lc.enum_words(field, value, unmapped)
    return str(value)


def format_number(kind, value, field):
    if value is None:
        return lc.EMPTY
    if kind == "int":
        return lc.fmt_int(value)
    if kind in ("micros", "decimal"):
        return lc.fmt_money(value)
    if kind == "share" and abs(value - 0.0999) < 1e-9:
        return "< 10%"
    if kind == "lost" and abs(value - 0.9001) < 1e-9:
        return "> 90%"
    return lc.fmt_pct(value)


def cell(row, column, names, joined, unmapped):
    kind, field = column["kind"], column["field"]
    if column.get("join"):
        return format_number(kind, joined.get(field, 0.0), field)
    if kind in NUMERIC:
        return format_number(kind, value_of(row, field, kind), field)
    if kind == "enum":
        return lc.enum_words(field, row.get(field), unmapped)
    if kind == "keyword":
        return keyword_cell(row, column)
    if kind == "parents":
        return parents_cell(row, column)
    if kind == "ad_name":
        return ad_name_cell(row, column)
    if kind == "first":
        return first_cell(row.get(field))
    if kind == "lookup":
        return lookup_cell(row.get(field), names)
    if kind == "change":
        return change_cell(row, column)
    if kind == "datetime":
        return lc.fmt_datetime(row.get(field))
    if kind == "primary":
        return "Primary action" if str(row.get(field)).lower() in ("true", "1") else "Secondary action"
    if kind == "days":
        days = lc.number(row.get(field))
        return ("%d day" if days == 1 else "%d days") % days if days else lc.EMPTY
    if kind == "auto":
        return auto_cell(row.get(field), field, unmapped)
    value = row.get(field)
    if isinstance(value, list):
        value = "; ".join(str(v) for v in value)
    return lc.EMPTY if value in (None, "") else str(value)


def name_map(join_rows):
    names = {}
    for rows in join_rows.values():
        for row in rows:
            for key, value in row.items():
                if key.endswith(".resource_name") and value:
                    name = row.get(key[: -len("resource_name")] + "name")
                    if name:
                        names[value] = str(name)
    return names


def regroup(rows, fields):
    """A field that is itself an object (such as changed_fields as {"paths": [...]}) was flattened
    into its parts. Put it back together under the field's own name."""
    for row in rows:
        for field in fields:
            if field not in row:
                parts = {k[len(field) + 1:]: v for k, v in row.items() if k.startswith(field + ".")}
                if parts:
                    row[field] = parts
    return rows


def match_query(rows, params, what, path):
    """Refuse a saved result that answers a different search than the query file holds."""
    if not rows:
        return
    fields = set(params["fields"])
    seen = set()
    for row in rows:
        seen.update(row)
    extra = sorted(k for k in seen - fields
                   if not k.endswith(".resource_name") and not any(k.startswith(f + ".") for f in fields))
    resource = params["resource"]
    own = [f for f in fields if f.split(".")[0] == resource]
    if extra:
        problem = "it holds fields that search did not ask for: %s" % ", ".join(extra[:6])
    elif own and not any(f in seen for f in own):
        problem = "it holds none of the %s fields that search asked for" % resource
    else:
        return
    raise lc.Refusal("The saved result at %s does not match the %s search (%s, from %s): %s. Save the result of that "
                     "search, run with the parameters queries.py printed, to that path, then run this again." % (
                         path, what, resource, ", ".join(params["fields"][:3]) + (", ..." if len(params["fields"]) > 3 else ""), problem))


def slug(header):
    return re.sub(r"[^a-z0-9]+", "_", header.lower()).strip("_") or "column"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--query", required=True, help="the query file queries.py wrote")
    parser.add_argument("--result", help="the saved search result. Default: the path in the query file")
    parser.add_argument("--out", required=True, help="folder for the CSV and the summary")
    parser.add_argument("--currency", help="the account's currency code, such as USD, from the account check")
    args = parser.parse_args()

    if not os.path.isfile(args.query):
        raise lc.Refusal("I can't find the query file %s. Run scripts/queries.py first." % args.query)
    with open(args.query, encoding="utf-8") as handle:
        query = json.load(handle)
    if query.get("kind") not in ("report", "custom"):
        raise lc.Refusal("This query file is the account check. Read its result directly; there is nothing to convert.")
    if args.currency and not re.match(r"^[A-Z]{3}$", args.currency):
        raise lc.Refusal("Write the currency as its three letter code, such as USD.")
    params = query["parameters"]
    fields = params["fields"]
    query_dir = os.path.dirname(os.path.abspath(args.query))
    result_path = args.result or os.path.join(query_dir, query["result"])
    rows = regroup(lc.load_result(result_path, fields), fields)
    match_query(rows, params, query["report"], result_path)
    join_rows = {}
    for join in query.get("joins", []):
        join_path = os.path.join(query_dir, join["result"])
        join_rows[join["name"]] = regroup(lc.load_result(join_path, join["parameters"]["fields"]), join["parameters"]["fields"])
        match_query(join_rows[join["name"]], join["parameters"], join["name"], join_path)
    warnings, notes, unmapped = [], [], set()

    if rows and not any(any(f in row for f in fields) for row in rows):
        raise lc.Refusal("The saved result does not hold the fields this report asked for. Run the search again with the parameters queries.py printed, unchanged, and save the whole result.")
    for field in query.get("needs", []):
        if rows and not present(rows, field):
            raise lc.Refusal("The saved result has no %s. Run the search again with the parameters queries.py printed, unchanged." % field)
    empty = [f for f in fields if rows and not present(rows, f) and not f.startswith("metrics.")]
    if empty:
        notes.append("Empty in every row, so written as --: %s." % ", ".join(empty))
    limit = params.get("limit")
    if limit and len(rows) >= limit:
        warnings.append("The search returned %d rows, its limit, so the report may be cut off. Narrow the date range or raise the limit, then run it again." % len(rows))

    start = dt.date.fromisoformat(query["start"]) if query.get("start") else None
    end = dt.date.fromisoformat(query["end"]) if query.get("end") else None
    if query.get("report") == "change-history" and end:
        kept = [r for r in rows if str(r.get("change_event.change_date_time", ""))[:10] <= end.isoformat()]
        if len(kept) != len(rows):
            notes.append("%d changes after %s were left out, to keep to the date range." % (len(rows) - len(kept), lc.long_date(end)))
        rows = kept

    joined_by_key, unlisted = {}, {}
    if query.get("join_key"):
        key_field, match_field = query["join_key"]
        listed = {str(r.get(match_field)) for r in rows}
        for jrows in join_rows.values():
            for jrow in jrows:
                key = str(jrow.get(key_field))
                slot = joined_by_key.setdefault(key, {})
                for column in query["columns"]:
                    if column.get("join"):
                        slot[column["field"]] = slot.get(column["field"], 0.0) + (lc.number(jrow.get(column["field"])) or 0.0)
        for key, values in joined_by_key.items():
            if key not in listed:
                unlisted[key] = values
    names = name_map(join_rows)

    columns = list(query["columns"])
    header = [c["header"] for c in columns]
    currency_at = None
    numeric_at = next((i for i, c in enumerate(columns) if c["kind"] in NUMERIC or c.get("join")), None)
    if args.currency and numeric_at is not None:
        currency_at = numeric_at
        header.insert(currency_at, "Currency code")

    body, sums = [], {c["header"]: 0.0 for c in columns if c.get("sum")}
    for row in rows:
        joined = joined_by_key.get(str(row.get(query["join_key"][1])), {}) if query.get("join_key") else {}
        cells = []
        for column in columns:
            cells.append(cell(row, column, names, joined, unmapped))
            if column.get("sum"):
                raw = joined.get(column["field"], 0.0) if column.get("join") else value_of(row, column["field"], column["kind"])
                sums[column["header"]] += raw or 0.0
        if currency_at is not None:
            cells.insert(currency_at, args.currency)
        body.append(cells)

    total_row = None
    if query.get("total") and sums:
        total_row = [query["total"]] + [lc.EMPTY] * (len(columns) - 1)
        for index, column in enumerate(columns):
            if column.get("sum") and index > 0:
                total_row[index] = format_number(column["kind"], round(sums[column["header"]], 6), column["field"])
        if currency_at is not None:
            total_row.insert(currency_at, args.currency)

    outputs.ensure_dir(args.out)
    csv_path = os.path.abspath(os.path.join(args.out, query["file"]))
    grid = [[query["title"]]]
    if start and end:
        grid.append([lc.range_text(start, end)])
    grid.append(header)
    grid += body
    if total_row:
        grid.append(total_row)
    with open(csv_path, "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(grid)

    # Read the file back with the pack's own reader, as every other skill will.
    aliases = {h.lower(): slug(h) for h in header}
    sum_slugs = [slug(c["header"]) for c in columns if c.get("sum")]
    meta, back = io.read_report(csv_path, extra_aliases=aliases, extra_numeric=sum_slugs)
    check = {"rows_written": len(body), "rows_read_back": meta["row_count"], "date_range_read_back": meta["date_range"],
             "totals": {h: round(v, 2) for h, v in sums.items()}, "matches": meta["row_count"] == len(body)}
    for column in columns:
        if column.get("sum"):
            key = slug(column["header"])
            from_rows = round(sum(r.get(key) or 0.0 for r in back), 2)
            from_total = meta["totals"].get(query["total"], {}).get(key)
            check.setdefault("by_column", {})[column["header"]] = {"rows": from_rows, "total_row": from_total}
            # Each row is rounded to two decimals, so the rows can differ from the total by half a cent a row.
            if from_total is not None and abs(from_rows - from_total) > 0.005 * len(back) + 0.01:
                check["matches"] = False
    if start and meta["date_range"] != [start.isoformat(), end.isoformat()]:
        check["matches"] = False
    if not check["matches"]:
        warnings.append("Reading the file back did not give the same rows and totals. Do not hand it to another skill; report this.")
    if unmapped:
        warnings.append("Values written as Google sent them, because their words are not known here: %s." % "; ".join(sorted(unmapped)))
    if unlisted:
        total_unlisted = sum(v.get("metrics.all_conversions", 0.0) for v in unlisted.values())
        notes.append("Not enabled, but still recorded conversions in the range, so not in this file: %s. Together: %s All conv." % (
            ", ".join(sorted(unlisted)), lc.fmt_money(total_unlisted)))

    lines = ["# %s, converted from live data" % query["title"], ""]
    lines.append("**File:** %s, in the layout of a Google Ads download." % csv_path)
    if start and end:
        lines.append("**Date range:** %s, %d days." % (lc.range_text(start, end), (end - start).days + 1))
    lines.append("**Rows:** %d.%s" % (len(body), " The search returned no rows for this range." if not body else ""))
    if sums:
        lines.append("**Totals:** " + ", ".join("%s %s" % (h, lc.fmt_int(v) if h in ("Impr.", "Clicks") else lc.fmt_money(v)) for h, v in sums.items()) + ".")
    lines.append("**Check:** %s" % ("the file reads back with the pack's own reader: %d rows, the date range, and every total row figure equal to the sum of its rows." % meta["row_count"]
                                     if check["matches"] else "FAILED. The file did not read back the same."))
    if warnings:
        lines += ["", "## Warnings", ""] + ["- " + w for w in warnings]
    if query.get("readers"):
        lines += ["", "## Hand it to", ""] + ["- The %s (run from that skill's folder, FILE is %s)" % (r, csv_path) for r in query["readers"]]
    lines += ["", "## How the numbers were made", "",
              "- Money fields arrive in micros, millionths of the account currency, and are divided by 1,000,000. Money is written with two decimals and no currency symbol.",
              "- Rates and shares arrive as ratios and are written as percentages. An impression share Google reports as 0.0999 is written < 10%, and a lost share of 0.9001 is written > 90%, as the interface shows them.",
              "- API values such as ENABLED or EXACT are written as the interface's words, such as Enabled or Exact match.",
              "- A metric missing from a row is read as 0, because results written as JSON leave out zero values.",
              "- The total row is the sum of the rows in this file."]
    lines += ["", "## What this did not cover", ""] + ["- " + g for g in query.get("gaps", []) + notes] + [
        "- One search reads one account and one date range. Rows Google does not return are not here."]
    summary = "\n".join(lines) + "\n"
    base = os.path.join(args.out, "%s.conversion" % query["report"])
    # The saved summary sits beside the CSV, so it names the file alone and carries no folder of this machine.
    with open(base + ".md", "w", encoding="utf-8") as handle:
        handle.write(summary.replace(csv_path, query["file"]))
    outputs.write_json(base + ".json", {"report": query["report"], "file": query["file"], "rows": len(body), "check": check,
                                        "warnings": warnings, "notes": notes,
                                        "start": query.get("start"), "end": query.get("end")})
    print(summary)
    if not check["matches"]:
        sys.exit(1)


if __name__ == "__main__":
    main()
