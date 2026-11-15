#!/usr/bin/env python3
"""Step 1 of the search term review: load the export and measure it.

Reads a Google Ads search terms report, totals every search, sets the
account's own line for "spent enough to judge", and sorts searches into
Keep, Watch and Exclude candidates. Writes work files for the next steps
and prints the tables to review.

    python3 measure.py REPORT --work WORKDIR [--target-cpa 40] [--brand "acme, acme plumbing"] [--competitors "rival, other co"]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import io, metrics, outputs  # noqa: E402

STOPWORDS = set("a an and are as at be by for from how i in is it me my near of on or the to what when where with you your".split())
MAX_CANDIDATES_TO_REVIEW = 150


def aggregate(rows):
    merged = {}
    for row in rows:
        term = (row.get("search_term") or "").strip()
        if not term:
            continue
        key = (term.lower(), row.get("campaign", ""), row.get("ad_group", ""))
        item = merged.setdefault(key, {
            "search_term": term, "campaign": row.get("campaign", ""), "ad_group": row.get("ad_group", ""),
            "match_types": [], "sources": [], "status": [],
            "clicks": 0.0, "impressions": 0.0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0,
        })
        for field in ("clicks", "impressions", "cost", "conversions", "conv_value"):
            item[field] += row.get(field) or 0
        for field, target in (("match_type", "match_types"), ("source", "sources"), ("added_excluded", "status")):
            value = (row.get(field) or "").strip()
            if value and value not in item[target]:
                item[target].append(value)
    return list(merged.values())


def is_brand(term, brand_phrases):
    words = metrics.tokens(term)
    for phrase in brand_phrases:
        span = len(phrase)
        if span and any(words[i:i + span] == phrase for i in range(len(words) - span + 1)):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report")
    parser.add_argument("--work", required=True, help="folder for work files")
    parser.add_argument("--target-cpa", type=float, help="the account's target cost per conversion")
    parser.add_argument("--brand", default="", help="brand terms, comma separated")
    parser.add_argument("--competitors", default="", help="competitor names, comma separated")
    parser.add_argument("--min-clicks", type=int, default=3, help="fewer clicks than this is too little to judge")
    args = parser.parse_args()

    meta, rows = io.read_report(args.report)
    io.require(meta, ["search_term", "clicks", "cost", "conversions"], "search terms report")
    terms = aggregate(rows)
    brand_phrases = [metrics.tokens(p) for p in args.brand.split(",") if p.strip()]
    competitor_phrases = [metrics.tokens(p) for p in args.competitors.split(",") if metrics.tokens(p)]

    cost = metrics.total(terms, "cost")
    clicks = metrics.total(terms, "clicks")
    conversions = metrics.total(terms, "conversions")
    baseline_cpa = metrics.div(cost, conversions)
    # Brand searches convert cheaply and would pull the line down, so they are left out of it.
    non_brand = [t for t in terms if not is_brand(t["search_term"], brand_phrases)]
    non_brand_cpa = metrics.div(metrics.total(non_brand, "cost"), metrics.total(non_brand, "conversions"))
    if args.target_cpa:
        line, line_source = args.target_cpa, "the target cost per conversion you gave"
    elif brand_phrases and non_brand_cpa:
        line, line_source = non_brand_cpa, "the cost per conversion of the non brand searches in this report"
    elif baseline_cpa:
        line, line_source = baseline_cpa, "this account's own cost per conversion in this report"
    else:
        ranked = sorted(t["cost"] for t in terms)
        line = ranked[int(len(ranked) * 0.9)] if ranked else 0
        line_source = "the top tenth of searches by cost, because this report has no conversions"

    for number, term in enumerate(sorted(terms, key=lambda t: -t["cost"]), start=1):
        term["id"] = number
        term["cpa"] = metrics.div(term["cost"], term["conversions"])
        # How far a converting search's cost per conversion sits from the line, as a share of the line.
        term["cpa_vs_line"] = metrics.change(term["cpa"], line) if term["cpa"] is not None and line else None
        term["competitor"] = bool(competitor_phrases) and is_brand(term["search_term"], competitor_phrases)
        excluded = any("exclud" in s.lower() for s in term["status"])
        if excluded:
            term["class"], term["class_reason"] = "Already excluded", "Already excluded in the account"
        elif is_brand(term["search_term"], brand_phrases):
            term["class"], term["class_reason"] = "Keep", "Brand search"
        elif term["conversions"] > 0:
            term["class"], term["class_reason"] = "Keep", "Converted in this period"
        elif term["cost"] >= line > 0:
            term["class"], term["class_reason"] = "Exclude candidate", "No conversions, and it has spent as much as a conversion costs here"
        elif term["clicks"] < args.min_clicks:
            term["class"], term["class_reason"] = "Watch", "Too few clicks to judge"
        else:
            term["class"], term["class_reason"] = "Watch", "No conversions yet, and it has spent less than a conversion costs here"
    terms.sort(key=lambda t: t["id"])

    # Words and phrases that spend without converting anywhere in the report.
    grams = {}
    for term in terms:
        if term["class"] == "Already excluded":
            continue
        seen = set()
        for size in (1, 2, 3):
            for gram in metrics.ngrams(term["search_term"], size):
                if size == 1 and (gram in STOPWORDS or len(gram) < 2):
                    continue
                if gram in seen:
                    continue
                seen.add(gram)
                slot = grams.setdefault(gram, {"phrase": gram, "words": size, "searches": 0, "clicks": 0.0, "cost": 0.0, "conversions": 0.0})
                slot["searches"] += 1
                for field in ("clicks", "cost", "conversions"):
                    slot[field] += term[field]
    waste = [g for g in grams.values() if g["conversions"] == 0 and g["searches"] >= 2 and g["cost"] >= line * 0.5]
    waste.sort(key=lambda g: (-g["cost"], g["words"]))

    listed_total, other_total = None, None
    for label, values in meta["totals"].items():
        if "search term" in label.lower() and "other" not in label.lower():
            listed_total = values
        elif "other" in label.lower():
            other_total = values
    reconcile = None
    if listed_total and listed_total.get("cost") is not None:
        reconcile = {"file_total_cost": listed_total["cost"], "rows_cost": cost, "difference": round(cost - listed_total["cost"], 2)}

    ai_max_cost = sum(t["cost"] for t in terms if any("ai max" in m.lower() for m in t["match_types"]))
    candidates = [t for t in terms if t["class"] == "Exclude candidate"]
    to_review = candidates[:MAX_CANDIDATES_TO_REVIEW]

    measured = {
        "report": os.path.basename(args.report),
        "title_rows": meta["title_rows"],
        "columns_found": sorted(meta["columns"]),
        "columns_not_used": meta["unknown_headers"],
        "totals": {"searches": len(terms), "clicks": clicks, "cost": cost, "conversions": conversions,
                   "conv_value": metrics.total(terms, "conv_value"), "baseline_cpa": baseline_cpa, "non_brand_cpa": non_brand_cpa},
        "not_listed": other_total,
        "campaigns": sorted({t["campaign"] for t in terms if t["campaign"]}),
        "line": {"value": line, "source": line_source, "min_clicks": args.min_clicks, "words_min_cost": line * 0.5},
        "brand": [" ".join(p) for p in brand_phrases],
        "competitors": [" ".join(p) for p in competitor_phrases],
        "reconcile": reconcile,
        "ai_max": {"present": ai_max_cost > 0, "cost": ai_max_cost, "share_of_cost": metrics.div(ai_max_cost, cost)},
        "terms": terms,
        "waste_words": waste[:60],
    }
    outputs.ensure_dir(args.work)
    outputs.write_json(os.path.join(args.work, "measured.json"), measured)
    watch = [t for t in terms if t["class"] == "Watch"]
    template = {
        "how_to_fill": "Give every search below a verdict (Keep, Watch or Exclude), a one line reason and, for Exclude, a short theme "
                       "such as 'Job seekers'. Searches with an empty verdict must be judged. Watch searches are prefilled and may be "
                       "changed. Any other search can be added by its id. List each negative keyword once under negatives. "
                       "Then run check_negatives.py.",
        "verdicts": [{"id": t["id"], "search_term": t["search_term"], "campaign": t["campaign"], "ad_group": t["ad_group"],
                      "cost": round(t["cost"], 2), "clicks": int(t["clicks"]), "verdict": "", "reason": "", "theme": ""} for t in to_review]
                    + [{"id": t["id"], "search_term": t["search_term"], "campaign": t["campaign"], "ad_group": t["ad_group"],
                        "cost": round(t["cost"], 2), "clicks": int(t["clicks"]), "verdict": "Watch", "reason": t["class_reason"], "theme": ""} for t in watch],
        "negatives": [{"text": "", "match": "phrase", "level": "campaign", "campaign": "", "ad_group": "", "why": ""}],
    }
    outputs.write_json(os.path.join(args.work, "verdicts.template.json"), template)

    counts = {}
    for term in terms:
        counts[term["class"]] = counts.get(term["class"], 0) + 1
    print("LOAD REPORT")
    for title in meta["title_rows"]:
        print("  " + title)
    print("  Searches read: %d   Clicks: %s   Cost: %s   Conversions: %s" % (len(terms), "{:,.0f}".format(clicks), metrics.money(cost), "{:,.2f}".format(conversions)))
    if reconcile:
        print("  File total for listed searches: %s   Difference from rows: %s" % (metrics.money(reconcile["file_total_cost"]), metrics.money(reconcile["difference"])))
    if other_total and other_total.get("cost"):
        print("  Not listed by Google (low volume searches): %s cost. These are outside this review." % metrics.money(other_total["cost"]))
    print("  Spent enough to judge: %s or more with no conversions. That is %s." % (metrics.money(line), line_source))
    if measured["ai_max"]["present"]:
        print("  AI Max share of cost: %s" % metrics.pct(measured["ai_max"]["share_of_cost"]))
    print("  " + "   ".join("%s: %d" % (k, v) for k, v in sorted(counts.items())))
    print("  Google leaves low volume searches out of this report, so this covers the searches Google shows.")
    print()
    print("EXCLUDE CANDIDATES TO JUDGE (%d of %d, by cost)" % (len(to_review), len(candidates)))
    print(outputs.md_table(["id", "Search", "Campaign", "Ad group", "Clicks", "Cost"],
                           [[t["id"], t["search_term"], t["campaign"], t["ad_group"], int(t["clicks"]), "%.2f" % t["cost"]] for t in to_review]))
    print()
    print("SEARCHES TO PROTECT. No negative may block these. Change a Watch to Exclude only when the reason is clear.")
    print("'Cost / conv. against the line' compares a converting search's cost per conversion with the line, %s." % metrics.money(line))
    keep_watch = [t for t in terms if t["class"] in ("Keep", "Watch")]
    print(outputs.md_table(["id", "Search", "Campaign", "Class", "Clicks", "Cost", "Conversions", "Cost / conv.", "Cost / conv. against the line"],
                           [[t["id"], t["search_term"], t["campaign"], t["class"], int(t["clicks"]), "%.2f" % t["cost"], "%.2f" % t["conversions"],
                             "%.2f" % t["cpa"] if t["cpa"] is not None else "",
                             ("%+.0f%%" % (t["cpa_vs_line"] * 100)) if t["cpa_vs_line"] is not None else ""] for t in keep_watch]))
    print()
    if competitor_phrases:
        rivals = [t for t in terms if t["competitor"]]
        print("SEARCHES THAT NAME A COMPETITOR (%s): %d searches, cost %s, conversions %s"
              % (", ".join(measured["competitors"]), len(rivals), metrics.money(sum(t["cost"] for t in rivals)),
                 "{:,.2f}".format(sum(t["conversions"] for t in rivals))))
        print(outputs.md_table(["id", "Search", "Campaign", "Class", "Clicks", "Cost", "Conversions"],
                               [[t["id"], t["search_term"], t["campaign"], t["class"], int(t["clicks"]), "%.2f" % t["cost"], "%.2f" % t["conversions"]]
                                for t in rivals]) if rivals else "  None of the names appears in a search.")
        print()
    print("WORDS AND PHRASES IN TWO OR MORE SEARCHES, WITH NO CONVERSIONS ANYWHERE IN THE REPORT AND COST OF AT LEAST %s (HALF THE LINE)"
          % metrics.money(line * 0.5))
    print(outputs.md_table(["Phrase", "Searches", "Clicks", "Cost"],
                           [[g["phrase"], g["searches"], int(g["clicks"]), "%.2f" % g["cost"]] for g in waste[:20]]))
    print()
    print("Next: copy %s to verdicts.json, fill it in, then run python3 scripts/check_negatives.py --work %s" % (os.path.join(args.work, "verdicts.template.json"), args.work))


if __name__ == "__main__":
    main()
