#!/usr/bin/env python3
"""Write the sample exports for the performance reviews skill.

SYNTHETIC DATA. The business, the campaigns and every number are made up.
The files copy the layout of real Google Ads downloads: a title row, a quoted
date range row, the header, the rows, then "Total" rows, with " --" for empty
cells and thousands separators. The keyword report and the campaign report by
Day follow layouts seen in real downloads. The other reports have not been
downloaded from a real account yet and use the column names Google documents.

Planted problems the reviews must find:
1. Weekly: Plumbing | Emergency halved its conversion rate in the last 7 days,
   so the account's cost per conversion jumped. Drain Cleaning | Old was
   paused and must be named as paused, not as a loss.
2. Keywords: "plumbing jobs" (job seekers) spent 640.00 with no conversions.
   "tankless water heater" costs far more per conversion than the account.
3. Quality Score: every Water Heaters keyword has Landing page exp. rated
   Below average.
4. Ads: in Plumbing | Emergency > Emergency, the second ad trails its sibling.
5. Devices: tablets, and computers in Plumbing | Emergency, cost more than they return.
6. Landing pages: the water heater page (with and without tracking
   parameters) converts poorly, and the hydro jetting page brought nothing.
7. Audiences: Home Improvement, an observation audience, costs far more than the rest.
8. Locations: Gary, Indiana is outside the service area and spent with no conversions.
9. Ad schedule: Sundays convert at a third of the usual rate.
   Bid strategies differ by campaign, so the same device finding has different levers.
10. Placements: a mobile game spent with no conversions.
11. Video: "Meet Our Plumbers (60s)" has a low view rate and loses most viewers between 25% and 50%.

    python3 examples/make_samples_performance-reviews.py
"""
import csv
import datetime
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports", "performance-reviews")
PERIOD = "October 14, 2026 - November 12, 2026"
DASH = " --"
EMERGENCY, HEATERS, DRAINS, BRAND, OLD = "Plumbing | Emergency", "Plumbing | Water Heaters", "Drain Cleaning | Search", "Brand", "Drain Cleaning | Old"
SITE = "https://www.northsideplumbing.com"
STRATEGY = {EMERGENCY: "Manual CPC", HEATERS: "Maximize Conversions", DRAINS: "Target CPA", BRAND: "Manual CPC", OLD: "Manual CPC"}


def whole(n):
    return "{:,}".format(int(round(n)))


def money(x):
    return "{:,.2f}".format(x)


def pct(x):
    return "%.2f%%" % (x * 100)


def metric(clicks, impr, cost, conv, clicks_name="Clicks"):
    return {"Impr.": whole(impr), clicks_name: whole(clicks), "CTR": pct(clicks / impr) if impr else DASH,
            "Avg. CPC": money(cost / clicks) if clicks else DASH, "Avg. cost": money(cost / clicks) if clicks else DASH,
            "Interaction rate": pct(clicks / impr) if impr else DASH, "Cost": money(cost), "Conversions": money(conv),
            "Conv. rate": pct(conv / clicks) if clicks else DASH, "Cost / conv.": money(cost / conv) if conv else DASH,
            "Currency code": "USD"}


def write(name, title, header, records, totals, period=PERIOD):
    """records: dicts keyed by header. totals: (cells before, label, sums) where sums holds raw numbers."""
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", newline="", encoding="utf-8") as handle:
        out = csv.writer(handle)
        out.writerow([title])
        out.writerow([period])
        out.writerow(header)
        for record in records:
            out.writerow([record.get(h, DASH) for h in header])
        for lead, label, sums in totals:
            cells = metric(sums["clicks"], sums["impr"], sums["cost"], sums["conv"], sums.get("clicks_name", "Clicks"))
            row = []
            for index, h in enumerate(header):
                if index < len(lead):
                    row.append(lead[index])
                elif index == len(lead):
                    row.append(label)
                elif h in ("Impr.", "Clicks", "Interactions", "Cost", "Conversions", "CTR", "Avg. CPC", "Avg. cost", "Conv. rate", "Cost / conv.", "Interaction rate"):
                    row.append(cells[h])
                else:
                    row.append("")
            out.writerow(row)


def sums(rows, clicks_name="Clicks"):
    return {"clicks": sum(r[0] for r in rows), "impr": sum(r[1] for r in rows), "cost": round(sum(r[2] for r in rows), 2),
            "conv": round(sum(r[3] for r in rows), 2), "clicks_name": clicks_name}


def weekly():
    """Campaign report segmented by Day, 28 days."""
    rng = random.Random(7)
    start, days = datetime.date(2026, 10, 16), 28
    drop_from = datetime.date(2026, 11, 6)
    # campaign: status, clicks a day, cost per click, conversion rate, last day it ran
    plan = {EMERGENCY: ("Enabled", 30, 8.00, 0.10), HEATERS: ("Enabled", 18, 8.50, 0.08), DRAINS: ("Enabled", 16, 6.30, 0.10),
            BRAND: ("Enabled", 6, 1.45, 0.22), OLD: ("Paused", 4, 7.00, 0.0)}
    header = ["Day", "Campaign status", "Campaign", "Budget", "Currency code", "Status", "Campaign type", "Bid strategy type", "Cost", "Impr.", "Clicks",
              "CTR", "Avg. CPC", "Conv. rate", "Conversions", "Cost / conv."]
    records, totals = [], []
    for i in range(days):
        day = start + datetime.timedelta(days=i)
        today = []
        for camp, (status, clicks, cpc, cvr) in plan.items():
            if camp == OLD and day > datetime.date(2026, 11, 2):
                continue
            if camp == EMERGENCY and day >= drop_from:
                cvr = 0.05
            n = max(1, int(round(clicks * rng.uniform(0.9, 1.1))))
            cost = round(n * cpc * rng.uniform(0.95, 1.05), 2)
            conv = round(n * cvr * rng.uniform(0.85, 1.15), 2)
            impr = int(round(n / 0.07))
            record = metric(n, impr, cost, conv)
            record.update({"Day": day.isoformat(), "Campaign status": status, "Campaign": camp, "Budget": money(clicks * cpc * 1.2),
                           "Status": "Paused" if status == "Paused" else "Eligible", "Campaign type": "Search",
                           "Bid strategy type": STRATEGY[camp]})
            records.append(record)
            today.append((n, impr, cost, conv))
        for label in ("Total: Account", "Total: Search"):
            totals.append(([day.isoformat()], label, sums(today)))
    write("campaign-report-by-day.csv", "Campaign report", header, records, totals,
          period="October 16, 2026 - November 12, 2026")


KEYWORDS = [
    # campaign, ad group, keyword, match, status, impr, clicks, cost, conv, QS, exp CTR, ad relevance, landing page exp.
    (EMERGENCY, "Emergency", "[24 hour plumber]", "Exact match", "Enabled", 1650, 160, 1280.00, 26, "8", "Above average", "Above average", "Average"),
    (EMERGENCY, "Emergency", '"emergency plumber"', "Phrase match", "Enabled", 5200, 420, 3402.00, 38, "7", "Average", "Above average", "Average"),
    (EMERGENCY, "Emergency", "emergency plumbing service", "Broad match", "Enabled", 3900, 210, 1850.00, 12, "6", "Average", "Average", "Average"),
    (EMERGENCY, "Emergency", "plumbing jobs", "Broad match", "Enabled", 2800, 95, 640.00, 0, "3", "Below average", "Below average", "Average"),
    (EMERGENCY, "Burst Pipes", '"burst pipe repair"', "Phrase match", "Enabled", 1500, 140, 1150.00, 13, "7", "Average", "Above average", "Average"),
    (EMERGENCY, "Burst Pipes", "frozen pipe repair", "Broad match", "Enabled", 300, 10, 85.00, 0, DASH, DASH, DASH, DASH),
    (EMERGENCY, "Burst Pipes", "[burst pipe plumber]", "Exact match", "Paused", 400, 28, 210.00, 0, "5", "Average", "Average", "Average"),
    (HEATERS, "Repair", '"water heater repair"', "Phrase match", "Enabled", 2600, 236, 1671.40, 17, "4", "Average", "Above average", "Below average"),
    (HEATERS, "Repair", "[water heater replacement]", "Exact match", "Enabled", 900, 80, 690.00, 8, "5", "Average", "Above average", "Below average"),
    (HEATERS, "Install", '"water heater installation"', "Phrase match", "Enabled", 2100, 172, 1404.80, 11, "4", "Average", "Average", "Below average"),
    (HEATERS, "Install", "tankless water heater", "Broad match", "Enabled", 1900, 120, 1020.00, 4, "3", "Below average", "Average", "Below average"),
    (DRAINS, "Drains", '"drain cleaning"', "Phrase match", "Enabled", 3100, 300, 1890.00, 30, "7", "Above average", "Above average", "Average"),
    (DRAINS, "Drains", "[clogged drain]", "Exact match", "Enabled", 1000, 110, 640.00, 9, "7", "Average", "Above average", "Average"),
    (DRAINS, "Drains", "diy drain unclog", "Broad match", "Enabled", 1400, 70, 230.00, 0, "4", "Below average", "Average", "Average"),
    (DRAINS, "Hydro Jetting", "hydro jetting", "Broad match", "Enabled", 700, 60, 480.00, 2, "5", "Average", "Average", "Average"),
    (BRAND, "Brand", "[northside plumbing]", "Exact match", "Enabled", 900, 180, 260.00, 40, "10", "Above average", "Above average", "Above average"),
]


def keywords():
    header = ["Keyword status", "Keyword", "Match type", "Campaign", "Ad group", "Status", "Status reasons", "Final URL", "Currency code",
              "Avg. CPM", "Impr.", "Interactions", "Interaction rate", "Avg. cost", "Cost", "Conv. rate", "Conversions", "Cost / conv.",
              "Quality Score", "Exp. CTR", "Ad relevance", "Landing page exp."]
    pages = {EMERGENCY: "/emergency/", HEATERS: "/water-heaters/", DRAINS: "/drain-cleaning/", BRAND: "/"}
    records, rows = [], []
    for camp, group, text, match, status, impr, clicks, cost, conv, qs, ctr, rel, lp in KEYWORDS:
        record = metric(clicks, impr, cost, conv, "Interactions")
        record.update({"Keyword status": status, "Keyword": text, "Match type": match, "Campaign": camp, "Ad group": group,
                       "Status": "Paused" if status == "Paused" else "Eligible", "Status reasons": DASH, "Final URL": SITE + pages[camp],
                       "Avg. CPM": money(cost / impr * 1000), "Quality Score": qs, "Exp. CTR": ctr, "Ad relevance": rel,
                       "Landing page exp.": lp})
        records.append(record)
        rows.append((clicks, impr, cost, conv))
    every = sums(rows, "Interactions")
    account = dict(every, cost=round(every["cost"] + 512.30, 2))
    totals = [([], "Total: Keywords in your account", every), ([], "Total: All but removed keywords", every),
              ([], "Total: Account", account), ([], "Total: Search", every)]
    write("keyword-report.csv", "Search keyword report", header, records, totals)


ADS = [
    # status, ad, campaign, ad group, serving status, ad strength, impr, clicks, cost, conv
    ("Enabled", "24/7 Emergency Plumber | Here in 60 Minutes | Licensed and Insured", EMERGENCY, "Emergency", "Eligible", "Excellent", 9000, 640, 5300.00, 66),
    ("Enabled", "Emergency Plumbing Service | Fair Upfront Prices | Call Now", EMERGENCY, "Emergency", "Eligible", "Average", 6000, 300, 2500.00, 12),
    ("Enabled", "Burst Pipe Repair | Same Day Service", EMERGENCY, "Burst Pipes", "Eligible", "Good", 1100, 80, 650.00, 7),
    ("Enabled", "Frozen Pipes? We Fix Them Fast", EMERGENCY, "Burst Pipes", "Eligible", "Good", 1000, 72, 585.00, 6),
    ("Enabled", "Water Heater Repair Today | Upfront Pricing", HEATERS, "Repair", "Eligible", "Good", 2000, 170, 1300.00, 14),
    ("Enabled", "No Hot Water? | Repairs in Hours", HEATERS, "Repair", "Eligible", "Poor", 1500, 146, 1061.40, 11),
    ("Enabled", "Water Heater Installation | Tank and Tankless", HEATERS, "Install", "Eligible", "Average", 4000, 292, 2424.80, 15),
    ("Enabled", "Drain Cleaning Experts | Clogs Cleared Today", DRAINS, "Drains", "Eligible", "Excellent", 4000, 380, 2300.00, 34),
    ("Enabled", "Clogged Drain? | Fast Local Plumbers", DRAINS, "Drains", "Eligible", "Good", 300, 25, 160.00, 0),
    ("Enabled", "Hydro Jetting Specialists", DRAINS, "Hydro Jetting", "Disapproved", "Good", 400, 30, 357.00, 1),
    ("Paused", "Sewer Line Jetting | Book Online", DRAINS, "Hydro Jetting", "Paused", "Average", 200, 12, 123.00, 0),
    ("Enabled", "Northside Plumbing | Official Site", BRAND, "Brand", "Eligible", "Excellent", 900, 180, 260.00, 40),
]


def ads():
    header = ["Ad status", "Ad", "Campaign", "Ad group", "Status", "Ad type", "Ad strength", "Currency code", "Impr.", "Clicks", "CTR",
              "Cost", "Conversions", "Cost / conv."]
    records, rows = [], []
    for status, text, camp, group, serving, strength, impr, clicks, cost, conv in ADS:
        record = metric(clicks, impr, cost, conv)
        record.update({"Ad status": status, "Ad": text, "Campaign": camp, "Ad group": group, "Status": serving,
                       "Ad type": "Responsive search ad", "Ad strength": strength})
        records.append(record)
        rows.append((clicks, impr, cost, conv))
    write("ads-report.csv", "Ad report", header, records, [([], "Total: Account", sums(rows))])


DEVICES = {
    # campaign: status, {device: (clicks, cost, conversions)}
    EMERGENCY: ("Enabled", {"Mobile phones": (700, 5600.00, 70), "Computers": (250, 2250.00, 10), "Tablets": (30, 250.00, 2)}),
    HEATERS: ("Enabled", {"Mobile phones": (300, 2500.00, 22), "Computers": (280, 2350.00, 24), "Tablets": (40, 350.00, 0)}),
    DRAINS: ("Enabled", {"Mobile phones": (380, 2500.00, 34), "Computers": (150, 1000.00, 12), "Tablets": (20, 130.00, 1)}),
    BRAND: ("Enabled", {"Mobile phones": (130, 180.00, 30), "Computers": (45, 70.00, 9), "Tablets": (5, 10.00, 1)}),
    OLD: ("Paused", {"Mobile phones": (60, 420.00, 0), "Computers": (20, 150.00, 0)}),
}


def devices():
    header = ["Device", "Campaign status", "Campaign", "Currency code", "Status", "Bid strategy type", "Impr.", "Clicks", "CTR", "Avg. CPC", "Cost",
              "Conversions", "Conv. rate", "Cost / conv."]
    records, rows = [], []
    for camp, (status, split) in DEVICES.items():
        for device, (clicks, cost, conv) in split.items():
            impr = int(round(clicks / 0.075))
            record = metric(clicks, impr, cost, conv)
            record.update({"Device": device, "Campaign status": status, "Campaign": camp, "Status": "Paused" if status == "Paused" else "Eligible",
                           "Bid strategy type": STRATEGY[camp]})
            records.append(record)
            rows.append((clicks, impr, cost, conv))
    write("campaign-report-by-device.csv", "Campaign report", header, records, [([], "Total: Account", sums(rows))])


def landing_pages():
    header = ["Landing page", "Clicks", "Impr.", "CTR", "Cost", "Conversions", "Conv. rate", "Cost / conv.", "Mobile speed score",
              "Mobile-friendly click rate"]
    pages = [(SITE + "/emergency/", 1000, 11000, 7880.00, 88, "7", "100.00%"),
             (SITE + "/water-heaters/", 520, 6000, 4200.00, 25, "3", "94.00%"),
             (SITE + "/water-heaters/?utm_source=google&utm_medium=cpc", 88, 1500, 586.20, 4, "3", "94.00%"),
             (SITE + "/drain-cleaning/", 410, 4100, 2530.00, 39, "8", "100.00%"),
             (SITE + "/hydro-jetting/", 60, 700, 520.00, 0, "6", "100.00%"),
             (SITE + "/", 180, 900, 260.00, 40, "8", "100.00%")]
    records, rows = [], []
    for url, clicks, impr, cost, conv, speed, friendly in pages:
        record = metric(clicks, impr, cost, conv)
        record.update({"Landing page": url, "Mobile speed score": speed, "Mobile-friendly click rate": friendly})
        records.append(record)
        rows.append((clicks, impr, cost, conv))
    write("landing-page-report.csv", "Landing page report", header, records, [([], "Total: Account", sums(rows))])


def audiences():
    header = ["Audience segment", "Type", "Campaign", "Ad group", "Targeting setting", "Impr.", "Clicks", "Cost", "Conversions", "Cost / conv."]
    data = [("Homeowners", "Detailed demographics", EMERGENCY, "Emergency", 3000, 260, 2100.00, 26),
            ("Homeowners", "Detailed demographics", HEATERS, "Repair", 1200, 110, 900.00, 9),
            ("Home Improvement", "Affinity", EMERGENCY, "Emergency", 2400, 180, 1500.00, 3),
            ("Home Improvement", "Affinity", HEATERS, "Install", 1300, 90, 760.00, 0),
            ("Plumbing Services", "In-market", EMERGENCY, "Emergency", 1800, 170, 1300.00, 21),
            ("Website visitors", "Your data", DRAINS, "Drains", 600, 70, 380.00, 9)]
    records, rows = [], []
    for name, kind, camp, group, impr, clicks, cost, conv in data:
        record = metric(clicks, impr, cost, conv)
        record.update({"Audience segment": name, "Type": kind, "Campaign": camp, "Ad group": group, "Targeting setting": "Observation"})
        records.append(record)
        rows.append((clicks, impr, cost, conv))
    write("audience-report.csv", "Audience segment report", header, records, [([], "Total: Account", sums(rows))])


def locations():
    header = ["Location", "Campaign", "Impr.", "Clicks", "Cost", "Conversions", "Cost / conv."]
    data = [("Evanston, Illinois, United States", EMERGENCY, 2400.00, 30), ("Evanston, Illinois, United States", DRAINS, 900.00, 12),
            ("Skokie, Illinois, United States", EMERGENCY, 1800.00, 20), ("Skokie, Illinois, United States", HEATERS, 1500.00, 14),
            ("Chicago, Illinois, United States", EMERGENCY, 3000.00, 34), ("Chicago, Illinois, United States", HEATERS, 2600.00, 22),
            ("Chicago, Illinois, United States", DRAINS, 1400.00, 18),
            ("Gary, Indiana, United States", EMERGENCY, 620.00, 0), ("Gary, Indiana, United States", HEATERS, 380.00, 0),
            ("Wilmette, Illinois, United States", DRAINS, 200.00, 1),
            ("Evanston, Illinois, United States", BRAND, 150.00, 25)]
    records, rows = [], []
    for place, camp, cost, conv in data:
        clicks = int(round(cost / 8.0))
        impr = int(round(clicks / 0.08))
        record = metric(clicks, impr, cost, conv)
        record.update({"Location": place, "Campaign": camp})
        records.append(record)
        rows.append((clicks, impr, cost, conv))
    write("location-report.csv", "Location report", header, records, [([], "Total: Account", sums(rows))])


def schedule():
    """Campaign report segmented by Day of the week and Hour of day, with the noise real hours have."""
    rng = random.Random(11)
    header = ["Day of the week", "Hour of day", "Campaign", "Campaign status", "Impr.", "Clicks", "Cost", "Conversions"]
    plan = {EMERGENCY: (1000, 8.00, 0.09), HEATERS: (620, 8.50, 0.08), DRAINS: (560, 6.30, 0.10), BRAND: (180, 1.45, 0.22)}
    day_weight = {"Monday": 1.08, "Tuesday": 1.02, "Wednesday": 0.97, "Thursday": 1.0, "Friday": 0.9, "Saturday": 0.72, "Sunday": 0.62}
    hour_weight = [0.12, 0.08, 0.06, 0.06, 0.1, 0.2, 0.45, 0.8, 1.05, 1.15, 1.1, 1.05, 1.0, 1.0, 1.05, 1.0, 0.95, 0.9, 0.8, 0.7,
                   0.6, 0.45, 0.3, 0.2]
    records, rows = [], []
    for camp, (month_clicks, cpc, cvr) in plan.items():
        weights = {(d, h): day_weight[d] * hour_weight[h] for d in day_weight for h in range(24)}
        scale = month_clicks / sum(weights.values())
        for (day, hour), weight in weights.items():
            clicks = int(round(weight * scale * rng.uniform(0.75, 1.25)))
            if clicks <= 0:
                continue
            rate = (cvr / 3 if day == "Sunday" else cvr) * rng.uniform(0.7, 1.3)
            cost = round(clicks * cpc * rng.uniform(0.9, 1.1), 2)
            conv = round(clicks * rate, 2)
            impr = int(round(clicks / rng.uniform(0.06, 0.08)))
            record = metric(clicks, impr, cost, conv)
            record.update({"Day of the week": day, "Hour of day": str(hour), "Campaign": camp, "Campaign status": "Enabled"})
            records.append(record)
            rows.append((clicks, impr, cost, conv))
    write("ad-schedule-report.csv", "Campaign report", header, records, [([], "Total: Account", sums(rows))])


def placements():
    header = ["Placement", "Placement URL", "Type", "Campaign", "Impr.", "Clicks", "Cost", "Conversions", "Cost / conv."]
    camp = "Remarketing | Display"
    data = [("Bubble Shooter Classic", "mobileapp::2-com.example.bubbleshooter", "Mobile application", 48000, 400, 380.00, 0),
            ("Home Repair Weekly", "homerepairweekly.example", "Website", 12000, 150, 300.00, 9),
            ("Neighborhood News Today", "neighborhoodnews.example", "Website", 9000, 60, 140.00, 2),
            ("DIY Plumbing Fixes", "youtube.com/channel/UCexample1", "YouTube channel", 15000, 40, 120.00, 0),
            ("Late Night Crime Stories", "latenightcrime.example", "Website", 7500, 30, 70.00, 0),
            ("Weather Radar Live", "mobileapp::1-100000001", "Mobile application", 20000, 120, 160.00, 1)]
    for i in range(1, 7):
        data.append(("Local Site %d" % i, "localsite%d.example" % i, "Website", 300 + 120 * i, i % 4 + 1, 2.0 + i * 1.25, 0))
    records, rows = [], []
    for name, url, kind, impr, clicks, cost, conv in data:
        record = metric(clicks, impr, cost, conv)
        record.update({"Placement": name, "Placement URL": url, "Type": kind, "Campaign": camp})
        records.append(record)
        rows.append((clicks, impr, cost, conv))
    write("placement-report.csv", "Placement report", header, records, [([], "Total: Account", sums(rows))])


def videos():
    header = ["Campaign", "Ad group", "Video", "Impr.", "Views", "View rate", "Avg. CPV", "Cost", "Clicks", "Conversions",
              "Video played to 25%", "Video played to 50%", "Video played to 75%", "Video played to 100%"]
    camp = "YouTube | Local Awareness"
    data = [("24/7 Emergency Plumber (30s)", 60000, 18000, 900.00, 240, 6, (78, 55, 41, 30)),
            ("Water Heater Warning Signs (15s)", 40000, 13200, 594.00, 150, 4, (85, 66, 52, 44)),
            ("Meet Our Plumbers (60s)", 35000, 5250, 420.00, 50, 0, (70, 31, 22, 15))]
    records, rows = [], []
    for video, impr, views, cost, clicks, conv, quarters in data:
        record = metric(clicks, impr, cost, conv)
        record.update({"Campaign": camp, "Ad group": "Local Homeowners", "Video": video, "Views": whole(views),
                       "View rate": pct(views / impr), "Avg. CPV": money(cost / views)})
        for q, value in zip((25, 50, 75, 100), quarters):
            record["Video played to %d%%" % q] = "%.2f%%" % value
        records.append(record)
        rows.append((clicks, impr, cost, conv))
    write("video-report.csv", "Video report", header, records, [([], "Total: Account", sums(rows))])


def main():
    weekly()
    keywords()
    ads()
    devices()
    landing_pages()
    audiences()
    locations()
    schedule()
    placements()
    videos()
    print("Sample exports written to %s" % OUT)


if __name__ == "__main__":
    main()
