#!/usr/bin/env python3
"""Step 2 of the performance reviews: write the deliverables.

Joins the numbers in WORK/review.json with the judgment in WORK/notes.json (a
summary for each review and the actions, each labeled Official or
Practitioner rule) and writes performance-review.json, performance-review.xlsx
(one tab per review) and performance-review.md, a summary a client could read.
Every number comes from review.json. Nothing here carries a vendor name.

    python3 scripts/write_report.py --work WORK --out OUTPUT
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import outputs, xlsx  # noqa: E402

SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LABELS = ("Official", "Practitioner rule")
MD_ROWS = 10
LIMITS = [
    "Each review reads one export for one date range. Recent days can still gain conversions that are reported late.",
    "Segments are judged against this account's own numbers in the same file, not against a target or an industry figure.",
    "The same spend sits in several reviews (a click has a device, an hour and a location), so money is never added across reviews.",
    "Quality Score is a diagnostic reported for Search keywords, not a figure to optimize as an average (Official). It is never averaged here.",
    "An export shows how ads did, not why. Ad fatigue over time, the content of a page or a video, and policy detail need the "
    "account itself or the asset.",
]


def m(value):
    return "" if value is None else "{:,.2f}".format(value)


def load(work):
    review_path, notes_path = os.path.join(work, "review.json"), os.path.join(work, "notes.json")
    if not os.path.isfile(review_path):
        raise SystemExit("Run review.py first. There is no review.json in %s." % work)
    if not os.path.isfile(notes_path):
        raise SystemExit("Copy %s to %s and fill it in first." % (os.path.join(work, "notes.template.json"), notes_path))
    review, notes = outputs.read_json(review_path), outputs.read_json(notes_path)
    problems, missing = [], []
    if not (notes.get("headline") or "").strip():
        problems.append("the headline is empty")
    given = notes.get("reviews") or {}
    for key in given:
        if key not in review["reviews"]:
            problems.append("notes name a review that did not run: %s" % key)
    for key, item in review["reviews"].items():
        note = given.get(key) or {}
        if not (note.get("summary") or "").strip():
            missing.append(item["title"])
        kept = []
        for action in note.get("actions") or []:
            text = (action.get("action") or "").strip()
            if not text:
                continue
            label = (action.get("label") or "").strip()
            if label not in LABELS:
                problems.append("an action in %s has the label '%s'; use Official or Practitioner rule" % (item["title"], label))
            source = (action.get("source") or "").strip()
            if label == "Official" and not (source and os.path.isfile(os.path.join(SKILL, source))):
                problems.append("an Official action in %s needs a source file from references/ (got '%s')" % (item["title"], source))
            elif source and not os.path.isfile(os.path.join(SKILL, source)):
                problems.append("an action in %s names a source that is not a file in this skill: '%s'" % (item["title"], source))
            kept.append({"action": text, "label": label, "source": source})
        item["summary"], item["actions"] = (note.get("summary") or "").strip(), kept
    if missing:
        problems.append("these reviews have no summary yet: %s" % ", ".join(missing))
    if problems:
        raise SystemExit("notes.json is not ready: %s." % "; ".join(problems))
    review["headline"] = notes["headline"].strip()
    review["assumptions"] = [a for a in notes.get("assumptions") or [] if str(a).strip()]
    return review


def money_rows(review):
    """(scope, money) pairs for the summary, one per level and split. Never added together."""
    money = review.get("money")
    if not money:
        return []
    if "account" in money or "inside_campaigns" in money:
        money = {"": money}
    rows = []
    for split, levels in money.items():
        for level, label in (("account", "account level"), ("inside_campaigns", "inside campaigns")):
            if levels.get(level):
                rows.append((("%s, " % split if split else "") + label, levels[level]))
    return rows


def segments(n):
    return "1 segment" if n == 1 else "%d segments" % n


def file_line(f):
    rec = f["reconcile"]
    when = "%s to %s" % (f["period"]["start"], f["period"]["end"]) if f["period"] else "no date range in the file"
    check = ("its rows match the file's own total, %s" % rec["label"] if rec and rec["matches"]
             else "its rows do not match the file's own total (%s against %s)" % (m(rec["rows"]), m(rec["file_total"])) if rec
             else "it has no total row to check against")
    others = [t for t in (rec or {}).get("totals", []) if t["label"] != rec["label"] and abs(t["gap"]) > 0.005]
    if others:
        check += ". Other totals: " + "; ".join("%s is %s %s the rows, as it covers %s" % (
            t["label"], m(abs(t["gap"])), "more than" if t["gap"] > 0 else "less than", t["meaning"]) for t in others)
    return "%s (%s), %s, %d rows, cost %s; %s." % (f["report"][:1].upper() + f["report"][1:], f["file"], when, f["rows"], m(f["cost"]), check)


def write_markdown(path, review):
    out = ["# Google Ads performance review", ""]
    out += ["## The answer", "", review["headline"], ""]
    out += ["## What I read", ""] + ["- " + file_line(f) for f in review["files"]]
    brand = review["brand"]
    if brand["campaigns"] or brand["terms"]:
        out.append("- Brand set apart from the baselines: campaigns %s; terms %s."
                   % (", ".join(brand["campaigns"]) or "none", ", ".join(brand["terms"]) or "none"))
    else:
        out.append("- No brand campaigns or terms were given, so brand results are inside every baseline.")
    out += ["- Assumed: %s" % a for a in review["assumptions"]]
    out.append("")
    for item in review["reviews"].values():
        out += ["## %s" % item["title"], "", item["summary"], ""]
        for scope, money in money_rows(item):
            wasted = ("wasted %s, spend with no conversions on %s that spent enough to judge" % (m(money["wasted"]), segments(money["wasted_count"]))
                      if money["wasted_count"] else "nothing wasted")
            less = ("less efficient %s, the cost above the baseline on %s judged worse" % (m(money["less_efficient"]), segments(money["worse_count"]))
                    if money["worse_count"] else "nothing judged less efficient")
            out.append("- **Money, %s:** %s; %s. The two are never added." % (scope, wasted, less))
        out += ["- " + line for line in item["facts"]]
        out.append("")
        for table in item["tables"]:
            if table["rows"]:
                out += ["**%s**" % table["title"], "", outputs.md_table(table["header"], table["rows"][:MD_ROWS])]
                if len(table["rows"]) > MD_ROWS:
                    out.append("\n%d more rows are in the workbook." % (len(table["rows"]) - MD_ROWS))
                out.append("")
        if item["actions"]:
            out += ["**What to do**", ""]
            out += ["%d. %s (%s)" % (i, a["action"], a["label"]) for i, a in enumerate(item["actions"], start=1)]
            out.append("")
    if review.get("across"):
        out += ["## Across reports", ""] + ["- " + line for line in review["across"]] + [""]
    out += ["## How the numbers were made", ""] + ["- " + line for line in review["rules"]]
    for item in review["reviews"].values():
        out += ["- %s: %s" % (item["title"], line) for line in item["left_out"]]
    out += ["", "## What this did not cover", ""]
    out += ["- %s was not run. %s" % (n["title"], n["unlock"]) for n in review["not_run"]]
    out += ["- " + item["pointer"] for item in review["reviews"].values() if item.get("pointer")]
    out += ["- " + line for line in LIMITS]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(out).replace("\n\n\n", "\n\n") + "\n")


def write_workbook(path, review):
    book = xlsx.Workbook()
    summary = []
    for item in review["reviews"].values():
        period = item.get("period") or {}
        base = item.get("baseline") or {}
        levels = money_rows(item) or [("", None)]
        for scope, money in levels:
            summary.append([item["title"] + (", " + scope if scope else ""), item["report"], period.get("start", ""), period.get("end", ""),
                            base.get("cpa") if isinstance(base.get("cpa"), (int, float)) else None,
                            money["wasted"] if money else None, money["less_efficient"] if money else None,
                            money["too_early"] if money else None, item["summary"]])
    book.add_sheet("Summary", ["Review", "Report", "From", "To", "Baseline cost / conv.", "Wasted", "Less efficient",
                               "No conversions under the line", "Summary"], summary,
                   formats={4: "money", 5: "money", 6: "money", 7: "money", 8: "wrap"}, widths={8: 80})
    for item in review["reviews"].values():
        for tab in item["tabs"]:
            book.add_sheet(tab["name"], tab["header"], tab["rows"], formats={int(k): v for k, v in tab["formats"].items()})
    actions = [[item["title"], i, a["action"], a["label"], a["source"]] for item in review["reviews"].values()
               for i, a in enumerate(item["actions"], start=1)]
    book.add_sheet("Actions", ["Review", "Order", "Action", "Basis", "Source"], actions, formats={2: "wrap"}, widths={2: 90})
    rules = [[line] for line in review["rules"]] + [["%s: %s" % (item["title"], line)] for item in review["reviews"].values()
                                                    for line in item["left_out"]]
    book.add_sheet("Rules used", ["Rule"], rules, formats={0: "wrap"}, widths={0: 120})
    files = [[f["file"], f["report"], (f["period"] or {}).get("start", ""), (f["period"] or {}).get("end", ""), f["rows"], f["cost"],
              (f["reconcile"] or {}).get("file_total"), "Yes" if (f["reconcile"] or {}).get("matches") else "No",
              ", ".join(f["columns_not_used"])] for f in review["files"]]
    book.add_sheet("Files read", ["File", "Report", "From", "To", "Rows", "Cost in rows", "File's own total", "Matches", "Columns not used"],
                   files, formats={4: "int", 5: "money", 6: "money"})
    not_run = [[n["title"], n["unlock"]] for n in review["not_run"]]
    book.add_sheet("Reviews not run", ["Review", "What would unlock it"], not_run, formats={1: "wrap"}, widths={1: 100})
    book.save(path)


def main():
    parser = argparse.ArgumentParser(description="Write the performance review deliverables.")
    parser.add_argument("--work", required=True, help="The folder review.py wrote to")
    parser.add_argument("--out", required=True, help="Folder for the deliverables")
    args = parser.parse_args()
    review = load(args.work)
    outputs.ensure_dir(args.out)
    outputs.write_json(os.path.join(args.out, "performance-review.json"), review)
    write_workbook(os.path.join(args.out, "performance-review.xlsx"), review)
    md = os.path.join(args.out, "performance-review.md")
    write_markdown(md, review)
    actions = sum(len(item["actions"]) for item in review["reviews"].values())
    for name in ("performance-review.md", "performance-review.xlsx", "performance-review.json"):
        print(os.path.join(args.out, name))
    print("Wrote %d reviews with %d actions. Open performance-review.md for the client summary and the workbook for every segment."
          % (len(review["reviews"]), actions))


if __name__ == "__main__":
    main()
