#!/usr/bin/env python3
"""Performance Max and Shopping review: run every check the exports allow.

Give whichever reports you have. The script runs the checks those files
allow, lists every check it could not run with the report that would unlock
it, and writes pmax-review.json, pmax-review.xlsx and pmax-review.md.

    python3 scripts/audit.py --out OUTPUT [--campaigns CAMPAIGN_REPORT] [--asset-groups ASSET_GROUP_REPORT]
        [--channels CHANNEL_REPORT] [--search-terms SEARCH_TERMS_REPORT] [--products PRODUCTS_REPORT]
        [--prices PRICE_BENCHMARKS] [--brand "acme, acme shop"] [--target-cpa 40] [--target-roas 400]
        [--campaign "PMax | Shop"]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics  # noqa: E402
import pmax_data as data  # noqa: E402
import pmax_write as write  # noqa: E402

KIND_ORDER = ("Data check", "Spend with no conversions", "Setup risk", "Question")
NO_RETURN = "Spend with no conversions"
TITLES = {"campaigns": "Campaign report", "asset_groups": "Asset group report", "channels": "Channel performance report",
          "search_terms": "Search terms report", "products": "Products report", "prices": "Price benchmark report"}


def money(value):
    return metrics.money(value)


def names(items, limit=5):
    shown = ", ".join(items[:limit])
    return shown + (", and %d more" % (len(items) - limit) if len(items) > limit else "")


def check_campaign_names(chosen, loaded):
    """Refuse a campaign name that is not in any of the reports."""
    known = set()
    for kind, (meta, rows) in loaded.items():
        if "campaign" in meta["columns"]:
            known |= {r["campaign"] for r in rows if r.get("campaign")}
    if "campaigns" in loaded and "campaign_type" in loaded["campaigns"][0]["columns"]:
        known = {r["campaign"] for r in loaded["campaigns"][1] if r.get("campaign") and "performance max" in (r.get("campaign_type") or "").lower()}
    if not known:
        data.plain_exit("None of these reports has a Campaign column, so --campaign can't be checked. Run without it.")
    wrong = [c for c in chosen if c not in known]
    if wrong:
        data.plain_exit('I can\'t find the campaign "%s" in these reports. The campaigns they name are: %s.' % (wrong[0], ", ".join(sorted(known))))


def consistency(parts, metas):
    camp = parts.get("campaigns")
    camp_cost = {c["campaign"]: c["cost"] for c in camp["campaigns"]} if camp else {}
    rows = []
    for kind in ("campaigns", "asset_groups", "channels", "search_terms", "products"):
        part = parts.get(kind)
        if not part:
            continue
        row = {"report": TITLES[kind], "date_range": metas[kind]["date_range"], "cost": part["total"]["cost"],
               "conversions": part["total"]["conversions"], "compare_to": "", "compare_cost": None, "difference": None, "share": None, "expect": ""}
        if kind in ("asset_groups", "channels", "products") and camp:
            covered = None
            if kind == "asset_groups" and part["has_campaign"]:
                covered = [s["campaign"] for s in part["by_campaign"]]
            elif kind == "channels" and part["has_campaign"]:
                covered = sorted({c["campaign"] for c in part["per_campaign"]})
            elif kind == "products" and part["campaigns"]:
                covered = part["campaigns"]
            pool = [n for n in covered if n in camp_cost] if covered is not None else list(camp_cost)
            row["compare_to"] = "Campaign report cost of the same Performance Max campaigns" if covered is not None else "Performance Max cost in the campaign report"
            row["compare_cost"] = sum(camp_cost[n] for n in pool)
            row["expect"] = "part" if kind == "products" else "equal"
        if kind == "search_terms":
            if parts.get("channels"):
                row["compare_to"], row["compare_cost"] = "Google Search and Search partners cost in the channel report", parts["channels"]["search_cost"]
            elif camp:
                row["compare_to"], row["compare_cost"] = "Performance Max cost in the campaign report", camp["total"]["cost"]
            row["expect"] = "part"
            if not part["has_cost"]:
                row["cost"] = None
        if row["compare_cost"] is not None and row["cost"] is not None:
            row["difference"] = round(row["cost"] - row["compare_cost"], 2)
            row["share"] = metrics.div(row["cost"], row["compare_cost"])
        rows.append(row)
    per_campaign = []
    if camp:
        ag = {s["campaign"]: s["cost"] for s in parts["asset_groups"]["by_campaign"]} if parts.get("asset_groups") and parts["asset_groups"]["has_campaign"] else None
        ch = None
        if parts.get("channels") and parts["channels"]["has_campaign"]:
            ch = {}
            for c in parts["channels"]["per_campaign"]:
                ch[c["campaign"]] = ch.get(c["campaign"], 0.0) + c["cost"]
        for c in camp["campaigns"]:
            per_campaign.append({"campaign": c["campaign"], "state": c["state"], "campaign_cost": c["cost"],
                                 "asset_group_cost": ag.get(c["campaign"]) if ag is not None else None,
                                 "channel_cost": ch.get(c["campaign"]) if ch is not None else None})
    ranges = sorted({tuple(metas[k]["date_range"]) for k in metas if metas[k]["date_range"] and k != "prices"})
    return {"reports": rows, "per_campaign": per_campaign, "date_ranges_differ": len(ranges) > 1, "date_ranges": [list(r) for r in ranges]}


def build_findings(parts, cons, brand_phrases):
    found = []

    def add(area, kind, title, detail, cost, surface, label, rule, no_fix=False):
        found.append({"area": area, "kind": kind, "title": title, "detail": detail, "cost": cost, "surface": surface,
                      "label": label, "rule": rule, "no_fix": no_fix})

    if cons["date_ranges_differ"]:
        add("All reports", "Data check", "The reports cover different dates",
            "Date ranges found: %s. Comparisons between reports are approximate." % "; ".join("%s to %s" % (a, b) for a, b in cons["date_ranges"]),
            None, "Download every report for the same date range", "Practitioner rule", "Reconcile the evidence before declaring waste.")
    for row in cons["reports"]:
        if row["expect"] == "equal" and row["difference"] is not None and abs(row["difference"]) >= data.ROUNDING:
            add(row["report"], "Data check", "%s does not add up to the campaign report" % row["report"],
                "%s adds up to %s. %s is %s. The difference is %s." % (row["report"], money(row["cost"]), row["compare_to"], money(row["compare_cost"]), money(row["difference"])),
                abs(row["difference"]), "Date range and filters of the two downloads", "Practitioner rule", "Reconcile the evidence before declaring waste.")
    camp = parts.get("campaigns")
    learning = set(camp["learning"]) if camp else set()
    not_serving = {c["campaign"] for c in camp["campaigns"] if c["state"] != "Enabled"} if camp else set()

    def tag(name, campaign):
        return name + (" (campaign still learning)" if campaign in learning else "")

    if camp:
        if camp["campaigns"] and camp["total"]["cost"] == 0:
            add("Campaigns", "Data check", "No Performance Max spend in this date range",
                "The campaign report lists %d Performance Max campaigns and none spent in this date range." % len(camp["campaigns"]), None,
                "Date range and campaign status", "Practitioner rule", "Explain status and date range before declaring waste from empty rows.")
        if camp["learning"]:
            add("Campaigns", "Data check", "Campaigns still learning", "Status shows learning for: %s. Read their numbers as early." % names(camp["learning"]),
                sum(c["cost"] for c in camp["campaigns"] if c["learning"]), "No change yet: judge them after the learning window", "Official",
                "Run a new campaign at least 6 weeks, and allow 1 to 2 weeks or one full conversion cycle after a significant change.")
        if camp["enabled_no_cost"]:
            add("Campaigns", "Setup risk", "Enabled campaigns with no cost", "Enabled with no cost in this period: %s." % names(camp["enabled_no_cost"]),
                None, "Campaign status and the Status column", "Practitioner rule", "An enabled campaign that does not spend is not serving on its own terms.")
    ag = parts.get("asset_groups")
    if ag:
        below = ag["below_good"]
        if below and below["groups"] and below["cost"] > 0:
            weak = [g for g in ag["groups"] if g["ad_strength"] in ("Average", "Poor")]
            add("Asset groups", "Setup risk", "Asset groups rated below Good carry spend",
                "%d asset groups rated Average or Poor carry %s, %s of the asset group report's cost: %s." % (
                    below["groups"], money(below["cost"]), metrics.pct(below["share_of_cost"]),
                    "; ".join("%s, %s, %s" % (tag(g["asset_group"], g["campaign"]), g["ad_strength"], money(g["cost"])) for g in weak[:5])),
                below["cost"], "Assets in those asset groups", "Official",
                "Google recommends Ad strength of Good or Excellent. Ad strength measures asset coverage and variety. It is not an auction input.")
        if ag["no_conv_over_line"]:
            groups = ag["no_conv_over_line"]
            add("Asset groups", NO_RETURN, "Asset groups that spent enough to judge with no conversions",
                "%s." % "; ".join("%s in %s: %s" % (tag(g["asset_group"], g["campaign"]), g["campaign"] or "its campaign", money(g["cost"])) for g in groups[:5]),
                metrics.total(groups, "cost"), "Assets, listing groups and final URL of those asset groups", "Practitioner rule",
                "Check the asset group's products, assets and landing page before pausing it.")
        if ag["enabled_no_cost"]:
            add("Asset groups", "Setup risk", "Enabled asset groups with no cost", "Enabled with no cost in this period: %s." % names(ag["enabled_no_cost"]),
                None, "Asset group status, listing groups and assets", "Practitioner rule", "An enabled asset group that does not spend is worth a look.")
    ch = parts.get("channels")
    if ch:
        for c in ch["with_issues"]:
            where = " in %s" % c["campaign"] if c.get("campaign") else ""
            add("Channels", "Setup risk", "%s%s shows a status issue" % (c["channel"], where), "%s%s has the status %s." % (c["channel"], where, " / ".join(c["issues"])), c["cost"],
                "Assets in the asset groups" if any("asset" in s.lower() for s in c["issues"]) else "The Status column of the channel performance report",
                "Official", "The channel performance report's Status column flags issues such as Missing required assets.")
        for c in ch["flags"]:
            if c.get("campaign") in not_serving:
                continue
            scope = c["campaign"] if c.get("campaign") else "the channel report"
            if c["basis"] == "conv. value":
                title = "%s returns less conv. value per cost than %s as a whole" % (c["channel"], scope)
                compare = "Its conv. value / cost is %s against %s." % ("{:,.2f}".format(c["roas"] or 0), "{:,.2f}".format(c["whole_roas"] or 0))
            else:
                title = "%s costs more per conversion than %s as a whole" % (c["channel"], scope)
                compare = "Its cost / conv. is %s against %s." % (money(c["cpa"]), money(c["whole_cpa"]))
            add("Channels", "Question", tag(title, c.get("campaign")),
                "In %s, %s has %s of the cost and %s of the %s in the channel report. %s" % (scope, c["channel"], metrics.pct(c["share_of_cost"]), metrics.pct(c["share_of_basis"]), c["basis"], compare),
                c["cost"], "The channel report's diagnostics and the assets that channel uses", "Official",
                "Performance Max optimises for marginal return across channels, so an average by channel can mislead. Judge the campaign against its goal. Do not cut a channel on this alone.",
                no_fix=True)
    st = parts.get("search_terms")
    if st:
        if st["brand"] and st["brand"]["searches"]:
            b = st["brand"]
            detail = "Brand searches are %s of the listed Performance Max search cost, %s of the listed conversions and %s of the listed conv. value in the search terms report." % (
                metrics.pct(b["share_of_cost"]), metrics.pct(b["share_of_conversions"]), metrics.pct(b["share_of_value"]))
            rule = ("Brand exclusions block brand terms on Search and Shopping, and Google prefers them over negatives for brand protection. "
                    "Practitioner rule: brand traffic is not waste without business context.")
            named = [c["campaign"] for c in (camp["search_campaigns"] if camp else []) if data.tokens_match(c["campaign"], brand_phrases)]
            overlap = {s["campaign"]: s for s in st["brand_in_search"]}
            for name in named:
                overlap.setdefault(name, {"campaign": name, "keywords": [], "brand_searches": 0})
            if overlap:
                bits = []
                for s in overlap.values():
                    why = []
                    if s["campaign"] in named:
                        why.append("its name holds a brand term")
                    if s["keywords"]:
                        why.append("its keywords include %s" % ", ".join(s["keywords"][:3]))
                    if s["brand_searches"] and not s["keywords"]:
                        why.append("it served %d brand searches" % s["brand_searches"])
                    bits.append("%s (%s)" % (s["campaign"], "; ".join(why)))
                detail += " Search campaigns that also carry the brand: %s." % ", ".join(bits)
                rule += (" Official (references/pmax.md): only a Search keyword in exact match identical to the search is preferred over Performance Max. "
                         "Identical phrase or broad keywords share the next priority with identical search themes, and a budget limited Search campaign lets Performance Max serve on exact terms at times.")
            add("Searches", "Question", "Brand searches inside Performance Max", detail,
                b["cost"] if st["has_cost"] else None, "Brand exclusions in the campaign settings, or exact match brand keywords in Search", "Official", rule)
        if st["has_cost"] and st["no_conv_terms"]:
            add("Searches", NO_RETURN, "Non brand searches with cost and no conversions",
                "%d non brand searches had cost and no conversions, costing %s, %s of the listed Performance Max search cost. %d of them spent at least %s, "
                "enough to judge on spend alone, costing %s. The other %d cost %s. Every one needs a relevance call before a negative is added." % (
                    len(st["no_conv_terms"]), money(st["no_conv"]["cost"]), metrics.pct(st["no_conv"]["share_of_cost"]), len(st["over_line"]),
                    money(st["line"]["value"]), money(st["over_line_cost"]), st["below_line"]["searches"], money(st["below_line"]["cost"])),
                st["over_line_cost"], "Negative keywords on the campaign", "Official",
                "Performance Max negative keywords apply to Search and Shopping inventory only, up to 10,000 per campaign, and do not match close variants.")
        if st["waste_words"]:
            top = st["waste_words"][:5]
            held = st["held_back_words"][:5]
            add("Searches", "Question", "Words in searches that never converted",
                "In two or more searches with cost and no conversions: %s. Candidates only: a word can be relevant to the business.%s" % (", ".join(
                    '"%s" (%s)' % (g["phrase"], money(g["cost"])) for g in top),
                    " Held back because every word appears in a product title, asset group name or campaign name: %s." % ", ".join(
                        '"%s"' % g["phrase"] for g in held) if held else ""),
                top[0]["cost"], "Negative keywords on the campaign", "Practitioner rule", "Check every search that holds the word before excluding it.")
    pr = parts.get("products")
    pc = parts.get("prices")
    above_keys = {r["key"] for r in pc["rows"] if r["position"] == "Above benchmark"} if pc else set()
    if pr:
        if pr["over_line"]:
            types = [g for g in pr["groups"].get("product_type", []) if g["no_conv_cost"] > 0]
            types.sort(key=lambda g: -g["no_conv_cost"])
            lead = (" The largest share sits in product type %s, %s of the products report's cost with no conversions." % (types[0]["value"], metrics.pct(types[0]["share_of_no_conv_cost"]))) if types else ""
            overlap = [x for x in pr["over_line"] if x["key"] in above_keys]
            if overlap:
                lead += " %d of those that spent enough to judge are priced above their benchmark, carrying %s." % (len(overlap), money(metrics.total(overlap, "cost")))
            add("Products", NO_RETURN, "Products with cost and no conversions",
                "%d products had cost and no conversions, costing %s, %s of the products report's cost. %d of them spent at least %s, enough to judge on spend alone, "
                "costing %s.%s" % (
                    pr["no_conv"]["products"], money(pr["no_conv"]["cost"]), metrics.pct(pr["no_conv"]["share_of_cost"]), len(pr["over_line"]),
                    money(pr["line"]["value"]) if pr["line"]["value"] else "something", money(pr["over_line_cost"]), lead),
                pr["over_line_cost"], "Price, listing groups, or the product data in Merchant Center", "Practitioner rule",
                "When the problem is product or feed led, act on the feed or listing groups before changing bids. Check price first where a product is above its benchmark.")
        for gap in pr["gaps"]:
            label = gap["attribute"]
            if gap["cost"] > 0 and not label.startswith("Custom label"):
                add("Products", "Setup risk", "%s is blank on products that spend" % label,
                    "%s is blank for %d products carrying %s, %s of the products report's cost." % (label, gap["products"], money(gap["cost"]), metrics.pct(gap["share_of_cost"])),
                    gap["cost"], "Product data in Merchant Center", "Practitioner rule",
                    "Fill required and high signal attributes before chasing title experiments.")
        flagged = [s for s in pr["status"] if s["cost"] > 0 and (s["with_issues"] or s["status"].strip().lower() not in ("eligible", "approved", "active", "(blank)"))]
        for s in flagged:
            add("Products", "Setup risk", "Products with status %s" % s["status"],
                "%d products with status %s carry %s%s." % (s["products"], s["status"], money(s["cost"]), ", %d of them with listed issues" % s["with_issues"] if s["with_issues"] else ""),
                s["cost"], "Merchant Center diagnostics", "Official", "Retail diagnostics start with Merchant Center linkage, product data status and product issues.")
        if pr["below_target_roas"]:
            low = pr["below_target_roas"]
            add("Products", "Question", "Products below the target ROAS",
                "%d products spent at least %s with a ROAS below the target of %s, costing %s." % (
                    len(low), money(pr["line"]["value"]) if pr["line"]["value"] else "something", metrics.pct(pr["target_roas"], 0), money(metrics.total(low, "cost"))),
                metrics.total(low, "cost"), "Listing groups, or custom labels that split these products out", "Practitioner rule",
                "Use custom labels for business slicing and bidding logic. They do not raise rank by themselves.")
    if pc and pc["above"]["products"]:
        above = next((g for g in pc["groups"] if g["position"] == "Above benchmark"), None)
        rest = [g for g in pc["groups"] if g["position"] in ("At benchmark", "Below benchmark")]
        rest_rate = metrics.div(sum(g["conversions"] for g in rest), sum(g["clicks"] for g in rest))
        detail = "%d products are priced above their benchmark" % pc["above"]["products"]
        if pc["with_performance"]:
            detail += ", carrying %s, %s of the cost on products with a benchmark. Conv. rate is %s above benchmark and %s at or below it." % (
                money(pc["above"]["cost"]), metrics.pct(pc["above"]["share_of_priced_cost"]), metrics.pct(above["conv_rate"], 2), metrics.pct(rest_rate, 2))
            if pc["above_no_conv"]["products"]:
                detail += " %d of them spent with no conversions, costing %s." % (pc["above_no_conv"]["products"], money(pc["above_no_conv"]["cost"]))
        else:
            detail += "."
        add("Prices", "Question", "Products priced above benchmark", detail, pc["above"]["cost"] if pc["with_performance"] else None,
            "Price in Merchant Center, or how hard listing groups push these products", "Practitioner rule",
            "Separate price pressure from ad rank or creative pressure before acting. A benchmark needs a valid GTIN.")
    found.sort(key=lambda f: (KIND_ORDER.index(f["kind"]), -(f["cost"] or 0)))
    for number, f in enumerate(found, start=1):
        f["id"] = "F%d" % number
    return found


def against_targets(camp, target_cpa, target_roas):
    """Set each campaign's target by its own goal, and how far it sits from it.

    A lead campaign (cost / conv.) is set against the target cost per conversion, a retail one (conv. value / cost) against the
    target ROAS. The person's target comes first; the campaign's own Target CPA or Target ROAS column is used only when no target
    was given. Gap is the campaign's number divided by the target, minus one; "worse" and "better" follow the goal's direction.
    """
    for c in camp["campaigns"]:
        value_goal = c["goal"] == "conv. value / cost"
        yours = target_roas if value_goal else target_cpa
        own = c.get("target_roas") / 100.0 if value_goal and c.get("target_roas") else c.get("target_cpa") if not value_goal else None
        target, source = (yours, "yours") if yours else (own, "campaign setting") if own else (None, "")
        c["target"], c["target_source"], c["target_conflict"] = target, source, bool(yours and own and abs(yours - own) > 0.005)
        c["campaign_target"] = own
        actual = c["roas"] if value_goal else c["cpa"]
        c["gap_to_target"] = metrics.div(actual, target) - 1 if target and actual is not None else None
        if c.get("state") and c["state"] != "Enabled":
            c["against_target"] = "%s, not judged" % c["state"].lower()
        elif not target:
            c["against_target"] = "no target given"
        elif actual is None:
            c["against_target"] = "no conversions yet"
        else:
            gap = c["gap_to_target"]
            worse = gap < 0 if value_goal else gap > 0
            c["against_target"] = "on target" if abs(gap) < 0.0005 else "%s than target by %s" % ("worse" if worse else "better", metrics.pct(abs(gap)))
        if c.get("learning") and target:
            c["against_target"] += " (still learning)"


def build_checks(parts, args):
    checks = []

    def add(name, ran, used="", unlock="", note=""):
        checks.append({"check": name, "status": ran, "used": used, "unlock": unlock, "note": note})

    camp, ag, ch, st, pr, pc = (parts.get(k) for k in ("campaigns", "asset_groups", "channels", "search_terms", "products", "prices"))
    others = [k for k in ("asset_groups", "channels", "search_terms", "products") if parts.get(k)]
    if camp and others:
        add("Evidence consistency across reports", "Ran", "Campaign report and " + ", ".join(TITLES[k].lower() for k in others))
    else:
        add("Evidence consistency across reports", "Not run", unlock=data.UNLOCK["campaigns"] + ", plus at least one other report")
    add("Campaign inventory, status and learning", "Ran" if camp else "Not run", "Campaign report" if camp else "", "" if camp else data.UNLOCK["campaigns"])
    add("Channel mix: share of cost and conversions by channel", "Ran" if ch else "Not run", "Channel performance report" if ch else "", "" if ch else data.UNLOCK["channels"])
    if ag:
        add("Asset groups by spend", "Ran", "Asset group report")
        add("Spend in asset groups below Good", "Ran" if ag["has_strength"] else "Not run", "Asset group report" if ag["has_strength"] else "",
            "" if ag["has_strength"] else data.UNLOCK["ad_strength"])
    else:
        add("Asset groups by spend", "Not run", unlock=data.UNLOCK["asset_groups"])
        add("Spend in asset groups below Good", "Not run", unlock=data.UNLOCK["asset_groups"])
    if st:
        add("Brand share of Performance Max searches", "Ran" if st["brand"] else "Not run", "Search terms report" if st["brand"] else "",
            "" if st["brand"] else data.UNLOCK["brand"], "" if st["has_cost"] else "Shares of conversions only. The report has no Cost column.")
        add("Searches with cost and no conversions", "Ran" if st["has_cost"] else "Not run", "Search terms report" if st["has_cost"] else "",
            "" if st["has_cost"] else data.UNLOCK["search_cost"])
    else:
        add("Brand share of Performance Max searches", "Not run", unlock=data.UNLOCK["search_terms"])
        add("Searches with cost and no conversions", "Not run", unlock=data.UNLOCK["search_terms"])
    for name in ("Products that spend with no conversions", "Spend concentration in the top products", "Product groups by brand, product type and custom label"):
        add(name, "Ran" if pr else "Not run", "Products report" if pr else "", "" if pr else data.UNLOCK["products"])
    if pr:
        add("Feed attribute gaps on products that spend", "Ran" if pr["gaps"] else "Not run", "Products report" if pr["gaps"] else "",
            "" if pr["gaps"] else "the products report with Brand, Product type (1st level) and Custom label columns")
        if not pr["has_value"]:
            add("Products below the target ROAS", "Not run", unlock=data.UNLOCK["conv_value"])
        else:
            add("Products below the target ROAS", "Ran" if args.target_roas else "Not run", "Products report" if args.target_roas else "",
                "" if args.target_roas else data.UNLOCK["target_roas"])
    else:
        add("Feed attribute gaps on products that spend", "Not run", unlock=data.UNLOCK["products"])
        add("Products below the target ROAS", "Not run", unlock=data.UNLOCK["products"])
    if pc:
        add("Price competitiveness", "Ran", pc["source"].capitalize(),
            note="" if pc["with_performance"] else "Price positions only. Add the products report to see cost and conversions by price position.")
    else:
        add("Price competitiveness", "Not run", unlock=data.UNLOCK["prices"])
    return checks


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True, help="folder for the review files")
    parser.add_argument("--campaigns", help="campaign report, filtered to Performance Max or not")
    parser.add_argument("--asset-groups", help="asset group report")
    parser.add_argument("--channels", help="channel performance report")
    parser.add_argument("--search-terms", help="search terms report")
    parser.add_argument("--products", help="products report")
    parser.add_argument("--prices", help="price benchmarks from Merchant Center")
    parser.add_argument("--brand", default="", help="brand terms, comma separated")
    parser.add_argument("--target-cpa", type=float, help="target cost per conversion")
    parser.add_argument("--target-roas", type=float, help="target ROAS in percent as Google shows it, for example 400")
    parser.add_argument("--campaign", action="append", default=[], help="limit the review to this campaign; repeat for more")
    args = parser.parse_args()

    paths = {k: getattr(args, k) for k in ("campaigns", "asset_groups", "channels", "search_terms", "products", "prices") if getattr(args, k)}
    if not paths:
        data.plain_exit("Give at least one report, for example --campaigns with the campaign report filtered to Performance Max.")
    if args.target_roas is not None and args.target_roas <= 20:
        data.plain_exit("Give the target ROAS in percent as Google shows it, for example 400 for 400%.")
    target_roas = args.target_roas / 100.0 if args.target_roas else None
    loaded = {kind: data.load(kind, path) for kind, path in paths.items()}
    if "products" in loaded and not ({"item_id", "title"} & set(loaded["products"][0]["columns"])):
        data.plain_exit("I can't find these columns in the products report: Item ID. Download the report again with those columns added.")
    chosen = set(args.campaign)
    if chosen:
        check_campaign_names(chosen, {k: v for k, v in loaded.items() if k != "prices"})
    brand_phrases = [metrics.tokens(p) for p in args.brand.split(",") if p.strip()]

    # Words that name what the account sells or builds. A suggested negative made only of these would block its own business.
    texts, sources = [], []
    for kind, fields in (("products", ("title",)), ("prices", ("title",)), ("asset_groups", ("asset_group", "campaign"))):
        if kind in loaded:
            texts += [r.get(f) or "" for r in loaded[kind][1] for f in fields]
            sources.append(data.REPORTS[kind]["name"])
    if "campaigns" in loaded:
        texts += [r.get("campaign") or "" for r in loaded["campaigns"][1] if "performance max" in (r.get("campaign_type") or "performance max").lower()]
        sources.append("campaign report")
    protected = data.word_set(texts)

    parts = {}
    if "campaigns" in loaded:
        parts["campaigns"] = data.campaigns_part(*loaded["campaigns"], chosen)
        against_targets(parts["campaigns"], args.target_cpa, target_roas)
    if "asset_groups" in loaded:
        parts["asset_groups"] = data.asset_groups_part(*loaded["asset_groups"], chosen, args.target_cpa)
    if "channels" in loaded:
        parts["channels"] = data.channels_part(*loaded["channels"], chosen)
    if "search_terms" in loaded:
        parts["search_terms"] = data.search_terms_part(*loaded["search_terms"], chosen, brand_phrases, args.target_cpa, protected)
    if "products" in loaded:
        parts["products"] = data.products_part(*loaded["products"], chosen, args.target_cpa, target_roas)
    if "products" in parts or "prices" in loaded:
        price_meta, price_rows = loaded.get("prices", (None, None))
        prices = data.prices_part(parts["products"]["products"] if "products" in parts else None, price_rows, price_meta)
        if prices:
            parts["prices"] = prices
        elif "prices" in loaded:
            data.plain_exit("None of the products in the price benchmark report has both a price and a benchmark I can read, "
                            "or none matches the products report by Item ID. Check that both files come from the same Merchant Center account.")

    metas = {k: v[0] for k, v in loaded.items()}
    cons = consistency(parts, metas)
    review = {
        "reports": {k: {"file": m["path"], "title_rows": m["title_rows"], "date_range": m["date_range"], "days": m["days"],
                        "rows": m["row_count"], "columns_found": sorted(m["columns"]), "columns_not_used": m["unknown_headers"],
                        "totals_in_file": m["totals"], "odd_total_labels": m["odd_totals"]} for k, m in metas.items()},
        "currency": sorted({(r.get("currency") or "").strip() for _, rows in loaded.values() for r in rows if (r.get("currency") or "").strip()}),
        "inputs": {"protected_words_from": sources, "brand": [" ".join(p) for p in brand_phrases], "target_cpa": args.target_cpa, "target_roas": target_roas, "campaigns": sorted(chosen)},
        "consistency": cons,
        "parts": parts,
        "findings": build_findings(parts, cons, brand_phrases),
        "checks": build_checks(parts, args),
        "actions": [],
    }
    text = write.write_all(review, args.out)
    print(text)
    print(write.judgment_block(review))
    print("Wrote the files to %s" % args.out)


if __name__ == "__main__":
    main()
