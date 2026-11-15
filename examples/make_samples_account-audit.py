#!/usr/bin/env python3
"""Write the sample exports for the account audit skill.

SYNTHETIC DATA. The business, the campaigns and every number are made up.
The files copy the layout of real Google Ads downloads: a title row, a quoted
date range row, the header, the rows, then "Total" rows, with " --" for empty
cells and thousands separators. The ads report, ad group report and
conversions summary have not yet been seen in a real download, so they use
the column names Google documents.

Planted problems the audit must find:
1. Drain Cleaning | Search > Hydro Jetting has no active ad. Its only enabled
   ad is disapproved and the other is paused.
2. Two primary conversion actions record the same lead form, and the Google
   Analytics one counts Every conversion.
3. Plumbing | Emergency is held back by budget while it converts below the
   account's non brand cost per conversion.
And one trap: Drain Cleaning | Old is paused. It spent with no conversions
and must not be judged as if it were serving.

    python3 examples/make_samples_account-audit.py
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "exports", "account-audit")
PERIOD = "October 14, 2026 - November 12, 2026"
EMERGENCY, HEATERS, DRAINS, BRAND, OLD = "Plumbing | Emergency", "Plumbing | Water Heaters", "Drain Cleaning | Search", "Brand", "Drain Cleaning | Old"
DASH = " --"

# campaign: status, serving status, bid strategy, budget, budget name, impr. share, lost IS (rank), lost IS (budget)
CAMPAIGNS = {
    EMERGENCY: ("Enabled", "Eligible", "Manual CPC", 240.00, "Plumbing | Emergency", "51.30%", "14.50%", "34.20%"),
    HEATERS: ("Enabled", "Limited by budget", "Maximize Conversions", 160.00, "Water Heaters", "58.10%", "20.80%", "21.10%"),
    DRAINS: ("Enabled", "Eligible (Learning)", "Maximize Conversions", 120.00, "Drain Cleaning", "66.40%", "33.60%", "< 10%"),
    BRAND: ("Enabled", "Eligible", "Manual CPC", 40.00, "Brand", "92.70%", "> 90%", "< 10%"),
    OLD: ("Paused", "Paused", "Manual CPC", 50.00, "Drain Cleaning | Old", DASH, DASH, DASH),
}
AD_GROUPS = [(EMERGENCY, "Emergency"), (EMERGENCY, "Burst Pipes"), (HEATERS, "Repair"), (HEATERS, "Install"),
             (DRAINS, "Drains"), (DRAINS, "Hydro Jetting"), (BRAND, "Brand"), (OLD, "Old Drains")]
# status, keyword, match type, campaign, ad group, impr., clicks, cost, conversions, Quality Score, Exp. CTR, Ad relevance, Landing page exp.
KEYWORDS = [
    ("Enabled", '"emergency plumber"', "Phrase match", EMERGENCY, "Emergency", 5200, 410, 3402.00, 52, 7, "Above average", "Average", "Average"),
    ("Enabled", "[24 hour plumber]", "Exact match", EMERGENCY, "Emergency", 1905, 148, 1273.40, 26, 8, "Above average", "Above average", "Average"),
    ("Enabled", "plumber free estimate", "Broad match", EMERGENCY, "Emergency", 1890, 99, 689.30, 3, 4, "Average", "Average", "Below average"),
    ("Enabled", "plumber near me", "Broad match", EMERGENCY, "Emergency", 3300, 240, 1520.00, 0, 5, "Average", "Average", "Average"),
    ("Paused", "plumber cost", "Broad match", EMERGENCY, "Emergency", 610, 12, 87.40, 0, 5, "Average", "Average", "Average"),
    ("Enabled", '"burst pipe repair"', "Phrase match", EMERGENCY, "Burst Pipes", 910, 64, 521.10, 9, 6, "Average", "Above average", "Average"),
    ("Enabled", '"emergency plumber"', "Phrase match", EMERGENCY, "Burst Pipes", 300, 21, 180.60, 1, 6, "Average", "Average", "Average"),
    ("Enabled", "frozen pipe repair", "Broad match", EMERGENCY, "Burst Pipes", 0, 0, 0.00, 0, None, DASH, DASH, DASH),
    ("Enabled", '"water heater repair"', "Phrase match", HEATERS, "Repair", 2010, 131, 943.20, 12, 7, "Above average", "Above average", "Average"),
    ("Enabled", "water heater not heating", "Broad match", HEATERS, "Repair", 1330, 55, 379.50, 3, 5, "Average", "Below average", "Average"),
    ("Enabled", '"water heater installation"', "Phrase match", HEATERS, "Install", 1180, 74, 695.60, 6, 7, "Average", "Above average", "Above average"),
    ("Enabled", "tankless water heater", "Broad match", HEATERS, "Install", 1890, 62, 508.40, 2, 6, "Average", "Average", "Average"),
    ("Enabled", '"drain cleaning"', "Phrase match", DRAINS, "Drains", 3100, 180, 918.00, 16, 8, "Above average", "Above average", "Above average"),
    ("Enabled", "clogged drain", "Broad match", DRAINS, "Drains", 2200, 120, 612.00, 5, 6, "Average", "Average", "Average"),
    ("Enabled", '"hydro jetting"', "Phrase match", DRAINS, "Hydro Jetting", 900, 70, 357.00, 1, 6, "Average", "Average", "Average"),
    ("Enabled", "[northside plumbing]", "Exact match", BRAND, "Brand", 410, 96, 142.10, 28, 10, "Above average", "Above average", "Above average"),
    ("Enabled", '"northside plumbing"', "Phrase match", BRAND, "Brand", 180, 22, 38.50, 3, 9, "Above average", "Above average", "Above average"),
    ("Enabled", "drain unblocking", "Broad match", OLD, "Old Drains", 1500, 60, 310.25, 0, 4, "Average", "Average", "Below average"),
]
# campaign, ad group, ad status, status, policy details, ad strength, headline, share of the ad group's traffic
ADS = [
    (EMERGENCY, "Emergency", "Enabled", "Eligible", DASH, "Excellent", "24/7 Emergency Plumber", 0.6),
    (EMERGENCY, "Emergency", "Enabled", "Eligible", DASH, "Good", "Plumber At Your Door In 60 Min", 0.4),
    (EMERGENCY, "Burst Pipes", "Enabled", "Eligible", DASH, "Average", "Burst Pipe Repair Today", 0.7),
    (EMERGENCY, "Burst Pipes", "Enabled", "Eligible", DASH, "Poor", "Fix Burst Pipes Fast", 0.3),
    (HEATERS, "Repair", "Enabled", "Eligible", DASH, "Good", "Water Heater Repair Same Day", 0.65),
    (HEATERS, "Repair", "Enabled", "Eligible", DASH, "Average", "No Hot Water? Call Us", 0.35),
    (HEATERS, "Install", "Enabled", "Eligible", DASH, "Excellent", "Tankless Water Heater Installs", 0.5),
    (HEATERS, "Install", "Enabled", "Eligible", DASH, "Good", "New Water Heater, Installed", 0.5),
    (DRAINS, "Drains", "Enabled", "Eligible", DASH, "Excellent", "Drain Cleaning From 89", 0.5),
    (DRAINS, "Drains", "Enabled", "Eligible", DASH, "Good", "Clogged Drain? Same Day Service", 0.3),
    (DRAINS, "Drains", "Enabled", "Eligible (limited)", "Trademarks in ad text", "Average", "Roto Style Drain Service", 0.2),
    (DRAINS, "Hydro Jetting", "Enabled", "Disapproved", "Destination not working", "Good", "Hydro Jetting Specialists", 0.85),
    (DRAINS, "Hydro Jetting", "Paused", "Paused", DASH, "Average", "Hydro Jet Your Drains", 0.15),
    (BRAND, "Brand", "Enabled", "Eligible", DASH, "Good", "Northside Plumbing Official Site", 0.6),
    (BRAND, "Brand", "Enabled", "Eligible", DASH, "Good", "Northside Plumbing, Since 1998", 0.4),
    (OLD, "Old Drains", "Enabled", "Campaign paused", DASH, "Average", "Drain Unblocking Experts", 1.0),
]
# search term, match type, added/excluded, campaign, ad group, clicks, impr., cost, conversions
SEARCH_TERMS = [
    ("emergency plumber near me", "Phrase match", "None", EMERGENCY, "Emergency", 230, 2950, 1908.00, 31, '"emergency plumber"'),
    ("24 hour plumber", "Exact match", "Added", EMERGENCY, "Emergency", 148, 1905, 1273.40, 26, '[24 hour plumber]'),
    ("plumber near me", "Broad match", "None", EMERGENCY, "Emergency", 89, 1440, 640.20, 0, 'plumber near me'),
    ("plumbing jobs near me", "Broad match", "None", EMERGENCY, "Emergency", 71, 2310, 468.60, 0, 'plumber near me'),
    ("free estimate plumber", "Broad match", "None", EMERGENCY, "Emergency", 58, 1120, 402.30, 3, 'plumber free estimate'),
    ("plumber jobs hiring", "Broad match", "None", EMERGENCY, "Emergency", 38, 1150, 243.20, 0, 'plumber free estimate'),
    ("how to fix a leaky faucet yourself", "Broad match", "None", EMERGENCY, "Emergency", 33, 1980, 184.80, 0, 'plumber near me'),
    ("plumber salary", "Broad match", "None", EMERGENCY, "Emergency", 24, 1420, 139.20, 0, 'plumber near me'),
    ("northside plumber", "Broad match", "None", EMERGENCY, "Emergency", 9, 140, 61.20, 0, 'plumber near me'),
    ("northside plumbing reviews", "Broad match", "None", EMERGENCY, "Emergency", 22, 180, 38.50, 0, 'plumber free estimate'),
    ("burst pipe repair", "Phrase match", "Added", EMERGENCY, "Burst Pipes", 51, 720, 412.30, 7, '"burst pipe repair"'),
    ("emergency pipe burst", "Phrase match", "None", EMERGENCY, "Burst Pipes", 18, 260, 150.10, 1, '"emergency plumber"'),
    ("water heater repair", "Phrase match", "Added", HEATERS, "Repair", 90, 1390, 640.10, 10, '"water heater repair"'),
    ("diy water heater repair", "Broad match", "None", HEATERS, "Repair", 44, 1760, 277.20, 0, '"water heater repair"'),
    ("water heater not heating", "Broad match", "None", HEATERS, "Repair", 22, 610, 150.40, 2, 'water heater not heating'),
    ("tankless water heater installation", "Phrase match", "None", HEATERS, "Install", 53, 900, 495.60, 4, '"water heater installation"'),
    ("water heater replacement cost", "Broad match", "None", HEATERS, "Install", 46, 1210, 380.10, 3, 'tankless water heater'),
    ("free water heater program", "AI Max", "None", HEATERS, "Install", 27, 1490, 159.30, 0, '"water heater installation"'),
    ("drain cleaning near me", "Phrase match", "None", DRAINS, "Drains", 138, 2240, 702.00, 13, '"drain cleaning"'),
    ("drain cleaning cost", "Phrase match", "None", DRAINS, "Drains", 41, 690, 210.40, 2, '"drain cleaning"'),
    ("how to unclog a drain with baking soda", "Broad match", "None", DRAINS, "Drains", 37, 1630, 189.30, 0, 'clogged drain'),
    ("hydro jetting service", "Phrase match", "None", DRAINS, "Hydro Jetting", 59, 760, 301.00, 1, '"hydro jetting"'),
    ("northside plumbing", "Exact match", "Added", BRAND, "Brand", 96, 410, 142.10, 28, '[northside plumbing]'),
    ("northside plumbing hours", "Phrase match", "None", BRAND, "Brand", 19, 150, 30.10, 3, '"northside plumbing"'),
    ("drain unblocking", "Broad match", "None", OLD, "Old Drains", 40, 980, 210.00, 0, 'drain unblocking'),
]
# Share of each campaign's traffic on Search partners, and the conversions there.
PARTNERS = {EMERGENCY: (0.0876, 2), HEATERS: (0.0435, 2)}


def fmt(value, digits=2):
    return "{:,.{d}f}".format(value, d=digits)


def cents(value):
    return int(round(value * 100))


def split(total, shares):
    """Split an amount in cents so the parts add up exactly."""
    parts = [int(total * s) for s in shares[:-1]]
    return parts + [total - sum(parts)]


def rates(clicks, impr, cost, conv):
    return ["%.2f%%" % (100.0 * clicks / impr) if impr else DASH, fmt(cost / clicks) if clicks else DASH,
            "%.2f%%" % (100.0 * conv / clicks) if clicks else DASH, fmt(cost / conv) if conv else DASH]


def sums(rows):
    out = {}
    for row in rows:
        for key in ("impr", "clicks", "cost", "conv"):
            out[key] = out.get(key, 0) + row[key]
    return out


def keyword_rows():
    return [{"status": s, "keyword": k, "match": mt, "campaign": c, "ad_group": g, "impr": i, "clicks": cl, "cost": cents(co), "conv": cv,
             "qs": qs, "ctr": e, "rel": r, "lp": lp} for s, k, mt, c, g, i, cl, co, cv, qs, e, r, lp in KEYWORDS]


def group_totals(kws):
    out = {}
    for row in kws:
        slot = out.setdefault((row["campaign"], row["ad_group"]), {"impr": 0, "clicks": 0, "cost": 0, "conv": 0})
        for key in slot:
            slot[key] += row[key]
    return out


def campaign_totals(groups):
    out = {}
    for (campaign, _), g in groups.items():
        slot = out.setdefault(campaign, {"impr": 0, "clicks": 0, "cost": 0, "conv": 0})
        for key in slot:
            slot[key] += g[key]
    return out


def money(c):
    return fmt(c / 100.0)


def totals_line(label, width, cells):
    row = [label] + [DASH] * (width - 1)
    for index, value in cells.items():
        row[index] = value
    return row


def write(name, lines):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(lines)
    print("wrote examples/exports/account-audit/%s (%d lines)" % (name, len(lines)))


def campaigns(groups):
    header = ["Campaign status", "Campaign", "Budget", "Budget name", "Budget type", "Currency code", "Status", "Status reasons", "Campaign type",
              "Bid strategy type", "Cost", "Impr.", "Clicks", "CTR", "Avg. CPC", "Search impr. share", "Search lost IS (rank)",
              "Search lost IS (budget)", "Conv. rate", "Conversions", "Cost / conv.", "Goals"]
    totals = campaign_totals(groups)
    lines = [["Campaign report"], [PERIOD], header]
    for name, (state, serving, strategy, budget, budget_name, share, rank, lost) in CAMPAIGNS.items():
        t = totals[name]
        ctr, cpc, cvr, cpa = rates(t["clicks"], t["impr"], t["cost"] / 100.0, t["conv"])
        reasons = "Campaign paused" if state == "Paused" else DASH
        lines.append([state, name, fmt(budget), budget_name, "Daily", "USD", serving, reasons, "Search", strategy, money(t["cost"]), fmt(t["impr"], 0),
                      fmt(t["clicks"], 0), ctr, cpc, share, rank, lost, cvr, fmt(t["conv"]), cpa, "Leads"])
    every = sums(totals.values())
    cells = {5: "USD", 10: money(every["cost"]), 11: fmt(every["impr"], 0), 12: fmt(every["clicks"], 0), 19: fmt(every["conv"])}
    for label in ("Total: Filtered campaigns", "Total: Account", "Total: Search"):
        lines.append(totals_line(label, len(header), cells))
    write("campaign-report.csv", lines)
    return totals


def networks(totals):
    header = ["Campaign", "Network (with search partners)", "Currency code", "Impr.", "Clicks", "Cost", "Conversions"]
    lines = [["Campaign report"], [PERIOD], header]
    for name in CAMPAIGNS:
        t = totals[name]
        share, conv = PARTNERS.get(name, (0.0, 0))
        part = {"impr": int(t["impr"] * share), "clicks": int(t["clicks"] * share), "cost": int(t["cost"] * share), "conv": conv}
        main = {k: t[k] - part[k] for k in part}
        lines.append([name, "Google search", "USD", fmt(main["impr"], 0), fmt(main["clicks"], 0), money(main["cost"]), fmt(main["conv"])])
        if part["cost"]:
            lines.append([name, "Search partners", "USD", fmt(part["impr"], 0), fmt(part["clicks"], 0), money(part["cost"]), fmt(part["conv"])])
    every = sums(totals.values())
    lines.append(totals_line("Total: Account", len(header), {2: "USD", 3: fmt(every["impr"], 0), 4: fmt(every["clicks"], 0), 5: money(every["cost"]), 6: fmt(every["conv"])}))
    write("campaign-report-by-network.csv", lines)


def ad_groups(groups):
    header = ["Ad group status", "Ad group", "Campaign", "Status", "Ad group type", "Currency code", "Impr.", "Clicks", "Cost", "Conversions", "Cost / conv."]
    lines = [["Ad group report"], [PERIOD], header]
    for campaign, group in AD_GROUPS:
        g = groups[(campaign, group)]
        serving = "Campaign paused" if CAMPAIGNS[campaign][0] == "Paused" else "Eligible"
        lines.append(["Enabled", group, campaign, serving, "Standard", "USD", fmt(g["impr"], 0), fmt(g["clicks"], 0), money(g["cost"]), fmt(g["conv"]),
                      rates(g["clicks"], g["impr"], g["cost"] / 100.0, g["conv"])[3]])
    every = sums(groups.values())
    for label in ("Total: Account", "Total: Search"):
        lines.append(totals_line(label, len(header), {5: "USD", 6: fmt(every["impr"], 0), 7: fmt(every["clicks"], 0), 8: money(every["cost"]), 9: fmt(every["conv"])}))
    write("ad-group-report.csv", lines)


def keywords(kws):
    header = ["Keyword status", "Keyword", "Match type", "Campaign", "Ad group", "Status", "Status reasons", "Final URL", "Currency code", "Avg. CPM",
              "Impr.", "Interactions", "Interaction rate", "Avg. cost", "Cost", "Conv. rate", "Conversions", "Cost / conv.",
              "Quality Score", "Exp. CTR", "Ad relevance", "Landing page exp.", "Conversions (Calls only)"]
    lines = [["Search keyword report"], [PERIOD], header]
    for k in kws:
        cost = k["cost"] / 100.0
        ctr, cpc, cvr, cpa = rates(k["clicks"], k["impr"], cost, k["conv"])
        if CAMPAIGNS[k["campaign"]][0] == "Paused":
            serving = "Campaign paused"
        else:
            serving = "Paused" if k["status"] == "Paused" else ("Low search volume" if not k["impr"] else "Eligible")
        lines.append([k["status"], k["keyword"], k["match"], k["campaign"], k["ad_group"], serving, DASH,
                      "https://www.northsideplumbing.example/%s" % k["ad_group"].lower().replace(" ", "-"), "USD",
                      fmt(1000.0 * cost / k["impr"]) if k["impr"] else DASH, fmt(k["impr"], 0), fmt(k["clicks"], 0), ctr, cpc, money(k["cost"]), cvr,
                      fmt(k["conv"]), cpa, str(k["qs"]) if k["qs"] else DASH, k["ctr"], k["rel"], k["lp"], "0.00"])
    every = sums(kws)
    cells = {8: "USD", 10: fmt(every["impr"], 0), 11: fmt(every["clicks"], 0), 14: money(every["cost"]), 16: fmt(every["conv"])}
    for label in ("Total: Keywords in your account", "Total: All but removed keywords", "Total: Account", "Total: Search"):
        lines.append(totals_line(label, len(header), cells))
    write("keyword-report.csv", lines)


def ads(groups):
    header = ["Ad status", "Ad", "Ad type", "Ad strength", "Campaign", "Ad group", "Status", "Policy details", "Final URL", "Currency code",
              "Impr.", "Clicks", "Cost", "Conversions"]
    lines = [["Ads report"], [PERIOD], header]
    for key in AD_GROUPS:
        mine = [a for a in ADS if (a[0], a[1]) == key]
        g = groups[key]
        shares = [a[7] for a in mine]
        parts = {field: split(g[field], shares) for field in ("impr", "clicks", "cost")}
        conv = split(int(round(g["conv"] * 100)), shares)
        for index, (campaign, group, state, serving, policy, strength, headline, _) in enumerate(mine):
            lines.append([state, headline, "Responsive search ad", strength, campaign, group, serving, policy,
                          "https://www.northsideplumbing.example/%s" % group.lower().replace(" ", "-"), "USD", fmt(parts["impr"][index], 0),
                          fmt(parts["clicks"][index], 0), money(parts["cost"][index]), fmt(conv[index] / 100.0)])
    every = sums(groups.values())
    for label in ("Total: Account", "Total: Search"):
        lines.append(totals_line(label, len(header), {9: "USD", 10: fmt(every["impr"], 0), 11: fmt(every["clicks"], 0), 12: money(every["cost"]), 13: fmt(every["conv"])}))
    write("ads-report.csv", lines)


def search_terms():
    header = ["Search term", "Match type", "Added/Excluded", "Campaign", "Ad group", "Keyword", "Currency code", "Avg. CPM", "Clicks", "Impr.",
              "CTR", "Avg. CPC", "Cost", "Campaign type", "Conv. rate", "Conversions", "Cost / conv."]
    lines = [["Search terms report"], [PERIOD], header]
    total = {"clicks": 0, "impr": 0, "cost": 0, "conv": 0}
    for term, match, added, campaign, group, clicks, impr, cost, conv, keyword in SEARCH_TERMS:
        ctr, cpc, cvr, cpa = rates(clicks, impr, cost, conv)
        lines.append([term, match, added, campaign, group, keyword, "USD", fmt(1000.0 * cost / impr), fmt(clicks, 0), fmt(impr, 0), ctr, cpc, fmt(cost),
                      "Search", cvr, fmt(conv), cpa])
        for key, value in (("clicks", clicks), ("impr", impr), ("cost", cents(cost)), ("conv", conv)):
            total[key] += value
    lines.append(totals_line("Total: Search terms", len(header), {6: "USD", 8: fmt(total["clicks"], 0), 9: fmt(total["impr"], 0), 12: money(total["cost"]), 15: fmt(total["conv"])}))
    write("search-terms-report.csv", lines)


def conversions(kws):
    primary = sum(k["conv"] for k in kws)
    contact, calls = 70, 20
    rows = [
        ("Contact form submit", "Primary", "Website", "Submit lead form", "One", "Recording conversions", contact, contact),
        ("GA4 generate_lead", "Primary", "Google Analytics 4 (web)", "Submit lead form", "Every", "Recording conversions", primary - contact - calls, primary - contact - calls),
        ("Calls from ads", "Primary", "Call from ads", "Phone call lead", "One", "Recording conversions", calls, calls),
        ("Thank you page view", "Secondary", "Website", "Page view", "Every", "Recording conversions", 0, 160),
        ("Old quote form", "Secondary", "Website", "Request quote", "One", "Removed", 0, 0),
    ]
    header = ["Conversion action", "Action optimization", "Conversion source", "Category", "Count", "Tracking status", "Conversions", "All conv."]
    lines = [["Conversion actions"], [PERIOD], header] + [[a, b, c, d, e, f, fmt(g), fmt(h)] for a, b, c, d, e, f, g, h in rows]
    write("conversions-summary.csv", lines)


if __name__ == "__main__":
    kws = keyword_rows()
    groups = group_totals(kws)
    totals = campaigns(groups)
    networks(totals)
    ad_groups(groups)
    keywords(kws)
    ads(groups)
    search_terms()
    conversions(kws)
