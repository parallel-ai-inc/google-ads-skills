#!/usr/bin/env python3
"""Size and plan a test: an experiment in Google Ads, a geo test, or an on and off test.

Reads a campaign report segmented by Day. Measures the daily level and spread
of the outcome, checks for a day of week pattern, then works out how many days
the test needs to detect a given lift, or what lift a given number of days can
detect, at a stated confidence and power. Writes a test plan with its dates,
what changes, what stays fixed, the decision rule and the weekly checks.

    python3 design.py REPORT --out OUTPUTDIR [--design experiment|geo|onoff]
        [--campaign "NAME"] [--metric conversions] [--lift 0.15] [--days 28]
        [--split 0.5] [--confidence 0.95] [--power 0.8] [--max-days 56]
        [--start 2026-11-16] [--settle 7] [--change "TEXT"] [--keep "TEXT"]
        [--geo GEO_REPORT --test-regions "A;B" [--control-regions "C;D"] [--kind go-dark|holdback|heavy-up]]
"""
import argparse
import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import testmath  # noqa: E402
from gads import dates, metrics, outputs, xlsx  # noqa: E402

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SIZES = (14, 21, 28, 42, 56)
# User-based Conversion Lift, references/incrementality.md (Official).
LIFT_STUDY_CONVERSIONS = 1000
LIFT_STUDY_SPEND_USD = 5000
# Custom experiments, references/experiments-and-planning.md (Official).
EXPERIMENT_TYPES = {"search", "display", "demand gen", "video"}
NO_EXPERIMENT_TYPES = {"app", "shopping"}
# Geo tests keep at least 3x the test length in pre-test data, references/incrementality.md (Official).
PRE_PERIOD_MULTIPLE = 3
DESIGN_NAMES = {"experiment": "a Google Ads custom experiment (a split of one campaign)",
                "geo": "a geo test (test regions against control regions)",
                "onoff": "an on and off test (whole weeks with ads on, then off)"}


def detectable(design, days, z_total, level, noise, share, count):
    """The smallest relative lift the test can detect in this many measured days."""
    if not level or days <= 0:
        return None
    if design == "experiment":
        cv2 = noise / level ** 2
        if count:
            cv2 = max(cv2, 1.0 / level)
        return math.exp(z_total * math.sqrt(cv2 * (1 / share + 1 / (1 - share)) / days)) - 1
    if count:
        noise = max(noise, level)
    if design == "geo":
        return z_total * math.sqrt(noise * (1 + 1.0 / PRE_PERIOD_MULTIPLE) / days) / level
    return z_total * math.sqrt(noise / (days * share * (1 - share))) / level


def days_needed(design, lift, z_total, level, noise, share, count):
    """The measured days needed to detect this relative lift."""
    if not level or lift <= 0:
        return None
    if design == "experiment":
        cv2 = noise / level ** 2
        if count:
            cv2 = max(cv2, 1.0 / level)
        return int(math.ceil(z_total ** 2 * cv2 * (1 / share + 1 / (1 - share)) / math.log(1 + lift) ** 2))
    if count:
        noise = max(noise, level)
    if design == "geo":
        return int(math.ceil(z_total ** 2 * noise * (1 + 1.0 / PRE_PERIOD_MULTIPLE) / (lift * level) ** 2))
    return int(math.ceil(z_total ** 2 * noise / (share * (1 - share) * (lift * level) ** 2)))


def whole(days, block):
    return int(math.ceil(days / float(block)) * block)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--out", required=True)
    parser.add_argument("--design", choices=("experiment", "geo", "onoff"), default="experiment")
    parser.add_argument("--campaign", action="append", help="campaigns in the test; repeat or separate with ;")
    parser.add_argument("--metric", choices=("conversions", "conv_value", "clicks", "cost"), default="conversions")
    parser.add_argument("--lift", type=float, help="the relative lift that would change the decision, e.g. 0.15")
    parser.add_argument("--days", type=int, help="measured days to plan for when no --lift is given")
    parser.add_argument("--split", type=float, help="experiment: the trial's share (0.5). geo: the test regions' share of the outcome. onoff: the share of days off (0.5)")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--power", type=float, default=0.8)
    parser.add_argument("--max-days", type=int, default=56, help="the longest measurement the plan allows")
    parser.add_argument("--since", help="use the data from this day on, for example after a budget change")
    parser.add_argument("--until", help="use the data up to this day, for example before an earlier test")
    parser.add_argument("--geo-metric", help="the outcome column in the geographic file, for example leads")
    parser.add_argument("--start", help="first day of the test")
    parser.add_argument("--settle", type=int, help="days at the start left out of the reading")
    parser.add_argument("--change", default="", help="what the test changes, in one sentence")
    parser.add_argument("--keep", action="append", default=[], help="something that must stay fixed; repeat")
    parser.add_argument("--geo", help="geographic report by Day, for a geo test")
    parser.add_argument("--test-regions", action="append")
    parser.add_argument("--control-regions", action="append")
    parser.add_argument("--kind", choices=("go-dark", "holdback", "heavy-up"), default="go-dark")
    args = parser.parse_args()
    for name, value in (("--confidence", args.confidence), ("--power", args.power)):
        if not 0.5 <= value < 1:
            raise SystemExit("%s is a share between 0.5 and 1, for example 0.95." % name)
    if args.lift is not None and args.lift <= 0:
        raise SystemExit("--lift is a relative change above zero, for example 0.15 for 15%.")

    meta, rows = common.load(args.report, "campaign report segmented by Day")
    common.require(meta, sorted({"day", "campaign", "cost", "conversions", args.metric}), "campaign report segmented by Day")
    info = {}
    for row in rows:
        name = row.get("campaign")
        if name:
            slot = info.setdefault(name, {})
            for key in ("campaign_status", "campaign_type", "budget_name", "bid_strategy", "serving_status"):
                if row.get(key):
                    slot[key] = row[key]
    if not info:
        raise SystemExit("I can't read any campaign rows. Download the campaign report again with the Campaign column.")

    def serving(name):
        return info[name].get("campaign_status", "Enabled").strip().lower() == "enabled"

    if args.campaign:
        chosen = common.match_names(common.split_names(args.campaign), list(info), "campaign")
    else:
        chosen = sorted(c for c in info if serving(c)) or sorted(info)
    not_serving = [c for c in chosen if not serving(c)]
    count = args.metric in common.COUNT_METRICS
    metric_name = common.METRIC_NAMES[args.metric]

    series = common.daily_series(rows, "campaign", chosen, args.metric, extra=("cost", "conversions"))
    if not series:
        raise SystemExit("I can't read any dated rows for those campaigns. Add the Day segment to the campaign report and download it again.")
    all_days = [d for d in (dates.parse_day(r.get("day")) for r in rows) if d]
    last = max(all_days)
    if meta["date_range"]:
        last = max(last, dates.parse_day(meta["date_range"][1]))
    first = min(series)
    range_start = dates.parse_day(meta["date_range"][0]) if meta["date_range"] else min(all_days)
    since = None
    if args.since:
        since = dates.parse_day(args.since)
        if not since or since >= last:
            raise SystemExit("--since must be a day inside the report, before %s." % last.isoformat())
        first = max(first, since)
    report_last = last
    if args.until:
        until = dates.parse_day(args.until)
        if not until or until <= first:
            raise SystemExit("--until must be a day inside the report, after %s." % first.isoformat())
        last = min(last, until)
    filled = common.fill_days(series, first, last, sorted({args.metric, "cost", "conversions"}))
    day_list = [d for d, _ in filled]
    values = [v[args.metric] for _, v in filled]
    level = testmath.mean(values)
    raw_var = testmath.variance(values) or 0.0
    pattern = testmath.weekday_pattern(day_list, values)
    noise = pattern["within_variance"] if pattern["present"] else raw_var
    mean_cost = testmath.mean([v["cost"] for _, v in filled])
    mean_conv = testmath.mean([v["conversions"] for _, v in filled])

    design = args.design
    share = args.split if args.split is not None else 0.5
    if not 0 < share < 1:
        raise SystemExit("--split is a share between 0 and 1, for example 0.5.")
    geo = None
    test_level, test_noise, noise_source = level, noise, "the daily spread of the campaigns' %s%s" % (
        metric_name, " after removing the weekday pattern" if pattern["present"] else "")
    if design == "geo" and args.geo:
        gmeta, grows = common.load(args.geo, "geographic report segmented by Day")
        tests = common.split_names(args.test_regions)
        if not tests:
            raise SystemExit("Name the test regions with --test-regions, separated by ;.")
        column = common.group_column(gmeta, grows, tests)
        if not column or column == "campaign":
            raise SystemExit("I can't find a location column (Region, City, Metro area, Country/Territory or Postal code) in the geographic report.")
        gm = args.geo_metric or args.metric
        if gm not in common.METRIC_NAMES:
            raise SystemExit("--geo-metric is one of: %s." % ", ".join(sorted(common.METRIC_NAMES)))
        common.require(gmeta, ["day", gm], "geographic report segmented by Day")
        regions = sorted({r.get(column) for r in grows if r.get(column)})
        tests = common.match_names(tests, regions, column.replace("_", " "))
        controls = common.match_names(common.split_names(args.control_regions), regions, column.replace("_", " ")) if args.control_regions else [r for r in regions if r not in tests]
        t_series = common.daily_series(grows, column, tests, gm)
        c_series = common.daily_series(grows, column, controls, gm)
        g_first, g_last = min(list(t_series) + list(c_series)), max(list(t_series) + list(c_series))
        g_first = max(g_first, since) if since else g_first
        g_last = min(g_last, last) if args.until else g_last
        t_filled = common.fill_days(t_series, g_first, g_last, [gm])
        t_vals = [v[gm] for _, v in t_filled]
        c_vals = [v[gm] for _, v in common.fill_days(c_series, g_first, g_last, [gm])]
        fit = testmath.ols([[1.0, x] for x in c_vals], t_vals)
        if fit is None:
            raise SystemExit("The test and control regions do not have enough days to fit one against the other. Download a longer date range.")
        # From here the outcome is the test regions' own series.
        metric_name, count = common.METRIC_NAMES[gm], gm in common.COUNT_METRICS
        day_list, values = [d for d, _ in t_filled], t_vals
        level, raw_var = testmath.mean(values), testmath.variance(values) or 0.0
        pattern = testmath.weekday_pattern(day_list, values)
        first, last = g_first, g_last
        test_level, test_noise = level, fit["sigma2"]
        share = test_level / (test_level + testmath.mean(c_vals)) if (test_level + testmath.mean(c_vals)) else share
        noise_source = "how far the test regions' daily %s stray from what the control regions predict (fit over %d days, R squared %.2f)" % (
            metric_name, len(t_vals), fit["r2"] or 0)
        geo = {"report": os.path.basename(args.geo), "column": column, "test": tests, "control": controls,
               "days": len(t_vals), "r2": fit["r2"], "residual_sd": math.sqrt(fit["sigma2"]), "test_level": test_level,
               "control_level": testmath.mean(c_vals), "test_share": share}
    elif design == "geo":
        test_level, test_noise = share * level, share * noise
        noise_source += ", scaled to the test regions' share of %s. Without a geographic report the script assumes the control regions explain none of the day to day spread, which is the cautious end" % metrics.pct(share, 0)

    z_total = testmath.z_two_sided(args.confidence) + testmath.z_power(args.power)
    sizes = sorted(set([d for d in SIZES if d <= args.max_days] + [args.max_days]))
    table = [(d, detectable(design, d, z_total, test_level, test_noise, share, count)) for d in sizes]
    block = 14 if design == "onoff" else 7
    need, verdict, readable = None, "", None
    mde_max = detectable(design, args.max_days, z_total, test_level, test_noise, share, count)
    if args.lift:
        need = days_needed(design, args.lift, z_total, test_level, test_noise, share, count)
        readable = need is not None and whole(need, block) <= args.max_days
        planned = whole(need, block) if readable else (args.max_days // block) * block or block
        if readable:
            verdict = "Readable. A lift of %s in %s needs %d measured days, planned as %d days so every weekday counts the same." % (
                metrics.pct(args.lift, 0), metric_name, need, planned)
        else:
            verdict = "Too little volume. A lift of %s in %s needs %s measured days, longer than the %d day limit. In %d days the smallest lift this test could detect is %s." % (
                metrics.pct(args.lift, 0), metric_name, "{:,}".format(need) if need else "more than any", args.max_days, args.max_days, metrics.pct(mde_max, 0))
    else:
        planned = whole(args.days or 28, block)
        verdict = "In %d measured days the smallest lift this test could detect is %s. Give the lift that would change the decision with --lift to get a verdict." % (
            planned, metrics.pct(detectable(design, planned, z_total, test_level, test_noise, share, count), 0))
    mde_planned = detectable(design, planned, z_total, test_level, test_noise, share, count)
    if count and test_level < 1:
        verdict += " The %s average fewer than one a day, so any test of them is slow to read." % metric_name

    start = dates.parse_day(args.start) if args.start else report_last + dt.timedelta(days=7 - report_last.weekday())
    if not start:
        raise SystemExit("Write --start as a date, for example 2026-11-16.")
    settle = args.settle if args.settle is not None else {"experiment": 7, "geo": 5 if args.kind == "heavy-up" else 0, "onoff": 0}[design]
    measure_start = start + dt.timedelta(days=settle)
    stop = measure_start + dt.timedelta(days=planned - 1)
    run_days = (stop - start).days + 1
    plan = {"design": design, "start": start.isoformat(), "settle_days": settle, "measure_from": measure_start.isoformat(),
            "stop": stop.isoformat(), "run_days": run_days, "measured_days": planned, "change": args.change}
    history_days = len(day_list) if geo else (last - range_start).days + 1
    if design == "geo":
        pre_days = PRE_PERIOD_MULTIPLE * run_days
        plan["pre_period"] = [(start - dt.timedelta(days=pre_days)).isoformat(), (start - dt.timedelta(days=1)).isoformat()]
        plan["pre_period_days"] = pre_days
        plan["kind"] = args.kind
    blocks = []
    if design == "onoff":
        for i in range(planned // 7):
            a = measure_start + dt.timedelta(days=7 * i)
            blocks.append({"from": a.isoformat(), "to": (a + dt.timedelta(days=6)).isoformat(), "ads": "Off" if i % 2 == 0 else "On"})
        plan["blocks"] = blocks

    keep = list(args.keep)
    official, practitioner = [], []
    if design == "experiment":
        practitioner += ["The base campaign's budget, bid strategy, targets, keywords, ads and audiences, other than the change under test.",
                         "The conversion actions and their settings, in both arms."]
        official += ["The %s split. It sets which auctions each arm can enter, not equal impressions or spend." % metrics.pct(share, 0),
                     "Experiment sync is turned off if edits made to the trial arm must not be overwritten."]
    elif design == "geo":
        official += ["Test and control regions are targeted with the Presence location option.",
                     "Holdback and go dark campaigns each keep their own budget. No budget is shared across test and control.",
                     "Budgets move less than 20% during the test: the geo test guidance says a larger change starts a new learning period."]
        if args.kind == "heavy-up":
            official.append("Duplicated campaigns are made early, so their learning period falls before the reading starts.")
        practitioner += ["Ads, keywords and bids are the same in test and control regions.",
                         "The outcome is counted the same way in every region: the business's own leads or sales by region."]
    else:
        practitioner += ["Off means paused for the whole week, not a lower budget.",
                         "Every other campaign keeps its budget and bids.",
                         "The outcome is the business total (all leads or sales), counted the same way every week."]
    weekly = []
    week = 0
    while start + dt.timedelta(days=7 * week + 6) <= stop + dt.timedelta(days=6):
        weekly.append((start + dt.timedelta(days=7 * week + 6)).isoformat())
        week += 1
    checks = {"experiment": ["Both arms served all week. The trial's share of impressions is near the split; a gap is normal, a collapse is not.",
                             "No edits were made to either arm other than the planned change.",
                             "Conversions recorded every day in both arms. A day at zero is a tracking problem, not a result.",
                             "Neither arm is limited by budget more than the other (Search lost IS (budget)).",
                             "Do not call the result from a weekly look. Read it once, on the stop date."],
              "geo": ["Cost in the go dark or holdback regions is zero, or the planned level for a heavy up.",
                      "The control regions spent at their usual level.",
                      "The business's leads or sales by region arrived for every day.",
                      "No campaign added or changed location targets during the test.",
                      "Do not call the result from a weekly look. Read it once, on the stop date."],
              "onoff": ["The campaign was fully paused in the off week and fully serving in the on week.",
                        "Other campaigns kept their budgets and bids.",
                        "The business total arrived for every day.",
                        "Do not call the result from a weekly look. Read it once, after the last block."]}[design]

    conf = metrics.pct(args.confidence, 0)
    if design == "experiment":
        rule = ("On %s, read Google's experiment report for %s at %s confidence. If the trial is higher and Google marks it statistically significant, "
                "apply the trial. If it is lower and significant, end the experiment and keep the original. If it is not significant, keep the original: "
                "the test found no lift of %s or more.") % (stop.isoformat(), metric_name, conf, metrics.pct(mde_planned, 0))
    elif design == "geo":
        side = "above zero" if args.kind == "heavy-up" else "below zero"
        rule = ("On %s, run the readout with the pre-period %s to %s. If the %s interval for the change in %s in the test regions is entirely %s, "
                "the ads cause %s at that size: compare the cost of each incremental one with what it is worth to the business. "
                "If the interval includes zero, the test found no effect of %s or more.") % (
            stop.isoformat(), plan["pre_period"][0], plan["pre_period"][1], conf, metric_name, side, metric_name, metrics.pct(mde_planned, 0))
    else:
        rule = ("After the last block on %s, run the readout. If the %s interval for the off weeks is entirely below zero, the ads cause that share of the "
                "business total. If it includes zero, the test found no effect of %s or more, and the money is better tested elsewhere.") % (
            stop.isoformat(), conf, metrics.pct(mde_planned, 0))

    # Eligibility, from the report where it can tell.
    budget_users = {}
    for name in info:
        b = info[name].get("budget_name")
        if b:
            budget_users.setdefault(b, []).append(name)
    eligibility = []
    if design == "experiment":
        for name in chosen:
            c = info[name]
            kind = (c.get("campaign_type") or "").strip()
            blocks_it, notes = [], []
            if not serving(name):
                blocks_it.append("not Enabled: the base campaign must be active")
            if kind.lower() in NO_EXPERIMENT_TYPES:
                blocks_it.append("%s campaigns can't use custom experiments" % kind)
            elif kind and kind.lower() not in EXPERIMENT_TYPES:
                notes.append("%s: check Google's own experiment type for it" % kind)
            shared = [o for o in budget_users.get(c.get("budget_name"), []) if o != name]
            if shared:
                blocks_it.append("shares its budget with %s; a custom experiment needs its own budget" % ", ".join(shared))
            if "budget_name" not in meta["columns"]:
                notes.append("budget: not in the report, check it has its own")
            notes.append("bid strategy: check it is not a portfolio strategy")
            eligibility.append({"campaign": name, "type": kind or "not in report", "status": c.get("campaign_status", "not in report"),
                                "blocked": bool(blocks_it), "notes": blocks_it + notes})
    conv_run = mean_conv * run_days if mean_conv is not None else None
    cost_run = mean_cost * run_days if mean_cost is not None else None

    payload = {"report": os.path.basename(args.report), "title_rows": meta["title_rows"], "data_from": first.isoformat(),
               "data_to": last.isoformat(), "days": len(day_list), "report_range_start": range_start.isoformat(),
               "campaigns": chosen, "campaigns_not_serving": not_serving, "metric": args.metric,
               "level_per_day": level, "raw_sd": math.sqrt(raw_var), "weekday": {
                   "checked": pattern["checked"], "present": pattern["present"], "f": pattern["f"], "p": pattern["p"],
                   "index": {WEEKDAYS[k]: v for k, v in pattern["index"].items()},
                   "within_sd": math.sqrt(pattern["within_variance"]) if pattern["within_variance"] else None},
               "noise_sd_used": math.sqrt(test_noise), "test_level_per_day": test_level, "share": share, "noise_source": noise_source,
               "confidence": args.confidence, "power": args.power, "lift_asked": args.lift, "days_needed": need,
               "readable": readable, "verdict": verdict, "max_days": args.max_days, "detectable_at_max_days": mde_max,
               "detectable_at_planned_days": mde_planned, "sizes": [{"days": d, "detectable_lift": v} for d, v in table],
               "plan": plan, "keep_fixed": {"yours": keep, "official": official, "practitioner": practitioner},
               "decision_rule": rule, "weekly_checks": {"dates": weekly, "checks": checks}, "eligibility": eligibility,
               "geo": geo, "lift_study": {"conversions_over_run": conv_run, "cost_over_run": cost_run,
                                          "threshold_conversions": LIFT_STUDY_CONVERSIONS, "threshold_spend_usd": LIFT_STUDY_SPEND_USD},
               "reconcile": common.reconcile(meta, rows), "history_days": history_days}

    book = xlsx.Workbook()
    plan_rows = [["Design", DESIGN_NAMES[design]], ["Campaigns", "; ".join(chosen)], ["Outcome", metric_name],
                 ["What changes", args.change or "(to be written)"], ["Start", plan["start"]], ["Days left out at the start", settle],
                 ["Reading from", plan["measure_from"]], ["Stop", plan["stop"]], ["Measured days", planned]]
    if design == "geo":
        plan_rows += [["Pre-period for the readout", "%s to %s" % tuple(plan["pre_period"])], ["Test regions", "; ".join(geo["test"]) if geo else "(to be chosen)"],
                      ["Control regions", "; ".join(geo["control"]) if geo else "(to be chosen)"]]
    plan_rows += [["Smallest lift it can detect", metrics.pct(mde_planned, 1)], ["Confidence", conf], ["Power", metrics.pct(args.power, 0)],
                  ["Verdict", verdict], ["Decision rule", rule]]
    plan_rows += [["Stays fixed (yours)", k] for k in keep] + [["Stays fixed (Official)", k] for k in official] + [["Stays fixed (Practitioner rule)", k] for k in practitioner]
    book.add_sheet("Plan", ["Item", "Value"], plan_rows, formats={1: "wrap"}, widths={0: 30, 1: 100})
    book.add_sheet("What it can detect", ["Measured days", "Smallest lift it can detect"], [[d, v] for d, v in table], formats={0: "int", 1: "pct"}, widths={1: 28})
    book.add_sheet("Weekly checks", ["Week ending"] + ["Check %d" % (i + 1) for i in range(len(checks))],
                   [[w] + checks for w in weekly], formats={i + 1: "wrap" for i in range(len(checks))}, widths={i + 1: 40 for i in range(len(checks))})
    if blocks:
        book.add_sheet("Blocks", ["From", "To", "Ads"], [[b["from"], b["to"], b["ads"]] for b in blocks])
    if eligibility:
        book.add_sheet("Eligibility", ["Campaign", "Type", "Status", "Notes"], [[e["campaign"], e["type"], e["status"], "; ".join(e["notes"])] for e in eligibility],
                       formats={3: "wrap"}, widths={0: 30, 3: 90})
    book.add_sheet("Daily outcome", ["Day", "Weekday", metric_name.capitalize()],
                   [[d.isoformat(), WEEKDAYS[d.weekday()], round(v, 2)] for d, v in zip(day_list, values)], formats={2: "money"})
    if pattern["checked"]:
        book.add_sheet("Weekday pattern", ["Weekday", "Against the daily average"], [[WEEKDAYS[k], v] for k, v in pattern["index"].items()], formats={1: "pct"})

    shown = (lambda v: metrics.money(v)) if args.metric in ("cost", "conv_value") else (lambda v: common.number(v))
    lines = ["# Test plan", ""] + ["%s." % t for t in meta["title_rows"]]
    lines += ["", "The data covers %d days, %s to %s, for %s." % (len(day_list), first.isoformat(), last.isoformat(),
                                                                  "the test regions in %s" % geo["report"] if geo else "; ".join(chosen))]
    if since:
        lines.append("Only the days from %s on are used, as asked, so an earlier change does not count as noise." % first.isoformat())
    elif not geo and first > range_start:
        lines.append("The report's range starts on %s, but these campaigns first show on %s, so the averages use the %d days they cover." % (
            range_start.isoformat(), first.isoformat(), len(filled)))
    if common.currency_line(rows):
        lines.append(common.currency_line(rows))
    lines += ["", "## The answer", "", verdict, "", "Design: %s. %s" % (DESIGN_NAMES[design], (
        "Run %s to %s, reading from %s." % (plan["start"], plan["stop"], plan["measure_from"])))]
    if not_serving:
        lines += ["", "**Not serving:** %s. A test needs campaigns that serve; say whether turning one on is the test." % ", ".join(not_serving)]
    lines += ["", "## The outcome, day by day", "",
              "- %s a day: %s on average, with a spread (standard deviation) of %s." % (metric_name.capitalize(), shown(level), shown(math.sqrt(raw_var)))]
    if pattern["checked"]:
        if pattern["present"]:
            busiest = max(pattern["index"], key=pattern["index"].get)
            quietest = min(pattern["index"], key=pattern["index"].get)
            tail = ("The control regions share it, so the fit against them takes it out." if geo else
                    "The spread used is the one left after the weekday pattern, %s." % shown(math.sqrt(pattern["within_variance"])))
            lines.append("- There is a weekday pattern (p = %.3f): %s runs at %s of the daily average, %s at %s. The plan runs whole weeks. %s" % (
                pattern["p"], WEEKDAYS[busiest], metrics.pct(pattern["index"][busiest], 0), WEEKDAYS[quietest],
                metrics.pct(pattern["index"][quietest], 0), tail))
        else:
            lines.append("- No clear weekday pattern (p = %.3f). The plan still runs whole weeks." % pattern["p"])
    else:
        lines.append("- Too few days to check for a weekday pattern; at least two of each weekday are needed.")
    lines.append("- The noise used: %s." % noise_source)
    if geo:
        lines.append("- Test regions: %s. Control regions: %s. The test regions carry %s of the %s." % (
            "; ".join(geo["test"]), "; ".join(geo["control"]), metrics.pct(geo["test_share"], 0), metric_name))
    lines += ["", "## What lift it can detect", "", "At %s confidence and %s power:" % (conf, metrics.pct(args.power, 0)), "",
              outputs.md_table(["Measured days", "Smallest lift it can detect"], [[d, metrics.pct(v, 1)] for d, v in table])]
    lines +=["", "## The plan", "",
              "- **What changes:** %s" % (args.change or "(write the one change under test here)"),
              "- **Start:** %s. **Left out at the start:** %d days%s. **Reading:** %s to %s, %d days. **Stop:** %s." % (
                  plan["start"], settle, " (the trial arm settling)" if design == "experiment" and settle else (" (learning)" if settle else ""),
                  plan["measure_from"], plan["stop"], planned, plan["stop"])]
    if design == "geo":
        lines.append("- **Pre-period for the readout:** %s to %s, %d days, three times the test length. The history read here holds %d days%s." % (
            plan["pre_period"][0], plan["pre_period"][1], plan["pre_period_days"], history_days,
            "" if history_days >= plan["pre_period_days"] else ": download the longer range before the readout"))
    for b in blocks:
        lines.append("- %s to %s: ads %s." % (b["from"], b["to"], b["ads"].lower()))
    lines += ["- **Stays fixed:**"]
    lines += ["  - %s" % k for k in keep]
    lines += ["  - %s **Official**, `references/%s`." % (k, "experiments-and-planning.md" if design == "experiment" else "incrementality.md") for k in official]
    lines += ["  - %s **Practitioner rule.**" % k for k in practitioner]
    lines += ["- **Decision rule, written before the test starts:** %s" % rule,
              "- **Each week** (%s), check:" % ", ".join(weekly)]
    lines += ["  - %s" % c for c in checks]
    if eligibility:
        lines += ["", "## Eligibility for a custom experiment", "",
                  "**Official** (`references/experiments-and-planning.md`): custom experiments run on Search, Display, Demand Gen and Video campaigns whose base campaign is active, on its own daily budget and a standard (not portfolio) bid strategy. App and Shopping campaigns can't use them.", ""]
        lines += ["- **%s** (%s, %s): %s." % (e["campaign"], e["type"], e["status"], "; ".join(e["notes"])) for e in eligibility]
    lines += ["", "## Lift studies run by Google", "",
              "**Official** (`references/incrementality.md`): user based Conversion Lift needs at least %s observed conversions, a %s US dollar minimum campaign budget and a compatible conversion action, runs at least 7 days (14 recommended), and goes through a Google account representative. It is not available to every account." % (
                  "{:,}".format(LIFT_STUDY_CONVERSIONS), "{:,}".format(LIFT_STUDY_SPEND_USD)),
              "- Over the %d day run, these campaigns would record about %s conversions and spend about %s in the account's currency, at their daily average." % (
                  run_days, common.number(conv_run, 0), metrics.money(cost_run)),
              "- %s" % ("That is below the %s conversion floor." % "{:,}".format(LIFT_STUDY_CONVERSIONS) if (conv_run or 0) < LIFT_STUDY_CONVERSIONS else
                        "That reaches the %s conversion floor; ask the Google account representative whether the account is eligible." % "{:,}".format(LIFT_STUDY_CONVERSIONS))]
    lines += ["", "## How the numbers were made", "",
              "- " + common.reconcile_line(payload["reconcile"]),
              "- Days with no row in the report count as zero between the first and last day.",
              "- The lift sizes use the normal approximation written out in `references/test-math.md`: confidence %s two sided, power %s." % (conf, metrics.pct(args.power, 0)),
              "- %s" % {"experiment": "For an experiment the spread is treated as noise in each arm, scaled to its share. This is cautious: both arms run on the same days, so swings they share cancel. Counts are never treated as less noisy than a Poisson count.",
                        "geo": "For a geo test the noise is the test regions' daily stray from what the control regions predict, with a pre-period three times the test length.",
                        "onoff": "For an on and off test the effect is the difference between off weeks and on weeks after the weekday pattern."}[design],
              "- Measured days are rounded up to whole weeks%s. The longest plan allowed is %d days (`--max-days`)." % (" and an even number of weeks" if design == "onoff" else "", args.max_days),
              "", "## What this did not cover", "",
              "- The report shows what Google Ads attributed, not what the ads caused. That is the question the test answers.",
              "- Whether the account can run Google's own lift studies: only Google can confirm that.",
              "- Late conversions: the readout should wait until the conversion lag has passed.", ""]
    text = "\n".join(lines)
    common.finish(outputs.ensure_dir(args.out), "test-plan", text, payload, book)


if __name__ == "__main__":
    main()
