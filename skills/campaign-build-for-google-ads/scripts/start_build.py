#!/usr/bin/env python3
"""Step 1 of the campaign build: read what the account already has and write the empty plan.

Reads a campaigns report and a keywords report when they are given, so the
new build can stay clear of names and keywords the account already uses.
Writes the plan template and prints the limits the check will enforce.

    python3 scripts/start_build.py --work WORKDIR [--campaigns CAMPAIGNS_REPORT] [--keywords KEYWORDS_REPORT]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_rules as rules  # noqa: E402
from gads import io, metrics, outputs  # noqa: E402

# A real keyword report can show Interactions in place of Clicks. Keyword status comes before Status, and the first wins.
KEYWORD_ALIASES = {"keyword status": "keyword_status", "status": "keyword_status", "search keyword status": "keyword_status",
                   "search keyword match type": "match_type", "interactions": "clicks"}
MAX_KEYWORDS_SHOWN = 40


def read(path, name, **extra):
    if not os.path.exists(path):
        raise SystemExit("I can't find the %s at %s. Check the path." % (name, path))
    try:
        return io.read_report(path, **extra)
    except ValueError as error:
        raise SystemExit("%s That was the %s, %s." % (error, name, path))


def account_campaigns(path):
    meta, rows = read(path, "campaigns report")
    io.require(meta, ["campaign"], "campaigns report")
    found = {}
    for row in rows:
        name = (row.get("campaign") or "").strip()
        if not name:
            continue
        item = found.setdefault(name.lower(), {"name": name, "status": "", "type": "", "bid_strategy": "", "budget": None})
        # A report segmented by day repeats each campaign. The last row read wins.
        item["status"] = (row.get("campaign_status") or item["status"]).strip()
        item["type"] = (row.get("campaign_type") or item["type"]).strip()
        item["bid_strategy"] = (row.get("bid_strategy") or item["bid_strategy"]).strip()
        if row.get("budget") is not None:
            item["budget"] = row["budget"]
    return meta, sorted(found.values(), key=lambda c: c["name"].lower())


def match_from(label, raw_text):
    label = (label or "").lower()
    for match in rules.MATCH_TYPES:
        if match in label:
            return match
    if raw_text.startswith("[") and raw_text.endswith("]"):
        return "exact"
    if raw_text.startswith('"') and raw_text.endswith('"'):
        return "phrase"
    return "broad" if not label else ""


def account_keywords(path):
    meta, rows = read(path, "keywords report", extra_aliases=KEYWORD_ALIASES)
    io.require(meta, ["keyword", "campaign"], "keywords report")
    found, skipped_negative = {}, 0
    for row in rows:
        raw = (row.get("keyword") or "").strip()
        if not raw:
            continue
        if raw.startswith("-"):
            skipped_negative += 1
            continue
        text = raw.strip('[]"+').strip()
        match = match_from(row.get("match_type"), raw)
        key = (" ".join(rules.words(text)), match, row.get("campaign", ""), row.get("ad_group", ""))
        item = found.setdefault(key, {"text": text, "match": match, "campaign": row.get("campaign", ""),
                                      "ad_group": row.get("ad_group", ""), "status": (row.get("keyword_status") or "").strip(),
                                      "clicks": 0.0, "cost": 0.0, "conversions": 0.0})
        for field in ("clicks", "cost", "conversions"):
            item[field] += row.get(field) or 0
    keywords = sorted(found.values(), key=lambda k: (-k["conversions"], -k["cost"], k["text"]))
    return meta, keywords, skipped_negative


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True, help="folder for work files")
    parser.add_argument("--campaigns", help="campaigns report export, to keep new names clear of the account's campaigns")
    parser.add_argument("--keywords", help="keywords report export, to find keywords the account already has")
    args = parser.parse_args()

    account = {"campaigns_report": None, "keywords_report": None, "campaigns": [], "keywords": [],
               "campaign_title_rows": [], "keyword_title_rows": [], "keyword_columns": []}
    print("WHAT THE ACCOUNT ALREADY HAS")
    if args.campaigns:
        meta, campaigns = account_campaigns(args.campaigns)
        account.update(campaigns_report=os.path.basename(args.campaigns), campaigns=campaigns, campaign_title_rows=meta["title_rows"])
        print("  Campaigns report: %s. %s read." % (" / ".join(meta["title_rows"]) or account["campaigns_report"], rules.plural(len(campaigns), "campaign")))
        print("  A new campaign must not use one of these names. Google Ads Editor matches rows by name, so a row with one of")
        print("  these names would edit that campaign, pause it and change its budget. (Official: %s)" % rules.HAND)
        print(outputs.md_table(["Campaign", "Status", "Type", "Bid strategy", "Daily budget"],
                               [[c["name"], c["status"], c["type"], c["bid_strategy"], rules.shown(c["budget"])] for c in campaigns]))
        if not meta["columns"].get("campaign_status"):
            print("  The report has no Campaign status column, so removed campaigns cannot be told apart.")
    else:
        print("  No campaigns report was given, so new campaign names will not be checked against the account.")
        print("  To check them, download it in Google Ads: Campaigns, Download, CSV, with the columns Campaign, Campaign status and Campaign type.")
    print()
    if args.keywords:
        meta, keywords, skipped = account_keywords(args.keywords)
        account.update(keywords_report=os.path.basename(args.keywords), keywords=keywords, keyword_title_rows=meta["title_rows"],
                       keyword_columns=sorted(meta["columns"]))
        has_results = "conversions" in meta["columns"]
        print("  Keywords report: %s. %s read%s." % (" / ".join(meta["title_rows"]) or account["keywords_report"], rules.plural(len(keywords), "keyword"),
                                                      ", %s left out" % rules.plural(skipped, "negative keyword") if skipped else ""))
        print("  The check warns when a new keyword repeats one of these with the same match type. Use them to see what the account")
        print("  already covers%s." % (" and what converts" if has_results else ""))
        header = ["Keyword", "Match type", "Campaign", "Ad group", "Status"] + (["Clicks", "Cost", "Conversions"] if has_results else [])
        body = []
        for k in keywords[:MAX_KEYWORDS_SHOWN]:
            line = [k["text"], k["match"] or "not stated", k["campaign"], k["ad_group"], k["status"]]
            if has_results:
                line += ["{:,.0f}".format(k["clicks"]), rules.shown(k["cost"]), rules.shown(k["conversions"])]
            body.append(line)
        print(outputs.md_table(header, body))
        if len(keywords) > MAX_KEYWORDS_SHOWN:
            print("  Showing %d of %d, most conversions first. The check uses all %d." % (MAX_KEYWORDS_SHOWN, len(keywords), len(keywords)))
        if has_results:
            print("  Totals for the keywords read: %s clicks, %s cost, %s conversions."
                  % ("{:,.0f}".format(metrics.total(keywords, "clicks")), rules.shown(metrics.total(keywords, "cost")), rules.shown(metrics.total(keywords, "conversions"))))
    else:
        print("  No keywords report was given, so new keywords will not be compared with the account's keywords.")
        print("  To compare them, download it in Google Ads: Keywords, Search keywords, Download, CSV, with the columns Keyword, Match type, Campaign and Ad group.")

    outputs.ensure_dir(args.work)
    outputs.write_json(os.path.join(args.work, "account.json"), account)
    template_path = os.path.join(args.work, "plan.template.json")
    outputs.write_json(template_path, rules.template())
    # A new start begins a new check history. An earlier pass no longer counts.
    for stale in ("checked.json", "check-history.json"):
        if os.path.exists(os.path.join(args.work, stale)):
            os.remove(os.path.join(args.work, stale))
    plan_exists = os.path.exists(os.path.join(args.work, "plan.json"))

    print()
    print("LIMITS THE CHECK ENFORCES. Each line names the reference file it comes from.")
    for line, source in rules.LIMIT_LINES:
        print("  - %s (Official: %s)" % (line, source))
    print()
    print("THE PLAN FIELDS")
    for line in rules.FIELD_LINES:
        print("  - " + line)
    print()
    print("EVERYTHING IS WRITTEN PAUSED: campaigns, ad groups, keywords and ads. The plan has no way to enable anything.")
    print()
    if plan_exists:
        print("%s already exists and was kept. Run python3 scripts/check_plan.py --work %s to check it again."
              % (os.path.join(args.work, "plan.json"), args.work))
    else:
        print("Next: copy %s to %s, fill it in, then run python3 scripts/check_plan.py --work %s"
              % (template_path, os.path.join(args.work, "plan.json"), args.work))


if __name__ == "__main__":
    main()
