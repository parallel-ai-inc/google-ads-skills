#!/usr/bin/env python3
"""Write the sample exports used to try the skills.

SYNTHETIC DATA. The business, the campaigns and every number are made up.
The files copy the layout of real Google Ads downloads: a title row and a
date range above the header, "Total" rows at the bottom, "--" for empty
cells, thousands separators and percent signs.

    python3 dev/samples/make_samples.py
"""
import csv
import datetime as dt
import os
import random

HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples")
OUT = os.path.join(HERE, "exports")
EMERGENCY = "Plumbing | Emergency"
HEATERS = "Plumbing | Water Heaters"
DRAINS = "Drain Cleaning | Search"
BRAND = "Brand"


def fmt(value, digits=2):
    return "{:,.{d}f}".format(value, d=digits)


def search_terms():
    # search, match type, campaign, ad group, clicks, impressions, cost, conversions, value, status
    rows = [
        ("emergency plumber near me", "Phrase match", EMERGENCY, "Emergency", 212, 2840, 1908.00, 31, 9300, "None"),
        ("24 hour plumber", "Exact match", EMERGENCY, "Emergency", 148, 1905, 1273.40, 22, 6600, "Added"),
        ("burst pipe repair", "Broad match", EMERGENCY, "Emergency", 64, 910, 521.10, 9, 3150, "None"),
        ("free estimate plumber", "Broad match", EMERGENCY, "Emergency", 58, 1120, 402.30, 7, 2100, "None"),
        ("plumber cost estimate", "Broad match", EMERGENCY, "Emergency", 41, 890, 287.00, 3, 900, "None"),
        ("plumber open now", "AI Max", EMERGENCY, "Emergency", 37, 640, 301.90, 5, 1500, "None"),
        ("northside plumbing", "Exact match", EMERGENCY, "Emergency", 96, 410, 142.10, 28, 8400, "None"),
        ("northside plumbing reviews", "Broad match", EMERGENCY, "Emergency", 22, 180, 38.50, 0, 0, "None"),
        ("plumbing jobs near me", "Broad match", EMERGENCY, "Emergency", 71, 2310, 468.60, 0, 0, "None"),
        ("plumber jobs hiring", "Broad match", EMERGENCY, "Emergency", 38, 1150, 243.20, 0, 0, "None"),
        ("plumbing apprenticeship", "Broad match", EMERGENCY, "Emergency", 29, 980, 171.10, 0, 0, "None"),
        ("plumber salary", "Broad match", EMERGENCY, "Emergency", 24, 1420, 139.20, 0, 0, "None"),
        ("how to fix a leaky faucet yourself", "Broad match", EMERGENCY, "Emergency", 33, 1980, 184.80, 0, 0, "None"),
        ("free plumbing course", "Broad match", EMERGENCY, "Emergency", 17, 760, 98.60, 0, 0, "None"),
        ("plumbing school", "AI Max", EMERGENCY, "Emergency", 26, 1310, 150.80, 0, 0, "None"),
        ("plumbing supply store", "Broad match", EMERGENCY, "Emergency", 19, 1240, 104.50, 0, 0, "None"),
        ("emergency plumber", "Exact match", EMERGENCY, "Emergency", 9, 150, 82.80, 0, 0, "None"),
        ("plumber near me cheap", "Broad match", EMERGENCY, "Emergency", 6, 210, 44.40, 0, 0, "None"),
        ("leaking pipe under sink", "Broad match", EMERGENCY, "Emergency", 2, 95, 15.20, 0, 0, "None"),
        ("plumber license lookup", "Broad match", EMERGENCY, "Emergency", 11, 430, 61.60, 0, 0, "Excluded"),
        ("water heater repair", "Phrase match", HEATERS, "Repair", 131, 2010, 943.20, 17, 6800, "Added"),
        ("water heater not heating", "Broad match", HEATERS, "Repair", 55, 1330, 379.50, 6, 2400, "None"),
        ("tankless water heater installation", "Phrase match", HEATERS, "Install", 74, 1180, 695.60, 8, 9600, "None"),
        ("water heater replacement cost", "Broad match", HEATERS, "Install", 62, 1890, 508.40, 4, 4800, "None"),
        ("free water heater estimate", "Broad match", HEATERS, "Install", 18, 420, 129.60, 2, 2400, "None"),
        ("diy water heater repair", "Broad match", HEATERS, "Repair", 44, 1760, 277.20, 0, 0, "None"),
        ("water heater parts home depot", "Broad match", HEATERS, "Repair", 36, 1540, 208.80, 0, 0, "None"),
        ("how to drain a water heater", "Broad match", HEATERS, "Repair", 41, 2620, 229.60, 0, 0, "None"),
        ("water heater repair jobs", "Broad match", HEATERS, "Repair", 13, 510, 79.30, 0, 0, "None"),
        ("free water heater program", "AI Max", HEATERS, "Install", 27, 1490, 159.30, 0, 0, "None"),
        ("rheem water heater manual", "Broad match", HEATERS, "Repair", 21, 1120, 119.70, 0, 0, "None"),
        ("water heater installation near me", "Broad match", HEATERS, "Install", 8, 260, 71.20, 0, 0, "None"),
        ("gas water heater pilot light", "Broad match", HEATERS, "Repair", 5, 340, 28.50, 0, 0, "None"),
        ("electric water heater element", "Broad match", HEATERS, "Repair", 2, 150, 11.80, 0, 0, "None"),
    ]
    header = ["Search term", "Match type", "Added/Excluded", "Campaign", "Ad group", "Currency code", "Clicks", "Impr.",
              "CTR", "Avg. CPC", "Cost", "Conversions", "Cost / conv.", "Conv. rate", "Conv. value"]
    lines = [["Search terms report"], ["October 14, 2026 - November 12, 2026"], header]
    sums = [0, 0, 0.0, 0.0, 0.0]
    for term, match, campaign, group, clicks, impr, cost, conv, value, status in rows:
        sums = [sums[0] + clicks, sums[1] + impr, sums[2] + cost, sums[3] + conv, sums[4] + value]
        lines.append([term, match, status, campaign, group, "USD", fmt(clicks, 0), fmt(impr, 0),
                      "%.2f%%" % (100.0 * clicks / impr), fmt(cost / clicks), fmt(cost), fmt(conv),
                      fmt(cost / conv) if conv else "0.00", "%.2f%%" % (100.0 * conv / clicks), fmt(value)])
    lines.append(["Total: Search terms", "--", "--", "--", "--", "USD", fmt(sums[0], 0), fmt(sums[1], 0), "--", "--",
                  fmt(sums[2]), fmt(sums[3]), "--", "--", fmt(sums[4])])
    lines.append(["Total: Other search terms", "--", "--", "--", "--", "USD", "118", "6,940", "--", "--", "612.40", "3.00", "--", "--", "900.00"])
    write("search-terms-report.csv", lines)


def keywords():
    header = ["Keyword status", "Keyword", "Match type", "Campaign", "Ad group", "Clicks", "Cost"]
    rows = [
        ("Enabled", "emergency plumber", "Phrase match", EMERGENCY, "Emergency", "410", "3,402.00"),
        ("Enabled", "[24 hour plumber]", "Exact match", EMERGENCY, "Emergency", "148", "1,273.40"),
        ("Enabled", "plumber free estimate", "Broad match", EMERGENCY, "Emergency", "99", "689.30"),
        ("Enabled", "water heater repair", "Phrase match", HEATERS, "Repair", "236", "1,671.40"),
        ("Enabled", "water heater installation", "Phrase match", HEATERS, "Install", "172", "1,404.80"),
    ]
    write("keywords-report.csv", [["Search keyword report"], ["October 14, 2026 - November 12, 2026"], header] + [list(r) for r in rows])


def campaigns_by_day():
    rng = random.Random(7)
    start, end = dt.date(2026, 10, 1), dt.date(2026, 11, 12)
    header = ["Day", "Campaign", "Campaign status", "Budget", "Currency code", "Impr.", "Clicks", "Cost",
              "Conversions", "Conv. value", "Search lost IS (budget)"]
    lines = [["Campaign report"], ["October 1, 2026 - November 12, 2026"], header]
    day = start
    while day <= end:
        weekend = 0.82 if day.weekday() >= 5 else 1.0
        # name, budget, impressions, CTR, CPC, conversion rate, value per conversion, lost IS (budget)
        plan = [
            (EMERGENCY, 240.0, 420, 0.075, 8.90, 0.220, 300, 0.34),
            (HEATERS, 160.0, 300, 0.062, 7.20, 0.120, 520, 0.0),
            (DRAINS, 120.0, 260, 0.058, 5.10, 0.090, 210, 0.0),
            (BRAND, 40.0, 52, 0.310, 1.45, 0.300, 300, 0.0),
        ]
        for name, budget, impr, ctr, cpc, cvr, value, lost in plan:
            # Water Heaters: conversion rate falls from November 3, the day after a bid strategy change.
            if name == HEATERS and day >= dt.date(2026, 11, 3):
                cvr *= 0.48
            # Drain Cleaning: cost per click climbs from November 5, after broad match keywords were added.
            if name == DRAINS and day >= dt.date(2026, 11, 5):
                cpc *= 1.55
                impr = int(impr * 1.25)
            impressions = int(impr * weekend * rng.uniform(0.9, 1.1))
            click_rate = impressions * ctr * rng.uniform(0.9, 1.1)
            cost = click_rate * cpc * rng.uniform(0.94, 1.06)
            if name == EMERGENCY:
                cost = min(cost, budget * rng.uniform(1.0, 1.12))
                click_rate = cost / cpc
            clicks = max(int(round(click_rate)), 1)
            conversions = round(click_rate * cvr * rng.uniform(0.8, 1.2), 2)
            lost_text = "%.1f%%" % (100 * lost * rng.uniform(0.85, 1.15)) if lost else "< 10%"
            lines.append([day.isoformat(), name, "Enabled", fmt(budget), "USD", fmt(impressions, 0), fmt(clicks, 0),
                          fmt(cost), fmt(conversions), fmt(conversions * value), lost_text])
        day += dt.timedelta(days=1)
    write("campaigns-by-day.csv", lines)


def change_history():
    header = ["Date & time", "User", "Campaign", "Ad group", "Changes"]
    rows = [
        ("Oct 20, 2026, 9:14:02 AM", "sam@northside.example", EMERGENCY, "--", "Ad schedule changed"),
        ("Nov 2, 2026, 4:41:55 PM", "sam@northside.example", HEATERS, "--", "Bid strategy changed from Maximize conversions to Target CPA. Target CPA set to $45.00"),
        ("Nov 5, 2026, 10:02:11 AM", "lee@northside.example", DRAINS, "Drains", "12 keywords added (broad match)"),
        ("Nov 9, 2026, 1:30:40 PM", "sam@northside.example", BRAND, "--", "Sitelink asset added"),
    ]
    write("change-history.csv", [["Change history"], ["October 1, 2026 - November 12, 2026"], header] + [list(r) for r in rows])


def write(name, lines):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(lines)
    print("wrote examples/exports/%s (%d lines)" % (name, len(lines)))


if __name__ == "__main__":
    search_terms()
    keywords()
    campaigns_by_day()
    change_history()
