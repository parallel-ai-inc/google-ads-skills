#!/usr/bin/env python3
"""Read the result of a test that has run.

Three kinds of test, and a step that finds one:

experiment  A Google Ads experiment: the control and trial arms' metrics,
            by day or in total, or Google's own scorecard (one row per metric
            with Google's difference, range and significance). Where Google
            gives significance, its figure is shown and not replaced.
daily       Test and control groups by day: regions in a geo test, or two
            campaigns. Fits the test group on the control group before the
            test and measures how far the test group moved from that during
            it (time-based regression).
onoff       One series by day with weeks of ads off: compares off days with
            on days, after the weekday pattern.
find        Finds the test regions and dates in a cost report by region and
            day (cost stops), with a first look at the outcome against the
            other regions, for the person to confirm.

    python3 readout.py experiment EXPORT --out DIR [--split 0.5] [--control NAME --trial NAME] [--from DAY] [--to DAY]
    python3 readout.py daily REPORT --out DIR --test "A;B" --during START:END [--control "C;D"] [--control-report FILE]
        [--pre START:END] [--metric leads] [--value-metric revenue] [--kind go-dark|holdback|heavy-up] [--cost-report FILE]
        [--margin 0.40] [--value-per-outcome 250] [--inferred]
    python3 readout.py onoff REPORT --out DIR --off START:END [--off START:END] [--names "A;B"] [--metric leads]
    python3 readout.py find COST_BY_REGION --out DIR [--outcome LEADS_BY_REGION]
"""
import argparse
import datetime as dt
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import testmath  # noqa: E402
from geo import outcome_metric, run_daily, run_find  # noqa: E402
from gads import dates, io, metrics, outputs, xlsx  # noqa: E402

EXPERIMENT_ALIASES = {
    "experiment arm": "arm", "experiment arms": "arm", "arm": "arm", "arm type": "arm", "arm name": "arm",
    "metric": "metric", "control": "control_value", "control arm": "control_value", "control campaign": "control_value",
    "control average": "control_value", "treatment": "trial_value", "trial": "trial_value", "treatment arm": "trial_value",
    "trial arm": "trial_value", "treatment campaign": "trial_value", "trial campaign": "trial_value", "treatment average": "trial_value",
    "difference": "g_diff", "% difference": "g_diff", "difference (%)": "g_diff", "relative difference": "g_diff",
    "treatment minus control": "g_diff", "confidence interval": "g_ci", "range": "g_ci", "confidence range": "g_ci",
    "lower bound": "g_low", "upper bound": "g_high", "statistically significant": "g_sig", "significance": "g_sig",
    "statistical significance": "g_sig", "p-value": "g_p", "p value": "g_p", "margin of error": "g_moe",
    "results": "g_result", "result": "g_result",
}
# label, numerator, denominator, which way is better (1 higher, -1 lower, 0 neither)
ARM_METRICS = [("Impr.", "impressions", None, 0), ("Clicks", "clicks", None, 0), ("Cost", "cost", None, 0),
               ("Conversions", "conversions", None, 1), ("Conv. value", "conv_value", None, 1), ("CTR", "clicks", "impressions", 1),
               ("Avg. CPC", "cost", "clicks", -1), ("Conv. rate", "conversions", "clicks", 1),
               ("Cost / conv.", "cost", "conversions", -1), ("Conv. value / cost", "conv_value", "cost", 1)]
LOWER_IS_BETTER = ("cost / conv", "cost per conv", "avg. cpc", "cpc", "cpa", "avg. cpm", "cost per")
VALUE_METRICS = ("revenue", "conv_value", "sales")
PERCENT_NUMBER = re.compile(r"[-+]?\d[\d,]*(?:\.\d+)?\s*%?")


def relative(text, base):
    """'+12.3%' -> 0.123. A plain number is an absolute difference in the metric's units, divided by the control."""
    text = (text or "").strip()
    if not text or text in ("--", "-"):
        return None
    value = io.to_number(text)
    if value is None:
        return None
    if "%" in text:
        return value / 100.0
    return value / base if base else None


def arm_value(text):
    """'11.85%' -> 0.1185, '5,989.51' -> 5989.51."""
    value = io.to_number(text)
    if value is not None and "%" in str(text):
        value /= 100.0
    return value


def significance(text):
    t = (text or "").strip().lower()
    if not t or t == "--":
        return None
    if "not" in t or t in ("no", "false", "n"):
        return False
    if t in ("yes", "true", "y", "*") or "significant" in t:
        return True
    return None


def verdict(low, high, direction, significant=None):
    if significant is None:
        if low is None or high is None:
            return "No interval"
        significant = low > 0 or high < 0
    if not significant:
        return "No clear difference"
    up = (high or 0) > 0 if low is None else low > 0
    word = "Higher" if up else "Lower"
    if direction:
        word += ", better" if (up and direction > 0) or (not up and direction < 0) else ", worse"
    return word


def scorecard(meta, rows, args):
    """Google's own figures, one row per metric. Google's significance is shown as given."""
    out = []
    for row in rows:
        name = (row.get("metric") or "").strip()
        if not name:
            continue
        control, trial = arm_value(row.get("control_value")), arm_value(row.get("trial_value"))
        diff = relative(row.get("g_diff"), control)
        low = high = None
        if row.get("g_ci"):
            found = PERCENT_NUMBER.findall(row["g_ci"])
            if len(found) >= 2:
                low, high = relative(found[0], control), relative(found[1], control)
        low = relative(row.get("g_low"), control) if row.get("g_low") else low
        high = relative(row.get("g_high"), control) if row.get("g_high") else high
        if low is None and diff is not None and row.get("g_moe"):
            moe = relative(row["g_moe"], control)
            if moe is not None:
                low, high = diff - moe, diff + moe
        sig, source = significance(row.get("g_sig")), "Google"
        if sig is None and row.get("g_p") is not None:
            sig, source = row["g_p"] < 1 - args.confidence, "Google's p-value"
        if sig is None and low is not None and high is not None:
            sig, source = low > 0 or high < 0, "Google's range"
        computed = None
        if diff is None and control and trial is not None:
            diff, computed = trial / control - 1, "our arithmetic from the two arms"
        if sig is None:
            source = "none"
        direction = -1 if any(k in name.lower() for k in LOWER_IS_BETTER) else (0 if name.lower() in ("cost", "impr.", "clicks") else 1)
        out.append({"metric": name, "control": control, "trial": trial, "difference": diff, "low": low, "high": high,
                    "significant": sig, "p": row.get("g_p"), "source": source, "difference_source": computed or "Google",
                    "verdict": verdict(low, high, direction, sig) if sig is not None else "Google gave no significance",
                    "google_text": {k: row.get(k) for k in ("g_diff", "g_ci", "g_sig", "g_low", "g_high", "g_moe") if row.get(k)}})
    if not out:
        raise SystemExit("The scorecard has no metric rows. Copy one row per metric: Metric, Control, Treatment, Difference, Confidence interval, Statistically significant.")
    return out


def arms(meta, rows, args):
    """The two arms' metrics, by day when the file has days. Our own interval."""
    if "arm" in meta["columns"]:
        def side(row):
            v = (row.get("arm") or "").lower()
            if "control" in v or "base" in v or "original" in v:
                return "control"
            if "treatment" in v or "trial" in v or "experiment" in v:
                return "trial"
            return None
        found = sorted({row.get("arm") for row in rows if row.get("arm") and side(row) is None})
        if found:
            raise SystemExit("I can't tell which arm these are: %s. Name them Control and Treatment, or use --control and --trial with campaign names." % ", ".join(found))
    else:
        names = sorted({row.get("campaign") for row in rows if row.get("campaign")})
        control = common.match_names([args.control], names, "campaign")[0]
        trial = common.match_names([args.trial], names, "campaign")[0]

        def side(row):
            return "control" if row.get("campaign") == control else ("trial" if row.get("campaign") == trial else None)
    start = dates.parse_day(args.from_day) if args.from_day else None
    end = dates.parse_day(args.to_day) if args.to_day else None
    by_day, totals, skipped = {}, {"control": {}, "trial": {}}, 0
    has_days = "day" in meta["columns"]
    for row in rows:
        s = side(row)
        if not s:
            continue
        day = dates.parse_day(row.get("day")) if has_days else None
        if has_days and (not day or (start and day < start) or (end and day > end)):
            skipped += 1
            continue
        for key in ("impressions", "clicks", "cost", "conversions", "conv_value"):
            v = row.get(key) or 0.0
            totals[s][key] = totals[s].get(key, 0.0) + v
            if has_days:
                by_day.setdefault(day, {"control": {}, "trial": {}})[s][key] = by_day.setdefault(day, {"control": {}, "trial": {}})[s].get(key, 0.0) + v
    if not totals["control"] or not totals["trial"]:
        raise SystemExit("The file needs rows for both arms, the control and the trial.")
    pairs = [(by_day[d]["trial"], by_day[d]["control"]) for d in sorted(by_day) if by_day[d]["trial"] and by_day[d]["control"]]
    adjust_sum = (1 - args.split) / args.split
    results = []
    for label, num, den, direction in ARM_METRICS:
        if num not in meta["columns"] or (den and den not in meta["columns"]):
            continue
        c_val = metrics.div(totals["control"].get(num), totals["control"].get(den)) if den else totals["control"].get(num)
        t_val = metrics.div(totals["trial"].get(num), totals["trial"].get(den)) if den else totals["trial"].get(num)
        adjust = 1.0 if den else adjust_sum
        est = testmath.ratio_lift(pairs, num, den, adjust, args.confidence) if len(pairs) >= 7 else None
        if est is None and not has_days:
            if den is None and num in ("impressions", "clicks", "conversions"):
                est = testmath.count_lift(t_val, c_val, adjust, args.confidence)
            elif (num, den) in (("clicks", "impressions"), ("conversions", "clicks")):
                est = testmath.count_lift(None, None, 1.0, args.confidence, rate_numerators=(
                    (totals["trial"].get(num), totals["trial"].get(den)), (totals["control"].get(num), totals["control"].get(den))))
        diff = (t_val * (adjust if not den else 1.0) / c_val - 1) if (t_val is not None and c_val) else None
        results.append({"metric": label, "control": c_val, "trial": t_val, "difference": diff,
                        "low": est["low"] if est else None, "high": est["high"] if est else None, "p": est["p"] if est else None,
                        "significant": (est["low"] > 0 or est["high"] < 0) if est else None,
                        "source": "ours" if est else "none", "method": est["method"] if est else None,
                        "verdict": verdict(est["low"], est["high"], direction) if est else ("No interval: this needs the arms by day" if not has_days else "No interval: too few days"),
                        "difference_source": "our arithmetic from the two arms"})
    share = metrics.div(totals["trial"].get("impressions"), (totals["trial"].get("impressions") or 0) + (totals["control"].get("impressions") or 0))
    days = sorted(by_day)
    return results, {"days": len(pairs), "from": days[0].isoformat() if days else None, "to": days[-1].isoformat() if days else None,
                     "rows_skipped": skipped, "trial_share_of_impressions": share, "totals": totals,
                     "daily": [[d.isoformat(), by_day[d]["control"].get("conversions", 0.0), by_day[d]["trial"].get("conversions", 0.0),
                                by_day[d]["control"].get("cost", 0.0), by_day[d]["trial"].get("cost", 0.0)] for d in days]}


def run_experiment(args):
    meta, rows = common.load(args.report, "experiment report", EXPERIMENT_ALIASES, numeric=("g_p",))
    if not 0 < args.split < 1:
        raise SystemExit("--split is the trial's share, between 0 and 1, for example 0.5.")
    result_text = sorted({r.get("g_result") for r in rows if r.get("g_result")})
    info = {}
    if "metric" in meta["columns"] and "control_value" in meta["columns"] and "trial_value" in meta["columns"]:
        form, results = "scorecard", scorecard(meta, rows, args)
    elif "arm" in meta["columns"] or (args.control and args.trial and "campaign" in meta["columns"]):
        form = "arms"
        results, info = arms(meta, rows, args)
    else:
        raise SystemExit("I can't tell the control from the trial in this file. Download the experiment's report with a column that names "
                         "the arm (Control or Treatment), or name the two campaigns with --control and --trial.")
    check = common.reconcile(meta, rows, ("cost", "clicks")) if form == "arms" else {"checked": False}
    google = any(r["source"].startswith("Google") for r in results)
    payload = {"kind": "experiment", "form": form, "report": os.path.basename(args.report), "title_rows": meta["title_rows"],
               "confidence": args.confidence, "split": args.split, "google_result": result_text, "results": results,
               "google_significance_used": google, "arms": info, "reconcile": check}

    def pct_or(v):
        return common.signed(v) if v is not None else "n/a"

    def val(v, label):
        if v is None:
            return "n/a"
        if label.lower() in ("ctr", "conv. rate", "conversion rate", "interaction rate", "search impr. share"):
            return metrics.pct(v, 2)
        if form == "scorecard":
            return common.number(v)
        return "{:,.0f}".format(v) if label in ("Impr.", "Clicks") else common.number(v)

    header = ["Metric", "Control", "Trial", "Difference", "Range low", "Range high", "Significant", "Verdict", "Whose figure"]
    table = [[r["metric"], val(r["control"], r["metric"]), val(r["trial"], r["metric"]), pct_or(r["difference"]), pct_or(r["low"]), pct_or(r["high"]),
              {True: "Yes", False: "No", None: "n/a"}[r["significant"]], r["verdict"], r["source"]] for r in results]
    book = xlsx.Workbook()
    book.add_sheet("Result", header, [[r["metric"], r["control"], r["trial"], r["difference"], r["low"], r["high"],
                                       {True: "Yes", False: "No", None: ""}[r["significant"]], r["verdict"], r["source"]] for r in results],
                   formats={1: "money", 2: "money", 3: "pct", 4: "pct", 5: "pct"}, widths={0: 20, 7: 28, 8: 50})
    if info.get("daily"):
        book.add_sheet("Arms by day", ["Day", "Control conv.", "Trial conv.", "Control cost", "Trial cost"], info["daily"],
                       formats={1: "money", 2: "money", 3: "money", 4: "money"})
    lines = ["# Experiment readout", ""] + ["%s." % t for t in meta["title_rows"]] + [""]
    lines += ["## The answer", ""]
    if result_text:
        lines.append("Google's own result for the experiment: %s." % "; ".join(result_text))
    main_row = next((r for r in results if r["metric"].lower() == args.metric.lower()), None)
    if main_row:
        lines.append("- **%s, the outcome asked about:** %s, range %s to %s at %s confidence. %s. Figure: %s." % (
            main_row["metric"], pct_or(main_row["difference"]), pct_or(main_row["low"]), pct_or(main_row["high"]),
            metrics.pct(args.confidence, 0), main_row["verdict"], main_row["source"]))
    clear = [r for r in results if r["significant"] and r is not main_row]
    unclear = [r["metric"] for r in results if r["significant"] is False and r is not main_row]
    if clear:
        lines.append("- Clearly different: %s." % "; ".join("%s %s (%s, figure: %s)" % (r["metric"], pct_or(r["difference"]), r["verdict"].lower(), r["source"]) for r in clear))
    if unclear:
        lines.append("- No clear difference: %s." % ", ".join(unclear))
    payload["main_metric"] = main_row["metric"] if main_row else None
    if not any(r["significant"] is not None for r in results):
        lines.append("No metric has a significance figure. Download the arms by day, or copy Google's scorecard, and run this again.")
    lines += ["", "## Every metric", "", outputs.md_table(header, table), ""]
    if form == "arms":
        lines += ["- Days read: %d, %s to %s.%s" % (info["days"], info["from"], info["to"],
                                                   " %d rows outside the dates asked for were left out (`--from` and `--to`)." % info["rows_skipped"] if info["rows_skipped"] else ""),
                  "- The trial took %s of impressions with a %s split. **Official** (`references/experiments-and-planning.md`): the split sets which auctions each arm can enter, not equal impressions or spend." % (
                      metrics.pct(info["trial_share_of_impressions"], 1), metrics.pct(args.split, 0)),
                  "- Totals (Impr., Clicks, Cost, Conversions, Conv. value) are compared after scaling each arm to its share of the split. Rates and ratios are compared as they are.", ""]
    lines += ["## How the numbers were made", ""]
    if google:
        lines.append("- Where Google's report gives significance, a range or a p-value, that is the figure shown, as Google gave it. **Official** (`references/experiments-and-planning.md`): read significance from Google's figures rather than recomputing it from campaign totals.")
    if form == "arms":
        lines.append("- " + common.reconcile_line(check))
        lines.append("- Our range: each day is one observation of both arms; the log of the trial over control ratio gets its spread from how the days vary (delta method), with a t value for the number of days. Days both arms shared cancel out. See `references/test-math.md`.")
    lines += ["- Confidence: %s, two sided. A metric is called different only when its whole range sits on one side of zero." % metrics.pct(args.confidence, 0),
              "", "## What this did not cover", "",
              "- An experiment compares two setups of the same campaign. It says which one Google Ads attributes more to, not how much the ads cause in total.",
              "- Conversions still to come in from late reporting. Read again after the conversion lag has passed.", ""]
    return payload, book, "\n".join(lines)


def run_onoff(args):
    meta, rows = common.load(args.report, "daily report")
    common.require(meta, ["day"], "daily report")
    metric = outcome_metric(meta, args.metric)
    names = common.split_names(args.names)
    col = common.group_column(meta, rows, names) if names else None
    if names:
        names = common.match_names(names, sorted({r.get(col) for r in rows if r.get(col)}), (col or "group").replace("_", " "))
    extra = ("cost",) if "cost" in meta["columns"] else ()
    series = common.daily_series(rows, col, names or None, metric, extra=extra)
    if not series:
        raise SystemExit("I can't read any dated rows. Check the names and that the report is segmented by Day.")
    first, last = min(series), max(series)
    offs = [common.span(text) for text in args.off]
    filled = common.fill_days(series, first, last, (metric,) + extra)
    off_flags = [any(a <= d <= b for a, b in offs) for d, _ in filled]
    if sum(off_flags) < 3 or len(filled) - sum(off_flags) < 3 or len(filled) < 14:
        raise SystemExit("The file needs at least 14 days, with at least 3 days off and 3 on. It has %d days, %d off." % (len(filled), sum(off_flags)))
    X = [[1.0 if d.weekday() == k else 0.0 for k in range(7)] + [1.0 if off else 0.0] for (d, _), off in zip(filled, off_flags)]
    y = [v[metric] for _, v in filled]
    fit = testmath.ols(X, y)
    if fit is None:
        raise SystemExit("Every weekday needs both on and off days around it to compare. Use a longer file or whole weeks off.")
    gamma = fit["coef"][7]
    se = math.sqrt(fit["sigma2"] * fit["inv"][7][7])
    tq = testmath.t_quantile(1 - (1 - args.confidence) / 2, fit["df"])
    low, high = gamma - tq * se, gamma + tq * se
    off_days = [i for i, off in enumerate(off_flags) if off]
    base = testmath.mean([sum(c * x for c, x in zip(fit["coef"][:7], X[i][:7])) for i in off_days])
    distinct = low > 0 or high < 0
    name = common.METRIC_NAMES.get(metric, metric)
    cost_saved = None
    if extra:
        on_cost = testmath.mean([v["cost"] for (_, v), off in zip(filled, off_flags) if not off])
        off_cost = testmath.mean([v["cost"] for (_, v), off in zip(filled, off_flags) if off])
        cost_saved = on_cost - off_cost
    payload = {"kind": "onoff", "report": os.path.basename(args.report), "metric": metric, "names": names or "all rows", "group_column": col,
               "off": [[a.isoformat(), b.isoformat()] for a, b in offs], "days": len(filled), "off_days": len(off_days),
               "effect_per_off_day": gamma, "low": low, "high": high, "p": testmath.t_two_sided_p(gamma / se if se else None, fit["df"]),
               "baseline_per_day": base, "relative": metrics.div(gamma, base), "relative_low": metrics.div(low, base), "relative_high": metrics.div(high, base),
               "distinguishable_from_zero": distinct, "cost_saved_per_off_day": cost_saved,
               "cost_per_incremental": metrics.div(cost_saved, -gamma) if cost_saved and gamma < 0 and distinct else None,
               "reconcile": common.reconcile(meta, rows, ("cost",) if extra else ())}
    shown = metrics.money if metric in VALUE_METRICS else (lambda v: common.number(v, 2))
    book = xlsx.Workbook()
    book.add_sheet("Days", ["Day", "Weekday", "Ads", name.capitalize()] + (["Cost"] if extra else []),
                   [[d.isoformat(), d.strftime("%A"), "Off" if off else "On", v[metric]] + ([v["cost"]] if extra else []) for (d, v), off in zip(filled, off_flags)],
                   formats={3: "money", 4: "money"})
    book.add_sheet("Result", ["Item", "Value"], [["Change per day with ads off", gamma], ["Range low", low], ["Range high", high],
                                                 ["Expected per day with ads on, on the off days' weekdays", base], ["Relative change", payload["relative"]]],
                   formats={1: "money"}, widths={0: 50})
    lines = ["# On and off readout", ""] + ["%s." % t for t in meta["title_rows"]] + ["", "## The answer", ""]
    lines.append("On the %d days with ads off, %s ran %s a day %s what the on days predict for the same weekdays (%s), range %s to %s at %s confidence. %s" % (
        len(off_days), name, shown(abs(gamma)), "below" if gamma < 0 else "above", common.signed(payload["relative"]), shown(low), shown(high),
        metrics.pct(args.confidence, 0), "That is distinguishable from zero." if distinct else "That range includes zero, so the test did not show an effect it can tell apart from noise."))
    if cost_saved is not None:
        lines.append("")
        lines.append("- Spend saved per off day: %s.%s" % (metrics.money(cost_saved), " Cost per incremental %s: %s." % (
            name.rstrip("s"), metrics.money(payload["cost_per_incremental"])) if payload["cost_per_incremental"] else ""))
    if col == "campaign" and metric in ("conversions", "conv_value", "clicks"):
        lines += ["", "**Read with care:** this outcome is Google Ads' own %s for the named campaigns. When a campaign is off it records none, so the drop says little about what the business lost. Use the business's total leads or sales by day." % name]
    lines += ["", "## How the numbers were made", "",
              "- One average per weekday plus one shift for the off days, fitted together (least squares), so an off week is compared with the same weekdays when the ads were on. The range uses a t value for %d degrees of freedom. Formulas in `references/test-math.md`." % fit["df"],
              "- Days with no row count as zero.",
              "- " + common.reconcile_line(payload["reconcile"], "the report"),
              "", "## What this did not cover", "",
              "- Demand that changed between on and off weeks for other reasons, such as a season or a promotion.",
              "- Searches that waited and came back in an on week.", ""]
    return payload, book, "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="test_type")
    e = sub.add_parser("experiment", help="a Google Ads experiment's arms or scorecard")
    e.add_argument("report")
    e.add_argument("--split", type=float, default=0.5, help="the trial's share of the split")
    e.add_argument("--control", help="control campaign name, when the file has no arm column")
    e.add_argument("--trial", help="trial campaign name, when the file has no arm column")
    e.add_argument("--from", dest="from_day", help="first day to read, after the trial settled")
    e.add_argument("--to", dest="to_day", help="last day to read")
    e.add_argument("--metric", default="Conversions", help="the metric the test was about, as Google names it")
    d = sub.add_parser("daily", help="test and control groups by day")
    d.add_argument("report")
    d.add_argument("--test", action="append")
    d.add_argument("--control", action="append")
    d.add_argument("--control-report")
    d.add_argument("--during", required=True, help="START:END of the test")
    d.add_argument("--pre", help="START:END of the pre-period")
    d.add_argument("--metric")
    d.add_argument("--value-metric")
    d.add_argument("--kind", choices=("go-dark", "holdback", "heavy-up"), default="go-dark")
    d.add_argument("--cost-report")
    d.add_argument("--margin", type=float, help="gross margin, for profit per unit of spend")
    d.add_argument("--value-per-outcome", type=float, help="what one lead or sale is worth, when there is no revenue column")
    d.add_argument("--inferred", action="store_true", help="the regions and dates were found from the data, not given by the person")
    f = sub.add_parser("find", help="find the test regions and dates from a cost report by region and day")
    f.add_argument("report", help="Google Ads cost by region and day")
    f.add_argument("--outcome", help="the business's outcome by region and day")
    f.add_argument("--metric")
    o = sub.add_parser("onoff", help="one series by day with periods of ads off")
    o.add_argument("report")
    o.add_argument("--off", action="append", required=True, help="START:END with ads off; repeat")
    o.add_argument("--names", action="append")
    o.add_argument("--metric")
    for p in (e, d, o, f):
        p.add_argument("--out", required=True)
        p.add_argument("--confidence", type=float, default=0.95)
    args = parser.parse_args()
    if not args.test_type:
        parser.error("say which step: experiment, daily, onoff or find")
    if not 0.5 <= args.confidence < 1:
        raise SystemExit("--confidence is a share between 0.5 and 1, for example 0.95.")
    payload, book, text = {"experiment": run_experiment, "daily": run_daily, "onoff": run_onoff, "find": run_find}[args.test_type](args)
    common.finish(outputs.ensure_dir(args.out), "find" if args.test_type == "find" else "readout", text, payload, book)


if __name__ == "__main__":
    main()
