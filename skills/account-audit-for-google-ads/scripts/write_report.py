#!/usr/bin/env python3
"""Step 2 of the account audit: write the deliverables.

Joins the audit's numbers with the judgments in notes.json (which failed
checks matter for this account, the fix for each, and why the others do not
apply) and writes audit.json, a workbook and a summary a client could read.
Every number comes from audit.json. Nothing here carries a vendor name.

    python3 scripts/write_report.py --work WORK --out OUTPUT
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics, outputs, xlsx  # noqa: E402

AREAS = ("Conversion tracking and goals", "Structure", "Keywords and match types", "Ads and assets", "Budgets and bidding",
         "Search terms and negatives", "Settings")
TITLES = {"audit": "Google Ads account audit", "readiness": "Google Ads acquisition readiness check", "qa": "Google Ads QA checklist"}
RESULT = {"pass": "Passed", "fail": "Failed", "not run": "Not run", "by hand": "Check by hand"}
KINDS = ("wasted", "exposed", "held back")
KIND_LABEL = {"wasted": "Wasted", "exposed": "Exposed", "held back": "Held back (estimate, upper bound)"}
KIND_INTRO = {
    "wasted": "Spend with no result.",
    "exposed": "Spend that depends on a problem. It was not lost, but it rests on something that needs fixing.",
    "held back": "An estimate of spend the budget kept out. It is an upper bound, because the searches the ads missed usually convert worse than "
                 "the ones they won, so it is not shown as a share of the account's cost.",
}
FULL = 5
YES, NO = ("yes", "y", "true"), ("no", "n", "false")


def m(value):
    return "" if value is None else metrics.money(value)


def money_cell(value):
    return None if value is None else round(value, 2)


def basis(check):
    if check["label"] == "Official" and check.get("page"):
        return "Official. Google Ads Help: %s." % check["page"]
    return "%s." % check["label"]


def where(found):
    parts = []
    for part in (found["campaign"], found["ad_group"], found["item"]):
        if part and part not in parts:
            parts.append(part)
    return " > ".join(parts)


def result_text(check):
    return RESULT[check["status"]] + (", does not apply here" if check["status"] == "fail" and not check.get("relevant") else "")


def money_text(check):
    if check.get("money") is None:
        return "not tied to a cost"
    return "%s %s" % (KIND_LABEL[check["kind"]].lower(), m(check["money"]))


def load(work):
    audit_path, notes_path = os.path.join(work, "audit.json"), os.path.join(work, "notes.json")
    if not os.path.isfile(audit_path):
        raise SystemExit("Run audit.py first. There is no audit.json in %s." % work)
    if not os.path.isfile(notes_path):
        raise SystemExit("Copy %s to %s and fill it in first." % (os.path.join(work, "notes.template.json"), notes_path))
    audit, notes = outputs.read_json(audit_path), outputs.read_json(notes_path)
    failed = {c["id"]: c for c in audit["checks"] if c["status"] == "fail"}
    problems, judged = [], {}
    for note in notes.get("findings", []):
        cid = str(note.get("id", "")).strip()
        if cid not in failed:
            problems.append("%s is not a failed check in this audit. Use the ids in notes.template.json." % (cid or "A finding with no id"))
            continue
        relevant = str(note.get("relevant", "")).strip().lower()
        fix, why = str(note.get("fix", "")).strip(), str(note.get("why", "")).strip()
        if relevant in YES and not fix:
            problems.append("%s is marked relevant but has no fix." % cid)
        elif relevant in NO and not why:
            problems.append("%s is marked not relevant but does not say why." % cid)
        elif relevant not in YES + NO:
            problems.append("%s: set relevant to yes or no." % cid)
        judged[cid] = {"relevant": relevant in YES, "fix": fix, "why": why}
    missing = [cid for cid in failed if cid not in judged]
    if missing:
        problems.append("These failed checks have no judgment yet: %s." % ", ".join(missing))
    if problems:
        raise SystemExit("notes.json is not complete:\n- " + "\n- ".join(problems))
    for cid, judgment in judged.items():
        failed[cid].update(judgment)
    extra = [str(a).strip() for a in notes.get("assumptions", []) if str(a).strip()]
    return audit, str(notes.get("summary", "")).strip(), extra


def workbook(audit, path):
    checks, job = audit["checks"], audit["job"]
    failed = [c for c in checks if c["status"] == "fail"]
    relevant = sorted([c for c in failed if c["relevant"]], key=lambda c: (c["stage"], c["id"]))
    dismissed = [c for c in failed if not c["relevant"]]
    passed = [c for c in checks if c["status"] == "pass"]
    book = xlsx.Workbook()
    flag = {"readiness": ("Readiness check", "gate"), "qa": ("Must pass", "must")}.get(job)
    header = ["Fix order", "Fix stage", "Id", "Area", "Check", "Result", "Money kind", "Rank in kind", "Money", "Share of account cost",
              "What the money is", "Evidence", "Recommendation", "Basis", "Source"]
    if flag:
        header.insert(6, flag[0])

    def row(c, order):
        cells = [order, c["stage_name"], c["id"], c["area"], c["name"], result_text(c), KIND_LABEL[c["kind"]] if c["status"] == "fail" else "",
                 c.get("rank") if c["status"] == "fail" else None, money_cell(c.get("money")), c.get("share_of_account_cost"),
                 c.get("money_basis", ""), " ".join(c.get("evidence", [])), c.get("fix") or c.get("why") or "", basis(c), c["source"]]
        if flag:
            cells.insert(6, "Yes" if c[flag[1]] else "No")
        return cells
    rows = [row(c, number) for number, c in enumerate(relevant, start=1)] + [row(c, None) for c in dismissed + passed]
    s = 1 if flag else 0
    book.add_sheet("Findings", header, rows, formats={0: "int", 7 + s: "int", 8 + s: "money", 9 + s: "pct", 10 + s: "wrap", 11 + s: "wrap", 12 + s: "wrap"},
                   widths={4: 44, 10 + s: 50, 11 + s: 70, 12 + s: 70, 14 + s: 50})
    area_header = ["Id", "Check", "Result", "Money kind", "Campaign", "Ad group", "Item", "Detail", "Cost", "Clicks", "Conversions", "Cost / conv.", "Money"]
    for area in AREAS:
        area_rows = []
        for c in [c for c in checks if c["area"] == area]:
            kind = KIND_LABEL[c["kind"]] if c["status"] == "fail" else ""
            if c["status"] == "fail" and c["items"]:
                for i in c["items"]:
                    area_rows.append([c["id"], c["name"], result_text(c), kind, i["campaign"], i["ad_group"], i["item"], i["detail"], money_cell(i["cost"]),
                                      i["clicks"], i["conversions"], money_cell(i["cpa"]), money_cell(i["stake"])])
            else:
                note = " ".join(c.get("evidence", [])) if c["status"] in ("pass", "fail") else c.get("unlock", "")
                area_rows.append([c["id"], c["name"], result_text(c), kind, "", "", "", note, None, None, None, None, None])
        book.add_sheet(area, area_header, area_rows, formats={7: "wrap", 8: "money", 9: "int", 10: "money", 11: "money", 12: "money"},
                       widths={1: 40, 6: 34, 7: 60})
    blocked = [c for c in checks if c["status"] in ("not run", "by hand")]
    book.add_sheet("Checks not run", ["Id", "Area", "Check", "Why it could not run", "What would unlock it"],
                   [[c["id"], c["area"], c["name"], c["why"], c["unlock"]] for c in blocked], formats={3: "wrap", 4: "wrap"}, widths={2: 44, 3: 60, 4: 70})
    book.add_sheet("Files read", ["Report", "File", "Date range", "Rows", "Cost", "File total used", "File total", "Difference"],
                   [[f["report"], f["file"], f["period"]["text"] if f["period"] else "", f["rows"], money_cell(f["cost"]),
                     f["reconcile"]["label"] if f["reconcile"] else "", money_cell(f["reconcile"]["file_total"]) if f["reconcile"] else None,
                     money_cell(f["reconcile"]["difference"]) if f["reconcile"] else None] for f in audit["files"]],
                   formats={3: "int", 4: "money", 6: "money", 7: "money"})
    book.save(path)


def summary_text(audit, summary, extra):
    checks, job, counts = audit["checks"], audit["job"], audit["counts"]
    failed = [c for c in checks if c["status"] == "fail"]
    relevant = [c for c in failed if c["relevant"]]
    dismissed = [c for c in failed if not c["relevant"]]
    passed = [c for c in checks if c["status"] == "pass"]
    blocked = [c for c in checks if c["status"] in ("not run", "by hand")]
    lines = ["# %s" % TITLES[job], ""]
    if summary:
        lines += ["## The answer", "", summary, ""]

    lines += ["## What I read", ""]
    periods = sorted({f["period"]["text"] for f in audit["files"] if f["period"]})
    lines.append("- Google Ads exports: %s%s." % (", ".join(f["report"] for f in audit["files"]), ", for %s" % "; ".join(periods) if periods else ""))
    if audit["currency"]:
        lines.append("- Amounts are in %s." % audit["currency"])
    lines += ["- " + a for a in audit["assumptions"] + extra]
    if audit["account"]:
        acc = audit["account"]
        lines.append("- The account spent %s across %d campaigns, %s of it in the %d enabled campaigns. Paused and removed campaigns, ad groups, "
                     "keywords and ads were not judged as if serving." % (m(acc["cost"]), acc["campaigns"], m(acc["enabled_cost"]), acc["enabled_campaigns"]))

    ran = counts["pass"] + counts["fail"]
    lines += ["", "## Result", "",
              "- %d checks ran: %d passed and %d failed. Of the failed checks, %d %s for this account and %d %s judged not to apply."
              % (ran, counts["pass"], counts["fail"], len(relevant), "matters" if len(relevant) == 1 else "matter", len(dismissed),
                 "was" if len(dismissed) == 1 else "were"),
              "- %d checks could not run with these files, and %d settings can only be checked in Google Ads. Both are listed below with what would unlock them."
              % (counts["not run"], counts["by hand"]),
              "- There is no single score. Money is of three kinds, wasted, exposed and held back, ranked within each kind and never added together."]

    waste = audit.get("clear_waste")
    if waste:
        lines += ["", "## Where money is wasted", "",
                  "**Clear waste, counted once: %s**%s." % (m(waste["total"]), ", %s of the account's cost" % metrics.pct(waste["share_of_account_cost"])
                                                            if waste["share_of_account_cost"] is not None else ""),
                  "", "- Includes: " + waste["includes"], "- Leaves out: " + waste["leaves_out"]]
        lines += ["- " + note for note in waste["notes"]]
        if len(waste["by_campaign"]) > 1:
            lines += ["", outputs.md_table(["Campaign", "Clear waste"], [[name, m(value)] for name, value in waste["by_campaign"]])]

    if job == "readiness":
        lines += ["", "## Readiness checks", "", "These are the checks that bear on whether the account can take more spend. A failed BB-03 is the exception: "
                  "it marks a campaign that converts well and is held back by its budget, which is where more spend would go first.", "",
                  outputs.md_table(["Check", "Result", "Money"], [["%s %s" % (c["id"], c["name"]), result_text(c), money_text(c) if c["status"] == "fail" else ""]
                                                                  for c in checks if c["gate"]])]
    if job == "qa":
        def qa_table(subset):
            return outputs.md_table(["Check", "Result"], [["%s %s" % (c["id"], c["name"]), result_text(c)] for c in subset])
        lines += ["", "## Must pass", "", qa_table([c for c in checks if c["must"] and c["status"] != "by hand"]),
                  "", "## Other checks", "", "These do not block the change, and are worth fixing.", "",
                  qa_table([c for c in checks if not c["must"] and c["status"] != "by hand"]), "", "## Confirm by hand", ""]
        lines += ["- **%s.** %s" % (c["name"], c["unlock"]) for c in checks if c["status"] == "by hand"]

    lines += ["", "## Findings by money", "", "Each table is ranked by money within its kind. The kinds are never added together, and money under one "
              "check can also sit under another."]
    for kind in KINDS:
        mine = sorted([c for c in relevant if c["kind"] == kind], key=lambda c: c["rank"])
        if not mine:
            continue
        header = ["Check", "Money"] + (["Share of account cost"] if kind != "held back" else []) + ["What the money is"]
        lines += ["", "### %s" % KIND_LABEL[kind], "", KIND_INTRO[kind], "",
                  outputs.md_table(header, [["%s %s" % (c["id"], c["name"]), m(c["money"]) if c["money"] is not None else "not tied to a cost"]
                                            + ([metrics.pct(c["share_of_account_cost"]) if c.get("share_of_account_cost") is not None else ""] if kind != "held back" else [])
                                            + [c["money_basis"]] for c in mine])]

    plan = sorted(relevant, key=lambda c: (c["stage"], c["id"]))
    lines += ["", "## Fix plan", "", "Fixes run in this order, whatever the money: measurement first, then what stops ads serving, then waste, then structure "
              "and ads, then bidding, then budget. Bidding learns from conversions, so it is changed once they are counted right, and more budget is added "
              "last so it does not scale a problem.", ""]
    if not plan:
        lines.append("No failed check needs action for this account.")
    for number, c in enumerate(plan[:FULL], start=1):
        lines.append("%d. **%s** (%s, %s). Money: %s, which is %s." % (number, c["name"], c["id"], c["stage_name"], money_text(c), c["money_basis"]))
        lines.append("   - Found: %s" % " ".join(c["evidence"]))
        if c["items"]:
            more = " and %d more in the workbook" % (len(c["items"]) - 3) if len(c["items"]) > 3 else ""
            lines.append("   - Where: %s%s." % ("; ".join(where(i) for i in c["items"][:3]), more))
        lines.append("   - Fix: %s" % c["fix"])
        lines.append("   - Basis: %s" % basis(c))
    if len(plan) > FULL:
        lines += ["", "Then, in order:", ""]
        lines += ["%d. **%s** (%s, %s; %s). %s" % (number, c["name"], c["id"], c["stage_name"], money_text(c), c["fix"])
                  for number, c in enumerate(plan[FULL:], start=FULL + 1)]

    design = next((c.get("by_design") for c in checks if c["id"] == "BB-03"), None)
    if design:
        lines += ["", "## Limited by budget by design", ""]
        lines += ["- %s uses %s, which Google builds to spend the full daily budget, so Search lost IS (budget) of %s does not mean it is starved, and it "
                  "was left out of the budget check. Judge its headroom with the budget simulator in Google Ads, and by whether its cost per conversion "
                  "holds as the budget rises." % (c["campaign"], c["bid_strategy"], "%.1f%%" % c["lost_is_budget"]) for c in design]
    if dismissed:
        lines += ["", "## Failed, but judged not to apply", "",
                  outputs.md_table(["Check", "Money", "Why it does not apply"], [["%s %s" % (c["id"], c["name"]), money_text(c), c["why"]] for c in dismissed])]
    if passed:
        lines += ["", "## What passed", "", outputs.md_table(["Check", "What was found"], [["%s %s" % (c["id"], c["name"]), " ".join(c["evidence"])] for c in passed])]
    if blocked:
        lines += ["", "## Checks not run", "", outputs.md_table(["Check", "Why", "What would unlock it"], [["%s %s" % (c["id"], c["name"]), c["why"], c["unlock"]] for c in blocked])]
    if audit.get("compare"):
        changes = audit["compare"]["changes"]
        lines += ["", "## Since the earlier run", ""]
        lines.append(outputs.md_table(["Check", "Before", "Now", "Money before", "Money now"],
                                      [["%s %s" % (c["id"], c["name"]), RESULT[c["before"]], RESULT[c["now"]], m(c["money_before"]), m(c["money_now"])] for c in changes])
                     if changes else "No check changed its result or its money.")

    lines += ["", "## How the numbers were made", ""]
    for f in audit["files"]:
        name, rec = f["report"][0].upper() + f["report"][1:], f["reconcile"]
        if rec:
            lines.append("- %s: %d rows. The rows add up to %s and the file's own total (%s) is %s%s." % (
                name, f["rows"], m(rec["rows"]), rec["label"], m(rec["file_total"]), "" if rec["matches"] else ", a difference of %s" % m(rec["difference"])))
        else:
            lines.append("- %s: %d rows%s." % (name, f["rows"], ", cost %s, no total row to check against" % m(f["cost"]) if f["cost"] is not None else ""))
    for key, line in audit["lines"].items():
        lines.append("- A %s with no conversions has spent enough to judge at %s. That is %s." % (
            {"campaigns": "campaign", "keywords": "keyword", "search_terms": "search term"}[key], m(line["value"]), line["source"]))
    lines += ["- Each check's threshold is in the workbook. Shares are of the cost of every campaign in the campaign report.",
              "- Quality Score is never averaged. Google says it is a diagnostic and should not be aggregated.",
              "- Each check is labeled Official, when a Google Ads Help page supports it, or Practitioner rule, when it is experience."]
    lines += ["- " + note for note in audit["notes"]]
    lines += ["", "## What this did not cover", "",
              "- Settings no export shows, and the checks listed as not run above.",
              "- The website, the tracking code and anything outside Google Ads.",
              "- Searches Google leaves out of the search terms report for low volume.",
              "- Performance Max asset groups, Shopping product groups, audiences, locations and ad schedules.",
              "- Results after the period of the files. Recent days can still gain conversions reported late."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    audit, summary, extra = load(args.work)
    audit["summary"], audit["your_assumptions"] = summary, extra
    out = outputs.ensure_dir(args.out)
    outputs.write_json(os.path.join(out, "audit.json"), audit)
    workbook(audit, os.path.join(out, "account-audit.xlsx"))
    text = summary_text(audit, summary, extra)
    with open(os.path.join(out, "account-audit.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote account-audit.md, account-audit.xlsx and audit.json to %s" % out)


if __name__ == "__main__":
    main()
