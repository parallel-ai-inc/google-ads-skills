#!/usr/bin/env python3
"""Step 2 of the search term review: test every proposed negative keyword.

A negative passes only if it blocks no search with a Keep or Watch verdict
and none of the account's own keywords. Anything else is rejected, with the
searches it would have blocked, so it can be narrowed or dropped.

    python3 check_negatives.py --work WORKDIR [--keywords KEYWORDS_REPORT]
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import io, negatives, outputs  # noqa: E402

VERDICTS = ("Keep", "Watch", "Exclude")


def file_hash(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def final_verdicts(measured, verdict_rows):
    """Apply the reviewer's verdicts on top of the measured classes."""
    by_id = {t["id"]: t for t in measured["terms"]}
    problems = []
    for term in by_id.values():
        if term["class"] == "Exclude candidate":
            term["verdict"], term["reason"] = "Watch", "Not reviewed. No conversions and cost above the line."
        else:
            term["verdict"], term["reason"] = term["class"], term["class_reason"]
    for row in verdict_rows:
        term = by_id.get(row.get("id"))
        verdict = (row.get("verdict") or "").strip().capitalize()
        if not term:
            problems.append("Verdict for unknown search id %r was ignored." % row.get("id"))
            continue
        if verdict not in VERDICTS:
            problems.append('Search %d "%s" has no valid verdict, so it stays Watch.' % (term["id"], term["search_term"]))
            continue
        if verdict == "Exclude" and term["conversions"] > 0:
            problems.append('Search %d "%s" converted in this period, so it cannot be Exclude. It stays Keep.' % (term["id"], term["search_term"]))
            continue
        if verdict == "Exclude" and term["class"] == "Keep":
            problems.append('Search %d "%s" is a brand search, so it cannot be Exclude. It stays Keep.' % (term["id"], term["search_term"]))
            continue
        term["verdict"] = verdict
        term["reason"] = (row.get("reason") or "").strip() or term["reason"]
        term["theme"] = (row.get("theme") or "").strip()
    return list(by_id.values()), problems


def own_keywords(path):
    meta, rows = io.read_report(path)
    io.require(meta, ["keyword"], "keywords report")
    keywords = []
    for row in rows:
        text = (row.get("keyword") or "").strip()
        if not text or text.startswith("-"):
            continue
        keywords.append({"search_term": text.strip('[]"+'), "campaign": row.get("campaign", ""), "ad_group": row.get("ad_group", "")})
    return keywords


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True)
    parser.add_argument("--keywords", help="keywords report export, to protect the account's own keywords")
    args = parser.parse_args()

    measured = outputs.read_json(os.path.join(args.work, "measured.json"))
    verdict_path = os.path.join(args.work, "verdicts.json")
    if not os.path.exists(verdict_path):
        raise SystemExit("No verdicts.json in %s. Copy verdicts.template.json to verdicts.json and fill it in first." % args.work)
    filled = outputs.read_json(verdict_path)
    terms, problems = final_verdicts(measured, filled.get("verdicts", []))
    keywords = own_keywords(args.keywords) if args.keywords else []
    protected = [t for t in terms if t["verdict"] in ("Keep", "Watch")]
    excluded = [t for t in terms if t["verdict"] == "Exclude"]

    known_campaigns = set(measured.get("campaigns") or {t["campaign"] for t in terms})
    results, seen = [], set()
    for neg in filled.get("negatives", []):
        text = (neg.get("text") or "").strip().strip('[]"').lstrip("-").strip().lower()
        match = (neg.get("match") or "phrase").strip().lower()
        level = (neg.get("level") or "campaign").strip().lower().replace(" ", "_")
        if not text:
            continue
        if match not in negatives.MATCH_TYPES:
            problems.append('Negative "%s" has match type "%s". Use exact, phrase or broad.' % (text, match))
            continue
        if level not in ("account", "campaign", "ad_group"):
            problems.append('Negative "%s" has level "%s". Use account, campaign or ad_group.' % (text, level))
            continue
        if level != "account" and not neg.get("campaign"):
            problems.append('Negative "%s" needs a campaign name, or the level account.' % text)
            continue
        if level != "account" and neg["campaign"] not in known_campaigns:
            problems.append('Negative "%s" names the campaign "%s", which is not in this report. Copy the campaign name exactly.' % (text, neg["campaign"]))
            continue
        item = {"text": text, "match": match, "level": level, "campaign": neg.get("campaign", ""),
                "ad_group": neg.get("ad_group", ""), "why": (neg.get("why") or "").strip()}
        key = (text.lower(), match, level, item["campaign"], item["ad_group"])
        if key in seen:
            continue
        seen.add(key)
        hits = lambda pool: [t for t in pool if negatives.in_scope(item, t) and negatives.blocks(text, match, t["search_term"])]  # noqa: E731
        blocked_good = hits(protected)
        blocked_keywords = hits(keywords)
        stops = hits(excluded)
        item["blocks_protected"] = [{"search_term": t["search_term"], "verdict": t["verdict"], "campaign": t["campaign"],
                                     "cost": round(t["cost"], 2), "conversions": t["conversions"]} for t in blocked_good]
        item["blocks_keywords"] = [{"keyword": k["search_term"], "campaign": k["campaign"], "ad_group": k["ad_group"]} for k in blocked_keywords]
        item["stops_count"] = len(stops)
        item["stops_cost"] = round(sum(t["cost"] for t in stops), 2)
        item["stops_ids"] = [t["id"] for t in stops]
        item["passed"] = not blocked_good and not blocked_keywords
        # A negative that stops nothing here is not evidence based, so it is left out of the files.
        item["unused"] = item["passed"] and not stops
        item["note"] = "" if stops else "Stops no Exclude search in this report, so it is left out of the files."
        results.append(item)

    covered = set()
    for item in results:
        if item["passed"]:
            covered.update(item["stops_ids"])
        if item.get("unused"):
            problems.append('Negative "%s" stops no Exclude search in this report, so it is left out of the files.' % item["text"])
    uncovered = [t for t in excluded if t["id"] not in covered]

    outputs.write_json(os.path.join(args.work, "checked.json"), {
        "verdicts_hash": file_hash(verdict_path),
        "keywords_checked": bool(keywords),
        "terms": terms, "negatives": results, "problems": problems,
        "uncovered_excludes": [{"id": t["id"], "search_term": t["search_term"], "cost": round(t["cost"], 2)} for t in uncovered],
    })

    passed = [r for r in results if r["passed"] and not r.get("unused")]
    rejected = [r for r in results if not r["passed"]]
    print("NEGATIVE KEYWORD TEST")
    print("  Tested against %d Keep and Watch searches%s." % (len(protected), " and %d of the account's own keywords" % len(keywords) if keywords else ""))
    print("  Passed: %d   Rejected: %d" % (len(passed), len(rejected)))
    for problem in problems:
        print("  NOTE: " + problem)
    if rejected:
        print()
        print("REJECTED. Narrow these or drop them, then run this test again.")
        for item in rejected:
            print('  "%s" (%s, %s%s)' % (item["text"], item["match"], item["level"], ", " + item["campaign"] if item["campaign"] else ""))
            for hit in item["blocks_protected"]:
                print('     would block the %s search "%s" (cost %.2f, conversions %.2f)' % (hit["verdict"], hit["search_term"], hit["cost"], hit["conversions"]))
            for hit in item["blocks_keywords"]:
                print('     would block your own keyword "%s" in %s' % (hit["keyword"], hit["campaign"]))
    if uncovered:
        print()
        print("EXCLUDE SEARCHES NO PASSING NEGATIVE COVERS YET")
        for term in uncovered[:25]:
            print('  %d "%s" (cost %.2f)' % (term["id"], term["search_term"], term["cost"]))
    if not rejected and not uncovered:
        print("  Every Exclude search is covered and no negative blocks anything worth keeping.")
    print()
    print("Next: python3 scripts/write_outputs.py --work %s --out OUTPUTDIR" % args.work)


if __name__ == "__main__":
    main()
