"""Write the review: a JSON file with every number, a workbook and a summary a client can read.

Imported by audit.py and add_actions.py. Nothing written here carries a vendor name.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics, outputs, xlsx  # noqa: E402

ACTION_KINDS = ("fix", "test", "investigate")
ACTION_LABELS = ("Official", "Practitioner rule", "Both")
GOAL_NOTE = ("These campaigns have different goals. Campaigns whose conversions carry value are judged by conv. value / cost, the others by cost per conversion. "
             "Judge each against its own goal, not against each other.")


def m(value):
    return metrics.money(value)


def n2(value):
    return "n/a" if value is None else "{:,.2f}".format(value)


def p(value, digits=1):
    return metrics.pct(value, digits)


def r2(value):
    return None if value is None else round(value, 2)


def ratio(value):
    return "n/a" if value is None else "{:,.2f}".format(value)


def vc(item):
    """Conv. value / cost, left out where conversions carry no value, as in a lead campaign."""
    if item.get("conversions") and not item.get("conv_value"):
        return "n/a"
    return ratio(item.get("roas"))


def vc_cell(item):
    return None if item.get("conversions") and not item.get("conv_value") else r2(item.get("roas"))


def table(header, rows):
    return outputs.md_table(header, rows)


def target_value(item, value):
    return ratio(value) if item.get("goal") == "conv. value / cost" else m(value)


def target_cell(item):
    if not item.get("target"):
        return ""
    return "%s (%s)" % (target_value(item, item["target"]), item["target_source"])


def validate_actions(review, actions):
    """Refuse actions that point at no finding, carry no label, or cut a channel on averages."""
    if not isinstance(actions, list):
        raise SystemExit('The actions file needs a list under "actions", each with finding, kind, action, where, label and priority.')
    findings = {f["id"]: f for f in review["findings"]}
    clean = []
    for number, item in enumerate(actions, start=1):
        fid = str(item.get("finding", "")).strip()
        if fid not in findings:
            raise SystemExit('Action %d points at finding "%s", which is not in this review. The findings are %s.' % (number, fid, ", ".join(findings) or "none"))
        kind = str(item.get("kind", "")).strip().lower()
        if kind not in ACTION_KINDS:
            raise SystemExit("Action %d needs a kind: fix, test or investigate." % number)
        label = str(item.get("label", "")).strip()
        if label not in ACTION_LABELS:
            raise SystemExit("Action %d needs a label: Official, Practitioner rule, or Both when it mixes a Google fact with advice." % number)
        text = str(item.get("action", "")).strip()
        if not text:
            raise SystemExit("Action %d has no text." % number)
        if label == "Both" and not ("Official:" in text and "Practitioner rule:" in text):
            raise SystemExit('Action %d is labelled Both. Start each sentence with "Official:" or "Practitioner rule:" so the reader sees which is which.' % number)
        if findings[fid]["no_fix"] and kind == "fix":
            raise SystemExit("Action %d is a fix for %s, a channel judged on its average cost per conversion. Performance Max optimises for "
                             "marginal return across channels (Official), so make it an investigate or test action." % (number, fid))
        try:
            priority = int(item.get("priority", 9))
        except (TypeError, ValueError):
            raise SystemExit("Action %d needs a whole number for priority." % number)
        clean.append({"finding": fid, "kind": kind, "action": text, "where": str(item.get("where", "") or findings[fid]["surface"]).strip(),
                      "label": "Labelled per sentence" if label == "Both" else label, "priority": priority, "finding_title": findings[fid]["title"]})
    clean.sort(key=lambda a: (a["priority"], a["finding"]))
    return clean


def validate_negatives(review, negatives):
    """Searches judged irrelevant, checked against the report: present, not converting, not brand."""
    if not isinstance(negatives, list):
        raise SystemExit('Put the searches judged irrelevant in a list under "negatives", each with search, campaign and reason.')
    if not negatives:
        return []
    st = review["parts"].get("search_terms")
    if not st:
        raise SystemExit("Negatives need the search terms report. Run audit.py with --search-terms first.")
    index = {}
    for term in st["terms"]:
        index.setdefault(term["search_term"].lower(), []).append(term)
    clean, seen = [], set()
    for number, item in enumerate(negatives, start=1):
        text = str(item.get("search", "")).strip()
        matches = index.get(text.lower())
        if not matches:
            raise SystemExit('Negative %d: the search "%s" is not in the search terms report. Copy it exactly from the report.' % (number, text))
        campaign = str(item.get("campaign", "")).strip()
        if campaign:
            ran_in = sorted({t["campaign"] for t in matches})
            matches = [t for t in matches if t["campaign"] == campaign]
            if not matches:
                raise SystemExit('Negative %d: "%s" did not run in "%s". It ran in: %s.' % (number, text, campaign, ", ".join(ran_in)))
        reason = str(item.get("reason", "")).strip()
        if not reason:
            raise SystemExit("Negative %d needs a reason, such as Job seekers." % number)
        for term in matches:
            if term["brand"]:
                raise SystemExit('Negative %d: "%s" is a brand search. Brand searches are handled with brand exclusions (Official), not negatives.' % (number, term["search_term"]))
            if term["conversions"] > 0:
                raise SystemExit('Negative %d: "%s" converted in %s. A converting search is never excluded.' % (number, term["search_term"], term["campaign"]))
            key = (term["search_term"].lower(), term["campaign"])
            if key in seen:
                continue
            seen.add(key)
            clean.append({"search": term["search_term"], "campaign": term["campaign"], "clicks": term["clicks"], "cost": term["cost"], "reason": reason,
                          "negative": "[%s]" % term["search_term"], "match": "exact", "level": "campaign", "spent_enough": term["over_line"]})
    clean.sort(key=lambda n: -n["cost"])
    return clean


def key_numbers(review):
    parts, lines = review["parts"], []
    camp = parts.get("campaigns")
    if camp:
        t = camp["total"]
        if camp["value_mixed"]:
            lines.append("Performance Max spent %s for %s conversions across %d campaigns (%d enabled). The campaigns have different goals, so each is judged "
                         "against its own: %s." % (m(t["cost"]), n2(t["conversions"]), len(camp["campaigns"]), camp["by_state"]["Enabled"], "; ".join(
                             "%s by %s, %s" % (c["campaign"], c["goal"], vc(c) if c["goal"] == "conv. value / cost" else m(c["cpa"])) for c in camp["campaigns"] if c["cost"])))
        else:
            lines.append("Performance Max spent %s for %s conversions, %s per conversion%s, across %d campaigns (%d enabled)." % (
                m(t["cost"]), n2(t["conversions"]), m(t["cpa"]), ", %s conv. value / cost" % ratio(t["roas"]) if camp["has_value"] else "",
                len(camp["campaigns"]), camp["by_state"]["Enabled"]))
    ch = parts.get("channels")
    if ch and ch["channels"]:
        top = ch["channels"][0]
        lines.append("%s carries the most cost, %s of the channel report's cost. Google Search and Search partners carry %s of it." % (
            top["channel"], p(top["share_of_cost"]), p(ch["search_share_of_cost"])))
    ag = parts.get("asset_groups")
    if ag and ag["below_good"]:
        lines.append("Asset groups rated below Good carry %s, %s of the asset group report's cost." % (m(ag["below_good"]["cost"]), p(ag["below_good"]["share_of_cost"])))
    st = parts.get("search_terms")
    if st and st["brand"]:
        lines.append("Brand searches are %s of the listed Performance Max search cost and %s of the listed conversions in the search terms report." % (
            p(st["brand"]["share_of_cost"]), p(st["brand"]["share_of_conversions"])))
    if st and st["has_cost"]:
        lines.append("Non brand searches with cost and no conversions: %d, costing %s, %s of the listed Performance Max search cost. %d of them spent at least %s, "
                     "enough to judge on spend alone, costing %s." % (st["no_conv"]["searches"], m(st["no_conv"]["cost"]), p(st["no_conv"]["share_of_cost"]),
                                                                      len(st["over_line"]), m(st["line"]["value"]), m(st["over_line_cost"])))
    pr = parts.get("products")
    if pr:
        lines.append("Products with cost and no conversions: %d, costing %s, %s of the products report's cost. %d of them spent at least %s, "
                     "enough to judge on spend alone, costing %s." % (pr["no_conv"]["products"], m(pr["no_conv"]["cost"]), p(pr["no_conv"]["share_of_cost"]),
                                                                      len(pr["over_line"]), m(pr["line"]["value"]), m(pr["over_line_cost"])))
        lines.append("The top 10 products carry %s of the products report's cost. %s products make half of it." % (p(pr["concentration"]["top10_share"]), pr["concentration"]["for_half"] or 0))
    pc = parts.get("prices")
    if pc:
        text = "%d products are priced above their benchmark" % pc["above"]["products"]
        if pc["with_performance"]:
            text += ", carrying %s of the cost on products with a benchmark" % p(pc["above"]["share_of_priced_cost"])
        lines.append(text + ".")
    return lines


def evidence_lines(review):
    parts, cons, lines = review["parts"], review["consistency"], []
    rows = []
    for r in cons["reports"]:
        if r["compare_cost"] is None:
            compared = ""
        elif r["expect"] == "equal":
            compared = "difference %s" % m(r["difference"])
        else:
            compared = "%s of it" % p(r["share"])
        rows.append([r["report"], "%s to %s" % tuple(r["date_range"]) if r["date_range"] else "not stated", m(r["cost"]) if r["cost"] is not None else "no Cost column",
                     n2(r["conversions"]), r["compare_to"] or "", m(r["compare_cost"]) if r["compare_cost"] is not None else "", compared])
    if rows:
        lines += [table(["Report", "Date range", "Cost", "Conversions", "Compared with", "That cost", "Result"], rows), ""]
    for kind, title in (("campaigns", "campaign report"), ("asset_groups", "asset group report"), ("channels", "channel performance report"),
                        ("search_terms", "search terms report"), ("products", "products report")):
        part = parts.get(kind)
        if not part:
            continue
        rec = part.get("reconcile")
        if rec:
            if kind == "search_terms" and part["not_listed_cost"] > 0:
                lines.append("- The %s lists searches costing %s. Its total row \"%s\" says %s, so %s sits on searches Google does not list. Every share of search cost here is of the listed cost." % (
                    title, m(rec["rows_cost"]), rec["label"], m(rec["file_cost"]), m(part["not_listed_cost"])))
            else:
                lines.append("- The %s rows add up to %s. Its total row \"%s\" says %s. Difference: %s." % (title, m(rec["rows_cost"]), rec["label"], m(rec["file_cost"]), m(rec["difference"])))
        elif not review["inputs"]["campaigns"]:
            lines.append("- The %s has no total row with cost to check the rows against." % title)
        if part.get("other_types_left_out"):
            lines.append("- %d rows of other campaign types were left out of the %s." % (part["other_types_left_out"], title))
        if kind in ("campaigns", "search_terms") and not part.get("type_column"):
            lines.append("- The %s has no Campaign type column, so every row was read as Performance Max." % title)
    for kind, info in review["reports"].items():
        if info["odd_total_labels"]:
            lines.append("- In the %s, rows starting with \"Total\" were read as total rows: %s. If one is a product or campaign name, it is missing from the review." % (
                kind.replace("_", " "), ", ".join(info["odd_total_labels"])))
    camp = parts.get("campaigns")
    if camp and camp["paused_with_cost"]:
        lines.append("- Spent in this period and now paused or removed: %s. These are reported, not judged as underspending." % ", ".join(camp["paused_with_cost"]))
    if review["inputs"]["campaigns"]:
        lines.append("- The review is limited to: %s. Reports with no Campaign column are read whole." % ", ".join(review["inputs"]["campaigns"]))
    return lines


def write_markdown(review, actions):
    parts = review["parts"]
    lines = ["# Performance Max review", ""]
    if len(review["currency"]) == 1:
        lines += ["Amounts are in %s." % review["currency"][0], ""]
    elif len(review["currency"]) > 1:
        lines += ["The reports carry more than one currency (%s). Totals mix them." % ", ".join(review["currency"]), ""]
    lines += ["## Key numbers", ""] + ["- %s" % t for t in key_numbers(review)]
    lines += ["", "## Evidence check", ""] + evidence_lines(review)

    camp = parts.get("campaigns")
    if camp and camp["campaigns"]:
        lines += ["", "## Campaigns", ""]
        if camp["value_mixed"]:
            lines += [GOAL_NOTE, ""]
        lines += [table(
            ["Campaign", "Campaign status", "Status", "Bid strategy type", "Judged by", "Budget", "Cost", "Share of Performance Max cost in the campaign report", "Conversions",
             "Cost / conv.", "Conv. value / cost", "Target", "Against target"],
            [[c["campaign"], c["campaign_status"] or c["state"], c["status"], c["bid_strategy"], c["goal"], m(c["budget"]) if c["budget"] is not None else "", m(c["cost"]),
              p(c["share_of_cost"]), n2(c["conversions"]), m(c["cpa"]), vc(c), target_cell(c), c.get("against_target", "")] for c in camp["campaigns"]])]
        lines.append("")
        lines.append("Each campaign is set against the target for its own goal: target cost per conversion for cost / conv., target ROAS (as conv. value / cost) "
                     "for conv. value / cost. Your target comes first; the campaign's own setting is used only when you gave none.")
        for c in camp["campaigns"]:
            if c.get("target_conflict"):
                lines.append("- %s: your target %s differs from the campaign's own setting %s. Your target is used here; the campaign bids to its own." % (
                    c["campaign"], target_value(c, c["target"]), target_value(c, c["campaign_target"])))

    ch = parts.get("channels")
    if ch:
        lines += ["", "## Channels", "",
                  "Official: Performance Max optimises for marginal return across channels, so an average cost per conversion by channel can mislead. "
                  "Read a channel that looks expensive against the campaign's goal and the report's diagnostics before acting.", "",
                  table(["Channel", "Status", "Cost", "Share of channel report cost", "Conversions", "Share of channel report conversions", "Share of channel report conv. value",
                         "Cost / conv.", "Conv. value / cost"],
                        [[c["channel"], " / ".join(c["statuses"]), m(c["cost"]), p(c["share_of_cost"]), n2(c["conversions"]), p(c["share_of_conversions"]),
                          p(c["share_of_value"]) if ch["has_value"] and not ch["value_mixed"] else "n/a", m(c["cpa"]),
                          vc(c) if not ch["value_mixed"] else "n/a"] for c in ch["channels"]]),
                  "", "- Shares are of the channel report's own total: %s cost, %s conversions." % (m(ch["total"]["cost"]), n2(ch["total"]["conversions"])),
                  "- Google Search and Search partners carry %s of that cost." % p(ch["search_share_of_cost"])]
        if ch["no_cost"]:
            lines.append("- No cost on %s. Official: a channel with no ads and no listed issue most likely means the campaign favours channels with a higher return." % ", ".join(ch["no_cost"]))
        lines.append("- Official: Conversions here are only the conversions the campaign optimises for, and store visit conversions are not split by channel.")
        if ch["value_mixed"]:
            lines.append("- " + GOAL_NOTE + " In this report each channel is compared only within its campaign, in the table below.")
        if len({c["campaign"] for c in ch["per_campaign"]}) > 1:
            lines += ["", "By campaign. Each share is of that campaign's own total in the channel report:", "",
                      table(["Campaign", "Channel", "Status", "Cost", "Share of campaign cost", "Share of campaign conversions", "Share of campaign conv. value"],
                            [[c["campaign"], c["channel"], " / ".join(c["statuses"]), m(c["cost"]), p(c["share_of_cost"]), p(c["share_of_conversions"]),
                              p(c["share_of_value"]) if c["basis"] == "conv. value" else "n/a"] for c in ch["per_campaign"] if c["cost"] or c["issues"]])]
        if ch["formats"]:
            lines += ["", table(["Channel", "Segment", "Value", "Cost", "Conversions", "Cost / conv."],
                                [[f["channel"], f["segment"], f["value"], m(f["cost"]), n2(f["conversions"]), m(f["cpa"])] for f in ch["formats"]])]

    ag = parts.get("asset_groups")
    if ag:
        lines += ["", "## Asset groups", ""]
        if ag["value_mixed"]:
            lines += [GOAL_NOTE + " Compare an asset group only with others in its campaign.", ""]
        lines += [table(
            ["Asset group", "Campaign", "Status", "Ad strength", "Judged by", "Cost", "Share of asset group report cost", "Share of its campaign's cost", "Conversions",
             "Cost / conv.", "Conv. value / cost"],
            [[g["asset_group"], g["campaign"], g["status"] or g["state"], g["ad_strength"], g["goal"], m(g["cost"]), p(g["share_of_cost"]), p(g["share_of_campaign_cost"]),
              n2(g["conversions"]), m(g["cpa"]), vc(g)]
             for g in ag["groups"][:20]])]
        if len(ag["groups"]) > 20:
            lines.append("\nThe %d asset groups with the least cost are in the workbook." % (len(ag["groups"]) - 20))
        if ag["has_strength"]:
            lines += ["", table(["Ad strength", "Asset groups", "Cost", "Share of asset group report cost", "Conversions", "Cost / conv."],
                                [[s["ad_strength"], s["groups"], m(s["cost"]), p(s["share_of_cost"]), n2(s["conversions"]), "n/a" if ag["value_mixed"] else m(s["cpa"])]
                                 for s in ag["by_strength"]]),
                      "", "Official: Google recommends Ad strength of Good or Excellent. Ad strength measures asset coverage and variety, not auction outcome."]
        lines += ["", table(["Campaign", "Asset groups", "Cost", "Largest group's share of campaign cost", "Spent enough to judge"],
                            [[s["campaign"] or "(not named)", s["groups"], m(s["cost"]), p(s["top_share"]), m(s["line"]["value"])] for s in ag["by_campaign"]])]

    st = parts.get("search_terms")
    if st:
        t = st["total"]
        lines += ["", "## Searches", "",
                  "- %d Performance Max searches listed, %s cost, %s conversions." % (len(st["terms"]), m(t["cost"]) if st["has_cost"] else "no Cost column", n2(t["conversions"]))]
        if st["field"] == "search_category":
            lines.append("- This file lists search categories, not single searches.")
        if st["brand"]:
            lines += ["", table(["Searches", "Count", "Cost", "Share of listed search cost", "Conversions", "Share of listed conversions", "Share of listed conv. value"],
                                [[name, part["searches"], m(part["cost"]) if st["has_cost"] else "n/a", p(part["share_of_cost"]) if st["has_cost"] else "n/a", n2(part["conversions"]),
                                  p(part["share_of_conversions"]), p(part["share_of_value"]) if st["has_value"] else "n/a"]
                                 for name, part in (("Brand", st["brand"]), ("Non brand", st["non_brand"]))]),
                      "", "Brand terms used: %s. A search counts as brand when it holds one of them as whole words. Misspellings are not matched." % ", ".join(st["brand_terms"])]
        if st["has_cost"]:
            lines += ["", "- A non brand search has spent enough to judge at %s with no conversions. That is %s." % (m(st["line"]["value"]), st["line"]["source"])]
            lines.append("- %d non brand searches had cost and no conversions, costing %s. %d reached that line, costing %s. %d did not, costing %s." % (
                len(st["no_conv_terms"]), m(st["no_conv"]["cost"]), len(st["over_line"]), m(st["over_line_cost"]), st["below_line"]["searches"], m(st["below_line"]["cost"])))
            if st["no_conv_terms"]:
                lines += ["", table(["Search", "Campaign", "Clicks", "Cost", "Spent enough to judge", "Holds a word that never converted"],
                                    [[x["search_term"], x["campaign"], int(x["clicks"]), m(x["cost"]), "Yes" if x["over_line"] else "", x["candidate_word"]]
                                     for x in st["no_conv_terms"][:25]])]
                if len(st["no_conv_terms"]) > 25:
                    lines.append("\nThe other %d are in the workbook, sheet Searches." % (len(st["no_conv_terms"]) - 25))
            if st["waste_words"]:
                lines += ["", "Words and phrases in two or more searches with cost and no conversions:", "",
                          table(["Word or phrase", "Searches", "Cost"], [[g["phrase"], g["searches"], m(g["cost"])] for g in st["waste_words"][:10]])]
            if st["held_back_words"]:
                lines.append("\nHeld back from that list because every word appears in a product title, asset group name or campaign name, so a negative would block "
                             "the account's own business: %s." % ", ".join('"%s" (%s)' % (g["phrase"], m(g["cost"])) for g in st["held_back_words"][:10]))

    pr = parts.get("products")
    if pr:
        t, c = pr["total"], pr["concentration"]
        lines += ["", "## Products", "",
                  "- %d products, %d of them with cost. %s cost, %s conversions, %s per conversion%s." % (
                      c["count"], c["with_cost"], m(t["cost"]), n2(t["conversions"]), m(t["cpa"]), ", %s conv. value / cost" % ratio(t["roas"]) if pr["has_value"] else ""),
                  "- The top 10 products carry %s of the products report's cost. %s products make half of it and %s make 80%%." % (p(c["top10_share"]), c["for_half"] or 0, c["for_80"] or 0)]
        if pr["value_concentration"]:
            lines.append("- The top 10 products by conv. value carry %s of all product conv. value." % p(pr["value_concentration"]["top10_share"]))
        if pr["no_impressions"] is not None:
            lines.append("- Products in the report with no impressions: %d." % pr["no_impressions"])
        if pr["skipped_rows"]:
            lines.append("- %d rows had no Item ID or Title and were left out." % pr["skipped_rows"])
        lines.append("- A product has spent enough to judge at %s with no conversions. That is %s." % (m(pr["line"]["value"]), pr["line"]["source"]))
        lines.append("- %d products had cost and no conversions, costing %s. %d reached that line, costing %s." % (
            pr["no_conv"]["products"], m(pr["no_conv"]["cost"]), len(pr["over_line"]), m(pr["over_line_cost"])))
        if pr["over_line"]:
            lines += ["", table(["Item ID", "Title", "Product type", "Clicks", "Cost"],
                                [[x["item_id"], x["title"], x["product_type"], int(x["clicks"]), m(x["cost"])] for x in pr["over_line"][:15]])]
        for field, label in (("product_type", "Product type (1st level)"), ("brand", "Brand")):
            if pr["groups"].get(field):
                lines += ["", "By %s:" % label, "", table(
                    [label, "Products", "Cost", "Share of products report cost", "Conversions", "Cost / conv.", "Share of products report conv. value", "Cost with no conversions"],
                    [[g["value"], g["products"], m(g["cost"]), p(g["share_of_cost"]), n2(g["conversions"]), m(g["cpa"]), p(g["share_of_value"]) if pr["has_value"] else "n/a", m(g["no_conv_cost"])]
                     for g in pr["groups"][field][:10]])]
        labels = [label for label in pr["dimensions"] if label.startswith("Custom label")]
        if labels:
            lines.append("\nTotals by %s are in the workbook." % ", ".join(labels))
        if pr["gaps"]:
            lines += ["", "Blank attributes:", "", table(["Attribute", "Products blank", "Share of products in the report", "Cost on them", "Share of products report cost"],
                                                       [[g["attribute"], g["products"], p(g["share_of_products"]), m(g["cost"]), p(g["share_of_cost"])] for g in pr["gaps"]])]
        if pr["status"]:
            lines += ["", table(["Product status", "Products", "With listed issues", "Cost"], [[s["status"], s["products"], s["with_issues"], m(s["cost"])] for s in pr["status"]])]
        if pr["target_roas"]:
            lines.append("\n- Products below the target ROAS of %s after spending enough to judge: %d." % (p(pr["target_roas"], 0), len(pr["below_target_roas"])))

    pc = parts.get("prices")
    if pc:
        lines += ["", "## Prices against the benchmark", "",
                  "- Price positions come from %s. %d products have a benchmark." % (pc["source"], pc["matched"])]
        if pc["unmatched_in_price_file"]:
            lines.append("- %d products in the price file are not in the products report." % pc["unmatched_in_price_file"])
        lines += ["", table(["Position", "Products", "Cost", "Share of cost on products with a benchmark", "Clicks", "Conversions", "Conv. rate", "Conv. value / cost"],
                            [[g["position"], g["products"], m(g["cost"]), p(g["share_of_priced_cost"]) if g["share_of_priced_cost"] is not None else "", "{:,.0f}".format(g["clicks"]),
                              n2(g["conversions"]), p(g["conv_rate"], 2), vc(g)] for g in pc["groups"]])]
        if pc["above"]["median_gap"] is not None:
            lines.append("\n- The middle product above benchmark is priced %s over it." % p(pc["above"]["median_gap"]))
        if pc["top_above"]:
            lines += ["", table(["Item ID", "Title", "Price", "Benchmark", "Gap", "Cost", "Conversions"],
                                [[x["item_id"], x["title"], n2(x["price"]), n2(x["benchmark"]), p(x["gap"]), m(x["cost"]), n2(x["conversions"])] for x in pc["top_above"][:15]])]
        lines += ["", "Official: the benchmark is the average price that typically leads to more successful auctions, clicks or conversions for the same GTIN. "
                      "A product needs a valid GTIN to get one, and the Merchant Center view counts clicks over the last 28 days."]

    lines += ["", "## Findings", ""]
    if not review["findings"]:
        lines.append("Nothing in these reports crossed a line the review checks.")
    for f in review["findings"]:
        lines.append("- **%s. %s** (%s, %s). %s Where the fix lives: %s. %s: %s" % (
            f["id"], f["title"], f["kind"], f["area"], f["detail"], f["surface"], f["label"], f["rule"]))
    if actions:
        lines += ["", "## Recommended fixes", ""]
        for number, a in enumerate(actions, start=1):
            lines.append("%d. **%s** (%s, for %s: %s). Where: %s. %s." % (number, a["action"].rstrip("."), a["kind"], a["finding"], a["finding_title"], a["where"], a["label"]))
    negs = review.get("negatives") or []
    if negs:
        lines += ["", "## Negatives to review", "",
                  "%d searches were judged irrelevant to the business, costing %s. Each is written as an exact match negative for its campaign, "
                  "so it blocks that search only. Review them before adding." % (len(negs), m(sum(n["cost"] for n in negs))), "",
                  table(["Negative keyword", "Campaign", "Clicks", "Cost", "Reason"], [[n["negative"], n["campaign"], int(n["clicks"]), m(n["cost"]), n["reason"]] for n in negs])]

    lines += ["", "## How the numbers were made", "",
              "- Every number comes from the reports listed above. Rows of the same campaign, asset group, channel, search or product are added together first.",
              "- \"Spent enough to judge\" is the cost a row must reach, with no conversions, before it is listed. It is the target cost per conversion when one was given, "
              "and otherwise the report's own cost per conversion, with brand searches left out for searches. It is a sorting line, not a verdict.",
              "- Each share names its base. Channel shares are of the channel report's total. Search shares are of the listed searches. Product shares are of the products report.",
              "- A channel is raised as a question when its share of cost is larger than its share of what the campaign earns: conv. value where the campaign's "
              "conversions carry value, and conversions where they do not. It is judged within each campaign when the channel report names campaigns. Paused campaigns are not judged.",
              "- Conv. value / cost is left out where conversions carry no value, as in a lead campaign.",
              "- Below Good means Ad strength Average or Poor. Pending or blank Ad strength is shown as Not rated.",
              "- A product is above benchmark when its price is higher than the benchmark price. When both prices are given the gap is price divided by benchmark, minus one.",
              "- Findings are ordered: data checks first, then spend with no conversions, setup risks and questions, each by cost.",
              "- A word is held back from the negative candidates when every word in it appears in a product title, an asset group name or a campaign name."]
    lines += ["", "## What this did not cover", ""]
    for c in review["checks"]:
        if c["status"] != "Ran":
            lines.append("- %s. Needs %s." % (c["check"], c["unlock"]))
        elif c["note"]:
            lines.append("- %s: %s" % (c["check"], c["note"]))
    lines += ["- The assets themselves, search themes, audience signals, URL settings and exclusions. These exports do not show them.",
              "- Official: placement reports are for brand safety, not for judging performance, and were not read.",
              "- Official: only about half of Performance Max conversions land inside the 30 day click and 3 day engaged view windows, so a short date range understates it.",
              "- Searches Google leaves out of the search terms report, and searches that did not happen in this date range."]
    return "\n".join(lines) + "\n"


def write_workbook(review, actions, path):
    parts = review["parts"]
    book = xlsx.Workbook()
    book.add_sheet("Key numbers", ["Key number"], [[t] for t in key_numbers(review)], widths={0: 120})
    book.add_sheet("Findings", ["ID", "Kind", "Area", "Finding", "Detail", "Cost involved", "Where the fix lives", "Basis", "Rule"],
                   [[f["id"], f["kind"], f["area"], f["title"], f["detail"], r2(f["cost"]), f["surface"], f["label"], f["rule"]] for f in review["findings"]],
                   formats={4: "wrap", 5: "money", 8: "wrap"}, widths={3: 40, 4: 70, 6: 40, 8: 70})
    if actions:
        book.add_sheet("Recommended fixes", ["Priority", "Finding", "Kind", "Action", "Where", "Basis"],
                       [[a["priority"], a["finding"], a["kind"], a["action"], a["where"], a["label"]] for a in actions],
                       formats={0: "int", 3: "wrap"}, widths={3: 80, 4: 40})
    if review.get("negatives"):
        book.add_sheet("Negatives to review", ["Negative keyword", "Match type", "Level", "Campaign", "Search term", "Clicks", "Cost", "Spent enough to judge", "Reason"],
                       [[n["negative"], n["match"], n["level"], n["campaign"], n["search"], int(n["clicks"]), r2(n["cost"]), "Yes" if n["spent_enough"] else "", n["reason"]]
                        for n in review["negatives"]], formats={5: "int", 6: "money"}, widths={0: 40, 4: 40, 8: 40})
    book.add_sheet("Checks", ["Check", "Status", "Used", "Report that unlocks it", "Note"],
                   [[c["check"], c["status"], c["used"], c["unlock"], c["note"]] for c in review["checks"]], formats={3: "wrap"}, widths={0: 50, 3: 80, 4: 50})
    cons = review["consistency"]
    book.add_sheet("Evidence check", ["Report", "Start", "End", "Cost", "Conversions", "Compared with", "That cost", "Difference", "Share"],
                   [[r["report"], (r["date_range"] or ["", ""])[0], (r["date_range"] or ["", ""])[1], r2(r["cost"]), r2(r["conversions"]), r["compare_to"],
                     r2(r["compare_cost"]), r["difference"] if r["expect"] == "equal" else None, r["share"] if r["expect"] == "part" else None] for r in cons["reports"]],
                   formats={3: "money", 4: "money", 6: "money", 7: "money", 8: "pct"}, widths={5: 60})
    camp = parts.get("campaigns")
    if camp:
        book.add_sheet("Campaigns", ["Campaign", "Campaign status", "Status", "Bid strategy type", "Budget", "Days", "Avg. daily cost", "Impr.", "Clicks", "Cost",
                                     "Share of Performance Max cost", "Conversions", "Cost / conv.", "Conv. value", "Conv. value / cost", "Judged by", "Target",
                                     "Target from", "Against target"],
                       [[c["campaign"], c["campaign_status"] or c["state"], c["status"], c["bid_strategy"], c["budget"], c["days"], r2(c["avg_daily_cost"]), int(c["impressions"]),
                         int(c["clicks"]), r2(c["cost"]), c["share_of_cost"], r2(c["conversions"]), r2(c["cpa"]), r2(c["conv_value"]), vc_cell(c), c["goal"],
                         r2(c.get("target")), c.get("target_source", ""), c.get("against_target", "")] for c in camp["campaigns"]],
                       formats={4: "money", 5: "int", 6: "money", 7: "int", 8: "int", 9: "money", 10: "pct", 11: "money", 12: "money", 13: "money", 14: "money",
                                16: "money"})
        if cons["per_campaign"]:
            book.add_sheet("Cost by report", ["Campaign", "State", "Campaign report cost", "Asset group report cost", "Channel report cost"],
                           [[r["campaign"], r["state"], r2(r["campaign_cost"]), r2(r["asset_group_cost"]), r2(r["channel_cost"])] for r in cons["per_campaign"]],
                           formats={2: "money", 3: "money", 4: "money"})
    ch = parts.get("channels")
    if ch:
        header = ["Channel", "Status", "Impr.", "Clicks", "Cost", "Share of cost", "Conversions", "Share of conversions", "Conv. value", "Share of conv. value", "Cost / conv.", "Conv. value / cost"]
        book.add_sheet("Channels", header, [[c["channel"], " / ".join(c["statuses"]), int(c["impressions"]), int(c["clicks"]), r2(c["cost"]), c["share_of_cost"], r2(c["conversions"]),
                                             c["share_of_conversions"], r2(c["conv_value"]), c["share_of_value"], r2(c["cpa"]), vc_cell(c)] for c in ch["channels"]],
                       formats={2: "int", 3: "int", 4: "money", 5: "pct", 6: "money", 7: "pct", 8: "money", 9: "pct", 10: "money", 11: "money"})
        if ch["per_campaign"]:
            book.add_sheet("Channels by campaign", ["Campaign", "Channel", "Cost", "Conversions", "Conv. value", "Cost / conv."],
                           [[c["campaign"], c["channel"], r2(c["cost"]), r2(c["conversions"]), r2(c["conv_value"]), r2(c["cpa"])] for c in ch["per_campaign"]],
                           formats={2: "money", 3: "money", 4: "money", 5: "money"})
    ag = parts.get("asset_groups")
    if ag:
        book.add_sheet("Asset groups", ["Asset group", "Campaign", "State", "Status", "Ad strength", "Impr.", "Clicks", "Cost", "Share of asset group cost",
                                        "Share of campaign cost", "Conversions", "Cost / conv.", "Conv. value", "Conv. value / cost", "Spent enough to judge, no conversions"],
                       [[g["asset_group"], g["campaign"], g["state"], g["status"], g["ad_strength"], int(g["impressions"]), int(g["clicks"]), r2(g["cost"]), g["share_of_cost"],
                         g["share_of_campaign_cost"], r2(g["conversions"]), r2(g["cpa"]), r2(g["conv_value"]), vc_cell(g), "Yes" if g["no_conv_over_line"] else ""] for g in ag["groups"]],
                       formats={5: "int", 6: "int", 7: "money", 8: "pct", 9: "pct", 10: "money", 11: "money", 12: "money", 13: "money"})
    st = parts.get("search_terms")
    if st:
        book.add_sheet("Searches", ["Search term", "Campaign", "Brand", "Impr.", "Clicks", "Cost", "Conversions", "Cost / conv.", "Conv. value", "Spent enough to judge, no conversions",
                                    "Holds a word that never converted"],
                       [[t["search_term"], t["campaign"], "Yes" if t["brand"] else "", int(t["impressions"]), int(t["clicks"]), r2(t["cost"]), r2(t["conversions"]), r2(t["cpa"]),
                         r2(t["conv_value"]), "Yes" if t["over_line"] else "", t.get("candidate_word", "")] for t in st["terms"]],
                       formats={3: "int", 4: "int", 5: "money", 6: "money", 7: "money", 8: "money"}, widths={0: 40})
        book.add_sheet("Words with no conversions", ["Word or phrase, in two or more searches", "Searches", "Clicks", "Cost"],
                       [[g["phrase"], g["searches"], int(g["clicks"]), r2(g["cost"])] for g in st["waste_words"]], formats={1: "int", 2: "int", 3: "money"}, widths={0: 44})
    pr = parts.get("products")
    if pr:
        book.add_sheet("Products", ["Item ID", "Title", "Brand", "Product type (1st level)", "Category (1st level)"] + ["Custom label %d" % n for n in range(5)] +
                       ["Status", "Impr.", "Clicks", "Cost", "Share of product cost", "Conversions", "Cost / conv.", "Conv. value", "Conv. value / cost",
                        "Spent enough to judge, no conversions", "Below target ROAS"],
                       [[x["item_id"], x["title"], x["brand"], x["product_type"], x["category"]] + [x["custom_label_%d" % n] for n in range(5)] +
                        [x["product_status"], int(x["impressions"]), int(x["clicks"]), r2(x["cost"]), x["share_of_cost"], r2(x["conversions"]), r2(x["cpa"]), r2(x["conv_value"]),
                         r2(x["roas"]), "Yes" if x["over_line"] else "", "Yes" if x["below_target_roas"] else ""] for x in pr["products"]],
                       formats={11: "int", 12: "int", 13: "money", 14: "pct", 15: "money", 16: "money", 17: "money", 18: "money"}, widths={1: 44})
        group_rows = [[g["dimension"], g["value"], g["products"], r2(g["cost"]), g["share_of_cost"], r2(g["conversions"]), r2(g["cpa"]), r2(g["conv_value"]), g["share_of_value"],
                       r2(g["roas"]), g["no_conv_products"], r2(g["no_conv_cost"]), g["share_of_no_conv_cost"]] for f in pr["groups"] for g in pr["groups"][f]]
        book.add_sheet("Product groups", ["Dimension", "Value", "Products", "Cost", "Share of product cost", "Conversions", "Cost / conv.", "Conv. value", "Share of conv. value",
                                          "Conv. value / cost", "Products with cost and no conversions", "Their cost", "Share of all no conversion cost"], group_rows,
                       formats={2: "int", 3: "money", 4: "pct", 5: "money", 6: "money", 7: "money", 8: "pct", 9: "money", 10: "int", 11: "money", 12: "pct"}, widths={1: 36})
        if pr["gaps"]:
            book.add_sheet("Blank attributes", ["Attribute", "Products blank", "Share of products", "Cost on them", "Share of product cost"],
                           [[g["attribute"], g["products"], g["share_of_products"], r2(g["cost"]), g["share_of_cost"]] for g in pr["gaps"]],
                           formats={1: "int", 2: "pct", 3: "money", 4: "pct"})
    pc = parts.get("prices")
    if pc:
        book.add_sheet("Price positions", ["Position", "Products", "Cost", "Share of cost on products with a benchmark", "Clicks", "Conversions", "Conv. rate", "Conv. value", "Conv. value / cost"],
                       [[g["position"], g["products"], r2(g["cost"]), g["share_of_priced_cost"], int(g["clicks"]), r2(g["conversions"]), g["conv_rate"], r2(g["conv_value"]), r2(g["roas"])]
                        for g in pc["groups"]], formats={1: "int", 2: "money", 3: "pct", 4: "int", 5: "money", 6: "pct", 7: "money", 8: "money"})
        book.add_sheet("Prices", ["Item ID", "Title", "Brand", "Product type", "Price", "Benchmark", "Gap", "Position", "Clicks", "Cost", "Conversions", "Conv. value"],
                       [[x["item_id"], x["title"], x["brand"], x["product_type"], r2(x["price"]), r2(x["benchmark"]), x["gap"], x["position"], int(x["clicks"] or 0),
                         r2(x["cost"]), r2(x["conversions"]), r2(x["conv_value"])] for x in pc["rows"]],
                       formats={4: "money", 5: "money", 6: "pct", 8: "int", 9: "money", 10: "money", 11: "money"}, widths={1: 44})
    book.save(path)


def write_all(review, out, actions=None, negatives=None):
    outputs.ensure_dir(out)
    review["actions"] = actions or []
    review["negatives"] = negatives or []
    outputs.write_json(os.path.join(out, "pmax-review.json"), review)
    write_workbook(review, review["actions"], os.path.join(out, "pmax-review.xlsx"))
    text = write_markdown(review, review["actions"])
    with open(os.path.join(out, "pmax-review.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    return text


def judgment_block(review):
    """What the AI tool needs to judge, printed only, never written to the client files."""
    parts = review["parts"]
    lines = ["", "=" * 70, "FOR YOUR JUDGMENT. Not in the client files.", ""]
    lines.append("Findings. A finding marked 'investigate or test only' takes no fix action.")
    lines.append(table(["ID", "Kind", "Area", "Finding", "Cost involved", "Where the fix lives", "Actions allowed"],
                       [[f["id"], f["kind"], f["area"], f["title"], m(f["cost"]) if f["cost"] is not None else "", f["surface"],
                         "investigate or test only" if f["no_fix"] else "fix, test or investigate"] for f in review["findings"]]))
    st = parts.get("search_terms")
    if st and st["no_conv_terms"]:
        lines += ["", "Every non brand search with cost and no conversions, by cost. Judge each for relevance, whatever it cost. 'Yes' marks those that spent at least %s, "
                      "enough to judge on spend alone. Record the ones the business can never convert under negatives in actions.json." % m(st["line"]["value"]),
                  table(["Search", "Campaign", "Clicks", "Cost", "Spent enough to judge", "Holds a word that never converted"],
                        [[t["search_term"], t["campaign"], int(t["clicks"]), m(t["cost"]), "Yes" if t["over_line"] else "", t["candidate_word"]] for t in st["no_conv_terms"][:300]])]
        if len(st["no_conv_terms"]) > 300:
            lines.append("%d more are in the workbook, sheet Searches." % (len(st["no_conv_terms"]) - 300))
        if st["below_line_with_word"]:
            lines += ["", "Below the line, but holding a word that never converted elsewhere:",
                      table(["Search", "Campaign", "Cost", "Word"], [[t["search_term"], t["campaign"], m(t["cost"]), t["candidate_word"]] for t in st["below_line_with_word"]])]
        if st["held_back_words"]:
            lines.append("Words held back from the candidates because every word names something the account sells or builds: %s." % ", ".join(
                '"%s"' % g["phrase"] for g in st["held_back_words"][:15]))
    if st and st["brand"]:
        lines += ["", "Brand searches by cost, to judge capture against cannibalisation:",
                  table(["Search", "Campaign", "Cost", "Conversions"], [[t["search_term"], t["campaign"], m(t["cost"]), n2(t["conversions"])] for t in st["terms"] if t["brand"]][:20])]
    pr = parts.get("products")
    if pr and pr["over_line"]:
        lines += ["", "Products that spent at least %s with no conversions:" % m(pr["line"]["value"]),
                  table(["Item ID", "Title", "Brand", "Product type", "Cost"], [[x["item_id"], x["title"], x["brand"], x["product_type"], m(x["cost"])] for x in pr["over_line"][:50]])]
    lines += ["", "Lines used:"]
    for name, part in (("Asset groups", parts.get("asset_groups")), ("Searches", st), ("Products", pr)):
        if part and name == "Asset groups":
            for s in part["by_campaign"]:
                lines.append("- Asset groups in %s: %s, %s." % (s["campaign"] or "the report", m(s["line"]["value"]), s["line"]["source"]))
        elif part:
            lines.append("- %s: %s, %s." % (name, m(part["line"]["value"]), part["line"]["source"]))
    lines += ["", "Next: write OUTPUT/actions.json with your actions and the searches you judged irrelevant (see SKILL.md), then run",
              "  python3 scripts/add_actions.py --out OUTPUT --actions OUTPUT/actions.json",
              "For a launch or clone plan: python3 scripts/launch_checklist.py --review OUTPUT/pmax-review.json --out OUTPUT [--source \"CAMPAIGN\"]"]
    return "\n".join(lines)
