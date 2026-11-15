#!/usr/bin/env python3
"""Find what changed, where, and when.

Reads a Google Ads campaign report segmented by Day and compares two periods.
For the account and each campaign it computes the change in cost and
conversions, which campaigns carry the change, which lever moved (how often
ads showed, click through rate, cost per click, conversion rate), and the day
the shift started. With a change history export it lists the account changes
made just before that day.

    python3 compare.py REPORT --out OUTPUTDIR [--days 10] [--changes CHANGE_HISTORY]
    python3 compare.py REPORT --out OUTPUTDIR --current 2026-11-03:2026-11-12 --previous 2026-10-24:2026-11-02
"""
import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics, outputs, xlsx  # noqa: E402

FIELDS = ("impressions", "clicks", "cost", "conversions", "conv_value")
LEVER_NAMES = {"impressions": "how often ads showed", "ctr": "click through rate", "cpc": "cost per click", "cvr": "conversion rate"}
# A campaign is called out when its cost or conversions moved at least this much.
NOTABLE_CHANGE = 0.20
# How many days before the shift to look for account changes.
CHANGE_LOOKBACK_DAYS = 3


def span(text):
    start, _, end = text.partition(":")
    a, b = dates.parse_day(start), dates.parse_day(end)
    if not a or not b or b < a:
        raise SystemExit("Write a period as START:END, for example 2026-11-03:2026-11-12.")
    return a, b


def sums(day_rows, start, end):
    total = {f: 0.0 for f in FIELDS}
    for day, values in day_rows.items():
        if start <= day <= end:
            for f in FIELDS:
                total[f] += values[f]
    total["ctr"] = metrics.div(total["clicks"], total["impressions"])
    total["cpc"] = metrics.div(total["cost"], total["clicks"])
    total["cvr"] = metrics.div(total["conversions"], total["clicks"])
    total["cpa"] = metrics.div(total["cost"], total["conversions"])
    total["roas"] = metrics.div(total["conv_value"], total["cost"])
    total["value_per_conv"] = metrics.div(total["conv_value"], total["conversions"])
    return total


def shift_day(day_rows, start, end, lever):
    """The day that best splits the daily series of one lever into before and after."""
    series = []
    day = start
    while day <= end:
        values = day_rows.get(day)
        if values:
            point = {"impressions": values["impressions"], "ctr": metrics.div(values["clicks"], values["impressions"]),
                     "cpc": metrics.div(values["cost"], values["clicks"]), "cvr": metrics.div(values["conversions"], values["clicks"])}[lever]
            if point is not None:
                series.append((day, point))
        day += dt.timedelta(days=1)
    best, best_score = None, 0.0
    for cut in range(3, len(series) - 2):
        before = [v for _, v in series[:cut]]
        after = [v for _, v in series[cut:]]
        gap = abs(sum(after) / len(after) - sum(before) / len(before))
        score = gap * (len(before) * len(after) / float(len(series))) ** 0.5
        if score > best_score:
            best, best_score = series[cut][0], score
    return best


def describe(scope, cur, prev):
    cost_change = metrics.change(cur["cost"], prev["cost"])
    conv_change = metrics.change(cur["conversions"], prev["conversions"])
    conv_levers = metrics.log_shares({"impressions": cur["impressions"], "ctr": cur["ctr"], "cvr": cur["cvr"]},
                                     {"impressions": prev["impressions"], "ctr": prev["ctr"], "cvr": prev["cvr"]})
    cost_levers = metrics.log_shares({"impressions": cur["impressions"], "ctr": cur["ctr"], "cpc": cur["cpc"]},
                                     {"impressions": prev["impressions"], "ctr": prev["ctr"], "cpc": prev["cpc"]})
    return {"scope": scope, "current": cur, "previous": prev, "cost_change": cost_change, "conversions_change": conv_change,
            "cpa_change": metrics.change(cur["cpa"], prev["cpa"]), "conversion_levers": conv_levers, "cost_levers": cost_levers}


def main_lever(levers):
    if not levers:
        return None
    return max(levers, key=lambda name: abs(levers[name]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--out", required=True)
    parser.add_argument("--days", type=int, default=10, help="compare the last N days with the N days before")
    parser.add_argument("--current", help="START:END")
    parser.add_argument("--previous", help="START:END")
    parser.add_argument("--changes", help="change history export")
    args = parser.parse_args()

    meta, rows = io.read_report(args.report)
    io.require(meta, ["day", "campaign", "cost", "clicks", "impressions", "conversions"], "campaign report segmented by Day")
    by_campaign, account_days, last_status = {}, {}, {}
    for row in rows:
        day = dates.parse_day(row.get("day"))
        if not day or not row.get("campaign"):
            continue
        status = (row.get("campaign_status") or "").strip()
        if status and day >= last_status.get(row["campaign"], (day, ""))[0]:
            last_status[row["campaign"]] = (day, status)
        for target in (by_campaign.setdefault(row["campaign"], {}), account_days):
            slot = target.setdefault(day, {f: 0.0 for f in FIELDS})
            for f in FIELDS:
                slot[f] += row.get(f) or 0
    if not account_days:
        raise SystemExit("I can't read any dated rows. Add the Day segment to the campaign report and download it again.")

    last = max(account_days)
    if args.current and args.previous:
        cur_start, cur_end = span(args.current)
        prev_start, prev_end = span(args.previous)
    else:
        cur_end, cur_start = last, last - dt.timedelta(days=args.days - 1)
        prev_end = cur_start - dt.timedelta(days=1)
        prev_start = prev_end - dt.timedelta(days=args.days - 1)
    if prev_start < min(account_days):
        raise SystemExit("The report starts on %s, so it does not cover the earlier period. Download a longer date range." % min(account_days).isoformat())

    account = describe("Account", sums(account_days, cur_start, cur_end), sums(account_days, prev_start, prev_end))
    campaigns = [describe(name, sums(days, cur_start, cur_end), sums(days, prev_start, prev_end)) for name, days in by_campaign.items()]
    cost_delta = account["current"]["cost"] - account["previous"]["cost"]
    conv_delta = account["current"]["conversions"] - account["previous"]["conversions"]
    for c in campaigns:
        c["cost_delta"] = c["current"]["cost"] - c["previous"]["cost"]
        c["conversions_delta"] = c["current"]["conversions"] - c["previous"]["conversions"]
        c["share_of_cost_change"] = metrics.div(c["cost_delta"], cost_delta)
        c["share_of_conversion_change"] = metrics.div(c["conversions_delta"], conv_delta)
        notable_cost = c["cost_change"] is not None and abs(c["cost_change"]) >= NOTABLE_CHANGE
        notable_conv = c["conversions_change"] is not None and abs(c["conversions_change"]) >= NOTABLE_CHANGE
        c["notable"] = notable_cost or notable_conv
        if c["notable"]:
            use_conv = notable_conv and (not notable_cost or abs(c["conversions_change"]) >= abs(c["cost_change"]))
            c["headline_metric"] = "conversions" if use_conv else "cost"
            c["main_lever"] = main_lever(c["conversion_levers"] if use_conv else c["cost_levers"])
            if c["main_lever"]:
                found = shift_day(by_campaign[c["scope"]], prev_start, cur_end, c["main_lever"])
                c["shift_day"] = found.isoformat() if found else None
    campaigns.sort(key=lambda c: -(abs(c["cost_delta"]) + abs(c["conversions_delta"]) * (account["previous"]["cpa"] or 0)))

    changes = []
    if args.changes:
        change_meta, change_rows = io.read_report(args.changes)
        io.require(change_meta, ["changed_at", "changes"], "change history export")
        for row in change_rows:
            day = dates.parse_day(row.get("changed_at"))
            if day:
                changes.append({"day": day, "campaign": row.get("campaign", ""), "user": row.get("user", ""), "changes": row.get("changes", "")})
    for c in campaigns:
        c["changes_before_shift"] = []
        if c.get("shift_day") and changes:
            shift = dates.parse_day(c["shift_day"])
            for change in changes:
                same = change["campaign"] in ("", c["scope"])
                if same and 0 <= (shift - change["day"]).days <= CHANGE_LOOKBACK_DAYS:
                    c["changes_before_shift"].append({"day": change["day"].isoformat(), "user": change["user"], "changes": change["changes"]})

    periods = {"current": [cur_start.isoformat(), cur_end.isoformat()], "previous": [prev_start.isoformat(), prev_end.isoformat()]}
    out = outputs.ensure_dir(args.out)
    outputs.write_json(os.path.join(out, "diagnosis.json"), {"report": os.path.basename(args.report), "title_rows": meta["title_rows"], "periods": periods,
                                                             "account": account, "campaigns": campaigns, "change_history_read": bool(args.changes)})

    def r2(v):
        return round(v, 2) if v is not None else None

    def row_for(item):
        cur, prev = item["current"], item["previous"]
        return [item["scope"], r2(prev["cost"]), r2(cur["cost"]), item["cost_change"], r2(prev["conversions"]), r2(cur["conversions"]), item["conversions_change"],
                r2(prev["cpa"]), r2(cur["cpa"]), item["cpa_change"], prev["ctr"], cur["ctr"], r2(prev["cpc"]), r2(cur["cpc"]), prev["cvr"], cur["cvr"]]

    header = ["Scope", "Cost before", "Cost now", "Cost change", "Conv. before", "Conv. now", "Conv. change", "Cost / conv. before", "Cost / conv. now",
              "Cost / conv. change", "CTR before", "CTR now", "Avg. CPC before", "Avg. CPC now", "Conv. rate before", "Conv. rate now"]
    formats = {1: "money", 2: "money", 3: "pct", 4: "money", 5: "money", 6: "pct", 7: "money", 8: "money", 9: "pct", 10: "pct", 11: "pct", 12: "money", 13: "money", 14: "pct", 15: "pct"}
    lever_rows = []
    for item in [account] + campaigns:
        for metric, levers in (("Conversions", item["conversion_levers"]), ("Cost", item["cost_levers"])):
            if levers:
                lever_rows.append([item["scope"], metric] + [levers.get(k) for k in ("impressions", "ctr", "cvr", "cpc")])
    all_days = sorted(d for d in account_days if prev_start <= d <= cur_end)
    names = [c["scope"] for c in campaigns]
    daily_rows = []
    for day in all_days:
        line = [day.isoformat(), "Now" if day >= cur_start else "Before"]
        for name in names:
            v = by_campaign[name].get(day, {})
            line += [r2(v.get("cost")), r2(v.get("conversions"))]
        daily_rows.append(line)
    daily_header = ["Day", "Period"] + [h for name in names for h in (name + " cost", name + " conv.")]

    book = xlsx.Workbook()
    book.add_sheet("Before and now", header, [row_for(account)] + [row_for(c) for c in campaigns], formats=formats, widths={0: 30})
    book.add_sheet("Which lever moved", ["Scope", "Change in", "How often ads showed", "Click through rate", "Conversion rate", "Cost per click"], lever_rows,
                   formats={2: "pct", 3: "pct", 4: "pct", 5: "pct"}, widths={0: 30})
    book.add_sheet("Shift and changes", ["Campaign", "What moved", "Main lever", "Shift starts", "Account changes in the 3 days before"],
                   [[c["scope"], c.get("headline_metric", ""), LEVER_NAMES.get(c.get("main_lever"), ""), c.get("shift_day") or "",
                     "; ".join("%s: %s" % (x["day"], x["changes"]) for x in c["changes_before_shift"])] for c in campaigns if c["notable"]],
                   widths={0: 30, 4: 90})
    book.add_sheet("Daily", daily_header, daily_rows, formats={i: "money" for i in range(2, len(daily_header))})
    book.save(os.path.join(out, "performance-diagnosis.xlsx"))

    def signed(value):
        return "n/a" if value is None else ("+" if value >= 0 else "") + metrics.pct(value)

    def lever_value(lever, values):
        if lever == "impressions":
            return "{:,.0f}".format(values["impressions"])
        if lever == "cpc":
            return metrics.money(values["cpc"])
        return metrics.pct(values.get(lever), 2)

    def around_shift(name, shift, key):
        """Average per day of one measure before the shift day and from it."""
        days = by_campaign[name]
        before = [days[d][key] for d in days if prev_start <= d < shift]
        after = [days[d][key] for d in days if shift <= d <= cur_end]
        return metrics.div(sum(before), len(before)), metrics.div(sum(after), len(after)), len(before), len(after)

    def ratio(value):
        return "n/a" if value is None else "{:,.2f}".format(value)

    currencies = sorted({(row.get("currency") or "").strip() for row in rows if (row.get("currency") or "").strip()})
    cur, prev = account["current"], account["previous"]
    has_value = bool(cur["conv_value"] or prev["conv_value"])
    account_rows = [
        ["Cost", metrics.money(prev["cost"]), metrics.money(cur["cost"]), signed(account["cost_change"])],
        ["Conversions", "{:,.2f}".format(prev["conversions"]), "{:,.2f}".format(cur["conversions"]), signed(account["conversions_change"])],
        ["Cost / conv.", metrics.money(prev["cpa"]), metrics.money(cur["cpa"]), signed(account["cpa_change"])],
        ["Conv. rate", metrics.pct(prev["cvr"], 2), metrics.pct(cur["cvr"], 2), signed(metrics.change(cur["cvr"], prev["cvr"]))],
        ["Avg. CPC", metrics.money(prev["cpc"]), metrics.money(cur["cpc"]), signed(metrics.change(cur["cpc"], prev["cpc"]))],
    ]
    if has_value:
        account_rows += [
            ["Conv. value", metrics.money(prev["conv_value"]), metrics.money(cur["conv_value"]), signed(metrics.change(cur["conv_value"], prev["conv_value"]))],
            ["Value / conv.", metrics.money(prev["value_per_conv"]), metrics.money(cur["value_per_conv"]),
             signed(metrics.change(cur["value_per_conv"], prev["value_per_conv"]))],
            ["Conv. value / cost", ratio(prev["roas"]), ratio(cur["roas"]), signed(metrics.change(cur["roas"], prev["roas"]))],
        ]
    campaign_header = ["Campaign", "Cost before", "Cost now", "Conv. before", "Conv. now", "Cost / conv. before", "Cost / conv. now",
                       "Avg. CPC before", "Avg. CPC now", "Conv. rate before", "Conv. rate now"]
    if has_value:
        campaign_header += ["Conv. value before", "Conv. value now"]
    campaign_rows = []
    for c in campaigns:
        p, n = c["previous"], c["current"]
        line = [c["scope"], metrics.money(p["cost"]), metrics.money(n["cost"]), "{:,.2f}".format(p["conversions"]), "{:,.2f}".format(n["conversions"]),
                metrics.money(p["cpa"]), metrics.money(n["cpa"]), metrics.money(p["cpc"]), metrics.money(n["cpc"]),
                metrics.pct(p["cvr"], 2), metrics.pct(n["cvr"], 2)]
        if has_value:
            line += [metrics.money(p["conv_value"]), metrics.money(n["conv_value"])]
        campaign_rows.append(line)
    lines = ["# Performance diagnosis", ""]
    lines += ["%s." % t for t in meta["title_rows"]]
    lines += ["", "Now: %s to %s. Before: %s to %s. Each period is %d days." % (
        cur_start.isoformat(), cur_end.isoformat(), prev_start.isoformat(), prev_end.isoformat(), (cur_end - cur_start).days + 1)]
    if len(currencies) == 1:
        lines.append("Amounts are in %s." % currencies[0])
    lines += ["",
              "## Account", "",
              outputs.md_table(["Measure", "Before", "Now", "Change"], account_rows),
              "", "## Campaigns, before and now", "",
              outputs.md_table(campaign_header, campaign_rows),
              "", "## Where the change is", ""]
    notable = [c for c in campaigns if c["notable"]]
    if not notable:
        lines.append("- No campaign moved 20% or more in cost or conversions between the two periods.")
    for c in notable:
        lever = LEVER_NAMES.get(c.get("main_lever"), "no single lever")
        if c["headline_metric"] == "conversions":
            amount = "%+.2f conversions, against %+.2f for the whole account" % (c["conversions_delta"], conv_delta)
        else:
            amount = "%+.2f in cost, against %+.2f for the whole account" % (c["cost_delta"], cost_delta)
        lines.append("- **%s:** cost %s, conversions %s. That is %s. The main lever is %s.%s" % (
            c["scope"], signed(c["cost_change"]), signed(c["conversions_change"]), amount, lever,
            " The shift starts around %s." % c["shift_day"] if c.get("shift_day") else ""))
        if c.get("main_lever"):
            lines.append("  - %s: %s before, %s now." % (lever.capitalize(), lever_value(c["main_lever"], c["previous"]), lever_value(c["main_lever"], c["current"])))
        p, n = c["previous"], c["current"]
        lines.append("  - Impr.: %s before, %s now (%s). Clicks: %s before, %s now (%s). CTR: %s before, %s now." % (
            "{:,.0f}".format(p["impressions"]), "{:,.0f}".format(n["impressions"]), signed(metrics.change(n["impressions"], p["impressions"])),
            "{:,.0f}".format(p["clicks"]), "{:,.0f}".format(n["clicks"]), signed(metrics.change(n["clicks"], p["clicks"])),
            metrics.pct(p["ctr"], 2), metrics.pct(n["ctr"], 2)))
        if has_value:
            lines.append("  - Conv. value: %s before, %s now (%s). Value / conv.: %s before, %s now." % (
                metrics.money(p["conv_value"]), metrics.money(n["conv_value"]), signed(metrics.change(n["conv_value"], p["conv_value"])),
                metrics.money(p["value_per_conv"]), metrics.money(n["value_per_conv"])))
        if c["scope"] in last_status:
            lines.append("  - Campaign status on %s: %s." % (last_status[c["scope"]][0].isoformat(), last_status[c["scope"]][1]))
        if c.get("shift_day"):
            before, after, n_before, n_after = around_shift(c["scope"], dates.parse_day(c["shift_day"]), c["headline_metric"])
            shown = metrics.money if c["headline_metric"] == "cost" else (lambda v: "n/a" if v is None else "{:,.2f}".format(v))
            lines.append("  - %s per day: %s on average in the %d days before the shift, %s in the %d days from it." % (
                c["headline_metric"].capitalize(), shown(before), n_before, shown(after), n_after))
        for change in c["changes_before_shift"]:
            lines.append("  - Changed on %s by %s: %s" % (change["day"], change["user"] or "unknown", change["changes"]))
        if c.get("shift_day") and args.changes and not c["changes_before_shift"]:
            lines.append("  - No account change is recorded in the %d days before the shift." % CHANGE_LOOKBACK_DAYS)
    steady = [c["scope"] for c in campaigns if not c["notable"]]
    if steady:
        lines += ["", "Steady, within 20%: " + ", ".join(steady) + "."]
    lines += ["", "## How the numbers were made", "",
              "- Conversions = how often ads showed x click through rate x conversion rate. Cost = how often ads showed x click through rate x cost per click. The main lever is the factor with the largest share of the change.",
              "- The shift day is the day that best splits that lever's daily values into a before and an after.",
              "- " + ("Change history was read, and changes in the %d days before each shift are listed." % CHANGE_LOOKBACK_DAYS if args.changes else "No change history export was provided, so account changes are not checked."),
              "- A change made just before a shift is a lead to check, not proof of the cause.",
              "- Recent days can still gain conversions as late conversions are reported.",
              "- A campaign is listed under \"Where the change is\" when its cost or conversions moved 20% or more. Impr., clicks and conv. value are shown for it but do not decide the listing.",
              "", "## What this did not cover", "",
              "- Ads and their approval status, search terms, keywords, auction insights and impression share. This report has none of them.",
              "- Settings and bid strategy status. The change history shows edits, not the current state.",
              "- The website, the tags and the conversion actions behind the Conversions column.", ""]
    text = "\n".join(lines)
    with open(os.path.join(out, "performance-diagnosis.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote the files to %s" % out)


if __name__ == "__main__":
    main()
