"""Load Performance Max and Shopping exports and compute every number the review uses.

Imported by audit.py. Nothing here prints or writes files. Standard library only.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics  # noqa: E402

STRENGTH_RANK = {"excellent": 4, "good": 3, "average": 2, "poor": 1}
STOPWORDS = set("a an and are as at be by for from how i in is it me my near of on or the to what when where with you your".split())
CHANNEL_NAMES = {
    "google search": "Google Search", "search": "Google Search", "google search network": "Google Search",
    "search network": "Google Search", "search partners": "Search partners", "search partner": "Search partners",
    "google display network": "Google Display Network", "display": "Google Display Network", "display network": "Google Display Network",
    "youtube": "YouTube", "youtube videos": "YouTube", "discover": "Discover", "gmail": "Gmail", "maps": "Maps",
    "google maps": "Maps", "cross-network": "Cross-network", "cross network": "Cross-network", "mixed": "Cross-network",
}
SEARCH_CHANNELS = ("Google Search", "Search partners")
BLANK = ("", "(not set)", "not set", "--")
# Rounding tolerance when two reports' costs are compared: below one currency unit is rounding.
ROUNDING = 1.0
DIMENSIONS = [("brand", "Brand"), ("product_type", "Product type (1st level)"), ("category", "Category (1st level)")] + \
             [("custom_label_%d" % n, "Custom label %d" % n) for n in range(5)]

_COMMON = {"status": "status", "interactions": "interactions", "asset group": "asset_group", "asset group name": "asset_group"}
_PRODUCT = dict(_COMMON, **{
    "item id": "item_id", "product item id": "item_id", "id": "item_id", "offer id": "item_id", "product id": "item_id",
    "title": "title", "product title": "title", "brand": "brand", "product brand": "brand",
    "product type (1st level)": "product_type", "product type": "product_type", "product type l1": "product_type",
    "category (1st level)": "category", "product category (1st level)": "category", "google product category (1st level)": "category",
    "product status": "product_status", "item status": "product_status", "status": "product_status",
    "issues": "issues", "item issues": "issues", "product issues": "issues",
    "price": "price", "product price": "price", "your price": "price",
    "benchmark": "benchmark", "benchmark price": "benchmark", "price benchmark": "benchmark", "benchmark product price": "benchmark",
    "price gap": "price_gap", "price benchmark difference": "price_gap", "benchmark price difference": "price_gap",
    "benchmark product price difference": "price_gap", "price difference": "price_gap", "gtin": "gtin",
})
_PRODUCT.update({"custom label %d" % n: "custom_label_%d" % n for n in range(5)})
REPORTS = {
    "campaigns": {"name": "campaign report", "aliases": dict(_COMMON, **{"target roas": "target_roas", "target cpa": "target_cpa"}),
                  "needs": ["campaign", "cost", "conversions"]},
    "asset_groups": {"name": "asset group report", "aliases": dict(_COMMON, **{"asset group status": "asset_group_status", "ad strength": "ad_strength"}),
                     "needs": ["asset_group", "cost", "conversions"]},
    "channels": {"name": "channel performance report", "aliases": dict(_COMMON, **{
        "channel": "channel", "channels": "channel", "ad network type": "channel", "network": "channel", "network (with search partners)": "channel",
        "ads using product data": "product_data", "ads using video": "video"}), "needs": ["channel", "cost", "conversions"]},
    "search_terms": {"name": "search terms report", "aliases": dict(_COMMON, **{"search category": "search_category"}), "needs": ["conversions"]},
    "products": {"name": "products report", "aliases": _PRODUCT, "needs": ["cost", "conversions"]},
    "prices": {"name": "price benchmark report", "aliases": dict(_PRODUCT, **{"product": "title"}), "needs": []},
}
LABELS = {"asset_group": "Asset group", "ad_strength": "Ad strength", "channel": "Channel", "item_id": "Item ID", "title": "Title",
          "price": "Your price", "benchmark": "Benchmark", "price_gap": "Price gap", "search_term": "Search term", "cost": "Cost",
          "conversions": "Conversions", "conv_value": "Conv. value", "campaign": "Campaign", "impressions": "Impr."}
NUMERIC = ("interactions", "price", "benchmark", "target_cpa")
PERCENT = ("price_gap", "target_roas")
DATE_RANGE = re.compile(r"([A-Za-z]{3,9}\.? \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})\s*[-\u2013\u2014]\s*([A-Za-z]{3,9}\.? \d{1,2}, \d{4}|\d{4}-\d{2}-\d{2})")
UNLOCK = {
    "campaigns": "the campaign report (Campaigns, filter Campaign type to Performance Max, Download, CSV) with Campaign status, Campaign, "
                 "Campaign type, Status, Bid strategy type, Budget, Cost, Conversions and Conv. value",
    "asset_groups": "the asset group report (Campaigns, Asset groups, Download, CSV) with Asset group, Campaign, Asset group status, "
                    "Ad strength, Cost, Conversions and Conv. value",
    "ad_strength": "the asset group report with the Ad strength column added",
    "channels": "the channel performance report (open the Performance Max campaign, Insights and reports, Channel performance, "
                "then Download on the channel table) with Channel, Status, Cost, Conversions and Conv. value",
    "search_terms": "the search terms report (Insights and reports, Search terms, Download, CSV) with Search term, Campaign, "
                    "Campaign type, Cost, Conversions and Conv. value",
    "search_cost": "the search terms report with the Cost column. Older Performance Max search term insights have no cost",
    "brand": "your brand terms, passed as --brand",
    "products": "the products report (Campaigns, Products, Download, CSV) with Item ID, Title, Brand, Product type (1st level), "
                "Custom label 0 to 4, Impr., Clicks, Cost, Conversions and Conv. value",
    "conv_value": "the Conv. value column in the products report",
    "target_roas": "the target ROAS, passed as --target-roas",
    "prices": "the price benchmarks from Merchant Center (Analytics, Pricing, Price benchmarks, Download) with Product ID, Title, "
              "Your price, Benchmark and Price gap, or Benchmark columns in the products report",
}


def plain_exit(text):
    raise SystemExit(text)


def date_range(title_rows):
    for row in title_rows:
        found = DATE_RANGE.search(row.replace('"', ""))
        if found:
            start, end = dates.parse_day(found.group(1)), dates.parse_day(found.group(2))
            if start and end:
                return start, end
    return None


def load(kind, path):
    spec = REPORTS[kind]
    if not os.path.isfile(path):
        plain_exit("I can't find the file %s for the %s." % (path, spec["name"]))
    try:
        meta, rows = io.read_report(path, extra_aliases=spec["aliases"], extra_numeric=NUMERIC, extra_percent=PERCENT)
    except ValueError as err:
        plain_exit("The %s: %s" % (spec["name"], err))
    except Exception:  # a damaged or unknown file must still give a plain message
        plain_exit("I can't read the %s at %s. Download it again from Google Ads as CSV." % (spec["name"], path))
    io.require(meta, spec["needs"], spec["name"], labels=LABELS)
    for row in rows:
        if row.get("clicks") is None and row.get("interactions") is not None:
            row["clicks"] = row["interactions"]
    span = date_range(meta["title_rows"])
    meta["date_range"] = [span[0].isoformat(), span[1].isoformat()] if span else None
    meta["days"] = (span[1] - span[0]).days + 1 if span else None
    meta["path"] = os.path.basename(path)
    meta["odd_totals"] = [label for label in meta["totals"] if not re.match(r"^total(:|$|,)", label.strip().lower())]
    return meta, rows


def blank(value):
    return str(value or "").strip().lower() in BLANK


def file_total(meta, prefer):
    """The file's own total row: the first whose label holds one of prefer, '' means any."""
    for want in prefer:
        for label, values in meta["totals"].items():
            if want in label.lower() and values.get("cost") is not None:
                return label.split(",")[0].strip(), values
    return None, None


def reconcile(meta, rows_cost, prefer):
    label, values = file_total(meta, prefer)
    if not label:
        return None
    return {"label": label, "file_cost": values["cost"], "rows_cost": rows_cost, "difference": round(rows_cost - values["cost"], 2)}


def rates(item):
    item["cpa"] = metrics.div(item.get("cost"), item.get("conversions"))
    item["roas"] = metrics.div(item.get("conv_value"), item.get("cost")) if item.get("conv_value") is not None else None
    return item


def sum_fields(rows, fields=("impressions", "clicks", "cost", "conversions", "conv_value")):
    return {f: metrics.total(rows, f) for f in fields}


def tokens_match(term, phrases):
    words = metrics.tokens(term)
    for phrase in phrases:
        span = len(phrase)
        if span and any(words[i:i + span] == phrase for i in range(len(words) - span + 1)):
            return True
    return False


def campaign_state(row):
    status = (row.get("campaign_status") or "").lower()
    serving = (row.get("status") or "").lower()
    if "removed" in status or (not status and "removed" in serving):
        return "Removed"
    if "paused" in status or (not status and "paused" in serving):
        return "Paused"
    return "Enabled"


def group_state(row):
    status = (row.get("asset_group_status") or "").lower()
    serving = (row.get("status") or "").lower()
    if "removed" in status or "removed" in serving:
        return "Removed"
    if "paused" in status or "paused" in serving:
        return "Paused"
    return "Enabled"


def strength_of(text):
    value = (text or "").strip().lower()
    for name in STRENGTH_RANK:
        if value.startswith(name):
            return name.capitalize()
    return "Not rated"


def channel_name(text):
    value = (text or "").strip()
    return CHANNEL_NAMES.get(value.lower(), value or "Not named")


def product_key(row):
    ident = (row.get("item_id") or "").strip().lower()
    online = re.match(r"^(online|local):[^:]*:[^:]*:(.+)$", ident)
    if online:
        return online.group(2)
    if ident:
        return ident
    title = (row.get("title") or "").strip().lower()
    return "title:" + title if title else ""


def line_for(target_cpa, own, own_source):
    """The amount a row must spend, with no conversions, before it is called out."""
    if target_cpa:
        return {"value": target_cpa, "source": "the target cost per conversion you gave"}
    if own:
        return {"value": own, "source": own_source}
    return {"value": None, "source": "none: there are no conversions to set it from, so every row with cost and no conversions is listed"}


def word_set(texts):
    """Words that name what the account sells or builds. A negative made only of these is never suggested."""
    words = set()
    for text in texts:
        words.update(w for w in metrics.tokens(text) if w not in STOPWORDS and len(w) > 1)
    return words


def goal_of(item):
    """What a campaign is judged by: conv. value / cost when its conversions carry value or it bids for value."""
    strategy = (item.get("bid_strategy") or "").lower()
    if item.get("conv_value") or "value" in strategy or "roas" in strategy:
        return "conv. value / cost"
    return "cost / conv."


def concentration(values):
    ranked = sorted((v for v in values if v > 0), reverse=True)
    whole = sum(ranked)
    result = {"count": len(values), "with_cost": len(ranked), "top10_share": metrics.div(sum(ranked[:10]), whole), "for_half": None, "for_80": None}
    running = 0.0
    for number, value in enumerate(ranked, start=1):
        running += value
        if result["for_half"] is None and running >= whole * 0.5:
            result["for_half"] = number
        if result["for_80"] is None and running >= whole * 0.8:
            result["for_80"] = number
    return result


# --------------------------------------------------------------------------- campaigns

def campaigns_part(meta, rows, chosen):
    has_type = "campaign_type" in meta["columns"]
    pmax = [r for r in rows if r.get("campaign") and (not has_type or "performance max" in (r.get("campaign_type") or "").lower())]
    dropped = sum(1 for r in rows if r.get("campaign")) - len(pmax)
    if chosen:
        pmax = [r for r in pmax if r["campaign"] in chosen]
    merged = {}
    for row in pmax:
        item = merged.setdefault(row["campaign"], {
            "campaign": row["campaign"], "state": campaign_state(row), "campaign_status": row.get("campaign_status", ""),
            "status": row.get("status", ""), "bid_strategy": row.get("bid_strategy", ""), "budget": row.get("budget"),
            "target_cpa": row.get("target_cpa"), "target_roas": row.get("target_roas"), "days_with_data": set(),
            "impressions": 0.0, "clicks": 0.0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0})
        for field in ("impressions", "clicks", "cost", "conversions", "conv_value"):
            item[field] += row.get(field) or 0
        if row.get("day"):
            item["days_with_data"].add(row["day"])
    total = sum_fields(list(merged.values()))
    items = []
    for item in sorted(merged.values(), key=lambda c: -c["cost"]):
        days = len(item.pop("days_with_data")) or meta["days"]
        item["days"] = days
        item["avg_daily_cost"] = metrics.div(item["cost"], days)
        item["share_of_cost"] = metrics.div(item["cost"], total["cost"])
        item["learning"] = "learning" in (item["status"] or "").lower()
        item["goal"] = goal_of(item)
        items.append(rates(item))
    prefer = ["performance max", "filtered", "account"] if dropped == 0 else ["performance max"]
    search_campaigns, seen = [], set()
    for row in rows:
        kind = (row.get("campaign_type") or "").lower()
        if has_type and row.get("campaign") and "search" in kind and "performance max" not in kind and row["campaign"] not in seen:
            seen.add(row["campaign"])
            search_campaigns.append({"campaign": row["campaign"], "state": campaign_state(row)})
    return {"campaigns": items, "total": rates(dict(total)), "other_types_left_out": dropped, "type_column": has_type,
            "has_value": "conv_value" in meta["columns"] and total["conv_value"] > 0,
            "value_mixed": len({c["goal"] for c in items if c["cost"]}) > 1,
            "search_campaigns": search_campaigns,
            "reconcile": None if chosen else reconcile(meta, total["cost"], prefer),
            "by_state": {s: sum(1 for c in items if c["state"] == s) for s in ("Enabled", "Paused", "Removed")},
            "enabled_no_cost": [c["campaign"] for c in items if c["state"] == "Enabled" and c["cost"] == 0],
            "paused_with_cost": [c["campaign"] for c in items if c["state"] != "Enabled" and c["cost"] > 0],
            "learning": [c["campaign"] for c in items if c["learning"]]}


# --------------------------------------------------------------------------- asset groups

def asset_groups_part(meta, rows, chosen, target_cpa):
    if chosen and "campaign" in meta["columns"]:
        rows = [r for r in rows if r.get("campaign") in chosen]
    merged = {}
    for row in rows:
        name = (row.get("asset_group") or "").strip()
        if not name:
            continue
        item = merged.setdefault((row.get("campaign", ""), name), {
            "asset_group": name, "campaign": row.get("campaign", ""), "state": group_state(row),
            "status": row.get("status", "") or row.get("asset_group_status", ""), "ad_strength": strength_of(row.get("ad_strength")),
            "impressions": 0.0, "clicks": 0.0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0})
        for field in ("impressions", "clicks", "cost", "conversions", "conv_value"):
            item[field] += row.get(field) or 0
    groups = [rates(g) for g in merged.values()]
    total = rates(sum_fields(groups))
    by_campaign = {}
    for g in groups:
        slot = by_campaign.setdefault(g["campaign"], {"campaign": g["campaign"], "groups": 0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0, "top_share": 0.0})
        slot["groups"] += 1
        for field in ("cost", "conversions", "conv_value"):
            slot[field] += g[field]
    for slot in by_campaign.values():
        rates(slot)
        slot["goal"] = goal_of(slot)
        slot["line"] = line_for(target_cpa, slot["cpa"] or total["cpa"],
                                "the cost per conversion of this campaign's asset groups" if slot["cpa"] else "the cost per conversion of all asset groups in the report")
    for g in groups:
        slot = by_campaign[g["campaign"]]
        g["share_of_cost"] = metrics.div(g["cost"], total["cost"])
        g["share_of_campaign_cost"] = metrics.div(g["cost"], slot["cost"])
        g["goal"] = slot["goal"]
        slot["top_share"] = max(slot["top_share"], g["share_of_campaign_cost"] or 0)
        line = slot["line"]["value"]
        g["no_conv_over_line"] = g["cost"] > 0 and g["conversions"] == 0 and (line is None or g["cost"] >= line)
    groups.sort(key=lambda g: -g["cost"])
    has_strength = "ad_strength" in meta["columns"]
    strength = {}
    for g in groups:
        slot = strength.setdefault(g["ad_strength"], {"ad_strength": g["ad_strength"], "groups": 0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0})
        slot["groups"] += 1
        for field in ("cost", "conversions", "conv_value"):
            slot[field] += g[field]
    for slot in strength.values():
        slot["share_of_cost"] = metrics.div(slot["cost"], total["cost"])
        rates(slot)
    below = [g for g in groups if g["ad_strength"] in ("Average", "Poor")]
    return {"groups": groups, "total": total, "by_campaign": sorted(by_campaign.values(), key=lambda s: -s["cost"]),
            "has_strength": has_strength, "has_campaign": "campaign" in meta["columns"],
            "value_mixed": len({s["goal"] for s in by_campaign.values() if s["cost"]}) > 1,
            "by_strength": sorted(strength.values(), key=lambda s: -STRENGTH_RANK.get(s["ad_strength"].lower(), 0)),
            "below_good": {"groups": len(below), "cost": metrics.total(below, "cost"), "share_of_cost": metrics.div(metrics.total(below, "cost"), total["cost"]),
                           "conversions": metrics.total(below, "conversions"), "names": [g["asset_group"] for g in below]} if has_strength else None,
            "no_conv_over_line": [g for g in groups if g["no_conv_over_line"]],
            "enabled_no_cost": [g["asset_group"] for g in groups if g["state"] == "Enabled" and g["cost"] == 0],
            "paused_with_cost": [g["asset_group"] for g in groups if g["state"] != "Enabled" and g["cost"] > 0],
            "reconcile": None if chosen else reconcile(meta, total["cost"], ["asset group", "filtered", "performance max", "account", ""])}


# --------------------------------------------------------------------------- channels

def channels_part(meta, rows, chosen):
    if chosen and "campaign" in meta["columns"]:
        rows = [r for r in rows if r.get("campaign") in chosen]
    merged, per_campaign, formats = {}, {}, {}
    for row in rows:
        name = channel_name(row.get("channel"))
        if not (row.get("channel") or "").strip():
            continue
        targets = [merged.setdefault(name, {"channel": name, "statuses": []})]
        if row.get("campaign"):
            targets.append(per_campaign.setdefault((row["campaign"], name), {"campaign": row["campaign"], "channel": name, "statuses": []}))
        for key in ("product_data", "video"):
            flag = (row.get(key) or "").strip()
            if flag:
                targets.append(formats.setdefault((name, key, flag), {"channel": name, "segment": "Ads using product data" if key == "product_data" else "Ads using video", "value": flag, "statuses": []}))
        for item in targets:
            for field in ("impressions", "clicks", "cost", "conversions", "conv_value"):
                item[field] = item.get(field, 0.0) + (row.get(field) or 0)
            status = (row.get("status") or "").strip()
            if status and status not in item["statuses"]:
                item["statuses"].append(status)
    channels = list(merged.values())
    total = rates(sum_fields(channels))
    shares(channels, total)
    channels.sort(key=lambda c: -c["cost"])
    search = [c for c in channels if c["channel"] in SEARCH_CHANNELS]
    for item in formats.values():
        rates(item)
    by_campaign = {}
    for item in per_campaign.values():
        by_campaign.setdefault(item["campaign"], []).append(item)
    for items in by_campaign.values():
        shares(items, rates(sum_fields(items)))
    # Each campaign is judged against its own goal: conv. value when its conversions carry value, else conversions.
    judged = [i for items in by_campaign.values() for i in items] if by_campaign else channels
    return {"channels": channels, "total": total, "has_value": "conv_value" in meta["columns"],
            "search_cost": metrics.total(search, "cost"), "search_share_of_cost": metrics.div(metrics.total(search, "cost"), total["cost"]),
            "per_campaign": sorted(per_campaign.values(), key=lambda c: (c["campaign"], -c["cost"])),
            "formats": sorted(formats.values(), key=lambda f: (f["channel"], f["segment"], f["value"])),
            "flags": sorted([i for i in judged if i["flag"]], key=lambda i: -i["cost"]),
            "no_cost": [c["channel"] for c in channels if not c["cost"]],
            "with_issues": sorted([i for i in judged if i["issues"]], key=lambda i: -i["cost"]),
            "has_campaign": bool(by_campaign),
            "value_mixed": len({i["basis"] for i in judged if i["cost"]}) > 1,
            "reconcile": None if chosen else reconcile(meta, total["cost"], [""])}


def shares(items, whole):
    """Shares of one campaign's (or the report's) total, and whether a channel takes more cost than it returns."""
    basis = "conv. value" if whole.get("conv_value") else "conversions"
    for c in items:
        rates(c)
        c["share_of_cost"] = metrics.div(c["cost"], whole["cost"])
        c["share_of_conversions"] = metrics.div(c["conversions"], whole["conversions"])
        c["share_of_value"] = metrics.div(c["conv_value"], whole["conv_value"])
        c["basis"] = basis
        c["share_of_basis"] = c["share_of_value"] if basis == "conv. value" else c["share_of_conversions"]
        c["whole_cpa"], c["whole_roas"] = whole["cpa"], whole["roas"]
        c["issues"] = [s for s in c["statuses"] if s.lower() != "eligible"]
        c["flag"] = bool(c["cost"] and (whole["conversions"] or whole.get("conv_value")) and (c["share_of_cost"] or 0) > (c["share_of_basis"] or 0))


# --------------------------------------------------------------------------- search terms

def search_terms_part(meta, rows, chosen, brand_phrases, target_cpa, protected=frozenset()):
    has_type = "campaign_type" in meta["columns"]
    field = "search_term" if "search_term" in meta["columns"] else ("search_category" if "search_category" in meta["columns"] else None)
    if not field:
        plain_exit("I can't find the Search term column in the search terms report. Download the report again with that column.")
    listed = [r for r in rows if (r.get(field) or "").strip()]
    pmax = [r for r in listed if not has_type or "performance max" in (r.get("campaign_type") or "").lower()]
    dropped = len(listed) - len(pmax)
    if chosen and "campaign" in meta["columns"]:
        pmax = [r for r in pmax if r.get("campaign") in chosen]
    has_cost = "cost" in meta["columns"]
    merged = {}
    for row in pmax:
        term = row[field].strip()
        item = merged.setdefault((term.lower(), row.get("campaign", "")), {
            "search_term": term, "campaign": row.get("campaign", ""), "impressions": 0.0, "clicks": 0.0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0})
        for name in ("impressions", "clicks", "cost", "conversions", "conv_value"):
            item[name] += row.get(name) or 0
    terms = [rates(t) for t in merged.values()]
    for t in terms:
        t["brand"] = bool(brand_phrases) and tokens_match(t["search_term"], brand_phrases)
    total = rates(sum_fields(terms))
    brand = [t for t in terms if t["brand"]]
    non_brand = [t for t in terms if not t["brand"]]
    brand_sum, non_brand_sum = rates(sum_fields(brand)), rates(sum_fields(non_brand))
    for part in (brand_sum, non_brand_sum):
        part["searches"] = len(brand) if part is brand_sum else len(non_brand)
        part["share_of_cost"] = metrics.div(part["cost"], total["cost"])
        part["share_of_conversions"] = metrics.div(part["conversions"], total["conversions"])
        part["share_of_value"] = metrics.div(part["conv_value"], total["conv_value"])
    if brand_phrases and non_brand_sum["cpa"]:
        line = line_for(target_cpa, non_brand_sum["cpa"], "the cost per conversion of the non brand Performance Max searches in this report")
    else:
        line = line_for(target_cpa, total["cpa"], "the cost per conversion of the Performance Max searches in this report")
    no_conv = [t for t in terms if t["cost"] > 0 and t["conversions"] == 0 and not t["brand"]]
    no_conv.sort(key=lambda t: -t["cost"])
    over = [t for t in no_conv if line["value"] is None or t["cost"] >= line["value"]]
    for t in terms:
        t["over_line"] = False
        t["candidate_word"] = ""
    for t in over:
        t["over_line"] = True
    grams = {}
    for t in terms:
        seen = set()
        for size in (1, 2, 3):
            for gram in metrics.ngrams(t["search_term"], size):
                if (size == 1 and (gram in STOPWORDS or len(gram) < 2)) or gram in seen:
                    continue
                seen.add(gram)
                slot = grams.setdefault(gram, {"phrase": gram, "words": size, "searches": 0, "clicks": 0.0, "cost": 0.0, "conversions": 0.0})
                slot["searches"] += 1
                for name in ("clicks", "cost", "conversions"):
                    slot[name] += t[name]
    half_line = (line["value"] or 0) * 0.5
    found = sorted([g for g in grams.values() if g["conversions"] == 0 and g["searches"] >= 2 and g["cost"] > 0 and g["cost"] >= half_line],
                   key=lambda g: (-g["cost"], g["words"]))
    for g in found:
        g["protected"] = bool(protected) and all(w in protected for w in g["phrase"].split())
    waste_words = [g for g in found if not g["protected"]][:60]
    held_back = [g for g in found if g["protected"]][:30]
    candidates = [g["phrase"].split() for g in waste_words]
    for t in no_conv:
        words = metrics.tokens(t["search_term"])
        t["candidate_word"] = next((" ".join(c) for c in candidates if any(words[i:i + len(c)] == c for i in range(len(words) - len(c) + 1))), "")
    below = [t for t in no_conv if not t["over_line"]]
    brand_in_search = {}
    if has_type and brand_phrases:
        for row in listed:
            kind = (row.get("campaign_type") or "").lower()
            if "search" not in kind or "performance max" in kind:
                continue
            keyword = (row.get("keyword") or "").strip()
            hit_keyword = bool(keyword) and tokens_match(keyword, brand_phrases)
            hit_term = tokens_match(row[field], brand_phrases)
            if not (hit_keyword or hit_term):
                continue
            slot = brand_in_search.setdefault(row.get("campaign", ""), {"campaign": row.get("campaign", ""), "brand_searches": 0, "cost": 0.0, "keywords": []})
            slot["brand_searches"] += 1 if hit_term else 0
            slot["cost"] += row.get("cost") or 0
            label = keyword + (" (%s)" % row["match_type"] if (row.get("match_type") or "").strip() else "")
            if hit_keyword and label not in slot["keywords"]:
                slot["keywords"].append(label)
    terms.sort(key=lambda t: -t["cost"])
    prefer = ["performance max"] if has_type else ["account", ""]
    rec = None if chosen or not has_cost else reconcile(meta, total["cost"], prefer)
    return {"terms": terms, "total": total, "field": field, "has_cost": has_cost, "has_value": "conv_value" in meta["columns"],
            "type_column": has_type, "other_types_left_out": dropped, "brand_terms": [" ".join(p) for p in brand_phrases],
            "brand": brand_sum if brand_phrases else None, "non_brand": non_brand_sum if brand_phrases else None,
            "line": line, "no_conv": {"searches": len(no_conv), "cost": metrics.total(no_conv, "cost"), "share_of_cost": metrics.div(metrics.total(no_conv, "cost"), total["cost"])},
            "over_line": over, "over_line_cost": metrics.total(over, "cost"), "waste_words": waste_words, "held_back_words": held_back,
            "no_conv_terms": no_conv, "below_line": {"searches": len(below), "cost": metrics.total(below, "cost")},
            "below_line_with_word": [t for t in below if t["candidate_word"]],
            "brand_in_search": sorted(brand_in_search.values(), key=lambda s: -s["cost"]), "protected_checked": bool(protected),
            "reconcile": rec, "not_listed_cost": (rec["file_cost"] - rec["rows_cost"]) if rec and rec["file_cost"] > rec["rows_cost"] else 0.0}


# --------------------------------------------------------------------------- products

def products_part(meta, rows, chosen, target_cpa, target_roas):
    if chosen and "campaign" in meta["columns"]:
        rows = [r for r in rows if r.get("campaign") in chosen]
    items, skipped = {}, 0
    text_fields = ["item_id", "title", "brand", "product_type", "category", "product_status", "issues", "gtin"] + ["custom_label_%d" % n for n in range(5)]
    for row in rows:
        key = product_key(row)
        if not key:
            skipped += 1
            continue
        item = items.setdefault(key, dict({f: "" for f in text_fields}, key=key, campaigns=[], price=None, benchmark=None, price_gap=None,
                                          impressions=0.0, clicks=0.0, cost=0.0, conversions=0.0, conv_value=0.0))
        for f in text_fields:
            if blank(item[f]) and not blank(row.get(f)):
                item[f] = row.get(f).strip()
        for f in ("price", "benchmark", "price_gap"):
            if item[f] is None and row.get(f) is not None:
                item[f] = row[f]
        for f in ("impressions", "clicks", "cost", "conversions", "conv_value"):
            item[f] += row.get(f) or 0
        if row.get("campaign") and row["campaign"] not in item["campaigns"]:
            item["campaigns"].append(row["campaign"])
    products = [rates(p) for p in items.values()]
    total = rates(sum_fields(products))
    line = line_for(target_cpa, total["cpa"], "the cost per conversion of all products in this report")
    has_value = "conv_value" in meta["columns"]
    for p in products:
        p["share_of_cost"] = metrics.div(p["cost"], total["cost"])
        p["no_conv"] = p["cost"] > 0 and p["conversions"] == 0
        p["over_line"] = p["no_conv"] and (line["value"] is None or p["cost"] >= line["value"])
        p["below_target_roas"] = bool(target_roas and has_value and p["cost"] > 0 and (line["value"] is None or p["cost"] >= line["value"])
                                      and (p["roas"] or 0) < target_roas)
    products.sort(key=lambda p: -p["cost"])
    no_conv = [p for p in products if p["no_conv"]]
    over = [p for p in products if p["over_line"]]
    dims = [(f, label) for f, label in DIMENSIONS if f in meta["columns"]]
    groups = {}
    for f, label in dims:
        slots = {}
        for p in products:
            name = p[f] if not blank(p[f]) else "(blank)"
            s = slots.setdefault(name, {"dimension": label, "value": name, "products": 0, "impressions": 0.0, "clicks": 0.0, "cost": 0.0,
                                         "conversions": 0.0, "conv_value": 0.0, "no_conv_products": 0, "no_conv_cost": 0.0})
            s["products"] += 1
            for m in ("impressions", "clicks", "cost", "conversions", "conv_value"):
                s[m] += p[m]
            if p["no_conv"]:
                s["no_conv_products"] += 1
                s["no_conv_cost"] += p["cost"]
        for s in slots.values():
            rates(s)
            s["share_of_cost"] = metrics.div(s["cost"], total["cost"])
            s["share_of_value"] = metrics.div(s["conv_value"], total["conv_value"])
            s["share_of_no_conv_cost"] = metrics.div(s["no_conv_cost"], metrics.total(no_conv, "cost"))
        groups[f] = sorted(slots.values(), key=lambda s: -s["cost"])
    gaps = []
    for f, label in [("title", "Title"), ("brand", "Brand"), ("product_type", "Product type (1st level)"), ("category", "Category (1st level)")] + \
            [("custom_label_%d" % n, "Custom label %d" % n) for n in range(5)]:
        if f in meta["columns"]:
            missing = [p for p in products if blank(p[f])]
            gaps.append({"attribute": label, "products": len(missing), "share_of_products": metrics.div(len(missing), len(products)),
                         "cost": metrics.total(missing, "cost"), "share_of_cost": metrics.div(metrics.total(missing, "cost"), total["cost"])})
    status = {}
    if "product_status" in meta["columns"] or "issues" in meta["columns"]:
        for p in products:
            name = p["product_status"] or ("Has issues" if p["issues"] else "(blank)")
            s = status.setdefault(name, {"status": name, "products": 0, "cost": 0.0, "with_issues": 0})
            s["products"] += 1
            s["cost"] += p["cost"]
            s["with_issues"] += 1 if p["issues"] else 0
    return {"products": products, "total": total, "line": line, "has_value": has_value, "has_impressions": "impressions" in meta["columns"],
            "skipped_rows": skipped, "dimensions": [label for _, label in dims], "groups": groups, "gaps": gaps,
            "status": sorted(status.values(), key=lambda s: -s["cost"]),
            "no_conv": {"products": len(no_conv), "cost": metrics.total(no_conv, "cost"), "share_of_cost": metrics.div(metrics.total(no_conv, "cost"), total["cost"])},
            "over_line": over, "over_line_cost": metrics.total(over, "cost"),
            "no_impressions": sum(1 for p in products if p["impressions"] == 0) if "impressions" in meta["columns"] else None,
            "concentration": concentration([p["cost"] for p in products]),
            "value_concentration": concentration([p["conv_value"] for p in products]) if has_value else None,
            "target_roas": target_roas,
            "below_target_roas": [p for p in products if p["below_target_roas"]],
            "campaigns": sorted({c for p in products for c in p["campaigns"]}),
            "reconcile": None if chosen else reconcile(meta, total["cost"], ["filtered", "account", "product", ""])}


# --------------------------------------------------------------------------- prices

def position(price, benchmark, gap):
    """Return (gap as a fraction, position) or (None, None)."""
    if price is not None and benchmark:
        if abs(price - benchmark) < 0.005:
            return 0.0, "At benchmark"
        value = price / benchmark - 1
    elif gap is not None:
        value = gap / 100.0
    else:
        return None, None
    if value > 0:
        return value, "Above benchmark"
    return value, "Below benchmark" if value < 0 else "At benchmark"


def prices_part(products, price_rows, price_meta):
    """Price position per product, from the products report's own columns or a Merchant Center file."""
    source = {}
    if price_rows is not None:
        has_id = "item_id" in price_meta["columns"]
        if not has_id and "title" not in price_meta["columns"]:
            plain_exit("I can't find a Product ID or Title column in the price benchmark report. Download it again with those columns.")
        if not (("price" in price_meta["columns"] and "benchmark" in price_meta["columns"]) or "price_gap" in price_meta["columns"]):
            plain_exit("I can't find Your price and Benchmark, or Price gap, in the price benchmark report. Download it again with those columns.")
        for row in price_rows:
            key = product_key(row) if has_id else product_key({"title": row.get("title")})
            if key and key not in source:
                source[key] = {"price": row.get("price"), "benchmark": row.get("benchmark"), "price_gap": row.get("price_gap"),
                               "title": row.get("title", ""), "item_id": row.get("item_id", ""), "clicks": row.get("clicks")}
    rows, matched, unmatched_source = [], 0, 0
    if products is not None:
        by_title = {}
        if source and not any(not k.startswith("title:") for k in source):
            by_title = source
        used = set()
        for p in products:
            info = None
            if p["benchmark"] is not None or p["price_gap"] is not None:
                info = {"price": p["price"], "benchmark": p["benchmark"], "price_gap": p["price_gap"]}
            elif by_title:
                info = by_title.get("title:" + (p["title"] or "").strip().lower())
                if info:
                    used.add("title:" + (p["title"] or "").strip().lower())
            elif p["key"] in source:
                info = source[p["key"]]
                used.add(p["key"])
            gap, where = position(info["price"], info["benchmark"], info["price_gap"]) if info else (None, None)
            if where:
                matched += 1
            rows.append({"key": p["key"], "item_id": p["item_id"], "title": p["title"], "brand": p["brand"], "product_type": p["product_type"],
                         "price": info["price"] if info else None, "benchmark": info["benchmark"] if info else None, "gap": gap, "position": where or "No benchmark",
                         "impressions": p["impressions"], "clicks": p["clicks"], "cost": p["cost"], "conversions": p["conversions"],
                         "conv_value": p["conv_value"], "no_conv": p["no_conv"]})
        unmatched_source = len(set(source) - used)
    else:
        for key, info in source.items():
            gap, where = position(info["price"], info["benchmark"], info["price_gap"])
            rows.append({"key": key, "item_id": info["item_id"], "title": info["title"], "brand": "", "product_type": "", "price": info["price"],
                         "benchmark": info["benchmark"], "gap": gap, "position": where or "No benchmark", "impressions": 0.0,
                         "clicks": info["clicks"] or 0.0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0, "no_conv": False})
            matched += 1 if where else 0
    if not matched:
        return None
    whole_cost = metrics.total([r for r in rows if r["position"] != "No benchmark"], "cost")
    groups = []
    for name in ("Above benchmark", "At benchmark", "Below benchmark", "No benchmark"):
        part = [r for r in rows if r["position"] == name]
        if not part:
            continue
        g = dict(sum_fields(part), position=name, products=len(part))
        g["share_of_priced_cost"] = metrics.div(g["cost"], whole_cost) if name != "No benchmark" else None
        g["conv_rate"] = metrics.div(g["conversions"], g["clicks"])
        groups.append(rates(g))
    above = [r for r in rows if r["position"] == "Above benchmark"]
    above.sort(key=lambda r: (-r["cost"], -(r["gap"] or 0)))
    above_no_conv = [r for r in above if r["no_conv"]]
    gaps = sorted(r["gap"] for r in above)
    return {"rows": sorted(rows, key=lambda r: -r["cost"]), "groups": groups, "matched": matched, "with_performance": products is not None,
            "unmatched_in_price_file": unmatched_source, "source": "a separate price benchmark file" if price_rows is not None else "the products report's own columns",
            "above": {"products": len(above), "cost": metrics.total(above, "cost"), "share_of_priced_cost": metrics.div(metrics.total(above, "cost"), whole_cost),
                      "median_gap": gaps[len(gaps) // 2] if gaps else None},
            "above_no_conv": {"products": len(above_no_conv), "cost": metrics.total(above_no_conv, "cost")},
            "top_above": above[:25]}
