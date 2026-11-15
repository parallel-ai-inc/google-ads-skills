#!/usr/bin/env python3
"""Write synthetic Google Ads exports for the bidding and scaling skill.

The layout follows REAL-EXPORT-LAYOUTS.md: a title row, a quoted date range, the
header, the rows by day, then the total rows, each starting with its date. Planted
problems a practitioner would recognise:

- Plumbing | Emergency beats its Target CPA while limited by budget.
- Plumbing | Water Heaters beats its Target ROAS while losing impressions to rank.
- Drain Cleaning | Search is learning after a switch to Target CPA and a budget change.
- Sewer Line | Search misses its Target CPA by a wide margin.
- Gas Line | Demand Gen has spent for a month with no conversion.
- Plumbing | Holiday Promo is paused.

    python3 examples/make_samples_bidding-and-scaling.py
"""
import csv
import datetime as dt
import json
import os
import random

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "exports", "bidding-and-scaling")
FIRST, LAST = dt.date(2026, 9, 14), dt.date(2026, 11, 12)
HEADER = ["Day", "Campaign status", "Campaign", "Budget", "Budget name", "Budget type", "Currency code", "Status", "Status reasons",
          "Campaign type", "Bid strategy type", "Target CPA", "Target ROAS", "Cost", "Impr.", "Clicks", "CTR", "Avg. CPC",
          "Search impr. share", "Search lost top IS (rank)", "Search lost top IS (budget)", "Conv. rate", "Conversions", "Cost / conv.", "Conv. value"]
EMPTY = " --"

# name: type, campaign status, status, reasons, strategy, target CPA, target ROAS, first day, last day
CAMPAIGNS = {
    "Plumbing | Emergency": ("Search", "Enabled", "Eligible (Limited)", "Limited by budget", "Target CPA", 60.0, None, FIRST, LAST),
    "Plumbing | Water Heaters": ("Search", "Enabled", "Eligible", "", "Target ROAS", None, 4.0, FIRST, LAST),
    "Drain Cleaning | Search": ("Search", "Enabled", "Eligible (Learning)", "bidding strategy learning", "Target CPA", 50.0, None, FIRST, LAST),
    "Brand": ("Search", "Enabled", "Eligible", "", "Target impression share", None, None, FIRST, LAST),
    "Sewer Line | Search": ("Search", "Enabled", "Eligible", "", "Target CPA", 55.0, None, FIRST, LAST),
    "Gas Line | Demand Gen": ("Demand Gen", "Enabled", "Eligible", "", "Target CPA", 70.0, None, dt.date(2026, 10, 13), LAST),
    "Plumbing | Holiday Promo": ("Search", "Paused", "Paused", "", "Maximize Conversions", None, None, FIRST, dt.date(2026, 10, 5)),
}


def money(value):
    return "{:,.2f}".format(value)


def share(value):
    if value is None:
        return EMPTY
    return "< 10%" if value < 10 else "%.2f%%" % value


def day_numbers(name, day, rng):
    """cost, cpc, cost per conversion, value per conversion, impression share, lost rank, lost budget, budget."""
    noise = lambda spread: rng.uniform(1 - spread, 1 + spread)  # noqa: E731
    if name == "Plumbing | Emergency":
        return 240 * rng.uniform(0.93, 1.02), 7.8, 50 * noise(0.25), 290, 52 * noise(0.05), 14 * noise(0.2), 31 * noise(0.12), 240.0
    if name == "Plumbing | Water Heaters":
        return 118 * noise(0.12), 6.4, 56 * noise(0.3), 280, 41 * noise(0.06), 38 * noise(0.1), 5 * noise(0.5), 160.0
    if name == "Drain Cleaning | Search":
        after = day >= dt.date(2026, 11, 6)
        budget = 150.0 if day >= dt.date(2026, 11, 8) else 120.0
        return (110 if after else 104) * noise(0.1), 5.1, (70 if after else 58) * noise(0.3), 210, 47 * noise(0.06), 25 * noise(0.15), 12 * noise(0.3), budget
    if name == "Brand":
        return 28 * noise(0.15), 1.4, 7 * noise(0.25), 290, 92 * noise(0.02), 6 * noise(0.3), 2 * noise(0.5), 50.0
    if name == "Sewer Line | Search":
        return 112 * noise(0.12), 8.9, 84 * noise(0.3), 450, 38 * noise(0.07), 47 * noise(0.08), 4 * noise(0.5), 150.0
    if name == "Gas Line | Demand Gen":
        return 37 * noise(0.15), 0.9, None, 0, None, None, None, 40.0
    return 55 * noise(0.1), 4.2, 65 * noise(0.3), 220, 45 * noise(0.06), 20 * noise(0.1), 3 * noise(0.5), 60.0


def main():
    rng = random.Random(11)
    os.makedirs(OUT, exist_ok=True)
    rows, totals = [], {}
    day = FIRST
    while day <= LAST:
        for name, (ctype, status, serving, reasons, strategy, tcpa, troas, first, last) in CAMPAIGNS.items():
            if not first <= day <= last:
                continue
            cost, cpc, cpa, value_per, impr_share, lost_rank, lost_budget, budget = day_numbers(name, day, rng)
            clicks = max(int(round(cost / cpc)), 1)
            cost = round(clicks * cpc * rng.uniform(0.95, 1.05), 2)
            impressions = int(clicks / (0.006 if ctype == "Demand Gen" else rng.uniform(0.07, 0.11)))
            conversions = round(cost / cpa, 2) if cpa else 0.0
            value = round(conversions * value_per * rng.uniform(0.85, 1.15), 2)
            rows.append([day.isoformat(), status, name, money(budget), EMPTY, "Daily", "USD", serving, reasons or EMPTY, ctype, strategy,
                         money(tcpa) if tcpa else EMPTY, "%.2f%%" % (troas * 100) if troas else EMPTY, money(cost), "{:,}".format(impressions),
                         "{:,}".format(clicks), "%.2f%%" % (100.0 * clicks / impressions), money(cost / clicks),
                         share(impr_share) if impr_share else EMPTY, share(lost_rank), share(lost_budget),
                         "%.2f%%" % (100.0 * conversions / clicks), "%.2f" % conversions, money(cost / conversions) if conversions else "0.00", money(value)])
            for label in ("Total: Filtered campaigns", "Total: Account", "Total: %s" % ctype):
                slot = totals.setdefault((day, label), [0.0, 0, 0, 0.0, 0.0])
                for i, v in enumerate((cost, impressions, clicks, conversions, value)):
                    slot[i] += v
        day += dt.timedelta(days=1)

    total_rows = []
    for (day, label), (cost, impressions, clicks, conversions, value) in sorted(totals.items(), key=lambda kv: (kv[0][0], kv[0][1])):
        row = [""] * len(HEADER)
        row[0], row[1] = day.isoformat(), label
        row[6] = "USD"
        row[13], row[14], row[15] = money(cost), "{:,}".format(impressions), "{:,}".format(clicks)
        row[22], row[24] = "%.2f" % conversions, money(value)
        total_rows.append(row)

    with open(os.path.join(OUT, "campaigns-by-day.csv"), "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Campaign report"])
        writer.writerow(["%s %d, %d - %s %d, %d" % (FIRST.strftime("%B"), FIRST.day, FIRST.year, LAST.strftime("%B"), LAST.day, LAST.year)])
        writer.writerow(HEADER)
        writer.writerows(rows)
        writer.writerows(total_rows)

    changes = [
        ("Nov 13, 2026, 8:02:10 AM", "Plumbing | Emergency", "Ad schedule changed"),
        ("Nov 8, 2026, 10:21:40 AM", "Drain Cleaning | Search", "Budget changed from 120.00 to 150.00"),
        ("Nov 5, 2026, 3:12:09 PM", "Drain Cleaning | Search", "Bid strategy changed from Maximize conversions to Target CPA\nTarget CPA set to 50.00"),
        ("Oct 13, 2026, 11:00:41 AM", "Gas Line | Demand Gen", "Campaign created"),
        ("Oct 6, 2026, 4:30:00 PM", "Plumbing | Holiday Promo", "Status changed from Enabled to Paused"),
        ("Sep 30, 2026, 2:15:33 PM", "Plumbing | Water Heaters", "Target ROAS changed from 450% to 400%"),
        ("Sep 22, 2026, 9:40:12 AM", "Sewer Line | Search", "Keywords added: 6"),
    ]
    with open(os.path.join(OUT, "change-history.csv"), "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["Change history report"])
        writer.writerow(["September 14, 2026 - November 13, 2026"])
        writer.writerow(["Date & time", "User", "Campaign", "Ad group", "Changes"])
        for stamp, campaign, text in changes:
            writer.writerow([stamp, "sam@northside.example", campaign, EMPTY, text])

    plan = {"steps": [
        {"step": 1, "campaign": "Plumbing | Emergency", "change": "budget", "to": 280,
         "why": "Beats its Target CPA of 60.00 and is limited by budget. Since August 17, 2026 more budget buys conversions at about the target, which the business accepts."},
        {"step": 1, "campaign": "Plumbing | Water Heaters", "change": "target_roas", "to": 3.6,
         "why": "Beats its Target ROAS of 4.00 and loses impressions to rank, so a lower target lets it enter more auctions."},
        {"step": 1, "campaign": "Gas Line | Demand Gen", "change": "pause", "why": "No conversions since it was created."},
        {"step": 1, "campaign": "Sewer Line | Search", "change": "investigate",
         "why": "Misses its Target CPA of 55.00. Check search terms, the landing page and call tracking before changing the target."},
        {"step": 1, "campaign": "Drain Cleaning | Search", "change": "hold", "why": "Learning after a switch to Target CPA and a budget change three days later."},
        {"step": 2, "campaign": "Plumbing | Water Heaters", "change": "target_roas", "to": 3.3,
         "why": "A second step toward more volume, only if the first held its return."},
    ]}
    draft = {"steps": [
        {"step": 1, "campaign": "Plumbing | Emergancy", "change": "budget", "to": 300, "why": "Limited by budget."},
        {"step": 1, "campaign": "Drain Cleaning | Search", "change": "budget", "to": 200, "why": "Needs more budget."},
        {"step": 1, "campaign": "Gas Line | Demand Gen", "change": "target_cpa", "to": 91, "why": "Give it room to convert."},
        {"step": 1, "campaign": "Plumbing | Water Heaters", "change": "target_roas", "to": 3.6, "why": "Its return is about 12.34 times cost."},
        {"step": 1, "campaign": "Plumbing | Water Heaters", "change": "budget", "to": 200, "why": "More room."},
    ]}
    for name, data in (("example-plan.json", plan), ("example-plan-first-draft.json", draft)):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=1)
    print("Wrote samples to %s" % OUT)


if __name__ == "__main__":
    main()
