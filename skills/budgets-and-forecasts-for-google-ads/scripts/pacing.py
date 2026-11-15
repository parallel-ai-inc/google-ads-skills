#!/usr/bin/env python3
"""Budget pacing, month end forecast and reallocation evidence.

Reads a Google Ads campaign report segmented by Day and computes, for each
campaign and the account: spend so far this month, the month end forecast two
ways, Google's monthly spending limit, whether budget is the constraint, and
the evidence for moving budget between campaigns.

    python3 pacing.py REPORT --out OUTPUTDIR [--month 2026-11] [--monthly-target 9000]
"""
import argparse
import datetime as dt
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics, outputs, xlsx  # noqa: E402

# Google bills at most 30.4 times the average daily budget in a month.
MONTHLY_LIMIT_FACTOR = 30.4
RECENT_DAYS = 7
# Cost per conversion trend: the last 14 days against the 14 before.
TREND_DAYS = 14
SHARP_CHANGE = 0.25
MIN_TREND_CONVERSIONS = 5


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--out", required=True)
    parser.add_argument("--month", help="YYYY-MM. Default: the latest month in the report")
    parser.add_argument("--monthly-target", type=float, help="the account's spend target for the month")
    parser.add_argument("--exclude", default="", help="campaigns to leave out of the efficiency comparison, comma separated, for example brand campaigns")
    args = parser.parse_args()

    meta, rows = io.read_report(args.report)
    io.require(meta, ["day", "campaign", "cost"], "campaign report segmented by Day")
    has_budget = "budget" in meta["columns"]
    has_lost = "lost_is_budget" in meta["columns"]
    for row in rows:
        row["date"] = dates.parse_day(row.get("day"))
    rows = [r for r in rows if r["date"] and r.get("campaign")]
    if not rows:
        raise SystemExit("I can't read any dated rows. Add the Day segment to the campaign report and download it again.")

    last_day = max(r["date"] for r in rows)
    month = args.month or dates.month_key(last_day)
    in_month = [r for r in rows if dates.month_key(r["date"]) == month]
    if not in_month:
        raise SystemExit("The report has no rows for %s." % month)
    as_of = max(r["date"] for r in in_month)
    data_start = min(r["date"] for r in in_month)
    month_days = dates.days_in_month(as_of)
    elapsed, remaining = as_of.day, month_days - as_of.day
    # Averages use the days the report covers, which can be fewer than the days gone by.
    covered = (as_of - data_start).days + 1
    recent_start = as_of - dt.timedelta(days=RECENT_DAYS - 1)

    campaigns = {}
    for row in in_month:
        slot = campaigns.setdefault(row["campaign"], {"campaign": row["campaign"], "days": {}, "budget": None, "lost": [], "status": "", "status_day": None})
        if row.get("campaign_status") and (slot["status_day"] is None or row["date"] >= slot["status_day"]):
            slot["status_day"], slot["status"] = row["date"], row["campaign_status"]
        day = slot["days"].setdefault(row["date"], {"cost": 0.0, "clicks": 0.0, "impressions": 0.0, "conversions": 0.0, "conv_value": 0.0})
        for field in day:
            day[field] += row.get(field) or 0
        # The budget in force is the one on the latest day in the month.
        if row.get("budget") and (slot.get("budget_day") is None or row["date"] >= slot["budget_day"]):
            slot["budget_day"], slot["budget"] = row["date"], row["budget"]
        if has_lost:
            slot["lost"].append(row.get("lost_is_budget"))

    table = []
    for slot in campaigns.values():
        days = slot["days"]
        mtd = {field: sum(d[field] for d in days.values()) for field in ("cost", "clicks", "impressions", "conversions", "conv_value")}
        recent = [days[d]["cost"] for d in days if d >= recent_start]
        recent_avg = metrics.div(sum(recent), len(recent)) or 0.0
        mtd_avg = metrics.div(mtd["cost"], covered) or 0.0
        not_serving = slot["status"].strip().lower() in ("paused", "removed", "ended")
        budget = slot["budget"]
        limit = budget * MONTHLY_LIMIT_FACTOR if budget else None
        forecast_recent = mtd["cost"] + recent_avg * remaining
        forecast_mtd = mtd["cost"] + mtd_avg * remaining
        reported = [v for v in slot["lost"] if v is not None]
        lost_avg = metrics.div(sum(reported), len(slot["lost"])) if slot["lost"] else None
        near_budget = bool(budget) and recent_avg >= 0.95 * budget
        limited = (bool(reported and lost_avg is not None and lost_avg >= 10) or near_budget) and not not_serving
        hits_limit_on = None
        if limit and recent_avg > 0 and forecast_recent > limit:
            days_to_limit = int((limit - mtd["cost"]) / recent_avg)
            hits_limit_on = (as_of + dt.timedelta(days=max(days_to_limit, 0) + 1)).isoformat()
        if not_serving:
            status = slot["status"].strip().capitalize()
            hits_limit_on = None
        elif limit is None:
            status = "No budget column in the report"
        elif forecast_recent > limit:
            status = "Will reach Google's monthly limit"
        elif forecast_recent >= 0.9 * limit:
            status = "On pace to use the budget"
        else:
            status = "Underspending the budget"
        table.append({
            "campaign": slot["campaign"], "campaign_status": slot["status"], "not_serving": not_serving, "daily_budget": budget, "monthly_limit": limit,
            "mtd_cost": mtd["cost"], "mtd_avg_daily": mtd_avg, "recent_avg_daily": recent_avg,
            "forecast_recent": forecast_recent, "forecast_mtd": forecast_mtd,
            "forecast_billed": min(forecast_recent, limit) if limit else forecast_recent,
            "share_of_limit": metrics.div(forecast_recent, limit), "status": status,
            "limited_by_budget": limited, "lost_is_budget": lost_avg, "near_budget": near_budget, "hits_limit_on": hits_limit_on,
            "conversions": mtd["conversions"], "conv_value": mtd["conv_value"],
            "cpa": metrics.div(mtd["cost"], mtd["conversions"]), "roas": metrics.div(mtd["conv_value"], mtd["cost"]),
        })
    table.sort(key=lambda c: -c["mtd_cost"])

    account = {field: sum(c[field] for c in table) for field in ("mtd_cost", "forecast_recent", "forecast_mtd", "forecast_billed", "conversions", "conv_value")}
    account["cpa"] = metrics.div(account["mtd_cost"], account["conversions"])
    account["roas"] = metrics.div(account["conv_value"], account["mtd_cost"])
    account["monthly_limit"] = sum(c["monthly_limit"] for c in table if c["monthly_limit"] and not c["not_serving"]) or None
    account["daily_budget_total"] = sum(c["daily_budget"] for c in table if c["daily_budget"] and not c["not_serving"]) or None
    # Budget a campaign that underspends did not use over the last 7 days. Trimming it lowers
    # Google's monthly limit without lowering what the campaign spends.
    account["unused_budget_per_day"] = sum(max(c["daily_budget"] - c["recent_avg_daily"], 0) for c in table
                                           if c["daily_budget"] and not c["not_serving"] and c["status"] == "Underspending the budget")
    target = args.monthly_target
    if target:
        account["target"] = target
        account["needed_daily"] = metrics.div(target - account["mtd_cost"], remaining) if remaining else None
        account["forecast_vs_target"] = metrics.div(account["forecast_billed"], target)
        # The gap between the capped forecast and the target, spread over the days left: the daily
        # budget to take out (or the room to add) across campaigns that spend their budget.
        account["gap_to_target"] = account["forecast_billed"] - target
        account["gap_per_day"] = metrics.div(account["gap_to_target"], remaining) if remaining else None
        # For a whole month (next month, for example): Google bills at most 30.4 times the daily
        # budget, so daily budgets totalling the target / 30.4 cap a month at the target.
        account["daily_total_for_target"] = target / MONTHLY_LIMIT_FACTOR

    # Cost per conversion trend, over the whole report, not only this month. A campaign whose
    # cost per conversion changed sharply is held out of any budget move until the cause is known.
    trend_recent_start = as_of - dt.timedelta(days=TREND_DAYS - 1)
    trend_prior_end = trend_recent_start - dt.timedelta(days=1)
    trend_prior_start = trend_prior_end - dt.timedelta(days=TREND_DAYS - 1)
    trend_covered = min(r["date"] for r in rows) <= trend_prior_start
    has_clicks = "clicks" in meta["columns"]
    all_days = {}
    for row in rows:
        day = all_days.setdefault(row["campaign"], {}).setdefault(row["date"], [0.0, 0.0, 0.0])
        day[0] += row.get("cost") or 0
        day[1] += row.get("conversions") or 0
        day[2] += row.get("clicks") or 0
    for c in table:
        days = all_days.get(c["campaign"], {})
        rc = sum(v[0] for d, v in days.items() if trend_recent_start <= d <= as_of)
        rv = sum(v[1] for d, v in days.items() if trend_recent_start <= d <= as_of)
        rk = sum(v[2] for d, v in days.items() if trend_recent_start <= d <= as_of)
        pc = sum(v[0] for d, v in days.items() if trend_prior_start <= d <= trend_prior_end)
        pv = sum(v[1] for d, v in days.items() if trend_prior_start <= d <= trend_prior_end)
        pk = sum(v[2] for d, v in days.items() if trend_prior_start <= d <= trend_prior_end)
        c["cpa_prior"], c["cpa_recent"] = metrics.div(pc, pv), metrics.div(rc, rv)
        c["cpa_trend"] = metrics.change(c["cpa_recent"], c["cpa_prior"])
        c["conversions_prior"], c["conversions_recent"] = pv, rv
        # Cost per conversion is cost per click divided by conversions per click, so a change in
        # it comes from one, the other or both. Which moved more says where to look first.
        c["cpc_prior"], c["cpc_recent"] = (metrics.div(pc, pk), metrics.div(rc, rk)) if has_clicks else (None, None)
        c["cvr_prior"], c["cvr_recent"] = (metrics.div(pv, pk), metrics.div(rv, rk)) if has_clicks else (None, None)
        c["cpc_change"] = metrics.change(c["cpc_recent"], c["cpc_prior"])
        c["cvr_change"] = metrics.change(c["cvr_recent"], c["cvr_prior"])
        driver = None
        if c["cpc_change"] is not None and c["cvr_change"] is not None and c["cvr_change"] > -1:
            by_price = abs(math.log(1 + c["cpc_change"]))
            by_rate = abs(math.log(1 + c["cvr_change"]))
            driver = "the price of clicks" if by_price >= by_rate else "conversions per click"
        c["cpa_driver"] = driver
        enough = pv >= MIN_TREND_CONVERSIONS
        c["cpa_sharp_change"] = bool(trend_covered and enough and (
            (rv >= MIN_TREND_CONVERSIONS and c["cpa_trend"] is not None and abs(c["cpa_trend"]) >= SHARP_CHANGE) or (rv == 0 and rc > 0)))

    # Evidence for moving budget. A judgment still has to be made from the playbook.
    left_out = [name.strip() for name in args.exclude.split(",") if name.strip()]
    compared = [c for c in table if c["campaign"] not in left_out and not c["not_serving"]]
    baseline_cpa = metrics.div(sum(c["mtd_cost"] for c in compared), sum(c["conversions"] for c in compared))
    receivers, donors, held = [], [], []
    for c in compared:
        if not baseline_cpa or not c["cpa"]:
            continue
        if c["cpa_sharp_change"]:
            held.append({key: c[key] for key in ("campaign", "cpa_prior", "cpa_recent", "cpa_trend", "conversions_prior", "conversions_recent",
                                                  "cpc_prior", "cpc_recent", "cpc_change", "cvr_prior", "cvr_recent", "cvr_change", "cpa_driver",
                                                  "limited_by_budget", "status", "hits_limit_on")})
            continue
        better = c["cpa"] <= baseline_cpa
        if c["limited_by_budget"] and better and c["conversions"] >= 10:
            lost = c["lost_is_budget"]
            headroom = c["mtd_cost"] * (lost / (100.0 - lost)) if lost and lost < 95 else None
            per_day = metrics.div(headroom, covered) if headroom else None
            # Budget moves go in at least two steps, each read before the next, so a first step
            # takes at most half the room.
            receivers.append({"campaign": c["campaign"], "cpa": c["cpa"], "lost_is_budget": lost,
                              "extra_cost_if_unlimited_so_far": headroom, "extra_per_day": per_day,
                              "first_step_per_day": per_day / 2 if per_day else None,
                              "why": "Limited by budget, with a cost per conversion at or below the comparison average"})
        elif not c["limited_by_budget"] and c["cpa"] >= 1.25 * baseline_cpa and c["conversions"] >= 5:
            donors.append({"campaign": c["campaign"], "cpa": c["cpa"], "mtd_cost": c["mtd_cost"],
                           "why": "Not limited by budget, with a cost per conversion at least 25% above the comparison average"})

    # Where a ceiling cut comes from: only campaigns that spend their budget, a held out campaign
    # first and one that could take more last, the larger budget first within each group. For a
    # campaign that will reach its monthly limit, a lower daily budget lowers that limit by about
    # the same amount for each day left, so the daily cut holds the month.
    ceiling_cut = []
    if target and account.get("gap_per_day") and account["gap_to_target"] > 0 and account["mtd_cost"] < target:
        held_names = {h["campaign"] for h in held}
        receiver_names = {r["campaign"] for r in receivers}
        spenders = [c for c in table if not c["not_serving"] and c["daily_budget"]
                    and c["status"] in ("Will reach Google's monthly limit", "On pace to use the budget")]
        spenders.sort(key=lambda c: (0 if c["campaign"] in held_names else 2 if c["campaign"] in receiver_names else 1, -c["daily_budget"]))
        left = account["gap_per_day"]
        for c in spenders:
            if left <= 0.005:
                break
            cut = min(left, c["daily_budget"])
            ceiling_cut.append({"campaign": c["campaign"], "daily_budget": c["daily_budget"], "cut": cut, "new_daily_budget": c["daily_budget"] - cut,
                                "held": c["campaign"] in held_names, "could_take_more": c["campaign"] in receiver_names})
            left -= cut
        account["ceiling_cut"] = ceiling_cut
        account["ceiling_cut_uncovered"] = left if left > 0.005 else 0.0

    result = {"report": os.path.basename(args.report), "title_rows": meta["title_rows"], "month": month,
              "as_of": as_of.isoformat(), "days_elapsed": elapsed, "days_remaining": remaining, "days_in_month": month_days,
              "has_budget": has_budget, "has_lost_is": has_lost, "campaigns": table, "account": account,
              "comparison": {"cpa": baseline_cpa, "left_out": left_out},
              "trend": {"covered": trend_covered, "prior": [trend_prior_start.isoformat(), trend_prior_end.isoformat()],
                        "recent": [trend_recent_start.isoformat(), as_of.isoformat()]},
              "receivers": receivers, "donors": donors, "held": held}
    out = outputs.ensure_dir(args.out)
    outputs.write_json(os.path.join(out, "pacing.json"), result)

    def r2(value):
        return round(value, 2) if value is not None else None

    def signed(value):
        return "n/a" if value is None else ("+" if value >= 0 else "") + metrics.pct(value)

    pacing_header = ["Campaign", "Daily budget", "Google's monthly limit", "Spend so far", "Avg per day, last 7 days", "Forecast at the recent pace",
                     "Forecast at the month's pace", "Forecast as share of limit", "Status", "Limited by budget", "Lost IS (budget), avg"]
    pacing_rows = [[c["campaign"], r2(c["daily_budget"]), r2(c["monthly_limit"]), r2(c["mtd_cost"]), r2(c["recent_avg_daily"]), r2(c["forecast_recent"]),
                    r2(c["forecast_mtd"]), c["share_of_limit"], c["status"], c["limited_by_budget"],
                    (c["lost_is_budget"] / 100.0) if c["lost_is_budget"] is not None else None] for c in table]
    eff_header = ["Campaign", "Spend so far", "Conversions", "Cost / conv.", "Conv. value", "Conv. value / cost"]
    eff_rows = [[c["campaign"], r2(c["mtd_cost"]), r2(c["conversions"]), r2(c["cpa"]), r2(c["conv_value"]), r2(c["roas"])] for c in table]
    eff_rows.append(["Account", r2(account["mtd_cost"]), r2(account["conversions"]), r2(account["cpa"]), r2(account["conv_value"]), r2(account["roas"])])
    daily_days = sorted({d for slot in campaigns.values() for d in slot["days"]})
    daily_header = ["Day"] + [c["campaign"] for c in table]
    daily_rows = [[d.isoformat()] + [r2(campaigns[c["campaign"]]["days"].get(d, {}).get("cost")) for c in table] for d in daily_days]

    book = xlsx.Workbook()
    book.add_sheet("Pacing", pacing_header, pacing_rows, formats={1: "money", 2: "money", 3: "money", 4: "money", 5: "money", 6: "money", 7: "pct", 10: "pct"}, widths={0: 30, 8: 34})
    book.add_sheet("Efficiency this month", eff_header, eff_rows, formats={1: "money", 2: "money", 3: "money", 4: "money", 5: "money"}, widths={0: 30})
    book.add_sheet("Reallocation evidence", ["Role", "Campaign", "Cost / conv.", "Lost IS (budget), avg", "Spend it could have added so far",
                                             "A day, upper bound", "First step, a day", "Why"],
                   [["Could take more", r["campaign"], r2(r["cpa"]), (r["lost_is_budget"] / 100.0) if r["lost_is_budget"] is not None else None, r2(r["extra_cost_if_unlimited_so_far"]),
                     r2(r["extra_per_day"]), r2(r["first_step_per_day"]), r["why"]] for r in receivers]
                   + [["Could give", d["campaign"], r2(d["cpa"]), None, None, None, None, d["why"]] for d in donors]
                   + [["Held out", h["campaign"], r2(h["cpa_recent"]), None, None, None, None,
                       "Cost per conversion moved %s over the last %d days%s" % (signed(h["cpa_trend"]), TREND_DAYS,
                                                                              ", mostly from %s" % h["cpa_driver"] if h["cpa_driver"] else "")] for h in held],
                   formats={2: "money", 3: "pct", 4: "money", 5: "money", 6: "money"}, widths={1: 30, 7: 70})
    book.add_sheet("Daily cost", daily_header, daily_rows, formats={i: "money" for i in range(1, len(daily_header))})
    book.save(os.path.join(out, "budget-pacing.xlsx"))

    lines = ["# Budget pacing", ""]
    lines += ["%s." % t for t in meta["title_rows"]]
    lines += ["", "Month %s, read through %s: day %d of %d, %d days left." % (month, as_of.isoformat(), elapsed, month_days, remaining)]
    if data_start.day > 1:
        lines += ["", "**The report starts on %s.** Spend earlier in the month is not in it, so spend so far and both forecasts leave it out. Averages use the %d days the report covers." % (data_start.isoformat(), covered)]
    lines += ["",
              "## Account", "",
              "- Spend so far: %s." % metrics.money(account["mtd_cost"]),
              "- Forecast for the month at the pace of the last %d days: %s." % (RECENT_DAYS, metrics.money(account["forecast_recent"])),
              "- Forecast at the month's average pace: %s." % metrics.money(account["forecast_mtd"])]
    if account["monthly_limit"]:
        lines.append("- Google's monthly limit across the campaigns that are serving: %s. That is 30.4 times their daily budgets, which total %s a day." % (
            metrics.money(account["monthly_limit"]), metrics.money(account["daily_budget_total"])))
        lines.append("- **Forecast once each campaign stops at its monthly limit: %s.** This is the most the month should cost at the recent pace." % metrics.money(account["forecast_billed"]))
    if target:
        lines.append("- Your target for the month: %s. The forecast once limits apply is %s of it." % (metrics.money(target), metrics.pct(account["forecast_vs_target"])))
        recent_daily = sum(c["recent_avg_daily"] for c in table if not c["not_serving"])
        if account["mtd_cost"] >= target:
            lines.append("- Spend so far is already above the target.")
        elif account.get("needed_daily") is not None:
            gap = recent_daily - account["needed_daily"]
            lines.append("- To land on the target, the account can spend %s a day for the %d days left. The last %d days averaged %s a day, %s %s." % (
                metrics.money(account["needed_daily"]), remaining, RECENT_DAYS, metrics.money(recent_daily),
                "which is", ("%s a day more than that" if gap >= 0 else "%s a day less than that") % metrics.money(abs(gap))))
        if account["mtd_cost"] < target and account.get("gap_per_day") is not None:
            if account["gap_to_target"] > 0:
                lines.append("- **The forecast once limits apply is %s above the target: about %s a day for the %d days left.** If the target is a ceiling, that is the daily budget to take out of campaigns that spend their budget. It can be less than the gap to the last %d days' pace, because Google's monthly limits already hold back the campaigns that will reach them." % (
                    metrics.money(account["gap_to_target"]), metrics.money(account["gap_per_day"]), remaining, RECENT_DAYS))
                for cut in account.get("ceiling_cut", []):
                    why = "held out, so first" if cut["held"] else "could take more, so last" if cut["could_take_more"] else "spends its budget"
                    lines.append("  - Take it from %s (%s): daily budget %s to about %s, %s a day less." % (
                        cut["campaign"], why, metrics.money(cut["daily_budget"]), metrics.money(cut["new_daily_budget"]), metrics.money(cut["cut"])))
                if account.get("ceiling_cut_uncovered"):
                    lines.append("  - About %s a day is left over: no other campaign spends its budget. Lowering an underspending campaign's budget does not cut its spend, so the ceiling cannot be held by budgets alone." % (
                        metrics.money(account["ceiling_cut_uncovered"])))
            else:
                lines.append("- **The forecast once limits apply is %s below the target: about %s a day for the %d days left.** If the target is a goal to reach, that is how much more a day the account can spend and still land on it." % (
                    metrics.money(-account["gap_to_target"]), metrics.money(-account["gap_per_day"]), remaining))
    if target and account["daily_budget_total"]:
        cap, now = account["daily_total_for_target"], account["daily_budget_total"]
        lines += ["", "## A whole month at the target", "",
                  "For planning next month, or any full month with the same campaigns. Google bills at most 30.4 times the daily budget in a month, whatever the month's length.", "",
                  "- Daily budgets that cap a whole month at %s total %s a day: the target divided by 30.4. Today the serving campaigns' budgets total %s a day, %s %s that." % (
                      metrics.money(target), metrics.money(cap), metrics.money(now), metrics.money(abs(now - cap)), "more than" if now >= cap else "less than")]
        if now > cap:
            unused = account["unused_budget_per_day"]
            cover = "That covers the whole cut." if unused >= now - cap else "That covers %s of the %s cut. The other %s a day has to come from campaigns that spend their budget." % (
                metrics.money(unused), metrics.money(now - cap), metrics.money(now - cap - unused))
            lines.append("- Campaigns underspending their budget left about %s a day unused over the last %d days. Trimming that unused budget lowers Google's limit without lowering what they spend. %s" % (
                metrics.money(unused), RECENT_DAYS, cover))
        else:
            lines.append("- Today's budgets cannot bill the target in a full month. More budget helps only the campaigns limited by budget: see the evidence for moving budget.")
    lines += ["", "## Campaigns", "",
              outputs.md_table(["Campaign", "Daily budget", "Spend so far", "Forecast", "Monthly limit", "Status", "Limited by budget"],
                               [[c["campaign"], metrics.money(c["daily_budget"]), metrics.money(c["mtd_cost"]), metrics.money(c["forecast_recent"]),
                                 metrics.money(c["monthly_limit"]), c["status"] + (" around %s" % c["hits_limit_on"] if c["hits_limit_on"] else ""),
                                 "Yes" if c["limited_by_budget"] else "No"] for c in table])]
    lines += ["", "## Cost per conversion trend", ""]
    if trend_covered:
        lines += ["Last %d days (%s to %s) against the %d days before. A change of %s or more, with at least %d conversions in the earlier period, counts as sharp." % (
            TREND_DAYS, trend_recent_start.isoformat(), as_of.isoformat(), TREND_DAYS, metrics.pct(SHARP_CHANGE, 0), MIN_TREND_CONVERSIONS), "",
                  outputs.md_table(["Campaign", "Cost / conv. before", "Cost / conv. last %d days" % TREND_DAYS, "Change", "Sharp change"],
                                   [[c["campaign"], metrics.money(c["cpa_prior"]), metrics.money(c["cpa_recent"]),
                                     "n/a" if c["cpa_trend"] is None else ("+" if c["cpa_trend"] >= 0 else "") + metrics.pct(c["cpa_trend"]),
                                     "Yes" if c["cpa_sharp_change"] else "No"] for c in table if not c["not_serving"]])]
    else:
        lines.append("The report does not reach back %d days before %s, so the trend could not be checked. Download a longer date range to check it." % (
            TREND_DAYS * 2, as_of.isoformat()))
    lines += ["", "## Evidence for moving budget", "",
              "Cost per conversion is compared with %s: the total cost of %s this month divided by their total conversions." % (
                  metrics.money(baseline_cpa), "the serving campaigns" if not left_out else "the serving campaigns other than " + ", ".join(left_out)), ""]
    for h in held:
        text = "- **%s is held out.** Its cost per conversion moved from %s to %s over the last %d days, on %s conversions before and %s in the last %d days." % (
            h["campaign"], metrics.money(h["cpa_prior"]), metrics.money(h["cpa_recent"]), TREND_DAYS,
            "{:,.1f}".format(h["conversions_prior"]), "{:,.1f}".format(h["conversions_recent"]), TREND_DAYS)
        if h["cpa_driver"]:
            text += " Avg. CPC went from %s to %s (%s) and conv. rate from %s to %s (%s), so most of the change came from %s." % (
                metrics.money(h["cpc_prior"]), metrics.money(h["cpc_recent"]), signed(h["cpc_change"]),
                metrics.pct(h["cvr_prior"]), metrics.pct(h["cvr_recent"]), signed(h["cvr_change"]), h["cpa_driver"])
        text += " Find the cause before moving its budget either way."
        lines.append(text)
    if receivers or donors:
        for r in receivers:
            extra = " At the same cost per click it could have spent about %s more so far." % metrics.money(r["extra_cost_if_unlimited_so_far"]) if r["extra_cost_if_unlimited_so_far"] else ""
            if r["extra_per_day"]:
                extra += " That is about %s a day, an upper bound. A first step of up to %s a day, half of it, leaves room for a second step once the first is read." % (
                    metrics.money(r["extra_per_day"]), metrics.money(r["first_step_per_day"]))
            lines.append("- **%s could take more.** %s (%s against %s).%s" % (r["campaign"], r["why"], metrics.money(r["cpa"]), metrics.money(baseline_cpa), extra))
        for d in donors:
            lines.append("- **%s could give.** %s (%s against %s)." % (d["campaign"], d["why"], metrics.money(d["cpa"]), metrics.money(baseline_cpa)))
    elif not held:
        lines.append("- No campaign meets both tests this month, so the numbers alone do not support a move.")
    lines += ["", "These are averages for the month so far. The next dollar in a campaign can cost more than its average, so move budget in steps.", "",
              "## How the numbers were made", "",
              "- Forecast = spend so far + average daily cost of the last %d days x days left. The second forecast uses the whole month's average." % RECENT_DAYS,
              "- Limited by budget = lost impression share to budget averaging 10%% or more, or average daily cost over the last %d days at 95%% of the daily budget or above. Paused campaigns are never limited." % RECENT_DAYS,
              "- Spend so far and the forecasts use this month only. Earlier months in the report are used only for the cost per conversion trend.",
              "- Google can spend up to twice the daily budget on one day, and bills at most 30.4 times the daily budget in a month.",
              "- Today's partial data, if the report includes today, makes the last day look low.",
              "- A first step is half the room a campaign's lost impression share to budget implies, so that budget moves in at least two steps, each read before the next.",
              "",
              "## What this did not cover", "",
              "- What a different budget would buy. Nothing here models how conversions or cost per conversion change at another budget. Google's budget simulator and Performance Planner do that.",
              "- Demand ahead, seasonality and promotions. The forecasts assume the recent pace continues.",
              "- Conversions still arriving. Recent days can gain conversions after the report was downloaded.",
              "- Shared budgets, campaign total budgets and ad schedules that switch off whole days. Each campaign is read as having its own daily budget.",
              "- Bid strategies, targets and the change history. Nothing was changed in any account.", ""]
    text = "\n".join(lines)
    with open(os.path.join(out, "budget-pacing.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote the files to %s" % out)


if __name__ == "__main__":
    main()
