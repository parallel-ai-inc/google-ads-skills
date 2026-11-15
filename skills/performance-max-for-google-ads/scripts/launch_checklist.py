#!/usr/bin/env python3
"""Write a launch or clone checklist for a new Performance Max rollout.

Built from the launch playbook and, when given, the account's numbers from
audit.py. With --source the checklist is a clone of that campaign, which must
be in the campaign report, and it opens with a go or no go line. Name the
asset groups or product groups the clone copies with --asset-group and
--product-group; otherwise any whose name appears in --name are taken as
copied, and failing that the clone copies every asset group of the source.
Dates are worked out from --start.

    python3 scripts/launch_checklist.py --out OUTPUT [--review OUTPUT/pmax-review.json]
        [--source "PMax | Shop"] [--name "PMax | Shop | New"] [--asset-group "Drain Tools"] [--product-group "Drain Tools"]
        [--daily-budget 150] [--start 2026-11-20] [--retail]
"""
import argparse
import datetime as dt
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, metrics, outputs  # noqa: E402
import pmax_data as data  # noqa: E402

FILE = "pmax-launch-checklist.md"
VALUE = "conv. value / cost"


def m(value):
    return metrics.money(value)


def n2(value):
    return "n/a" if value is None else "{:,.2f}".format(value)


def when(start, offset, fallback):
    return (start + dt.timedelta(days=offset)).isoformat() if start else fallback


def weakest(items, goal):
    """The weakest item with cost by the goal: lowest conv. value / cost, or highest cost per conversion (none at all is weakest)."""
    spent = [i for i in items if i["cost"] > 0]
    if len(spent) < 2:
        return None
    if goal == VALUE:
        return min(spent, key=lambda i: ((i.get("roas") or 0), -i["cost"]))
    return max(spent, key=lambda i: (i["conversions"] == 0, i["cpa"] or 0, i["cost"]))


def score(item, goal):
    return "%s conv. value / cost" % n2(item.get("roas") or 0) if goal == VALUE else ("%s per conversion" % m(item["cpa"]) if item["cpa"] else "no conversions on %s" % m(item["cost"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True)
    parser.add_argument("--review", help="pmax-review.json from audit.py")
    parser.add_argument("--source", help="the Performance Max campaign to clone")
    parser.add_argument("--name", default="", help="name of the new campaign")
    parser.add_argument("--asset-group", action="append", default=[], help="an asset group of the source that the clone copies; repeat for more")
    parser.add_argument("--product-group", action="append", default=[], help="a product type, brand or custom label value the clone carries; repeat for more")
    parser.add_argument("--daily-budget", type=float)
    parser.add_argument("--start", help="planned start day, YYYY-MM-DD")
    parser.add_argument("--retail", action="store_true", help="the campaign uses a Merchant Center feed")
    args = parser.parse_args()

    review = None
    if args.review:
        if not os.path.isfile(args.review):
            raise SystemExit("I can't find %s. Run audit.py first." % args.review)
        review = outputs.read_json(args.review)
    parts = review["parts"] if review else {}
    camp, ag, st, pr, pc, ch = (parts.get(k) for k in ("campaigns", "asset_groups", "search_terms", "products", "prices", "channels"))
    source = None
    if args.source:
        if not camp:
            raise SystemExit("To clone a campaign, run audit.py with the campaign report first, then pass --review.")
        source = next((c for c in camp["campaigns"] if c["campaign"] == args.source), None)
        if not source:
            raise SystemExit('I can\'t find the campaign "%s" in the campaign report. The Performance Max campaigns are: %s.' % (
                args.source, ", ".join(c["campaign"] for c in camp["campaigns"])))
    if (args.asset_group or args.product_group) and not source:
        raise SystemExit("--asset-group and --product-group name what a clone copies, so they need --source.")
    start = dates.parse_day(args.start) if args.start else None
    if args.start and not start:
        raise SystemExit("Write the start day as YYYY-MM-DD, for example 2026-11-20.")
    if args.daily_budget is not None and args.daily_budget <= 0:
        raise SystemExit("The daily budget must be more than zero.")

    source_groups = [g for g in ag["groups"] if g["campaign"] == args.source] if (source and ag) else []
    copied, products_copied, notes = [], [], []
    for name in args.asset_group:
        group = next((g for g in source_groups if g["asset_group"] == name), None)
        if not group:
            raise SystemExit('I can\'t find the asset group "%s" in %s. Its asset groups are: %s.' % (
                name, args.source, ", ".join(g["asset_group"] for g in source_groups) or "none in the asset group report"))
        copied.append(group)
    product_groups = pr["groups"] if pr else {}
    for value in args.product_group:
        hit = next(((f, g) for f, groups in product_groups.items() for g in groups if g["value"] == value), None)
        if not hit:
            known = [g["value"] for g in product_groups.get("product_type", [])] or [g["value"] for groups in product_groups.values() for g in groups][:20]
            raise SystemExit('I can\'t find the product group "%s" in the products report. Product types there: %s.' % (value, ", ".join(known) or "none"))
        products_copied.append(hit)
    lowered = args.name.lower()
    if source and args.name and not copied:
        copied = [g for g in source_groups if g["asset_group"].lower() in lowered]
        if copied:
            notes.append("Asset groups taken as copied because the new name holds their name: %s." % ", ".join(g["asset_group"] for g in copied))
    if source and args.name and not products_copied:
        products_copied = [("product_type", g) for g in product_groups.get("product_type", []) if g["value"] != "(blank)" and g["value"].lower() in lowered]
        if products_copied:
            notes.append("Product groups taken as copied because the new name holds their name: %s." % ", ".join(g["value"] for _, g in products_copied))
    copies_all = source is not None and not copied
    if copies_all:
        copied = source_groups

    retail = args.retail or bool(pr or pc)
    base = source or (camp["total"] if camp else None)
    cpa = base["cpa"] if base else None
    name = args.name or ("a copy of %s" % args.source if source else "the new Performance Max campaign")
    lines = ["# Performance Max %s checklist" % ("clone" if source else "launch"), "",
             "For %s.%s" % (name, " Cloned from %s." % args.source if source else "")]
    ranges = sorted({tuple(r["date_range"]) for r in review["reports"].values() if r.get("date_range")}) if review else []
    if review:
        lines.append("Account numbers come from reports covering %s." % ("; ".join("%s to %s" % r for r in ranges) or "dates not stated in the files"))
    else:
        lines.append("No account reports were given, so the account numbers are left out. Run audit.py and pass --review to fill them in.")
    lines += ["Each item says whether it is **Official** (Google documents it) or a **Practitioner rule**.", ""]

    if source:
        goal = source.get("goal") or (VALUE if source.get("conv_value") else "cost / conv.")
        reasons, checks = [], []
        if source.get("learning"):
            reasons.append("%s is still learning, so its numbers are early. Official: run a new campaign at least 6 weeks, and allow 1 to 2 weeks or one full "
                           "conversion cycle after a significant change." % args.source)
        worst = weakest(source_groups, goal)
        for g in copied:
            if worst and g["asset_group"] == worst["asset_group"]:
                text = "Asset group %s is the weakest in %s by %s: %s against %s for the campaign." % (
                    g["asset_group"], args.source, goal, score(g, goal), score(source, goal))
                (checks if copies_all else reasons).append(text + (" Leave it out of the copy or fix it first." if copies_all else ""))
            if g["ad_strength"] in ("Average", "Poor"):
                reasons.append("Asset group %s is rated %s, with %s cost and %s against %s for the campaign. Official: Google recommends Ad strength of Good or Excellent." % (
                    g["asset_group"], g["ad_strength"], m(g["cost"]), score(g, goal), score(source, goal)))
            if g.get("no_conv_over_line"):
                reasons.append("Asset group %s spent %s with no conversions, enough to judge on spend alone." % (g["asset_group"], m(g["cost"])))
        pgoal = VALUE if pr and pr["has_value"] and pr["total"]["conv_value"] else "cost / conv."
        for field, g in products_copied:
            peers = product_groups[field]
            low = weakest(peers, pgoal)
            if low and low["value"] == g["value"]:
                reasons.append("Product group %s (%s) is the weakest of %d by %s: %s against %s for all products." % (
                    g["value"], g["dimension"], len([x for x in peers if x["cost"] > 0]), pgoal, score(g, pgoal), score(pr["total"], pgoal)))
        verdict = "fix first" if reasons else "go"
        lines += ["**Go or no go: %s.**" % verdict, ""]
        if reasons:
            lines += ["Fix these before cloning, or the copy starts with the same weakness:", ""] + ["- %s" % r for r in reasons]
        else:
            lines.append("None of the copied asset groups or product groups is the weakest by the campaign's goal or rated below Good, and the source is not learning.")
        lines += ["- %s" % c for c in checks] + ["- %s" % n for n in notes]
        if copies_all and source_groups:
            lines.append("- The clone copies every asset group of %s. Name the ones it copies with --asset-group to judge only those." % args.source)
        lines.append("")

    lines += ["## 1. Measurement first", "",
              "- [ ] Confirm the conversion goals the campaign will bid to, and that each counts what the business values. Practitioner rule: goal and conversion meaning come before any other check.",
              "- [ ] If the aim is new customers only, set the new customer acquisition goal. Official: audience signals are suggestions, not targeting."]
    if base:
        lines.append("- Account number: %s spent %s for %s conversions, %s per conversion%s." % (
            args.source if source else "Performance Max", m(base["cost"]), n2(base["conversions"]), m(cpa),
            ", %s conv. value / cost" % n2(base["roas"]) if base.get("roas") is not None and base.get("conv_value") else ""))
        if not source and camp and camp.get("value_mixed"):
            lines.append("- The current campaigns have different goals. Set this campaign's target from the campaigns that share its goal, not from the total.")

    if retail:
        lines += ["", "## 2. Product data", "",
                  "- [ ] Merchant Center is linked and the products have no blocking issues. Official: retail diagnostics start with Merchant Center linkage, product data status and product issues.",
                  "- [ ] Fix mismatches between the feed and the landing pages, then fill required and high signal attributes. Practitioner rule."]
        if pr:
            lines.append("- Account number: %d products had cost and no conversions, costing %s. %d of them spent at least %s, enough to judge on spend alone, costing %s. "
                         "Decide whether they belong in the new listing groups." % (
                             pr["no_conv"]["products"], m(pr["no_conv"]["cost"]), len(pr["over_line"]), m(pr["line"]["value"]), m(pr["over_line_cost"])))
            for gap in pr["gaps"]:
                if gap["cost"] > 0 and not gap["attribute"].startswith("Custom label"):
                    lines.append("- Account number: %s is blank on %d products carrying %s." % (gap["attribute"], gap["products"], m(gap["cost"])))
            types = product_groups.get("product_type") or product_groups.get("brand") or []
            if types:
                lines.append("- [ ] Plan listing groups from the account's own split. Largest product groups by cost: %s. Practitioner rule: use custom labels for business slicing, not as a rank lever." % "; ".join(
                    "%s (%s cost, %s)" % (g["value"], m(g["cost"]), score(g, VALUE if pr["has_value"] else "cost / conv.")) for g in types[:5]))
        if pc:
            lines.append("- Account number: %d products are priced above their benchmark%s. Practitioner rule: decide on price before pushing them harder." % (
                pc["above"]["products"], ", carrying %s" % m(pc["above"]["cost"]) if pc["with_performance"] else ""))
        lines.append("- Official: retail campaigns linked to Merchant Center generate the minimum assets automatically.")

    lines += ["", "## %d. Campaign shell and settings" % (3 if retail else 2), "",
              "- [ ] Build it paused, then enable once the asset groups and exclusions are in. Practitioner rule."]
    if source:
        lines.append("- [ ] Bid strategy type: the source uses %s%s. Practitioner rule: start the copy from the source's own setting and numbers." % (
            source["bid_strategy"] or "a strategy not shown in the report", ", budget %s a day" % m(source["budget"]) if source.get("budget") is not None else ""))
    if args.daily_budget:
        line = "- [ ] Daily budget %s." % m(args.daily_budget)
        if cpa:
            line += " At %s per conversion it pays for %s conversions a day." % (m(cpa), n2(args.daily_budget / cpa))
        if source and source.get("avg_daily_cost") is not None:
            line += " The source spent %s a day on average over the %s days of the report." % (m(source["avg_daily_cost"]), source["days"])
        lines.append(line)
    lines += ["- Official: since August 17, 2026 budget limited Target CPA and Target ROAS campaigns, Performance Max included, deliver toward the stated target and may shift channel mix.",
              "- [ ] Final URL expansion. Official: Google's baseline is Final URL expansion on plus search themes. URL exclusions only work while it is on. Turning it off and attaching a page feed restricts serving to listed pages.",
              "- [ ] Device and age targeting, if the business needs them. Official: both are full Performance Max controls.",
              "- Official: text customization is on by default. Google written text serves only when predicted to beat your own."]

    section = 4 if retail else 3
    lines += ["", "## %d. Asset groups and signals" % section, "",
              "- [ ] Each asset group, per Google's asset requirements. Official: up to 15 headlines (30 characters, at least 3), up to 5 long headlines (90 characters, at least 1), "
              "up to 5 descriptions (90 characters, at least 2), 1 to 20 landscape images (1.91:1), 1 to 20 square images (1:1), up to 20 portrait images (4:5) and up to 15 videos of at least 10 seconds.",
              "- [ ] Business name and logos. Official: with brand guidelines off, each asset group needs one business name (up to 25 characters) and 1 to 5 logos. With brand guidelines on, they sit at campaign level.",
              "- [ ] Aim for Ad strength Good or Excellent, with every asset type in every group. Official: Google recommends this, and 2 to 3 weeks before replacing low performers. Without your own video, Google may generate one.",
              "- [ ] Search themes, up to 50, for what customers search that the site, assets and feed do not already show. Official.",
              "- [ ] Audience signals from the business's own customer data and best converting segments. Official: they are suggestions, not targeting."]
    if source and source_groups:
        lines.append("- Account number: the source has %d asset groups. %s." % (len(source_groups), "; ".join(
            "%s: %s, %s cost, %s" % (g["asset_group"], g["ad_strength"], m(g["cost"]), score(g, source.get("goal") or "cost / conv.")) for g in source_groups[:8])))
    elif ag and ag["below_good"]:
        lines.append("- Account number: asset groups rated below Good carry %s of the asset group report's cost. Practitioner rule: build the new groups to Good before launch." % metrics.pct(ag["below_good"]["share_of_cost"]))

    section += 1
    lines += ["", "## %d. Exclusions and safety" % section, ""]
    brand_line = "- [ ] Brand exclusions, if Search campaigns should own brand searches. Official: they block brand terms, misspellings and subsidiary brands on Search and Shopping, and Google prefers them over negatives."
    if st and st.get("brand"):
        brand_line += " Account number: brand searches are %s of the listed Performance Max search cost and %s of the listed conversions in the search terms report." % (
            metrics.pct(st["brand"]["share_of_cost"]), metrics.pct(st["brand"]["share_of_conversions"]))
    lines += [brand_line,
              "- [ ] Negative keywords. Official: they apply to Search and Shopping inventory only, up to 10,000 per campaign and 1,000 at account level, with no close variant matching."]
    if st:
        # A negative is never suggested when every word names what the new campaign carries.
        sets = [("the new campaign's name", data.word_set([args.name, args.source or ""])),
                ("the asset group names it copies" if source else "the account's asset group names", data.word_set([g["asset_group"] for g in (copied if source else (ag["groups"] if ag else []))])),
                ("the titles of the products it will carry", data.word_set([p["title"] for p in (pr["products"] if pr else [])
                                                                            if not source or not p["campaigns"] or args.source in p["campaigns"]]))]
        union = set().union(*(words for _, words in sets))
        candidates, held = [], []
        for g in sorted(st.get("waste_words", []) + st.get("held_back_words", []), key=lambda x: -x["cost"]):
            words = g["phrase"].split()
            if all(w in union for w in words):
                held.append((g, [label for label, found in sets if any(w in found for w in words)]))
            elif g.get("protected"):
                held.append((g, ["the account's other product titles, asset group or campaign names"]))
            else:
                candidates.append(g)
        if candidates:
            lines.append("- Account number: words in two or more current searches with cost and no conversions, to review as negatives: %s." % ", ".join(
                '"%s" (%s)' % (g["phrase"], m(g["cost"])) for g in candidates[:8]))
        if held:
            lines.append("- Held back, never to be added as negatives here: %s. Every word appears in what this campaign sells or builds, so a negative would block its own business." % "; ".join(
                '"%s" (%s, found in %s)' % (g["phrase"], m(g["cost"]), " and ".join(where)) for g, where in held[:8]))
    lines += ["- [ ] Brand safety on Display and video. Official: block placements there through excluded content keywords in content suitability.",
              "- [ ] Overlap with Search. Official: only an exact match keyword identical to the search is preferred over Performance Max. Identical phrase or broad keywords share the next priority with identical search themes."]

    section += 1
    lines += ["", "## %d. Rollout and verification order" % section, ""]
    steps = ["Measurement checked (section 1)."]
    if retail:
        steps.append("Product data and Merchant Center checked (section 2).")
    steps += ["Shell built paused, with budget and bidding.", "Asset groups built and Ad strength checked.", "Exclusions applied.",
              "Enable on %s." % (start.isoformat() if start else "the start day"),
              "%s: check it serves. Status, impressions and cost by channel, and any policy issues. Practitioner rule." % (
                  "From %s to %s" % (when(start, 0, ""), when(start, 2, "")) if start else "Days 1 to 3"),
              "%s: first read of the channel report Status column, asset group Ad strength and the search terms. Official: allow 1 to 2 weeks, or one full conversion cycle, "
              "after a significant change, and avoid frequent budget, bid strategy or status changes early." % when(start, 13, "Day 14"),
              "%s: earliest full judgment. Official: run a new campaign at least 6 weeks. Only about half of Performance Max conversions land inside the 30 day click and 3 day engaged view windows, so early reads understate it." % when(start, 41, "Day 42")]
    if source:
        baseline = "Compare the copy with the source's numbers above"
        own = [c for c in ch["per_campaign"] if c["campaign"] == args.source] if ch else []
        if own:
            search = sum(c["cost"] for c in own if c["channel"] in ("Google Search", "Search partners"))
            baseline += ", and with its channel mix: Google Search and Search partners carry %s of its cost in the channel report" % metrics.pct(
                metrics.div(search, sum(c["cost"] for c in own)))
        elif ch:
            baseline += ", and with the current channel mix: Google Search and Search partners carry %s of channel report cost" % metrics.pct(ch["search_share_of_cost"])
        steps.append(baseline + ". Practitioner rule.")
    lines += ["%d. %s" % (n, s) for n, s in enumerate(steps, start=1)]
    text = "\n".join(lines) + "\n"
    outputs.ensure_dir(args.out)
    with open(os.path.join(args.out, FILE), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote %s" % os.path.join(args.out, FILE))


if __name__ == "__main__":
    main()
