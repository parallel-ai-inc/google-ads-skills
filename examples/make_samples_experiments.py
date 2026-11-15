#!/usr/bin/env python3
"""Write the sample exports for the experiments skill.

SYNTHETIC DATA. The business, the campaigns, the cities and every number are
made up. The Google Ads files copy the layout of real downloads: a title row,
a quoted date range, the header, the rows, then "Total" rows. In a report
segmented by Day each total row starts with the date and carries "Total: ..."
in the second column. Empty cells are " --". The business file is a plain
export from a booking system: a header and rows.

Planted findings the skill must make:
1. Return on investment at a 40% margin: "Plumbing | Water Heaters" loses
   money (Conv. value / cost about 1.8, break even 2.5). "Plumbing |
   Emergency" is profitable on average, but its budget rose from 150.00 to
   320.00 on 2026-10-01 and its value grows with spend at an elasticity of
   0.35, so the next dollar does not pay. "Brand" has the highest return and
   is flagged as the least likely to be incremental. "Sewer Line | Search" is
   Paused.
2. Experiment readout: the trial arm (Target CPA) on "Plumbing | Emergency"
   has conversions about 17% higher, but the range includes zero. Conv.
   rate and Avg. CPC both rose, clearly. The first 7 days are the trial
   settling and are worse. The scorecard copies Google's figures for the
   same arms.
3. Geo test readout: ads went dark in Evanston, Skokie and Oak Park from
   2026-10-22 to the end of the files (2026-11-11). The business's leads
   there fell by about 22%, about half of what Google Ads attributed to
   those cities. Niles, a control city, had its own jump in leads during the
   test (a local event) and must be flagged. The files carry no note of the
   test cities or dates: the skill has to find them.

    python3 examples/make_samples_experiments.py
"""
import csv
import datetime as dt
import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports", "experiments")
WEEKDAY = [1.2, 1.1, 1.05, 1.0, 0.95, 0.75, 0.7]


def fmt(value, digits=2):
    return "{:,.{d}f}".format(value, d=digits)


def poisson(rng, rate):
    if rate > 30:
        return max(0, int(round(rng.gauss(rate, math.sqrt(rate)))))
    limit, k, p = math.exp(-rate), 0, 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def days(first, last):
    day = first
    while day <= last:
        yield day
        day += dt.timedelta(days=1)


def write(name, lines):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(lines)


def campaign_report(rng):
    first, last = dt.date(2026, 8, 15), dt.date(2026, 11, 12)
    raise_day = dt.date(2026, 10, 1)
    paused_day = dt.date(2026, 10, 1)
    # name: budget name, budget, type, value per conversion, conversions per unit of cost scale
    header = ["Day", "Campaign status", "Campaign", "Budget", "Budget name", "Budget type", "Currency code", "Status", "Campaign type",
              "Bid strategy type", "Cost", "Impr.", "Clicks", "Conversions", "Conv. value", "Search lost IS (budget)"]
    lines = [["Campaign report"], ["August 15, 2026 - November 12, 2026"], header]
    for day in days(first, last):
        wd = WEEKDAY[day.weekday()]
        totals = [0.0] * 5
        rows = []
        # Plumbing | Emergency: budget limited, value grows with spend at elasticity 0.35.
        budget = 320.0 if day >= raise_day else 150.0
        cost = budget * rng.uniform(0.82, 1.0)
        conv = poisson(rng, 3.4 * (cost / 150.0) ** 0.35 * wd)
        value = sum(rng.uniform(180, 240) for _ in range(conv))
        rows.append(["Enabled", "Plumbing | Emergency", budget, "Plumbing | Emergency", "Eligible", "Search", "Maximize conversions",
                     cost, conv, value, rng.uniform(0.25, 0.4) if budget < 200 else rng.uniform(0.0, 0.08)])
        # Plumbing | Water Heaters: loses money at a 40% margin.
        cost = 120.0 * rng.uniform(0.85, 1.0)
        conv = poisson(rng, 0.9 * wd)
        value = sum(rng.uniform(170, 210) for _ in range(conv))
        rows.append(["Enabled", "Plumbing | Water Heaters", 120.0, "Plumbing | Water Heaters", "Eligible", "Search", "Maximize conversions",
                     cost, conv, value, rng.uniform(0.05, 0.15)])
        # Drain Cleaning | Search: near break even on few conversions.
        cost = 70.0 * rng.uniform(0.8, 1.0)
        conv = poisson(rng, 0.45 * wd)
        value = sum(rng.uniform(380, 460) for _ in range(conv))
        rows.append(["Enabled", "Drain Cleaning | Search", 80.0, "Drain and Sewer", "Eligible", "Search", "Maximize conversions",
                     cost, conv, value, None])
        # Brand: cheap, high attributed return.
        cost = 25.0 * rng.uniform(0.85, 1.05)
        conv = poisson(rng, 3.0 * wd)
        value = sum(rng.uniform(260, 340) for _ in range(conv))
        rows.append(["Enabled", "Brand", 40.0, "Brand", "Eligible", "Search", "Maximize clicks", cost, conv, value, None])
        # Sewer Line | Search: paused on 2026-10-01, so it has no rows after.
        if day < paused_day:
            cost = 60.0 * rng.uniform(0.8, 1.0)
            conv = poisson(rng, 0.3 * wd)
            value = sum(rng.uniform(380, 420) for _ in range(conv))
            rows.append(["Paused", "Sewer Line | Search", 80.0, "Drain and Sewer", "Paused", "Search", "Maximize conversions",
                         cost, conv, value, None])
        for status, name, budget, budget_name, serving, kind, bidding, cost, conv, value, lost in rows:
            clicks = max(1, int(round(cost / rng.uniform(5.5, 8.5))))
            impr = int(round(clicks / rng.uniform(0.05, 0.09)))
            cost, value = round(cost, 2), round(value, 2)
            lines.append([day.isoformat(), status, name, fmt(budget), budget_name, "Daily", "USD", serving, kind, bidding, fmt(cost),
                          fmt(impr, 0), fmt(clicks, 0), fmt(conv), fmt(value) if value else "0.00",
                          " --" if lost is None else ("< 10%" if lost < 0.1 else "%.1f%%" % (lost * 100))])
            for i, v in enumerate((cost, impr, clicks, conv, value)):
                totals[i] += v
        for label in ("Total: Account", "Total: Search"):
            lines.append([day.isoformat(), label, "", "", "", "", "", "", "", "", fmt(totals[0]), fmt(totals[1], 0), fmt(totals[2], 0),
                          fmt(totals[3]), fmt(totals[4]), ""])
    write("campaigns-by-day.csv", lines)


def experiment(rng):
    start, settle_end, last = dt.date(2026, 9, 24), dt.date(2026, 9, 30), dt.date(2026, 11, 11)
    header = ["Day", "Experiment arm", "Campaign", "Currency code", "Impr.", "Clicks", "Cost", "Conversions", "Conv. value"]
    lines = [["Experiment report"], ["September 24, 2026 - November 11, 2026"], header]
    totals = {"Control": [0.0] * 5, "Treatment": [0.0] * 5}
    for day in days(start, last):
        wd = WEEKDAY[day.weekday()]
        demand = rng.uniform(0.85, 1.15)
        for arm, name in (("Control", "Plumbing | Emergency"), ("Treatment", "Plumbing | Emergency [trial]")):
            settling = day <= settle_end
            click_rate = 20.0 * (0.88 if arm == "Treatment" else 1.0)
            cvr = 0.12 * ((0.85 if settling else 1.39) if arm == "Treatment" else 1.0)
            clicks = poisson(rng, click_rate * demand * wd)
            conv = sum(1 for _ in range(clicks) if rng.random() < cvr)
            cpc = rng.uniform(7.2, 7.8) * (1.16 if arm == "Treatment" else 1.0)
            cost = round(clicks * cpc, 2)
            impr = int(round(clicks / rng.uniform(0.06, 0.08)))
            value = round(sum(rng.uniform(180, 240) for _ in range(conv)), 2)
            lines.append([day.isoformat(), arm, name, "USD", fmt(impr, 0), fmt(clicks, 0), fmt(cost), fmt(conv), fmt(value)])
            if not settling:
                for i, v in enumerate((impr, clicks, cost, conv, value)):
                    totals[arm][i] += v
    write("experiment-arms-by-day.csv", lines)
    c, t = totals["Control"], totals["Treatment"]
    score = [["Experiment scorecard"], ["October 1, 2026 - November 11, 2026"],
             ["Metric", "Control", "Treatment", "Difference", "Confidence interval", "Statistically significant"],
             ["Clicks", fmt(c[1], 0), fmt(t[1], 0), "-9.7%", "[-20.1%, +2.1%]", "Not statistically significant"],
             ["Conversions", fmt(c[3]), fmt(t[3]), "+17.0%", "[-9.5%, +51.3%]", "Not statistically significant"],
             ["Cost / conv.", fmt(c[2] / c[3]), fmt(t[2] / t[3]), "-11.4%", "[-29.1%, +10.7%]", "Not statistically significant"],
             ["Conv. rate", "%.2f%%" % (100 * c[3] / c[1]), "%.2f%%" % (100 * t[3] / t[1]), "+29.6%", "[+4.0%, +61.5%]", "Statistically significant"],
             ["Cost", fmt(c[2]), fmt(t[2]), "+3.7%", "[-8.5%, +17.5%]", "Not statistically significant"]]
    write("experiment-scorecard.csv", score)


def geo(rng):
    first, last = dt.date(2026, 8, 1), dt.date(2026, 11, 11)
    dark_from, dark_to = dt.date(2026, 10, 22), dt.date(2026, 11, 11)
    test = {"Evanston": 11.0, "Skokie": 10.0, "Oak Park": 9.0}
    control = {"Cicero": 9.0, "Berwyn": 8.0, "Des Plaines": 10.5, "Park Ridge": 8.0, "Niles": 9.0}
    business = [["Day", "City", "Leads", "Revenue"]]
    ads_header = ["Day", "City (User location)", "Currency code", "Impr.", "Clicks", "Cost", "Conversions"]
    ads = [["Locations report"], ["August 1, 2026 - November 11, 2026"], ads_header]
    for day in days(first, last):
        wd = WEEKDAY[day.weekday()]
        weather = rng.uniform(0.75, 1.3)
        dark = dark_from <= day <= dark_to
        totals = [0.0] * 4
        for city, rate in list(test.items()) + list(control.items()):
            in_test = city in test
            off = in_test and dark
            # Niles had a local flood during the test window: its leads rose on their own.
            event = 1.45 if city == "Niles" and dark else 1.0
            leads = poisson(rng, rate * wd * weather * event * (0.78 if off else 1.0))
            revenue = sum(rng.uniform(200, 300) for _ in range(leads))
            business.append([day.isoformat(), city, str(leads), fmt(revenue)])
            if off:
                continue
            cost = round(rate * 4.8 * rng.uniform(0.85, 1.05), 2)
            clicks = max(1, int(round(cost / rng.uniform(6, 8))))
            impr = int(round(clicks / rng.uniform(0.05, 0.08)))
            conv = poisson(rng, rate * 0.45 * wd * weather)
            ads.append([day.isoformat(), city, "USD", fmt(impr, 0), fmt(clicks, 0), fmt(cost), fmt(conv)])
            for i, v in enumerate((impr, clicks, cost, conv)):
                totals[i] += v
        ads.append([day.isoformat(), "Total: Account", "", fmt(totals[0], 0), fmt(totals[1], 0), fmt(totals[2]), fmt(totals[3])])
    write("leads-by-city-by-day.csv", business)
    write("cost-by-city-by-day.csv", ads)


def main():
    rng = random.Random(20261113)
    campaign_report(rng)
    experiment(rng)
    geo(rng)
    print("Wrote the samples to %s" % OUT)


if __name__ == "__main__":
    main()
