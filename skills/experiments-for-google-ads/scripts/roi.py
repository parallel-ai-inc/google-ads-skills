#!/usr/bin/env python3
"""Return on investment: profit after ad cost, and whether the next dollar pays.

Reads a campaign report (segmented by Day for the next dollar question, and
with Ad group for ad group rows). At the business's gross margin it works out,
by campaign and in total: profit after ad cost (Conv. value x margin, minus Cost),
the break even Conv. value / cost (1 / margin), and whether each campaign is
profitable, loses money, or has too few conversions to call. From daily rows
it estimates how value grows with spend, and whether the next dollar pays.

    python3 roi.py REPORT --out OUTPUTDIR --margin 0.40 [--value-per-conversion 250] [--value-is-profit]
        [--brand "Brand"] [--confidence 0.9] [--recent-days 28]
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
from gads import dates, metrics, outputs, xlsx  # noqa: E402

# The spend curve needs this many days with spend and value, and is skipped
# when more than this share of days had spend but no value (log of zero).
# It then tries weekly totals, which need this many full weeks.
MIN_CURVE_DAYS = 21
MAX_ZERO_VALUE_SHARE = 0.25
MIN_CURVE_WEEKS = 12
# Below this spread of log spend (a typical day within about 10% of the
# average), spend hardly varied and the curve can't be read.
MIN_SPEND_SPREAD = 0.10


def call(conversions, roas, breakeven, z):
    """Profitable, loses money, or too few conversions to call, from a Poisson range on conversions."""
    if not conversions:
        return "No conversions", None, None
    lo = max(0.0, conversions - z * math.sqrt(conversions)) / conversions * roas
    hi = (conversions + z * math.sqrt(conversions)) / conversions * roas
    if lo > breakeven:
        return "Profitable", lo, hi
    if hi < breakeven:
        return "Loses money", lo, hi
    return "Too few conversions to call", lo, hi


def fit_curve(points, confidence, weekday_terms):
    """log(value) = a + b log(cost) [+ weekday], by least squares. b is how value grows with spend."""
    X = [[1.0, math.log(c)] + ([1.0 if d.weekday() == k else 0.0 for k in range(1, 7)] if weekday_terms else []) for d, c, _ in points]
    fit = testmath.ols(X, [math.log(v) for _, _, v in points])
    if fit is None:
        return None
    b = fit["coef"][1]
    se = math.sqrt(fit["sigma2"] * fit["inv"][1][1])
    tq = testmath.t_quantile(1 - (1 - confidence) / 2, fit["df"])
    logs = [math.log(c) for _, c, _ in points]
    return {"elasticity": b, "low": b - tq * se, "high": b + tq * se, "weekday_terms": weekday_terms, "df": fit["df"],
            "spend_spread": math.sqrt(testmath.variance(logs))}


def weeks_of(days):
    """Full Monday to Sunday weeks: (monday, cost, value)."""
    weeks = {}
    for d, c, v in days:
        monday = d - dt.timedelta(days=d.weekday())
        slot = weeks.setdefault(monday, [0, 0.0, 0.0])
        slot[0] += 1
        slot[1] += c
        slot[2] += v
    return [(m, c, v) for m, (n, c, v) in sorted(weeks.items()) if n == 7]


def curve(days, confidence):
    """How value grows with spend, from days, or from full weeks when too many days had no value.

    Every outcome says why it could not answer and what data would let it.
    """
    used = [(d, c, v) for d, c, v in days if c > 0 and v > 0]
    spent = [x for x in days if x[1] > 0]
    zero = len(spent) - len(used)
    out = {"days_with_spend": len(spent), "days_used": len(used), "days_no_value": zero, "basis": "days"}
    daily_ok = len(used) >= MIN_CURVE_DAYS and not (spent and zero / float(len(spent)) > MAX_ZERO_VALUE_SHARE)
    fit = None
    if daily_ok:
        fit = fit_curve(used, confidence, len(used) >= 28 and len({d.weekday() for d, _, _ in used}) == 7)
    else:
        weeks = weeks_of(days)
        w_used = [w for w in weeks if w[1] > 0 and w[2] > 0]
        w_spent = [w for w in weeks if w[1] > 0]
        out.update({"weeks_with_spend": len(w_spent), "weeks_used": len(w_used)})
        if len(w_used) >= MIN_CURVE_WEEKS and len(w_used) >= (1 - MAX_ZERO_VALUE_SHARE) * len(w_spent):
            fit = fit_curve(w_used, confidence, False)
            out["basis"] = "full weeks, because %d of %d days with spend had no value" % (zero, len(spent)) if len(used) >= MIN_CURVE_DAYS else \
                "full weeks, because only %d days had both spend and value" % len(used)
        else:
            if len(used) < MIN_CURVE_DAYS:
                out["reason"] = "only %d days had both spend and value (a daily fit needs %d) and only %d full weeks did (a weekly fit needs %d)" % (
                    len(used), MIN_CURVE_DAYS, len(w_used), MIN_CURVE_WEEKS)
            else:
                out["reason"] = "%d of %d days with spend had no value, too many for a daily fit, and only %d full weeks had value (a weekly fit needs %d)" % (
                    zero, len(spent), len(w_used), MIN_CURVE_WEEKS)
            out["needs"] = "a longer date range: %d full weeks or more with conversion value, so the fit can use weekly totals" % MIN_CURVE_WEEKS
            return out
    if fit is None:
        out["reason"] = "spend was the same every day, so the curve can't be fitted"
        out["needs"] = "some weeks at a clearly different budget, such as before and after a budget change"
        return out
    out.update(fit)
    if out["high"] < 1:
        out["shape"] = "Returns fall as spend rises"
    elif out["low"] > 1:
        out["shape"] = "Returns rose with spend"
    else:
        out["shape"] = "Can't tell from this data"
        if out["spend_spread"] < MIN_SPEND_SPREAD:
            out["reason"] = "spend hardly varied: a typical %s spend sat within about %s of the average" % (
                "day's" if out["basis"] == "days" else "week's", metrics.pct(out["spend_spread"], 0))
            out["needs"] = "some weeks at a clearly different budget, such as before and after a budget change"
        else:
            out["reason"] = "the range for how value grows with spend is too wide"
            out["needs"] = "more days, or a longer stretch at a different budget"
    return out


def why_not(k):
    if not k.get("reason"):
        return ""
    if k.get("needs", "").startswith("nothing"):
        return k["reason"].capitalize() + ". Not asked."
    return "%s. Needs %s." % (k["reason"].capitalize(), k.get("needs", "more data"))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--out", required=True)
    parser.add_argument("--margin", type=float, help="gross margin, for example 0.40 or 40")
    parser.add_argument("--value-per-conversion", type=float, help="revenue one conversion is worth, when Conv. value is not tracked")
    parser.add_argument("--value-is-profit", action="store_true", help="Conv. value already holds profit, not revenue")
    parser.add_argument("--brand", action="append", help="brand campaigns; default: names containing 'brand'")
    parser.add_argument("--confidence", type=float, default=0.9)
    parser.add_argument("--recent-days", type=int, default=28)
    args = parser.parse_args()
    if args.value_is_profit:
        margin = 1.0
    else:
        if args.margin is None:
            raise SystemExit("Give the business's gross margin with --margin, for example --margin 0.40. If Conv. value already holds profit, use --value-is-profit.")
        margin = args.margin / 100.0 if args.margin > 1 else args.margin
        if not 0 < margin <= 1:
            raise SystemExit("--margin is a share above 0 and up to 1, for example 0.40.")
    if not 0.5 <= args.confidence < 1:
        raise SystemExit("--confidence is a share between 0.5 and 1, for example 0.9.")
    breakeven = 1.0 / margin
    z = testmath.z_two_sided(args.confidence)

    meta, rows = common.load(args.report, "campaign report")
    needed = ["campaign", "cost", "conversions"] + ([] if args.value_per_conversion else ["conv_value"])
    common.require(meta, needed, "campaign report")
    value_source = ("Conversions x %s, as you gave it" % common.number(args.value_per_conversion)) if args.value_per_conversion else "Conv. value"

    def value_of(row):
        if args.value_per_conversion:
            return (row.get("conversions") or 0.0) * args.value_per_conversion
        return row.get("conv_value") or 0.0

    has_days = "day" in meta["columns"]
    has_groups = "ad_group" in meta["columns"]
    camps, groups, daily = {}, {}, {}
    all_days = []
    for row in rows:
        name = row.get("campaign")
        if not name:
            continue
        keys = [("campaign", name)] + ([("group", (name, row.get("ad_group") or ""))] if has_groups else [])
        for kind, key in keys:
            target = camps if kind == "campaign" else groups
            slot = target.setdefault(key, {"cost": 0.0, "conversions": 0.0, "value": 0.0, "clicks": 0.0, "status": "", "type": "", "lost": []})
            slot["cost"] += row.get("cost") or 0.0
            slot["conversions"] += row.get("conversions") or 0.0
            slot["value"] += value_of(row)
            slot["clicks"] += row.get("clicks") or 0.0
            slot["status"] = row.get("campaign_status") or slot["status"]
            slot["type"] = row.get("campaign_type") or slot["type"]
        if has_days:
            day = dates.parse_day(row.get("day"))
            if day:
                all_days.append(day)
                d = daily.setdefault(name, {}).setdefault(day, {"cost": 0.0, "value": 0.0, "lost": None})
                d["cost"] += row.get("cost") or 0.0
                d["value"] += value_of(row)
                if row.get("lost_is_budget") is not None:
                    d["lost"] = row["lost_is_budget"] / 100.0  # the report writes 32.6% and the reader keeps 32.6
    if not camps:
        raise SystemExit("I can't read any campaign rows. Download the campaign report again with the Campaign column.")

    if args.brand:
        brand = set(common.match_names(common.split_names(args.brand), list(camps), "campaign"))
        brand_rule = "the campaigns you named"
    else:
        brand = {c for c in camps if re.search(r"\bbrand", c, re.I)}
        brand_rule = "campaigns with \"brand\" in the name"

    def serving(slot):
        return (slot["status"] or "Enabled").strip().lower() == "enabled"

    total_cost = sum(c["cost"] for c in camps.values())
    total_value = sum(c["value"] for c in camps.values())

    def describe(slot):
        roas = metrics.div(slot["value"], slot["cost"])
        verdict, lo, hi = call(slot["conversions"], roas or 0.0, breakeven, z)
        if slot["cost"] > 0 and not slot["conversions"]:
            verdict = "No conversions"
        value_per_conv = metrics.div(slot["value"], slot["conversions"])
        return {"cost": slot["cost"], "conversions": slot["conversions"], "value": slot["value"], "roas": roas,
                "profit": slot["value"] * margin - slot["cost"], "cpa": metrics.div(slot["cost"], slot["conversions"]),
                "breakeven_cpa": value_per_conv * margin if value_per_conv is not None else None,
                "share_of_cost": metrics.div(slot["cost"], total_cost), "share_of_value": metrics.div(slot["value"], total_value),
                "verdict": verdict, "roas_low": lo, "roas_high": hi, "status": slot["status"] or "not in report", "type": slot["type"]}

    last_day = max(all_days) if all_days else None
    campaigns = []
    for name, slot in camps.items():
        item = describe(slot)
        item["campaign"] = name
        item["brand"] = name in brand
        if has_days and name in daily:
            series = daily[name]
            first = min(series)
            filled = common.fill_days({d: {"cost": v["cost"], "value": v["value"]} for d, v in series.items()}, first, last_day, ["cost", "value"])
            recent_from = last_day - dt.timedelta(days=args.recent_days - 1)
            recent = [(d, v) for d, v in filled if d >= recent_from]
            r_cost, r_value = sum(v["cost"] for _, v in recent), sum(v["value"] for _, v in recent)
            item["recent"] = {"from": recent_from.isoformat(), "to": last_day.isoformat(), "cost": r_cost, "value": r_value,
                              "roas": metrics.div(r_value, r_cost), "cost_per_day": r_cost / len(recent) if recent else None}
            lost = [series[d]["lost"] for d in series if d >= recent_from and series[d]["lost"] is not None]
            item["recent"]["lost_is_budget"] = testmath.mean(lost) if lost else None
            if serving(slot):
                shape = curve([(d, v["cost"], v["value"]) for d, v in filled], args.confidence)
                if "elasticity" in shape and item["recent"]["roas"]:
                    r = item["recent"]["roas"]
                    shape["marginal_roas"] = shape["elasticity"] * r
                    shape["marginal_low"], shape["marginal_high"] = shape["low"] * r, shape["high"] * r
                    shape["next_dollar"] = ("Pays" if shape["marginal_low"] > breakeven else
                                            "Does not pay" if shape["marginal_high"] < breakeven else "Unclear")
                    if shape["next_dollar"] == "Unclear" and "reason" not in shape:
                        shape["reason"] = "the range for the next dollar's return crosses break even"
                        shape["needs"] = "more days at different spend levels"
                item["curve"] = shape
            else:
                item["curve"] = {"reason": "the campaign is %s, not serving" % (slot["status"] or "not enabled"),
                                 "needs": "nothing: the next dollar question is for serving campaigns"}
        campaigns.append(item)
    campaigns.sort(key=lambda c: -c["profit"])

    def block(items):
        cost = sum(i["cost"] for i in items)
        value = sum(i["value"] for i in items)
        conv = sum(i["conversions"] for i in items)
        return {"campaigns": len(items), "cost": cost, "value": value, "conversions": conv, "roas": metrics.div(value, cost),
                "profit": value * margin - cost}
    account = block(campaigns)
    no_brand = block([c for c in campaigns if not c["brand"]])
    groups_out = []
    for (camp, group), slot in groups.items():
        item = describe(slot)
        item.update({"campaign": camp, "ad_group": group})
        groups_out.append(item)
    groups_out.sort(key=lambda g: -g["profit"])
    check = common.reconcile(meta, rows, ("cost", "conversions") + (("conv_value",) if not args.value_per_conversion else ()))
    span = [min(all_days).isoformat(), max(all_days).isoformat()] if all_days else meta["date_range"]

    payload = {"report": os.path.basename(args.report), "title_rows": meta["title_rows"], "period": span, "margin": margin,
               "value_source": value_source, "value_is_profit": args.value_is_profit, "breakeven_roas": breakeven,
               "confidence": args.confidence, "brand_rule": brand_rule, "brand": sorted(brand), "account": account,
               "account_without_brand": no_brand, "campaigns": campaigns, "ad_groups": groups_out, "reconcile": check,
               "thresholds": {"min_curve_days": MIN_CURVE_DAYS, "max_zero_value_share": MAX_ZERO_VALUE_SHARE, "recent_days": args.recent_days}}

    def row_for(c, first_cols):
        return first_cols + [c["status"], round(c["cost"], 2), round(c["conversions"], 2), round(c["value"], 2), c["roas"], round(c["profit"], 2),
                             c["cpa"], c["breakeven_cpa"], c["share_of_cost"], c["verdict"]]
    head = ["Status", "Cost", "Conversions", "Value", "Value / cost", "Profit after ad cost", "Cost / conv.", "Break even cost / conv.", "Share of cost", "Call"]
    fmt = {1: "money", 2: "money", 3: "money", 4: "money", 5: "money", 6: "money", 7: "money", 8: "pct"}
    book = xlsx.Workbook()
    book.add_sheet("Campaigns", ["Campaign"] + head, [row_for(c, [c["campaign"]]) for c in campaigns],
                   formats={k + 1: v for k, v in fmt.items()}, widths={0: 30, 10: 28})
    if groups_out:
        book.add_sheet("Ad groups", ["Campaign", "Ad group"] + head, [row_for(g, [g["campaign"], g["ad_group"]]) for g in groups_out],
                       formats={k + 2: v for k, v in fmt.items()}, widths={0: 30, 1: 30, 11: 28})
    curve_rows = []
    for c in campaigns:
        k = c.get("curve")
        if k is None:
            continue
        curve_rows.append([c["campaign"], k.get("days_used"), k.get("elasticity"), k.get("low"), k.get("high"),
                           c.get("recent", {}).get("roas"), k.get("marginal_roas"), k.get("marginal_low"), k.get("marginal_high"),
                           breakeven, k.get("next_dollar") or "Not answered", why_not(k)])
    if curve_rows:
        book.add_sheet("Next dollar (estimate)", ["Campaign", "Days used", "Value growth per 1% more spend (%)", "Low", "High", "Recent value / cost",
                                                  "Next dollar value / cost", "Low", "High", "Break even", "Verdict", "Why not answered, and what would allow it"], curve_rows,
                       formats={1: "int", 2: "money", 3: "money", 4: "money", 5: "money", 6: "money", 7: "money", 8: "money", 9: "money"},
                       widths={0: 30, 2: 18, 10: 16, 11: 70})
    book.add_sheet("Totals", ["Scope", "Campaigns", "Cost", "Conversions", "Value", "Value / cost", "Profit after ad cost"],
                   [["Account", account["campaigns"], account["cost"], account["conversions"], account["value"], account["roas"], account["profit"]],
                    ["Account without brand", no_brand["campaigns"], no_brand["cost"], no_brand["conversions"], no_brand["value"], no_brand["roas"], no_brand["profit"]]],
                   formats={1: "int", 2: "money", 3: "money", 4: "money", 5: "money", 6: "money"}, widths={0: 24})

    money, num = metrics.money, common.number
    lines = ["# Return on investment", ""] + ["%s." % t for t in meta["title_rows"]]
    if span:
        lines += ["", "Period read: %s to %s." % tuple(span)]
    if common.currency_line(rows):
        lines.append(common.currency_line(rows))
    lines += ["Margin: %s%s. Value: %s. Break even Conv. value / cost: %s (1 / margin)." % (
        metrics.pct(margin, 0), " (Conv. value already holds profit)" if args.value_is_profit else "", value_source, num(breakeven))]
    losing = [c for c in campaigns if c["verdict"] in ("Loses money", "No conversions")]
    paying = [c for c in campaigns if c["verdict"] == "Profitable"]
    unsure = [c for c in campaigns if c["verdict"] == "Too few conversions to call"]
    lines += ["", "## The answer", "",
              "- **Account:** profit after ad cost %s on %s of cost. Conv. value / cost %s against a break even of %s." % (
                  money(account["profit"]), money(account["cost"]), num(account["roas"]), num(breakeven))]
    if brand:
        lines.append("- **Without brand** (%s: %s): profit %s on %s of cost, Conv. value / cost %s." % (
            brand_rule, ", ".join(sorted(brand)), money(no_brand["profit"]), money(no_brand["cost"]), num(no_brand["roas"])) +
            " Brand's return is attributed, and brand searches are the ones most likely to convert without the ads.")
    for label, items in (("Loses money", losing), ("Profitable", paying), ("Too few conversions to call", unsure)):
        if items:
            lines.append("- **%s:** %s." % (label + (" by attributed value" if label == "Profitable" and any(c["brand"] for c in items) else ""), "; ".join("%s (profit %s, Conv. value / cost %s%s)" % (
                c["campaign"], money(c["profit"]), num(c["roas"]), ", %s" % c["status"] if c["status"].lower() not in ("enabled", "not in report") else "") for c in items)))
    nexts = [c for c in campaigns if c.get("curve", {}).get("next_dollar") in ("Pays", "Does not pay")]
    open_ones = [c for c in campaigns if c.get("curve") and c["curve"].get("next_dollar") not in ("Pays", "Does not pay")]
    for c in nexts:
        k = c["curve"]
        lines.append("- **Next dollar in %s:** %s (estimate). Recent Conv. value / cost is %s; each extra dollar brings about %s (range %s to %s) against a break even of %s." % (
            c["campaign"], k["next_dollar"].lower(), num(c["recent"]["roas"]), num(k["marginal_roas"]), num(k["marginal_low"]), num(k["marginal_high"]), num(breakeven)))
    if open_ones:
        lines.append("- **Next dollar not answered:**")
        for c in open_ones:
            k = c["curve"]
            lines.append("  - %s: %s. %s." % (c["campaign"], k.get("reason", "the estimate is unclear"),
                                              "Not asked" if k.get("needs", "").startswith("nothing") else "It needs " + k.get("needs", "more data")))
    lines += ["", "## Campaigns", "", "Ranked by profit after ad cost. Share of cost is the share of the whole account's cost (%s)." % money(total_cost), "",
              outputs.md_table(["Campaign", "Status", "Cost", "Conv.", "Value", "Value / cost", "Profit", "Cost / conv.", "Break even cost / conv.", "Share of cost", "Call"],
                               [[c["campaign"], c["status"], money(c["cost"]), num(c["conversions"]), money(c["value"]), num(c["roas"]), money(c["profit"]),
                                 money(c["cpa"]), money(c["breakeven_cpa"]), metrics.pct(c["share_of_cost"], 1),
                                 c["verdict"] + (" (range %s to %s)" % (num(c["roas_low"]), num(c["roas_high"])) if c["verdict"] == "Too few conversions to call" else "")]
                                for c in campaigns])]
    if has_days:
        lines += ["", "## Where the next dollar goes (estimate)", "",
                  "How much Conv. value grows when daily spend is higher, from the campaign's own days, then the Conv. value the next dollar brings at the last %d days' return." % args.recent_days, ""]
        rows_out = []
        for c in campaigns:
            k = c.get("curve")
            if not k:
                continue
            if "elasticity" in k:
                rows_out.append([c["campaign"], "%d days" % k["days_used"] if k["basis"] == "days" else "%d weeks" % k["weeks_used"],
                                 "%s (%s to %s)" % (num(k["elasticity"]), num(k["low"]), num(k["high"])), k["shape"],
                                 num(c["recent"]["roas"]), "%s (%s to %s)" % (num(k.get("marginal_roas")), num(k.get("marginal_low")), num(k.get("marginal_high"))),
                                 k.get("next_dollar", "n/a"), why_not(k),
                                 metrics.pct(c["recent"]["lost_is_budget"], 0) if c["recent"].get("lost_is_budget") is not None else "n/a"])
            else:
                rows_out.append([c["campaign"], "%d days" % k.get("days_used", 0), "not fitted", "", num(c.get("recent", {}).get("roas")), "", "Not answered", why_not(k), ""])
        lines.append(outputs.md_table(["Campaign", "Read from", "Value growth per 1% more spend", "Shape", "Recent value / cost", "Next dollar value / cost",
                                       "Next dollar", "Why not answered, and what would allow it", "Recent Search lost IS (budget)"], rows_out))
        lines += ["", "A value growth of 1.00 means value rises in step with spend. Below 1.00, each extra dollar returns less than the average dollar."]
    lines += ["", "## How the numbers were made", "",
              "- " + common.reconcile_line(check),
              "- Profit after ad cost = value x margin, minus Cost. Break even Conv. value / cost = 1 / margin; break even cost / conv. = value per conversion x margin. This is business arithmetic, not a Google Ads rule (`references/test-math.md`).",
              "- A campaign's call uses a %s range on its conversion count (Poisson), holding value per conversion fixed. When that range crosses break even, it is too few conversions to call." % metrics.pct(args.confidence, 0),
              "- Paused campaigns are counted in the totals for the cost they spent, and left out of the next dollar question.",
              "- Next dollar: log(daily value) = a + b log(daily cost) + a weekday term (when there are 28 days or more), by least squares, on days with both spend and value. It needs at least %d such days. When more than %s of days with spend had no value, or there are too few days, it uses full Monday to Sunday weeks instead and needs %d of them. b times the last %d days' Conv. value / cost is the next dollar's return. It is an **estimate**: days with more spend often also had more demand, which pulls b toward 1." % (
                  MIN_CURVE_DAYS, metrics.pct(MAX_ZERO_VALUE_SHARE, 0), MIN_CURVE_WEEKS, args.recent_days),
              "- The curve can't be read when spend hardly varied: a typical day (or week) within about %s of the average. That case says so, and what data would let it answer." % metrics.pct(MIN_SPEND_SPREAD, 0),
              "", "## What this did not cover", "",
              "- Conv. value is what Google Ads attributed, not what the ads caused. A campaign can look profitable and still add little: only a test shows the difference.",
              "- **Official** (`references/incrementality.md`): a 2012 Google meta-analysis found ad clicks less incremental when the advertiser already ranked first organically. That is a historical average, not a current rate. Test brand with an experiment before moving its budget.",
              "- Costs other than ad cost and the margin (fees, labour, returns), and value that arrives after the report's last day.", ""]
    text = "\n".join(lines)
    common.finish(outputs.ensure_dir(args.out), "roi", text, payload, book)


if __name__ == "__main__":
    main()
