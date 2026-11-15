#!/usr/bin/env python3
"""Write the sample exports for the client reporting skill.

SYNTHETIC DATA. The business, the campaigns and every number are made up.
The campaign report copies the layout of a real Google Ads download segmented
by Day: a title row, a date range row, the header, the rows, then one set of
"Total" rows per day with the date first and the label in the second column.

Planted for the skill to find in the October 2026 monthly review:
1. Drain Cleaning | Search was paused on October 20. Its cost fell because it
   stopped, not because it declined.
2. Brand flatters the account. The account's cost per conversion is under the
   40.00 target only because of Brand. Without Brand it is well above.
3. Plumbing | Water Heaters lost conversions after its bid strategy moved to
   Target CPA on October 6, the biggest mover of the month.
The draft report written by "someone else" carries four planted errors: a
direction that contradicts the data, a change against last year presented as
month over month, and two numbers that appear nowhere in the data.

    python3 examples/make_samples_client-reporting.py
"""
import csv
import datetime as dt
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports", "client-reporting")
START, END = dt.date(2025, 7, 1), dt.date(2026, 11, 12)
EMERGENCY, HEATERS, DRAINS, BRAND = "Plumbing | Emergency", "Plumbing | Water Heaters", "Drain Cleaning | Search", "Brand"
# name: (status, budget, bid strategy, impressions a day, CTR, CPC, conversion rate, value per conversion)
CAMPAIGNS = {
    EMERGENCY: ("Enabled", 240.0, "Maximize Conversions", 420, 0.068, 8.90, 0.21, 300.0),
    HEATERS: ("Enabled", 160.0, "Target CPA", 300, 0.060, 6.80, 0.13, 520.0),
    DRAINS: ("Paused", 120.0, "Maximize Conversions", 330, 0.055, 7.40, 0.08, 210.0),
    BRAND: ("Enabled", 40.0, "Target impression share", 45, 0.300, 1.45, 0.33, 300.0),
}


def long_date(day):
    return "%s %d, %d" % (day.strftime("%B"), day.day, day.year)


def fmt(value, digits=2):
    return "{:,.{d}f}".format(value, d=digits)


def day_values(rng, name, day):
    status, budget, strategy, impr, ctr, cpc, cvr, per_conv = CAMPAIGNS[name]
    if name == DRAINS and day >= dt.date(2026, 10, 20):
        return None
    scale = 0.85 if day < dt.date(2026, 1, 1) else 1.0
    if day.weekday() >= 5:
        scale *= 0.8
    if name == EMERGENCY and day >= dt.date(2026, 10, 1):
        scale *= 1.12
    if name == HEATERS and day >= dt.date(2026, 10, 6):
        scale *= 0.85
        cvr = 0.085
    impressions = max(1, int(round(impr * scale * rng.uniform(0.9, 1.1))))
    clicks = max(0, int(round(impressions * ctr * rng.uniform(0.9, 1.1))))
    cost = round(clicks * cpc * rng.uniform(0.92, 1.08), 2)
    conversions = round(clicks * cvr * rng.uniform(0.75, 1.25), 2)
    value = round(conversions * per_conv * rng.uniform(0.9, 1.1), 2)
    return impressions, clicks, cost, conversions, value


def campaign_report(rng):
    header = ["Day", "Campaign status", "Campaign", "Budget", "Budget type", "Currency code", "Status", "Campaign type", "Bid strategy type",
              "Cost", "Impr.", "Clicks", "CTR", "Avg. CPC", "Conv. rate", "Conversions", "Cost / conv.", "Conv. value"]
    lines = [["Campaign report"], ["%s - %s" % (long_date(START), long_date(END))], header]
    totals = []
    day = START
    while day <= END:
        sums = [0, 0, 0.0, 0.0, 0.0]
        for name in CAMPAIGNS:
            values = day_values(rng, name, day)
            if values is None:
                continue
            impressions, clicks, cost, conversions, value = values
            status, budget, strategy = CAMPAIGNS[name][:3]
            lines.append([day.isoformat(), status, name, fmt(budget), "Daily", "USD", "Paused" if status == "Paused" else "Eligible", "Search", strategy,
                          fmt(cost), fmt(impressions, 0), fmt(clicks, 0), "%.2f%%" % (100.0 * clicks / impressions) if impressions else " --",
                          fmt(cost / clicks) if clicks else " --", "%.2f%%" % (100.0 * conversions / clicks) if clicks else " --",
                          fmt(conversions), fmt(cost / conversions) if conversions else " --", fmt(value)])
            sums = [sums[0] + impressions, sums[1] + clicks, sums[2] + cost, sums[3] + conversions, sums[4] + value]
        for label in ("Total: Filtered campaigns", "Total: Account", "Total: Search"):
            totals.append([day.isoformat(), label, " --", " --", " --", "USD", " --", " --", " --", fmt(sums[2]), fmt(sums[0], 0), fmt(sums[1], 0),
                           " --", " --", " --", fmt(sums[3]), " --", fmt(sums[4])])
        day += dt.timedelta(days=1)
    # The report keeps only the columns SKILL.md asks for, plus currency, so the sample stays under
    # the 256 KiB a plugin directory allows for one file. The skill works out CTR, CPC, conversion
    # rate and cost per conversion itself, and never reads budget or bid strategy from this report.
    dropped = {"Budget", "Budget type", "Status", "Bid strategy type", "CTR", "Avg. CPC", "Conv. rate", "Cost / conv."}
    keep = [i for i, column in enumerate(header) if column not in dropped]
    rows = lines[:2] + [[row[i] for i in keep] for row in lines[2:] + totals]
    write("campaigns-by-day.csv", rows)


def change_history():
    header = ["Date & time", "User", "Campaign", "Ad group", "Changes"]
    rows = [
        ("Sep 15, 2026, 2:10:00 PM", "sam@northside.example", EMERGENCY, " --", "Ad schedule changed"),
        ("Oct 1, 2026, 9:02:13 AM", "sam@northside.example", EMERGENCY, " --", "Budget changed from 200.00 to 240.00"),
        ("Oct 6, 2026, 4:41:55 PM", "sam@northside.example", HEATERS, " --", "Bid strategy changed from Maximize conversions to Target CPA\nTarget CPA set to 45.00"),
        ("Oct 14, 2026, 11:20:05 AM", "Google Ads system", EMERGENCY, "Emergency", "6 keywords added (broad match)"),
        ("Oct 20, 2026, 8:15:40 AM", "lee@northside.example", DRAINS, " --", "Campaign status changed from Enabled to Paused"),
        ("Oct 27, 2026, 3:05:12 PM", "lee@northside.example", BRAND, " --", "Sitelink asset added"),
        ("Nov 3, 2026, 10:00:41 AM", "sam@northside.example", HEATERS, " --", "Target CPA changed from 45.00 to 55.00"),
    ]
    write("change-history.csv", [["Change history report"], ["September 1, 2026 - November 12, 2026"], header] + [list(r) for r in rows])


NARRATIVE = {
    "report_type": "monthly",
    "title": "Northside Plumbing: Google Ads, October 2026",
    "sections": [
        {"heading": "Month-over-month snapshot", "tables": ["account_without_brand", "account", "scorecard"],
         "text": "October brought {acct.conv.cur} conversions at a cost of {acct.cost.cur}, against {acct.conv.prev} conversions in September. "
                 "Conversions rose {acct.conv.chg_prev} while cost fell {acct.cost.chg_prev}.\n\n"
                 "Without Brand, cost per conversion was {nb.cpa.cur}, which is {score.cpa_nb.diff_pct} above the {target.cpa} target. "
                 "Brand searches convert cheaply by nature, so the whole account's figure of {acct.cpa.cur} looks better than the rest of the account performs.",
         "bullets": ["Against October last year, conversions rose {acct.conv.chg_ly}.",
                     "Spend came in {score.cost.diff_pct} below the spend target of {target.cost}, mostly because Drain Cleaning | Search was paused."]},
        {"heading": "Main drivers", "tables": ["movers", "campaigns"],
         "text": "Plumbing | Water Heaters was the biggest mover. Its conversions fell {c2.conv.chg_prev} after its bid strategy moved to Target CPA "
                 "on {chg2.date}, with the target set at {chg2.n1}. That change is the first lead to check, not proven cause.\n\n"
                 "Plumbing | Emergency grew. Its conversions rose {c1.conv.chg_prev} after its daily budget rose from {chg1.n1} to {chg1.n2} on {chg1.date}. "
                 "Google's systems also added {chg3.n1} keywords to it on {chg3.date}.",
         "bullets": ["Drain Cleaning | Search was paused on {chg4.date} and its last day with cost was {c3.last_cost_day}, "
                     "so its cost fell by {c3.cost.delta_prev.abs}. It did not decline; it stopped."]},
        {"heading": "Budget shifts", "tables": [],
         "text": "Plumbing | Emergency took {c1.cost.share_cur} of October's cost and brought {c1.conv.share_cur} of its conversions. "
                 "The pause of Drain Cleaning | Search freed budget that was not moved elsewhere."},
        {"heading": "Recommended next actions", "tables": [],
         "bullets": ["Review the Target CPA on Plumbing | Water Heaters. It was raised after the month closed, so November will show whether that helps.",
                     "Decide with you whether Drain Cleaning | Search comes back on, and on what budget.",
                     "Judge cost per conversion without Brand from now on, since Brand hides the gap to target."]},
    ],
}
FIRST_DRAFT = {
    "report_type": "monthly",
    "title": "Northside Plumbing: Google Ads, October 2026",
    "sections": [
        {"heading": "Month-over-month snapshot", "tables": ["account"],
         "text": "Conversions fell {acct.conv.chg_prev} in October. Cost per conversion was 35.10, comfortably under target.",
         "bullets": ["Water Heaters conversions fell {c1.conv.chg_prev}."]},
        {"heading": "Main drivers", "tables": ["leaderboard"], "text": ""},
    ],
}
DRAFT_REPORT = """# Northside Plumbing: October 2026 Google Ads report

Reporting period: October 1 to 31, 2026, compared with September 2026.

## Summary

October was a strong month. Conversions grew {conv_chg} on September, and cost was {cost}.
Cost per conversion rose {cpa_chg} to {cpa}, under the 40.00 target.

## Campaigns

- Plumbing | Water Heaters conversions fell {heaters_ly} month over month after the move to Target CPA.
- Drain Cleaning | Search declined sharply, with cost down 18% on September.
- Return on ad spend reached 9.4x for the month.
- Plumbing | Emergency took {share} of the account's cost.

## Next month

We will keep the current setup and expect a similar result.
"""


def drafts(work):
    """The draft report is written from the real numbers, with errors planted."""
    numbers_path = os.path.join(work, "numbers.json")
    with open(numbers_path, encoding="utf-8") as handle:
        numbers = json.load(handle)["numbers"]

    def pct(nid):
        return "%.1f%%" % (abs(numbers[nid]["value"]) * 100)

    text = DRAFT_REPORT.format(cost="{:,.2f}".format(numbers["acct.cost.cur"]["value"]), cpa="{:,.2f}".format(numbers["acct.cpa.cur"]["value"]),
                               heaters_ly=pct("c2.conv.chg_ly"), share=pct("c1.cost.share_cur"),
                               conv_chg=pct("acct.conv.chg_prev"), cpa_chg=pct("acct.cpa.chg_prev"))
    with open(os.path.join(OUT, "draft-report-to-check.md"), "w", encoding="utf-8") as handle:
        handle.write(text)


def write(name, lines):
    # Google Ads downloads end lines with a plain line feed, so the samples do too.
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle, lineterminator="\n").writerows(lines)


def write_json(name, data):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1, ensure_ascii=False)


def main():
    os.makedirs(OUT, exist_ok=True)
    campaign_report(random.Random(20261113))
    change_history()
    write_json("example-narrative.json", NARRATIVE)
    write_json("example-narrative-first-draft.json", FIRST_DRAFT)
    # The draft report quotes real figures, so it is written after a measure run.
    skill = os.path.join(os.path.dirname(HERE), "skills", "client-reporting-for-google-ads", "scripts", "measure.py")
    work = tempfile.mkdtemp()
    subprocess.run([sys.executable, skill, os.path.join(OUT, "campaigns-by-day.csv"), "--work", work, "--report-type", "monthly",
                    "--changes", os.path.join(OUT, "change-history.csv"), "--brand-campaigns", BRAND, "--target-cpa", "40", "--target-spend", "16000"],
                   check=True, capture_output=True)
    drafts(work)
    shutil.rmtree(work)
    print("Wrote the samples to %s" % OUT)


if __name__ == "__main__":
    main()
