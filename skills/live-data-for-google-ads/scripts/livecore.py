"""Shared parts of the live data skill.

The known fields, the named reports, the words Google Ads shows for API
values, and the reader for the search tool's results. Standard library only.
Nothing in this file connects to anything or calls any tool.
"""
import datetime as dt
import difflib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH_TOOL = "search_search"
LIST_TOOL = "customers_list_accessible_customers"
METADATA_TOOL = "metadata_get_resource_metadata"
# The server's write tools. No script in this skill calls them, and the read only
# tools_config.yaml turns them off. They are named here only so they can be refused.
WRITE_TOOLS = ("create_asset", "upload_video_asset", "manage_labels", "manage_label_associations")
EMPTY = " --"
FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$")
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August",
          "September", "October", "November", "December"]

# Written by hand from Google's field reference on 2026-11-13. To be re-read
# against the source before release. See references/live-access.md.
HAND = {
    "attributed": {
        "search_term_view": ["ad_group", "campaign", "customer"],
        "ad_group_ad": ["ad_group", "campaign", "customer"],
    },
    "fields": {"ad_group_ad": ["ad_group_ad.ad_strength"]},
    "sources": {
        "search_term_view": "https://developers.google.com/google-ads/api/fields/v22/search_term_view",
        "ad_group_ad": "https://developers.google.com/google-ads/api/fields/v22/ad_group_ad",
    },
}


class Refusal(SystemExit):
    """A plain message for the person, never a stack trace."""


# ---------------------------------------------------------------- known fields

def _fields_in(entry):
    """'metrics.clicks (when ...)' -> ['metrics.clicks']. A placeholder such as
    'SEGMENT_FIELD_FOR_TIME_GRANULARITY (segments.date|segments.week)' gives the
    fields inside it. Wildcards give nothing here."""
    text = entry.strip()
    placeholder = re.match(r"^[A-Z_]+\s*\((.*)\)$", text)
    if placeholder:
        return [p.strip() for p in placeholder.group(1).split("|") if FIELD_RE.match(p.strip())]
    text = re.sub(r"\s*\(.*\)$", "", text)
    return [p.strip() for p in text.split(",") if FIELD_RE.match(p.strip())]


class Catalogue:
    """Every field our product reads, by the resource it was read from."""

    def __init__(self, path=None):
        path = path or os.path.join(HERE, "known_fields.json")
        with open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
        self.by_resource, self.wild, self.known = {}, {}, set()
        for key, entries in raw.items():
            resources = [r.strip() for r in re.sub(r"\s*\(.*\)$", "", key).split("|") if r.strip()]
            for resource in resources:
                self.by_resource.setdefault(resource, set())
                self.wild.setdefault(resource, set())
            for entry in entries:
                if "*" in entry:
                    for resource in resources:
                        self.wild[resource].add(entry.split("*")[0])
                    continue
                for field in _fields_in(entry):
                    self.known.add(field)
                    for resource in resources:
                        self.by_resource[resource].add(field)
        self.hand_fields = {r: set(f) for r, f in HAND["fields"].items()}
        # The same library, as Markdown, also lists the fields each resource is filtered and dated by.
        self.filters = {}
        library = os.path.join(os.path.dirname(HERE), "references", "queries-by-resource.md")
        if os.path.isfile(library):
            resources = []
            with open(library, encoding="utf-8") as handle:
                for line in handle:
                    if line.startswith("## "):
                        resources = [r.strip() for r in re.sub(r"\s*\(.*\)$", "", line[3:].strip()).split("|")]
                    elif line.startswith("**Filters used:**") or line.startswith("**Date field:**"):
                        for name in re.findall(r"`([a-z][a-z0-9_.]*)", line):
                            if FIELD_RE.match(name):
                                for resource in resources:
                                    self.filters.setdefault(resource, set()).add(name)

    def resources(self):
        return sorted(self.by_resource)

    def is_known(self, field, resource=None):
        return field in self.known or field in self.hand_fields.get(resource, set())

    def classify(self, resource, field, where="select"):
        """seen, attributed, hand, unproven or unknown, with a note."""
        prefix = field.split(".")[0]
        filtered = where != "select" and field in self.filters.get(resource, set())
        if not self.is_known(field, resource) and not filtered:
            return "unknown", "not in the known fields"
        if field in self.by_resource.get(resource, set()):
            return "seen", "seen with %s in working queries" % resource
        if filtered:
            return "seen", "used to filter %s in working queries" % resource
        if field in self.hand_fields.get(resource, set()):
            return "hand", "added by hand from Google's field reference for %s" % resource
        if prefix in ("metrics", "segments"):
            if any(field.startswith(w) for w in self.wild.get(resource, ())):
                return "seen", "%s accepts any %s field in working queries" % (resource, prefix)
            return "unproven", "a known %s field not yet seen with %s" % (prefix, resource)
        if prefix in HAND["attributed"].get(resource, ()):
            return "hand", "Google lists %s as attributed to %s" % (prefix, resource)
        inferred = {f.split(".")[0] for f in self.by_resource.get(resource, ())} - {resource, "metrics", "segments"}
        if prefix in inferred:
            return "attributed", "other %s fields are read with %s in working queries" % (prefix, resource)
        return "unproven", "a known field not yet seen with %s" % resource

    def nearest(self, field, resource=None, count=5):
        pool = sorted(self.known | self.hand_fields.get(resource, set()))
        starts = [f for f in pool if f.startswith(field)][:count]
        close = difflib.get_close_matches(field, pool, n=count, cutoff=0.55)
        seen, out = set(), []
        for name in starts + close:
            if name not in seen:
                seen.add(name)
                out.append(name)
        return out[:count]

    def nearest_resources(self, resource):
        return difflib.get_close_matches(resource, self.resources(), n=5, cutoff=0.5)


# ---------------------------------------------------------------- the words Google Ads shows

ENUMS = {
    "segments.search_term_match_type": {"BROAD": "Broad match", "EXACT": "Exact match", "PHRASE": "Phrase match",
                                        "NEAR_EXACT": "Exact match (close variant)", "NEAR_PHRASE": "Phrase match (close variant)"},
    "ad_group_criterion.keyword.match_type": {"BROAD": "Broad match", "EXACT": "Exact match", "PHRASE": "Phrase match"},
    "search_term_view.status": {"ADDED": "Added", "EXCLUDED": "Excluded", "ADDED_EXCLUDED": "Added/Excluded", "NONE": "None"},
    "campaign.advertising_channel_type": {"SEARCH": "Search", "DISPLAY": "Display", "SHOPPING": "Shopping", "VIDEO": "Video",
                                          "MULTI_CHANNEL": "App", "PERFORMANCE_MAX": "Performance Max", "DEMAND_GEN": "Demand Gen",
                                          "LOCAL": "Local", "SMART": "Smart", "HOTEL": "Hotel", "LOCAL_SERVICES": "Local services",
                                          "TRAVEL": "Travel"},
    "campaign.bidding_strategy_type": {"MANUAL_CPC": "Manual CPC", "MANUAL_CPM": "Manual CPM", "MANUAL_CPV": "Manual CPV",
                                       "MANUAL_CPA": "Manual CPA", "MAXIMIZE_CONVERSIONS": "Maximize Conversions",
                                       "MAXIMIZE_CONVERSION_VALUE": "Maximize Conversion Value", "TARGET_CPA": "Target CPA",
                                       "TARGET_ROAS": "Target ROAS", "TARGET_SPEND": "Maximize Clicks", "TARGET_CPC": "Target CPC",
                                       "TARGET_IMPRESSION_SHARE": "Target Impression Share", "TARGET_CPM": "Target CPM",
                                       "TARGET_CPV": "Target CPV", "ENHANCED_CPC": "Enhanced CPC", "COMMISSION": "Commission",
                                       "PERCENT_CPC": "Percent CPC", "FIXED_CPM": "Fixed CPM"},
    "campaign_budget.period": {"DAILY": "Daily", "FIXED_DAILY": "Daily", "CUSTOM_PERIOD": "Custom"},
    "ad_group.type": {"SEARCH_STANDARD": "Standard", "DISPLAY_STANDARD": "Standard", "SEARCH_DYNAMIC_ADS": "Dynamic"},
    "ad_group_ad.policy_summary.approval_status": {"APPROVED_LIMITED": "Approved (limited)"},
    "conversion_action.type": {"WEBPAGE": "Website", "WEBPAGE_CODELESS": "Website", "AD_CALL": "Calls from ads",
                               "GOOGLE_ANALYTICS_4_CUSTOM": "Google Analytics (GA4)",
                               "GOOGLE_ANALYTICS_4_PURCHASE": "Google Analytics (GA4)",
                               "UPLOAD_CLICKS": "Import from clicks", "UPLOAD_CALLS": "Import from calls"},
    "conversion_action.category": {"SIGNUP": "Sign-up", "DEFAULT": "Other", "SUBSCRIBE_PAID": "Subscribe"},
    "conversion_action.counting_type": {"ONE_PER_CLICK": "One", "MANY_PER_CLICK": "Every"},
    "conversion_action.attribution_model_settings.attribution_model": {
        "GOOGLE_SEARCH_ATTRIBUTION_DATA_DRIVEN": "Data-driven", "GOOGLE_ADS_LAST_CLICK": "Last click", "EXTERNAL": "External"},
    "change_event.client_type": {"GOOGLE_ADS_WEB_CLIENT": "Google Ads web interface", "GOOGLE_ADS_API": "Google Ads API",
                                 "GOOGLE_ADS_SCRIPTS": "Google Ads scripts", "GOOGLE_ADS_EDITOR": "Google Ads Editor",
                                 "GOOGLE_ADS_AUTOMATED_RULE": "Automated rule", "GOOGLE_ADS_RECOMMENDATIONS": "Recommendations",
                                 "GOOGLE_ADS_BULK_UPLOAD": "Bulk upload", "GOOGLE_ADS_MOBILE_APP": "Google Ads mobile app"},
    "change_event.change_resource_type": {"AD_GROUP_AD": "Ad", "AD_GROUP_BID_MODIFIER": "Ad group bid adjustment",
                                          "CUSTOMER_ASSET": "Account asset"},
    "change_event.resource_change_operation": {"CREATE": "added", "UPDATE": "changed", "REMOVE": "removed"},
}
NOT_SET = {"UNSPECIFIED", "UNKNOWN"}


def enum_name(value):
    """'ENABLED', 'CampaignStatus.ENABLED' or '<CampaignStatus.ENABLED: 2>' -> 'ENABLED'.
    A number is returned as it is: its meaning is not known here."""
    if value is None:
        return None
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).strip()
    match = re.match(r"^<?(?:[A-Za-z_]+\.)?([A-Z][A-Z0-9_]*)(?::\s*\d+>)?$", text)
    return match.group(1) if match else text


def enum_words(field, value, unmapped=None):
    name = enum_name(value)
    if name in (None, "") or name in NOT_SET:
        return EMPTY
    words = ENUMS.get(field, {}).get(name)
    if words:
        return words
    if re.match(r"^[A-Z][A-Z0-9_]*$", name):
        return name.replace("_", " ").capitalize()
    if unmapped is not None:
        unmapped.add("%s = %s" % (field, name))
    return name


# ---------------------------------------------------------------- the named reports

def col(header, field, kind, **extra):
    item = {"header": header, "field": field, "kind": kind}
    item.update(extra)
    return item


IMPR = col("Impr.", "metrics.impressions", "int", sum=True)
CLICKS = col("Clicks", "metrics.clicks", "int", sum=True)
CTR = col("CTR", "metrics.ctr", "percent")
CPC = col("Avg. CPC", "metrics.average_cpc", "micros")
COST = col("Cost", "metrics.cost_micros", "micros", sum=True)
CONV = col("Conversions", "metrics.conversions", "decimal", sum=True)
CPA = col("Cost / conv.", "metrics.cost_per_conversion", "micros")
VALUE = col("Conv. value", "metrics.conversions_value", "decimal", sum=True)
ALL_CONV = col("All conv.", "metrics.all_conversions", "decimal", sum=True)
ALL_VALUE = col("All conv. value", "metrics.all_conversions_value", "decimal", sum=True)
CAMPAIGN = col("Campaign", "campaign.name", "text")
AD_GROUP = col("Ad group", "ad_group.name", "text")
CAMPAIGN_STATUS = col("Campaign status", "campaign.status", "enum")
CAMPAIGN_TYPE = col("Campaign type", "campaign.advertising_channel_type", "enum")
DAY = col("Day", "segments.date", "text")
NOT_REMOVED = ("campaign.status != 'REMOVED'",)

REPORTS = {
    "search-terms": {
        "title": "Search terms report", "file": "search-terms-report.csv", "resource": "search_term_view", "days": 30,
        "total": "Total: Search terms",
        "what": "Every search that triggered an ad, with its campaign, ad group and results.",
        "columns": [col("Search term", "search_term_view.search_term", "text"),
                    col("Match type", "segments.search_term_match_type", "enum"),
                    col("Added/Excluded", "search_term_view.status", "enum"),
                    CAMPAIGN, AD_GROUP, CAMPAIGN_TYPE, IMPR, CLICKS, CTR, CPC, COST, CONV, CPA, VALUE],
        "conditions": ["{date}"], "orderings": ["metrics.cost_micros DESC"], "limit": 10000,
        "needs": ["search_term_view.search_term", "metrics.cost_micros"],
        "readers": ["search terms skill: python3 scripts/measure.py FILE --work WORK --brand \"...\"",
                    "account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --search-terms FILE"],
        "gaps": ["The Keyword column is left out, so no search is split or dropped by keyword.",
                 "Google leaves low volume searches out of search results, as it does in the interface."],
    },
    "keywords": {
        "title": "Search keyword report", "file": "keyword-report.csv", "resource": "keyword_view", "days": 30,
        "total": "Total: All but removed keywords",
        "what": "Every keyword that is not removed, with Quality Score and its three parts.",
        "columns": [col("Keyword status", "ad_group_criterion.status", "enum"),
                    col("Keyword", "ad_group_criterion.keyword.text", "keyword",
                        inputs=["ad_group_criterion.keyword.match_type"]),
                    col("Match type", "ad_group_criterion.keyword.match_type", "enum"),
                    CAMPAIGN, AD_GROUP,
                    col("Status", "campaign.status", "parents", inputs=["ad_group.status"]),
                    IMPR, CLICKS, CTR, CPC, COST, CONV, CPA, VALUE,
                    col("Quality Score", "ad_group_criterion.quality_info.quality_score", "int"),
                    col("Exp. CTR", "ad_group_criterion.quality_info.search_predicted_ctr", "enum"),
                    col("Ad relevance", "ad_group_criterion.quality_info.creative_quality_score", "enum"),
                    col("Landing page exp.", "ad_group_criterion.quality_info.post_click_quality_score", "enum")],
        "conditions": ["{date}", "ad_group_criterion.status != 'REMOVED'", "ad_group_criterion.negative = FALSE",
                       "ad_group.status != 'REMOVED'"] + list(NOT_REMOVED),
        "orderings": ["metrics.cost_micros DESC"], "limit": 10000,
        "needs": ["ad_group_criterion.keyword.text", "metrics.cost_micros"],
        "readers": ["account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --keywords FILE",
                    "search terms skill, to protect the account's own keywords: python3 scripts/check_negatives.py --work WORK --keywords FILE"],
        "gaps": ["Status shows only a paused or removed campaign or ad group. Google's other serving reasons are not in this file."],
    },
    "campaigns": {
        "title": "Campaign report", "file": "campaign-report.csv", "resource": "campaign", "days": 30,
        "total": "Total: Filtered campaigns",
        "what": "Every campaign that is not removed, with budget, bid strategy and Search impression share.",
        "columns": [CAMPAIGN_STATUS, CAMPAIGN,
                    col("Budget", "campaign_budget.amount_micros", "micros"),
                    col("Budget name", "campaign_budget.name", "text"),
                    col("Budget type", "campaign_budget.period", "enum"),
                    CAMPAIGN_TYPE, col("Bid strategy type", "campaign.bidding_strategy_type", "enum"),
                    IMPR, CLICKS, CTR, CPC, COST, CONV, CPA, VALUE,
                    col("Search impr. share", "metrics.search_impression_share", "share"),
                    col("Search lost IS (rank)", "metrics.search_rank_lost_impression_share", "lost"),
                    col("Search lost IS (budget)", "metrics.search_budget_lost_impression_share", "lost")],
        "conditions": ["{date}"] + list(NOT_REMOVED), "orderings": ["metrics.cost_micros DESC"], "limit": 10000,
        "needs": ["campaign.name", "metrics.cost_micros"],
        "readers": ["account audit: python3 scripts/audit.py --work WORK --campaigns FILE",
                    "bidding and scaling, and client reporting, where they ask for a campaign report"],
        "gaps": ["Status and Status reasons (the serving status, such as Limited by budget) are not in this file. Checks that need them show as not run.",
                 "Budget is the budget today."],
    },
    "campaigns-by-day": {
        "title": "Campaign report", "file": "campaigns-by-day.csv", "resource": "campaign", "days": 60,
        "total": "Total: Filtered campaigns",
        "what": "The campaign report segmented by Day, for pacing and trends.",
        "columns": [DAY, CAMPAIGN_STATUS, CAMPAIGN,
                    col("Budget", "campaign_budget.amount_micros", "micros"),
                    col("Budget type", "campaign_budget.period", "enum"),
                    CAMPAIGN_TYPE, col("Bid strategy type", "campaign.bidding_strategy_type", "enum"),
                    IMPR, CLICKS, COST, CONV, VALUE,
                    col("Search impr. share", "metrics.search_impression_share", "share"),
                    col("Search lost IS (budget)", "metrics.search_budget_lost_impression_share", "lost")],
        "conditions": ["{date}"] + list(NOT_REMOVED), "orderings": ["segments.date ASC", "campaign.name ASC"], "limit": 10000,
        "needs": ["segments.date", "campaign.name", "metrics.cost_micros"],
        "readers": ["budgets and forecasts: python3 scripts/pacing.py FILE --out OUTPUT",
                    "conversion tracking, as the clicks file: python3 scripts/find_breaks.py REPORT --out OUTPUT --clicks FILE"],
        "gaps": ["Budget is the budget today, written on every day. A budget changed during the range shows its new amount on the earlier days too."],
    },
    "ad-groups": {
        "title": "Ad group report", "file": "ad-group-report.csv", "resource": "ad_group", "days": 30,
        "total": "Total: Filtered ad groups",
        "what": "Every ad group that is not removed, with its results.",
        "columns": [col("Ad group status", "ad_group.status", "enum"), AD_GROUP, CAMPAIGN,
                    col("Status", "campaign.status", "parents"),
                    col("Ad group type", "ad_group.type", "enum"),
                    IMPR, CLICKS, CTR, CPC, COST, CONV, CPA, VALUE],
        "conditions": ["{date}", "ad_group.status != 'REMOVED'"] + list(NOT_REMOVED),
        "orderings": ["metrics.cost_micros DESC"], "limit": 10000,
        "needs": ["ad_group.name", "metrics.cost_micros"],
        "readers": ["account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --ad-groups FILE"],
        "gaps": ["Status shows only a paused or removed campaign. Google's other serving reasons are not in this file."],
    },
    "ads": {
        "title": "Ads report", "file": "ads-report.csv", "resource": "ad_group_ad", "days": 30,
        "total": "Total: Filtered ads",
        "what": "Every ad that is not removed, with Ad strength and approval status.",
        "columns": [col("Ad status", "ad_group_ad.status", "enum"),
                    col("Ad", "ad_group_ad.ad.responsive_search_ad.headlines", "ad_name",
                        inputs=["ad_group_ad.ad.name", "ad_group_ad.ad.id"]),
                    col("Ad type", "ad_group_ad.ad.type", "enum"),
                    col("Ad strength", "ad_group_ad.ad_strength", "enum"),
                    CAMPAIGN, AD_GROUP,
                    col("Status", "campaign.status", "parents", inputs=["ad_group.status"]),
                    col("Approval status", "ad_group_ad.policy_summary.approval_status", "enum"),
                    col("Final URL", "ad_group_ad.ad.final_urls", "first"),
                    IMPR, CLICKS, COST, CONV],
        "conditions": ["{date}", "ad_group_ad.status != 'REMOVED'", "ad_group.status != 'REMOVED'"] + list(NOT_REMOVED),
        "orderings": ["metrics.cost_micros DESC"], "limit": 10000,
        "needs": ["ad_group_ad.ad.id", "metrics.cost_micros"],
        "readers": ["account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --ads FILE"],
        "gaps": ["The Ad column shows the first headline of a responsive search ad, else the ad's name, else its ID.",
                 "Policy details are not in this file. Approval status is."],
    },
    "change-history": {
        "title": "Change history report", "file": "change-history.csv", "resource": "change_event", "days": 30, "max_days": 30,
        "total": None,
        "what": "Changes made to the account in the last 30 days at most, newest first.",
        "columns": [col("Date & time", "change_event.change_date_time", "datetime"),
                    col("User", "change_event.user_email", "text"),
                    col("Campaign", "change_event.campaign", "lookup"),
                    col("Ad group", "change_event.ad_group", "lookup"),
                    col("Changes", "change_event.change_resource_type", "change",
                        inputs=["change_event.resource_change_operation", "change_event.changed_fields"]),
                    col("Changed through", "change_event.client_type", "enum")],
        "conditions": ["{change_start}", "{change_end}"], "orderings": ["change_event.change_date_time DESC"], "limit": 10000,
        "needs": ["change_event.change_date_time"],
        "joins": ["campaign-names", "ad-group-names"],
        "readers": ["conversion tracking: python3 scripts/find_breaks.py REPORT --out OUTPUT --changes FILE"],
        "gaps": ["Google keeps change events for 30 days, returns at most 10,000 rows and only the latest change to each item in the range.",
                 "Change events cover campaigns, ad groups, ads, keywords and other criteria, budgets, bid adjustments and assets. Changes to conversion actions are not among them.",
                 "Changes is written from the item type, what happened and the fields changed. It does not show old and new values."],
    },
    "conversion-actions": {
        "title": "Conversion actions", "file": "conversion-actions-summary.csv", "resource": "conversion_action", "days": 30,
        "total": "Total: Conversion actions", "dated_by_join": True,
        "what": "Every enabled conversion action with its settings, and its conversions in the range.",
        "columns": [col("Conversion action", "conversion_action.name", "text"),
                    col("Action optimization", "conversion_action.primary_for_goal", "primary"),
                    col("Conversion source", "conversion_action.type", "enum"),
                    col("Category", "conversion_action.category", "enum"),
                    col("Count", "conversion_action.counting_type", "enum"),
                    col("Click-through conv. window", "conversion_action.click_through_lookback_window_days", "days"),
                    col("View-through conv. window", "conversion_action.view_through_lookback_window_days", "days"),
                    col("Attribution model", "conversion_action.attribution_model_settings.attribution_model", "enum"),
                    col("Conversions", "metrics.conversions", "decimal", sum=True, join="conversions-by-action"),
                    col("Conv. value", "metrics.conversions_value", "decimal", sum=True, join="conversions-by-action"),
                    col("All conv.", "metrics.all_conversions", "decimal", sum=True, join="conversions-by-action"),
                    col("All conv. value", "metrics.all_conversions_value", "decimal", sum=True, join="conversions-by-action")],
        "conditions": ["conversion_action.status = 'ENABLED'"], "orderings": ["conversion_action.name ASC"], "limit": 10000,
        "needs": ["conversion_action.name"],
        "joins": ["conversions-by-action"], "join_key": ["segments.conversion_action_name", "conversion_action.name"],
        "readers": ["conversion tracking: python3 scripts/audit_actions.py FILE --out OUTPUT",
                    "account audit: python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS --conversions FILE"],
        "gaps": ["The tracking status (such as Recording conversions) is not in this file. Checks that need it show as not run.",
                 "Conversions are matched to actions by name."],
    },
    "conversions-by-action-and-day": {
        "title": "Conversions by action and day", "file": "conversions-by-action-and-day.csv", "resource": "campaign", "days": 60,
        "total": "Total: Account",
        "what": "Conversions by conversion action, campaign and day, to find when tracking broke.",
        "columns": [DAY, col("Conversion action", "segments.conversion_action_name", "text"), CAMPAIGN, CAMPAIGN_STATUS,
                    CONV, ALL_CONV, VALUE, ALL_VALUE],
        "conditions": ["{date}"], "orderings": ["segments.date ASC"], "limit": 10000,
        "needs": ["segments.date", "segments.conversion_action_name"],
        "readers": ["conversion tracking: python3 scripts/find_breaks.py FILE --out OUTPUT [--actions SUMMARY] [--clicks CAMPAIGNS_BY_DAY] [--changes CHANGE_HISTORY]"],
        "gaps": ["Cost and clicks cannot be read in the same query as conversion actions. Use the campaigns by day report for them."],
    },
}

# Searches that support a report: they are never converted on their own.
LOOKUPS = {
    "campaign-names": {"resource": "campaign", "fields": ["campaign.resource_name", "campaign.name"], "limit": 10000,
                       "conditions": [], "orderings": []},
    "ad-group-names": {"resource": "ad_group", "fields": ["ad_group.resource_name", "ad_group.name"], "limit": 10000,
                       "conditions": [], "orderings": []},
    "conversions-by-action": {"resource": "campaign", "conditions": ["{date}"], "orderings": [], "limit": 10000,
                              "fields": ["segments.conversion_action_name", "metrics.conversions", "metrics.conversions_value",
                                         "metrics.all_conversions", "metrics.all_conversions_value"]},
}

CHECK = {"resource": "customer", "limit": 1, "conditions": [], "orderings": [],
         "fields": ["customer.id", "customer.descriptive_name", "customer.currency_code", "customer.time_zone",
                    "customer.manager", "customer.test_account"]}


def report_fields(spec):
    out = []
    for column in spec["columns"]:
        if column.get("join"):
            continue
        for field in [column["field"]] + column.get("inputs", []):
            if field not in out:
                out.append(field)
    return out


# ---------------------------------------------------------------- dates and ids

def long_date(day):
    return "%s %d, %d" % (MONTHS[day.month - 1], day.day, day.year)


def range_text(start, end):
    return "%s - %s" % (long_date(start), long_date(end))


def iso(text, what):
    try:
        return dt.date.fromisoformat(str(text))
    except ValueError:
        raise Refusal("I can't read %s as a date. Write it as YYYY-MM-DD, for example 2026-11-12." % what)


def customer_id(text, what="the account ID"):
    digits = re.sub(r"[\s-]", "", str(text or ""))
    if not re.match(r"^\d{10}$", digits):
        raise Refusal("I can't read %s. Write the 10 digit Google Ads ID, for example 123-456-7890." % what)
    return digits


def dashed(digits):
    return "%s-%s-%s" % (digits[:3], digits[3:6], digits[6:])


def fill(conditions, start, end):
    out = []
    for condition in conditions:
        if condition == "{date}":
            out.append("segments.date BETWEEN '%s' AND '%s'" % (start.isoformat(), end.isoformat()))
        elif condition == "{change_start}":
            out.append("change_event.change_date_time >= '%s'" % start.isoformat())
        elif condition == "{change_end}":
            # Google's own example counts up to the next day, so the last day is whole.
            out.append("change_event.change_date_time <= '%s'" % (end + dt.timedelta(days=1)).isoformat())
        else:
            out.append(condition)
    return out


def parameters(resource, fields, conditions, orderings, limit, customer, login=None):
    params = {"customer_id": customer, "resource": resource, "fields": list(fields)}
    if conditions:
        params["conditions"] = list(conditions)
    if orderings:
        params["orderings"] = list(orderings)
    if limit:
        params["limit"] = int(limit)
    if login:
        params["login_customer_id"] = login
    return params


# ---------------------------------------------------------------- conditions

OPERATORS = ["NOT REGEXP_MATCH", "REGEXP_MATCH", "CONTAINS ANY", "CONTAINS ALL", "CONTAINS NONE", "IS NOT NULL",
             "IS NULL", "NOT BETWEEN", "BETWEEN", "NOT LIKE", "LIKE", "NOT IN", "IN", "DURING", "!=", ">=", "<=", "=", ">", "<"]


def condition_field(condition):
    """'metrics.clicks > 10' -> 'metrics.clicks'. Refuses anything that is not one condition."""
    text = " ".join(str(condition).split())
    if not text or ";" in text or re.search(r"\b(SELECT|FROM|WHERE|ORDER BY|LIMIT|PARAMETERS)\b", text, re.I):
        raise Refusal("Write each condition on its own, as a field, an operator and a value, for example: metrics.clicks > 10")
    match = re.match(r"^([a-z][a-z0-9_.]*)\s*(.*)$", text)
    rest = match.group(2) if match else ""
    if not match or not any(rest.upper().startswith(op) for op in OPERATORS):
        raise Refusal("I can't read the condition \"%s\". Write a field, an operator and a value, for example: metrics.clicks > 10" % text)
    return match.group(1)


def ordering_field(ordering):
    text = " ".join(str(ordering).split())
    match = re.match(r"^([a-z][a-z0-9_.]*)(\s+(ASC|DESC))?$", text, re.I)
    if not match:
        raise Refusal("I can't read the ordering \"%s\". Write a field, then ASC or DESC, for example: metrics.cost_micros DESC" % text)
    return match.group(1)


def check_fields(catalogue, resource, fields, conditions=(), orderings=()):
    """Classify every field. Refuse unknown ones with the nearest known names."""
    if resource not in catalogue.by_resource:
        near = catalogue.nearest_resources(resource)
        raise Refusal("I don't know the resource \"%s\".%s" % (
            resource, " The nearest known resources: %s." % ", ".join(near) if near else ""))
    checks, unknown = [], []
    every = [(f, "select") for f in fields]
    every += [(condition_field(c), "condition") for c in conditions]
    every += [(ordering_field(o), "ordering") for o in orderings]
    for field, where in every:
        status, note = catalogue.classify(resource, field, where)
        checks.append({"field": field, "used_in": where, "status": status, "note": note})
        if status == "unknown":
            unknown.append(field)
    if unknown:
        lines = ["I won't run this query. These fields are not in the known fields:"]
        for field in unknown:
            near = catalogue.nearest(field, resource)
            lines.append("- %s. Nearest known: %s." % (field, ", ".join(near) if near else "none close"))
        lines.append("Pick from the nearest names, or look the resource up with the metadata tool (%s)." % METADATA_TOOL)
        raise Refusal("\n".join(lines))
    return checks


# ---------------------------------------------------------------- reading the search tool's result

def _snake(part):
    return re.sub(r"(?<=[a-z0-9])([A-Z])", r"_\1", str(part)).lower()


def _flatten(row, prefix=""):
    out = {}
    for key, value in row.items():
        path = ".".join(_snake(p) for p in str(key).split("."))
        full = "%s.%s" % (prefix, path) if prefix else path
        if isinstance(value, dict) and value:
            out.update(_flatten(value, full))
        else:
            out[full] = value
    return out


ROW_KEYS = ("results", "result", "rows", "data", "structuredContent", "structured_content", "content")


def _rows(data, depth=0):
    if depth > 6:
        return
    if isinstance(data, str):
        try:
            parsed = json.loads(data)
        except ValueError:
            raise Refusal("The saved result holds text I can't read as a search result. Save the search tool's whole result again, unchanged.")
        yield from _rows(parsed, depth + 1)
        return
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict) and item.get("type") == "text" and "text" in item:
                yield from _rows(item["text"], depth + 1)
            elif isinstance(item, dict) and any(k in item for k in ROW_KEYS) and not any("." in str(k) for k in item):
                yield from _rows(item, depth + 1)
            else:
                yield item
        return
    if isinstance(data, dict):
        for key in ROW_KEYS:
            if key in data:
                yield from _rows(data[key], depth + 1)
                return
        yield data


def load_result(path, fields):
    """Rows of field path -> value, from the shapes a search result can take:
    a list of rows keyed by field path, nested objects (snake or camel case),
    a list of value lists in field order, batches with 'results', an MCP text
    content wrapper, or JSON lines."""
    if not os.path.isfile(path):
        raise Refusal("I can't find the search result at %s. Save the search tool's whole result there, unchanged, then run this again." % path)
    with open(path, encoding="utf-8-sig") as handle:
        text = handle.read()
    try:
        data = json.loads(text)
    except ValueError:
        try:
            data = [json.loads(line) for line in text.splitlines() if line.strip()]
        except ValueError:
            raise Refusal("The file %s is not a search result I can read. Save the search tool's whole result again, unchanged." % path)
    rows = []
    for row in _rows(data):
        if isinstance(row, list) and len(row) == len(fields):
            rows.append(dict(zip(fields, row)))
        elif isinstance(row, dict):
            rows.append(_flatten(row))
        else:
            raise Refusal("The file %s is not a search result I can read. Save the search tool's whole result again, unchanged." % path)
    return rows


# ---------------------------------------------------------------- formatting cells

def number(value):
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def fmt_int(value):
    return EMPTY if value is None else "{:,}".format(int(round(value)))


def fmt_money(value):
    return EMPTY if value is None else "{:,.2f}".format(value)


def fmt_pct(ratio):
    return EMPTY if ratio is None else "%.2f%%" % (ratio * 100)


def fmt_datetime(text):
    """'2026-11-13 11:00:41.123456' -> 'Nov 13, 2026, 11:00:41 AM'."""
    match = re.match(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2}):(\d{2})", str(text or ""))
    if not match:
        return str(text or "") or EMPTY
    year, month, day, hour, minute, second = (int(g) for g in match.groups())
    half = "AM" if hour < 12 else "PM"
    return "%s %d, %d, %d:%02d:%02d %s" % (MONTHS[month - 1][:3], day, year, (hour % 12) or 12, minute, second, half)


def readable_fields(value):
    if isinstance(value, dict):
        value = value.get("paths", [])
    if isinstance(value, str):
        value = value.split(",")
    words = []
    for path in value or []:
        last = _snake(str(path).strip().split(".")[-1])
        last = re.sub(r"_micros$", "", last).replace("_", " ").strip()
        if last and last not in words:
            words.append(last)
    return words
