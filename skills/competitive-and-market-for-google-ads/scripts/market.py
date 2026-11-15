#!/usr/bin/env python3
"""Read the competition and the market from Google Ads exports.

Reads the auction insights report (for the account or one campaign, as a
whole or segmented by Month or Week) and a campaign report with impression
share columns (best segmented by Month over 13 months or more). Works out who
the account meets in the auction and who gained or lost, whether the account's
own share was taken in the auction or held back by budget, a competitor
landscape, and seasonality: a monthly index, the same month last year, and the
months that usually rise or fall.

    python3 market.py --out OUTPUTDIR --campaigns CAMPAIGNS_BY_MONTH.csv --auction AUCTION_INSIGHTS.csv
    python3 market.py --out OUTPUTDIR --campaigns CAMPAIGNS.csv --auction ACCOUNT.csv --scope Account \\
        --auction EMERGENCY.csv --scope "Plumbing | Emergency" --brand "Brand" --earlier 2026-09 --later 2026-10
"""
import argparse
import datetime as dt
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics, outputs, xlsx  # noqa: E402
import reports  # noqa: E402
from reports import Share, combine, move  # noqa: E402

FIELDS = ("cost", "clicks", "impressions", "conversions")
TIMELINE_PERIODS = 6
# Seasonality needs one full year. A week report needs 52 weeks.
CYCLE = {"month": 12, "week": 52}
RECENT = 3
AHEAD = 3
# A move this many times the typical move in the file is marked large: a common robust fence for outliers.
LARGE_FENCE = 3


def sh(share, missing="n/a"):
    return share.fmt() if share is not None else missing


def mv(change):
    return change.fmt() if change is not None else "n/a"


def money(value):
    return metrics.money(value)


def num(value, places=0):
    return "n/a" if value is None else "{:,.{p}f}".format(value, p=places)


def signed(value):
    if value is None:
        return "n/a"
    if abs(value) < 0.0005:
        return "0.0%"
    return ("+" if value >= 0 else "") + metrics.pct(value)


GROUP_WORDS = {"All campaigns": "all campaigns", "Without brand": "campaigns other than brand"}


def period_sort(p):
    return (p.start.isoformat() if p.start else "", p.key)


def period_note(period, date_range):
    covered = period.covered(date_range)
    if period.days and covered is not None and covered < period.days:
        return "partial: %d of %d days" % (covered, period.days)
    return ""


def complete(period, date_range):
    return not period_note(period, date_range)


def pick_pair(periods, date_range):
    """Default comparison: the latest complete period against the one before it."""
    full = [p for p in periods if complete(p, date_range)]
    if len(full) >= 2:
        return full[-2], full[-1], False
    if len(periods) >= 2:
        return periods[-2], periods[-1], True
    return None, None, False


def reading(sis, rank, budget):
    """Which way the share went, and which lost column carries the fall. Arithmetic only.

    With exact values, the lost column that rose more carries the fall. With
    Google's bands, a column is named only when its smallest possible rise
    covers the whole fall, or is larger than the other's largest possible rise.
    """
    if sis is None:
        return "No Search impr. share in one of the periods"
    if sis.direction == "rose":
        return "Share rose"
    if sis.direction == "level":
        return "Share held"
    if sis.direction == "unclear":
        return "Too close to call: Google shows a band, not a number"
    if rank is None and budget is None:
        return "Share fell. The report has no lost IS columns"
    fall = -sis.lo  # the largest possible fall, in share
    exact = (rank is None or rank.exact) and (budget is None or budget.exact)
    if exact:
        r = rank.lo if rank is not None else None
        b = budget.lo if budget is not None else None
        if (b or 0) > 0 and (b or 0) >= (r or 0):
            return "Share fell, mostly lost to budget"
        if (r or 0) > 0:
            return "Share fell, mostly lost to rank"
        return "Share fell with no rise in lost to rank or budget"
    for name, this, other in (("rank", rank, budget), ("budget", budget, rank)):
        if this is not None and this.lo > 0 and (this.lo >= fall or other is None or this.lo > other.hi):
            return "Share fell, mostly lost to %s" % name
    return "Share fell. Google's bands leave it unclear whether rank or budget carries more"


def three(a, b, moves, earlier_key, later_key):
    """Search impr. share and both lost columns, earlier and later, in one sentence."""
    a, b = a or {}, b or {}
    parts = []
    for key, label in (("sis", "Search impr. share"), ("lost_rank", "lost to rank"), ("lost_budget", "lost to budget")):
        if earlier_key is None:
            if b.get(key) is not None:
                parts.append("%s %s in %s" % (label, sh(b.get(key)), later_key))
            continue
        parts.append("%s %s in %s, %s in %s (%s)" % (label, sh(a.get(key)), earlier_key, sh(b.get(key)), later_key, mv(moves.get(key))))
    text = "; ".join(parts)
    return text[0].upper() + text[1:]


def missed(row_shares, key):
    """Estimated impressions missed for one reason: eligible impressions x the lost share, as a range."""
    if not row_shares or row_shares.get(key) is None:
        return None
    lo, hi = row_shares["eligible_impressions"]
    share = row_shares[key]
    return lo * share.lo, hi * share.hi


def fmt_range(pair):
    if pair is None:
        return "n/a"
    lo, hi = pair
    if hi == float("inf"):
        return "at least {:,.0f}".format(lo)
    if abs(hi - lo) < 0.5:
        return "{:,.0f}".format(lo)
    return "{:,.0f} to {:,.0f}".format(lo, hi)


def range_cell(pair):
    """A workbook cell for an estimate: a whole number when exact, the range as text otherwise."""
    if pair is None:
        return ""
    lo, hi = pair
    return round(lo) if hi != float("inf") and abs(hi - lo) < 0.5 else fmt_range(pair)


def json_share(share):
    return share.as_json() if share is not None else None


def json_shares(d):
    if not d:
        return None
    out = {k: json_share(v) for k, v in d.items() if isinstance(v, Share) or v is None}
    if "eligible_impressions" in d:
        lo, hi = d["eligible_impressions"]
        out["eligible_impressions"] = [round(lo, 2), None if hi == float("inf") else round(hi, 2)]
    return out


# ---------------------------------------------------------------- auction insights

def analyse_scope(scope, rows, date_range, earlier, later, camp, brand):
    periods = sorted({r["period"].key: r["period"] for r in rows}.values(), key=period_sort)
    keys = [p.key for p in periods]
    by = {}
    for r in rows:
        by.setdefault(r["period"].key, {})[r["domain"]] = r
    result = {"scope": scope, "periods": [{"period": p.key, "note": period_note(p, date_range)} for p in periods], "notes": []}
    missing_you = [k for k in keys if "You" not in by.get(k, {})]
    result["periods_without_you_row"] = missing_you
    domains = sorted({r["domain"] for r in rows if not r["own"]})
    # The typical move of each share: the median of every exact period to period change of every competitor.
    # A move of LARGE_FENCE times that or more is marked large.
    fences = {}
    for key in ("impression_share", "overlap_rate", "position_above_rate", "outranking_share"):
        steps = []
        for d in domains:
            for a, b in zip(keys, keys[1:]):
                x, y = by.get(a, {}).get(d), by.get(b, {}).get(d)
                m = move(x[key], y[key]) if x and y else None
                if m and m.exact:
                    steps.append(abs(m.lo))
        typical = statistics.median(steps) if steps else None
        fences[key] = {"typical": typical, "large": LARGE_FENCE * typical if typical is not None else None, "moves_counted": len(steps)}
    result["fences"] = {k: {"typical_points": round(v["typical"] * 100, 2) if v["typical"] is not None else None,
                            "large_points": round(v["large"] * 100, 2) if v["large"] is not None else None, "moves_counted": v["moves_counted"]}
                        for k, v in fences.items()}
    # A measure written exactly the same in every period is rare in real data. Flag it.
    result["identical"] = []
    for d in ["You"] + domains:
        for key in reports.AUCTION_SHARES:
            values = [by[k][d][key] for k in keys if d in by.get(k, {}) and by[k][d].get(key) is not None]
            if len(values) >= 2 and all(v.exact for v in values) and len({round(v.lo, 6) for v in values}) == 1:
                result["identical"].append({"domain": d, "measure": reports.AUCTION_LABELS[key], "value": values[0].fmt(), "periods": len(values)})
    result["typical_move_points"] = result["fences"]["impression_share"]["typical_points"]
    result["large_move_points"] = result["fences"]["impression_share"]["large_points"]
    result["timeline"] = {d: {k: json_share(by.get(k, {}).get(d, {}).get("impression_share")) if d in by.get(k, {}) else None for k in keys}
                          for d in ["You"] + domains}
    if earlier is None or later is None or earlier.key not in by or later.key not in by:
        have = ", ".join(keys)
        result["compared"] = None
        result["competitors"] = []
        if keys:
            # One period still shows who the account meets in the auction, just not who moved.
            last = keys[-1]
            order = sorted(by[last].values(), key=lambda r: (not r["own"], -(r["overlap_rate"].lo if r.get("overlap_rate") else -1)))
            result["landscape"] = {"period": last, "rows": [
                {"domain": "You" if r["own"] else r["domain"], **{k: json_share(r.get(k)) for k in reports.AUCTION_SHARES}} for r in order]}
            result["notes"].append("This file's periods (%s) do not include two to compare, so it shows who the account met in %s, "
                                   "not who rose or fell. A second file for an earlier date range, or the file segmented by month, shows the moves." % (have, last))
        else:
            result["notes"].append("This file has no data for the compared periods. Its periods: %s." % have)
        return result, periods, by
    e, l = by[earlier.key], by[later.key]
    result["compared"] = {"earlier": earlier.key, "later": later.key, "later_note": period_note(later, date_range)}
    you_e, you_l = e.get("You"), l.get("You")
    you = {}
    for key in reports.AUCTION_SHARES:
        a = you_e.get(key) if you_e else None
        b = you_l.get(key) if you_l else None
        you[key] = {"earlier": json_share(a), "later": json_share(b), "change": move(a, b).as_json() if move(a, b) else None}
    result["you"] = you
    comps = []
    for d in domains:
        a, b = e.get(d), l.get(d)
        if not a and not b:
            continue
        item = {"domain": d, "status": "both" if a and b else ("new" if b else "gone")}
        for key in reports.AUCTION_SHARES:
            x = a.get(key) if a else None
            y = b.get(key) if b else None
            m = move(x, y)
            item[key] = {"earlier": x, "later": y, "change": m}
        item["large_moves"] = {}
        for key, fence in fences.items():
            m, line = item[key]["change"], fence["large"]
            item["large_moves"][key] = bool(m and line is not None and ((m.direction == "rose" and m.lo >= max(line, 1e-9))
                                                                       or (m.direction == "fell" and -m.hi >= max(line, 1e-9))))
        item["large"] = item["large_moves"]["impression_share"]
        item["seen_in"] = sum(1 for k in keys if d in by.get(k, {}))
        item["first_seen"] = next(k for k in keys if d in by.get(k, {}))
        item["last_seen"] = [k for k in keys if d in by.get(k, {})][-1]
        comps.append(item)

    def overlap_key(c):
        later_overlap = c["overlap_rate"]["later"]
        earlier_overlap = c["overlap_rate"]["earlier"]
        return (0 if later_overlap else 1, -(later_overlap.sort_key() if later_overlap else (earlier_overlap.sort_key() if earlier_overlap else 0)))
    comps.sort(key=overlap_key)
    result["competitors"] = comps

    def changed(key, direction):
        found = [c for c in comps if c["status"] == "both" and c[key]["change"] and c[key]["change"].direction == direction]
        return sorted(found, key=lambda c: -abs(c[key]["change"].sort_key()))
    result["gained"] = changed("impression_share", "rose")
    result["lost"] = changed("impression_share", "fell")
    result["unclear"] = changed("impression_share", "unclear")
    result["new"] = [c for c in comps if c["status"] == "new"]
    result["gone"] = [c for c in comps if c["status"] == "gone"]
    result["above_more"] = changed("position_above_rate", "rose")
    result["outranked_less"] = changed("outranking_share", "fell")
    # The campaign report for the same scope and periods.
    result["campaign_side"] = None
    if camp and camp["has_share"]:
        def scope_rows(period):
            return [r for r in camp["rows"] if r["period"].key == period.key and (scope == "Account" or r["campaign"] == scope)]
        ce, cl = scope_rows(earlier), scope_rows(later)
        if ce and cl:
            a, _, _ = combine(ce)
            b, _, _ = combine(cl)
            if a and b:
                side = {"earlier": a, "later": b, "sis": move(a["sis"], b["sis"]), "lost_rank": move(a.get("lost_rank"), b.get("lost_rank")),
                        "lost_budget": move(a.get("lost_budget"), b.get("lost_budget"))}
                side["reading"] = reading(side["sis"], side["lost_rank"], side["lost_budget"])
                result["campaign_side"] = side
        else:
            result["notes"].append("The campaign report has no rows for %s in %s and %s, so lost to rank and budget are not paired here."
                                   % (scope, earlier.key, later.key))
    return result, periods, by


# ---------------------------------------------------------------- share of voice

def period_detail(row, period, date_range):
    """Cost, budget and the shares of one campaign in one period."""
    if not row:
        return None
    days = period.covered(date_range) or period.days
    daily = metrics.div(row["cost"], days)
    return {"period": period.key, "note": period_note(period, date_range), "days": days, "cost": row["cost"], "budget": row.get("budget"),
            "avg_daily_cost": daily, "budget_used": metrics.div(daily, row.get("budget")), "impressions": row["impressions"], "clicks": row["clicks"],
            "conversions": row["conversions"], "avg_cpc": metrics.div(row["cost"], row["clicks"]), "conv_rate": metrics.div(row["conversions"], row["clicks"]),
            "sis": row["sis"], "lost_rank": row["lost_rank"], "lost_budget": row["lost_budget"]}


def budget_puzzle(item, de, dl):
    """Lost to budget rose while the daily budget stayed the same and daily spend did not rise. That does not add up on its own."""
    m = item["moves"]["lost_budget"]
    if not (m and m.direction == "rose" and de and dl and de["budget"] is not None and de["budget"] == dl["budget"]):
        return None
    if de["avg_daily_cost"] is None or dl["avg_daily_cost"] is None or dl["avg_daily_cost"] > de["avg_daily_cost"]:
        return None
    return {"lost_budget_change": m, "budget": dl["budget"], "daily_cost": [de["avg_daily_cost"], dl["avg_daily_cost"]],
            "budget_used": [de["budget_used"], dl["budget_used"]], "cost": [de["cost"], dl["cost"]], "cost_change": metrics.change(dl["cost"], de["cost"])}


def share_of_voice(camp, earlier, later, brand):
    rows = camp["rows"]
    date_range = camp["meta"].get("date_range")
    names = sorted({r["campaign"] for r in rows})
    by = {}
    for r in rows:
        by.setdefault(r["campaign"], {})[r["period"].key] = r
    periods = sorted({r["period"].key: r["period"] for r in rows}.values(), key=period_sort)
    out = {"campaigns": [], "account": {}, "timeline": {}, "by_period": {}, "earlier_key": earlier.key if earlier else None, "later_key": later.key,
           "period_notes": {p.key: period_note(p, date_range) for p in periods}, "identical": []}
    for name in names:
        series = by[name]
        latest = series[max(series, key=lambda k: period_sort(series[k]["period"]))]
        item = {"campaign": name, "brand": name in brand, "status": latest["status"], "budget": latest.get("budget"),
                "campaign_type": latest["campaign_type"]}
        e, l = series.get(earlier.key) if earlier else None, series.get(later.key) if later else None
        if not l or not l["impressions"]:
            item["reading"] = "Not serving in %s" % later.key
            item["serving"] = False
        elif earlier is None:
            item["reading"] = "One period only, so no change to read"
            item["serving"] = True
        elif not e or not e["impressions"]:
            item["reading"] = "Not serving in %s" % earlier.key
            item["serving"] = False
        else:
            item["serving"] = True
        a = combine([e])[0] if e else None
        b = combine([l])[0] if l else None
        item["earlier"], item["later"] = a, b
        item["cost"] = {"earlier": e["cost"] if e else None, "later": l["cost"] if l else None}
        item["conversions"] = {"earlier": e["conversions"] if e else None, "later": l["conversions"] if l else None}
        item["cpa_later"] = metrics.div(l["cost"], l["conversions"]) if l else None
        item["moves"] = {k: move(a.get(k) if a else None, b.get(k) if b else None) for k in ("sis", "lost_rank", "lost_budget")}
        if item["serving"] and earlier is not None:
            item["reading"] = reading(item["moves"]["sis"], item["moves"]["lost_rank"], item["moves"]["lost_budget"])
        item["missed_budget"] = missed(b, "lost_budget")
        item["missed_rank"] = missed(b, "lost_rank")
        item["equal_missed"] = bool(b and b.get("lost_budget") and b.get("lost_rank") and b["lost_budget"].exact and b["lost_rank"].exact
                                    and abs(b["lost_budget"].lo - b["lost_rank"].lo) < 1e-9)
        if item["serving"] and not (b and b.get("sis")):
            item["reading"] = "No Search impr. share for this campaign type"
        item["detail"] = {"earlier": period_detail(e, earlier, date_range) if earlier else None, "later": period_detail(l, later, date_range)}
        item["budget_puzzle"] = budget_puzzle(item, item["detail"]["earlier"], item["detail"]["later"]) if item["serving"] else None
        out["campaigns"].append(item)
        out["timeline"][name] = {p.key: series[p.key]["sis"] if p.key in series else None for p in periods}
        out["by_period"][name] = [period_detail(series[p.key], p, date_range) for p in periods if p.key in series]
        exact = [series[p.key]["sis"] for p in periods if p.key in series and series[p.key]["sis"] is not None]
        if len(exact) >= 3 and all(x.exact for x in exact) and len({round(x.lo, 6) for x in exact}) == 1:
            out["identical"].append({"campaign": name, "measure": "Search impr. share", "value": exact[0].fmt(), "periods": len(exact)})
    groups = {"All campaigns": [r for r in rows]}
    if brand:
        groups["Without brand"] = [r for r in rows if r["campaign"] not in brand]
    for label, group in groups.items():
        line = {}
        for side, period in (("earlier", earlier), ("later", later)):
            picked = [r for r in group if period and r["period"].key == period.key]
            line[side], line[side + "_used"], line[side + "_left_out"] = combine(picked) if picked else (None, 0, 0)
        a, b = line["earlier"], line["later"]
        line["moves"] = {k: move(a.get(k) if a else None, b.get(k) if b else None) for k in ("sis", "lost_rank", "lost_budget")}
        line["reading"] = (reading(line["moves"]["sis"], line["moves"]["lost_rank"], line["moves"]["lost_budget"]) if earlier is not None
                           else "One period only, so no change to read")
        out["account"][label] = line
        out["timeline"]["[%s]" % label] = {p.key: (combine([r for r in group if r["period"].key == p.key])[0] or {}).get("sis") for p in periods}
    out["headline"] = "Without brand" if brand else "All campaigns"
    out["periods"] = periods
    return out


# ---------------------------------------------------------------- seasonality

def sums(rows):
    total = {f: sum(r[f] or 0 for r in rows) for f in FIELDS}
    total["cpa"] = metrics.div(total["cost"], total["conversions"])
    return total


def sequence(periods, date_range, kind):
    """Every period from the first to the last, including any with no rows."""
    first, last = periods[0], periods[-1]
    out, current = [], first
    while current.start <= last.start:
        out.append(current)
        if kind == "month":
            year, month = current.start.year + (current.start.month // 12), current.start.month % 12 + 1
            current = reports.month_period(year, month)
        else:
            current = reports.week_period(current.end + dt.timedelta(days=1))
    return out


def seasonality(camp, brand):
    kind = camp["kind"]
    date_range = camp["meta"].get("date_range")
    result = {"kind": kind, "readable": False}
    if kind not in CYCLE:
        result["reason"] = "The campaign report is not segmented by Month or Week, so trends and seasonality cannot be read."
        return result
    cycle = CYCLE[kind]
    unit = "months" if kind == "month" else "weeks"
    rows = camp["rows"]
    periods = sorted({r["period"].key: r["period"] for r in rows}.values(), key=period_sort)
    seq = sequence(periods, date_range, kind)
    by_period = {}
    for r in rows:
        by_period.setdefault(r["period"].key, []).append(r)
    empty = [p.key for p in seq if p.key not in by_period]
    full = [p for p in seq if complete(p, date_range)]
    partial = [{"period": p.key, "note": period_note(p, date_range)} for p in seq if not complete(p, date_range)]
    group_name = "Without brand" if brand else "All campaigns"
    groups = {"All campaigns": lambda r: True}
    if brand:
        groups["Without brand"] = lambda r: r["campaign"] not in brand
    table = {g: {p.key: sums([r for r in by_period.get(p.key, []) if keep(r)]) for p in seq} for g, keep in groups.items()}
    lost = {}
    if camp["has_share"]:
        for p in seq:
            shares, _, _ = combine([r for r in by_period.get(p.key, []) if groups[group_name](r)])
            lost[p.key] = shares
    result.update({"unit": unit, "cycle": cycle, "group": group_name, "periods": [p.key for p in seq], "complete": [p.key for p in full],
                   "partial": partial, "empty_periods": empty, "totals": table, "first": seq[0].key, "last": seq[-1].key})
    result["shares"] = {k: json_shares(v) for k, v in lost.items()}
    if len(full) < cycle:
        result["reason"] = ("The report covers %d complete %s. Seasonality needs at least %d, so it cannot be read from this file. "
                            "Download at least 13 months, and 25 to see whether a pattern repeats." % (len(full), unit, cycle))
        return result
    result["readable"] = True

    def index(window, g):
        values = [table[g][p.key] for p in window]
        means = {f: sum(v[f] for v in values) / len(values) for f in FIELDS}
        year_cpa = metrics.div(sum(v["cost"] for v in values), sum(v["conversions"] for v in values))
        out = {}
        for p, v in zip(window, values):
            out[p.key] = {f: metrics.div(v[f] * 100, means[f]) for f in FIELDS}
            out[p.key]["cpa"] = metrics.div((v["cpa"] or 0) * 100, year_cpa) if v["cpa"] is not None else None
        return out

    last_cycle = full[-cycle:]
    cycles = [last_cycle]
    if len(full) >= 2 * cycle:
        cycles = [full[-2 * cycle:-cycle], last_cycle]
    result["cycles"] = [[p.key for p in c] for c in cycles]
    result["index"] = {g: {"last": index(last_cycle, g), "earlier": index(cycles[0], g) if len(cycles) > 1 else None} for g in groups}
    # Months that usually rise or fall.
    positions = {}
    for c in cycles:
        idx = index(c, group_name)
        for p in c:
            positions.setdefault(p.cycle()[0], []).append((p.key, idx[p.key]))
    pattern = {}
    for metric in ("clicks", "conversions"):
        if len(cycles) > 1:
            rise = [pos for pos, vals in positions.items() if len(vals) == len(cycles) and all((v[metric] or 0) > 100 for _, v in vals)]
            fall = [pos for pos, vals in positions.items() if len(vals) == len(cycles) and all((v[metric] or 0) < 100 for _, v in vals)]
            pattern[metric] = {"rule": "above or below 100 in each of the %d years covered" % len(cycles), "rise": sorted(rise), "fall": sorted(fall)}
        else:
            idx = index(last_cycle, group_name)
            ranked = sorted(last_cycle, key=lambda p: -(idx[p.key][metric] or 0))
            pattern[metric] = {"rule": "the three highest and three lowest in the one year covered",
                               "rise": [p.cycle()[0] for p in ranked[:3]], "fall": [p.cycle()[0] for p in ranked[-3:]]}
        pattern[metric]["values"] = {pos: [(k, round(v[metric], 1) if v[metric] is not None else None) for k, v in vals] for pos, vals in positions.items()}
    result["pattern"] = pattern
    # The same period last year.
    lookup = {p.cycle(): p for p in full}
    yoy = []
    for p in last_cycle:
        pos, year = p.cycle()
        prior = lookup.get((pos, year - 1))
        if not prior:
            continue
        a, b = table[group_name][prior.key], table[group_name][p.key]
        yoy.append({"period": p.key, "prior": prior.key, "now": b, "before": a,
                    "change": {f: metrics.change(b[f], a[f]) for f in FIELDS + ("cpa",)},
                    "lost_budget": (lost.get(p.key) or {}).get("lost_budget"), "lost_budget_before": (lost.get(prior.key) or {}).get("lost_budget"),
                    "lost_rank": (lost.get(p.key) or {}).get("lost_rank"), "lost_rank_before": (lost.get(prior.key) or {}).get("lost_rank")})
    result["same_period_last_year"] = yoy
    # The periods ahead, read from the same periods a year earlier: how far each moved from the latest complete period's
    # counterpart, so a budget and timing call has a number behind it.
    ahead = []
    latest = last_cycle[-1]
    base = lookup.get((latest.cycle()[0], latest.cycle()[1] - 1))
    partial_keys = {p["period"] for p in partial}
    idx_last = index(last_cycle, group_name)
    current = latest
    for _ in range(AHEAD):
        if kind == "month":
            current = reports.month_period(current.start.year + current.start.month // 12, current.start.month % 12 + 1)
        else:
            current = reports.week_period(current.end + dt.timedelta(days=1))
        pos, year = current.cycle()
        prior = lookup.get((pos, year - 1))
        if not prior:
            continue
        then = table[group_name][prior.key]
        before = table[group_name][base.key] if base else None
        ahead.append({"period": current.key, "in_progress": current.key in partial_keys, "prior": prior.key, "base": base.key if base else None,
                      "usually": "rises" if pos in pattern["clicks"]["rise"] else "falls" if pos in pattern["clicks"]["fall"] else "neither",
                      "clicks_index": (idx_last.get(prior.key) or {}).get("clicks"),
                      "step": {f: metrics.change(then[f], before[f]) if before else None for f in ("cost", "clicks", "conversions")},
                      "lost_budget": (lost.get(prior.key) or {}).get("lost_budget")})
    result["ahead"] = ahead
    # Campaign exposure over the last year.
    names = sorted({r["campaign"] for r in rows})
    exposure = []
    recent = last_cycle[-RECENT:]
    for name in names:
        series = {p.key: sums([r for r in by_period.get(p.key, []) if r["campaign"] == name]) for p in seq}
        active = [p for p in last_cycle if series[p.key]["cost"] > 0]
        item = {"campaign": name, "brand": name in brand, "active_periods": len(active), "of": len(last_cycle)}
        mean_clicks = sum(series[p.key]["clicks"] for p in last_cycle) / float(len(last_cycle))
        if mean_clicks and len(active) == len(last_cycle):
            ranked = sorted(last_cycle, key=lambda p: -series[p.key]["clicks"])
            item["peak"], item["low"] = ranked[0].key, ranked[-1].key
            item["peak_index"] = series[ranked[0].key]["clicks"] * 100 / mean_clicks
            item["low_index"] = series[ranked[-1].key]["clicks"] * 100 / mean_clicks
        now = sums([r for p in recent for r in by_period.get(p.key, []) if r["campaign"] == name])
        priors = [lookup.get((p.cycle()[0], p.cycle()[1] - 1)) for p in recent]
        if all(priors):
            before = sums([r for p in priors for r in by_period.get(p.key, []) if r["campaign"] == name])
            item["recent"] = {"periods": [p.key for p in recent], "prior_periods": [p.key for p in priors], "now": now, "before": before,
                              "change": {f: metrics.change(now[f], before[f]) for f in FIELDS + ("cpa",)}}
        exposure.append(item)
    result["campaigns"] = exposure
    result["part_year_campaigns"] = [c["campaign"] for c in exposure if 0 < c["active_periods"] < c["of"]]
    result["levers"] = year_on_year_levers(rows, last_cycle[-1], lookup, brand)
    return result


LEVER_WORDS = {"eligible": "estimated eligible impressions (the searches it could show for)", "sis": "Search impr. share",
               "impressions": "impressions", "ctr": "click through rate", "cvr": "conversion rate"}


def year_on_year_levers(rows, period, lookup, brand):
    """For each campaign, the period against the same period a year earlier, and which factor moved conversions most.

    Conversions = estimated eligible impressions x Search impr. share x click
    through rate x conversion rate, the same split as a period comparison. When
    a share is banded, impressions stand in for the first two factors.
    """
    pos, year = period.cycle()
    prior = lookup.get((pos, year - 1))
    if not prior:
        return []
    out = []
    for name in sorted({r["campaign"] for r in rows}):
        now = next((r for r in rows if r["campaign"] == name and r["period"].key == period.key), None)
        then = next((r for r in rows if r["campaign"] == name and r["period"].key == prior.key), None)
        if not now or not then or not now["clicks"] or not then["clicks"]:
            continue
        sides = {}
        for label, r in (("then", then), ("now", now)):
            sides[label] = {"impressions": r["impressions"], "clicks": r["clicks"], "cost": r["cost"], "conversions": r["conversions"],
                            "ctr": metrics.div(r["clicks"], r["impressions"]), "cvr": metrics.div(r["conversions"], r["clicks"]),
                            "avg_cpc": metrics.div(r["cost"], r["clicks"]), "sis": r["sis"], "lost_rank": r["lost_rank"], "lost_budget": r["lost_budget"],
                            "eligible": r["impressions"] / r["sis"].lo if r["sis"] is not None and r["sis"].exact and r["sis"].lo else None}
        split = all(sides[x]["eligible"] for x in sides)
        keys = ("eligible", "sis", "ctr", "cvr") if split else ("impressions", "ctr", "cvr")

        def factor(side, key):
            return sides[side]["sis"].lo if key == "sis" else sides[side][key]
        shares = metrics.log_shares({k: factor("now", k) for k in keys}, {k: factor("then", k) for k in keys})
        main = max(shares, key=lambda k: abs(shares[k])) if shares else None
        out.append({"campaign": name, "brand": name in brand, "period": period.key, "prior": prior.key, "then": sides["then"], "now": sides["now"],
                    "split": "eligible impressions x share x CTR x conv. rate" if split else "impressions x CTR x conv. rate",
                    "levers": shares, "main_lever": main, "conversions_change": metrics.change(now["conversions"], then["conversions"])})
    return out


# ---------------------------------------------------------------- main

def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", required=True)
    parser.add_argument("--auction", action="append", default=[], help="an auction insights download; repeat for each file")
    parser.add_argument("--scope", action="append", default=[], help="what each auction file covers, in the same order: Account or a campaign name")
    parser.add_argument("--campaigns", help="a campaign report with Search impr. share and lost IS columns, best segmented by Month")
    parser.add_argument("--brand", default="", help="brand campaign names, comma separated")
    parser.add_argument("--earlier", help="the earlier period to compare, for example 2026-09")
    parser.add_argument("--later", help="the later period to compare, for example 2026-10")
    parser.add_argument("--own-domain", help="the account's own domain, if the auction file names it instead of writing You")
    args = parser.parse_args()
    if not args.auction and not args.campaigns:
        raise SystemExit("Give me an auction insights report (--auction), a campaign report (--campaigns), or both.")
    if len(args.scope) > len(args.auction):
        raise SystemExit("There are more --scope names than --auction files. Give one --scope after each --auction.")
    if bool(args.earlier) != bool(args.later):
        raise SystemExit("Give both --earlier and --later, or neither.")

    camp = reports.read_campaigns(args.campaigns) if args.campaigns else None
    names = sorted({r["campaign"] for r in camp["rows"]}) if camp else []
    brand = [b.strip() for b in args.brand.split(",") if b.strip()]
    for b in brand:
        if camp and b not in names:
            raise SystemExit("There is no campaign called '%s' in the campaign report. The campaigns are: %s." % (b, "; ".join(names)))

    files = []
    for i, path in enumerate(args.auction):
        scope = args.scope[i] if i < len(args.scope) else None
        if scope and scope != "Account" and camp and scope not in names:
            raise SystemExit("There is no campaign called '%s' in the campaign report. Use Account or one of: %s." % (scope, "; ".join(names)))
        files.append(reports.read_auction(path, scope, args.own_domain, names))
    unscoped = [os.path.basename(f["path"]) for f in files if f["scope_source"] == "assumed"]
    if len(unscoped) > 1:
        raise SystemExit("These auction insights files do not say which campaigns they cover: %s. Give each one --scope, Account or a campaign name, "
                         "in the same order as the files." % ", ".join(unscoped))
    for f in files:
        if f["scope"] and f["scope"] != "Account" and camp and f["scope"] not in names:
            raise SystemExit("The auction insights file %s names the campaign '%s', which is not in the campaign report. Give it --scope."
                             % (os.path.basename(f["path"]), f["scope"]))
    scopes, scope_ranges, seen = {}, {}, {}
    for f in files:
        for r in f["rows"]:
            mark = (r["scope"], r["period"].key)
            if seen.setdefault(mark, f["path"]) != f["path"]:
                raise SystemExit("Two auction insights files cover %s for %s. Give each file its own --scope, in the same order as the files."
                                 % (r["scope"], r["period"].key))
            scopes.setdefault(r["scope"], []).append(r)
            scope_ranges.setdefault(r["scope"], []).append(f["meta"].get("date_range"))
    for scope in scopes:
        if any(r["own"] for r in scopes[scope]):
            continue
        raise SystemExit("I can't find the row for your own account in the auction insights report for %s. Google labels it You. "
                         "If your file names your domain instead, pass it with --own-domain." % scope)

    def scope_range(scope):
        ranges = [r for r in scope_ranges[scope] if r]
        if not ranges:
            return None
        return [min(r[0] for r in ranges), max(r[1] for r in ranges)]

    # The two periods to compare.
    base_periods, base_range = [], None
    if scopes:
        first = next(iter(scopes))
        base_periods = sorted({r["period"].key: r["period"] for r in scopes[first]}.values(), key=period_sort)
        base_range = scope_range(first)
    elif camp:
        base_periods = sorted({r["period"].key: r["period"] for r in camp["rows"]}.values(), key=period_sort)
        base_range = camp["meta"].get("date_range")
    every = {}
    for rows in list(scopes.values()) + ([camp["rows"]] if camp else []):
        for r in rows:
            every[r["period"].key] = r["period"]
    if args.earlier:
        for wanted in (args.earlier, args.later):
            if wanted not in every:
                raise SystemExit("There is no period '%s' in these files. The periods are: %s." % (wanted, ", ".join(sorted(every))))
        earlier, later, early_read = every[args.earlier], every[args.later], False
        if (earlier.start and later.start and earlier.start >= later.start):
            raise SystemExit("--earlier must come before --later.")
        chosen_by = "chosen by you"
    else:
        earlier, later, early_read = pick_pair(base_periods, base_range)
        chosen_by = "the latest complete period against the one before it" if not early_read else "the two latest periods; the later one is partial"
    later_note = period_note(later, base_range) if later else ""

    # Auction insights.
    auction = []
    for scope, rows in scopes.items():
        result, _, _ = analyse_scope(scope, rows, scope_range(scope), earlier, later, camp, brand)
        auction.append(result)

    sov = None
    if camp and camp["has_share"]:
        camp_periods = sorted({r["period"].key: r["period"] for r in camp["rows"]}.values(), key=period_sort)
        if later is not None and later.key in {p.key for p in camp_periods}:
            sov = share_of_voice(camp, earlier if earlier is not None and earlier.key in {p.key for p in camp_periods} else None, later, brand)
        elif later is None:
            sov = share_of_voice(camp, None, camp_periods[-1], brand)
    season = seasonality(camp, brand) if camp else None

    # Competitor landscape, from the auction data only.
    landscape = {}
    for result in auction:
        for c in result.get("competitors", []):
            entry = landscape.setdefault(c["domain"], {"domain": c["domain"], "scopes": []})
            entry["scopes"].append({"scope": result["scope"], "status": c["status"], "seen_in": c["seen_in"], "of": len(result["periods"]),
                                    "first_period": result["periods"][0]["period"],
                                    "first_seen": c["first_seen"], "last_seen": c["last_seen"],
                                    "overlap_rate": c["overlap_rate"]["later"], "impression_share": c["impression_share"]["later"],
                                    "position_above_rate": c["position_above_rate"]["later"], "outranking_share": c["outranking_share"]["later"],
                                    "is_change": c["impression_share"]["change"], "overlap_change": c["overlap_rate"]["change"]})
    for entry in landscape.values():
        best = max(entry["scopes"], key=lambda s: s["overlap_rate"].sort_key() if s["overlap_rate"] else -1)
        entry["top_overlap"] = best["overlap_rate"]
        entry["top_scope"] = best["scope"]
    land = sorted(landscape.values(), key=lambda e: -(e["top_overlap"].sort_key() if e["top_overlap"] else -1))

    # Checks.
    checks = {}
    if camp:
        checks["campaign_report"] = reports.reconcile(camp["meta"], camp["rows"])
        checks["campaign_unread_rows"] = camp["unread_rows"]
    checks["auction"] = []
    for result in auction:
        line = {"scope": result["scope"], "periods_without_you_row": result["periods_without_you_row"], "against_campaign_report": []}
        if camp and camp["has_share"]:
            for p in (earlier, later):
                if p is None:
                    continue
                you = next((r for r in scopes[result["scope"]] if r["own"] and r["period"].key == p.key), None)
                picked = [r for r in camp["rows"] if r["period"].key == p.key and (result["scope"] == "Account" or r["campaign"] == result["scope"])]
                shares = combine(picked)[0] if picked else None
                if you and you["impression_share"] and shares:
                    line["against_campaign_report"].append({"period": p.key, "auction": you["impression_share"], "campaigns": shares["sis"],
                                                            "difference": move(shares["sis"], you["impression_share"])})
        checks["auction"].append(line)
    checks["auction_unread_rows"] = sum(f["unread_rows"] for f in files)

    currencies = sorted({r["currency"] for r in camp["rows"] if r["currency"]}) if camp else []
    out = outputs.ensure_dir(args.out)
    write_json(out, args, files, camp, earlier, later, chosen_by, later_note, auction, sov, season, land, checks, brand)
    write_workbook(out, auction, sov, season, land, checks, camp)
    text = write_summary(out, args, files, camp, earlier, later, chosen_by, later_note, auction, sov, season, land, checks, brand, currencies)
    print(text)
    print("Wrote the files to %s" % out)


# ---------------------------------------------------------------- outputs

def comp_json(c):
    out = {"domain": c["domain"], "status": c["status"], "large_move": c["large"], "large_moves": c["large_moves"], "seen_in_periods": c["seen_in"],
           "first_seen": c["first_seen"], "last_seen": c["last_seen"]}
    for key in reports.AUCTION_SHARES:
        out[key] = {"earlier": json_share(c[key]["earlier"]), "later": json_share(c[key]["later"]),
                    "change": c[key]["change"].as_json() if c[key]["change"] else None}
    return out


def side_json(side):
    if not side:
        return None
    return {"earlier": json_shares(side["earlier"]), "later": json_shares(side["later"]), "reading": side["reading"],
            "changes": {k: side[k].as_json() if side[k] else None for k in ("sis", "lost_rank", "lost_budget")}}


def detail_json(d):
    if not d:
        return d
    return {k: (json_share(v) if isinstance(v, Share) or (v is None and k in ("sis", "lost_rank", "lost_budget")) else v) for k, v in d.items()}


def puzzle_json(z):
    if not z:
        return None
    return dict(z, lost_budget_change=z["lost_budget_change"].as_json())


def write_json(out, args, files, camp, earlier, later, chosen_by, later_note, auction, sov, season, land, checks, brand):
    data = {"inputs": {"auction": [{"file": os.path.basename(f["path"]), "title_rows": f["meta"]["title_rows"], "date_range": f["meta"].get("date_range"),
                                    "segmented_by": f["kind"], "columns": f["columns"], "covers": f["scope"], "scope_source": f["scope_source"],
                                    "title_rows_name": f["title_scope"]} for f in files],
                       "campaigns": {"file": os.path.basename(camp["path"]), "title_rows": camp["meta"]["title_rows"], "date_range": camp["meta"].get("date_range"),
                                     "segmented_by": camp["kind"], "has_impression_share": camp["has_share"], "lost_columns_read": camp["lost_source"]} if camp else None,
                       "brand_campaigns": brand},
            "compared": {"earlier": earlier.key if earlier else None, "later": later.key if later else None, "chosen_by": chosen_by, "later_note": later_note}}
    data["auction"] = []
    for r in auction:
        item = {k: r.get(k) for k in ("scope", "periods", "notes", "periods_without_you_row", "typical_move_points", "large_move_points", "fences", "identical",
                                      "compared", "you", "timeline", "landscape")}
        item["competitors"] = [comp_json(c) for c in r.get("competitors", [])]
        for key in ("gained", "lost", "unclear", "new", "gone", "above_more", "outranked_less"):
            item[key] = [c["domain"] for c in r.get(key, [])]
        item["campaign_report"] = side_json(r.get("campaign_side"))
        data["auction"].append(item)
    if sov:
        data["share_of_voice"] = {
            "campaigns": [{"campaign": c["campaign"], "brand": c["brand"], "status": c["status"], "campaign_type": c["campaign_type"], "budget": c["budget"],
                           "serving": c["serving"], "reading": c["reading"], "earlier": json_shares(c["earlier"]), "later": json_shares(c["later"]),
                           "changes": {k: v.as_json() if v else None for k, v in c["moves"].items()}, "cost": c["cost"], "conversions": c["conversions"],
                           "cost_per_conv_later": c["cpa_later"],
                           "impressions_missed_budget": list(c["missed_budget"]) if c["missed_budget"] else None,
                           "impressions_missed_rank": list(c["missed_rank"]) if c["missed_rank"] else None, "missed_figures_equal": c["equal_missed"],
                           "detail": {k: detail_json(v) for k, v in c["detail"].items()}, "budget_does_not_add_up": puzzle_json(c["budget_puzzle"])}
                          for c in sov["campaigns"]],
            "headline": sov["headline"], "identical": sov["identical"], "period_notes": sov["period_notes"],
            "by_period": {name: [detail_json(d) for d in rows] for name, rows in sov["by_period"].items()},
            "account": {label: {"earlier": json_shares(line["earlier"]), "later": json_shares(line["later"]), "reading": line["reading"],
                                "rows_used": [line["earlier_used"], line["later_used"]], "rows_left_out": [line["earlier_left_out"], line["later_left_out"]],
                                "changes": {k: v.as_json() if v else None for k, v in line["moves"].items()}} for label, line in sov["account"].items()},
            "timeline": {name: {k: json_share(v) for k, v in series.items()} for name, series in sov["timeline"].items()}}
    if season:
        s = dict(season)
        s["same_period_last_year"] = [dict(y, **{k: json_share(y[k]) for k in ("lost_budget", "lost_budget_before", "lost_rank", "lost_rank_before")})
                                      for y in season.get("same_period_last_year", [])]
        s["levers"] = [dict(x, then=detail_json(x["then"]), now=detail_json(x["now"])) for x in season.get("levers", [])]
        s["ahead"] = [dict(a, lost_budget=json_share(a["lost_budget"])) for a in season.get("ahead", [])]
        data["seasonality"] = s
    data["landscape"] = [{"domain": e["domain"], "top_overlap": json_share(e["top_overlap"]), "top_scope": e["top_scope"],
                          "scopes": [dict(s, **{k: json_share(s[k]) for k in ("overlap_rate", "impression_share", "position_above_rate", "outranking_share")},
                                          is_change=s["is_change"].as_json() if s["is_change"] else None,
                                          overlap_change=s["overlap_change"].as_json() if s["overlap_change"] else None) for s in e["scopes"]]} for e in land]
    c = dict(checks)
    c["auction"] = [dict(line, against_campaign_report=[{"period": x["period"], "auction": json_share(x["auction"]), "campaigns": json_share(x["campaigns"]),
                                                         "difference": x["difference"].as_json() if x["difference"] else None}
                                                        for x in line["against_campaign_report"]]) for line in checks["auction"]]
    data["checks"] = c
    outputs.write_json(os.path.join(out, "market.json"), data)


def write_workbook(out, auction, sov, season, land, checks, camp):
    book = xlsx.Workbook()
    pct6 = {i: "pct" for i in range(2, 20)}
    rows = []
    for r in auction:
        if not r.get("compared"):
            continue
        for c in r["competitors"]:
            line = [r["scope"], c["domain"]]
            for key in reports.AUCTION_SHARES:
                x, y, m = c[key]["earlier"], c[key]["later"], c[key]["change"]
                line += [x.cell() if x else "", y.cell() if y else "", (round(m.lo, 6) if m.exact else m.fmt()) if m else ""]
            line += [c["status"], "Yes" if c["large"] else ""]
            rows.append(line)
    header = ["Scope", "Display URL domain"]
    for key in reports.AUCTION_SHARES:
        label = reports.AUCTION_LABELS[key]
        header += [label + " earlier", label + " later", label + " change (share points)"]
    header += ["In both periods", "Large move"]
    book.add_sheet("Competitors", header, rows, formats={i: "pct" for i in range(2, 20)}, widths={0: 24, 1: 30})
    timeline = []
    for r in auction:
        for p in r["periods"]:
            for d, series in r["timeline"].items():
                share = series.get(p["period"])
                if share is None:
                    continue
                timeline.append([r["scope"], p["period"], p["note"], d, share["low"] if share["exact"] else share["shown"]])
    book.add_sheet("Auction timeline", ["Scope", "Period", "Period note", "Display URL domain", "Impression share"], timeline, formats={4: "pct"}, widths={0: 24, 3: 30})
    if sov:
        lines = []
        for c in sov["campaigns"]:
            a, b = c["earlier"] or {}, c["later"] or {}
            line = [c["campaign"], c["status"]]
            for key in ("sis", "lost_rank", "lost_budget"):
                x, y, m = a.get(key), b.get(key), c["moves"][key]
                line += [x.cell() if x else "", y.cell() if y else "", (round(m.lo, 6) if m.exact else m.fmt()) if m else ""]
            line += [c["reading"], c["budget"], range_cell(c["missed_budget"]), range_cell(c["missed_rank"])]
            lines.append(line)
        for label, acc in sov["account"].items():
            a, b = acc["earlier"] or {}, acc["later"] or {}
            line = ["[%s]" % label, ""]
            for key in ("sis", "lost_rank", "lost_budget"):
                x, y, m = a.get(key), b.get(key), acc["moves"][key]
                line += [x.cell() if x else "", y.cell() if y else "", (round(m.lo, 6) if m.exact else m.fmt()) if m else ""]
            line += [acc["reading"], "", "", ""]
            lines.append(line)
        book.add_sheet("Share of voice", ["Campaign", "Campaign status", "Search impr. share earlier", "Search impr. share later", "Change",
                                          "Lost IS (rank) earlier", "Lost IS (rank) later", "Change", "Lost IS (budget) earlier", "Lost IS (budget) later", "Change",
                                          "Reading", "Budget", "Impr. missed to budget (estimate)", "Impr. missed to rank (estimate)"],
                       lines, formats=dict([(i, "pct") for i in range(2, 11)] + [(12, "money"), (13, "int"), (14, "int")]), widths={0: 30, 11: 44})
        lines = []
        for name, details in sov["by_period"].items():
            for d in details:
                lines.append([name, "Yes" if name in [c["campaign"] for c in sov["campaigns"] if c["brand"]] else "", d["period"], d["note"] or "complete",
                              d["cost"], d["budget"], d["avg_daily_cost"], d["budget_used"], d["avg_cpc"], d["impressions"], d["clicks"], d["conversions"], d["conv_rate"],
                              d["sis"].cell() if d["sis"] else "", d["lost_rank"].cell() if d["lost_rank"] else "", d["lost_budget"].cell() if d["lost_budget"] else ""])
        book.add_sheet("Campaign by period", ["Campaign", "Brand", "Period", "Period note", "Cost", "Daily budget", "Avg. daily cost", "Of budget", "Avg. CPC", "Impr.",
                                              "Clicks", "Conversions", "Conv. rate", "Search impr. share", "Lost IS (rank)", "Lost IS (budget)"], lines,
                       formats={4: "money", 5: "money", 6: "money", 7: "pct", 8: "money", 9: "int", 10: "int", 11: "money", 12: "pct", 13: "pct", 14: "pct", 15: "pct"},
                       widths={0: 30, 3: 22})
    if season and season.get("periods"):
        g = season["group"]
        idx = (season.get("index") or {}).get(g, {}).get("last") or {}
        lines = []
        for k in season["periods"]:
            v = season["totals"][g][k]
            i = idx.get(k, {})
            shares = season["shares"].get(k) or {}
            lines.append([k, "Yes" if k in season["complete"] else "Partial", v["cost"], v["clicks"], v["impressions"], v["conversions"], v["cpa"],
                          i.get("cost"), i.get("clicks"), i.get("impressions"), i.get("conversions"), i.get("cpa"),
                          (shares.get("lost_budget") or {}).get("shown", ""), (shares.get("lost_rank") or {}).get("shown", "")])
        book.add_sheet("Trend by period", ["Period", "Complete", "Cost", "Clicks", "Impr.", "Conversions", "Cost / conv.", "Cost index", "Clicks index",
                                           "Impr. index", "Conv. index", "Cost / conv. index", "Lost IS (budget)", "Lost IS (rank)"],
                       [[round(x, 1) if isinstance(x, float) and j >= 7 else x for j, x in enumerate(line)] for line in lines],
                       formats={2: "money", 3: "int", 4: "int", 5: "money", 6: "money", 7: "money", 8: "money", 9: "money", 10: "money", 11: "money"})
        if season.get("same_period_last_year"):
            lines = []
            for y in season["same_period_last_year"]:
                lines.append([y["period"], y["prior"], y["before"]["cost"], y["now"]["cost"], y["change"]["cost"], y["before"]["clicks"], y["now"]["clicks"],
                              y["change"]["clicks"], y["before"]["conversions"], y["now"]["conversions"], y["change"]["conversions"],
                              y["before"]["cpa"], y["now"]["cpa"], y["change"]["cpa"], sh(y["lost_budget_before"], ""), sh(y["lost_budget"], "")])
            book.add_sheet("Same period last year", ["Period", "A year earlier", "Cost then", "Cost now", "Cost change", "Clicks then", "Clicks now", "Clicks change",
                                                     "Conv. then", "Conv. now", "Conv. change", "Cost / conv. then", "Cost / conv. now", "Cost / conv. change",
                                                     "Lost IS (budget) then", "Lost IS (budget) now"], lines,
                           formats={2: "money", 3: "money", 4: "pct", 5: "int", 6: "int", 7: "pct", 8: "money", 9: "money", 10: "pct", 11: "money", 12: "money", 13: "pct"})
        if season.get("campaigns"):
            lines = []
            for c in season["campaigns"]:
                rec = c.get("recent") or {}
                ch = rec.get("change", {})
                lines.append([c["campaign"], c["active_periods"], c["of"], c.get("peak", ""), round(c["peak_index"], 1) if c.get("peak_index") is not None else "",
                              c.get("low", ""), round(c["low_index"], 1) if c.get("low_index") is not None else "", ch.get("cost"), ch.get("conversions"), ch.get("cpa")])
            book.add_sheet("Campaign seasonality", ["Campaign", "Periods with spend", "Of", "Peak (clicks)", "Peak clicks index", "Low (clicks)", "Low clicks index",
                                                    "Recent cost vs a year earlier", "Recent conv. vs a year earlier", "Recent cost / conv. vs a year earlier"], lines,
                           formats={1: "int", 2: "int", 4: "money", 6: "money", 7: "pct", 8: "pct", 9: "pct"}, widths={0: 30})
    if season and season.get("levers"):
        lines = []
        for x in season["levers"]:
            lv = x["levers"] or {}
            lines.append([x["campaign"], x["prior"], x["period"], x["then"]["impressions"], x["now"]["impressions"], x["then"]["sis"].cell() if x["then"]["sis"] else "",
                          x["now"]["sis"].cell() if x["now"]["sis"] else "", x["then"]["avg_cpc"], x["now"]["avg_cpc"], x["then"]["cvr"], x["now"]["cvr"],
                          x["then"]["conversions"], x["now"]["conversions"], x["conversions_change"], lv.get("eligible", lv.get("impressions")), lv.get("sis"),
                          lv.get("ctr"), lv.get("cvr"), LEVER_WORDS.get(x["main_lever"], "")])
        book.add_sheet("Year on year levers", ["Campaign", "A year earlier", "Period", "Impr. then", "Impr. now", "Search impr. share then", "Search impr. share now",
                                               "Avg. CPC then", "Avg. CPC now", "Conv. rate then", "Conv. rate now", "Conv. then", "Conv. now", "Conv. change",
                                               "Share of change: eligible impr. (or impr.)", "Share of change: impr. share", "Share of change: CTR",
                                               "Share of change: conv. rate", "Moved most"], lines,
                       formats={3: "int", 4: "int", 5: "pct", 6: "pct", 7: "money", 8: "money", 9: "pct", 10: "pct", 11: "money", 12: "money", 13: "pct",
                                14: "pct", 15: "pct", 16: "pct", 17: "pct"}, widths={0: 30, 18: 40})
    book.add_sheet("Landscape", ["Display URL domain", "Scope", "Seen in periods", "Of", "First seen", "Last seen", "Overlap rate", "Impression share",
                                 "Position above rate", "Outranking share", "Impression share change"],
                   [[e["domain"], s["scope"], s["seen_in"], s["of"], s["first_seen"], s["last_seen"]]
                    + [s[k].cell() if s[k] else "" for k in ("overlap_rate", "impression_share", "position_above_rate", "outranking_share")]
                    + [s["is_change"].fmt() if s["is_change"] else ""] for e in land for s in e["scopes"]],
                   formats={2: "int", 3: "int", 6: "pct", 7: "pct", 8: "pct", 9: "pct"}, widths={0: 30, 1: 24})
    check_rows = []
    if "campaign_report" in checks:
        rc = checks["campaign_report"]
        check_rows.append(["Campaign report rows against its own total", rc["label"] or "no total row", "Matched" if rc["matched"] else ("Not matched" if rc["matched"] is False else "Not checked"),
                           rc["difference"]])
    for line in checks["auction"]:
        for x in line["against_campaign_report"]:
            check_rows.append(["Auction insights You row against the campaign report, %s, %s" % (line["scope"], x["period"]), "%s against %s" % (x["auction"].fmt(), x["campaigns"].fmt()),
                               x["difference"].fmt() if x["difference"] else "", ""])
    book.add_sheet("Checks", ["Check", "Values", "Result", "Cost difference"], check_rows, formats={3: "money"}, widths={0: 70, 1: 30})
    book.save(os.path.join(out, "competitive-and-market.xlsx"))


def covers(meta):
    if meta.get("date_range"):
        return "%s to %s" % tuple(meta["date_range"])
    return "no date range in its title rows"


def mark(text, note):
    """A cell of a partial period carries the mark itself."""
    return "%s (partial)" % text if note and text not in ("n/a", "not seen") else text


def lever_move(x, key):
    """How one factor of the conversion split moved, in its own units."""
    t, n = x["then"], x["now"]
    if key == "sis":
        return "%s to %s (%s)" % (sh(t["sis"]), sh(n["sis"]), mv(move(t["sis"], n["sis"])))
    if key in ("ctr", "cvr"):
        return "%s to %s (%s)" % (metrics.pct(t[key], 2), metrics.pct(n[key], 2), signed(metrics.change(n[key], t[key])))
    return "%s to %s (%s)" % (num(t[key]), num(n[key]), signed(metrics.change(n[key], t[key])))


def puzzle_text(c, sov, short=False):
    z = c["budget_puzzle"]
    base = "%s: lost to budget %s while the daily budget stayed %s and average daily cost went from %s to %s (%s to %s of the budget)" % (
        c["campaign"], mv(z["lost_budget_change"]), money(z["budget"]), money(z["daily_cost"][0]), money(z["daily_cost"][1]),
        metrics.pct(z["budget_used"][0], 0), metrics.pct(z["budget_used"][1], 0))
    if short:
        return base
    return (base + ". That does not add up on its own: a campaign held back by its budget usually spends close to it (Practitioner rule). "
            "The Budget column may show today's budget on every row, so first confirm in the change history that the budget did not change. "
            "Then check for a bid strategy or target change, a shared budget, and how the budget is spent through the day.")


def campaign_answer(c, scope_result, lever, sov):
    a, b = c["earlier"] or {}, c["later"] or {}
    text = "**%s:** Search impr. share %s in %s, %s in %s (%s). %s." % (c["campaign"], sh(a.get("sis")), sov["earlier_key"], sh(b.get("sis")), sov["later_key"],
                                                                     mv(c["moves"]["sis"]), c["reading"])
    if scope_result and scope_result.get("compared"):
        pressing = [x for x in scope_result["above_more"] if x["large_moves"]["position_above_rate"] or x["large"]]
        if pressing or scope_result["new"]:
            text += " In its auction insights: %s." % "; ".join(
                ["%s showed above you more often (position above rate %s, impression share %s)" % (x["domain"], mv(x["position_above_rate"]["change"]), mv(x["impression_share"]["change"]))
                 for x in pressing] + ["%s is new" % x["domain"] for x in scope_result["new"]])
        else:
            text += " In its auction insights no competitor moved by a large amount."
    if lever and lever["levers"]:
        main = lever["main_lever"]
        text += " Against %s, conversions %s; the factor that moved them most is %s, %s." % (
            lever["prior"], signed(lever["conversions_change"]), LEVER_WORDS[main], lever_move(lever, main))
    if c.get("budget_puzzle"):
        text += " Lost to budget rose while the budget and daily spend did not: see the flag below."
    return text


def month_name(position, kind):
    if kind == "month":
        return ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"][position - 1]
    return "week %d" % position


def write_summary(out, args, files, camp, earlier, later, chosen_by, later_note, auction, sov, season, land, checks, brand, currencies):
    L = ["# Competition and market", ""]
    for f in files:
        L.append("- Auction insights: %s, %s%s. Covers: %s (%s)." % (os.path.basename(f["path"]), covers(f["meta"]),
                                                                   ", segmented by %s" % f["kind"] if f["kind"] in ("month", "week", "quarter", "day") else ", not segmented",
                                                                   f["scope"] or "the campaigns in its Campaign column", f["scope_source"]))
    if camp:
        L.append("- Campaign report: %s, %s%s." % (os.path.basename(camp["path"]), covers(camp["meta"]),
                                                  ", segmented by %s" % camp["kind"] if camp["kind"] in ("month", "week", "quarter", "day") else ", not segmented"))
    if camp:
        names = sorted({r["campaign"] for r in camp["rows"]})
        L.append("- Campaigns in the report: %s." % "; ".join(n + (" (brand)" if n in brand else "") for n in names))
    if len(currencies) == 1:
        L.append("- Amounts are in %s." % currencies[0])
    if earlier and later:
        L.append("- Compared: **%s** against **%s** (%s).%s" % (later.key, earlier.key, chosen_by, " %s is %s, so read it as an early read." % (later.key, later_note) if later_note else ""))
    L.append("- Brand campaigns: %s." % (", ".join(brand) if brand else "none named, so every campaign is in the account lines"))
    L.append("")

    # In short: one answer per campaign first, then the account. Brand is left out of the headline readings.
    L += ["## In short", ""]
    by_scope = {r["scope"]: r for r in auction}
    levers = {x["campaign"]: x for x in (season or {}).get("levers", [])}
    shown = set()
    if sov:
        for c in sov["campaigns"]:
            if c["brand"] or not c["serving"] or sov["earlier_key"] is None:
                continue
            L.append("- " + campaign_answer(c, by_scope.get(c["campaign"]), levers.get(c["campaign"]), sov))
            shown.add(c["campaign"])
        head = sov["account"][sov["headline"]]
        L.append("- %s: %s. %s." % (GROUP_WORDS[sov["headline"]].capitalize(), three(head["earlier"], head["later"], head["moves"], sov["earlier_key"], sov["later_key"]), head["reading"]))
        if brand:
            L.append("- Brand campaigns are left out of these readings: %s." % ", ".join(brand))
    for r in auction:
        if r.get("compared") and r["scope"] not in shown:
            moves = [c for c in r["gained"] + r["lost"] if c["large"]] + r["new"]
            L.append("- Auction insights, %s: %s." % (r["scope"], "; ".join(
                "%s %s" % (c["domain"], "new in %s, impression share %s" % (later.key, sh(c["impression_share"]["later"])) if c["status"] == "new"
                           else "impression share %s" % mv(c["impression_share"]["change"])) for c in moves) or "no competitor's impression share moved by a large amount"))
    if season:
        if season.get("readable"):
            pat = season["pattern"]["clicks"]
            L.append("- Seasonality (%s, clicks): rises in %s; falls in %s (%s)." % (GROUP_WORDS[season["group"]], ", ".join(month_name(p, season["kind"]) for p in pat["rise"]) or "no month",
                                                                                 ", ".join(month_name(p, season["kind"]) for p in pat["fall"]) or "no month", pat["rule"]))
            if season["same_period_last_year"]:
                y = season["same_period_last_year"][-1]
                L.append("- %s against %s, %s: cost %s, conversions %s, cost / conv. %s." % (
                    y["period"], y["prior"], GROUP_WORDS[season["group"]], signed(y["change"]["cost"]), signed(y["change"]["conversions"]), signed(y["change"]["cpa"])))
        else:
            L.append("- Seasonality: %s" % season["reason"])
    flags = [c for c in (sov["campaigns"] if sov else []) if c.get("budget_puzzle")]
    for c in flags:
        L.append("- **Does not add up:** %s. See Share of voice." % puzzle_text(c, sov, short=True))
    warnings = sum(len(r.get("identical", [])) for r in auction) + (len(sov["identical"]) if sov else 0)
    if warnings:
        L.append("- **Check the files:** %d measures are exactly the same in every period. See Checks." % warnings)
    L.append("")

    # Auction insights.
    for r in auction:
        L += ["## Auction insights: %s" % r["scope"], ""]
        notes = [p for p in r["periods"] if p["note"]]
        L.append("Periods in the file: %s. %s" % (", ".join(p["period"] for p in r["periods"]),
                                                  " ".join("%s is %s." % (p["period"], p["note"]) for p in notes)))
        if r["scope"] == "Account" and brand:
            L.append("")
            L.append("If the brand campaign was selected when this file was downloaded, its auctions are in these numbers. The report does not split them out.")
        if r.get("identical"):
            L.append("")
            L.append("**Check this file:** these values are exactly the same in every period: %s. Real shares rarely repeat to the decimal, so do not read them as steady. "
                     "Check that the download is segmented by period." % "; ".join("%s %s %s (%d periods)" % (x["domain"], x["measure"].lower(), x["value"], x["periods"]) for x in r["identical"]))
        for n in r["notes"]:
            L.append("")
            L.append(n)
        if not r.get("compared"):
            one = r.get("landscape")
            if one:
                L += ["", "Who you met in the auction in %s, sorted by overlap rate:" % one["period"], ""]
                L.append(outputs.md_table(["Display URL domain"] + [reports.AUCTION_LABELS[k] for k in reports.AUCTION_SHARES],
                                          [[x["domain"]] + [(x[k] or {}).get("shown", "n/a") for k in reports.AUCTION_SHARES] for x in one["rows"]]))
            L.append("")
            continue
        you = r["you"]
        L += ["", "**You:** impression share %s in %s, %s in %s (%s). Top of page rate %s to %s. Abs. top of page rate %s to %s." % (
            (you["impression_share"]["earlier"] or {}).get("shown", "n/a"), earlier.key, (you["impression_share"]["later"] or {}).get("shown", "n/a"), later.key,
            (you["impression_share"]["change"] or {}).get("shown", "n/a"),
            (you["top_of_page_rate"]["earlier"] or {}).get("shown", "n/a"), (you["top_of_page_rate"]["later"] or {}).get("shown", "n/a"),
            (you["abs_top_rate"]["earlier"] or {}).get("shown", "n/a"), (you["abs_top_rate"]["later"] or {}).get("shown", "n/a")), ""]
        L.append("Competitors, sorted by overlap rate in %s. Shares are in %s, with the change since %s in share points (pts)." % (later.key, later.key, earlier.key))
        L.append("")
        table = []
        for c in r["competitors"]:
            table.append([c["domain"] + (" (new)" if c["status"] == "new" else " (not seen in %s)" % later.key if c["status"] == "gone" else ""),
                          sh(c["overlap_rate"]["later"], "not seen"), sh(c["impression_share"]["later"], "not seen"), mv(c["impression_share"]["change"]) + (" (large)" if c["large"] else ""),
                          sh(c["position_above_rate"]["later"], "not seen"), mv(c["position_above_rate"]["change"]),
                          sh(c["outranking_share"]["later"], "not seen"), mv(c["outranking_share"]["change"])])
        L.append(outputs.md_table(["Display URL domain", "Overlap rate", "Impression share", "Change", "Position above rate", "Change", "Outranking share", "Change"], table))
        L.append("")
        recent = [p["period"] for p in r["periods"]][-TIMELINE_PERIODS:]
        notes = {p["period"]: p["note"] for p in r["periods"]}
        order = ["You"] + [c["domain"] for c in r["competitors"]]
        L.append("Impression share by period. A cell marked (partial) covers only part of its period.")
        L.append("")
        L.append(outputs.md_table(["Display URL domain"] + [mark(k, notes[k]) for k in recent],
                                  [[d] + [mark(((r["timeline"].get(d) or {}).get(k) or {}).get("shown", "not seen"), notes[k]) for k in recent] for d in order]))
        L.append("")
        if r["large_move_points"]:
            L.append("A move in impression share of %.1f pts or more is marked large. That is %d times the typical move in this file (%.1f pts, the median change in a competitor's impression share from one period to the next). "
                     "Position above rate uses its own line the same way: %s pts."
                     % (r["large_move_points"], LARGE_FENCE, r["typical_move_points"], num(r["fences"]["position_above_rate"]["large_points"], 1)))
        elif r["large_move_points"] == 0:
            L.append("The typical competitor's impression share did not move from one period to the next in this file, so any move is marked large.")
        else:
            L.append("No move is marked large: the file has too few exact period to period values to set a typical move.")
        L.append("")

        def names(items, key):
            return "; ".join("%s (%s%s)" % (c["domain"], mv(c[key]["change"]), ", large" if c["large_moves"].get(key) else "") for c in items) or "none"
        L.append("- Gained impression share: %s." % names(r["gained"], "impression_share"))
        L.append("- Lost impression share: %s." % names(r["lost"], "impression_share"))
        if r["unclear"]:
            L.append("- Too close to call (banded values): %s." % names(r["unclear"], "impression_share"))
        L.append("- New in %s: %s." % (later.key, "; ".join("%s (impression share %s, overlap rate %s)" % (c["domain"], sh(c["impression_share"]["later"]), sh(c["overlap_rate"]["later"])) for c in r["new"]) or "none"))
        L.append("- Not seen in %s: %s." % (later.key, "; ".join(c["domain"] for c in r["gone"]) or "none"))
        L.append("- Showed above you more often (position above rate rose): %s." % names(r["above_more"], "position_above_rate"))
        L.append("- You outranked them less often (outranking share fell): %s." % names(r["outranked_less"], "outranking_share"))
        side = r.get("campaign_side")
        if side:
            a, b = side["earlier"], side["later"]
            L += ["", "Campaign report for the same scope: %s. **%s.**" % (three(a, b, side, earlier.key, later.key), side["reading"])]
            if side["sis"] and side["sis"].direction == "fell":
                pressing = [c for c in r["above_more"] if c["large_moves"]["position_above_rate"] or c["large"]]
                if pressing or r["new"]:
                    L.append("In the same period these competitors showed above you more often by a large move, or entered: %s." % "; ".join(
                        ["%s (position above rate %s, impression share %s)" % (c["domain"], mv(c["position_above_rate"]["change"]), mv(c["impression_share"]["change"])) for c in pressing]
                        + ["%s (new)" % c["domain"] for c in r["new"]]))
                else:
                    L.append("No competitor's position above rate rose by a large move and none is new, so the auction data does not show a competitor taking this share.")
        L.append("")

    # Share of voice.
    if sov:
        L += ["## Share of voice", ""]
        if camp["lost_source"] == "Search lost IS":
            L.append("Each campaign's Search impr. share, and the share it lost to rank and to budget, %s against %s. Columns read: Search lost IS (rank) and (budget)." % (
                sov["later_key"], sov["earlier_key"] or "no earlier period"))
        else:
            L.append("Each campaign's Search impr. share, %s against %s. The share lost to rank and to budget needs Search lost IS (rank) and "
                     "Search lost IS (budget) in the campaign report.%s" % (
                         sov["later_key"], sov["earlier_key"] or "no earlier period",
                         " The file has Search lost top IS instead, which is the share of top of page impressions lost, a different measure, "
                         "so it is not read as share lost." if camp["lost_source"] == "top only" else ""))
        L.append("")
        table = []
        lines = [(c["campaign"] + (" (brand)" if c["brand"] else ""), c["status"] or "n/a", c["earlier"], c["later"], c["moves"], c["reading"]) for c in sov["campaigns"]]
        lines += [("**%s**" % label, "", line["earlier"], line["later"], line["moves"], line["reading"]) for label, line in sov["account"].items()]
        for name, status, a, b, moves, read in lines:
            a, b = a or {}, b or {}
            row = [name, status]
            for key in ("sis", "lost_rank", "lost_budget"):
                row += [sh(a.get(key)), sh(b.get(key)), mv(moves[key])]
            table.append(row + [read])
        e, l = sov["earlier_key"] or "earlier", sov["later_key"]
        L.append("Shares are in %s and %s; the change is in share points (pts)." % (e, l))
        L.append("")
        L.append(outputs.md_table(["Campaign", "Status", "Search impr. share %s" % e, "Search impr. share %s" % l, "Change", "Lost to rank %s" % e, "Lost to rank %s" % l,
                                   "Change", "Lost to budget %s" % e, "Lost to budget %s" % l, "Change", "Reading"], table))
        L.append("")
        L.append("What the share lost in %s stands for:" % sov["later_key"])
        L.append("")
        for c in sov["campaigns"]:
            if not c["serving"] or not c["later"] or not c["later"].get("sis"):
                L.append("- %s: %s. Left out of the readings." % (c["campaign"], c["reading"]))
                continue
            if c["later"].get("lost_rank") is None and c["later"].get("lost_budget") is None:
                L.append("- %s%s: Search impr. share %s in %s. Impressions missed need the Search lost IS columns. Daily budget %s. Cost %s, conversions %s, cost / conv. %s." % (
                    c["campaign"], " (brand)" if c["brand"] else "", sh(c["later"]["sis"]), sov["later_key"],
                    money(c["budget"]) if c["budget"] is not None else "not in the report", money(c["cost"]["later"]), num(c["conversions"]["later"], 2), money(c["cpa_later"])))
                continue
            equal = (" The two figures are equal because lost to budget and lost to rank are both %s in %s." % (sh(c["later"]["lost_budget"]), sov["later_key"])
                     if c["equal_missed"] else "")
            L.append("- %s%s: about %s impressions missed because of budget and %s because of rank in %s (estimates).%s Daily budget %s. Cost %s, conversions %s, cost / conv. %s." % (
                c["campaign"], " (brand)" if c["brand"] else "", fmt_range(c["missed_budget"]), fmt_range(c["missed_rank"]), sov["later_key"], equal,
                money(c["budget"]) if c["budget"] is not None else "not in the report", money(c["cost"]["later"]), num(c["conversions"]["later"], 2), money(c["cpa_later"])))
        L.append("")
        L.append("Spend beside lost share. Avg. daily cost divides cost by the days the period covers; the Budget column may show today's budget on every row.")
        L.append("")
        table = []
        for c in sov["campaigns"]:
            for d in (c["detail"]["earlier"], c["detail"]["later"]):
                if not d:
                    continue
                table.append([c["campaign"] + (" (brand)" if c["brand"] else ""), mark(d["period"], d["note"]), money(d["cost"]),
                              money(d["budget"]) if d["budget"] is not None else "n/a", money(d["avg_daily_cost"]), metrics.pct(d["budget_used"], 0),
                              money(d["avg_cpc"]), sh(d["sis"]), sh(d["lost_rank"]), sh(d["lost_budget"])])
        L.append(outputs.md_table(["Campaign", "Period", "Cost", "Daily budget", "Avg. daily cost", "Of budget", "Avg. CPC", "Search impr. share", "Lost to rank", "Lost to budget"], table))
        L.append("")
        for c in sov["campaigns"]:
            if c.get("budget_puzzle"):
                L.append("**Does not add up.** %s" % puzzle_text(c, sov))
                L.append("")
        recent = [p.key for p in sov["periods"]][-TIMELINE_PERIODS:]
        notes = sov["period_notes"]
        L.append("Search impr. share by period. A cell marked (partial) covers only part of its period.")
        L.append("")
        L.append(outputs.md_table(["Campaign"] + [mark(k, notes[k]) for k in recent],
                                  [[name + (" (brand)" if name in brand else "")] + [mark(sh(series.get(k)), notes[k]) for k in recent] for name, series in sov["timeline"].items()]))
        L.append("")
    elif camp and not camp["has_share"]:
        L += ["## Share of voice", "", "The campaign report has no Search impr. share column, so share of voice is not read. Add Search impr. share, "
              "Search lost IS (rank) and Search lost IS (budget) to the report and download it again.", ""]

    # Landscape.
    if land:
        L += ["## Competitor landscape", ""]
        L.append("Every domain the auction insights report shows, ranked by its highest overlap rate in %s. Built from the auction data only." % later.key)
        L.append("")
        table = []
        for e in land:
            for s in e["scopes"]:
                if s["seen_in"] == s["of"]:
                    pattern = "in every period"
                elif s["status"] == "gone":
                    pattern = "last seen %s" % s["last_seen"]
                elif s["first_seen"] != s["first_period"]:
                    pattern = "first seen %s" % s["first_seen"]
                else:
                    pattern = "seen in some periods, last %s" % s["last_seen"]
                table.append([e["domain"], s["scope"], "%d of %d" % (s["seen_in"], s["of"]), pattern, sh(s["overlap_rate"], "not seen"), sh(s["impression_share"], "not seen"),
                              sh(s["position_above_rate"], "not seen"), sh(s["outranking_share"], "not seen")])
        L.append(outputs.md_table(["Display URL domain", "Where", "Periods seen", "Pattern", "Overlap rate", "Impression share", "Position above rate", "Outranking share"], table))
        L.append("")

    # Seasonality.
    if season:
        L += ["## Seasonality and trends", ""]
        if season.get("periods"):
            L.append("The campaign report runs from %s to %s: %d complete %s." % (season["first"], season["last"], len(season["complete"]), season.get("unit", "periods")))
            for p in season["partial"]:
                L.append("%s is %s, and is left out of the index and the comparisons." % (p["period"], p["note"]))
            if season["empty_periods"]:
                L.append("These periods have no rows and count as zero: %s." % ", ".join(season["empty_periods"]))
            if season.get("part_year_campaigns"):
                L.append("Campaigns that spent in only part of the last year, and whose cost is in the account lines for those periods: %s." % "; ".join(
                    "%s (%d of %d)" % (c["campaign"], c["active_periods"], c["of"]) for c in season["campaigns"] if c["campaign"] in season["part_year_campaigns"]))
        L.append("")
        if not season.get("readable"):
            L.append("**%s**" % season["reason"])
            L.append("")
        else:
            g = season["group"]
            idx = season["index"][g]
            L.append("Index: 100 is the average %s of the last year, %s to %s, for %s. 130 means 30%% above that average." % (
                season["kind"], season["cycles"][-1][0], season["cycles"][-1][-1], GROUP_WORDS[g]))
            L.append("")
            table = []
            for k in season["cycles"][-1]:
                v, i = season["totals"][g][k], idx["last"][k]
                earlier_idx = None
                if idx["earlier"]:
                    pos = season["cycles"][-1].index(k)
                    earlier_idx = idx["earlier"][season["cycles"][0][pos]]["clicks"]
                table.append([k, money(v["cost"]), num(v["clicks"]), num(v["conversions"], 2), money(v["cpa"]), num(i["cost"]), num(i["clicks"]), num(i["conversions"]),
                              num(i["cpa"]), num(earlier_idx) if idx["earlier"] else "n/a"])
            L.append(outputs.md_table(["Period", "Cost", "Clicks", "Conversions", "Cost / conv.", "Cost index", "Clicks index", "Conv. index", "Cost / conv. index",
                                       "Clicks index a year earlier"], table))
            L.append("")
            for metric in ("clicks", "conversions"):
                pat = season["pattern"][metric]
                L.append("- **%s** usually rise in: %s. Usually fall in: %s. Rule: %s." % (
                    metric.capitalize(), ", ".join(month_name(p, season["kind"]) for p in pat["rise"]) or "no period",
                    ", ".join(month_name(p, season["kind"]) for p in pat["fall"]) or "no period", pat["rule"]))
            if len(season["cycles"]) == 1:
                L.append("- The file covers one year, so a high or low month may be a one off rather than a season. Download 25 months to see whether it repeats.")
            L.append("")
            if season.get("ahead"):
                base = season["ahead"][0]["base"]
                L.append("The %s ahead, read from the same %s a year earlier, %s. \"Then against %s\" is how far that %s moved from %s, "
                         "the %s a year before the latest complete one. It is last year's step, not a forecast." % (
                             season["unit"], season["unit"], GROUP_WORDS[g], base or "n/a", season["kind"], base or "n/a", season["kind"]))
                L.append("")
                L.append(outputs.md_table(
                    ["%s ahead" % season["kind"].capitalize(), "A year earlier", "Clicks usually", "Clicks index then", "Clicks then against %s" % (base or "n/a"),
                     "Cost then against %s" % (base or "n/a"), "Conv. then against %s" % (base or "n/a"), "Lost to budget then"],
                    [[a["period"] + (" (in progress)" if a["in_progress"] else ""), a["prior"], a["usually"], num(a["clicks_index"]),
                      signed(a["step"]["clicks"]), signed(a["step"]["cost"]), signed(a["step"]["conversions"]), sh(a["lost_budget"])] for a in season["ahead"]]))
                L.append("")
            if season["same_period_last_year"]:
                L.append("Same %s last year, %s:" % (season["kind"], GROUP_WORDS[g]))
                L.append("")
                table = []
                for y in season["same_period_last_year"]:
                    table.append([y["period"], money(y["before"]["cost"]), money(y["now"]["cost"]), signed(y["change"]["cost"]), num(y["before"]["conversions"], 2),
                                  num(y["now"]["conversions"], 2), signed(y["change"]["conversions"]), money(y["before"]["cpa"]), money(y["now"]["cpa"]), signed(y["change"]["cpa"]),
                                  sh(y["lost_budget_before"]), sh(y["lost_budget"]), sh(y["lost_rank_before"]), sh(y["lost_rank"])])
                L.append(outputs.md_table(["Period", "Cost a year earlier", "Cost", "Change", "Conv. a year earlier", "Conv.", "Change", "Cost / conv. a year earlier",
                                           "Cost / conv.", "Change", "Lost to budget a year earlier", "Lost to budget", "Lost to rank a year earlier", "Lost to rank"], table))
                L.append("")
            L.append("Each campaign over the last year: its peak and low %s by clicks, and its last %d complete %s against the same %s a year earlier." % (
                season["kind"], RECENT, season["unit"], season["unit"]))
            L.append("")
            table = []
            for c in season["campaigns"]:
                rec = c.get("recent") or {}
                ch = rec.get("change") or {}
                table.append([c["campaign"] + (" (brand)" if c["brand"] else ""), "%d of %d" % (c["active_periods"], c["of"]),
                              "%s (%s)" % (c["peak"], num(c["peak_index"])) if c.get("peak") else "part year", "%s (%s)" % (c["low"], num(c["low_index"])) if c.get("low") else "part year",
                              signed(ch.get("cost")) if rec else "n/a", signed(ch.get("conversions")) if rec else "n/a", signed(ch.get("cpa")) if rec else "n/a"])
            L.append(outputs.md_table(["Campaign", "Periods with spend", "Peak (clicks index)", "Low (clicks index)", "Cost vs a year earlier", "Conv. vs a year earlier",
                                       "Cost / conv. vs a year earlier"], table))
            L.append("")
        if season.get("levers"):
            L += ["## Why conversions moved against the same month last year", ""]
            L.append("Conversions are split into estimated eligible impressions x Search impr. share x click through rate x conversion rate. "
                     "Each factor's share of the change is its part of the whole change; a share above 100% means other factors moved the other way. "
                     "The factor with the largest share moved conversions most.")
            L.append("")
            for x in season["levers"]:
                t, n = x["then"], x["now"]
                L.append("**%s%s**, %s against %s:" % (x["campaign"], " (brand)" if x["brand"] else "", x["period"], x["prior"]))
                L.append("")
                rows_ = [["Impr.", num(t["impressions"]), num(n["impressions"]), signed(metrics.change(n["impressions"], t["impressions"]))],
                         ["Est. eligible impressions", num(t["eligible"]), num(n["eligible"]), signed(metrics.change(n["eligible"], t["eligible"]))],
                         ["Search impr. share", sh(t["sis"]), sh(n["sis"]), mv(move(t["sis"], n["sis"]))],
                         ["Lost to rank", sh(t["lost_rank"]), sh(n["lost_rank"]), mv(move(t["lost_rank"], n["lost_rank"]))],
                         ["Lost to budget", sh(t["lost_budget"]), sh(n["lost_budget"]), mv(move(t["lost_budget"], n["lost_budget"]))],
                         ["Avg. CPC", money(t["avg_cpc"]), money(n["avg_cpc"]), signed(metrics.change(n["avg_cpc"], t["avg_cpc"]))],
                         ["CTR", metrics.pct(t["ctr"], 2), metrics.pct(n["ctr"], 2), signed(metrics.change(n["ctr"], t["ctr"]))],
                         ["Conv. rate", metrics.pct(t["cvr"], 2), metrics.pct(n["cvr"], 2), signed(metrics.change(n["cvr"], t["cvr"]))],
                         ["Conversions", num(t["conversions"], 2), num(n["conversions"], 2), signed(x["conversions_change"])]]
                L.append(outputs.md_table(["Measure", x["prior"], x["period"], "Change"], rows_))
                L.append("")
                if x["levers"]:
                    L.append("Share of the change in conversions: %s. Moved most: **%s**, %s. Split used: %s." % (
                        "; ".join("%s %s" % (LEVER_WORDS[k], metrics.pct(v, 0)) for k, v in x["levers"].items()), LEVER_WORDS[x["main_lever"]],
                        lever_move(x, x["main_lever"]), x["split"]))
                else:
                    L.append("The split cannot be made: a value is zero or missing in one of the months.")
                L.append("")

    # Checks.
    L += ["## Checks", ""]
    if "campaign_report" in checks:
        rc = checks["campaign_report"]
        if rc["matched"]:
            L.append("- The campaign rows add up to the file's own %s (%s): cost %s, clicks %s." % (rc["label"], rc["how"], money(rc["rows"]["cost"]), num(rc["rows"]["clicks"])))
        elif rc["matched"] is False:
            L.append("- The campaign rows do not add up to the file's own %s: the rows hold %s of cost, the total says %s. Some rows may be filtered out of the download."
                     % (rc["label"], money(rc["rows"]["cost"]), money(rc["file"]["cost"])))
        else:
            L.append("- The campaign report has no total row, so its rows could not be checked against one.")
        if checks.get("campaign_unread_rows"):
            L.append("- %d campaign rows had a period I could not read and were left out." % checks["campaign_unread_rows"])
    for line in checks["auction"]:
        if line["periods_without_you_row"]:
            L.append("- Auction insights for %s has no You row in: %s." % (line["scope"], ", ".join(line["periods_without_you_row"])))
        for x in line["against_campaign_report"]:
            L.append("- %s, %s: impression share in auction insights %s, Search impr. share from the campaign report %s (difference %s)." % (
                line["scope"], x["period"], x["auction"].fmt(), x["campaigns"].fmt(), mv(x["difference"])))
    if checks.get("auction_unread_rows"):
        L.append("- %d auction insights rows had a period I could not read and were left out." % checks["auction_unread_rows"])
    for r in auction:
        for x in r.get("identical", []):
            L.append("- Auction insights, %s: %s %s is %s in all %d periods. Real values rarely repeat exactly; check the download." % (
                r["scope"], x["domain"], x["measure"].lower(), x["value"], x["periods"]))
    for x in (sov["identical"] if sov else []):
        L.append("- Campaign report: %s %s is %s in all %d periods. Real values rarely repeat exactly; check the download." % (x["campaign"], x["measure"], x["value"], x["periods"]))
    L.append("")

    # What the run had to assume, for the questions to confirm.
    assumed = []
    if camp and not brand:
        assumed.append("No campaign was named as brand, so every campaign is in the account lines and the headline readings. Is one of the campaigns listed at the top a brand campaign?")
    for f in files:
        if f["scope_source"] == "assumed":
            assumed.append("%s does not say which campaigns it covers, so it was read as the whole account. Which campaigns does it cover?" % os.path.basename(f["path"]))
        elif f["scope_source"] == "given with --scope" and f["title_scope"] and f["title_scope"] != f["scope"]:
            assumed.append("%s was read as %s as given, but its title rows name %s. Which is right?" % (os.path.basename(f["path"]), f["scope"], f["title_scope"]))
    if earlier and later and chosen_by != "chosen by you":
        assumed.append("The comparison is %s against %s, %s. Is that the period in question?" % (later.key, earlier.key, chosen_by))
    if camp:
        assumed.append("Conversions are the report's Conversions column. If the question is about calls or leads, confirm that this column counts them and nothing else.")
    if any(c.get("budget_puzzle") for c in (sov["campaigns"] if sov else [])):
        assumed.append("The Budget column was read as the budget in each period. Did any budget change in the period?")
    if assumed:
        L += ["## What was assumed", ""] + ["- %s" % a for a in assumed] + [""]

    L += ["## How the numbers were made", "",
          "- Shares are shown as Google wrote them. Google writes \"< 10%\" for small values, and that is kept as a band below 10%, never as zero. A change involving a band is shown as a range of share points.",
          "- Official (Google Ads Help): overlap rate is how often another advertiser's ad got an impression when yours did. Position above rate is how often their ad showed in a higher position than yours when both showed. "
          "Outranking share is how often your ad ranked higher than theirs, or showed when theirs did not. Impression share is impressions received divided by the estimated impressions the ads were eligible for.",
          "- Official (Google Ads Help): Search lost IS (rank) is the share of the time ads did not show because of Ad Rank. Search lost IS (budget) is the share of the time they did not show because the budget was not enough.",
          "- The reading for each campaign is arithmetic: when Search impr. share fell, it names the lost column that rose more.",
          "- Account lines combine campaigns by weighting each campaign's shares by its estimated eligible impressions (Impr. divided by Search impr. share). This is an estimate: Impr. can include Search partners, and Search impr. share does not.",
          "- Impressions missed are estimates: estimated eligible impressions times the share lost to budget or to rank.",
          "- \"Does not add up\" is flagged when lost to budget rose while the Budget column stayed the same and average daily cost did not rise.",
          "- The year on year split: conversions = estimated eligible impressions x Search impr. share x click through rate x conversion rate. Each factor's share is its part of the change in the logarithm of conversions, the same split used to compare two periods. With a banded share, impressions replace the first two factors.",
          "- A measure written exactly the same in every period is flagged, because real shares rarely repeat to the decimal.",
          "- The seasonality index divides each period by the average period of the last complete year and multiplies by 100. Cost / conv. index divides each period's cost / conv. by the year's cost / conv.",
          "- Partial periods are left out of the index and of the same period last year, because their totals cover fewer days.", ""]
    L += ["## What this did not cover", "",
          "- Competitors' spend, bids, budgets, Quality Score, ads or strategy. The auction insights report has no column for any of them, so nothing here says what a competitor spends or bids.",
          "- What a competitor's ads say. Their ads can be looked up in Google's Ads Transparency Center.",
          "- Why Search lost IS (rank) moved. Ad Rank depends on bids, ad quality, Ad Rank thresholds, the competition, the search context and the expected impact of assets, so a rise can come from the account's own changes as well as from a competitor.",
          "- Demand outside the account. A season read from the account's own clicks also carries its own budget and bid changes.", ""]
    text = "\n".join(L)
    with open(os.path.join(out, "competitive-and-market.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    return text


if __name__ == "__main__":
    main()
