#!/usr/bin/env python3
"""Write synthetic inputs for the Performance Max skill to examples/exports/performance-max/.

Northside Plumbing runs its Search campaigns plus three Performance Max
campaigns: an online supply shop with a Merchant Center feed, a lead campaign
for water heater installs that is still learning, and a paused spring promo.
The files are laid out the way Google Ads downloads them. Planted problems:

- Brand searches take a large share of Performance Max search conversions.
- The asset group "Water Heaters | General" is rated Poor and carries heavy
  spend. "Drain Tools" is rated Average.
- Drain tools spend with no conversions, and are priced above their benchmark.
- A trap: the Google Display Network costs more per conversion than the whole.
  The review must raise it as a question, never as a cut.

    python3 dev/samples/make_samples_performance-max.py
"""
import csv
import os
import random

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples")
OUT = os.path.join(ROOT, "exports", "performance-max")
RANGE = "October 14, 2026 - November 12, 2026"
SHOP, LEADS, PROMO = "PMax | Plumbing Supplies", "PMax | Water Heater Leads", "PMax | Spring Promo"
DASH = " --"


def fmt(value, places=2):
    return "{:,.{p}f}".format(value, p=places)


def write(name, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def clicks_for(rng, cost, cpc=(0.9, 2.4)):
    clicks = int(cost / rng.uniform(*cpc)) if cost else 0
    return clicks, clicks * rng.randint(18, 40) if cost else 0


def campaigns_report(rng):
    header = ["Campaign status", "Campaign", "Budget", "Budget name", "Budget type", "Currency code", "Status", "Status reasons", "Campaign type",
              "Bid strategy type", "Cost", "Impr.", "Clicks", "Conversions", "Conv. value"]
    specs = [
        ("Enabled", "Plumbing | Emergency", 240.0, "Eligible", "Search", "Maximize Conversions", 6850.40, 61.0, 0.0),
        ("Enabled", "Plumbing | Water Heaters", 160.0, "Eligible", "Search", "Target CPA", 4410.75, 38.0, 0.0),
        ("Enabled", "Drain Cleaning | Search", 90.0, "Eligible", "Search", "Maximize Conversions", 2480.10, 29.0, 0.0),
        ("Enabled", "Brand", 40.0, "Eligible", "Search", "Maximize clicks", 905.30, 74.0, 0.0),
        ("Enabled", SHOP, 330.0, "Eligible", "Performance Max", "Maximize conversion value", 9450.00, 104.0, 35810.00),
        ("Enabled", LEADS, 170.0, "Eligible (Learning)", "Performance Max", "Maximize Conversions", 4800.00, 28.0, 0.0),
        ("Paused", PROMO, 50.0, "Paused", "Performance Max", "Maximize Conversions", 120.00, 1.0, 0.0),
    ]
    rows, sums = [], {}
    for status, name, budget, serving, ctype, strategy, cost, conv, value in specs:
        clicks, impr = clicks_for(rng, cost, (3.5, 8.0) if ctype == "Search" else (0.9, 2.4))
        for key in ("Account", ctype):
            s = sums.setdefault(key, [0.0, 0, 0, 0.0, 0.0])
            sums[key] = [s[0] + cost, s[1] + impr, s[2] + clicks, s[3] + conv, s[4] + value]
        rows.append([status, name, fmt(budget), DASH, "Daily", "USD", serving, DASH, ctype, strategy, fmt(cost), fmt(impr, 0), fmt(clicks, 0), fmt(conv), fmt(value)])

    def total(label, s):
        return [DASH, label, DASH, DASH, DASH, "USD", DASH, DASH, DASH, DASH, fmt(s[0]), fmt(s[1], 0), fmt(s[2], 0), fmt(s[3]), fmt(s[4])]
    write("campaigns-report.csv", [["Campaign report"], [RANGE], header] + rows +
          [total("Total: Account", sums["Account"]), total("Total: Search", sums["Search"]), total("Total: Performance Max", sums["Performance Max"])])


def asset_groups_report(rng):
    header = ["Asset group status", "Asset group", "Campaign", "Status", "Ad strength", "Currency code", "Impr.", "Clicks", "Cost", "Conversions", "Conv. value"]
    specs = [
        ("Enabled", "Water Heaters | Shop", SHOP, "Eligible", "Good", 3600.00, 40.0, 22000.00),
        ("Enabled", "Faucets and Fixtures", SHOP, "Eligible", "Excellent", 2700.00, 52.0, 12500.00),
        ("Enabled", "Drain Tools", SHOP, "Eligible", "Average", 2100.00, 3.0, 210.00),
        ("Enabled", "Pipe Fittings", SHOP, "Eligible", "Good", 600.00, 9.0, 1100.00),
        ("Enabled", "Clearance", SHOP, "Eligible", "Good", 450.00, 0.0, 0.00),
        ("Enabled", "Water Heaters | General", LEADS, "Eligible", "Poor", 2900.00, 6.0, 0.00),
        ("Enabled", "Tankless Install", LEADS, "Eligible", "Good", 1900.00, 22.0, 0.00),
        ("Enabled", "Boiler Service", LEADS, "Eligible", "Good", 0.00, 0.0, 0.00),
        ("Enabled", "Spring Promo | All", PROMO, "Campaign paused", "Pending", 120.00, 1.0, 0.00),
    ]
    rows, s = [], [0, 0, 0.0, 0.0, 0.0]
    for state, name, campaign, serving, strength, cost, conv, value in specs:
        clicks, impr = clicks_for(rng, cost)
        s = [s[0] + impr, s[1] + clicks, s[2] + cost, s[3] + conv, s[4] + value]
        rows.append([state, name, campaign, serving, strength, "USD", fmt(impr, 0), fmt(clicks, 0), fmt(cost), fmt(conv), fmt(value)])
    write("asset-groups-report.csv", [["Asset group report"], [RANGE], header] + rows +
          [["Total: Account", DASH, DASH, DASH, DASH, "USD", fmt(s[0], 0), fmt(s[1], 0), fmt(s[2]), fmt(s[3]), fmt(s[4])]])


def channel_report(rng):
    header = ["Campaign", "Channel", "Status", "Currency code", "Impr.", "Interactions", "Cost", "Conversions", "Conv. value"]
    specs = {
        SHOP: [("Google Search", 5200.00, 69.0, 25000.00), ("Search partners", 300.00, 3.0, 900.00), ("Google Display Network", 2100.00, 6.0, 2000.00),
               ("YouTube", 1200.00, 13.0, 4800.00), ("Discover", 450.00, 8.0, 2110.00), ("Gmail", 200.00, 5.0, 1000.00), ("Maps", 0.0, 0.0, 0.0)],
        LEADS: [("Google Search", 2600.00, 18.0, 0.0), ("Search partners", 100.00, 1.0, 0.0), ("Google Display Network", 1300.00, 3.0, 0.0),
                ("YouTube", 600.00, 4.0, 0.0), ("Discover", 150.00, 1.0, 0.0), ("Gmail", 50.00, 1.0, 0.0), ("Maps", 0.0, 0.0, 0.0)],
        PROMO: [("Google Search", 80.00, 1.0, 0.0), ("Google Display Network", 40.00, 0.0, 0.0)],
    }
    rows, s = [], [0, 0, 0.0, 0.0, 0.0]
    for campaign, channels in specs.items():
        for channel, cost, conv, value in channels:
            clicks, impr = clicks_for(rng, cost)
            status = "Eligible (Limited)" if channel == "Discover" and campaign == SHOP else "Eligible"
            s = [s[0] + impr, s[1] + clicks, s[2] + cost, s[3] + conv, s[4] + value]
            rows.append([campaign, channel, status, "USD", fmt(impr, 0), fmt(clicks, 0), fmt(cost), fmt(conv), fmt(value)])
    write("channel-performance.csv", [["Channel performance report"], [RANGE], header] + rows +
          [[DASH, "Total: Performance Max", DASH, "USD", fmt(s[0], 0), fmt(s[1], 0), fmt(s[2]), fmt(s[3]), fmt(s[4])]])


def search_terms_report(rng):
    header = ["Search term", "Match type", "Added/Excluded", "Campaign", "Ad group", "Keyword", "Currency code", "Clicks", "Impr.", "Cost",
              "Campaign type", "Conversions", "Conv. value"]
    pmax = [
        # Planted: brand searches carry a large share of Performance Max search conversions.
        ("northside plumbing", SHOP, 420.00, 22.0, 3900.00), ("northside plumbing supply", SHOP, 310.00, 16.0, 2800.00),
        ("northside plumbing near me", LEADS, 150.00, 6.0, 0.0),
        ("tankless water heater 50 gallon", SHOP, 640.00, 9.0, 5400.00), ("rheem water heater 40 gallon", SHOP, 520.00, 7.0, 4100.00),
        ("kitchen faucet with sprayer", SHOP, 380.00, 11.0, 2300.00), ("pipe fittings near me", SHOP, 85.00, 2.0, 180.00),
        ("water heater installation near me", LEADS, 900.00, 10.0, 0.0), ("water heater replacement cost", LEADS, 420.00, 3.0, 0.0),
        ("tankless water heater installer", LEADS, 380.00, 5.0, 0.0),
        # Spend with no conversions: some relevant, some never for this business.
        ("drain snake 25 ft", SHOP, 260.00, 0.0, 0.0), ("toilet auger", SHOP, 190.00, 0.0, 0.0),
        ("how to unclog a drain without a snake", SHOP, 140.00, 0.0, 0.0), ("plumbing jobs near me", SHOP, 110.00, 0.0, 0.0),
        ("plumber jobs denver", LEADS, 95.00, 0.0, 0.0), ("water heater repair jobs", LEADS, 60.00, 0.0, 0.0),
        ("free water heater", SHOP, 70.00, 0.0, 0.0), ("water heater diy install", SHOP, 120.00, 0.0, 0.0),
        ("diy drain cleaning", SHOP, 75.00, 0.0, 0.0), ("pex fittings", SHOP, 20.00, 0.0, 0.0), ("faucet aerator", SHOP, 15.00, 0.0, 0.0),
    ]
    search = [("emergency plumber", "Plumbing | Emergency", 820.00, 9.0), ("24 hour plumber", "Plumbing | Emergency", 410.00, 4.0),
              ("water heater repair", "Plumbing | Water Heaters", 530.00, 5.0), ("northside plumbing", "Brand", 120.00, 11.0)]
    rows, sums = [], {}
    unlisted = {"Performance Max": 1250.00, "Search": 380.00}
    for term, campaign, cost, conv, value in pmax:
        clicks, impr = clicks_for(rng, cost)
        rows.append([term, DASH, "None", campaign, DASH, DASH, "USD", fmt(clicks, 0), fmt(impr, 0), fmt(cost), "Performance Max", fmt(conv), fmt(value)])
        for key in ("Account", "Performance Max"):
            sums[key] = sums.get(key, 0.0) + cost
    for term, campaign, cost, conv in search:
        clicks, impr = clicks_for(rng, cost, (3.5, 8.0))
        rows.append([term, "Phrase match", "None", campaign, "Main", '"%s"' % term, "USD", fmt(clicks, 0), fmt(impr, 0), fmt(cost), "Search", fmt(conv), "0.00"])
        for key in ("Account", "Search"):
            sums[key] = sums.get(key, 0.0) + cost
    sums["Account"] += sum(unlisted.values())
    for key, extra in unlisted.items():
        sums[key] += extra

    def total(label):
        return [label, DASH, DASH, DASH, DASH, DASH, "USD", DASH, DASH, fmt(sums[label.split(": ")[1]]), DASH, DASH, DASH]
    write("search-terms-report.csv", [["Search terms report"], [RANGE], header] + rows +
          [total("Total: Account"), total("Total: Search"), total("Total: Performance Max")])


PRODUCTS = [
    # item id, title, brand, product type, custom label 0, cost, conversions, conv. value, your price, benchmark
    ("ns-wh-001", "Rheem 40 Gallon Gas Water Heater", "Rheem", "Water Heaters", "bestseller", 1180.00, 14.0, 8120.00, 579.00, 565.00),
    ("ns-wh-002", "Rheem 50 Gallon Electric Water Heater", "Rheem", "Water Heaters", "bestseller", 960.00, 10.0, 6290.00, 629.00, 640.00),
    ("ns-wh-003", "Rinnai Tankless Water Heater 199k BTU", "Rinnai", "Water Heaters", "", 880.00, 6.0, 7140.00, 1249.00, 1110.00),
    ("ns-wh-004", "A.O. Smith 40 Gallon Water Heater", "A.O. Smith", "Water Heaters", "", 520.00, 4.0, 2280.00, 569.00, 572.00),
    ("ns-wh-005", "Navien Tankless Water Heater", "Navien", "Water Heaters", "", 410.00, 2.0, 2650.00, 1399.00, 1320.00),
    ("ns-fx-001", "Moen Kitchen Faucet with Pull Down Sprayer", "Moen", "Faucets", "bestseller", 690.00, 16.0, 3360.00, 209.00, 215.00),
    ("ns-fx-002", "Delta Single Handle Bathroom Faucet", "Delta", "Faucets", "bestseller", 540.00, 13.0, 1690.00, 129.00, 131.00),
    ("ns-fx-003", "Kohler Shower Head 2.5 GPM", "Kohler", "Faucets", "", 380.00, 9.0, 890.00, 99.00, 99.00),
    ("ns-fx-004", "Moen Bathroom Sink Drain Assembly", "Moen", "Faucets", "", 210.00, 6.0, 330.00, 54.00, 49.00),
    ("ns-fx-005", "Delta Faucet Cartridge", "Delta", "Faucets", "", 95.00, 4.0, 150.00, 37.00, 38.00),
    # Planted: drain tools spend with no conversions and sit above their benchmark.
    ("ns-dt-001", "RIDGID 25 ft Drain Snake", "RIDGID", "Drain Tools", "clearance", 420.00, 0.0, 0.00, 89.00, 72.00),
    ("ns-dt-002", "Cobra Toilet Auger 6 ft", "Cobra", "Drain Tools", "clearance", 330.00, 0.0, 0.00, 54.00, 44.00),
    ("ns-dt-003", "Drain Cleaning Machine 50 ft", "RIDGID", "Drain Tools", "", 290.00, 0.0, 0.00, 449.00, 379.00),
    ("ns-dt-004", "Sink Drain Auger 15 ft", "Cobra", "Drain Tools", "", 240.00, 0.0, 0.00, 32.00, 26.00),
    ("ns-dt-005", "Drain Hair Catcher 2 Pack", "Northside", "Drain Tools", "", 160.00, 1.0, 18.00, 14.00, 12.00),
    ("ns-dt-006", "Plunger and Auger Combo", "Cobra", "Drain Tools", "", 130.00, 0.0, 0.00, 39.00, 33.00),
    ("ns-pf-001", "SharkBite 1/2 in Push Fitting 10 Pack", "SharkBite", "Pipe Fittings", "", 140.00, 4.0, 280.00, 64.00, 66.00),
    ("ns-pf-002", "PEX Crimp Ring 100 Pack", "Apollo", "Pipe Fittings", "", 85.00, 2.0, 96.00, 29.00, 29.00),
    # Planted: two products with no brand and no product type.
    ("ns-pf-003", "Copper Elbow 3/4 in 25 Pack", "", "", "", 70.00, 1.0, 55.00, 47.00, 45.00),
    ("ns-pf-004", "Brass Ball Valve 1/2 in", "", "", "", 45.00, 0.0, 0.00, 18.00, 19.00),
    ("ns-pf-005", "PVC Primer and Cement Kit", "Oatey", "Pipe Fittings", "", 0.00, 0.0, 0.00, 16.00, None),
    ("ns-pf-006", "Thread Seal Tape 10 Pack", "Oatey", "Pipe Fittings", "", 0.00, 0.0, 0.00, 9.00, None),
]


def products_report(rng):
    header = ["Item ID", "Title", "Brand", "Product type (1st level)", "Custom label 0", "Campaign", "Currency code", "Impr.", "Clicks", "Cost", "Conversions", "Conv. value"]
    rows, s = [], [0, 0, 0.0, 0.0, 0.0]
    for item, title, brand, ptype, label, cost, conv, value, _, _ in PRODUCTS:
        clicks, impr = clicks_for(rng, cost)
        s = [s[0] + impr, s[1] + clicks, s[2] + cost, s[3] + conv, s[4] + value]
        rows.append([item, title, brand or DASH, ptype or DASH, label or DASH, SHOP, "USD", fmt(impr, 0), fmt(clicks, 0), fmt(cost), fmt(conv), fmt(value)])
    write("products-report.csv", [["Products report"], [RANGE], header] + rows +
          [["Total: Account", DASH, DASH, DASH, DASH, DASH, "USD", fmt(s[0], 0), fmt(s[1], 0), fmt(s[2]), fmt(s[3]), fmt(s[4])]])


def price_benchmarks():
    # Merchant Center's own layout is not confirmed. One header row, IDs in the channel:language:country:id form.
    header = ["Product ID", "Title", "Brand", "Your price", "Benchmark", "Price gap", "Clicks"]
    rows = []
    for item, title, brand, _, _, _, _, _, price, bench in PRODUCTS:
        if bench is None:
            continue
        rows.append(["online:en:US:%s" % item.upper(), title, brand or DASH, fmt(price), fmt(bench), "%.1f%%" % ((price / bench - 1) * 100), str(random.Random(item).randint(5, 300))])
    write("price-benchmarks.csv", [header] + rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(20261113)
    campaigns_report(rng)
    asset_groups_report(rng)
    channel_report(rng)
    search_terms_report(rng)
    products_report(rng)
    price_benchmarks()
    print("Wrote the samples to %s" % OUT)


if __name__ == "__main__":
    main()
