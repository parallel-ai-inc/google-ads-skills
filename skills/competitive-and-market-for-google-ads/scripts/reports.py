"""Loaders for the competition and market skill.

Reads the auction insights report and a campaign report with impression share
columns, keeping Google's banded values ("< 10%", "> 90%") as bands instead of
turning them into a number. Imported by market.py; it has no command line.
"""
import datetime as dt
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io  # noqa: E402

MONTHS = {name: number for number, name in enumerate(
    ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"], start=1)}
MONTHS.update({name[:3]: number for name, number in list(MONTHS.items())})
MONTHS["sept"] = 9


# ---------------------------------------------------------------- shares

class Share(object):
    """A share as a range. An exact value has lo == hi. Google's '< 10%' is lo=0, hi=0.10."""

    def __init__(self, lo, hi, text=""):
        self.lo, self.hi, self.text = max(0.0, lo), min(1.0, hi), text

    @property
    def exact(self):
        return abs(self.hi - self.lo) < 1e-12

    @property
    def band(self):
        return bool(self.text) and self.text.strip()[:1] in "<>"

    def sort_key(self):
        """For ordering only. Never printed."""
        return (self.lo + self.hi) / 2.0

    def fmt(self):
        if self.exact:
            return "%.1f%%" % (self.lo * 100)
        if self.band:
            return re.sub(r"\s+", " ", self.text.strip()).replace("<", "< ").replace(">", "> ").replace("  ", " ")
        return "between %.1f%% and %.1f%%" % (self.lo * 100, self.hi * 100)

    def cell(self):
        """For a workbook cell: a number when exact, the text otherwise."""
        return round(self.lo, 6) if self.exact else self.fmt()

    def as_json(self):
        return {"shown": self.fmt(), "low": round(self.lo, 6), "high": round(self.hi, 6), "exact": self.exact}


def parse_share(value):
    """'45.3%' -> exact, '< 10%' -> below 10%, '> 90%' -> above 90%, '--' -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        return Share(number, number) if number <= 1 else Share(number / 100, number / 100)
    text = str(value).strip()
    if text in ("", "--", "-", "\u2014"):
        return None
    band = re.match(r"^([<>])\s*=?\s*([0-9]+(?:[.,][0-9]+)?)\s*%?$", text)
    if band:
        bound = float(band.group(2).replace(",", ".")) / 100
        return Share(0.0, bound, text) if band.group(1) == "<" else Share(bound, 1.0, text)
    number = io.to_number(text)
    if number is None:
        return None
    # CSV downloads write '45.3%'. A workbook download can hold 0.453.
    if "%" not in text and number <= 1:
        return Share(number, number)
    return Share(number / 100, number / 100)


class Move(object):
    """The change between two shares, in percentage points, as a range."""

    def __init__(self, old, new):
        self.old, self.new = old, new
        self.lo = new.lo - old.hi
        self.hi = new.hi - old.lo

    @property
    def exact(self):
        return abs(self.hi - self.lo) < 1e-12

    @property
    def direction(self):
        if self.exact and abs(self.lo) < 1e-12:
            return "level"
        if self.lo > 0:
            return "rose"
        if self.hi < 0:
            return "fell"
        return "unclear"

    def sort_key(self):
        return (self.lo + self.hi) / 2.0

    def fmt(self):
        if self.exact:
            return "%+.1f pts" % (self.lo * 100)
        if self.old.band and self.new.band and self.old.text.replace(" ", "") == self.new.text.replace(" ", ""):
            return "stayed %s" % self.new.fmt()
        if self.lo > 0:
            return "rose %.1f to %.1f pts" % (self.lo * 100, self.hi * 100)
        if self.hi < 0:
            return "fell %.1f to %.1f pts" % (-self.hi * 100, -self.lo * 100)
        return "unclear, %+.1f to %+.1f pts" % (self.lo * 100, self.hi * 100)

    def as_json(self):
        return {"shown": self.fmt(), "low_points": round(self.lo * 100, 4), "high_points": round(self.hi * 100, 4),
                "exact": self.exact, "direction": self.direction}


def move(old, new):
    return Move(old, new) if old is not None and new is not None else None


def combine(rows, share_key="sis", lost_keys=("lost_rank", "lost_budget")):
    """Combine campaign shares into one, weighting each by its estimated eligible impressions.

    Eligible impressions are estimated as Impr. / Search impr. share. A banded
    share gives a range, and an open band ('< 10%') leaves the upper end open.
    Returns (shares by key, rows used, rows left out).
    """
    used = [r for r in rows if r.get("impressions") and r.get(share_key) is not None]
    left_out = len(rows) - len(used)
    if not used:
        return None, 0, left_out
    impressions = sum(r["impressions"] for r in used)

    def eligible(r):
        s = r[share_key]
        low = r["impressions"] / s.hi if s.hi > 0 else math.inf
        high = r["impressions"] / s.lo if s.lo > 0 else math.inf
        return low, high

    bounds = [eligible(r) for r in used]
    elig_lo, elig_hi = sum(b[0] for b in bounds), sum(b[1] for b in bounds)
    result = {share_key: Share(0.0 if math.isinf(elig_hi) else impressions / elig_hi, impressions / elig_lo if elig_lo else 1.0)}
    result["eligible_impressions"] = (elig_lo, elig_hi)
    if len(used) == 1:
        # One row: keep its shares exactly as Google wrote them.
        result[share_key] = used[0][share_key]
        for key in lost_keys:
            result[key] = used[0].get(key)
        return result, 1, left_out
    for key in lost_keys:
        pairs = [(b, r[key]) for b, r in zip(bounds, used) if r.get(key) is not None]
        if not pairs:
            result[key] = None
            continue
        e_lo, e_hi = sum(b[0] for b, _ in pairs), sum(b[1] for b, _ in pairs)
        n_lo = sum(b[0] * s.lo for b, s in pairs)
        n_hi = sum(b[1] * s.hi if s.hi > 0 else 0.0 for b, s in pairs)
        low = 0.0 if math.isinf(e_hi) else n_lo / e_hi
        high = 1.0 if math.isinf(n_hi) or not e_lo else n_hi / e_lo
        result[key] = Share(low, high)
    return result, len(used), left_out


# ---------------------------------------------------------------- periods

class Period(object):
    def __init__(self, kind, start, end, label):
        self.kind, self.start, self.end, self.label = kind, start, end, label

    @property
    def key(self):
        return self.label

    @property
    def days(self):
        return (self.end - self.start).days + 1 if self.start and self.end else None

    def covered(self, date_range):
        """Days of this period inside the report's own date range."""
        if not date_range or not self.start:
            return self.days
        first, last = dates.parse_day(date_range[0]), dates.parse_day(date_range[1])
        start, end = max(self.start, first), min(self.end, last)
        return max(0, (end - start).days + 1)

    def cycle(self):
        """(position in the year, year): month number, or ISO week number."""
        if self.kind == "month":
            return self.start.month, self.start.year
        if self.kind == "week":
            iso = self.start.isocalendar()
            return iso[1], iso[0]
        return None


def month_period(year, month):
    start = dt.date(year, month, 1)
    end = dt.date(year, month, dates.days_in_month(start))
    return Period("month", start, end, "%04d-%02d" % (year, month))


def week_period(start):
    return Period("week", start, start + dt.timedelta(days=6), start.isoformat())


def parse_month(text):
    text = str(text or "").strip()
    found = re.match(r"^(\d{4})-(\d{1,2})$", text)
    if found:
        return month_period(int(found.group(1)), int(found.group(2)))
    found = re.match(r"^([A-Za-z]+)\.?\s+(\d{4})$", text)
    if found and found.group(1).lower() in MONTHS:
        return month_period(int(found.group(2)), MONTHS[found.group(1).lower()])
    day = dates.parse_day(text)
    return month_period(day.year, day.month) if day else None


def parse_week(text):
    text = str(text or "").strip()
    first = re.split(r"\s+[-\u2013]\s+", text)[0]
    day = dates.parse_day(first)
    return week_period(day) if day else None


def parse_quarter(text):
    text = str(text or "").strip()
    found = re.match(r"^Q([1-4])\s*,?\s*(\d{4})$", text, re.I) or re.match(r"^(\d{4})\s*-?\s*Q([1-4])$", text, re.I)
    if found:
        a, b = found.groups()
        year, quarter = (int(b), int(a)) if len(a) == 1 else (int(a), int(b))
    else:
        day = dates.parse_day(text)
        if not day:
            return None
        year, quarter = day.year, (day.month - 1) // 3 + 1
    start = dt.date(year, 3 * quarter - 2, 1)
    last = dt.date(year, 3 * quarter, 1)
    return Period("quarter", start, dt.date(year, 3 * quarter, dates.days_in_month(last)), "%04d-Q%d" % (year, quarter))


def parse_day_period(text):
    day = dates.parse_day(text)
    return Period("day", day, day, day.isoformat()) if day else None


PARSERS = {"month": parse_month, "week": parse_week, "quarter": parse_quarter, "day": parse_day_period}
KIND_NAMES = {"month": "Month", "week": "Week", "quarter": "Quarter", "day": "Day"}


def file_period(meta):
    """The period of an unsegmented report: its own date range, or a calendar month when it is exactly one."""
    if not meta.get("date_range"):
        return Period("file", None, None, "the whole file")
    start, end = dates.parse_day(meta["date_range"][0]), dates.parse_day(meta["date_range"][1])
    if start.day == 1 and end == dt.date(start.year, start.month, dates.days_in_month(start)):
        return month_period(start.year, start.month)
    return Period("range", start, end, "%s to %s" % (start.isoformat(), end.isoformat()))


def time_column(meta):
    for kind in ("month", "week", "quarter", "day"):
        if kind in meta["columns"]:
            return kind
    return None


# ---------------------------------------------------------------- the auction insights report

def _variants(names, prefixes=("", "search ", "shopping ", "auction insights ", "auction insights: "), suffixes=("", " (auction insights)")):
    return {p + n + s for n in names for p in prefixes for s in suffixes}


AUCTION_SHARES = ("impression_share", "overlap_rate", "position_above_rate", "top_of_page_rate", "abs_top_rate", "outranking_share")
AUCTION_LABELS = {"domain": "Display URL domain", "impression_share": "Impression share", "overlap_rate": "Overlap rate",
                  "position_above_rate": "Position above rate", "top_of_page_rate": "Top of page rate",
                  "abs_top_rate": "Abs. top of page rate", "outranking_share": "Outranking share"}
AUCTION_ALIASES = {}
for _key, _names in (
        ("domain", ("display url domain", "display url", "domain", "store display name", "advertiser", "competitor")),
        ("impression_share", ("impression share", "impr. share", "impression share (is)")),
        ("overlap_rate", ("overlap rate",)),
        ("position_above_rate", ("position above rate",)),
        ("top_of_page_rate", ("top of page rate", "top of the page rate")),
        ("abs_top_rate", ("abs. top of page rate", "abs. top of the page rate", "absolute top of page rate", "absolute top of the page rate")),
        ("outranking_share", ("outranking share",))):
    for _name in _variants(_names):
        AUCTION_ALIASES[_name] = _key
AUCTION_ALIASES.update({"month": "month", "week": "week", "quarter": "quarter", "device": "device", "ad group": "ad_group", "keyword": "keyword",
                        "search keyword": "keyword"})


def scope_from_titles(title_rows, names):
    """The campaign a download covers, when its title rows name it. None when they do not, or name several."""
    text = " ".join(title_rows)
    found = re.search(r"\bcampaigns?\s*:\s*(.+)", text, re.I)
    if found:
        candidate = found.group(1).strip().strip('"')
        if candidate in names or not names:
            return candidate
    if re.search(r"\ball campaigns\b", text, re.I):
        return "Account"
    matches = [n for n in names if n and n in text]
    matches = [n for n in matches if not any(n != other and n in other for other in matches)]
    return matches[0] if len(matches) == 1 else None


def read_auction(path, scope=None, own_domain=None, names=()):
    """Rows of one auction insights download: scope, period, domain, the six shares, and whether the row is the account's own.

    The scope comes from --scope, else a Campaign column, else the title rows,
    else it is assumed to be the whole account and marked as assumed.
    """
    if not os.path.exists(path):
        raise SystemExit("I can't find the auction insights file %s." % path)
    try:
        meta, raw = io.read_report(path, extra_aliases=AUCTION_ALIASES)
    except ValueError:
        raise SystemExit("I can't find the auction insights header in %s. In Google Ads open Campaigns, select the campaigns, "
                         "open Auction insights, and download it as CSV with the column headers." % os.path.basename(path))
    io.require(meta, ["domain", "impression_share"], "auction insights report", labels=AUCTION_LABELS)
    for split, name in (("device", "Device"), ("ad_group", "Ad group"), ("keyword", "Keyword")):
        if split in meta["columns"] and len({(r.get(split) or "").strip() for r in raw if (r.get(split) or "").strip()}) > 1:
            raise SystemExit("The auction insights report %s is split by %s. Download it again for the account or for one campaign, "
                             "without the %s segment." % (os.path.basename(path), name, name))
    title_scope = scope_from_titles(meta["title_rows"], names)
    if scope:
        file_scope, source = scope, "given with --scope"
    elif "campaign" in meta["columns"]:
        file_scope, source = None, "read from its Campaign column"
    elif title_scope:
        file_scope, source = title_scope, "read from its title rows"
    else:
        file_scope, source = "Account", "assumed"
    kind = time_column(meta)
    whole = file_period(meta) if not kind else None
    rows, unread = [], 0
    for r in raw:
        domain = (r.get("domain") or "").strip()
        if not domain:
            continue
        period = PARSERS[kind](r.get(kind)) if kind else whole
        if period is None:
            unread += 1
            continue
        mine = domain.lower() == "you" or (own_domain and domain.lower() == own_domain.lower())
        row = {"scope": (r.get("campaign") or "").strip() or file_scope or "Account", "period": period, "domain": "You" if mine else domain, "own": bool(mine)}
        for key in AUCTION_SHARES:
            row[key] = parse_share(r.get(key)) if key in meta["columns"] else None
        rows.append(row)
    if not rows:
        raise SystemExit("The auction insights report %s has no rows I can read." % os.path.basename(path))
    return {"path": path, "meta": meta, "rows": rows, "kind": kind or (whole.kind if whole else None), "unread_rows": unread,
            "columns": [k for k in AUCTION_SHARES if k in meta["columns"]], "scope": file_scope, "scope_source": source, "title_scope": title_scope}


# ---------------------------------------------------------------- the campaign report

CAMPAIGN_ALIASES = {
    "search impr. share": "sis", "search impression share": "sis",
    "search lost is (rank)": "lost_rank", "search lost is (budget)": "lost_budget",
    "search lost top is (rank)": "lost_top_rank", "search lost top is (budget)": "lost_top_budget",
    "month": "month", "week": "week", "quarter": "quarter", "device": "device", "status": "serving_status",
    "interactions": "interactions",
}
CAMPAIGN_LABELS = {"sis": "Search impr. share", "lost_rank": "Search lost IS (rank)", "lost_budget": "Search lost IS (budget)",
                   "month": "Month", "week": "Week"}


def read_campaigns(path):
    if not os.path.exists(path):
        raise SystemExit("I can't find the campaign report %s." % path)
    try:
        meta, raw = io.read_report(path, extra_aliases=CAMPAIGN_ALIASES, extra_numeric=("interactions",))
    except ValueError:
        raise SystemExit("I can't find the campaign report header in %s. In Google Ads open Campaigns and download the table as CSV." % os.path.basename(path))
    if "clicks" not in meta["columns"] and "interactions" in meta["columns"]:
        meta["columns"]["clicks"] = meta["columns"]["interactions"]
        for r in raw:
            r["clicks"] = r.get("interactions")
    io.require(meta, ["campaign", "impressions", "clicks", "cost", "conversions"], "campaign report")
    if "device" in meta["columns"] and len({(r.get("device") or "").strip() for r in raw if (r.get("device") or "").strip()}) > 1:
        raise SystemExit("The campaign report is split by Device. Download it again without the Device segment.")
    # Only Search lost IS reads as share lost. Search lost top IS is the share of top of page
    # impressions lost, a different measure, so it is never used in its place (a real download
    # on 2026-11-14 carried only the top versions).
    rank_key, budget_key = "lost_rank", "lost_budget"
    lost_source = "Search lost IS"
    if "lost_rank" not in meta["columns"] and "lost_budget" not in meta["columns"]:
        lost_source = None
        if "lost_top_rank" in meta["columns"] or "lost_top_budget" in meta["columns"]:
            lost_source = "top only"
    kind = time_column(meta)
    whole = file_period(meta) if not kind else None
    rows, unread = [], 0
    for r in raw:
        name = (r.get("campaign") or "").strip()
        if not name:
            continue
        period = PARSERS[kind](r.get(kind)) if kind else whole
        if period is None:
            unread += 1
            continue
        rows.append({"campaign": name, "period": period, "status": (r.get("campaign_status") or "").strip(),
                     "serving_status": (r.get("serving_status") or "").strip(), "campaign_type": (r.get("campaign_type") or "").strip(),
                     "budget": r.get("budget"), "currency": (r.get("currency") or "").strip(),
                     "impressions": r.get("impressions") or 0.0, "clicks": r.get("clicks") or 0.0, "cost": r.get("cost") or 0.0,
                     "conversions": r.get("conversions") or 0.0, "conv_value": r.get("conv_value"),
                     "sis": parse_share(r.get("sis")) if "sis" in meta["columns"] else None,
                     "lost_rank": parse_share(r.get(rank_key)) if rank_key in meta["columns"] else None,
                     "lost_budget": parse_share(r.get(budget_key)) if budget_key in meta["columns"] else None})
    if not rows:
        raise SystemExit("The campaign report %s has no campaign rows I can read." % os.path.basename(path))
    return {"path": path, "meta": meta, "rows": rows, "kind": kind or (whole.kind if whole else None), "unread_rows": unread,
            "has_share": "sis" in meta["columns"], "has_lost": rank_key in meta["columns"] or budget_key in meta["columns"],
            "lost_source": lost_source}


def reconcile(meta, rows, fields=("cost", "clicks", "impressions", "conversions")):
    """Compare the rows with the file's own total rows.

    Prefers 'Total: Filtered campaigns', then 'Total: Account', then a bare
    'Total'. A segmented report may write one total per period, a grand total,
    or both, so the sum of the totals and each single total are both tried.
    """
    sums = {f: sum((r.get(f) or 0) for r in rows) for f in fields}
    # Google rounds each row's cost and conversions to two decimals and the total before rounding,
    # so each row can move the sum by up to half a cent. Clicks and impressions are whole numbers.
    allowance = max(0.01, 0.005 * (len(rows) + 1))
    for wanted in ("total: filtered campaigns", "total: account", "total"):
        found = [t for t in meta["total_rows"] if t["label"].strip().lower() == wanted]
        if not found:
            continue
        candidates = [("sum of %d total rows" % len(found), {f: sum(t["values"].get(f) or 0 for t in found) for f in fields})]
        candidates += [("one total row", {f: t["values"].get(f) or 0 for f in fields}) for t in found if len(found) > 1]
        for how, values in candidates:
            if all(abs(values[f] - sums[f]) < (0.01 if f in ("clicks", "impressions") else allowance) for f in fields if f in values):
                return {"label": found[0]["label"], "how": how, "file": values, "rows": sums, "difference": 0.0, "matched": True}
        values = candidates[0][1]
        return {"label": found[0]["label"], "how": candidates[0][0], "file": values, "rows": sums,
                "difference": round(values["cost"] - sums["cost"], 2), "matched": False}
    return {"label": None, "how": "no total row in the file", "file": None, "rows": sums, "difference": None, "matched": None}
