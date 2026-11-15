#!/usr/bin/env python3
"""Print the parameters for Google Ads' own MCP search tool, for a named report
or for a question the reports do not answer. Every field is checked against
the known fields first. This script calls nothing: you run the search.

    python3 scripts/queries.py list
    python3 scripts/queries.py check --customer 123-456-7890 --work WORK
    python3 scripts/queries.py report search-terms --customer 123-456-7890 --work WORK [--start 2026-10-14 --end 2026-11-12 | --days 30] [--login-customer 111-222-3333]
    python3 scripts/queries.py custom --name NAME --resource keyword_view --fields "campaign.name, metrics.clicks" [--where "metrics.clicks > 10"] [--order "metrics.clicks DESC"] [--limit 500] [--title "..."] --customer 123-456-7890 --work WORK

Each run writes WORK/NAME.query.json, which convert.py reads.
"""
import argparse
import datetime as dt
import json
import os
import shlex
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import livecore as lc  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

COUNTS = ("seen", "attributed", "hand", "unproven")
STATUS_WORDS = {"seen": "seen with this resource in working queries", "attributed": "from a resource read with this one in working queries",
                "hand": "checked by hand on Google's field reference", "unproven": "known, but not yet seen with this resource"}


def dates_for(args, default_days, max_days=None):
    today = lc.iso(args.today, "--today") if args.today else dt.date.today()
    notes = []
    if args.end:
        end = lc.iso(args.end, "--end")
    elif max_days:
        end = today
        notes.append("The range ends today, %s, so the latest changes are in. That was assumed." % lc.long_date(end))
    else:
        end = today - dt.timedelta(days=1)
        notes.append("The range ends yesterday, %s, the last full day. That was assumed. Pass --end to change it." % lc.long_date(end))
    if args.start:
        start = lc.iso(args.start, "--start")
    else:
        days = args.days or default_days
        start = end - dt.timedelta(days=days - 1)
        if not args.days:
            notes.append("The range is %d days. That was assumed. Pass --days or --start to change it." % days)
    if start > end:
        raise lc.Refusal("The start date %s is after the end date %s. Swap them." % (start, end))
    if end > today:
        raise lc.Refusal("The end date %s is after today. Pick an end date of today or earlier." % end)
    if max_days and (today - start).days >= max_days:
        raise lc.Refusal("Google keeps change history for %d days. Start on %s or later." % (max_days, today - dt.timedelta(days=max_days - 1)))
    return start, end, notes


def summarize(checks):
    """One line per search: the fields it selects, then the fields it filters or sorts by."""
    selected = [c for c in checks if c["used_in"] == "select"]
    counts = {k: sum(1 for c in selected if c["status"] == k) for k in COUNTS}
    parts = ["%d %s" % (counts[k], STATUS_WORDS[k]) for k in COUNTS if counts[k]]
    text = "%d fields selected, all known: %s." % (len(selected), "; ".join(parts))
    others = []
    for c in checks:
        if c["used_in"] != "select":
            item = "%s (%s)" % (c["field"], "filter" if c["used_in"] == "condition" else "sort")
            if item not in others:
                others.append(item)
    if others:
        text += " Also checked, as the search filters or sorts by them: %s." % ", ".join(others)
    return text


def search_block(label, params, save_to, checks=None):
    lines = ["%s Call the search tool (%s) with exactly these parameters:" % (label, lc.SEARCH_TOOL), ""]
    if checks is not None:
        lines += ["Field check: " + summarize(checks), ""]
    return lines + ["```json", json.dumps(params, indent=2), "```", "",
                    "Save the tool's whole result, unchanged, to:", "", "    %s" % save_to, ""]


def script(name):
    return "python3 %s" % shlex.quote(os.path.join(HERE, name))


def write_query(work, name, payload):
    os.makedirs(work, exist_ok=True)
    path = os.path.join(work, "%s.query.json" % name)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
    return path


def cmd_list(_args):
    print("# Named live reports\n")
    print("Each writes a CSV in the layout of a Google Ads download, so the other skills read it unchanged.\n")
    for name, spec in lc.REPORTS.items():
        print("- **%s** (%s, default %d days): %s" % (name, spec["file"], spec["days"], spec["what"]))
        for reader in spec["readers"]:
            print("  - Read by the %s" % reader)
    print("\n`check` runs the account check that ends the setup.")


def cmd_check(args):
    catalogue = lc.Catalogue()
    customer = lc.customer_id(args.customer)
    login = lc.customer_id(args.login_customer, "the manager account ID") if args.login_customer else None
    checks = lc.check_fields(catalogue, lc.CHECK["resource"], lc.CHECK["fields"])
    params = lc.parameters(lc.CHECK["resource"], lc.CHECK["fields"], [], [], lc.CHECK["limit"], customer, login)
    lines = ["# Account check for %s" % lc.dashed(customer), "",
             "1. Call %s with no parameters. It lists the accounts your sign in reaches directly. Say whether %s is among them, or whether it sits under a manager account (then pass --login-customer)." % (lc.LIST_TOOL, lc.dashed(customer)), ""]
    lines += search_block("2.", params, os.path.join(os.path.abspath(args.work), "check.result.json"), checks)
    lines += ["3. Tell the person the account name, currency and time zone from the result. These are read only calls."]
    write_query(args.work, "check", {"kind": "check", "parameters": params, "field_checks": checks})
    print("\n".join(lines))


def cmd_report(args):
    if args.name not in lc.REPORTS:
        raise lc.Refusal("I don't know the report \"%s\". The named reports: %s." % (args.name, ", ".join(lc.REPORTS)))
    spec = lc.REPORTS[args.name]
    catalogue = lc.Catalogue()
    customer = lc.customer_id(args.customer)
    login = lc.customer_id(args.login_customer, "the manager account ID") if args.login_customer else None
    start, end, notes = dates_for(args, spec["days"], spec.get("max_days"))
    fields = lc.report_fields(spec)
    conditions = lc.fill(spec["conditions"], start, end)
    main_checks = lc.check_fields(catalogue, spec["resource"], fields, conditions, spec["orderings"])
    checks = list(main_checks)
    params = lc.parameters(spec["resource"], fields, conditions, spec["orderings"], args.limit or spec["limit"], customer, login)
    joins = []
    for join in spec.get("joins", []):
        look = lc.LOOKUPS[join]
        join_conditions = lc.fill(look["conditions"], start, end)
        join_checks = lc.check_fields(catalogue, look["resource"], look["fields"], join_conditions, look["orderings"])
        checks += join_checks
        joins.append({"name": join, "result": "%s.result.json" % join, "field_checks": join_checks,
                      "parameters": lc.parameters(look["resource"], look["fields"], join_conditions, look["orderings"],
                                                  look["limit"], customer, login)})
    weak = [c for c in checks if c["status"] == "unproven"]
    if weak:
        raise lc.Refusal("A named report holds a field not yet proven for its resource: %s. Use a custom query instead." % ", ".join(c["field"] for c in weak))
    result = "%s.result.json" % args.name
    payload = {"kind": "report", "report": args.name, "title": spec["title"], "file": spec["file"], "total": spec["total"],
               "customer_id": customer, "start": start.isoformat(), "end": end.isoformat(), "tool": lc.SEARCH_TOOL,
               "parameters": params, "result": result, "joins": joins, "join_key": spec.get("join_key"),
               "columns": spec["columns"], "needs": spec["needs"], "gaps": spec["gaps"], "readers": spec["readers"],
               "field_checks": main_checks}
    query_path = os.path.abspath(write_query(args.work, args.name, payload))
    work = os.path.dirname(query_path)
    out = os.path.abspath(args.out or args.work)
    lines = ["# Live report: %s (%s)" % (spec["title"], args.name), "",
             "Account %s. Date range %s, %d days." % (lc.dashed(customer), lc.range_text(start, end), (end - start).days + 1)]
    lines += notes + [""]
    lines += search_block("Step 1.", params, os.path.join(work, result), main_checks)
    for index, join in enumerate(joins):
        lines += search_block("Step 1%s." % "bcdef"[index], join["parameters"], os.path.join(work, join["result"]), join["field_checks"])
    lines += ["Step 2. Convert it to the downloaded layout:", "",
              "    %s --query %s --out %s" % (script("convert.py"), shlex.quote(query_path), shlex.quote(out)), ""]
    if spec.get("max_days"):
        lines.append("Google keeps change history for %d days and needs the date filter and the limit above." % spec["max_days"])
    print("\n".join(lines))


def cmd_custom(args):
    catalogue = lc.Catalogue()
    customer = lc.customer_id(args.customer)
    login = lc.customer_id(args.login_customer, "the manager account ID") if args.login_customer else None
    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    if not fields:
        raise lc.Refusal("Name at least one field with --fields.")
    if not args.name.replace("-", "").isalnum():
        raise lc.Refusal("Give the query a short name of letters, digits and dashes, for example top-keywords.")
    if args.name in lc.REPORTS:
        raise lc.Refusal("%s is a named report. Run it with: %s report %s" % (args.name, script("queries.py"), args.name))
    conditions = list(args.where or [])
    dated = any(f.startswith("metrics.") for f in fields) and not args.no_date
    start = end = None
    notes = []
    if dated:
        start, end, notes = dates_for(args, 30)
        conditions = lc.fill(["{date}"], start, end) + conditions
    orderings = list(args.order or [])
    checks = lc.check_fields(catalogue, args.resource, fields, conditions, orderings)
    params = lc.parameters(args.resource, fields, conditions, orderings, args.limit or 1000, customer, login)
    result = "%s.result.json" % args.name
    columns = [lc.col(header_for(f), f, kind_for(f), sum=additive(f)) for f in fields]
    payload = {"kind": "custom", "report": args.name, "title": args.title or "Custom report", "file": "%s.csv" % args.name,
               "total": "Total: Rows in this report" if any(c.get("sum") for c in columns) else None,
               "customer_id": customer, "start": start.isoformat() if start else None, "end": end.isoformat() if end else None,
               "tool": lc.SEARCH_TOOL, "parameters": params, "result": result, "joins": [], "columns": columns,
               "needs": [], "gaps": [], "readers": [], "field_checks": checks}
    query_path = os.path.abspath(write_query(args.work, args.name, payload))
    out = os.path.abspath(args.out or args.work)
    lines = ["# Custom query: %s" % args.name, ""]
    if dated:
        lines.append("Date range %s." % lc.range_text(start, end))
    lines += notes + [""]
    weak = [c for c in checks if c["status"] == "unproven"]
    if weak:
        lines += ["Before you run it, call %s for %s and confirm these fields are selectable with it:" % (lc.METADATA_TOOL, args.resource)]
        lines += ["- %s (%s)" % (c["field"], c["note"]) for c in weak] + [""]
    lines += search_block("Step 1.", params, os.path.join(os.path.dirname(query_path), result), checks)
    lines += ["Step 2. Convert it:", "", "    %s --query %s --out %s" % (script("convert.py"), shlex.quote(query_path), shlex.quote(out))]
    print("\n".join(lines))


HEADERS = {c["field"]: c["header"] for spec in lc.REPORTS.values() for c in spec["columns"]
           if c["kind"] not in ("keyword", "parents", "ad_name", "lookup", "change")}
HEADERS["segments.date"] = "Day"
INT_METRICS = {"metrics.impressions", "metrics.clicks", "metrics.interactions", "metrics.video_views", "metrics.engagements"}


def header_for(field):
    return HEADERS.get(field, field)


def kind_for(field):
    if field.endswith("_micros") or field in ("metrics.average_cpc", "metrics.cost_per_conversion", "metrics.average_cpm",
                                              "metrics.average_cost", "metrics.cost_per_all_conversions"):
        return "micros"
    if field in INT_METRICS or field.endswith("quality_score"):
        return "int"
    if field.endswith("impression_share") or field.endswith("_rate") or field == "metrics.ctr" or field.endswith("_percentage"):
        return "percent"
    if field.startswith("metrics."):
        return "decimal"
    return "auto"


def additive(field):
    return field in INT_METRICS or field in ("metrics.cost_micros", "metrics.conversions", "metrics.conversions_value",
                                             "metrics.all_conversions", "metrics.all_conversions_value")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="the named reports")
    for name in ("check", "report", "custom"):
        p = sub.add_parser(name)
        if name == "report":
            p.add_argument("name", help="a named report, from: queries.py list")
        p.add_argument("--customer", required=True, help="the Google Ads account ID, 10 digits")
        p.add_argument("--login-customer", help="the manager account ID, when the account is reached through a manager")
        p.add_argument("--work", required=True, help="folder for the query and result files")
        if name != "check":
            p.add_argument("--out", help="folder for the converted CSV. Default: the --work folder")
            p.add_argument("--start", help="first day, YYYY-MM-DD")
            p.add_argument("--end", help="last day, YYYY-MM-DD. Default: yesterday")
            p.add_argument("--days", type=int, help="days in the range, counted back from --end")
            p.add_argument("--limit", type=int, help="most rows to return")
            p.add_argument("--today", help=argparse.SUPPRESS)
        if name == "custom":
            p.add_argument("--name", required=True, help="a short name for the query, such as top-keywords")
            p.add_argument("--resource", required=True, help="the resource to read FROM, such as keyword_view")
            p.add_argument("--fields", required=True, help="fields, comma separated")
            p.add_argument("--where", action="append", help="one condition, such as \"metrics.clicks > 10\". Repeat for more")
            p.add_argument("--order", action="append", help="one ordering, such as \"metrics.clicks DESC\"")
            p.add_argument("--title", help="the report name written on the first row")
            p.add_argument("--no-date", action="store_true", help="read all time instead of a date range")
    args = parser.parse_args()
    {"list": cmd_list, "check": cmd_check, "report": cmd_report, "custom": cmd_custom}[args.command](args)


if __name__ == "__main__":
    main()
