"""Read the reports the performance reviews accept. A helper for review.py, not a step.

Each file is recognised by its headers, not by its name: a keyword report, an
ads report, a campaign report segmented by Day or by Device, a landing page
report, an audience report, a location report, an ad schedule report, a
placement report or a video report. A file it does not recognise is refused
with a plain message that lists what it can read.

Also here: the statistics every review shares. A segment is judged against a
baseline from the same file, and only once it has spent enough.
"""
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics  # noqa: E402

# Lowercase header -> short name, for columns the shared reader does not know.
# Where Google has used more than one name for a column, every name seen or
# documented is listed. The first matching column in a file wins.
EXTRA_ALIASES = {
    "interactions": "clicks", "bid strategy": "bid_strategy", "target cpa": "target_cpa",
    "keyword status": "keyword_status", "keyword state": "keyword_status", "search keyword status": "keyword_status",
    "ad group status": "ad_group_status", "ad group state": "ad_group_status",
    "ad status": "ad_status", "ad state": "ad_status",
    "status": "status", "status reasons": "status_reasons", "approval status": "approval_status",
    "quality score": "quality_score", "qual. score": "quality_score",
    "quality score (hist.)": "quality_score", "qual. score (hist.)": "quality_score",
    "exp. ctr": "exp_ctr", "expected ctr": "exp_ctr", "exp. ctr (hist.)": "exp_ctr",
    "ad relevance": "ad_relevance", "ad relevance (hist.)": "ad_relevance",
    "landing page exp.": "landing_page_exp", "landing page experience": "landing_page_exp",
    "landing page exp. (hist.)": "landing_page_exp",
    "final url": "final_url",
    "ad type": "ad_type", "ad strength": "ad_strength", "ad": "ad", "ad name": "ad", "headline 1": "headline_1",
    "ad id": "ad_id",
    "device": "device",
    "landing page": "landing_page", "expanded landing page": "landing_page", "landing page url": "landing_page",
    "mobile speed score": "mobile_speed_score", "mobile-friendly click rate": "mobile_friendly_rate",
    "audience segment": "audience", "audience": "audience", "audience name": "audience",
    "audience segment name": "audience", "user list": "audience",
    "targeting setting": "targeting_setting", "level": "level", "type": "segment_type",
    "placement type": "segment_type",
    "location": "location", "matched location": "location", "targeted location": "location",
    "user location": "location", "location name": "location", "most specific location": "location",
    "location type": "location_type",
    "day of week": "day_of_week", "day of the week": "day_of_week",
    "hour of day": "hour", "hour of the day": "hour", "hour": "hour",
    "ad schedule": "ad_schedule", "day and time": "ad_schedule",
    "placement": "placement", "where ads showed": "placement", "placement name": "placement",
    "group placement": "placement", "placement url": "placement_url",
    "video": "video", "video title": "video", "video name": "video", "video id": "video_id",
    "video duration": "video_duration",
    "views": "views", "video views": "views", "trueview views": "views", "youtube views": "views",
    "view rate": "view_rate", "trueview view rate": "view_rate", "youtube view rate": "view_rate",
    "video view rate": "view_rate",
    "avg. cpv": "avg_cpv", "trueview avg. cpv": "avg_cpv", "avg. trueview cpv": "avg_cpv",
    "video played to 25%": "played_25", "video played to 50%": "played_50",
    "video played to 75%": "played_75", "video played to 100%": "played_100",
}
GEO = ("postal_code", "city", "metro", "region", "country")
_GEO_HEADERS = {"postal code": "postal_code", "zip code": "postal_code", "city": "city", "metro area": "metro",
                "region": "region", "country/territory": "country", "country": "country",
                "most specific location": "location"}
for _header, _name in _GEO_HEADERS.items():
    EXTRA_ALIASES.setdefault(_header, _name)
    for _suffix in (" (user location)", " (matched location)", " (physical location)", " (location of interest)"):
        EXTRA_ALIASES.setdefault(_header + _suffix, _name)
EXTRA_NUMERIC = ("quality_score", "views", "avg_cpv", "mobile_speed_score", "target_cpa")
EXTRA_PERCENT = ("view_rate", "played_25", "played_50", "played_75", "played_100", "mobile_friendly_rate")

# Short name -> the header as Google Ads shows it, for messages.
LABELS = {
    "campaign": "Campaign", "ad_group": "Ad group", "keyword": "Keyword", "day": "Day", "device": "Device",
    "clicks": "Clicks (or Interactions)", "impressions": "Impr.", "cost": "Cost", "conversions": "Conversions",
    "landing_page": "Landing page", "audience": "Audience segment", "location": "Location",
    "placement": "Placement", "views": "Views", "quality_score": "Quality Score", "exp_ctr": "Exp. CTR",
    "ad_relevance": "Ad relevance", "landing_page_exp": "Landing page exp.",
}

# The reports this skill reads: what each is called, where it is in Google Ads,
# the columns it cannot work without, and the reviews it runs.
REPORTS = {
    "weekly": {"title": "campaign report segmented by Day",
               "path": "Campaigns menu, Campaigns, Campaigns, then the segment icon, Time, Day. At least the last 14 days, "
                       "28 or more for the trend",
               "must": ["day", "campaign", "cost", "conversions"], "reviews": ["weekly"]},
    "keywords": {"title": "keyword report", "path": "Campaigns menu, Audiences, keywords, and content, Search keywords",
                 "must": ["keyword", "campaign", "ad_group", "clicks", "cost", "conversions"],
                 "reviews": ["keywords", "quality_score"]},
    "ads": {"title": "ads report", "path": "Campaigns menu, Campaigns, Ads",
            "must": ["campaign", "ad_group", "impressions", "clicks", "cost", "conversions"], "reviews": ["ads"]},
    "devices": {"title": "campaign report segmented by Device",
                "path": "Campaigns menu, Campaigns, Campaigns, then the segment icon, Device",
                "must": ["device", "clicks", "cost", "conversions"], "reviews": ["devices"]},
    "landing_pages": {"title": "landing page report", "path": "Campaigns menu, Insights and reports, Landing pages",
                      "must": ["landing_page", "clicks", "cost", "conversions"], "reviews": ["landing_pages"]},
    "audiences": {"title": "audience report", "path": "Campaigns menu, Audiences, keywords, and content, Audiences",
                  "must": ["audience", "clicks", "cost", "conversions"], "reviews": ["audiences"]},
    "locations": {"title": "location report",
                  "path": "Campaigns menu, Insights and reports, When and where ads showed, Locations",
                  "must": ["clicks", "cost", "conversions"], "reviews": ["locations"]},
    "schedule": {"title": "ad schedule report",
                 "path": "Campaigns menu, Insights and reports, When and where ads showed, Ad schedule, or the campaign "
                         "report segmented by Time, Day of the week or Hour of day",
                 "must": ["clicks", "cost", "conversions"], "reviews": ["schedule"]},
    "placements": {"title": "placement report", "path": "Campaigns menu, Insights and reports, When and where ads showed, Where ads showed",
                   "must": ["placement", "impressions", "cost", "conversions"], "reviews": ["placements"]},
    "videos": {"title": "video report", "path": "Campaigns menu, Campaigns, Ads, filtered to Video campaigns",
               "must": ["impressions", "views", "cost"], "reviews": ["videos"]},
}
ORDER = ("weekly", "keywords", "ads", "devices", "landing_pages", "audiences", "locations", "schedule", "placements", "videos")
WEEKDAYS = ("monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday")
PARENT_STOPS = ("campaign paused", "campaign removed", "campaign ended", "ad group paused", "ad group removed")


def can_read():
    return "; ".join("the %s (%s)" % (REPORTS[k]["title"], REPORTS[k]["path"]) for k in ORDER)


def recognise(columns):
    """Which report a set of columns belongs to, or None."""
    c = set(columns)
    if "search_term" in c:
        return "search_terms"
    if c & {"views", "played_25", "played_50", "played_75", "played_100", "view_rate", "avg_cpv"}:
        return "videos"
    if c & {"placement", "placement_url"}:
        return "placements"
    if "audience" in c:
        return "audiences"
    if c & ({"location"} | set(GEO)):
        return "locations"
    if c & {"day_of_week", "hour", "ad_schedule"}:
        return "schedule"
    if "device" in c:
        return "devices"
    if "keyword" in c:
        return "keywords"
    if c & {"ad_type", "ad_status", "ad", "headline_1", "ad_strength", "ad_id"}:
        return "ads"
    if c & {"landing_page", "final_url"}:
        return "landing_pages"
    if "day" in c and "campaign" in c:
        return "weekly"
    return None


def read(path):
    """Read one export, recognise it, and stop with a plain message when it cannot be used."""
    name = os.path.basename(path)
    if not os.path.isfile(path):
        raise SystemExit("I can't find the file %s. Check the path." % path)
    try:
        meta, rows = io.read_report(path, extra_aliases=EXTRA_ALIASES, extra_numeric=EXTRA_NUMERIC,
                                    extra_percent=EXTRA_PERCENT)
    except Exception:  # no header row, or a damaged or wrong kind of file
        raise SystemExit("I can't read %s as a Google Ads report. Download it again from Google Ads as .csv with its "
                         "column headers. I can read: %s." % (name, can_read()))
    kind = recognise(meta["columns"])
    if kind == "weekly" and rows:
        # The ad schedule page can label its weekday column "Day". Weekday names are not dates.
        names = [str(r.get("day") or "").strip().lower() for r in rows]
        if sum(1 for n in names if n in WEEKDAYS) > len(names) / 2:
            kind = "schedule"
            for row in rows:
                row["day_of_week"] = row.get("day")
            meta["columns"]["day_of_week"] = meta["columns"]["day"]
    if kind == "search_terms":
        raise SystemExit("%s is a search terms report. The search terms skill in this pack reviews it. This skill reads: %s."
                         % (name, can_read()))
    if kind is None:
        raise SystemExit("I can't tell which report %s is from its headers. I can read: %s. A plain campaign report needs "
                         "the Day segment for the weekly review, or the Device segment for the device review."
                         % (name, can_read()))
    if kind == "landing_pages" and "landing_page" not in meta["columns"]:
        for row in rows:
            row["landing_page"] = row.get("final_url")
        meta["columns"]["landing_page"] = meta["columns"]["final_url"]
    io.require(meta, REPORTS[kind]["must"], REPORTS[kind]["title"], labels=LABELS)
    return kind, meta, rows


# ----- rows that are not serving

def state(text):
    """Enabled, paused, removed, ended or other, from a status cell."""
    cell = (text or "").strip().lower()
    if not cell:
        return "unknown"
    if "removed" in cell or "deleted" in cell:
        return "removed"
    if "paused" in cell:
        return "paused"
    if "ended" in cell:
        return "ended"
    if cell.startswith("enabled") or cell.startswith("eligible") or cell in ("active", "approved"):
        return "enabled"
    return "other"


def stopped(row):
    """Why a row is not serving now, or ''. Its own status, its ad group's or its campaign's."""
    for field in ("campaign_status", "ad_group_status", "keyword_status", "ad_status"):
        if state(row.get(field)) in ("paused", "removed", "ended"):
            return state(row.get(field))
    cell = (row.get("status") or "").lower()
    if any(stop in cell for stop in PARENT_STOPS) or state(cell) in ("paused", "removed", "ended"):
        return state(cell) if state(cell) in ("paused", "removed", "ended") else "paused"
    return ""


def is_brand(text, brand_phrases):
    words = metrics.tokens(text)
    for phrase in brand_phrases:
        span = len(phrase)
        if span and any(words[i:i + span] == phrase for i in range(len(words) - span + 1)):
            return True
    return False


def keyword_parts(text, match_cell):
    """'[24 hour plumber]', '' -> ('24 hour plumber', 'exact'). The Keyword column carries the match symbols."""
    raw = (text or "").strip()
    by_symbol = "exact" if raw.startswith("[") and raw.endswith("]") else \
        "phrase" if raw.startswith('"') and raw.endswith('"') else "broad"
    clean = " ".join(raw.strip('[]"').replace("+", " ").split()).lower()
    cell = (match_cell or "").lower()
    match = "exact" if "exact" in cell else "phrase" if "phrase" in cell else "broad" if "broad" in cell else by_symbol
    return clean, match


def clean_url(url):
    """Group a landing page by its address, without what follows '?' or '#'."""
    text = (url or "").strip()
    if not text:
        return ""
    base = re.split(r"[?#]", text, maxsplit=1)[0]
    match = re.match(r"^(https?://)([^/]+)(.*)$", base, re.I)
    if match:
        base = match.group(1).lower() + match.group(2).lower() + (match.group(3) or "/")
    return base


def period_of(meta):
    """The report's own date range, as text and as two dates, or None."""
    if not meta.get("date_range"):
        return None
    start, end = dates.parse_day(meta["date_range"][0]), dates.parse_day(meta["date_range"][1])
    return {"start": start.isoformat(), "end": end.isoformat(), "days": (end - start).days + 1}


def rounding_allowance(row_count):
    """How far the rows can sum from a total through rounding alone.

    Google shows each row's cost rounded to the cent and works the total out
    before rounding, so each row can move the sum by up to half a cent.
    """
    return max(0.05, 0.005 * (row_count + 1))


def reconcile(meta, rows_cost, row_count=0, kind=None):
    """Compare the rows with the file's own total rows.

    A segmented report repeats a total for every day or segment, so each label
    is tried alone and as the sum of its rows.
    """
    tolerance = rounding_allowance(row_count)
    by_label = {}
    for total in meta.get("total_rows", []):
        cost = total["values"].get("cost")
        if cost is not None:
            by_label.setdefault(total["label"], []).append(cost)
    if not by_label:
        return None
    totals = [{"label": label, "value": round(values[-1] if len(values) == 1 else sum(values), 2),
               "gap": round((values[-1] if len(values) == 1 else sum(values)) - rows_cost, 2), "meaning": total_meaning(label, kind)}
              for label, values in by_label.items()]
    candidates = []
    for label, values in by_label.items():
        candidates.append((label, values[-1] if len(values) == 1 else sum(values)))
        if len(values) > 1:
            candidates += [(label, v) for v in values]
    close = [c for c in candidates if abs(c[1] - rows_cost) <= tolerance]
    label, value = (close or sorted(candidates, key=lambda c: abs(c[1] - rows_cost)))[0]
    return {"label": label, "file_total": round(value, 2), "rows": round(rows_cost, 2),
            "difference": round(rows_cost - value, 2), "matches": bool(close), "totals": totals,
            "tolerance": round(tolerance, 2)}


def total_meaning(label, kind=None):
    """What a total row covers, read from its label."""
    low = label.lower()
    if "keywords in your account" in low:
        return "every keyword in the account, removed ones included"
    if "removed" in low:
        return "the keywords that are not removed"
    if "ai max" in low:
        return "spend from AI Max matches"
    if "url inclusions" in low:
        return "spend from the URL inclusions set for AI Max"
    if "filtered" in low:
        return "only the rows the table's filter showed"
    if "automatic targeting" in low:
        return "spend from Display automatic targeting"
    if "account" in low and kind == "keywords":
        return ("the whole account, including spend outside this report's rows, such as campaigns or traffic that are not "
                "keyword based (Performance Max, Display, Video)")
    if "account" in low:
        return "the whole account, including spend on campaigns, ad groups or traffic this report's rows do not cover"
    for kind in ("performance max", "demand gen", "search", "display", "video", "shopping", "app"):
        if kind in low:
            return "one campaign type"
    return "a total the file gives"


# ----- the statistics every review shares

SUMS = ("impressions", "clicks", "cost", "conversions", "conv_value", "views")
MIN_EXPECTED = 3      # conversions (or clicks, or views) a segment must be expected to bring before it is judged
ALPHA = 0.10          # a gap is called real when chance alone would give it less than 1 time in 10
WATCH = 1.5           # a gap this large either way (50% higher, or a third lower) is worth watching even when unproven


def wide(value, base):
    """True when value is at least WATCH times base, or at most base / WATCH."""
    if not value or not base:
        return False
    ratio = value / base
    return ratio >= WATCH or ratio <= 1.0 / WATCH


def blank(**extra):
    slot = {field: 0.0 for field in SUMS}
    slot["rows"] = 0
    slot.update(extra)
    return slot


def add(slot, row):
    for field in SUMS:
        slot[field] += row.get(field) or 0
    slot["rows"] += 1


def rates(slot):
    div = metrics.div
    slot["ctr"] = div(slot["clicks"], slot["impressions"])
    slot["cpc"] = div(slot["cost"], slot["clicks"])
    slot["cvr"] = div(slot["conversions"], slot["clicks"])
    slot["cpa"] = div(slot["cost"], slot["conversions"])
    slot["roas"] = div(slot["conv_value"], slot["cost"]) if slot["conv_value"] else None
    slot["view_rate"] = div(slot["views"], slot["impressions"]) if slot["views"] else None
    slot["cpv"] = div(slot["cost"], slot["views"]) if slot["views"] else None
    return slot


def total_of(rows):
    slot = blank()
    for row in rows:
        add(slot, row)
    return rates(slot)


def poisson_cdf(k, lam):
    """P(X <= k) for a Poisson count with mean lam."""
    if k < 0:
        return 0.0
    if lam <= 0:
        return 1.0
    log_lam, total = math.log(lam), 0.0
    for i in range(int(k) + 1):
        total += math.exp(i * log_lam - lam - math.lgamma(i + 1))
    return min(total, 1.0)


def test_count(observed, expected):
    """'low', 'high' or 'even': is the observed count beyond chance for the expected one?"""
    if poisson_cdf(math.floor(observed), expected) <= ALPHA:
        return "low"
    if 1.0 - poisson_cdf(math.ceil(observed) - 1, expected) <= ALPHA:
        return "high"
    return "even"


def binom_cdf(k, n, p):
    """P(X <= k) for X ~ Binomial(n, p)."""
    if k < 0:
        return 0.0
    if k >= n or p <= 0:
        return 1.0
    if p >= 1:
        return 0.0
    lp, lq, head = math.log(p), math.log(1 - p), math.lgamma(n + 1)
    total = 0.0
    for i in range(int(k) + 1):
        total += math.exp(head - math.lgamma(i + 1) - math.lgamma(n - i + 1) + i * lp + (n - i) * lq)
    return min(total, 1.0)


def test_share(observed, events, share):
    """'low', 'high' or 'even': is one item's count of the events further from its share than chance gives?

    Used where both sides can be small, as with an ad and its siblings: under
    no difference, the ad's conversions are a draw from all the ad group's
    conversions in proportion to its impressions.
    """
    n = int(round(events))
    if binom_cdf(math.floor(observed), n, share) <= ALPHA:
        return "low"
    if 1.0 - binom_cdf(math.ceil(observed) - 1, n, share) <= ALPHA:
        return "high"
    return "even"


def judge(slot, base):
    """Judge a segment's cost per conversion against a baseline, only once it has spent enough.

    Expected conversions are what the segment's spend would have bought at the
    baseline cost per conversion. Verdicts: Better, Worse, In line, No
    conversions (spent enough, none came), Not enough data to judge (a wide
    gap the volume cannot prove), Too little data, Cannot judge.
    """
    cpa = base.get("cpa")
    slot["expected"] = metrics.div(slot["cost"], cpa)
    slot["vs_cpa"] = metrics.change(slot["cpa"], cpa)
    slot["vs_cvr"] = metrics.change(slot["cvr"], base.get("cvr"))
    slot["lever"], slot["wasted"], slot["extra"] = "", 0.0, 0.0
    if not cpa:
        slot["verdict"] = "Cannot judge"
        return slot
    if slot["expected"] < MIN_EXPECTED:
        slot["verdict"] = "Not enough data to judge" if wide(slot["cpa"], cpa) else "Too little data"
        return slot
    if slot["conversions"] <= 0:
        slot["verdict"], slot["wasted"] = "No conversions", slot["cost"]
        return slot
    gap = test_count(slot["conversions"], slot["expected"])
    slot["verdict"] = {"low": "Worse", "high": "Better",
                       "even": "Not enough data to judge" if wide(slot["cpa"], cpa) else "In line"}[gap]
    if gap == "low":
        slot["extra"] = max(0.0, slot["cost"] - slot["conversions"] * cpa)
    if gap != "even" and slot["cvr"] and slot["cpc"] and base.get("cvr") and base.get("cpc"):
        by_rate = abs(math.log(slot["cvr"] / base["cvr"]))
        by_click = abs(math.log(slot["cpc"] / base["cpc"]))
        slot["lever"] = "conversion rate" if by_rate >= by_click else "cost per click"
    return slot


def money_of(slots):
    """Wasted, less efficient and too early, kept apart. Never added together."""
    return {
        "wasted": round(sum(s["cost"] for s in slots if s.get("verdict") == "No conversions"), 2),
        "wasted_count": sum(1 for s in slots if s.get("verdict") == "No conversions"),
        "less_efficient": round(sum(s.get("extra", 0.0) for s in slots if s.get("verdict") == "Worse"), 2),
        "worse_count": sum(1 for s in slots if s.get("verdict") == "Worse"),
        "better_count": sum(1 for s in slots if s.get("verdict") == "Better"),
        "too_early": round(sum(s["cost"] for s in slots if s.get("verdict") == "Too little data" and s["conversions"] <= 0), 2),
        "too_early_count": sum(1 for s in slots if s.get("verdict") == "Too little data" and s["conversions"] <= 0 and s["cost"] > 0),
    }
