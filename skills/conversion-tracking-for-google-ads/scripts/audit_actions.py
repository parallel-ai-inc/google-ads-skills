#!/usr/bin/env python3
"""Step 1 of the conversion tracking review: audit the conversion actions.

Reads the conversions summary downloaded from Google Ads (Goals, Conversions,
All conversions, Download) and checks that the account counts the right things, once,
with the right settings. It finds Primary actions that are not recording or
recorded nothing, two Primary actions in one category from different sources,
purchase actions with no value, lead actions counted as Every, Primary page
view actions and categories with only Secondary actions. It also shows which
actions carry the conversions. Writes a JSON file, a workbook and a summary,
and prints the summary.

    python3 scripts/audit_actions.py SUMMARY_EXPORT --out OUTPUTDIR
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics, outputs, xlsx  # noqa: E402
import tracking as t  # noqa: E402

MOST = 0.5  # "carry most of the conversions" means more than half of them.

# Finding types, in the order they are ranked: risk to bidding first, then
# data loss, then settings that change what is counted.
TYPES = [
    ("primary_not_recording", "Primary actions that are not recording", ["status", "bidding", "repair_first"], "down"),
    ("primary_no_volume", "Primary actions with no conversions in this date range", ["bidding", "repair_first"], "down"),
    ("double_count", "Two Primary actions in one category from different sources", ["double", "double_fix", "bidding"], "double"),
    ("purchase_no_value", "Purchase actions with no value", ["value"], "value"),
    ("lead_every", "Lead actions counted as Every", ["count", "count_future"], "lead_count"),
    ("primary_page_view", "Primary page view actions", ["outcome", "bidding"], "outcome"),
    ("secondary_only_category", "Categories with only Secondary actions", ["bidding"], "outcome"),
]
TITLES = {key: title for key, title, _, _ in TYPES}


def share_text(value, label):
    return "n/a" if value is None else "%s of %s" % (metrics.pct(value), label)


def no_value(action):
    setting = action["value_setting"].lower()
    if setting and any(word in setting for word in ("don't use", "do not use", "no value", "not use a value")):
        return True
    return action["value"] is not None and bool(action["volume"]) and action["value"] == 0


def assess(meta, actions, info):
    """Every audit finding, ranked and numbered F1, F2 and so on. find_breaks.py uses it too."""
    has = meta["columns"]
    volume_key, volume_label = info["volume_key"], info["volume_label"] or "conversions"
    span = t.title_range(meta)
    basis = "%s over the whole report%s" % (volume_label, " (%s to %s)" % (span[0].isoformat(), span[1].isoformat()) if span else "")
    total = sum(a["volume"] for a in actions) if volume_key else None
    conv_total = sum(a["conversions"] for a in actions) if "conversions" in has else None
    for a in actions:
        a["share"] = metrics.div(a["volume"], total) if volume_key else None
        a["conversions_share"] = metrics.div(a["conversions"], conv_total) if conv_total else None
        a["findings"] = []

    findings, not_checked = [], []

    def add(kind, items, detail, family="other", category=""):
        key, title, rules, situation = next(x for x in TYPES if x[0] == kind)
        share = sum(a["share"] or 0 for a in items) if volume_key else None
        finding = {"id": "", "type": kind, "title": title, "actions": [a["name"] for a in items], "category": category,
                   "detail": detail, "share": share, "rules": [t.rule(r) for r in rules],
                   "checks": t.outside_checks(situation, family, "it stopped" if situation == "down" else None)}
        findings.append(finding)
        for a in items:
            a["findings"].append(title)

    def described(a):
        bits = [a["source"] or "source not shown", a["category"] or "category not shown"]
        if a["status"]:
            bits.append("status " + a["status"])
        if volume_key:
            bits.append("%s %s, %s" % (volume_label, t.two(a["volume"]), share_text(a["share"], basis)))
        return "%s (%s)" % (a["name"], ", ".join(bits))

    primary = [a for a in actions if a["optimization"] == "Primary"]
    if "optimization" not in has:
        not_checked.append("Primary or Secondary: the file has no Action optimization column, so every check that needs it was skipped.")

    if "status" in has:
        for a in sorted((a for a in primary if a["status_class"] in ("not_recording", "needs_attention")), key=lambda a: -(a["share"] or 0)):
            add("primary_not_recording", [a], "%s is Primary, so bidding uses it, and its status is %s." % (described(a), a["status"]), a["family"])
    else:
        not_checked.append("Status: the file has no Status column, so actions that stopped recording could not be found from it.")
    if volume_key:
        for a in primary:
            if not a["volume"] and a["status_class"] not in ("not_recording", "needs_attention"):
                add("primary_no_volume", [a], "%s is Primary and recorded no conversions in this date range." % described(a), a["family"])

    by_category = {}
    for a in actions:
        by_category.setdefault(a["category"].lower(), []).append(a)
    if "source" in has and "category" in has:
        for key, items in sorted(by_category.items()):
            live = [a for a in items if a["optimization"] == "Primary" and key]
            if len({a["source"].lower() for a in live if a["source"]}) >= 2:
                live.sort(key=lambda a: -(a["share"] or 0))
                valued = [a["name"] for a in live if a["value"]]
                detail = "In %s, %d Primary actions come from %d different sources: %s." % (
                    live[0]["category"], len(live), len({a["source"].lower() for a in live}), "; ".join(described(a) for a in live))
                if len(valued) >= 2:
                    detail += " %s carry a value, so value can be counted twice too. %s" % (" and ".join(valued), t.rule_text("value_non_purchase"))
                family = "analytics" if any(a["family"] == "analytics" for a in live) else live[0]["family"]
                add("double_count", live, detail, family, live[0]["category"])
    else:
        not_checked.append("Double counting: the file needs Conversion source and Category to find two Primary actions for one event.")

    if "category" in has:
        purchases = [a for a in actions if a["kind"] == "purchase"]
        if purchases and info["value_key"] is None and "value_setting" not in has:
            not_checked.append("Values: the file has no value column, so purchase actions with no value could not be found.")
        for a in purchases:
            if no_value(a):
                add("purchase_no_value", [a], "%s is a purchase action and %s." % (
                    described(a), "its value setting reads %s" % a["value_setting"] if a["value_setting"] else "its conversions carry no value"), a["family"])
        if "count" in has:
            for a in sorted((a for a in actions if a["kind"] == "lead" and a["count"] == "Every"), key=lambda a: -(a["share"] or 0)):
                add("lead_every", [a], "%s is a %s action counted as Every, so a second form or call from one click counts again." % (
                    described(a), a["optimization"] or "lead"), a["family"])
        else:
            not_checked.append("Count: the file has no Count column, so lead actions counted as Every could not be found.")
        for a in primary:
            if a["kind"] == "page_view":
                add("primary_page_view", [a], "%s is a page view and Primary, so bidding treats a page view as a conversion." % described(a), a["family"])
        if "optimization" in has:
            for key, items in sorted(by_category.items()):
                if key and all(a["optimization"] == "Secondary" for a in items):
                    add("secondary_only_category", items, "%s has only Secondary actions: %s. Bidding does not use them unless a custom goal includes them." % (
                        items[0]["category"], "; ".join(described(a) for a in items)), "other", items[0]["category"])
    else:
        not_checked.append("Categories: the file has no Category column, so the purchase, lead, page view and category checks were skipped.")

    order = [key for key, _, _, _ in TYPES]
    findings.sort(key=lambda f: (order.index(f["type"]), -(f["share"] or 0)))
    for number, f in enumerate(findings, start=1):
        f["id"] = "F%d" % number
    return {"volume_key": volume_key, "volume_label": volume_label, "basis": basis, "total": total, "conv_total": conv_total,
            "findings": findings, "not_checked": not_checked, "primary": primary, "by_category": by_category}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("summary", help="the conversions summary export")
    parser.add_argument("--out", required=True, help="folder for the files")
    args = parser.parse_args()

    meta, actions, info = t.read_actions(args.summary)
    has = meta["columns"]
    if not actions:
        raise SystemExit("The conversions summary has no active conversion actions in it. In Google Ads open Goals, "
                         "Conversions, All conversions, and download the table with its columns.")
    found = assess(meta, actions, info)
    volume_key, volume_label, basis = found["volume_key"], found["volume_label"], found["basis"]
    total, conv_total, findings, not_checked = found["total"], found["conv_total"], found["findings"], found["not_checked"]
    primary, by_category = found["primary"], found["by_category"]

    # Reconcile with the file's own total rows. Removed actions are listed in
    # the file too, so they are part of the rows the total covers.
    every = actions + info["removed"]
    sums, doubtful = t.file_totals(args.summary, meta, [k for k in (volume_key,) if k])
    check = t.reconcile(sums, volume_key, sum(a["volume"] or 0 for a in every), len(every)) if volume_key else None


    # Where the conversions are: the fewest actions that carry more than half.
    ranked = sorted(actions, key=lambda a: -(a["volume"] or 0)) if volume_key else []
    running, carriers = 0.0, []
    for a in ranked:
        running += a["share"] or 0
        a["cumulative_share"] = running
        if total and (not carriers or carriers[-1]["cumulative_share"] <= MOST):
            carriers.append(a)
    categories = []
    for key, items in sorted(by_category.items(), key=lambda kv: -sum(a["volume"] or 0 for a in kv[1])):
        volume = sum(a["volume"] or 0 for a in items) if volume_key else None
        categories.append({"category": items[0]["category"] or "(no category shown)", "actions": len(items),
                           "primary": sum(1 for a in items if a["optimization"] == "Primary"),
                           "secondary": sum(1 for a in items if a["optimization"] == "Secondary"),
                           "volume": volume, "share": metrics.div(volume, total)})

    counts = {"actions": len(actions), "primary": len(primary),
              "secondary": sum(1 for a in actions if a["optimization"] == "Secondary"),
              "optimization_not_shown": sum(1 for a in actions if not a["optimization"]),
              "removed": len(info["removed"]), "headings_left_out": len(info["headings"]), "rows_without_a_name": info["blank_rows"],
              "not_recording": sum(1 for a in actions if a["status_class"] in ("not_recording", "needs_attention"))}
    flagged = {name for f in findings for name in f["actions"]}

    out = outputs.ensure_dir(args.out)
    outputs.write_json(os.path.join(out, "conversion-audit.json"), {
        "report": os.path.basename(args.summary), "title_rows": meta["title_rows"], "columns_found": sorted(has),
        "columns_not_used": meta["unknown_headers"], "volume_column": volume_label, "volume_total": total,
        "conversions_total": conv_total, "reconcile": check, "rows_named_total": doubtful, "counts": counts,
        "headings_left_out": info["headings"], "findings": findings, "not_checked": not_checked,
        "most_means": "more than %d%% of %s" % (MOST * 100, volume_label), "carriers": [a["name"] for a in carriers],
        "categories": categories, "actions": actions, "removed": info["removed"]})

    def r2(value):
        return None if value is None else round(value, 2)

    action_rows = [[a["name"], a["optimization"], a["source"], a["category"], a["status"], a["count"], a["click_window"],
                    a["view_window"], a["attribution_model"], r2(a["volume"]), a["share"], a.get("cumulative_share"), r2(a["conversions"]),
                    r2(a["value"]), "; ".join(a["findings"])] for a in (ranked or actions)]
    action_rows += [[a["name"], a["optimization"], a["source"], a["category"], a["status"], a["count"], a["click_window"],
                     a["view_window"], a["attribution_model"], r2(a["volume"]), None, None, r2(a["conversions"]), r2(a["value"]),
                     "Removed, not audited"] for a in info["removed"]]
    summary_rows = [["Report", " / ".join(meta["title_rows"]) or os.path.basename(args.summary)],
                    ["Conversion actions audited", counts["actions"]], ["Primary", counts["primary"]], ["Secondary", counts["secondary"]],
                    ["Not recording or needing attention", counts["not_recording"]], ["Removed, listed apart", counts["removed"]],
                    ["Heading rows left out", counts["headings_left_out"]],
                    ["%s, all audited actions" % volume_label, t.two(total)], ["Findings", len(findings)],
                    ["Actions named in a finding", len(flagged)],
                    ["Check against the file's own total", t.reconcile_line(check, volume_label) if volume_key else "No conversions column"]]
    book = xlsx.Workbook()
    book.add_sheet("Summary", ["Measure", "Value"], summary_rows, formats={1: "int"}, widths={0: 40, 1: 90})
    book.add_sheet("Findings", ["Id", "Finding", "Actions", "Share of " + volume_label, "What the file shows", "Rules"],
                   [[f["id"], f["title"], "; ".join(f["actions"]), f["share"], f["detail"],
                     " ".join("%s: %s" % (r["label"], r["rule"]) for r in f["rules"])] for f in findings],
                   formats={3: "pct", 4: "wrap", 5: "wrap"}, widths={1: 34, 2: 34, 4: 80, 5: 80})
    book.add_sheet("Checks outside Google Ads", ["Who usually does it", "Check", "Label", "Source", "For findings"],
                   [[owner, i["check"]["check"], i["check"]["label"], i["check"]["source"], ", ".join(i["refs"])]
                    for owner, items in t.by_owner([(c, f["id"]) for f in findings for c in f["checks"]]) for i in items],
                   formats={1: "wrap"}, widths={0: 40, 1: 90, 3: 50})
    book.add_sheet("Conversion actions", ["Conversion action", "Action optimization", "Conversion source", "Category", "Status", "Count",
                                          "Click-through window", "View-through window", "Attribution model", volume_label,
                                          "Share of " + volume_label, "Running share", "Conversions", info["value_label"] or "Value", "Findings"],
                   action_rows, formats={9: "money", 10: "pct", 11: "pct", 12: "money", 13: "money"}, widths={0: 34, 14: 60})
    book.add_sheet("Categories", ["Category", "Actions", "Primary", "Secondary", volume_label, "Share of " + volume_label],
                   [[c["category"], c["actions"], c["primary"], c["secondary"], r2(c["volume"]), c["share"]] for c in categories],
                   formats={1: "int", 2: "int", 3: "int", 4: "money", 5: "pct"}, widths={0: 34})
    book.save(os.path.join(out, "conversion-audit.xlsx"))

    lines = ["# Conversion tracking audit", ""]
    lines += ["%s." % title for title in meta["title_rows"]] or [os.path.basename(args.summary)]
    lines += ["", "## What was read", "",
              "- %d conversion actions: %d Primary, %d Secondary%s. Not recording or needing attention: %d." % (
                  counts["actions"], counts["primary"], counts["secondary"],
                  ", %d with no Primary or Secondary shown" % counts["optimization_not_shown"] if counts["optimization_not_shown"] else "", counts["not_recording"])]
    if counts["removed"]:
        lines.append("- Removed actions, listed apart and not audited: %s." % ", ".join(a["name"] for a in info["removed"]))
    if info["headings"]:
        lines.append("- %d rows had a name and no settings, such as a goal heading, and were left out: %s." % (len(info["headings"]), ", ".join(info["headings"])))
    if volume_key:
        lines.append("- %s across the audited actions: %s." % (volume_label, t.two(total)))
        lines.append("- " + t.reconcile_line(check, volume_label))
    if doubtful:
        lines.append("- Rows that start with the word Total were read as total rows: %s. If one is a conversion action, rename it in the file." % ", ".join(doubtful))
    lines += ["", "## What the audit found", ""]
    if not findings:
        lines.append("- No finding. Every check that the file's columns allow passed.")
    for f in findings:
        lines.append("### %s. %s" % (f["id"], f["title"]))
        lines += ["", f["detail"], ""]
        if f["share"] is not None:
            lines += ["Share: %s." % share_text(f["share"], basis), ""]
        lines += ["- " + t.rule_text(rule) for rule in next(x[2] for x in TYPES if x[0] == f["type"])]
        lines += ["", "Checks outside Google Ads reports: in the list below, marked %s." % f["id"], ""]
    if findings:
        lines += ["## Checks outside Google Ads, by who usually does them", ""]
        lines += t.owner_lines([(c, f["id"]) for f in findings for c in f["checks"]], "finding")
    if volume_key and total:
        lines += ["## Where the conversions are", "",
                  "The fewest actions that carry most of the %s, meaning more than half: %s. A fault in one of these moves the numbers most." % (
                      volume_label, ", ".join(a["name"] for a in carriers)), "",
                  outputs.md_table(["Conversion action", "Optimization", "Source", volume_label, "Share", "Running share"],
                                   [[a["name"], a["optimization"], a["source"], t.two(a["volume"]), metrics.pct(a["share"]), metrics.pct(a["cumulative_share"])] for a in ranked]),
                  ""]
    if "category" in has:
        lines += ["## Categories", "", outputs.md_table(["Category", "Actions", "Primary", "Secondary", volume_label, "Share"],
                                                      [[c["category"], c["actions"], c["primary"], c["secondary"], t.two(c["volume"]),
                                                        metrics.pct(c["share"])] for c in categories]), ""]
    lines += ["## How the numbers were made", "",
              "- Every share is a share of %s across the audited actions. Removed actions and heading rows are not in the base." % basis,
              "- " + t.CATEGORY_RULE,
              "- Two Primary actions are flagged as possible double counting when they share a category and their Conversion source differs.",
              "- An action is not recording when its status reads Misconfigured, Awaiting conversions, No recent conversions, Unverified, Tag inactive or Inactive, "
              "and needs attention when it reads Needs attention.",
              "- \"Most of the conversions\" means more than half. That is a definition, not a benchmark.", "",
              "## What this did not cover", ""]
    lines += ["- " + item for item in not_checked]
    lines += ["- Which goals each campaign uses, and what a custom goal contains. A report does not show this, so an action may be used for bidding in some campaigns and not others.",
              "- The website, the tags, the consent banner and any upload. The checks above say what to look at there.",
              "- Changes over time. Run the breaks step on a report by conversion action and day for that."]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(out, "conversion-audit.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote conversion-audit.json, conversion-audit.xlsx and conversion-audit.md to %s" % out)


if __name__ == "__main__":
    main()
