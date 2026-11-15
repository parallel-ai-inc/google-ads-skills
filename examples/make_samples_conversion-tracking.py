#!/usr/bin/env python3
"""Write the sample exports for the conversion tracking skill.

SYNTHETIC DATA. The business, the campaigns and every number are made up.
The files copy the layout of real Google Ads downloads: a title row, a quoted
date range, the header, the rows, then "Total" rows. In a report segmented by
Day each total row starts with the date and carries "Total: ..." in the
second column. Empty cells are " --".

Planted problems the skill must find:
1. "Online booking" (Website, Primary) stops on 2026-11-04 while clicks carry on.
2. "GA4 generate_lead" was switched from Secondary to Primary on 2026-10-27, so
   two Primary actions from different sources now count the same lead form.
3. "Website lead form" is a lead action counted as Every.

    python3 examples/make_samples_conversion-tracking.py
"""
import csv
import datetime as dt
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports", "conversion-tracking")
FIRST, LAST = dt.date(2026, 10, 14), dt.date(2026, 11, 12)
RANGE = "October 14, 2026 - November 12, 2026"
SWITCH, BREAK = dt.date(2026, 10, 27), dt.date(2026, 11, 4)
CAMPAIGNS = {"Plumbing | Emergency": 0.45, "Plumbing | Water Heaters": 0.25, "Drain Cleaning | Search": 0.18, "Brand": 0.12}
CLICKS = {"Plumbing | Emergency": (28, 8.9), "Plumbing | Water Heaters": (17, 6.8), "Drain Cleaning | Search": (18, 7.6), "Brand": (16, 1.5)}

# name: source, category, count, status, daily rate, value, Secondary until (None = always Primary, "always" = always Secondary)
ACTIONS = [
    ("Website lead form", "Website", "Submit lead form", "Every", "Recording conversions", 6.0, 150, None),
    ("GA4 generate_lead", "Google Analytics (GA4)", "Submit lead form", "One", "Recording conversions", 5.4, 150, SWITCH),
    ("Calls from ads", "Calls from ads", "Phone call lead", "One", "Recording conversions", 4.0, 100, None),
    ("Online booking", "Website", "Book appointment", "One", "No recent conversions", 3.0, 200, None),
    ("Directions clicks", "Website", "Get directions", "Every", "Recording conversions", 2.0, 0, "always"),
]


def fmt(value, digits=2):
    return "{:,.{d}f}".format(value, d=digits)


def poisson(rng, rate):
    limit, k, p = math.exp(-rate), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def write(name, lines):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(lines)


def main():
    rng = random.Random(20261113)
    days = [FIRST + dt.timedelta(days=i) for i in range((LAST - FIRST).days + 1)]
    data = []  # day, action, campaign, conversions, all conv., value
    for day in days:
        for name, source, category, count, status, rate, value, secondary_until in ACTIONS:
            for campaign, weight in CAMPAIGNS.items():
                if name == "Online booking" and day >= BREAK:
                    continue
                all_conv = poisson(rng, rate * weight)
                if not all_conv:
                    continue
                primary = secondary_until is None or (secondary_until != "always" and day >= secondary_until)
                data.append((day, name, campaign, all_conv if primary else 0, all_conv, value))

    # Conversions by action and day, built in the Report editor.
    header = ["Day", "Conversion action", "Campaign", "Campaign status", "Currency code", "Cost", "Conversions", "All conv.", "Conv. value", "All conv. value"]
    lines = [["Conversions by action and day"], [RANGE], header]
    for day, name, campaign, conv, all_conv, value in data:
        lines.append([day.isoformat(), name, campaign, "Enabled", "USD", " --", fmt(conv), fmt(all_conv), fmt(conv * value), fmt(all_conv * value)])
    for day in days:
        rows = [r for r in data if r[0] == day]
        sums = [sum(r[3] for r in rows), sum(r[4] for r in rows), sum(r[3] * r[5] for r in rows), sum(r[4] * r[5] for r in rows)]
        for label in ("Total: Search", "Total: Account"):
            lines.append([day.isoformat(), label, " --", " --", "USD", " --"] + [fmt(v) for v in sums])
    write("conversions-by-action-and-day.csv", lines)

    # The conversions summary: Goals, Conversions, Summary, Download.
    header = ["Conversion action", "Action optimization", "Conversion source", "Category", "Status", "Count", "Click-through conv. window",
              "View-through conv. window", "Attribution model", "Conversions", "Conv. value", "All conv.", "All conv. value"]
    lines = [["Conversion actions"], [RANGE], header]
    sums = [0.0, 0.0, 0.0, 0.0]
    for name, source, category, count, status, rate, value, secondary_until in ACTIONS:
        rows = [r for r in data if r[1] == name]
        conv, all_conv = sum(r[3] for r in rows), sum(r[4] for r in rows)
        optimization = "Secondary action" if secondary_until == "always" else "Primary action"
        sums = [sums[0] + conv, sums[1] + conv * value, sums[2] + all_conv, sums[3] + all_conv * value]
        lines.append([name, optimization, source, category, status, count, "30 days", "1 day" if source == "Website" else " --",
                      "Data-driven", fmt(conv), fmt(conv * value), fmt(all_conv), fmt(all_conv * value)])
    lines.append(["Old contact form", "Secondary action", "Website", "Contact", "Removed", "One", "30 days", "1 day", "Data-driven",
                  "0.00", "0.00", "0.00", "0.00"])
    lines.append(["Total: Conversion actions", " --", " --", " --", " --", " --", " --", " --", " --"] + [fmt(v) for v in sums])
    write("conversion-actions-summary.csv", lines)

    # Clicks: the campaign report by Day, without the conversion segment. Clicks carry on after the break.
    header = ["Day", "Campaign status", "Campaign", "Currency code", "Campaign type", "Cost", "Impr.", "Clicks", "Conversions"]
    lines = [["Campaign report"], [RANGE], header]
    totals = {}
    for day in days:
        for campaign, (clicks_rate, cpc) in CLICKS.items():
            clicks = max(1, int(round(rng.gauss(clicks_rate, clicks_rate * 0.15))))
            impressions = clicks * rng.randint(9, 14)
            conv = sum(r[3] for r in data if r[0] == day and r[2] == campaign)
            cost = clicks * cpc * rng.uniform(0.9, 1.1)
            lines.append([day.isoformat(), "Enabled", campaign, "USD", "Search", fmt(cost), fmt(impressions, 0), fmt(clicks, 0), fmt(conv)])
            slot = totals.setdefault(day, [0.0, 0, 0, 0.0])
            slot[0], slot[1], slot[2], slot[3] = slot[0] + float(fmt(cost).replace(",", "")), slot[1] + impressions, slot[2] + clicks, slot[3] + conv
    for day in days:
        cost, impressions, clicks, conv = totals[day]
        for label in ("Total: Search", "Total: Account"):
            lines.append([day.isoformat(), label, " --", "USD", " --", fmt(cost), fmt(impressions, 0), fmt(clicks, 0), fmt(conv)])
    write("campaigns-by-day.csv", lines)

    # Change history. The switch to Primary is recorded; the website change behind the break is not.
    lines = [["Change history report"], [RANGE], ["Date & time", "User", "Campaign", "Ad group", "Changes"],
             ["Nov 9, 2026, 2:15:40 PM", "manager@example.com", "Brand", "", "Ad schedule changed"],
             ["Oct 30, 2026, 9:02:44 AM", "manager@example.com", "Drain Cleaning | Search", "Drains", "Keyword added: [drain cleaning near me]"],
             ["Oct 27, 2026, 10:12:03 AM", "manager@example.com", "", "", "Conversion action GA4 generate_lead changed\nAction optimization changed from Secondary action to Primary action"],
             ["Oct 20, 2026, 3:40:11 PM", "manager@example.com", "Plumbing | Emergency", "", "Budget changed from 220.00 to 240.00"]]
    write("change-history.csv", lines)
    print("Wrote the sample exports to %s" % OUT)


if __name__ == "__main__":
    main()
