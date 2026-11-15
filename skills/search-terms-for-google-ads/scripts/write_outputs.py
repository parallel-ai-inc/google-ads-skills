#!/usr/bin/env python3
"""Step 3 of the search term review: write the deliverables.

Writes a workbook, a review CSV, a Google Ads Editor import file with the
negatives that passed the test, and a summary. Every number comes from the
measured data. Nothing here carries a vendor name, so the files can go to a
client as they are.

    python3 write_outputs.py --work WORKDIR --out OUTPUTDIR
"""
import argparse
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics, outputs, xlsx  # noqa: E402

ORDER = ("Exclude", "Watch", "Keep", "Already excluded")


def two(value):
    return "" if value is None else "%.2f" % value


def shown(value):
    return "" if value is None else "{:,.2f}".format(value)


def group(terms, key):
    """Exclude searches totalled by a field, largest cost first."""
    slots = {}
    for term in terms:
        if term["verdict"] != "Exclude":
            continue
        name = term.get(key) or "Not grouped"
        slot = slots.setdefault(name, {"name": name, "searches": 0, "clicks": 0.0, "cost": 0.0})
        slot["searches"] += 1
        slot["clicks"] += term["clicks"]
        slot["cost"] += term["cost"]
    return sorted(slots.values(), key=lambda s: -s["cost"])


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    measured = outputs.read_json(os.path.join(args.work, "measured.json"))
    checked_path = os.path.join(args.work, "checked.json")
    if not os.path.exists(checked_path):
        raise SystemExit("Run check_negatives.py first. No negative is written until it has been tested.")
    checked = outputs.read_json(checked_path)
    with open(os.path.join(args.work, "verdicts.json"), "rb") as handle:
        if hashlib.sha256(handle.read()).hexdigest() != checked["verdicts_hash"]:
            raise SystemExit("verdicts.json changed after the last test. Run check_negatives.py again.")

    terms = checked["terms"]
    passed = [n for n in checked["negatives"] if n["passed"] and not n.get("unused")]
    rejected = [n for n in checked["negatives"] if not n["passed"]]
    covered_by = {}
    for neg in passed:
        for term_id in neg["stops_ids"]:
            covered_by.setdefault(term_id, neg)

    totals = measured["totals"]
    line = measured["line"]["value"]
    counts = {name: {"searches": 0, "cost": 0.0} for name in ORDER}
    for term in terms:
        slot = counts.setdefault(term["verdict"], {"searches": 0, "cost": 0.0})
        slot["searches"] += 1
        slot["cost"] += term["cost"]
    exclude = counts["Exclude"]
    covered_cost = sum(t["cost"] for t in terms if t["verdict"] == "Exclude" and t["id"] in covered_by)
    themes = group(terms, "theme")
    by_campaign = group(terms, "campaign")
    not_listed = measured.get("not_listed") or {}

    out = outputs.ensure_dir(args.out)
    review_header = ["Search term", "Campaign", "Ad group", "Match type", "Clicks", "Impr.", "Cost", "Conversions",
                     "Cost / conv.", "Verdict", "Reason", "Theme", "Negative keyword", "Negative match type", "Negative level"]
    ordered = sorted(terms, key=lambda t: (ORDER.index(t["verdict"]) if t["verdict"] in ORDER else 9, -t["cost"]))

    def review_row(term, as_text):
        neg = covered_by.get(term["id"]) if term["verdict"] == "Exclude" else None
        money = two if as_text else (lambda v: round(v, 2) if v is not None else None)
        return [term["search_term"], term["campaign"], term["ad_group"], ", ".join(term["match_types"]),
                int(term["clicks"]), int(term["impressions"]), money(term["cost"]), money(term["conversions"]),
                money(term.get("cpa")), term["verdict"], term["reason"], term.get("theme", ""),
                neg["text"] if neg else "", neg["match"] if neg else "", neg["level"].replace("_", " ") if neg else ""]

    outputs.write_csv(os.path.join(out, "search-term-review.csv"), review_header, [review_row(t, True) for t in ordered])

    _, editor_count = outputs.write_editor_negatives(os.path.join(out, "negatives-for-google-ads-editor.csv"), passed)
    account_path, account_count = outputs.write_account_list(os.path.join(out, "account-level-negatives.txt"), passed)
    if not account_count:
        os.remove(account_path)

    def blocked_text(neg):
        parts = ['the %s search "%s" (cost %s, conversions %s)' % (h["verdict"], h["search_term"], shown(h["cost"]), shown(h["conversions"])) for h in neg["blocks_protected"]]
        parts += ['your own keyword "%s"' % h["keyword"] for h in neg["blocks_keywords"]]
        return ", ".join(parts)

    summary = [
        ["Report", " / ".join(measured["title_rows"]) or measured["report"]],
        ["Searches read", str(totals["searches"])],
        ["Clicks", "{:,.0f}".format(totals["clicks"])],
        ["Cost", metrics.money(totals["cost"])],
        ["Conversions", "{:,.2f}".format(totals["conversions"])],
        ["Cost per conversion, all listed searches", metrics.money(totals["baseline_cpa"])],
        ["Spent enough to judge, with no conversions", metrics.money(line)],
        ["Where that amount comes from", measured["line"]["source"]],
        ["Exclude searches", str(exclude["searches"])],
        ["Cost on Exclude searches", metrics.money(exclude["cost"])],
        ["Share of listed cost on Exclude searches", metrics.pct(metrics.div(exclude["cost"], totals["cost"]))],
        ["Cost the passing negatives would have stopped", metrics.money(covered_cost)],
        ["Watch searches", str(counts["Watch"]["searches"])],
        ["Keep searches", str(counts["Keep"]["searches"])],
        ["Already excluded in the account", str(counts["Already excluded"]["searches"])],
        ["Negatives proposed", str(len(checked["negatives"]))],
        ["Negatives that passed the test", str(len(passed))],
        ["Negatives rejected by the test", str(len(rejected))],
        ["Own keywords included in the test", "Yes" if checked["keywords_checked"] else "No keywords report was provided"],
    ]
    if not_listed.get("cost"):
        summary.insert(5, ["Cost on searches Google does not list (outside this review)", metrics.money(not_listed["cost"])])

    book = xlsx.Workbook()
    book.add_sheet("Summary", ["Measure", "Value"], summary, widths={0: 52, 1: 70})
    book.add_sheet("Review", review_header, [review_row(t, False) for t in ordered],
                   formats={4: "int", 5: "int", 6: "money", 7: "money", 8: "money"}, widths={0: 38, 10: 60})
    book.add_sheet("Negatives to add", ["Negative keyword", "Match type", "Level", "Campaign", "Ad group", "Searches it stops", "Cost it stops", "Why"],
                   [[n["text"], n["match"], n["level"].replace("_", " "), n["campaign"], n["ad_group"], n["stops_count"], n["stops_cost"], n["why"]] for n in passed],
                   formats={5: "int", 6: "money"}, widths={7: 60})
    book.add_sheet("Rejected negatives", ["Negative keyword", "Match type", "Level", "Campaign", "Would have blocked"],
                   [[n["text"], n["match"], n["level"].replace("_", " "), n["campaign"], blocked_text(n)] for n in rejected], widths={4: 110})
    book.add_sheet("Waste by theme", ["Theme", "Searches", "Clicks", "Cost"],
                   [[s["name"], s["searches"], int(s["clicks"]), round(s["cost"], 2)] for s in themes], formats={1: "int", 2: "int", 3: "money"}, widths={0: 40})
    book.add_sheet("Waste by campaign", ["Campaign", "Exclude searches", "Clicks", "Cost"],
                   [[s["name"], s["searches"], int(s["clicks"]), round(s["cost"], 2)] for s in by_campaign], formats={1: "int", 2: "int", 3: "money"}, widths={0: 40})
    book.add_sheet("Words with no conversions", ["Word or phrase, in two or more searches", "Searches", "Clicks", "Cost"],
                   [[g["phrase"], g["searches"], int(g["clicks"]), round(g["cost"], 2)] for g in measured["waste_words"]],
                   formats={1: "int", 2: "int", 3: "money"}, widths={0: 44})
    book.save(os.path.join(out, "search-term-review.xlsx"))

    lines = ["# Search term review", ""]
    lines += ["%s." % title for title in measured["title_rows"]] or [measured["report"]]
    lines += ["", "## What was read", "",
              "- %d searches, %s clicks, %s cost, %s conversions." % (totals["searches"], "{:,.0f}".format(totals["clicks"]), metrics.money(totals["cost"]), "{:,.2f}".format(totals["conversions"]))]
    if measured.get("reconcile"):
        lines.append("- The file's own total for listed searches is %s. The rows add up to %s." % (metrics.money(measured["reconcile"]["file_total_cost"]), metrics.money(measured["reconcile"]["rows_cost"])))
    if not_listed.get("cost"):
        lines.append("- Google lists a further %s of cost on low volume searches it does not show. Those are outside this review, and every share below is of the listed cost." % metrics.money(not_listed["cost"]))
    lines.append("- A search with no conversions has spent enough to judge at %s. That is %s." % (metrics.money(line), measured["line"]["source"]))
    if measured["ai_max"]["present"]:
        lines.append("- AI Max matches carry %s of cost." % metrics.pct(measured["ai_max"]["share_of_cost"]))
    lines += ["", "## What it found", "",
              "- **%d searches to exclude,** costing %s with no conversions. That is %s of the listed cost." % (exclude["searches"], metrics.money(exclude["cost"]), metrics.pct(metrics.div(exclude["cost"], totals["cost"]))),
              "- **%d to watch** and **%d to keep.**%s" % (counts["Watch"]["searches"], counts["Keep"]["searches"],
                                                         " %d already excluded in the account." % counts["Already excluded"]["searches"] if counts["Already excluded"]["searches"] else "")]
    if themes and not (len(themes) == 1 and themes[0]["name"] == "Not grouped"):
        lines += ["", "### Where the wasted spend goes", "",
                  outputs.md_table(["Theme", "Searches", "Cost"], [[s["name"], s["searches"], shown(s["cost"])] for s in themes])]
    if len(by_campaign) > 1:
        lines += ["", "### By campaign", "",
                  outputs.md_table(["Campaign", "Exclude searches", "Cost"], [[s["name"], s["searches"], shown(s["cost"])] for s in by_campaign])]
    top = [t for t in ordered if t["verdict"] == "Exclude"][:10]
    if top:
        lines += ["", "### Costliest searches to exclude", "",
                  outputs.md_table(["Search", "Campaign", "Clicks", "Cost", "Reason"], [[t["search_term"], t["campaign"], int(t["clicks"]), shown(t["cost"]), t["reason"]] for t in top])]
    if measured["waste_words"]:
        lines += ["", "### Words in two or more searches that never converted", "",
                  outputs.md_table(["Word or phrase", "Searches", "Cost"], [[g["phrase"], g["searches"], shown(g["cost"])] for g in measured["waste_words"][:5]])]
    lines += ["", "## Negative keywords", "",
              "- %d proposed, %d passed the test, %d rejected." % (len(checked["negatives"]), len(passed), len(rejected)),
              "- The passing negatives would have stopped %s of the cost on Exclude searches." % metrics.money(covered_cost),
              "- " + ("The test also covered the account's own keywords." if checked["keywords_checked"] else "No keywords report was provided, so the account's own keywords were not part of the test.")]
    if passed:
        lines += ["", outputs.md_table(["Negative keyword", "Match type", "Level", "Campaign", "Searches it stops", "Cost it stops"],
                                       [[n["text"], n["match"], n["level"].replace("_", " "), n["campaign"], n["stops_count"], shown(n["stops_cost"])] for n in passed])]
    if rejected:
        lines += ["", "### Rejected by the test", ""]
        lines += ['- "%s" (%s) would have blocked %s.' % (neg["text"], neg["match"], blocked_text(neg)) for neg in rejected]
    if checked["uncovered_excludes"]:
        lines += ["", "%d Exclude searches are not covered by a passing negative yet." % len(checked["uncovered_excludes"])]
    lines += ["", "## What this review did not cover", "",
              "- Searches Google leaves out of the report for low volume.",
              "- Searches that did not happen in this date range. A negative that is safe here can still block a good search that did not appear.",
              "- Misspellings. This test uses the exact words. Google's pages disagree on whether negative keywords also block misspellings, so a negative can block slightly more in the account than shown, or miss a misspelled search. Where misspelled brand searches matter, use brand exclusions.",
              "- Plural and singular forms. Each needs its own negative, and only forms seen in this report were tested."]
    lines += ["", "## Files", "",
              "- `search-term-review.xlsx`: summary, every search with its verdict, negatives to add, rejected negatives, waste by theme and by campaign.",
              "- `search-term-review.csv`: the same review as one table.",
              "- `negatives-for-google-ads-editor.csv`: %d campaign or ad group %s, ready to import in Google Ads Editor. Review there before posting." % (editor_count, "negative" if editor_count == 1 else "negatives")]
    if account_count:
        lines.append("- `account-level-negatives.txt`: %d account level %s. Paste them into a negative keyword list in Google Ads, then apply the list to the campaigns. Quotation marks mean phrase match and square brackets mean exact match." % (account_count, "negative" if account_count == 1 else "negatives"))
    text = "\n".join(lines) + "\n"
    with open(os.path.join(out, "search-term-review.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote the files to %s" % out)


if __name__ == "__main__":
    main()
