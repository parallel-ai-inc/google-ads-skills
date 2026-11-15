#!/usr/bin/env python3
"""Write synthetic inputs for the competition and market skill to examples/exports/competitive-and-market/.

Northside Plumbing runs four Search campaigns and a paused spring promo. The
files are laid out the way Google Ads downloads them: a title row, the date
range, the header, the rows, then total rows. Planted problems:

- A new rival, rapidrooter.example, enters the Emergency auctions from August
  2026. Its impression share starts as "< 10%". Emergency loses share to rank
  while its budget loss stays flat: a competitor took the share.
- Water Heaters hits its budget in October 2026 as winter demand starts. It
  spends close to its daily budget, its share loss is to budget, and its
  competitors hold steady: the account gave the share away.
- Two years of months show a winter peak for water heaters and a November
  peak for drain cleaning, and October 2026 converts worse than October 2025.

    python3 dev/samples/make_samples_competitive-and-market.py
"""
import csv
import datetime as dt
import os
import random

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples")
OUT = os.path.join(ROOT, "exports", "competitive-and-market")
DASH = " --"
EMERGENCY, HEATERS, DRAINS, BRAND, PROMO = "Plumbing | Emergency", "Plumbing | Water Heaters", "Drain Cleaning | Search", "Brand", "Plumbing | Spring Promo"
MONTH_NAMES = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
LAST_DAY = dt.date(2026, 11, 12)

# name: (eligible impressions a month, CTR, Avg. CPC, conv. rate, daily budget, bid strategy, demand by month Jan..Dec)
CAMPAIGNS = {
    EMERGENCY: (16000, 0.072, 6.20, 0.110, 160.0, "Maximize Conversions", [1.30, 1.20, 1.00, 0.95, 0.90, 0.90, 0.95, 0.95, 0.95, 1.00, 1.05, 1.25]),
    HEATERS: (11000, 0.065, 5.40, 0.080, 85.0, "Maximize Conversions", [1.45, 1.35, 1.10, 0.90, 0.80, 0.70, 0.70, 0.75, 0.85, 1.00, 1.20, 1.40]),
    DRAINS: (13000, 0.060, 3.90, 0.100, 70.0, "Target CPA", [1.00, 0.90, 0.90, 0.90, 0.85, 0.85, 0.85, 0.90, 0.95, 1.05, 1.50, 1.35]),
    BRAND: (2600, 0.220, 1.10, 0.250, 25.0, "Target impression share", [1.05, 1.0, 1.0, 1.0, 1.0, 0.95, 0.95, 0.95, 1.0, 1.0, 1.05, 1.05]),
    PROMO: (9000, 0.050, 4.50, 0.060, 60.0, "Maximize Conversions", [1.0] * 12),
}


def months():
    year, month = 2024, 10
    while (year, month) <= (2026, 11):
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def shares(name, year, month, rng):
    """Search impr. share, lost to rank and lost to budget for one campaign month. They sum to 1."""
    jitter = rng.uniform(-0.015, 0.015)
    if name == EMERGENCY:
        lost_budget = 0.08
        share = {(2026, 8): 0.56, (2026, 9): 0.49, (2026, 10): 0.44, (2026, 11): 0.43}.get((year, month), 0.58 + jitter)
        lost_budget = {(2026, 10): 0.07, (2026, 11): 0.07}.get((year, month), lost_budget)
    elif name == HEATERS:
        winter = month in (12, 1, 2)
        lost_budget = {(2026, 9): 0.10, (2026, 10): 0.26, (2026, 11): 0.27}.get((year, month), 0.16 if winter else 0.10)
        share = {(2026, 9): 0.62, (2026, 10): 0.48, (2026, 11): 0.47}.get((year, month), (0.56 if winter else 0.62) + jitter)
    elif name == DRAINS:
        lost_budget, share = 0.05, 0.52 + jitter
    elif name == BRAND:
        lost_budget, share = 0.02, 0.95
    else:
        lost_budget, share = 0.15, 0.45
    return share, 1 - share - lost_budget, lost_budget


def pct(value):
    return "%.2f%%" % (value * 100)


def banded(value):
    if value < 0.10:
        return "< 10%"
    if value > 0.90:
        return "> 90%"
    return pct(value)


def lost(row, key):
    """Brand's small lost shares are written as Google writes small shares; the others as exact values."""
    return banded(row[key]) if row["campaign"] == BRAND else pct(row[key])


def fmt(value, places=2):
    return "{:,.{p}f}".format(value, p=places)


def build_rows(rng):
    rows = []
    for year, month in months():
        days = 12 if (year, month) == (2026, 11) else 0
        full = (dt.date(year + (month // 12), month % 12 + 1, 1) - dt.date(year, month, 1)).days
        part = (days or full) / float(full)
        growth = 1 + 0.04 * ((year - 2024) * 12 + month - 10) / 12.0
        for name, (base, ctr, cpc, cvr, budget, strategy, demand) in CAMPAIGNS.items():
            if name == PROMO and (year, month) not in ((2026, 3), (2026, 4)):
                continue
            eligible = base * demand[month - 1] * growth * rng.uniform(0.96, 1.04) * part
            share, lost_rank, lost_budget = shares(name, year, month, rng)
            impressions = int(round(eligible * share))
            clicks = int(round(impressions * ctr * rng.uniform(0.95, 1.05)))
            this_cpc = cpc * rng.uniform(0.96, 1.04)
            this_cvr = cvr * rng.uniform(0.92, 1.08)
            if name == EMERGENCY and (year, month) in ((2026, 9), (2026, 10), (2026, 11)):
                this_cpc *= {9: 1.12, 10: 1.20, 11: 1.22}[month]
                this_cvr *= 0.85
            cost = round(clicks * this_cpc, 2)
            if name == HEATERS and (year, month) in ((2026, 10), (2026, 11)):
                # Held back by its budget: it spends close to the budget every day, and winter clicks cost more.
                this_cpc *= 1.10
                clicks = int(round(budget * (days or full) * rng.uniform(0.97, 0.99) / this_cpc))
                impressions = int(round(clicks / (ctr * rng.uniform(0.97, 1.03))))
                share = impressions / eligible
                lost_rank = 1 - share - lost_budget
                cost = round(clicks * this_cpc, 2)
            conversions = round(clicks * this_cvr, 2)
            rows.append({"year": year, "month": month, "campaign": name, "budget": budget, "strategy": strategy, "eligible": eligible,
                         "impressions": impressions, "clicks": clicks, "cost": cost, "conversions": conversions,
                         "share": share, "lost_rank": lost_rank, "lost_budget": lost_budget})
    return rows


def campaign_report(rows):
    header = ["Month", "Campaign status", "Campaign", "Budget", "Budget name", "Budget type", "Currency code", "Status", "Status reasons", "Campaign type",
              "Bid strategy type", "Cost", "Impr.", "Clicks", "CTR", "Avg. CPC", "Search impr. share", "Search lost IS (rank)", "Search lost IS (budget)",
              "Conv. rate", "Conversions", "Cost / conv."]
    out = [["Campaign report"], ["October 1, 2024 - November 12, 2026"], header]
    totals = []
    for year, month in months():
        label = "%s %d" % (MONTH_NAMES[month - 1], year)
        group = [r for r in rows if (r["year"], r["month"]) == (year, month)]
        for r in group:
            paused = r["campaign"] == PROMO
            out.append([label, "Paused" if paused else "Enabled", r["campaign"], fmt(r["budget"]), DASH, "Daily", "USD", "Paused" if paused else "Eligible", DASH,
                        "Search", r["strategy"], fmt(r["cost"]), fmt(r["impressions"], 0), fmt(r["clicks"], 0), pct(r["clicks"] / r["impressions"]),
                        fmt(r["cost"] / r["clicks"]), banded(r["share"]), lost(r, "lost_rank"), lost(r, "lost_budget"),
                        pct(r["conversions"] / r["clicks"]), fmt(r["conversions"]), fmt(r["cost"] / r["conversions"])])
        cost, impr, clicks, conv = (sum(r[k] for r in group) for k in ("cost", "impressions", "clicks", "conversions"))
        for name in ("Total: Filtered campaigns", "Total: Account", "Total: Search"):
            totals.append([label, name, DASH, DASH, DASH, DASH, "USD", DASH, DASH, DASH, DASH, fmt(cost), fmt(impr, 0), fmt(clicks, 0), pct(clicks / impr),
                           fmt(cost / clicks), DASH, DASH, DASH, pct(conv / clicks), fmt(conv), fmt(cost / conv)])
    # Segmented totals start with the period and carry the label in the second column.
    out += totals
    return out


# domain: {month: (impression share, overlap, position above, top of page, abs. top, outranking share)}
def competitor_table(scope, you_share):
    steady = lambda a, b, c, d, e, f: {m: (a, b, c, d, e, f) for m in range(5, 12)}  # noqa: E731
    if scope == "Account":
        table = {
            "milehighplumbing.example": steady("39.10%", "47.20%", "33.40%", "58.10%", "20.30%", "41.20%"),
            "frontrangedrains.example": steady("21.40%", "18.30%", "25.10%", "49.80%", "14.20%", "52.40%"),
            "waterheaterdepot.example": steady("12.20%", "11.40%", "28.70%", "52.10%", "17.00%", "48.80%"),
            "bluepipeplumbing.example": steady("< 10%", "6.10%", "18.20%", "40.20%", "9.80%", "57.30%"),
            "homeservicesdirectory.example": {m: ("15.30%", "14.10%", "36.20%", "66.40%", "24.10%", "39.90%") for m in range(5, 10)},
            "rapidrooter.example": {9: ("< 10%", "8.90%", "58.00%", "71.00%", "38.00%", "30.10%"), 10: ("18.60%", "16.20%", "61.30%", "72.50%", "39.40%", "28.20%"),
                                    11: ("21.00%", "17.80%", "62.00%", "73.10%", "40.20%", "27.50%")},
        }
        top, abstop = "55.20%", "22.10%"
    elif scope == EMERGENCY:
        table = {
            "milehighplumbing.example": steady("41.30%", "52.10%", "35.20%", "60.20%", "21.10%", "40.10%"),
            "homeservicesdirectory.example": {m: ("17.10%", "16.20%", "37.10%", "67.20%", "25.30%", "38.20%") for m in range(5, 10)},
            "bluepipeplumbing.example": steady("< 10%", "7.20%", "19.10%", "41.10%", "10.20%", "56.10%"),
            "rapidrooter.example": {8: ("< 10%", "9.10%", "44.20%", "68.10%", "31.20%", "36.40%"), 9: ("21.40%", "20.30%", "55.60%", "70.40%", "36.10%", "31.20%"),
                                    10: ("33.80%", "31.20%", "63.10%", "73.20%", "40.10%", "26.30%"), 11: ("35.00%", "32.40%", "63.80%", "73.90%", "41.00%", "25.80%")},
        }
        top = {9: "52.30%", 10: "48.60%", 11: "48.00%"}
        abstop = {9: "19.20%", 10: "15.80%", 11: "15.50%"}
    else:
        table = {
            "waterheaterdepot.example": steady("36.20%", "35.10%", "30.20%", "55.10%", "18.20%", "45.20%"),
            "milehighplumbing.example": steady("38.40%", "40.20%", "32.10%", "57.20%", "19.40%", "42.30%"),
            "bluepipeplumbing.example": steady("< 10%", "5.40%", "17.20%", "39.10%", "9.10%", "58.20%"),
        }
        top, abstop = "53.40%", "20.80%"
    rng = random.Random(len(scope))
    out = []
    for month in range(5, 12):
        mark = lambda v, default: v.get(month, default) if isinstance(v, dict) else v  # noqa: E731
        out.append([month, "You", you_share[month], DASH, DASH, jitter(mark(top, "57.10%"), rng), jitter(mark(abstop, "23.40%"), rng), DASH])
        for domain, values in table.items():
            if month in values:
                out.append([month, domain] + [jitter(v, rng) for v in values[month]])
    return out


def jitter(text, rng):
    """Real shares move a little from month to month."""
    if text.startswith("<"):
        return text
    return "%.2f%%" % max(0.0, float(text.rstrip("%")) + rng.uniform(-0.9, 0.9))


def auction_report(rows, scope):
    def you(month):
        group = [r for r in rows if (r["year"], r["month"]) == (2026, month) and (scope == "Account" or r["campaign"] == scope)]
        return pct(sum(r["impressions"] for r in group) / sum(r["impressions"] / r["share"] for r in group))
    header = ["Month", "Display URL domain", "Impression share", "Overlap rate", "Position above rate", "Top of page rate", "Abs. top of page rate", "Outranking share"]
    out = [["Auction insights report"], ["May 1, 2026 - November 12, 2026"], header]
    for line in competitor_table(scope, {m: you(m) for m in range(5, 12)}):
        out.append(["2026-%02d-01" % line[0]] + line[1:])
    return out


def write(name, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(20261113)
    rows = build_rows(rng)
    write("campaigns-by-month.csv", campaign_report(rows))
    write("auction-insights-account-by-month.csv", auction_report(rows, "Account"))
    write("auction-insights-emergency-by-month.csv", auction_report(rows, EMERGENCY))
    write("auction-insights-water-heaters-by-month.csv", auction_report(rows, HEATERS))
    print("Wrote the samples to %s" % OUT)


if __name__ == "__main__":
    main()
