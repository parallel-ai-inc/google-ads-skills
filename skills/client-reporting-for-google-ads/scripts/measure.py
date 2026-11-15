#!/usr/bin/env python3
"""Step 1 of a client report: measure.

Reads a Google Ads campaign report segmented by Day that covers the reporting
period and the period before it (and the same period last year, when the file
reaches back that far). Computes the period against the period before and
against last year, for the account, the account without brand campaigns and
each campaign; a KPI scorecard against the targets given; the biggest movers;
and, with a change history export, what was changed in the period.

Writes WORK/numbers.json, where every number has an id, WORK/numbers.md (the
summary, also printed) and WORK/narrative.template.json with the sections for
the report type.

    python3 measure.py REPORT --work WORKDIR --report-type monthly
        [--period week|month|quarter | --current 2026-10-01:2026-10-31 [--previous 2026-09-01:2026-09-30]]
        [--changes CHANGE_HISTORY] [--brand-campaigns "Brand"]
        [--target-cpa 40] [--target-roas 4] [--target-spend 12000] [--target-conversions 300]
        [--given "Leads in the CRM=96"] [--client "Northside Plumbing"] [--agency "Your agency"]
        [--targets-agreed] [--confirm-targets] [--prepared 2026-11-13]
"""
import argparse
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics, outputs  # noqa: E402
import claims  # noqa: E402

DAY = dt.timedelta(days=1)
FIELDS = ("impressions", "clicks", "cost", "conversions", "conv_value")
# (id part, label, kind). Rates are stored as fractions and shown as percents.
METRICS = (("cost", "Cost", "money"), ("impr", "Impr.", "int"), ("clicks", "Clicks", "int"), ("ctr", "CTR", "rate"),
           ("cpc", "Avg. CPC", "money"), ("conv", "Conversions", "conv"), ("cvr", "Conv. rate", "rate"),
           ("cpa", "Cost / conv.", "money"), ("value", "Conv. value", "money"), ("roas", "Conv. value / cost", "ratio"),
           ("cost_per_day", "Cost per day", "money"), ("conv_per_day", "Conversions per day", "conv"))
COMP_LABEL = {"cur": "current period", "prev": "previous period", "ly": "same period last year",
              "chg_prev": "change vs previous period", "chg_ly": "change vs same period last year",
              "delta_prev": "difference vs previous period", "delta_ly": "difference vs same period last year",
              "pp_prev": "difference vs previous period, in percentage points", "pp_ly": "difference vs same period last year, in percentage points",
              "share_cur": "share of the account total, current period", "share_chg_prev": "share of the account's change vs previous period"}
# A target this far from the actual is printed as possibly wrong, to confirm before writing.
TARGET_CHECK = 0.25
# Practitioner rule: brand searches convert cheaply by nature. Brand is called an outlier
# when its cost per conversion is under half the rest of the account's, or its
# Conv. value / cost is over twice the rest of the account's.
BRAND_OUTLIER = 2.0
# Users that are Google's systems rather than the team. Official: the change history
# shows system edits as "Google Ads system" or "ads-dartsearch-budget"
# (references/reporting-and-diagnostics.md). The other two patterns are an assumption.
SYSTEM_USER = re.compile(r"google ads system|ads-dartsearch|auto-appl|recommendations", re.I)
TABLES = ("account", "account_without_brand", "campaign_types", "campaigns", "campaigns_last_year", "scorecard", "movers", "changes")
REPORT_TYPES = {
    "weekly": ("Weekly Google Ads update", "week", "playbooks/recurring-client-reports.md, playbooks/explaining-results-and-targets.md", [
        ("Performance snapshot", ["account"], "Lead with the movement the client cares about: conversions, cost and cost per conversion against the week before."),
        ("What drove it", ["movers"], "The campaigns that carried the change. Separate confirmed drivers from watch items. A change made in the period is a lead, not proof."),
        ("Work completed", ["changes"], "What the team changed this week, from the change history and from the person. Keep it separate from next steps."),
        ("Open risks", [], "Risks the client should know early: tracking, budget, a campaign that stopped, data that is still coming in."),
        ("Next steps", [], "Specific, owned actions for next week, and any asks of the client.")]),
    "monthly": ("Google Ads monthly business review", "month", "playbooks/recurring-client-reports.md, playbooks/explaining-results-and-targets.md", [
        ("Month-over-month snapshot", ["account", "account_without_brand", "scorecard"], "Lead with the business movement, not channel trivia."),
        ("Main drivers", ["movers", "campaigns"], "Connect the result to the campaigns, budget shifts and changes that mattered. Say what is durable and what is short term."),
        ("Budget shifts", [], "Where spend moved between campaigns, and what it bought."),
        ("Recommended next actions", [], "The decisions or actions for next month, in order.")]),
    "quarterly": ("Google Ads quarterly business review", "quarter", "playbooks/recurring-client-reports.md, playbooks/explaining-results-and-targets.md", [
        ("Quarterly snapshot", ["account", "account_without_brand", "scorecard"], "Start with the quarter's business story before tactics."),
        ("Wins and risks", ["movers", "campaigns_last_year"], "Which wins and risks were durable across the quarter."),
        ("Roadmap priorities", [], "What the next quarter should focus on, tied to resource choices."),
        ("Decisions needed", [], "The decisions, tradeoffs or support the next quarter needs.")]),
    "executive": ("Google Ads executive summary", None, "playbooks/summaries-memos-and-scorecards.md, playbooks/explaining-results-and-targets.md", [
        ("Summary", ["account"], "The biggest business relevant movement, with the few numbers that defend it."),
        ("Business implication", [], "What the movement means for the business, not just what moved."),
        ("Next step", [], "The most important next step or decision.")]),
    "board": ("Google Ads board summary", None, "playbooks/summaries-memos-and-scorecards.md, playbooks/explaining-results-and-targets.md", [
        ("Business impact", ["account"], "Business or portfolio implications first, channel detail second."),
        ("Strategic risks", [], "Only risks the evidence supports."),
        ("Budget implication", [], "What the results mean for budget."),
        ("Decision needed", [], "The decision, posture or watchout leadership should carry forward.")]),
    "decision": ("Google Ads decision memo", None, "playbooks/summaries-memos-and-scorecards.md, playbooks/explaining-results-and-targets.md", [
        ("Decision context", ["account"], "Frame the decision and why it matters before arguing for an option."),
        ("Options and tradeoffs", [], "The credible options, including why the ones not chosen lose. Separate facts, assumptions and recommendation."),
        ("Recommendation", [], "One recommendation."),
        ("Confidence and next step", [], "How sure, what would change the call, and the next decision point.")]),
    "scorecard": ("Google Ads KPI scorecard", None, "playbooks/summaries-memos-and-scorecards.md, playbooks/explaining-results-and-targets.md", [
        ("Scorecard", ["scorecard", "account"], "Targets, actuals and differences another operator can scan."),
        ("Biggest misses or wins", ["movers"], "The largest misses or wins, with just enough interpretation to drive follow up."),
        ("What needs follow-up", [], "The next owner or next check for each problem the scorecard shows.")]),
    "fact-check": ("Fact check", None, "playbooks/reading-a-fact-check.md", []),
}


def span(text):
    start, _, end = text.partition(":")
    a, b = dates.parse_day(start), dates.parse_day(end)
    if not a or not b or b < a:
        raise SystemExit("Write a period as START:END, for example 2026-10-01:2026-10-31.")
    return a, b


def year_back(day):
    try:
        return day.replace(year=day.year - 1)
    except ValueError:
        return day.replace(year=day.year - 1, day=28)


def month_end(day):
    return day.replace(day=dates.days_in_month(day))


def resolve_periods(args, period, first, last):
    if args.current:
        cur = span(args.current)
        whole_months = (cur[1].year - cur[0].year) * 12 + cur[1].month - cur[0].month + 1
        if args.previous:
            prev = span(args.previous)
        elif cur[0].day == 1 and cur[1] == month_end(cur[1]) and whole_months in (1, 3):
            # One whole calendar month, or three, is compared with the same number of whole months
            # before it, as a draft that says "compared with September" means, not with the same
            # number of days.
            prev_end = cur[0] - DAY
            prev_start = prev_end.replace(day=1)
            for _ in range(whole_months - 1):
                prev_start = (prev_start - DAY).replace(day=1)
            prev = (prev_start, prev_end)
        else:
            length = (cur[1] - cur[0]).days + 1
            prev = (cur[0] - DAY * length, cur[0] - DAY)
        ly = (year_back(cur[0]), year_back(cur[1]))
        kind = "custom"
    elif period == "week":
        cur = (last - DAY * 6, last)
        prev = (cur[0] - DAY * 7, cur[0] - DAY)
        ly = (cur[0] - DAY * 364, cur[1] - DAY * 364)
        kind = "week"
    elif period == "month":
        end = last if (last + DAY).day == 1 else last.replace(day=1) - DAY
        cur = (end.replace(day=1), end)
        prev_end = cur[0] - DAY
        prev = (prev_end.replace(day=1), prev_end)
        ly_start = cur[0].replace(year=cur[0].year - 1)
        ly = (ly_start, month_end(ly_start))
        kind = "month"
    elif period == "quarter":
        def quarter_start(day):
            return dt.date(day.year, 3 * ((day.month - 1) // 3) + 1, 1)
        end = last if (last + DAY).month != last.month and last.month % 3 == 0 else quarter_start(last) - DAY
        start = quarter_start(end)
        cur = (start, end)
        prev_end = start - DAY
        prev = (quarter_start(prev_end), prev_end)
        ly_start = start.replace(year=start.year - 1)
        ly = (ly_start, month_end(dt.date(ly_start.year, ly_start.month + 2, 1)))
        kind = "quarter"
    else:
        raise SystemExit("Say which period to report: --period week, month or quarter, or --current START:END.")
    if cur[0] < first or cur[1] > last:
        raise SystemExit("The report runs from %s to %s, so it does not cover the whole period %s to %s. Download the report again with that range."
                         % (first, last, cur[0], cur[1]))
    if prev[0] < first:
        raise SystemExit("The report starts on %s, so it does not cover the previous period (%s to %s). Download the report again from %s or earlier."
                         % (first, prev[0], prev[1], prev[0]))
    return kind, cur, prev, ly


def totals(day_rows, start, end, has_value):
    t = {f: 0.0 for f in FIELDS}
    for day, values in day_rows.items():
        if start <= day <= end:
            for f in FIELDS:
                t[f] += values[f]
    days = (end - start).days + 1
    return {"cost": t["cost"], "impr": t["impressions"], "clicks": t["clicks"], "conv": t["conversions"],
            "value": t["conv_value"] if has_value else None,
            "ctr": metrics.div(t["clicks"], t["impressions"]), "cpc": metrics.div(t["cost"], t["clicks"]),
            "cvr": metrics.div(t["conversions"], t["clicks"]), "cpa": metrics.div(t["cost"], t["conversions"]),
            "roas": metrics.div(t["conv_value"], t["cost"]) if has_value else None,
            "cost_per_day": t["cost"] / days, "conv_per_day": t["conversions"] / days}


class Registry:
    def __init__(self):
        self.numbers = {}

    def add(self, nid, value, kind, label, scope_id="", metric="", comp="", digits=None, raw=None):
        if value is None:
            return None
        entry = {"value": value, "kind": kind, "label": label, "scope_id": scope_id, "metric": metric, "comp": comp}
        if digits is not None:
            entry["digits"] = digits
        if raw is not None:
            entry["raw"] = raw
        entry["display"] = claims.display(entry, signed=claims.is_change(entry))
        self.numbers[nid] = entry
        return nid


def register_scope(reg, sid, name, per, has_ly):
    """Every measure of one scope, in every period and comparison."""
    for key, label, kind in METRICS:
        if per["cur"].get(key) is None and per["prev"].get(key) is None:
            continue
        base_kind = "pct" if kind == "rate" else kind
        digits = 2 if kind == "rate" else None
        comps = ["cur", "prev"] + (["ly"] if has_ly else [])
        for comp in comps:
            reg.add("%s.%s.%s" % (sid, key, comp), per[comp].get(key), base_kind, "%s: %s, %s" % (name, label, COMP_LABEL[comp]), sid, key, comp, digits)
        for other in comps[1:]:
            new, old = per["cur"].get(key), per[other].get(key)
            reg.add("%s.%s.chg_%s" % (sid, key, other), metrics.change(new, old), "pct", "%s: %s, %s" % (name, label, COMP_LABEL["chg_" + other]), sid, key, "chg_" + other, 1)
            if new is None or old is None or key.endswith("per_day"):
                continue
            if kind == "rate":
                reg.add("%s.%s.pp_%s" % (sid, key, other), (new - old) * 100, "pp", "%s: %s, %s" % (name, label, COMP_LABEL["pp_" + other]), sid, key, "pp_" + other)
            else:
                reg.add("%s.%s.delta_%s" % (sid, key, other), new - old, base_kind, "%s: %s, %s" % (name, label, COMP_LABEL["delta_" + other]), sid, key, "delta_" + other)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--work", required=True)
    parser.add_argument("--report-type", required=True, choices=sorted(REPORT_TYPES))
    parser.add_argument("--period", choices=("week", "month", "quarter"))
    parser.add_argument("--current", help="START:END")
    parser.add_argument("--previous", help="START:END")
    parser.add_argument("--changes", help="change history export")
    parser.add_argument("--brand-campaigns", default="", help="brand campaign names, comma separated, or none")
    parser.add_argument("--target-cpa", help="target cost per conversion")
    parser.add_argument("--target-roas", help="target conv. value / cost, as 4 or 400%%")
    parser.add_argument("--target-spend", help="planned spend for the period")
    parser.add_argument("--target-conversions", help="target conversions for the period")
    parser.add_argument("--given", action="append", default=[], help='a number the person gave you, "label=value"')
    parser.add_argument("--client", default="")
    parser.add_argument("--agency", default="")
    parser.add_argument("--targets-agreed", action="store_true", help="the person says the targets were agreed with the client")
    parser.add_argument("--confirm-targets", action="store_true", help="the person confirmed a target this step flagged as far from the actual")
    parser.add_argument("--prepared", help="the date the report is prepared, default today")
    args = parser.parse_args()
    prepared = dates.parse_day(args.prepared) if args.prepared else dt.date.today()
    if not prepared:
        raise SystemExit("Write the prepared date as YYYY-MM-DD.")

    type_title, default_period, playbook, sections = REPORT_TYPES[args.report_type]
    try:
        meta, rows = io.read_report(args.report)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error) if isinstance(error, ValueError) else "I can't open %s." % args.report)
    io.require(meta, ["day", "campaign", "cost", "impressions", "clicks", "conversions"], "campaign report segmented by Day")
    has_value = "conv_value" in meta["columns"]

    accounts = {(r.get("account") or "").strip() for r in rows if (r.get("account") or "").strip()}
    if len(accounts) > 1:
        raise SystemExit("This file holds %d accounts. A client report reads one account: download the report for that account alone." % len(accounts))
    currencies = sorted({(r.get("currency") or "").strip() for r in rows if (r.get("currency") or "").strip()})
    if len(currencies) > 1:
        raise SystemExit("This file mixes currencies (%s), so amounts cannot be added. Download one account at a time." % ", ".join(currencies))

    by_campaign, account_days, info = {}, {}, {}
    for row in rows:
        day = dates.parse_day(row.get("day"))
        name = (row.get("campaign") or "").strip()
        if not day or not name:
            continue
        for target in (by_campaign.setdefault(name, {}), account_days):
            slot = target.setdefault(day, {f: 0.0 for f in FIELDS})
            for f in FIELDS:
                slot[f] += row.get(f) or 0
        item = info.setdefault(name, {"status": "", "type": "", "last_cost_day": None})
        item["status"] = row.get("campaign_status") or item["status"]
        item["type"] = row.get("campaign_type") or item["type"]
        if (row.get("cost") or 0) > 0 and (item["last_cost_day"] is None or day > item["last_cost_day"]):
            item["last_cost_day"] = day
    if not account_days:
        raise SystemExit("I can't read any dated rows. Add the Day segment to the campaign report (Segment, Time, Day) and download it again.")
    first, last = min(account_days), max(account_days)
    period_kind, cur, prev, ly = resolve_periods(args, args.period or default_period, first, last)
    has_ly = first <= ly[0]
    windows = {"cur": cur, "prev": prev, "ly": ly}

    brand = []
    if args.brand_campaigns.strip().lower() not in ("", "none"):
        brand = [b.strip() for b in args.brand_campaigns.split(",") if b.strip()]
        unknown = [b for b in brand if b not in by_campaign]
        if unknown:
            raise SystemExit('These brand campaigns are not in the report: %s. Copy the names exactly. The campaigns are: %s.'
                             % (", ".join(unknown), ", ".join(sorted(by_campaign))))

    def active(name):
        days = by_campaign[name]
        return any(days[d]["impressions"] or days[d]["cost"] for d in days
                   if any(a <= d <= b for key, (a, b) in windows.items() if key != "ly" or has_ly))

    listed = [n for n in by_campaign if active(n)]
    left_out = len(by_campaign) - len(listed)
    per_campaign = {n: {k: totals(by_campaign[n], a, b, has_value) for k, (a, b) in windows.items()} for n in listed}
    listed.sort(key=lambda n: (-per_campaign[n]["cur"]["cost"], -per_campaign[n]["prev"]["cost"], n))

    reg = Registry()
    scopes = [{"id": "acct", "name": "Account", "kind": "account"}]
    per_scope = {"acct": {k: totals(account_days, a, b, has_value) for k, (a, b) in windows.items()}}
    non_brand = [n for n in listed if n not in brand]
    if brand and non_brand:
        nb_days = {}
        for name in non_brand:
            for day, values in by_campaign[name].items():
                slot = nb_days.setdefault(day, {f: 0.0 for f in FIELDS})
                for f in FIELDS:
                    slot[f] += values[f]
        scopes.append({"id": "nb", "name": "Account without brand", "kind": "nb"})
        per_scope["nb"] = {k: totals(nb_days, a, b, has_value) for k, (a, b) in windows.items()}
    types = sorted({info[n]["type"] for n in listed if info[n]["type"]})
    if len(types) > 1:
        for index, kind in enumerate(types, start=1):
            t_days = {}
            for name in listed:
                if info[name]["type"] == kind:
                    for day, values in by_campaign[name].items():
                        slot = t_days.setdefault(day, {f: 0.0 for f in FIELDS})
                        for f in FIELDS:
                            slot[f] += values[f]
            sid = "t%d" % index
            scopes.append({"id": sid, "name": kind, "kind": "type"})
            per_scope[sid] = {k: totals(t_days, a, b, has_value) for k, (a, b) in windows.items()}
    for index, name in enumerate(listed, start=1):
        sid = "c%d" % index
        status = info[name]["status"] or "Unknown"
        scopes.append({"id": sid, "name": name, "kind": "campaign", "status": status, "type": info[name]["type"], "brand": name in brand})
        per_scope[sid] = per_campaign[name]
    for scope in scopes:
        register_scope(reg, scope["id"], scope["name"], per_scope[scope["id"]], has_ly)

    acct = per_scope["acct"]
    for scope in scopes:
        if scope["kind"] != "campaign":
            continue
        sid, mine = scope["id"], per_scope[scope["id"]]
        for key, label in (("cost", "Cost"), ("conv", "Conversions"), ("value", "Conv. value")):
            if mine["cur"].get(key) is None:
                continue
            reg.add("%s.%s.share_cur" % (sid, key), metrics.div(mine["cur"][key], acct["cur"][key]), "pct",
                    "%s: %s, %s" % (scope["name"], label, COMP_LABEL["share_cur"]), sid, key, "share_cur", 1)
            reg.add("%s.%s.share_chg_prev" % (sid, key), metrics.div(mine["cur"][key] - mine["prev"][key], acct["cur"][key] - acct["prev"][key]),
                    "pct", "%s: %s, %s" % (scope["name"], label, COMP_LABEL["share_chg_prev"]), sid, key, "share_chg_prev", 1)
        last_cost = info[scope["name"]]["last_cost_day"]
        if last_cost and last_cost < cur[1]:
            reg.add("%s.last_cost_day" % sid, last_cost.isoformat(), "date", "%s: last day with cost in the file" % scope["name"], sid)

    for key, (a, b) in windows.items():
        if key == "ly" and not has_ly:
            continue
        reg.add("period.%s.start" % key, a.isoformat(), "date", "Start of the %s" % COMP_LABEL[key], comp=key)
        reg.add("period.%s.end" % key, b.isoformat(), "date", "End of the %s" % COMP_LABEL[key], comp=key)
        reg.add("period.%s.days" % key, (b - a).days + 1, "int", "Days in the %s" % COMP_LABEL[key], metric="days", comp=key)
    reg.add("report.prepared", prepared.isoformat(), "date", "Date the report was prepared")
    reg.add("file.first_day", first.isoformat(), "date", "First day in the report")
    reg.add("file.last_day", last.isoformat(), "date", "Last day in the report")
    paused = [s for s in scopes if s["kind"] == "campaign" and s["status"].lower() in ("paused", "removed")]
    reg.add("count.campaigns", len(listed), "int", "Campaigns with activity in the periods compared", metric="campaigns")
    reg.add("count.campaigns_paused", len(paused), "int", "Campaigns paused or removed on the day of download", metric="campaigns")

    brand_outlier = None
    if "nb" in per_scope:
        brand_days = {}
        for name in listed:
            if name in brand:
                for day, values in by_campaign[name].items():
                    slot = brand_days.setdefault(day, {f: 0.0 for f in FIELDS})
                    for f in FIELDS:
                        slot[f] += values[f]
        brand_cur = totals(brand_days, cur[0], cur[1], has_value)
        rest = per_scope["nb"]["cur"]
        cheap = brand_cur["cpa"] is not None and rest["cpa"] and brand_cur["cpa"] * BRAND_OUTLIER < rest["cpa"]
        rich = brand_cur["roas"] is not None and rest["roas"] and brand_cur["roas"] > BRAND_OUTLIER * rest["roas"]
        if cheap or rich:
            reg.add("brand.cpa.cur", brand_cur["cpa"], "money", "Brand campaigns together: Cost / conv., current period", "", "cpa", "cur")
            reg.add("brand.roas.cur", brand_cur["roas"], "ratio", "Brand campaigns together: Conv. value / cost, current period", "", "roas", "cur")
            brand_outlier = {"cpa": brand_cur["cpa"], "roas": brand_cur["roas"], "rest_cpa": rest["cpa"], "rest_roas": rest["roas"]}

    # Movers.
    movers = {}
    for key in ("conv", "cost", "value"):
        ranked = []
        for scope in scopes:
            if scope["kind"] != "campaign":
                continue
            delta = reg.numbers.get("%s.%s.delta_prev" % (scope["id"], key))
            if delta and abs(delta["value"]) > 1e-9:
                ranked.append((scope["id"], delta["value"]))
        movers[key] = [sid for sid, _ in sorted(ranked, key=lambda r: -abs(r[1]))]

    # Targets and the scorecard.
    def target(text, name):
        if text is None:
            return None
        value = io.to_number(text)
        if value is None or value <= 0:
            raise SystemExit("The %s target %r is not a positive number." % (name, text))
        return value

    scorecard, target_warnings = [], []
    roas_target = None
    if args.target_roas:
        roas_target = target(args.target_roas, "Conv. value / cost")
        if str(args.target_roas).strip().endswith("%"):
            roas_target = roas_target / 100
        elif roas_target > 50:
            raise SystemExit("A Conv. value / cost target of %s looks like a percent. Write it as a ratio (4 for 400%%) or with a percent sign." % args.target_roas)
        if not has_value:
            raise SystemExit("A Conv. value / cost target needs the Conv. value column. Add it to the campaign report and download it again.")
    wanted = (("cpa", "Cost / conv.", target(args.target_cpa, "cost per conversion"), "money", "lower"),
              ("roas", "Conv. value / cost", roas_target, "ratio", "higher"),
              ("cost", "Spend", target(args.target_spend, "spend"), "money", "plan"),
              ("conv", "Conversions", target(args.target_conversions, "conversions"), "conv", "higher"))
    for key, label, goal, kind, better in wanted:
        if goal is None:
            continue
        reg.add("target.%s" % key, goal, kind, "Target you gave: %s for the current period" % label, metric=key, comp="target")
        for sid in (["acct", "nb"] if key in ("cpa", "roas") and "nb" in per_scope else ["acct"]):
            actual = per_scope[sid]["cur"].get(key)
            suffix = "" if sid == "acct" else "_nb"
            scope_name = "Account" if sid == "acct" else "Account without brand"
            row = {"kpi": label + ("" if sid == "acct" else ", without brand"), "target_id": "target.%s" % key,
                   "actual_id": "%s.%s.cur" % (sid, key), "prev_id": "%s.%s.prev" % (sid, key), "status": "No data"}
            if actual is not None:
                row["diff_id"] = reg.add("score.%s%s.diff" % (key, suffix), actual - goal, kind, "%s: %s, difference from target" % (scope_name, label), sid, key, "diff")
                row["diff_pct_id"] = reg.add("score.%s%s.diff_pct" % (key, suffix), metrics.change(actual, goal), "pct",
                                             "%s: %s, difference from target in percent" % (scope_name, label), sid, key, "diff_pct", 1)
                if better == "lower":
                    row["status"] = "At or better than target" if actual <= goal else "Above target"
                elif better == "higher":
                    row["status"] = "Target met" if actual >= goal else "Below target"
                else:
                    row["status"] = "On target" if abs(actual - goal) < 0.005 else ("Below target" if actual < goal else "Above target")
                gap = metrics.change(actual, goal)
                if sid == "acct" and gap is not None and abs(gap) > TARGET_CHECK:
                    target_warnings.append("The %s target you gave, %s, is %s away from the actual %s. It may be wrong: a figure for a different period, "
                                           "an old plan or a typo. Confirm it with the person before writing about it." % (
                                               label.lower() if label != "Cost / conv." else "cost per conversion", claims.display(reg.numbers["target.%s" % key]),
                                               metrics.pct(abs(gap)), claims.display(reg.numbers["%s.%s.cur" % (sid, key)])))
            scorecard.append(row)

    if brand_outlier:
        scorecard.sort(key=lambda r: not r["kpi"].endswith("without brand"))

    # Change history.
    changes = {"read": bool(args.changes), "items": [], "outside_report": []}
    if args.changes:
        try:
            change_meta, change_rows = io.read_report(args.changes)
        except (OSError, ValueError):
            raise SystemExit("I can't read the change history file. In Google Ads open Change history, set the same date range, and Download it as CSV.")
        io.require(change_meta, ["changed_at", "changes"], "change history export")
        entries = []
        for row in change_rows:
            day = dates.parse_day(row.get("changed_at"))
            if day and cur[0] <= day <= cur[1]:
                text = re.sub(r"\s*\n\s*", "; ", (row.get("changes") or "").strip())
                entries.append((day, row.get("changed_at") or "", (row.get("campaign") or "").strip(), (row.get("ad_group") or "").strip(),
                                (row.get("user") or "").strip(), text))
        entries.sort(key=lambda e: (e[0], e[1]))
        campaign_ids = {s["name"]: s["id"] for s in scopes if s["kind"] == "campaign"}
        by_campaign_count = {}
        for index, (day, stamp, campaign, ad_group, user, text) in enumerate(entries, start=1):
            cid = "chg%d" % index
            system = bool(SYSTEM_USER.search(user))
            sid = campaign_ids.get(campaign, "")
            reg.add("%s.date" % cid, day.isoformat(), "date", "Date of change %d" % index)
            for n, token in enumerate([t for t in claims.tokens(text) if t["kind"] in ("num", "pct")], start=1):
                value = token["value"] / 100 if token["kind"] == "pct" else token["value"]
                reg.add("%s.n%d" % (cid, n), value, "pct" if token["kind"] == "pct" else "plain",
                        "Number in change %d: %s" % (index, text[:80]), sid, digits=token["decimals"] if token["kind"] == "pct" else None, raw=token["raw"])
            changes["items"].append({"id": cid, "date": day.isoformat(), "campaign": campaign, "ad_group": ad_group, "user": user,
                                     "by_system": system, "changes": text})
            if campaign:
                by_campaign_count[campaign] = by_campaign_count.get(campaign, 0) + 1
                if campaign not in campaign_ids:
                    changes["outside_report"].append(campaign)
        system_count = sum(1 for c in changes["items"] if c["by_system"])
        reg.add("count.changes.cur", len(entries), "int", "Changes made in the current period", metric="changes", comp="cur")
        reg.add("count.changes.team", len(entries) - system_count, "int", "Changes made by people in the current period", metric="changes", comp="cur")
        reg.add("count.changes.system", system_count, "int", "Changes made by Google's systems in the current period", metric="changes", comp="cur")
        for campaign, count in by_campaign_count.items():
            if campaign in campaign_ids:
                sid = campaign_ids[campaign]
                reg.add("%s.changes.cur" % sid, count, "int", "%s: changes made in the current period" % campaign, sid, "changes", "cur")
        changes["outside_report"] = sorted(set(changes["outside_report"]))

    given = []
    for index, item in enumerate(args.given, start=1):
        label, sep, raw = item.partition("=")
        if not sep or not label.strip() or not raw.strip():
            raise SystemExit('Write a given number as "label=value", for example "Leads in the CRM=96".')
        raw = raw.strip()
        gid = "given%d" % index
        day = dates.parse_day(raw) if re.search(r"[A-Za-z]|^\d{4}-\d", raw) else None
        if day:
            reg.add(gid, day.isoformat(), "date", "Given by you: %s" % label.strip())
        else:
            value = io.to_number(raw)
            if value is None:
                raise SystemExit("The given value %r is not a number or a date." % raw)
            if raw.endswith("%"):
                reg.add(gid, value / 100, "pct", "Given by you: %s" % label.strip(), digits=len(raw.rstrip("%").partition(".")[2]))
            else:
                reg.add(gid, value, "plain", "Given by you: %s" % label.strip(), raw=raw)
        given.append(gid)

    # Reconcile with the file's own totals.
    rows_cost = sum((r.get("cost") or 0) for r in rows if dates.parse_day(r.get("day")) and (r.get("campaign") or "").strip())
    reconcile = None
    for wanted_label in ("Total: Filtered campaigns", "Total: Account"):
        undated = [v for k, v in meta["totals"].items() if k == wanted_label]
        dated = [v for k, v in meta["totals"].items() if k.startswith(wanted_label + ", ")]
        picked = undated or dated
        if picked:
            file_cost = sum(v.get("cost") or 0 for v in picked)
            reconcile = {"label": wanted_label, "file_total_cost": round(file_cost, 2), "rows_cost": round(rows_cost, 2),
                         "matches": abs(file_cost - rows_cost) <= 0.01 + 0.005 * len(picked)}
            break

    notes = []
    if not has_ly:
        notes.append("The report starts on %s, so the same period last year (%s to %s) is not compared. To add it, download the report from %s."
                     % (first, ly[0], ly[1], ly[0]))
    if last > cur[1]:
        notes.append("The report runs to %s. Days after %s are not part of this report." % (last, cur[1]))
    for key, (a, b) in windows.items():
        if key == "ly" and not has_ly:
            continue
        missing = sum(1 for i in range((b - a).days + 1) if (a + DAY * i) not in account_days)
        if missing:
            notes.append("The %s has %d days with no rows in the file. Google leaves out rows with no activity, so they count as zero." % (COMP_LABEL[key], missing))
    for scope in paused:
        last_cost = info[scope["name"]]["last_cost_day"]
        notes.append("%s (%s) is %s on the day of download%s. Report it as %s, not as a decline."
                     % (scope["name"], scope["id"], scope["status"].lower(),
                        ", and its last day with cost is %s" % last_cost if last_cost else "", scope["status"].lower()))
    if left_out:
        notes.append("%d campaigns had no impressions and no cost in the periods compared, so they are left out of the tables." % left_out)
    if not brand:
        looks = [n for n in listed if "brand" in n.lower()]
        if looks:
            notes.append("%s looks like a brand campaign. Brand searches convert cheaply and pull the account's cost per conversion down. "
                         "If it is brand, run this step again with --brand-campaigns so the report shows the account without brand too." % ", ".join(looks))
    if reconcile and not reconcile["matches"]:
        notes.append("The rows add up to %s of cost, but the file's own %s is %s. Check the file was not filtered after download."
                     % (metrics.money(rows_cost), reconcile["label"], metrics.money(reconcile["file_total_cost"])))
    for warning in target_warnings:
        notes.insert(0, "CHECK THE TARGET. " + warning)
    if brand_outlier:
        notes.append("Brand is an outlier: %s per conversion against %s for the rest of the account%s. Brand searches convert cheaply by nature, so "
                     "give the figures without brand first (nb ids) and say why the blended figure flatters. Outlier means under half the rest's cost "
                     "per conversion, or over twice its Conv. value / cost. Practitioner rule." % (
                         metrics.money(brand_outlier["cpa"]), metrics.money(brand_outlier["rest_cpa"]),
                         ", and %s Conv. value / cost against %s" % (metrics.money(brand_outlier["roas"]), metrics.money(brand_outlier["rest_roas"]))
                         if brand_outlier["roas"] is not None and brand_outlier["rest_roas"] else ""))
    if changes["outside_report"]:
        notes.append("The change history names campaigns that are not in this report: %s." % ", ".join(changes["outside_report"]))
    if changes["read"] and not changes["items"]:
        notes.append("No change in the change history falls in the current period.")

    daily = []
    for key in ("prev", "cur"):
        a, b = windows[key]
        for i in range((b - a).days + 1):
            day = a + DAY * i
            v = account_days.get(day, {f: 0.0 for f in FIELDS})
            daily.append([day.isoformat(), "Current" if key == "cur" else "Previous", round(v["cost"], 2), int(v["impressions"]), int(v["clicks"]),
                          round(v["conversions"], 2), round(v["conv_value"], 2) if has_value else None])

    available = {"account": True, "account_without_brand": "nb" in per_scope, "campaign_types": len(types) > 1, "campaigns": True,
                 "campaigns_last_year": has_ly, "scorecard": bool(scorecard), "movers": True, "changes": changes["read"]}
    template_sections = [{"heading": h, "text": "", "bullets": [], "tables": [t for t in tabs if available.get(t)], "hint": hint}
                         for h, tabs, hint in sections]
    if brand_outlier:
        for section in template_sections:
            if "account" in section["tables"] and "account_without_brand" in section["tables"]:
                section["tables"].remove("account_without_brand")
                section["tables"].insert(section["tables"].index("account"), "account_without_brand")
    if period_kind == "month":
        period_label = "%s %d" % (cur[0].strftime("%B"), cur[0].year)
    elif period_kind == "quarter":
        period_label = "Q%d %d" % ((cur[0].month - 1) // 3 + 1, cur[0].year)
    elif period_kind == "week":
        period_label = "week of %s" % claims.long_date(cur[0].isoformat())
    else:
        period_label = "%s to %s" % (claims.long_date(cur[0].isoformat()), claims.long_date(cur[1].isoformat()))
    report_title = "%sGoogle Ads, %s" % ("%s: " % args.client.strip() if args.client.strip() else "", period_label)
    names = [s["name"] for s in scopes if s["kind"] in ("campaign", "type")]
    result = {
        "report": os.path.basename(args.report), "title_rows": meta["title_rows"], "currency": currencies[0] if len(currencies) == 1 else "",
        "client": args.client.strip(), "agency": args.agency.strip(), "report_type": args.report_type, "type_title": type_title,
        "prepared": prepared.isoformat(), "targets_agreed": args.targets_agreed, "targets_confirmed": args.confirm_targets, "target_warnings": target_warnings, "brand_outlier": brand_outlier,
        "playbook": playbook, "required_sections": [h for h, _, _ in sections],
        "periods": {"kind": period_kind, "current": [cur[0].isoformat(), cur[1].isoformat()], "previous": [prev[0].isoformat(), prev[1].isoformat()],
                    "last_year": [ly[0].isoformat(), ly[1].isoformat()] if has_ly else None, "file": [first.isoformat(), last.isoformat()]},
        "has_value": has_value, "brand": brand, "scopes": scopes, "names": names, "movers": movers, "scorecard": scorecard,
        "changes": changes, "given": given, "reconcile": reconcile, "notes": notes, "available_tables": [t for t in TABLES if available[t]],
        "left_out": left_out, "daily": daily, "numbers": reg.numbers,
    }
    work = outputs.ensure_dir(args.work)
    outputs.write_json(os.path.join(work, "numbers.json"), result)
    if sections:
        outputs.write_json(os.path.join(work, "narrative.template.json"), {
            "report_type": args.report_type, "title": report_title,
            "how_to": "Write each section's text (paragraphs separated by a blank line) and bullets. Write every number as its id in braces, "
                      "for example {acct.cost.cur}; the write step puts in the exact figure. Tables are inserted after the text. "
                      "Delete the hints when done. You may add or remove sections.",
            "sections": template_sections})

    text = summary(result, reg.numbers)
    with open(os.path.join(work, "numbers.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote %s" % os.path.join(work, "numbers.json"))


def summary(result, numbers):
    def show(nid):
        entry = numbers.get(nid)
        return claims.display(entry, signed=claims.is_change(entry)) if entry else "n/a"

    p = result["periods"]
    cur, prev, ly = p["current"], p["previous"], p["last_year"]

    def days(pair):
        return (dt.date.fromisoformat(pair[1]) - dt.date.fromisoformat(pair[0])).days + 1

    lines = ["# Numbers for the report", ""]
    lines += ["%s." % t for t in result["title_rows"]]
    lines += ["", "- Report type: %s. Sections the playbook asks for: %s." % (result["type_title"], ", ".join(result["required_sections"]) or "none"),
              "- Current period: %s to %s (%d days). Previous period: %s to %s (%d days)." % (cur[0], cur[1], days(cur), prev[0], prev[1], days(prev))]
    if ly:
        lines.append("- Same period last year: %s to %s (%d days)." % (ly[0], ly[1], days(ly)))
    if days(cur) != days(prev):
        lines.append("- The periods differ in length. Compare per day figures (cost_per_day, conv_per_day) as well as totals.")
    if result["currency"]:
        lines.append("- Amounts are in %s." % result["currency"])
    if result["reconcile"]:
        r = result["reconcile"]
        lines.append("- The rows add up to %s of cost. The file's own %s is %s.%s" % (
            metrics.money(r["rows_cost"]), r["label"], metrics.money(r["file_total_cost"]), "" if r["matches"] else " THEY DO NOT MATCH."))
    for note in result["notes"]:
        lines.append("- NOTE: " + note)
    if result["target_warnings"] and not result["targets_confirmed"]:
        lines.append("- Do not write the narrative until the person confirms each target marked CHECK THE TARGET, or gives the right one.")

    scopes = result["scopes"]
    lines += ["", "## How to cite a number", "",
              "Write every number in the narrative as its id in braces, for example {acct.cost.chg_prev}. The id is SCOPE.MEASURE.COMPARISON.",
              "",
              "- Scopes: " + "; ".join("%s = %s%s" % (s["id"], s["name"], " (%s)" % s["status"].lower() if s.get("status", "").lower() in ("paused", "removed") else "")
                                       for s in scopes) + ".",
              "- Measures: cost, impr, clicks, ctr, cpc, conv, cvr, cpa, value, roas, cost_per_day, conv_per_day." +
              ("" if result["has_value"] else " The report has no Conv. value column, so value and roas do not exist."),
              "- Comparisons: cur, prev%s; chg_prev%s (relative change); delta_prev%s (difference); pp_prev%s (ctr and cvr, in percentage points); "
              "share_cur and share_chg_prev (campaigns only: share of the account total, and of the account's change)." % (
                  ", ly" if ly else "", ", chg_ly" if ly else "", ", delta_ly" if ly else "", ", pp_ly" if ly else ""),
              "- Dates: period.cur.start, period.cur.end, period.prev.start, period.prev.end%s, and days: period.cur.days, period.prev.days." % (
                  ", period.ly.start, period.ly.end" if ly else ""),
              "- A change id is written without its sign when your sentence says which way it went (rose, fell), and with its sign when it does not. "
              "Add .abs to any id to always drop the sign: {c3.cost.delta_prev.abs}.",
              "- Other ids: target.cpa, target.roas, target.cost, target.conv (the targets given); score.cpa.diff, score.cpa.diff_pct "
              "(and score.cpa_nb.* without brand); count.campaigns, count.changes.cur; cN.last_cost_day; report.prepared; given1, given2.",
              ""]

    def scope_table(sid):
        header = ["Measure", "Now", "Previous", "Change", "Difference"] + (["Last year", "Change vs last year"] if ly else [])
        rows = []
        for key, label, kind in METRICS:
            if "%s.%s.cur" % (sid, key) not in numbers:
                continue
            diff = "%s.%s.%s_prev" % (sid, key, "pp" if kind == "rate" else "delta")
            row = ["%s (%s.%s)" % (label, sid, key), show("%s.%s.cur" % (sid, key)), show("%s.%s.prev" % (sid, key)),
                   show("%s.%s.chg_prev" % (sid, key)), show(diff)]
            if ly:
                row += [show("%s.%s.ly" % (sid, key)), show("%s.%s.chg_ly" % (sid, key))]
            rows.append(row)
        return outputs.md_table(header, rows)

    for scope in scopes:
        if scope["kind"] in ("account", "nb", "type"):
            lines += ["## %s (%s)" % (scope["name"], scope["id"]), "", scope_table(scope["id"]), ""]

    camp = [s for s in scopes if s["kind"] == "campaign"]
    header = ["id", "Campaign", "Status", "Cost", "Cost chg", "Conv.", "Conv. chg", "Cost / conv.", "Cost / conv. chg", "Share of cost", "Share of conv."]
    if result["has_value"]:
        header += ["Conv. value / cost", "Conv. value / cost chg"]
    if ly:
        header += ["Cost chg vs LY", "Conv. chg vs LY"]
    rows = []
    for s in camp:
        sid = s["id"]
        row = [sid, s["name"] + (" (brand)" if s.get("brand") else ""), s["status"], show(sid + ".cost.cur"), show(sid + ".cost.chg_prev"),
               show(sid + ".conv.cur"), show(sid + ".conv.chg_prev"), show(sid + ".cpa.cur"), show(sid + ".cpa.chg_prev"), show(sid + ".cost.share_cur"),
               show(sid + ".conv.share_cur")]
        if result["has_value"]:
            row += [show(sid + ".roas.cur"), show(sid + ".roas.chg_prev")]
        if ly:
            row += [show(sid + ".cost.chg_ly"), show(sid + ".conv.chg_ly")]
        rows.append(row)
    lines += ["## Campaigns, current period and change vs previous", "", outputs.md_table(header, rows), "",
              "Every other measure of a campaign follows the same ids, for example c1.ctr.cur. All ids are in numbers.json.", ""]

    names = {s["id"]: s["name"] for s in scopes}
    lines += ["## Biggest movers vs previous period", ""]
    for key, label in (("conv", "Conversions"), ("cost", "Cost"), ("value", "Conv. value")):
        ranked = result["movers"].get(key) or []
        if ranked:
            lines.append("- %s: " % label + "; ".join("%s %s %s (%s)" % (sid, names[sid], show("%s.%s.delta_prev" % (sid, key)), show("%s.%s.chg_prev" % (sid, key)))
                                                     for sid in ranked[:5]) + ".")
    lines.append("")

    if result["scorecard"]:
        rows = [[r["kpi"], show(r["target_id"]), show(r["actual_id"]), show(r.get("diff_id")), show(r.get("diff_pct_id")), r["status"],
                 ", ".join(i for i in (r["target_id"], r["actual_id"], r.get("diff_id"), r.get("diff_pct_id")) if i)] for r in result["scorecard"]]
        lines += ["## KPI scorecard", "", outputs.md_table(["KPI", "Target", "Actual", "Difference", "Difference %", "Status", "ids"], rows), ""]

    ch = result["changes"]
    if ch["read"]:
        lines += ["## Changes made in the current period", "",
                  "- %s changes in all (count.changes.cur): %s by people, %s by Google's systems." % (
                      show("count.changes.cur"), show("count.changes.team"), show("count.changes.system"))]
        for item in ch["items"]:
            where = "in %s" % item["campaign"] if item["campaign"] else "at account level"
            if item["ad_group"]:
                where += ", ad group %s" % item["ad_group"]
            cited = [nid for nid in sorted(numbers) if nid.startswith(item["id"] + ".n")]
            lines.append("- %s (%s), by %s, %s: %s%s" % (
                item["id"], item["date"], "Google's systems (%s)" % item["user"] if item["by_system"] else item["user"] or "an unknown user", where,
                item["changes"], ". Numbers in it: " + ", ".join("%s = %s" % (nid, show(nid)) for nid in cited) if cited else ""))
        lines += ["- Cite a change's date as chgN.date and a number inside it as chgN.n1, chgN.n2, as listed.", ""]
    else:
        lines += ["## Changes made in the current period", "", "- No change history was provided, so the report cannot list what was changed.", ""]
    if result["given"]:
        lines += ["## Numbers you gave", ""] + ["- %s: %s (%s)" % (g, show(g), numbers[g]["label"]) for g in result["given"]] + [""]

    lines += ["## Next", "",
              "Copy narrative.template.json to narrative.json in the work folder and write each section. Then run:",
              "", "    python3 scripts/fact_check.py --work WORK", "",
              "## How the numbers were made", "",
              "- Every total is the sum of the report's daily rows over the dates of each period. Ratios are computed from those totals, never averaged.",
              "- Change is (now minus before) divided by before. Difference is now minus before. CTR and Conv. rate differences are in percentage points.",
              "- Per day figures divide by the calendar days in the period.",
              "- Campaign status is the status on the day of download, not on each day of the period.",
              "- Changes made in the period are leads to explain a movement, not proof of its cause.",
              "",
              "## What this did not cover", "",
              "- Conversions for the last days of a period can still rise as late conversions are reported. Practitioner rule.",
              "- Conversions are counted as Google Ads reports them under the account's attribution settings. **Official:** the attribution model affects the Conversions column (references/attribution.md).",
              "- Nothing outside Google Ads: the website, the CRM, other channels or sales.",
              "- The change history can miss some changes. **Official:** some account level and Google representative changes may be missing (references/reporting-and-diagnostics.md)." if ch["read"] else
              "- What was changed in the account, since no change history was provided.",
              ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()
