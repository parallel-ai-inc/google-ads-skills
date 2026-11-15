"""Read the exports the account audit accepts. A helper for audit.py, not a step.

Every report is optional. A report that is given is read, checked for the
columns it must have, and turned into clean rows: one per campaign, ad group,
keyword, ad, search or conversion action. Paused and removed rows are kept and
marked, so no check judges them as if they were serving.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics  # noqa: E402

# Lowercase header -> short name, for columns the shared reader does not know.
EXTRA_ALIASES = {
    "interactions": "clicks",
    "ad group status": "ad_group_status", "ad group state": "ad_group_status",
    "keyword status": "keyword_status", "keyword state": "keyword_status", "search keyword status": "keyword_status",
    "ad status": "ad_status", "ad state": "ad_status",
    "status": "status", "status reasons": "status_reasons",
    "approval status": "approval_status", "policy details": "policy_details",
    "networks": "networks", "budget name": "budget_name", "budget type": "budget_type",
    "network (with search partners)": "network",
    "ad group type": "ad_group_type",
    "quality score": "quality_score", "exp. ctr": "exp_ctr", "expected ctr": "exp_ctr",
    "ad relevance": "ad_relevance", "landing page exp.": "landing_page_exp", "landing page experience": "landing_page_exp",
    "final url": "final_url",
    "ad type": "ad_type", "ad strength": "ad_strength", "ad": "ad", "ad name": "ad", "headline 1": "headline_1",
    "conversion action": "conversion_action", "conversion name": "conversion_action", "conversion action name": "conversion_action",
    "action optimization": "action_optimization", "conversion action optimization": "action_optimization",
    'include in "conversions"': "include_in_conversions", "include in 'conversions'": "include_in_conversions",
    "include in “conversions”": "include_in_conversions", "include in conversions": "include_in_conversions",
    "conversion source": "source",
    "category": "conv_category", "conversion category": "conv_category", "goal": "conv_category",
    "conversion goal": "conv_category", "goal category": "conv_category",
    "count": "count_setting", "counting": "count_setting",
    "all conv.": "all_conv", "all conversions": "all_conv",
    "all conv. value": "all_conv_value", "all conversions value": "all_conv_value",
    "tracking status": "tracking_status",
}
EXTRA_NUMERIC = ("quality_score", "all_conv", "all_conv_value")

# Short name -> the header as Google Ads shows it, for messages.
LABELS = {
    "campaign": "Campaign", "ad_group": "Ad group", "keyword": "Keyword", "search_term": "Search term",
    "cost": "Cost", "clicks": "Clicks", "impressions": "Impr.", "conversions": "Conversions", "conv_value": "Conv. value",
    "campaign_status": "Campaign status", "ad_group_status": "Ad group status", "keyword_status": "Keyword status",
    "ad_status": "Ad status", "status": "Status", "campaign_type": "Campaign type", "bid_strategy": "Bid strategy type",
    "budget_name": "Budget name", "networks": "Networks", "network": "Network (with search partners)",
    "lost_is_budget": "Search lost IS (budget)", "lost_is_rank": "Search lost IS (rank)", "impr_share": "Search impr. share",
    "match_type": "Match type", "quality_score": "Quality Score", "exp_ctr": "Exp. CTR", "ad_relevance": "Ad relevance",
    "landing_page_exp": "Landing page exp.", "ad_type": "Ad type", "ad_strength": "Ad strength",
    "conversion_action": "Conversion action", "action_optimization": "Action optimization", "source": "Conversion source",
    "conv_category": "Category", "count_setting": "Count", "all_conv": "All conv.", "added_excluded": "Added/Excluded",
}

# The reports the audit reads: how to name each one, where it is in Google Ads,
# the columns it cannot work without, and columns that show the wrong file was passed.
REPORTS = {
    "campaigns": {"title": "campaign report", "flag": "--campaigns", "path": "Campaigns menu, Campaigns, Campaigns",
                  "must": ["campaign", "cost"], "never": ["ad_group", "keyword", "search_term", "network"],
                  "totals": ["filtered", "account"]},
    "ad_groups": {"title": "ad group report", "flag": "--ad-groups", "path": "Campaigns menu, Campaigns, Ad groups",
                  "must": ["campaign", "ad_group", "cost"], "never": ["keyword", "search_term"], "totals": ["filtered", "account"]},
    "keywords": {"title": "keyword report", "flag": "--keywords",
                 "path": "Campaigns menu, Audiences, keywords, and content, Search keywords",
                 "must": ["keyword", "campaign", "ad_group", "cost"], "never": ["search_term"],
                 "totals": ["all but removed", "keywords in your account", "filtered", "account"]},
    "ads": {"title": "ads report", "flag": "--ads", "path": "Campaigns menu, Campaigns, Ads",
            "must": ["campaign", "ad_group", "cost"], "never": ["keyword", "search_term"], "totals": ["filtered", "account"]},
    "search_terms": {"title": "search terms report", "flag": "--search-terms", "path": "Campaigns menu, Insights and reports, Search terms",
                     "must": ["search_term", "campaign", "cost", "conversions"], "never": [], "totals": ["search terms", "filtered", "account"]},
    "conversions": {"title": "conversions summary", "flag": "--conversions", "path": "Goals menu, Conversions, All conversions",
                    "must": ["conversion_action"], "never": ["campaign"], "totals": ["account"]},
    "networks": {"title": "campaign report segmented by network", "flag": "--networks",
                 "path": "Campaigns menu, Campaigns, Campaigns, then the segment icon, Network (with search partners)",
                 "must": ["campaign", "network", "cost"], "never": ["ad_group", "keyword", "search_term"], "totals": ["filtered", "account"]},
}
ORDER = ("campaigns", "ad_groups", "keywords", "ads", "search_terms", "conversions", "networks")
SUMS = ("impressions", "clicks", "cost", "conversions", "conv_value")
# Statuses of a row that say its campaign or ad group is not running.
PARENT_STOPS = ("campaign paused", "campaign removed", "campaign ended", "campaign pending", "ad group paused", "ad group removed")
LEAD_CATEGORIES = ("submit lead form", "contact", "book appointment", "sign-up", "sign up", "request quote",
                   "phone call lead", "phone call leads")
STOPWORDS = set("a an and are as at be by for from how i in is it me my near of on or the to what when where with you your".split())


def label(name):
    return LABELS.get(name, name)


def word_list(names):
    names = [label(n) for n in names]
    return names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]


def state(text):
    """Enabled, paused or removed, from a status cell."""
    cell = (text or "").strip().lower()
    if not cell:
        return "unknown"
    if "removed" in cell or "deleted" in cell:
        return "removed"
    if "paused" in cell:
        return "paused"
    if cell.startswith("enabled") or cell.startswith("eligible") or cell in ("active", "approved"):
        return "enabled"
    return "other"


def parent_stopped(text):
    cell = (text or "").lower()
    return any(stop in cell for stop in PARENT_STOPS)


def strategy_kind(text):
    """How a Bid strategy type bids: on conversions, on value, or on neither."""
    cell = " ".join((text or "").lower().split())
    if not cell:
        return {"known": False, "conversion": False, "value": False, "maximize": False, "ecpc": False}
    value = "target roas" in cell or "conversion value" in cell
    conversion = value or "target cpa" in cell or "maximize conversions" in cell or "max conversions" in cell
    maximize = cell.startswith("maximize conversion") or cell.startswith("max conversion")
    return {"known": True, "conversion": conversion, "value": value, "maximize": maximize, "ecpc": "enhanced cpc" in cell or cell == "ecpc"}


def campaign_kind(text):
    cell = (text or "").lower()
    for word, kind in (("performance max", "pmax"), ("search", "search"), ("display", "display"), ("shopping", "shopping"),
                       ("video", "video"), ("demand gen", "demand gen"), ("app", "app")):
        if word in cell:
            return kind
    return "other" if cell else ""


def keyword_parts(text, match_cell):
    """'[24 hour plumber]', 'Exact match' -> ('24 hour plumber', 'exact')."""
    raw = (text or "").strip()
    by_symbol = "exact" if raw.startswith("[") and raw.endswith("]") else "phrase" if raw.startswith('"') and raw.endswith('"') else "broad"
    clean = " ".join(raw.strip('[]"').replace("+", " ").split()).lower()
    cell = (match_cell or "").lower()
    match = "exact" if "exact" in cell else "phrase" if "phrase" in cell else "broad" if "broad" in cell else by_symbol
    return clean, match


def is_brand(text, brand_phrases):
    words = metrics.tokens(text)
    for phrase in brand_phrases:
        span = len(phrase)
        if span and any(words[i:i + span] == phrase for i in range(len(words) - span + 1)):
            return True
    return False


def period_of(meta):
    """The date range row above the header, as text and as two dates."""
    for title in meta["title_rows"][1:] + meta["title_rows"][:1]:
        for dash in (" - ", " – ", " to "):
            if dash in title:
                left, _, right = title.partition(dash)
                start, end = dates.parse_day(left.strip()), dates.parse_day(right.strip())
                if start and end and end >= start:
                    return {"text": title, "start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days + 1}
    return None


def reconcile(meta, rows_cost, prefer, row_count=0):
    """Compare the rows with the file's own total row.

    Google shows each row's cost rounded to the cent and works the total out
    before rounding, so each row can move the sum by up to half a cent.
    """
    totals = [(name, values["cost"]) for name, values in meta["totals"].items()
              if values.get("cost") is not None and not any(ch.isdigit() for ch in name.partition(",")[2])]
    if not totals:
        return None
    close = [t for t in totals if abs(t[1] - rows_cost) <= max(0.05, 0.005 * (row_count + 1))]

    def rank(total):
        low = total[0].lower()
        return next((i for i, word in enumerate(prefer) if word in low), len(prefer))
    pool = close or totals
    name, value = sorted(pool, key=rank)[0]
    return {"label": name, "file_total": value, "rows": rows_cost, "difference": round(rows_cost - value, 2), "matches": bool(close)}


def read(key, path):
    """Read one export and stop with a plain message when it is not the right file."""
    spec = REPORTS[key]
    if not os.path.isfile(path):
        raise SystemExit("I can't find the file %s. Check the path to the %s." % (path, spec["title"]))
    try:
        meta, rows = io.read_report(path, extra_aliases=EXTRA_ALIASES, extra_numeric=EXTRA_NUMERIC)
    except ValueError as problem:
        raise SystemExit("The %s could not be read (%s). %s" % (spec["title"], os.path.basename(path), problem))
    except Exception:  # a damaged or wrong kind of file
        raise SystemExit("The %s could not be read (%s). Download it again from Google Ads as .csv. In Google Ads: %s."
                         % (spec["title"], os.path.basename(path), spec["path"]))
    wrong = [n for n in spec["never"] if n in meta["columns"]]
    if wrong:
        raise SystemExit("The file passed as the %s (%s) has the column %s, so it looks like a different report. "
                         "In Google Ads the %s is under: %s." % (spec["title"], os.path.basename(path), word_list(wrong[:1]), spec["title"], spec["path"]))
    io.require(meta, spec["must"], spec["title"], labels=LABELS)
    return meta, rows


def _sum_into(slot, row):
    for field in SUMS:
        slot[field] += row.get(field) or 0


def _first(slot, row, fields):
    for field in fields:
        if not slot.get(field) and row.get(field) not in (None, ""):
            slot[field] = row[field]


def _blank(**extra):
    slot = {field: 0.0 for field in SUMS}
    slot.update(extra)
    return slot


class Account:
    """Everything read from the files, joined by campaign and ad group name."""

    def __init__(self, brand_phrases=(), brand_campaigns=(), target_cpa=None):
        self.brand_phrases = list(brand_phrases)
        self.brand_campaigns = list(brand_campaigns)
        self.target_cpa = target_cpa
        self.reports = {}
        self.meta = {}
        self.campaigns, self.ad_groups, self.keywords, self.ads, self.terms, self.actions = [], [], [], [], [], []
        self.networks = {}
        self.campaign_by_name, self.ad_group_by_key = {}, {}
        self.notes = []

    # ----- loading

    def add(self, key, path):
        meta, rows = read(key, path)
        self.meta[key] = meta
        getattr(self, "_build_" + key)(rows, meta)
        cost = metrics.total(rows, "cost")
        entry = {
            "report": REPORTS[key]["title"], "file": os.path.basename(path), "title_rows": meta["title_rows"],
            "period": period_of(meta), "rows": len(rows),
            "cost": cost if "cost" in meta["columns"] else None,
            "conversions": metrics.total(rows, "conversions") if "conversions" in meta["columns"] else None,
            "clicks": metrics.total(rows, "clicks") if "clicks" in meta["columns"] else None,
            "reconcile": reconcile(meta, cost, REPORTS[key]["totals"], len(rows)) if "cost" in meta["columns"] else None,
            "columns_found": sorted(label(c) for c in meta["columns"]),
            "columns_not_used": meta["unknown_headers"],
        }
        self.reports[key] = entry

    def has(self, key, *columns):
        return key in self.meta and all(c in self.meta[key]["columns"] for c in columns)

    def _build_campaigns(self, rows, meta):
        for row in rows:
            name = (row.get("campaign") or "").strip()
            if not name:
                continue
            slot = self.campaign_by_name.get(name)
            if slot is None:
                slot = _blank(campaign=name, rows=0, budget=None, impr_share=None, lost_is_budget=None, lost_is_rank=None)
                self.campaign_by_name[name] = slot
                self.campaigns.append(slot)
            slot["rows"] += 1
            _sum_into(slot, row)
            _first(slot, row, ("campaign_status", "status", "status_reasons", "campaign_type", "bid_strategy", "budget_name",
                               "budget_type", "networks", "currency", "budget"))
            for field in ("impr_share", "lost_is_budget", "lost_is_rank"):
                # A share cannot be added up across the rows of a segmented report.
                slot[field] = row.get(field) if slot["rows"] == 1 else None
        self.segmented_campaigns = any(c["rows"] > 1 for c in self.campaigns)
        if self.segmented_campaigns:
            self.notes.append("The campaign report has more than one row per campaign, so it is segmented. Cost, clicks and "
                              "conversions were added up. Impression share columns cannot be added up and were not read.")
        has_own = "campaign_status" in meta["columns"]
        if not has_own:
            self.notes.append("The campaign report has no Campaign status column. A campaign was treated as enabled unless its "
                              "Status says paused or removed.")
        for slot in self.campaigns:
            if has_own:
                slot["state"] = state(slot.get("campaign_status"))
            else:
                serving = state(slot.get("status"))
                slot["state"] = serving if serving in ("paused", "removed") else "enabled"
            # An enabled campaign whose end date has passed does not serve either.
            serving_text = (slot.get("status") or "").lower()
            slot["live"] = slot["state"] == "enabled" and not any(word in serving_text for word in ("ended", "removed", "paused"))
            slot["kind"] = campaign_kind(slot.get("campaign_type"))
            slot["strategy"] = strategy_kind(slot.get("bid_strategy"))
            slot["cpa"] = metrics.div(slot["cost"], slot["conversions"])

    def _build_ad_groups(self, rows, meta):
        for row in rows:
            key = ((row.get("campaign") or "").strip(), (row.get("ad_group") or "").strip())
            if not key[0] or not key[1]:
                continue
            slot = self.ad_group_by_key.get(key)
            if slot is None:
                slot = _blank(campaign=key[0], ad_group=key[1])
                self.ad_group_by_key[key] = slot
                self.ad_groups.append(slot)
            _sum_into(slot, row)
            _first(slot, row, ("ad_group_status", "campaign_status", "status", "ad_group_type"))
        if "ad_group_status" not in meta["columns"]:
            self.notes.append("The ad group report has no Ad group status column, so every ad group was treated as enabled.")

    def _build_keywords(self, rows, meta):
        merged, self.negative_rows = {}, 0
        for row in rows:
            text = (row.get("keyword") or "").strip()
            if not text:
                continue
            if text.startswith("-"):
                self.negative_rows += 1
                continue
            clean, match = keyword_parts(text, row.get("match_type"))
            key = ((row.get("campaign") or "").strip(), (row.get("ad_group") or "").strip(), clean, match)
            slot = merged.get(key)
            if slot is None:
                slot = _blank(campaign=key[0], ad_group=key[1], keyword=text, text=clean, match=match)
                merged[key] = slot
                self.keywords.append(slot)
            _sum_into(slot, row)
            _first(slot, row, ("keyword_status", "campaign_status", "ad_group_status", "status", "status_reasons", "quality_score",
                               "exp_ctr", "ad_relevance", "landing_page_exp", "final_url"))
        if "keyword_status" not in meta["columns"]:
            self.notes.append("The keyword report has no Keyword status column, so every keyword was treated as enabled.")
        if self.negative_rows:
            self.notes.append("%d rows in the keyword report are negative keywords. They were left out." % self.negative_rows)

    def _build_ads(self, rows, meta):
        for number, row in enumerate(rows, start=1):
            campaign, ad_group = (row.get("campaign") or "").strip(), (row.get("ad_group") or "").strip()
            if not campaign or not ad_group:
                continue
            slot = _blank(campaign=campaign, ad_group=ad_group)
            _sum_into(slot, row)
            _first(slot, row, ("ad_status", "campaign_status", "ad_group_status", "status", "status_reasons", "approval_status",
                               "policy_details", "ad_type", "ad_strength", "final_url"))
            slot["name"] = (row.get("ad") or row.get("headline_1") or row.get("final_url") or "Ad in row %d" % number).strip()
            kind = (slot.get("ad_type") or "").lower()
            slot["kind"] = "rsa" if "responsive search" in kind else "dsa" if "dynamic" in kind else "eta" if "expanded text" in kind else "other"
            slot["strength"] = (slot.get("ad_strength") or "").strip().lower()
            review = " ".join(str(slot.get(f) or "") for f in ("status", "approval_status", "policy_details")).lower()
            slot["disapproved"] = "disapproved" in review
            slot["limited"] = "limited" in review and not slot["disapproved"]
            self.ads.append(slot)
        if "ad_status" not in meta["columns"] and "status" not in meta["columns"]:
            self.notes.append("The ads report has no Ad status or Status column, so every ad was treated as enabled.")

    def _build_search_terms(self, rows, meta):
        merged = {}
        for row in rows:
            term = (row.get("search_term") or "").strip()
            if not term:
                continue
            key = (term.lower(), (row.get("campaign") or "").strip(), (row.get("ad_group") or "").strip())
            slot = merged.get(key)
            if slot is None:
                slot = _blank(search_term=term, campaign=key[1], ad_group=key[2], excluded=False)
                merged[key] = slot
                self.terms.append(slot)
            _sum_into(slot, row)
            _first(slot, row, ("keyword",))
            if "exclud" in (row.get("added_excluded") or "").lower():
                slot["excluded"] = True
        for slot in self.terms:
            slot["brand"] = is_brand(slot["search_term"], self.brand_phrases)

    def _build_conversions(self, rows, meta):
        for row in rows:
            name = (row.get("conversion_action") or "").strip()
            if not name:
                continue
            setting = (row.get("action_optimization") or "").strip().lower()
            included = (row.get("include_in_conversions") or "").strip().lower()
            role = ("primary" if setting.startswith("primary") else "secondary" if setting.startswith("secondary")
                    else "primary" if included in ("yes", "true") else "secondary" if included in ("no", "false") else "unknown")
            count = row.get("all_conv") if "all_conv" in meta["columns"] else row.get("conversions")
            status = (row.get("tracking_status") or row.get("status") or "").strip()
            self.actions.append({
                "name": name, "role": role, "source": (row.get("source") or "").strip(),
                "category": (row.get("conv_category") or "").strip(), "count_setting": (row.get("count_setting") or "").strip(),
                "status": status, "recorded": count or 0.0,
                "value": (row.get("all_conv_value") if "all_conv_value" in meta["columns"] else row.get("conv_value")) or 0.0,
                "removed": state(status) == "removed" or "hidden" in status.lower(),
            })

    def _build_networks(self, rows, meta):
        for row in rows:
            name = (row.get("campaign") or "").strip()
            cell = (row.get("network") or "").lower()
            if not name or not cell:
                continue
            part = "partners" if "partner" in cell else "display" if "display" in cell else "search" if "search" in cell else "other"
            slot = self.networks.setdefault(name, {}).setdefault(part, _blank())
            _sum_into(slot, row)

    # ----- after every file is read

    def finish(self):
        """Mark which rows are running: enabled, inside an enabled ad group and an enabled campaign."""
        known_campaigns = bool(self.campaigns) and self.has("campaigns", "campaign_status")

        def campaign_runs(row):
            own = row.get("campaign_status")
            if own not in (None, "") and state(own) != "enabled":
                return False
            if known_campaigns and row["campaign"] in self.campaign_by_name:
                return self.campaign_by_name[row["campaign"]]["live"]
            return not parent_stopped(row.get("status"))

        for group in self.ad_groups:
            own = state(group.get("ad_group_status")) if self.has("ad_groups", "ad_group_status") else "enabled"
            group["live"] = own == "enabled" and campaign_runs(group) and not parent_stopped(group.get("status"))
            group["dynamic"] = "dynamic" in (group.get("ad_group_type") or "").lower()
            group["cpa"] = metrics.div(group["cost"], group["conversions"])

        def ad_group_runs(row):
            own = row.get("ad_group_status")
            if own not in (None, "") and state(own) != "enabled":
                return False
            group = self.ad_group_by_key.get((row["campaign"], row["ad_group"]))
            if group is not None:
                return group["live"]
            return campaign_runs(row) and not parent_stopped(row.get("status"))

        for keyword in self.keywords:
            own = state(keyword.get("keyword_status")) if self.has("keywords", "keyword_status") else "enabled"
            keyword["enabled"] = own == "enabled"
            keyword["live"] = keyword["enabled"] and ad_group_runs(keyword) and not parent_stopped(keyword.get("status"))
            keyword["brand"] = is_brand(keyword["text"], self.brand_phrases) or keyword["campaign"] in self.brand_campaigns
        for ad in self.ads:
            if self.has("ads", "ad_status"):
                own = state(ad.get("ad_status"))
            else:
                own = "paused" if state(ad.get("status")) in ("paused", "removed") and not parent_stopped(ad.get("status")) else "enabled"
            ad["enabled"] = own == "enabled"
            ad["parent_live"] = ad_group_runs(ad) and not parent_stopped(ad.get("status"))
            ad["active"] = ad["enabled"] and not ad["disapproved"]
        for term in self.terms:
            term["brand_campaign"] = term["campaign"] in self.brand_campaigns

    def bid_strategy(self, campaign):
        slot = self.campaign_by_name.get(campaign)
        return slot["strategy"] if slot and self.has("campaigns", "bid_strategy") else None

    def line(self, rows, name, noun):
        """How much a row with no conversions must have spent before it is judged.

        The target cost per conversion when one was given. Otherwise the cost
        per conversion of the non brand rows in the same report, so that cheap
        brand conversions do not pull the line down.
        """
        if self.target_cpa:
            return {"value": self.target_cpa, "source": "the target cost per conversion you gave", "brand_left_out": True}
        branded = bool(self.brand_phrases or self.brand_campaigns)
        plain = [r for r in rows if not r.get("brand") and r.get("campaign") not in self.brand_campaigns] if branded else list(rows)
        plain_cpa = metrics.div(metrics.total(plain, "cost"), metrics.total(plain, "conversions"))
        if plain_cpa and branded:
            return {"value": plain_cpa, "brand_left_out": True,
                    "source": "the cost per conversion of the non brand %s in the %s, judged in this audit" % (noun, name)}
        if plain_cpa:
            return {"value": plain_cpa, "brand_left_out": False,
                    "source": "the cost per conversion of the %s in the %s, judged in this audit. No brand terms or brand campaign "
                              "were given, so any brand rows are inside this number and pull it down" % (noun, name)}
        ranked = sorted(r["cost"] for r in plain)
        return {"value": ranked[int(len(ranked) * 0.9)] if ranked else 0.0, "brand_left_out": branded,
                "source": "the cost at the top tenth of %s by cost, because they have no conversions in the %s" % (noun, name)}
