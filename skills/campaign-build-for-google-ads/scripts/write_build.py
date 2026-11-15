#!/usr/bin/env python3
"""Step 3 of the campaign build: write the files, with everything paused.

Reads WORKDIR/checked.json. Refuses unless the plan passed the check and
neither the plan nor the account files changed since. Writes a Google Ads
Editor import file, the negative keyword list, a build workbook, a launch
checklist and a summary. Every campaign, ad group, keyword and ad is written
paused. The file is read back to prove it before anything is reported.
No file carries a vendor name.

    python3 scripts/write_build.py --work WORKDIR --out OUTPUTDIR [--today YYYY-MM-DD]
"""
import re
import argparse
import csv
import datetime as dt
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_rules as rules  # noqa: E402
from gads import outputs, xlsx  # noqa: E402

EDITOR_FILE = "build-for-google-ads-editor.csv"
LIST_FILE = "negative-keyword-list.txt"
HEADLINES = ["Headline %d" % i for i in range(1, rules.HEADLINES_MAX + 1)]
DESCRIPTIONS = ["Description %d" % i for i in range(1, rules.DESCRIPTIONS_MAX + 1)]
EDITOR_HEADER = (["Campaign", "Campaign Type", "Networks", "Campaign Daily Budget", "Bid Strategy Type", "Target CPA", "Target ROAS",
                  "Start Date", "End Date", "Campaign Status", "EU political ads", "AI Max", "Location", "Ad Group", "Max CPC", "Ad Group Status",
                  "Keyword", "Criterion Type", "Final URL"] + HEADLINES + DESCRIPTIONS + ["Path 1", "Path 2", "Status"])
STATUS_COLUMNS = ("Campaign Status", "Ad Group Status", "Status")
# Google Ads Editor will not post a campaign until it declares whether it contains EU political
# ads. This is the value Editor itself writes for "no" (Editor 2.14.2, 2026-11-14). The launch
# checklist asks the person to confirm it.
NO_EU_POLITICAL_ADS = "Doesn't have EU political ads"
OFFICIAL, PRACTICE = "Official", "Practitioner rule"


def sha(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def percent_text(value):
    return ("%f" % value).rstrip("0").rstrip(".") + "%"


def editor_rows(checked):
    """Every row of the import file, parents first, each tagged with its kind."""
    rows = []

    def add(kind, **cells):
        rows.append((kind, [cells.get(column, "") for column in EDITOR_HEADER]))

    for c in checked["campaigns"]:
        add("Campaign", **{"Campaign": c["name"], "Campaign Type": "Search", "Networks": ";".join(c["networks"]),
                           "Campaign Daily Budget": rules.money(c["daily_budget"]), "Bid Strategy Type": c["bid_strategy"],
                           "Target CPA": rules.money(c["target_cpa"]) if c["target_cpa"] else "",
                           "Target ROAS": percent_text(c["target_roas_percent"]) if c["target_roas_percent"] else "",
                           "Start Date": c["start_date"], "End Date": c["end_date"], "Campaign Status": rules.PAUSED,
                           "EU political ads": NO_EU_POLITICAL_ADS, "AI Max": "Enabled" if c["ai_max"] else "Disabled"})
        for place in c["locations"]:
            add("Location", **{"Campaign": c["name"], "Location": place})
    for g in checked["ad_groups"]:
        add("Ad group", **{"Campaign": g["campaign"], "Ad Group": g["name"], "Max CPC": rules.money(g["max_cpc"]),
                           "Ad Group Status": rules.PAUSED})
    for k in checked["keywords"]:
        add("Keyword", **{"Campaign": k["campaign"], "Ad Group": k["ad_group"], "Keyword": k["text"],
                          "Criterion Type": rules.MATCH_TYPES[k["match"]], "Final URL": k["final_url"], "Status": rules.PAUSED})
    for n in checked["negatives"]:
        if n["level"] == "account":
            continue
        add("Negative keyword", **{"Campaign": n["campaign"], "Ad Group": n["ad_group"] if n["level"] == "ad_group" else "",
                                   "Keyword": n["text"], "Criterion Type": outputs.editor_criterion_type(n["match"], n["level"])})
    for a in checked["ads"]:
        cells = {"Campaign": a["campaign"], "Ad Group": a["ad_group"], "Final URL": a["final_url"], "Path 1": a["path_1"],
                 "Path 2": a["path_2"], "Status": rules.PAUSED}
        cells.update({HEADLINES[i]: h["text"] for i, h in enumerate(a["headlines"])})
        cells.update({DESCRIPTIONS[i]: d["text"] for i, d in enumerate(a["descriptions"])})
        add("Responsive search ad", **cells)
    return rows


def kind_of(row):
    """Read a written row back the way Editor tells items apart: by the columns filled in."""
    if row["Headline 1"]:
        return "Responsive search ad"
    if row["Keyword"]:
        return "Negative keyword" if "negative" in row["Criterion Type"].lower() else "Keyword"
    if row["Ad Group"]:
        return "Ad group"
    if row["Location"]:
        return "Location"
    return "Campaign"


def prove_file(path, expected, totals):
    """Read the import file back. Every status is Paused, the counts match the plan, and the text fits."""
    with open(path, encoding="utf-8", newline="") as handle:
        read = list(csv.DictReader(handle))
    found = {}
    for row in read:
        kind = kind_of(row)
        found[kind] = found.get(kind, 0) + 1
        for column in STATUS_COLUMNS:
            if row[column] and row[column] != rules.PAUSED:
                raise SystemExit("Stopped: a %s row in %s has %s set to %s. Nothing was reported. Everything must be paused." % (kind, path, column, row[column]))
        if kind in ("Campaign", "Ad group", "Keyword", "Responsive search ad"):
            column = {"Campaign": "Campaign Status", "Ad group": "Ad Group Status"}.get(kind, "Status")
            if row[column] != rules.PAUSED:
                raise SystemExit("Stopped: a %s row in %s has no paused status. Nothing was reported." % (kind, path))
        for column, limit in [(h, rules.HEADLINE_CHARS) for h in HEADLINES] + [(d, rules.DESCRIPTION_CHARS) for d in DESCRIPTIONS] + [("Path 1", rules.PATH_CHARS), ("Path 2", rules.PATH_CHARS)]:
            if rules.text_len(row[column]) > limit:
                raise SystemExit("Stopped: %s in %s is over %d characters. Nothing was reported." % (column, path, limit))
    if found != expected or len(read) != totals["import_rows"]:
        raise SystemExit("Stopped: the import file holds %s, and the plan has %s. Nothing was reported." % (found, expected))
    return {"rows": len(read), "by_kind": found}


def checklist(checked):
    """Every launch item, in the order a launch runs, with its owner, how to verify it, and its source."""
    owners = checked["brief"]["owners"]
    totals = checked["totals"]
    campaigns = checked["campaigns"]
    items = []

    def add(stage, item, role, verify, label, source, status="To do"):
        items.append({"stage": stage, "item": item, "role": role, "owner": owners.get(role, "") or "Not assigned",
                      "verify": verify, "label": label, "source": source, "status": status})

    stop = "Stop launch"
    for b in checked["blockers"]:
        status = "Said yes" if b["answer"] == "yes" else ("Open: answered no" if b["answer"] == "no" else "Open: not answered")
        add(stop, (b["check"] + ". " + b["detail"]).strip(), b["owner_role"], b["verify"], PRACTICE, rules.LAUNCH, status)
    if checked["warnings"]:
        add(stop, "Every warning from the plan check is decided with the person (%s)" % rules.plural(len(checked["warnings"]), "warning"),
            "build", "Read the Warnings sheet of the workbook. Write the decision beside each one.", PRACTICE, rules.LAUNCH)

    imp = "Import and review in Google Ads Editor"
    add(imp, "Import %s" % EDITOR_FILE, "build",
        "In Google Ads Editor: Account, Import, From file. Check the column headers Editor shows, then import.", OFFICIAL, rules.HAND)
    add(imp, "Read every error and warning Editor lists", "build",
        "Fix a problem in plan.json, run the check and the write step again, and import the new file. The workbook then still matches what is posted.",
        OFFICIAL, rules.HAND)
    add(imp, "Count the proposed changes: %s, %s, %s, %s, %s and %s"
        % (rules.plural(totals["campaigns"], "campaign"), rules.plural(totals["locations"], "location"), rules.plural(totals["ad_groups"], "ad group"),
           rules.plural(totals["keywords"], "keyword"), rules.plural(totals["campaign_negatives"] + totals["ad_group_negatives"], "negative keyword"),
           rules.plural(totals["ads"], "responsive search ad")),
        "build", "Review imported changes. Imported rows arrive as proposed changes and nothing reaches the account until it is posted.", OFFICIAL, rules.HAND)
    add(imp, "Every campaign, ad group, keyword and ad shows Paused", "build",
        "Sort each view in Editor by status. Nothing in the file is set to serve.", PRACTICE, rules.HAND)
    add(imp, "Every location is resolved", "build",
        "A location typed by name must be resolved before posting. An unresolved location shows a yellow warning.", OFFICIAL, rules.HAND)
    for c in campaigns:
        if c["ai_max"]:
            add(imp, "AI Max is on for %s, as the plan chose" % c["name"], "build",
                "Google says to wait at least 2 weeks after turning AI Max on before changes such as adding negatives, and that it won't be effective "
                "while the campaign is limited by budget. It also turns on text customization and Final URL expansion; turn either off in Editor if the "
                "ads must stay word for word or every click must land on the page in the file.", OFFICIAL, rules.SETUP)
        else:
            add(imp, "AI Max is off for %s, as the plan chose" % c["name"], "build",
                "Google turns AI Max on for every new Search campaign unless the file says off. This file says off. Check it reads Disabled in Editor.",
                OFFICIAL, rules.HAND)
    add(imp, "The EU political ads declaration is right", "build",
        "The file declares that each campaign doesn't have EU political ads, because Google Ads will not post a campaign without the declaration. "
        "If a campaign carries political content as Google defines it for the EU, change the declaration in Editor before posting.", OFFICIAL, rules.HAND)
    for c in campaigns:
        add(imp, 'Campaign "%s": networks read %s, bid strategy reads %s%s' % (
            c["name"], " and ".join(c["networks"]), c["bid_strategy"],
            ", target CPA %s" % rules.shown(c["target_cpa"]) if c["target_cpa"] else
            (", target ROAS %s" % percent_text(c["target_roas_percent"]) if c["target_roas_percent"] else "")),
            "build", "Open the campaign settings in Editor and compare them with the Campaigns sheet.", PRACTICE, rules.HAND)
    if checked["negative_list_name"] or totals["list_negatives"]:
        add(imp, 'Add the negative keyword list "%s" (%s) and apply it to every new campaign'
            % (checked["negative_list_name"] or "no name given", rules.plural(totals["list_negatives"], "keyword")),
            "build", "Paste %s into a negative keyword list in Google Ads, then apply the list to each campaign of this build. Quotation marks mean phrase match and square brackets mean exact match." % LIST_FILE,
            PRACTICE, rules.HAND)
    add(imp, "Keep the proposed changes and post", "build",
        "Keep proposed changes, then post. Afterwards check in Google Ads that every campaign of this build still reads Paused.", OFFICIAL, rules.HAND)

    day = "Launch day"
    add(day, "Every Stop launch item reads Said yes", "launch", "Read the first section of this checklist. One open item means no launch.", PRACTICE, rules.LAUNCH)
    add(day, "Open every final URL on a phone and on a computer", "landing_pages",
        "Use the Ads sheet. Each page must load and offer what its ad offers.", PRACTICE, rules.LAUNCH)
    add(day, "No ad or keyword is disapproved in Google's policy review", "launch",
        "In Google Ads, read the status of each ad and keyword after posting.", PRACTICE, rules.LAUNCH)
    add(day, "Enable ads, keywords and ad groups, then enable the campaign last", "launch",
        "Enable in that order, so nothing serves half built.", PRACTICE, rules.HAND)
    add(day, "Write down the hypothesis, the success metric and the early warning sign", "launch",
        "Hypothesis: %s Success metric: %s Early warning: %s" % tuple(
            (checked["brief"][k] or "not recorded").rstrip(".") + "." for k in ("hypothesis", "success_metric", "early_warning")),
        PRACTICE, rules.LAUNCH)

    first = "First 14 days"
    add(first, "Serving: every campaign is eligible to serve", "launch", "Check campaign status in Google Ads on day 1 and day 2.", PRACTICE, rules.LAUNCH)
    add(first, "Pacing: one day can spend up to %s and one month is charged at most %s for this build"
        % (rules.shown(totals["day_limit"]), rules.shown(totals["month_limit"])), "launch",
        "That is the total daily budget of %s times %d and times %s. Compare cost each day with these limits." % (
            rules.shown(totals["daily_budget"]), rules.DAY_LIMIT_TIMES, rules.MONTH_LIMIT_TIMES), OFFICIAL, rules.HAND)
    said = checked["brief"]["primary_conversion"]
    add(first, "Tracking: the conversions this build is judged on are recorded", "tracking",
        ("The brief says: %s. " % said.rstrip(".") if said else "") +
        "In Google Ads: Goals, Conversions, All conversions. Then check the campaign's Conversions column.", PRACTICE, rules.LAUNCH)
    add(first, "Search terms: read the search terms report and exclude what is plainly wrong", "launch",
        "If AI Max is on, Google says to wait at least 2 weeks after enabling before changes such as adding negatives.", PRACTICE, rules.LAUNCH)
    add(first, "Make one strategic change at a time", "launch",
        "Do not stack changes while the first signals form. Check conversion delay and low volume before calling a failure.", PRACTICE, rules.LAUNCH)
    return items


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True, help="the folder that holds plan.json and checked.json")
    parser.add_argument("--out", required=True, help="the folder to write the files to")
    parser.add_argument("--today", help="the date to treat as today, YYYY-MM-DD. Left out, it is this computer's date")
    args = parser.parse_args()

    checked_path = os.path.join(args.work, "checked.json")
    if not os.path.exists(checked_path):
        raise SystemExit("Run scripts/check_plan.py --work %s first. No file is written from a plan that has not been checked." % args.work)
    checked = outputs.read_json(checked_path)
    if not checked.get("passed"):
        raise SystemExit("The last check refused the plan. Fix plan.json and run scripts/check_plan.py --work %s until it passes." % args.work)
    plan_path, account_path = os.path.join(args.work, "plan.json"), os.path.join(args.work, "account.json")
    if not os.path.exists(plan_path) or sha(plan_path) != checked["plan_hash"]:
        raise SystemExit("plan.json changed after the last check. Run scripts/check_plan.py --work %s again." % args.work)
    if (sha(account_path) if os.path.exists(account_path) else None) != checked.get("account_hash"):
        raise SystemExit("The account files changed after the last check. Run scripts/check_plan.py --work %s again." % args.work)
    try:
        today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    except ValueError:
        raise SystemExit('--today must be a date written YYYY-MM-DD. "%s" is not.' % args.today)
    late = [c["name"] for c in checked["campaigns"] if c["start_date"] and c["start_date"] < str(today)]
    if late:
        raise SystemExit("The start date of %s is now in the past, and Google Ads Editor does not take a past start date. Change it in plan.json and run the check again."
                         % ", ".join('"%s"' % name for name in late))

    totals, out = checked["totals"], outputs.ensure_dir(args.out)
    rows = editor_rows(checked)
    editor_path = os.path.join(out, EDITOR_FILE)
    outputs.write_csv(editor_path, EDITOR_HEADER, [cells for _, cells in rows])
    expected = {}
    for kind, _ in rows:
        expected[kind] = expected.get(kind, 0) + 1
    proof = prove_file(editor_path, expected, totals)
    list_path, list_count = outputs.write_account_list(os.path.join(out, LIST_FILE), checked["negatives"])
    if not list_count:
        os.remove(list_path)

    items = checklist(checked)
    open_items = [i for i in items if i["status"].startswith("Open")]
    history = outputs.read_json(os.path.join(args.work, "check-history.json")) if os.path.exists(os.path.join(args.work, "check-history.json")) else []
    refused_runs = [h for h in history if not h["passed"]]
    caught = []
    for run in refused_runs:
        for problem in run["problems"]:
            line = "%s: %s" % (problem["where"], problem["text"])
            if line not in caught:
                caught.append(line)
    brief = checked["brief"]
    # The business line is the person's own words; the title keeps only its name, before any
    # ":", ",", "(" or " - ", so a sentence is never cut off mid way.
    name = re.split(r":|,|\(| - ", brief["business"])[0].strip() if brief["business"] else ""
    title = "Campaign build" + (": " + name if name else "")

    # Workbook.
    book = xlsx.Workbook()
    summary_rows = [
        ["Everything in the import file", "Paused. Nothing can serve until a person enables it."],
        ["Plan checked on", checked["checked_on"]],
        ["Checks run on the final plan", "%d, every one passed or warned" % len(checked["checks"])],
        ["Earlier versions the check refused", len(refused_runs)],
        ["Problems the check caught on the way", len(caught)],
        ["Warnings to decide", len(checked["warnings"])],
        ["Stop launch items still open", len(open_items)],
        ["Campaigns", totals["campaigns"]], ["Ad groups", totals["ad_groups"]], ["Keywords", totals["keywords"]],
        ["Exact match keywords", totals["exact"]], ["Phrase match keywords", totals["phrase"]], ["Broad match keywords", totals["broad"]],
        ["Responsive search ads", totals["ads"]], ["Headlines", totals["headlines"]], ["Descriptions", totals["descriptions"]],
        ["Negative keywords in the list", totals["list_negatives"]], ["Campaign negative keywords", totals["campaign_negatives"]],
        ["Ad group negative keywords", totals["ad_group_negatives"]], ["Locations", totals["locations"]],
        # This sheet mixes counts and money in one column, so money is written as text with two decimals.
        ["Daily budget, all campaigns", rules.money(totals["daily_budget"])],
        ["Most Google can spend in one day (daily budget x %d)" % rules.DAY_LIMIT_TIMES, rules.money(totals["day_limit"])],
        ["Most Google can charge in one month (daily budget x %s)" % rules.MONTH_LIMIT_TIMES, rules.money(totals["month_limit"])],
        ["Rows in the import file", proof["rows"]],
    ]
    book.add_sheet("Summary", ["Measure", "Value"], summary_rows, formats={1: "int"}, widths={0: 58, 1: 60})
    book.add_sheet("Campaigns", ["Campaign", "Status", "Daily budget", "Most in one day", "Most in one month", "Bid strategy", "Target CPA",
                                 "Target ROAS", "Networks", "Locations", "Start date", "End date", "Ad groups", "Keywords", "Ads", "Campaign negatives"],
                   [[c["name"], rules.PAUSED, c["daily_budget"], c["day_limit"], c["month_limit"], c["bid_strategy"], c["target_cpa"],
                     percent_text(c["target_roas_percent"]) if c["target_roas_percent"] else "", "; ".join(c["networks"]), "; ".join(c["locations"]),
                     c["start_date"] or "When enabled", c["end_date"] or "None", c["ad_groups"], c["keywords"], c["ads"], c["campaign_negatives"]]
                    for c in checked["campaigns"]],
                   formats={2: "money", 3: "money", 4: "money", 6: "money", 12: "int", 13: "int", 14: "int", 15: "int"}, widths={9: 50})
    book.add_sheet("Ad groups", ["Campaign", "Ad group", "Status", "Max CPC", "Keywords", "Exact", "Phrase", "Broad", "Ads", "Ad group negatives"],
                   [[g["campaign"], g["name"], rules.PAUSED, g["max_cpc"], g["keywords"], g["exact"], g["phrase"], g["broad"], g["ads"], g["negatives"]]
                    for g in checked["ad_groups"]], formats={3: "money", 4: "int", 5: "int", 6: "int", 7: "int", 8: "int", 9: "int"})
    book.add_sheet("Keywords", ["Campaign", "Ad group", "Keyword", "Match type", "Final URL", "Status", "Already in the account"],
                   [[k["campaign"], k["ad_group"], k["text"], rules.MATCH_TYPES[k["match"]], k["final_url"] or "The ad's final URL", rules.PAUSED,
                     "; ".join("%s > %s" % (h["campaign"], h["ad_group"]) for h in k["in_account"])] for k in checked["keywords"]], widths={6: 50})
    book.add_sheet("Ads", ["Campaign", "Ad group", "Ad", "Status", "Final URL", "Path 1", "Path 2", "Headlines", "Descriptions", "Headlines with a keyword"],
                   [[a["campaign"], a["ad_group"], a["number"], rules.PAUSED, a["final_url"], a["path_1"], a["path_2"], len(a["headlines"]),
                     len(a["descriptions"]), a["headlines_with_keyword"]] for a in checked["ads"]],
                   formats={2: "int", 7: "int", 8: "int", 9: "int"}, widths={4: 50})
    text_rows = []
    for a in checked["ads"]:
        for kind, items_, limit in (("Headline", a["headlines"], rules.HEADLINE_CHARS), ("Description", a["descriptions"], rules.DESCRIPTION_CHARS)):
            for i, part in enumerate(items_, start=1):
                text_rows.append([a["campaign"], a["ad_group"], a["number"], "%s %d" % (kind, i), part["text"], part["characters"], limit, limit - part["characters"]])
    book.add_sheet("Ad text", ["Campaign", "Ad group", "Ad", "Part", "Text", "Characters", "Limit", "Room left"], text_rows,
                   formats={2: "int", 5: "int", 6: "int", 7: "int"}, widths={4: 70})
    book.add_sheet("Negative keywords", ["Level", "Campaign", "Ad group", "Negative keyword", "Match type", "Own keywords tested", "Why"],
                   [[{"account": "List", "campaign": "Campaign", "ad_group": "Ad group"}[n["level"]], n["campaign"] or "Every campaign in the build",
                     n["ad_group"], n["text"], n["match"].capitalize(), n["tested_against"], n["why"]] for n in checked["negatives"]],
                   formats={5: "int"}, widths={6: 60})
    book.add_sheet("Launch checklist", ["Stage", "Item", "Owner", "How to verify", "Status", "Source"],
                   [[i["stage"], i["item"], i["owner"], i["verify"], i["status"], "%s: %s" % (i["label"], i["source"])] for i in items],
                   formats={1: "wrap", 3: "wrap"}, widths={0: 22, 1: 60, 3: 70, 5: 44})
    book.add_sheet("Warnings", ["Where", "Warning", "Source", "Decision"],
                   [[w["where"], w["text"], "%s: %s" % (w["label"], w["source"]), ""] for w in checked["warnings"]],
                   formats={1: "wrap"}, widths={0: 50, 1: 90, 2: 44, 3: 40})
    book.add_sheet("Checks", ["Check", "Result", "Items tested", "Source"],
                   [[c["check"], c["result"], c["tested"] if not c["not_run"] else c["not_run"], "%s: %s" % (c["label"], c["source"])] for c in checked["checks"]],
                   widths={0: 70, 2: 40, 3: 50})
    book.add_sheet("What the check caught", ["Problem in an earlier version of the plan"], [[line] for line in caught], formats={0: "wrap"}, widths={0: 140})
    book.save(os.path.join(out, "campaign-build.xlsx"))

    # Launch checklist.
    lines = ["# Launch checklist", "", "%s. Built from the plan checked on %s." % (title, checked["checked_on"]), "",
             "Everything in the import file is paused. Nothing serves until a person enables it, on launch day, after every Stop launch item reads Said yes.", ""]
    for stage in ("Stop launch", "Import and review in Google Ads Editor", "Launch day", "First 14 days"):
        lines += ["## " + stage, ""]
        if stage == "Stop launch":
            lines += ["Each of these blocks the launch until it reads Said yes. Only the person can answer yes.", ""]
        for i in [i for i in items if i["stage"] == stage]:
            box = "x" if i["status"] == "Said yes" else " "
            lines.append("- [%s] **%s.** Owner: %s. %s%s (%s: %s)" % (box, i["item"].rstrip("."), i["owner"], i["verify"],
                                                                    "" if i["status"] == "To do" else " Status: %s." % i["status"], i["label"], i["source"]))
        lines.append("")
    if checked["warnings"]:
        lines += ["## Warnings from the plan check", "", "Decide each one with the person before launch.", ""]
        lines += ["- %s: %s" % (w["where"], w["text"]) for w in checked["warnings"]] + [""]
    with open(os.path.join(out, "launch-checklist.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))

    # Summary.
    s = ["# " + title, "",
         "**Everything is built paused.** Every campaign, ad group, keyword and ad in the import file is set to Paused. Nothing serves until a person enables it.",
         "", "**Review every row in Google Ads Editor before you post.** Files in this layout were test imported into Google Ads Editor 2.14.2 with no errors.", "",
         "## What the plan builds", "",
         "- %s, %s, %s (%d exact, %d phrase, %d broad), %s with %s and %s." % (
             rules.plural(totals["campaigns"], "campaign"), rules.plural(totals["ad_groups"], "ad group"), rules.plural(totals["keywords"], "keyword"),
             totals["exact"], totals["phrase"], totals["broad"], rules.plural(totals["ads"], "responsive search ad"),
             rules.plural(totals["headlines"], "headline"), rules.plural(totals["descriptions"], "description")),
         "- %s: %d in the list, %d at campaign level, %d at ad group level. Each was tested against every keyword of the build it can reach, and none blocks one." % (
             rules.plural(totals["negatives"], "negative keyword"), totals["list_negatives"], totals["campaign_negatives"], totals["ad_group_negatives"]),
         "- Daily budget, all campaigns: %s. The most Google can spend in one day is %s, and the most it can charge in one month is %s. (Official: %s)" % (
             rules.shown(totals["daily_budget"]), rules.shown(totals["day_limit"]), rules.shown(totals["month_limit"]), rules.HAND), "",
         outputs.md_table(["Campaign", "Daily budget", "Most in a month", "Bid strategy", "Networks", "Locations", "Ad groups", "Keywords", "Ads"],
                          [[c["name"], rules.shown(c["daily_budget"]), rules.shown(c["month_limit"]), c["bid_strategy"], ", ".join(c["networks"]),
                            "; ".join(c["locations"]), c["ad_groups"], c["keywords"], c["ads"]] for c in checked["campaigns"]]), "",
         outputs.md_table(["Campaign", "Ad group", "Keywords", "Exact", "Phrase", "Broad", "Ads", "Ad group negatives"],
                          [[g["campaign"], g["name"], g["keywords"], g["exact"], g["phrase"], g["broad"], g["ads"], g["negatives"]] for g in checked["ad_groups"]]),
         "", "## What the check caught", ""]
    if caught:
        s.append("The check refused %s of the plan and caught %s before any file was written:" % (rules.plural(len(refused_runs), "earlier version"), rules.plural(len(caught), "problem")))
        s += [""] + ["- " + line for line in caught[:20]]
        if len(caught) > 20:
            s.append("- And %d more, on the What the check caught sheet." % (len(caught) - 20))
    else:
        s.append("The plan passed the check the first time.")
    s += ["", "The final plan passed %d checks. Each names its source on the Checks sheet." % len(checked["checks"])]
    if checked["warnings"]:
        s += ["", "## Warnings to decide", "", "A warning does not stop the files. Decide each one with the person.", ""]
        s += ["%d. %s: %s" % (i, w["where"], w["text"]) for i, w in enumerate(checked["warnings"], start=1)]
    s += ["", "## Before launch", ""]
    if open_items:
        s.append("%s still open. Nothing may be enabled until each reads yes:" % rules.plural(len(open_items), "Stop launch item"))
        s += [""] + ["- %s Owner: %s. %s." % (i["item"].rstrip(".") + ".", i["owner"], i["status"]) for i in open_items]
    else:
        s.append("Every Stop launch item reads yes in the plan. The launch day steps are in launch-checklist.md.")
    if brief["assumptions"]:
        s += ["", "## Assumptions in the plan", ""] + ["- " + a for a in brief["assumptions"]]
    s += ["", "## Files", "",
          "- `%s`: %d rows for Google Ads Editor, all paused: %s." % (EDITOR_FILE, proof["rows"], ", ".join(
              "%d %s" % (count, kind.lower() + ("" if count == 1 else "s")) for kind, count in sorted(proof["by_kind"].items(), key=lambda kv: ["Campaign", "Location", "Ad group", "Keyword", "Negative keyword", "Responsive search ad"].index(kv[0])))),
          ]
    if list_count:
        s.append("- `%s`: %s for the negative keyword list%s. Paste it into a negative keyword list in Google Ads and apply the list to every campaign of this build. Quotation marks mean phrase match and square brackets mean exact match." % (
            LIST_FILE, rules.plural(list_count, "keyword"), ' "%s"' % checked["negative_list_name"] if checked["negative_list_name"] else ""))
    s += ["- `campaign-build.xlsx`: summary, campaigns, ad groups, keywords, ads, every line of ad text with its character count, negative keywords, the launch checklist, warnings, checks and what the check caught.",
          "- `launch-checklist.md`: what must be true before launch, the import and review in Editor, launch day and the first 14 days, each with an owner.",
          "- `campaign-build.json`: every number in this summary.",
          "", "## How to import", "",
          "1. In Google Ads Editor: Account, Import, From file. Choose `%s`. Check the column headers Editor shows. (Official: %s)" % (EDITOR_FILE, rules.HAND),
          "2. Read the list of errors and warnings. Fix a problem in the plan and write the files again, so the workbook keeps matching.",
          "3. Review imported changes. They arrive as proposed changes, and nothing reaches the account until it is posted. Keep them, resolve every location, then post. (Official: %s)" % rules.HAND,
          "4. Enable on launch day only, after the launch checklist's Stop launch items all read yes. Enable the campaign last.",
          "", "## How the numbers were made", "",
          "- Every count and sum comes from the checked plan. The import file was read back after writing. It holds %d rows, one for each of the plan's %s, %s, %s, %s, %s and %s, and every status in it is Paused." % (
              proof["rows"], rules.plural(totals["campaigns"], "campaign"), rules.plural(totals["locations"], "location"),
              rules.plural(totals["ad_groups"], "ad group"), rules.plural(totals["keywords"], "keyword"),
              rules.plural(totals["campaign_negatives"] + totals["ad_group_negatives"], "campaign or ad group negative keyword"),
              rules.plural(totals["ads"], "ad")),
          "- Characters are counted the way Google counts them: a double width character, as in Chinese, Japanese or Korean, counts as 2. A code in braces is counted with its default text in its place, and a countdown as %d characters. Every limit comes from %s or %s and names its page there. (Official)" % (rules.COUNTDOWN_CHARS, rules.HAND, rules.CUSTOMIZERS),
          "- The most in one day is the daily budget times %d. The most in one month is the daily budget times %s. (Official: %s)" % (rules.DAY_LIMIT_TIMES, rules.MONTH_LIMIT_TIMES, rules.HAND),
          "- Negative keywords were tested with Google's matching rules: exact, phrase and broad, with no close variants. (Official: %s)" % rules.KEYWORDS,
          "- Compared with the account: %s; %s." % (
              "%s from %s" % (rules.plural(checked["account"]["campaigns"], "campaign"), checked["account"]["campaigns_report"]) if checked["account"]["campaigns_report"] else "no campaigns report was given, so names were not compared",
              "%s from %s" % (rules.plural(checked["account"]["keywords"], "keyword"), checked["account"]["keywords_report"]) if checked["account"]["keywords_report"] else "no keywords report was given, so keywords were not compared"),
          "", "## What this did not cover", "",
          "- Search volume, cost per click and forecasts. Nothing here estimates traffic or results.",
          "- Assets such as sitelinks, callouts and call assets, audiences, ad schedules, devices and location options. Set them in Editor.",
          "- Pins. None are written. Pin in Editor after import if wanted.",
          "- Customizer attributes and their values. Codes in the ad text are written as planned, but an attribute used by {CUSTOMIZER.Name:default text} must be created in Google Ads, with a value, before posting. Google Ads Editor 2.14.2 imported every code unchanged in a test on 2026-11-14, but did not flag an attribute missing from the account.",
          "- Searches that have not happened. The negative test knows only this build's keywords. Negatives do not match close variants, so plural and singular forms each need their own.",
          "- Location names were compared as text only. Overlapping places with different names were not found.",
          "- Tested in Google Ads Editor 2.14.2 on 2026-11-14: this layout imports with no errors, and Editor reads each row as written. Review every row in Editor before you post.",
          ]
    text = "\n".join(s) + "\n"
    with open(os.path.join(out, "campaign-build.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    outputs.write_json(os.path.join(out, "campaign-build.json"), {
        "title": title, "checked_on": checked["checked_on"], "all_paused": True, "import_file": proof,
        "negative_list_keywords": list_count, "totals": totals, "refused_versions": len(refused_runs), "caught": caught,
        "warnings": checked["warnings"], "open_launch_items": open_items, "checklist": items, "checks": checked["checks"],
        "campaigns": checked["campaigns"], "ad_groups": checked["ad_groups"]})
    print(text)
    print("Wrote the files to %s" % out)


if __name__ == "__main__":
    main()
