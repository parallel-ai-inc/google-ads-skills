"""Two group readouts (a geo test, or two campaigns) and finding a test in the data.

Imported by readout.py, never run on its own. The readout fits the test group
on the control group before the test (time-based regression) and adds the
checks that say how far to trust it: a placebo check in the pre-period,
control regions that moved on their own, and the stated test length against
the days cost was actually off. The rules are written in
references/reading-a-result.md and references/test-math.md.
"""
import datetime as dt
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common  # noqa: E402
import testmath  # noqa: E402
from gads import dates, metrics, xlsx  # noqa: E402

# A day counts as off when the group's cost is under this share of its usual (median) spending day.
OFF_SHARE = 0.10
# A stop must last this many days, after at least this many spending days, to count as a test.
MIN_OFF_DAYS = 7
MIN_DAYS_BEFORE = 14
# Groups whose stops start within this many days of each other are one test.
SAME_TEST_DAYS = 3
# A control counts as serving in the window when it spent on this share of the days.
CONTROL_SERVING_SHARE = 0.8
# Placebo check: the verdict rule.
STRONG_PLACEBO = 0.05
DIRECTIONAL_PLACEBO = 0.20
DIRECTIONAL_PLACEBO_RANGE_HAS_ZERO = 0.10
MIN_PLACEBO_WINDOWS = 10
# A control region moved on its own when its range excludes zero and a gap that large appears in this share of its placebo windows or fewer.
CONTROL_MOVED_PLACEBO = 0.05
DAY = dt.timedelta(days=1)
OUTCOME_ORDER = ("leads", "orders", "sales", "bookings", "jobs", "conversions", "revenue", "conv_value", "clicks")
VALUE_METRICS = ("revenue", "conv_value", "sales")


def outcome_metric(meta, wanted):
    if wanted:
        if wanted not in meta["columns"]:
            common.require(meta, [wanted], "report")
        return wanted
    for name in OUTCOME_ORDER:
        if name in meta["columns"]:
            return name
    raise SystemExit("I can't find an outcome column: Leads, Orders, Sales, Bookings, Conversions or Revenue. Name it with --metric.")


def values(series, start, end, key):
    return [v[key] for _, v in common.fill_days(series, start, end, [key])]


def placebo(control_pre, test_pre, m, real_gap):
    """Run the same model on every pseudo test window of m days inside the pre-period.

    Returns how many windows were read and the share whose gap (|effect| /
    predicted) is at least as large as the real one.
    """
    n = len(test_pre)
    gaps = []
    for s in range(0, n - m + 1):
        keep_c, keep_t = control_pre[:s] + control_pre[s + m:], test_pre[:s] + test_pre[s + m:]
        if len(keep_c) < max(10, m):
            continue
        fit = testmath.tbr(keep_c, keep_t, control_pre[s:s + m], test_pre[s:s + m], 0.95)
        if fit and fit["predicted"] > 0:
            gaps.append(abs(fit["effect"]) / fit["predicted"])
    share = (sum(1 for g in gaps if g >= abs(real_gap)) / float(len(gaps))) if gaps and real_gap is not None else None
    return {"windows": len(gaps), "share_as_large": share, "typical_gap": statistics.median(gaps) if gaps else None,
            "largest_gap": max(gaps) if gaps else None}


def trust(distinct, plac, pre_ok):
    """Strong, Directional only or Not readable, with the reason in words."""
    share, windows = plac["share_as_large"], plac["windows"]
    if share is None or windows < MIN_PLACEBO_WINDOWS:
        return ("Directional only" if distinct else "Not readable",
                "the pre-period has room for only %d placebo windows, fewer than the %d the check needs" % (windows, MIN_PLACEBO_WINDOWS))
    why = "a gap this large appeared in %s of %d placebo windows in the pre-period" % (metrics.pct(share, 0), windows)
    if distinct and share <= STRONG_PLACEBO and pre_ok:
        return "Strong", why
    if distinct and share <= DIRECTIONAL_PLACEBO:
        return "Directional only", why + ("" if pre_ok else ", and the pre-period is shorter than three times the test")
    if not distinct and share <= DIRECTIONAL_PLACEBO_RANGE_HAS_ZERO:
        return "Directional only", why + ", but the range includes zero"
    return "Not readable", why


def analyse(ctx, pre, window):
    """Everything for one pre-period and one test window."""
    m = (window[1] - window[0]).days + 1
    t_pre, c_pre = values(ctx["t"], pre[0], pre[1], ctx["metric"]), values(ctx["c"], pre[0], pre[1], ctx["metric"])
    t_win, c_win = values(ctx["t"], window[0], window[1], ctx["metric"]), values(ctx["c"], window[0], window[1], ctx["metric"])
    main = testmath.tbr(c_pre, t_pre, c_win, t_win, ctx["confidence"])
    if main is None:
        raise SystemExit("The pre-period is too short to fit the test group on the control group. Use a longer pre-period.")
    sign = ctx["sign"]
    distinct = main["low"] > 0 or main["high"] < 0
    ads = {"total": sign * main["effect"], "low": min(sign * main["low"], sign * main["high"]),
           "high": max(sign * main["low"], sign * main["high"]), "per_day": sign * main["effect"] / m}
    pre_days = len(t_pre)
    plac = placebo(c_pre, t_pre, m, main["relative"])
    verdict, why = trust(distinct, plac, pre_days >= 3 * m)
    out = {"pre": [pre[0].isoformat(), pre[1].isoformat()], "window": [window[0].isoformat(), window[1].isoformat()],
           "pre_days": pre_days, "test_days": m, "pre_is_three_times_test": pre_days >= 3 * m, "main": main, "distinct": distinct,
           "ads": ads, "placebo": plac, "verdict": verdict, "verdict_reason": why, "value": None, "cost": None}
    # Incremental value: from a value column, or a value per outcome the person gave.
    if ctx["value_metric"]:
        vt_pre, vc_pre = values(ctx["t"], pre[0], pre[1], ctx["value_metric"]), values(ctx["c"], pre[0], pre[1], ctx["value_metric"])
        vt_win, vc_win = values(ctx["t"], window[0], window[1], ctx["value_metric"]), values(ctx["c"], window[0], window[1], ctx["value_metric"])
        vfit = testmath.tbr(vc_pre, vt_pre, vc_win, vt_win, ctx["confidence"])
        if vfit:
            lo, hi = sorted((sign * vfit["low"], sign * vfit["high"]))
            out["value"] = {"actual": vfit["actual"], "predicted": vfit["predicted"], "incremental": sign * vfit["effect"], "low": lo, "high": hi,
                            "source": "the %s column" % common.METRIC_NAMES.get(ctx["value_metric"], ctx["value_metric"])}
    elif ctx["value_per_outcome"]:
        v = ctx["value_per_outcome"]
        out["value"] = {"incremental": ads["total"] * v, "low": ads["low"] * v, "high": ads["high"] * v,
                        "source": "%s per %s, as you gave it" % (common.number(v), ctx["name"].rstrip("s"))}
    if ctx["kt"] is not None:
        kt_pre, kc_pre = values(ctx["kt"], pre[0], pre[1], "cost"), values(ctx["kc"], pre[0], pre[1], "cost")
        kt_win, kc_win = values(ctx["kt"], window[0], window[1], "cost"), values(ctx["kc"], window[0], window[1], "cost")
        cfit = testmath.tbr(kc_pre, kt_pre, kc_win, kt_win, ctx["confidence"])
        if cfit:
            spend = sign * cfit["effect"]
            cost = {"spend_change": spend, "actual": cfit["actual"], "predicted": cfit["predicted"],
                    "cost_per_day_before": testmath.mean(kt_pre)}
            if ctx["has_attributed"]:
                attributed = testmath.mean(values(ctx["kt"], pre[0], pre[1], "conversions"))
                cost["attributed_per_day_before"] = attributed
                if attributed:
                    cost["incremental_share_of_attributed"] = ads["per_day"] / attributed
                    cost["incremental_share_range"] = [ads["low"] / m / attributed, ads["high"] / m / attributed]
            if ads["total"] > 0 and spend > 0:
                cost["cost_per_incremental"] = spend / ads["total"]
                cost["cost_per_incremental_range"] = [spend / ads["high"], spend / ads["low"] if ads["low"] > 0 else None]
            if out["value"] and spend > 0:
                v = out["value"]
                cost["incremental_value_per_spend"] = v["incremental"] / spend
                cost["incremental_value_per_spend_range"] = [v["low"] / spend, v["high"] / spend]
                if ctx["margin"]:
                    g = ctx["margin"]
                    cost["incremental_profit_per_spend"] = v["incremental"] * g / spend - 1
                    cost["incremental_profit_per_spend_range"] = [v["low"] * g / spend - 1, v["high"] * g / spend - 1]
                    cost["breakeven_value_per_spend"] = 1 / g
                    cost["incremental_profit"] = v["incremental"] * g - spend
            out["cost"] = cost
    return out


def off_run(series, start, first, last, usual):
    """The run of days around start when cost was under OFF_SHARE of the usual day, or None when start was not off."""
    def off(day):
        return series.get(day, {}).get("cost", 0.0) < OFF_SHARE * usual
    if not off(start):
        return None
    a, b = start, start
    while a - DAY >= first and off(a - DAY):
        a -= DAY
    while b + DAY <= last and off(b + DAY):
        b += DAY
    return a, b


def load_groups(args):
    """The outcome series for the test and control groups, and the cost series when there is cost."""
    meta, rows = common.load(args.report, "daily report")
    common.require(meta, ["day"], "daily report")
    if args.control_report:
        cmeta, crows = common.load(args.control_report, "control group's daily report")
        common.require(cmeta, ["day"], "control group's daily report")
    else:
        cmeta, crows = meta, rows
    metric = outcome_metric(meta, args.metric)
    if metric not in cmeta["columns"]:
        common.require(cmeta, [metric], "control group's daily report")
    tests, controls = common.split_names(args.test), common.split_names(args.control)
    if not tests and not args.control_report:
        raise SystemExit("Name the test group with --test (regions or campaigns, separated by ;). If the person does not know them, run the find step first.")
    t_col = common.group_column(meta, rows, tests) if tests else None
    c_col = (common.group_column(cmeta, crows, controls) if controls else None) if args.control_report else (
        common.group_column(cmeta, crows, controls) if controls else t_col)
    if tests:
        tests = common.match_names(tests, sorted({r.get(t_col) for r in rows if r.get(t_col)}), (t_col or "group").replace("_", " "))
    if controls:
        controls = common.match_names(controls, sorted({r.get(c_col) for r in crows if r.get(c_col)}), (c_col or "group").replace("_", " "))
    elif not args.control_report:
        controls = sorted({r.get(c_col) for r in crows if r.get(c_col)} - set(tests))
    if args.value_metric:
        common.require(meta, [args.value_metric], "daily report")
    keys = (metric,) + ((args.value_metric,) if args.value_metric else ())
    groups = {"meta": meta, "rows": rows, "cmeta": cmeta, "crows": crows, "metric": metric, "tests": tests, "controls": controls,
              "t_col": t_col, "c_col": c_col, "keys": keys,
              "t": common.daily_series(rows, t_col, tests or None, metric, extra=keys),
              "c": common.daily_series(crows, c_col, controls or None, metric, extra=keys),
              "kt": None, "kc": None, "kmeta": None, "krows": None, "has_attributed": False}
    if not groups["t"] or not groups["c"]:
        raise SystemExit("I can't find dated rows for both groups. Check the names and that the report is segmented by Day.")
    if args.cost_report or "cost" in meta["columns"]:
        kmeta, krows = common.load(args.cost_report, "Google Ads report by day") if args.cost_report else (meta, rows)
        common.require(kmeta, ["day", "cost"], "Google Ads report by day")
        k_col = common.group_column(kmeta, krows, tests)
        k_all = sorted({r.get(k_col) for r in krows if r.get(k_col)})
        k_tests = common.match_names(tests, k_all, (k_col or "group").replace("_", " ")) if tests else None
        k_controls = (common.match_names(controls, k_all, (k_col or "group").replace("_", " ")) if controls
                      else [g for g in k_all if g not in (k_tests or [])])
        extra = ("cost", "conversions") if "conversions" in kmeta["columns"] else ("cost",)
        groups.update({"kt": common.daily_series(krows, k_col, k_tests, "cost", extra=extra),
                       "kc": common.daily_series(krows, k_col, k_controls, "cost", extra=extra),
                       "kmeta": kmeta, "krows": krows, "has_attributed": "conversions" in extra})
    return groups


def run_daily(args):
    g = load_groups(args)
    metric, name = g["metric"], common.METRIC_NAMES.get(g["metric"], g["metric"])
    margin = None
    if args.margin is not None:
        margin = args.margin / 100.0 if args.margin > 1 else args.margin
        if not 0 < margin <= 1:
            raise SystemExit("--margin is a share above 0 and up to 1, for example 0.40.")
        if not args.value_metric and not args.value_per_outcome:
            raise SystemExit("--margin needs a value: --value-metric (a revenue column) or --value-per-outcome (what one %s is worth)." % name.rstrip("s"))
    during = common.span(args.during)
    first = max(min(g["t"]), min(g["c"]))
    last = min(max(g["t"]), max(g["c"]))
    pre = common.span(args.pre) if args.pre else (first, during[0] - DAY)
    if pre[1] >= during[0]:
        raise SystemExit("The pre-period must end before the test period starts.")
    if during[1] > last:
        raise SystemExit("The outcome file ends on %s, before the test period ends on %s. Download the full range." % (last.isoformat(), during[1].isoformat()))
    ctx = {"t": g["t"], "c": g["c"], "metric": metric, "name": name, "value_metric": args.value_metric, "value_per_outcome": args.value_per_outcome,
           "kt": g["kt"], "kc": g["kc"], "has_attributed": g["has_attributed"], "sign": 1 if args.kind == "heavy-up" else -1,
           "confidence": args.confidence, "margin": margin}
    stated = analyse(ctx, pre, during)

    # The stated length against the days cost was actually off.
    length = {"checked": False}
    full = None
    if g["kt"] is not None and args.kind != "heavy-up":
        k_first, k_last = min(g["kt"]), max(max(g["kt"]), max(g["kc"]) if g["kc"] else max(g["kt"]))
        spend_days = [v["cost"] for d, v in g["kt"].items() if pre[0] <= d <= pre[1] and v["cost"] > 0]
        usual = statistics.median(spend_days) if spend_days else 0.0
        run = off_run(g["kt"], during[0], k_first, k_last, usual) if usual else None
        length = {"checked": True, "usual_cost_per_day": usual, "off_threshold": OFF_SHARE * usual, "cost_file_ends": k_last.isoformat()}
        if run is None:
            length["note"] = "Cost in the test group was still running on %s, the first day of the stated test. Check the dates." % during[0].isoformat()
        else:
            length.update({"off_from": run[0].isoformat(), "off_to": run[1].isoformat(), "off_days": (run[1] - run[0]).days + 1,
                           "still_off_at_file_end": run[1] == k_last})
            notes = []
            if run[0] < during[0]:
                notes.append("cost was already off from %s, before the stated start" % run[0].isoformat())
            if run[1] > during[1]:
                notes.append("cost stayed off until %s%s, after the stated end of %s" % (
                    run[1].isoformat(), " (when the cost file ends)" if run[1] == k_last else "", during[1].isoformat()))
            if run[1] < during[1]:
                notes.append("cost came back on %s, before the stated end of %s" % ((run[1] + DAY).isoformat(), during[1].isoformat()))
            if notes:
                length["note"] = "The stated test and the data differ: " + "; ".join(notes) + "."
                window = (run[0], min(run[1], last))
                full_pre = (pre[0], min(pre[1], run[0] - DAY))
                if window != during and (full_pre[1] - full_pre[0]).days >= 13:
                    full = analyse(ctx, full_pre, window)

    # Control regions that moved on their own.
    controls_check = []
    without = None
    if g["c_col"] and len(g["controls"]) >= 2:
        for one in g["controls"]:
            others = [c for c in g["controls"] if c != one]
            s_one = common.daily_series(g["crows"], g["c_col"], [one], metric)
            s_oth = common.daily_series(g["crows"], g["c_col"], others, metric)
            o_pre, x_pre = values(s_oth, pre[0], pre[1], metric), values(s_one, pre[0], pre[1], metric)
            fit = testmath.tbr(o_pre, x_pre, values(s_oth, during[0], during[1], metric), values(s_one, during[0], during[1], metric), args.confidence)
            if not fit:
                continue
            plac = placebo(o_pre, x_pre, stated["test_days"], fit["relative"])
            distinct = fit["low"] > 0 or fit["high"] < 0
            moved = distinct and plac["share_as_large"] is not None and plac["share_as_large"] <= CONTROL_MOVED_PLACEBO
            controls_check.append({"region": one, "relative": fit["relative"], "relative_low": fit["relative_low"], "relative_high": fit["relative_high"],
                                   "placebo_share": plac["share_as_large"], "moved": moved})
        moved = [c["region"] for c in controls_check if c["moved"]]
        if moved and len(moved) < len(g["controls"]):
            kept = [c for c in g["controls"] if c not in moved]
            alt = dict(ctx)
            alt["c"] = common.daily_series(g["crows"], g["c_col"], kept, metric, extra=g["keys"])
            if g["kt"] is not None and g["kc"] is not None:
                alt["kc"] = _without(g, kept)
            without = analyse(alt, pre, during)
            without["controls"] = kept
            without["left_out"] = moved

    payload = {"kind": "daily", "report": os.path.basename(args.report), "control_report": os.path.basename(args.control_report) if args.control_report else None,
               "inferred": args.inferred, "metric": metric, "test_group": g["tests"] or "all rows", "control_group": g["controls"] or "all rows",
               "group_column": g["t_col"], "test_kind": args.kind, "confidence": args.confidence, "margin": margin,
               "stated": _public(stated), "length": length, "full_off_period": _public(full) if full else None,
               "controls_check": controls_check, "without_moved_controls": _public(without) if without else None,
               "reconcile": common.reconcile(g["meta"], g["rows"], ("cost",) if "cost" in g["meta"]["columns"] else ()),
               "cost_reconcile": common.reconcile(g["kmeta"], g["krows"], ("cost",)) if g["kmeta"] else None}
    # Fields the earlier layout had at the top level, kept so a reader of the JSON finds them.
    payload.update({"pre": stated["pre"], "during": stated["window"], "pre_days": stated["pre_days"], "test_days": stated["test_days"],
                    "pre_is_three_times_test": stated["pre_is_three_times_test"], "distinguishable_from_zero": stated["distinct"],
                    "verdict": stated["verdict"], "effect": payload["stated"]["effect"], "caused_by_ads": stated["ads"], "cost": stated["cost"]})
    book = _workbook(g, stated, full, without, controls_check, name)
    text = _summary(args, g, stated, full, without, controls_check, length, payload, name)
    return payload, book, text


def _without(g, kept):
    """Cost for the kept controls, matched by name in the cost report."""
    k_col = common.group_column(g["kmeta"], g["krows"], kept)
    names = {r.get(k_col) for r in g["krows"] if r.get(k_col)}
    extra = ("cost", "conversions") if g["has_attributed"] else ("cost",)
    return common.daily_series(g["krows"], k_col, [k for k in kept if k in names], "cost", extra=extra)


def _public(result):
    main = result["main"]
    out = {k: result[k] for k in ("pre", "window", "pre_days", "test_days", "pre_is_three_times_test", "distinct", "ads", "placebo",
                                  "verdict", "verdict_reason", "value", "cost")}
    out.update({k: result[k] for k in ("controls", "left_out") if k in result})
    out["fit"] = {k: main[k] for k in ("intercept", "slope", "r2", "residual_sd", "df")}
    out["effect"] = {k: main[k] for k in ("actual", "predicted", "effect", "se", "low", "high", "p", "relative", "relative_low", "relative_high")}
    return out


def _result_line(r, name, shown, confidence):
    e = r["main"]
    return ("%s came in at %s against %s predicted from the control group: a difference of %s (%s), range %s to %s at %s confidence. %s" % (
        name.capitalize(), shown(e["actual"]), shown(e["predicted"]), shown(e["effect"]), common.signed(e["relative"]), shown(e["low"]),
        shown(e["high"]), metrics.pct(confidence, 0),
        "That is distinguishable from zero." if r["distinct"] else "That range includes zero."))


def _money_lines(r, name, value_name, kind):
    lines = []
    cost, ads, m = r["cost"], r["ads"], r["test_days"]
    if r["distinct"] and ads["total"] > 0:
        lines.append("- The ads caused about %s %s over the %d days (%s a day), range %s to %s." % (
            common.number(ads["total"], 1), name, m, common.number(ads["per_day"], 1), common.number(ads["low"], 1), common.number(ads["high"], 1)))
    if not cost:
        return lines
    lines.append("- Spend %s: %s over the %d days." % ("added" if kind == "heavy-up" else "removed", metrics.money(cost["spend_change"]), m))
    if cost.get("cost_per_incremental") and r["distinct"]:
        lo, hi = cost["cost_per_incremental_range"]
        lines.append("- Cost per incremental %s: %s (range %s to %s)." % (name.rstrip("s"), metrics.money(cost["cost_per_incremental"]),
                                                                        metrics.money(lo), metrics.money(hi) if hi else "no upper limit"))
    if cost.get("attributed_per_day_before") is not None:
        share = cost.get("incremental_share_of_attributed")
        lines.append("- Google Ads attributed %s conversions a day to the test group before the test. The ads caused %s %s a day: %s of the attributed figure (range %s to %s). Attributed is not incremental." % (
            common.number(cost["attributed_per_day_before"]), common.number(ads["per_day"], 1), name, metrics.pct(share, 0),
            metrics.pct(cost["incremental_share_range"][0], 0), metrics.pct(cost["incremental_share_range"][1], 0)) if share is not None else
            "- Google Ads attributed %s conversions a day to the test group before the test." % common.number(cost["attributed_per_day_before"]))
    if cost.get("incremental_value_per_spend") is not None:
        lo, hi = cost["incremental_value_per_spend_range"]
        lines.append("- Incremental %s per unit of spend: %s (range %s to %s)." % (value_name, common.number(cost["incremental_value_per_spend"]),
                                                                                common.number(lo), common.number(hi)))
    if cost.get("incremental_profit_per_spend") is not None:
        lo, hi = cost["incremental_profit_per_spend_range"]
        lines.append("- **Profit:** at this margin, each unit of spend returns %s of profit after paying for itself (range %s to %s); %s in total. Break even is %s of %s per unit of spend. %s" % (
            common.number(cost["incremental_profit_per_spend"]), common.number(lo), common.number(hi), metrics.money(cost["incremental_profit"]),
            common.number(cost["breakeven_value_per_spend"]), value_name,
            "The ads make money." if lo > 0 else ("The ads lose money." if hi < 0 else "Whether the ads make money is inside the range: not settled.")))
    return lines


def _summary(args, g, stated, full, without, controls_check, length, payload, name):
    shown = metrics.money if g["metric"] in VALUE_METRICS else (lambda v: common.number(v, 1))
    value_name = common.METRIC_NAMES.get(args.value_metric, "value") if args.value_metric else "value"
    test_words = {"go-dark": "with ads switched off", "holdback": "held back from the ads", "heavy-up": "with more spend"}[args.kind]
    tests = "; ".join(g["tests"]) if g["tests"] else "all rows"
    lines = ["# Test readout", ""] + ["%s." % t for t in g["meta"]["title_rows"]]
    if args.inferred:
        lines += ["", "**The test regions and dates were found from the data, not given by the person.** Confirm them before acting on this."]
    lines += ["", "## The answer", "",
              "**Verdict: %s.** In the test group (%s), %s, from %s to %s: %s" % (
                  stated["verdict"], tests, test_words, stated["window"][0], stated["window"][1], _result_line(stated, name, shown, args.confidence)),
              "", "Why that verdict: %s. Fit before the test: R squared %.2f." % (stated["verdict_reason"], stated["main"]["r2"] or 0), ""]
    lines += _money_lines(stated, name, value_name, args.kind)
    if length.get("note"):
        lines += ["", "**%s**" % length["note"]]
        if full:
            lines += ["", "Over the full off period, %s to %s (%d days): **Verdict: %s.** %s" % (
                full["window"][0], full["window"][1], full["test_days"], full["verdict"], _result_line(full, name, shown, args.confidence))]
            lines += _money_lines(full, name, value_name, args.kind)
    moved = [c for c in controls_check if c["moved"]]
    if moved:
        lines += ["", "**Control regions that moved on their own:** %s." % "; ".join(
            "%s, %s against the other controls (range %s to %s)" % (c["region"], common.signed(c["relative"]), common.signed(c["relative_low"]),
                                                                  common.signed(c["relative_high"])) for c in moved)]
        if without:
            lines += ["", "Without %s: **Verdict: %s.** %s" % (", ".join(without["left_out"]), without["verdict"], _result_line(without, name, shown, args.confidence))]
            lines += _money_lines(without, name, value_name, args.kind)
    lines += ["", "## To confirm with the person", ""]
    asks = []
    if args.inferred:
        asks.append("The test regions (%s) and the dates (%s to %s): are they the test?" % (tests, stated["window"][0], stated["window"][1]))
    if length.get("note"):
        asks.append("Which dates the test really ran: the stated window, or the full time cost was off.")
    if moved:
        asks.append("What happened in %s during the test (an event, a branch, a promotion)." % ", ".join(c["region"] for c in moved))
    asks += ["Whether every campaign was off in the test regions, or only some. A geo test reads all campaigns in a region together; it cannot say which campaign caused the result.",
             "Whether anything else changed in the test regions during the test."]
    lines += ["%d. %s" % (i + 1, a) for i, a in enumerate(asks)]
    plac = stated["placebo"]
    lines += ["", "## Checks on the result", "",
              "- Pre-period: %s to %s, %d days, %s the test's %d days. **Official** (`references/incrementality.md`): keep at least 3x the test length in pre-test data." % (
                  stated["pre"][0], stated["pre"][1], stated["pre_days"], "at least three times" if stated["pre_is_three_times_test"] else "LESS than three times", stated["test_days"]),
              "- Placebo check: the same model on %d pseudo test windows of %d days inside the pre-period. The typical gap was %s, the largest %s; the real gap is %s." % (
                  plac["windows"], stated["test_days"], metrics.pct(plac["typical_gap"], 1), metrics.pct(plac["largest_gap"], 1),
                  metrics.pct(abs(stated["main"]["relative"] or 0), 1)) if plac["windows"] else "- Placebo check: the pre-period is too short for one.",
              "- Verdict rule: **Strong** when the range excludes zero, a gap this large appeared in 5% or fewer of the placebo windows, and the pre-period is at least three times the test. **Directional only** when the range excludes zero and the share is 20% or less, or the range includes zero but the share is 10% or less. **Not readable** otherwise. Written in `references/test-math.md` and `references/reading-a-result.md`."]
    if length.get("checked"):
        lines.append("- Test length against the data: a day counts as off when the test group's cost is under %s, which is 10%% of its usual spending day (%s) before the test.%s" % (
            metrics.money(length["off_threshold"]), metrics.money(length["usual_cost_per_day"]),
            " Cost was off from %s to %s." % (length["off_from"], length["off_to"]) if length.get("off_from") else ""))
    if controls_check:
        lines.append("- Control regions checked one by one against the others: %s. A region counts as moved when its range excludes zero and a gap that large appeared in 5%% or fewer of its own placebo windows." % "; ".join(
            "%s %s%s" % (c["region"], common.signed(c["relative"]), " (moved)" if c["moved"] else "") for c in controls_check))
    elif g["c_col"]:
        lines.append("- Control regions were not checked one by one: there is only one.")
    lines += ["", "## How the numbers were made", "",
              "- Time-based regression (Google Research, `references/incrementality.md`): test = a + b x control, fitted on the pre-period (a = %s, b = %.3f). The range uses the fit's leftover spread and the uncertainty in a and b, with a t value for %d degrees of freedom. Formulas in `references/test-math.md`." % (
                  common.number(stated["main"]["intercept"]), stated["main"]["slope"], stated["main"]["df"]),
              "- Days with no row count as zero.",
              "- " + common.reconcile_line(payload["reconcile"], "the outcome file"),
              ("- " + common.reconcile_line(payload["cost_reconcile"], "the cost report")) if payload["cost_reconcile"] else "- No cost was read, so cost per incremental result is not worked out.",
              "- Spend is treated as known when the cost per incremental result is worked out, as the method's authors do.",
              ("- Profit after ad cost = incremental value x margin, minus the spend. Break even is 1 / margin of value per unit of spend." if payload["margin"] else
               "- No margin was given, so profit is not worked out. Add --margin."),
              "", "## What this did not cover", "",
              "- A geo test reads every campaign in the test regions together. It cannot split the result by campaign.",
              "- Anything that hit the test group and not the control group during the test (a local event, a competitor, the weather) shows up as an effect. The control check catches it only in the control regions.",
              "- Results that arrive after the test ends, such as jobs booked later from leads in the test.", ""]
    return "\n".join(lines)


def _workbook(g, stated, full, without, controls_check, name):
    book = xlsx.Workbook()
    rows = []
    for label, r in (("Stated window", stated), ("Full off period", full), ("Without moved controls", without)):
        if not r:
            continue
        e, c = r["main"], r["cost"] or {}
        rows.append([label, r["window"][0], r["window"][1], r["test_days"], e["actual"], e["predicted"], e["effect"], e["low"], e["high"], e["relative"],
                     r["placebo"]["share_as_large"], e["r2"], r["verdict"], c.get("spend_change"), c.get("cost_per_incremental"),
                     c.get("incremental_share_of_attributed"), c.get("incremental_value_per_spend"), c.get("incremental_profit_per_spend")])
    book.add_sheet("Result", ["Reading", "From", "To", "Days", "Actual " + name, "Predicted", "Difference", "Range low", "Range high", "Relative",
                              "Placebo share as large", "Fit R squared", "Verdict", "Spend change", "Cost per incremental",
                              "Incremental share of attributed", "Incremental value per spend", "Incremental profit per spend"], rows,
                   formats={3: "int", 4: "money", 5: "money", 6: "money", 7: "money", 8: "money", 9: "pct", 10: "pct", 11: "money", 13: "money",
                            14: "money", 15: "pct", 16: "money", 17: "money"}, widths={0: 24, 12: 18})
    pre, win = stated["pre"], stated["window"]
    a, b = dates.parse_day(pre[0]), dates.parse_day(win[1])
    days = []
    predicted = dict(zip([dates.parse_day(win[0]) + DAY * i for i in range(stated["test_days"])], stated["main"]["daily_predicted"]))
    for day, t in common.fill_days(g["t"], a, b, [g["metric"]]):
        c = g["c"].get(day, {}).get(g["metric"], 0.0)
        days.append([day.isoformat(), "Test" if day in predicted else ("Before" if day < dates.parse_day(win[0]) else "Between"),
                     c, t[g["metric"]], predicted.get(day)])
    book.add_sheet("Days", ["Day", "Period", "Control " + name, "Test " + name, "Test predicted"], days, formats={2: "money", 3: "money", 4: "money"})
    if controls_check:
        book.add_sheet("Control check", ["Control region", "Against the other controls", "Range low", "Range high", "Placebo share as large", "Moved on its own"],
                       [[c["region"], c["relative"], c["relative_low"], c["relative_high"], c["placebo_share"], "Yes" if c["moved"] else "No"] for c in controls_check],
                       formats={1: "pct", 2: "pct", 3: "pct", 4: "pct"}, widths={0: 22})
    return book


def run_find(args):
    """Find a test in the data: groups whose cost stopped, and whether their outcome fell against the others."""
    meta, rows = common.load(args.report, "Google Ads cost report by region and day")
    common.require(meta, ["day", "cost"], "Google Ads cost report by region and day")
    col = next((c for c in common.GROUP_COLUMNS if c != "campaign" and c in meta["columns"]), "campaign" if "campaign" in meta["columns"] else None)
    if not col:
        raise SystemExit("I can't find a location or campaign column in the cost report. Download it with Day and City, Region or Campaign as rows.")
    names = sorted({r.get(col) for r in rows if r.get(col)})
    series = {n: common.daily_series(rows, col, [n], "cost") for n in names}
    all_days = [d for s in series.values() for d in s]
    first, last = min(all_days), max(all_days)
    stops, usual_of = [], {}
    for n in names:
        filled = common.fill_days(series[n], first, last, ["cost"])
        spend = [v["cost"] for _, v in filled if v["cost"] > 0]
        if not spend:
            continue
        usual = statistics.median(spend)
        usual_of[n] = usual
        best, run_start = None, None
        for i, (day, v) in enumerate(filled):
            off = v["cost"] < OFF_SHARE * usual
            if off and run_start is None:
                run_start = i
            if run_start is not None and (not off or i == len(filled) - 1):
                end = i if off else i - 1
                if end - run_start + 1 >= MIN_OFF_DAYS and run_start >= MIN_DAYS_BEFORE and (best is None or end - run_start > best[1] - best[0]):
                    best = (run_start, end)
                run_start = None
        if best:
            stops.append({"region": n, "from": filled[best[0]][0], "to": filled[best[1]][0], "still_off_at_end": filled[best[1]][0] == last})
    stops.sort(key=lambda s: s["from"])
    tests = []
    for s in stops:
        if tests and abs((s["from"] - tests[-1]["from"]).days) <= SAME_TEST_DAYS:
            t = tests[-1]
            t["regions"].append(s["region"])
            t["to"] = min(t["to"], s["to"])
            t["still_off_at_end"] = t["still_off_at_end"] and s["still_off_at_end"]
            t["from_latest"] = max(t["from_latest"], s["from"])
        else:
            tests.append({"regions": [s["region"]], "from": s["from"], "from_latest": s["from"], "to": s["to"], "still_off_at_end": s["still_off_at_end"]})
    outcome = None
    if args.outcome:
        ometa, orows = common.load(args.outcome, "outcome file by region and day")
        common.require(ometa, ["day"], "outcome file by region and day")
        metric = outcome_metric(ometa, args.metric)
        ocol = next((c for c in common.GROUP_COLUMNS if c in ometa["columns"] and c != "campaign"), None) or (
            "campaign" if "campaign" in ometa["columns"] else None)
        if not ocol:
            raise SystemExit("I can't find a location column in the outcome file. It needs Day, a City or Region column and the outcome.")
        outcome = {"metric": metric, "column": ocol, "regions": sorted({r.get(ocol) for r in orows if r.get(ocol)})}
    for t in tests:
        window = (t["from_latest"], t["to"])
        t["days"] = (window[1] - window[0]).days + 1
        days = [window[0] + DAY * i for i in range(t["days"])]
        t["controls"] = [n for n in names if n not in t["regions"] and n in usual_of and
                         sum(1 for d in days if series[n].get(d, {}).get("cost", 0.0) >= OFF_SHARE * usual_of[n]) >= CONTROL_SERVING_SHARE * len(days)]
        if outcome:
            lower = {r.lower(): r for r in outcome["regions"]}
            t_names = [lower[r.lower()] for r in t["regions"] if r.lower() in lower]
            c_names = [lower[r.lower()] for r in t["controls"] if r.lower() in lower]
            t["missing_in_outcome"] = [r for r in t["regions"] + t["controls"] if r.lower() not in lower]
            if t_names and c_names:
                ts = common.daily_series(orows, outcome["column"], t_names, outcome["metric"])
                cs = common.daily_series(orows, outcome["column"], c_names, outcome["metric"])
                o_first = max(min(ts), min(cs))
                pre_t, pre_c = sum(values(ts, o_first, window[0] - DAY, outcome["metric"])), sum(values(cs, o_first, window[0] - DAY, outcome["metric"]))
                o_end = min(window[1], max(ts), max(cs))
                w_t, w_c = sum(values(ts, window[0], o_end, outcome["metric"])), sum(values(cs, window[0], o_end, outcome["metric"]))
                t["outcome_change_against_controls"] = metrics.div(metrics.div(w_t, w_c), metrics.div(pre_t, pre_c)) - 1 if pre_t and pre_c and w_c else None
                t["outcome_names"], t["outcome_control_names"] = t_names, c_names
    payload = {"kind": "find", "cost_report": os.path.basename(args.report), "outcome": os.path.basename(args.outcome) if args.outcome else None,
               "group_column": col, "first_day": first.isoformat(), "last_day": last.isoformat(),
               "rules": {"off_share": OFF_SHARE, "min_off_days": MIN_OFF_DAYS, "min_days_before": MIN_DAYS_BEFORE, "same_test_days": SAME_TEST_DAYS,
                         "control_serving_share": CONTROL_SERVING_SHARE},
               "candidates": [dict(t, **{"from": t["from"].isoformat(), "from_latest": t["from_latest"].isoformat(), "to": t["to"].isoformat()}) for t in tests]}
    book = xlsx.Workbook()
    book.add_sheet("Candidates", ["Test regions", "Cost off from", "To", "Days", "Still off when the file ends", "Control regions", "Outcome against controls"],
                   [["; ".join(t["regions"]), t["from_latest"].isoformat(), t["to"].isoformat(), t["days"], "Yes" if t["still_off_at_end"] else "No",
                     "; ".join(t["controls"]), t.get("outcome_change_against_controls")] for t in tests], formats={3: "int", 6: "pct"}, widths={0: 40, 5: 60})
    book.add_sheet("Cost by region", ["Region", "Usual spending day", "Cost off from", "To"],
                   [[n, usual_of.get(n), next((s["from"].isoformat() for s in stops if s["region"] == n), ""),
                     next((s["to"].isoformat() for s in stops if s["region"] == n), "")] for n in names], formats={1: "money"}, widths={0: 30})
    lines = ["# Finding the test in the data", ""] + ["%s." % t for t in meta["title_rows"]]
    lines += ["", "## The answer", ""]
    if not tests:
        lines.append("No region's cost stopped for %d days or more after at least %d days of spending. The data shows no go dark or holdback test. Ask the person which regions and dates the test used." % (MIN_OFF_DAYS, MIN_DAYS_BEFORE))
    for i, t in enumerate(tests, 1):
        lines.append("**Candidate %d:** cost stopped in %s from %s to %s (%d days)%s." % (
            i, "; ".join(t["regions"]), t["from_latest"].isoformat(), t["to"].isoformat(), t["days"], ", and was still off when the file ends" if t["still_off_at_end"] else ""))
        if t["from"] != t["from_latest"]:
            lines.append("- The regions stopped on different days, from %s; the window starts when all were off." % t["from"].isoformat())
        lines.append("- Regions that kept spending, the candidate controls: %s." % ("; ".join(t["controls"]) or "none"))
        if t.get("outcome_change_against_controls") is not None:
            lines.append("- In that window, %s in the candidate regions ran %s against the control regions, compared with before. This is a first look, not the readout." % (
                common.METRIC_NAMES.get(outcome["metric"], outcome["metric"]), common.signed(t["outcome_change_against_controls"])))
        if t.get("missing_in_outcome"):
            lines.append("- Not in the outcome file: %s." % "; ".join(t["missing_in_outcome"]))
        if outcome and t.get("outcome_names"):
            lines += ["", "If the person confirms it, read it with:", "", "```",
                      "python3 scripts/readout.py daily %s --out OUTPUT --test \"%s\" --control \"%s\" --during %s:%s --cost-report %s --inferred" % (
                          args.outcome, ";".join(t["outcome_names"]), ";".join(t["outcome_control_names"]), t["from_latest"].isoformat(), t["to"].isoformat(), args.report),
                      "```"]
    lines += ["", "## To confirm with the person", "",
              "1. Are these the test regions and dates? If they remember a different length, use theirs: the readout compares it with the data.",
              "2. Was every campaign off in those regions, or only some?",
              "3. Did anything else change in those regions in that time?",
              "", "## How the numbers were made", "",
              "- A day counts as off when a region's cost is under 10%% of its usual (median) spending day. A stop counts when it lasts %d days or more after at least %d days in the file." % (MIN_OFF_DAYS, MIN_DAYS_BEFORE),
              "- Regions whose stops start within %d days of each other are one test. Control regions spent on at least %s of the window's days." % (SAME_TEST_DAYS, metrics.pct(CONTROL_SERVING_SHARE, 0)),
              "- The outcome check is the test regions' share of the outcome in the window against before, relative to the controls. The readout gives the range and the verdict.",
              "", "## What this did not cover", "",
              "- Heavy up tests (cost rising) are not searched for.",
              "- A stop can be a budget running out or a campaign paused for another reason. Only the person can say it was a test.", ""]
    return payload, book, "\n".join(lines)
