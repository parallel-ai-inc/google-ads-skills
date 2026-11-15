#!/usr/bin/env python3
"""Step 1 of the performance reviews: read the reports and run every review they allow.

Give it any of the reports this skill reads, in any order. Each file is
recognised by its headers and runs its own review: the weekly review, top and
bottom keywords, Quality Score, ads, devices, landing pages, audiences,
locations, ad schedule, placements and YouTube ads. Every number is decided
here. It prints everything the judgment needs and writes WORK/review.json and
WORK/notes.template.json.

    python3 scripts/review.py REPORT [REPORT ...] --work WORK [--brand "brand, brand name"] [--brand-campaign "Brand"]
"""
import argparse
import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, metrics, outputs  # noqa: E402
import reports as R  # noqa: E402

TITLES = {
    "weekly": "Weekly performance review", "keywords": "Top and bottom keywords", "quality_score": "Quality Score review",
    "ads": "Ad performance", "devices": "Devices", "landing_pages": "Landing pages", "audiences": "Audiences",
    "locations": "Locations", "schedule": "Ad schedule", "placements": "Placements and brand suitability",
    "videos": "YouTube ads", "demand_gen": "Demand Gen",
}
REVIEW_ORDER = ("weekly", "demand_gen", "keywords", "quality_score", "ads", "devices", "landing_pages", "audiences",
                "locations", "schedule", "placements", "videos")
OPEN = {
    "weekly": "playbooks/weekly-performance-review.md, references/daily-optimization.md",
    "demand_gen": "playbooks/demand-gen-review.md, references/demand-gen.md",
    "keywords": "playbooks/keywords-and-quality-score.md",
    "quality_score": "playbooks/keywords-and-quality-score.md, references/quality-score.md",
    "ads": "playbooks/ads-and-landing-pages.md, references/creative.md",
    "devices": "playbooks/segment-splits.md, references/bid-adjustments.md",
    "landing_pages": "playbooks/ads-and-landing-pages.md",
    "audiences": "playbooks/segment-splits.md, references/bid-adjustments.md",
    "locations": "playbooks/segment-splits.md, references/bid-adjustments.md",
    "schedule": "playbooks/segment-splits.md, references/bid-adjustments.md",
    "placements": "playbooks/placements-and-video.md, references/display-video.md",
    "videos": "playbooks/placements-and-video.md, references/display-video.md",
}
SOURCE = {"weekly": "weekly", "demand_gen": "weekly", "keywords": "keywords", "quality_score": "keywords", "ads": "ads", "devices": "devices",
          "landing_pages": "landing_pages", "audiences": "audiences", "locations": "locations", "schedule": "schedule",
          "placements": "placements", "videos": "videos"}
COMPONENTS = (("exp_ctr", "Exp. CTR"), ("ad_relevance", "Ad relevance"), ("landing_page_exp", "Landing page exp."))
SHOW = 12  # rows printed per list; the workbook has every row

RULES = [
    "Every review compares a segment with a baseline from the same file: the cost per conversion and conversion rate of "
    "the rows the review judges. Brand campaigns you name, and paused, removed or ended items, are left out of the "
    "baseline and of the judging, and each review says how many rows that was.",
    "Enough to judge: a segment is judged only once it has spent three times the baseline cost per conversion. At the "
    "baseline it should then have brought 3 conversions, and the chance of none by luck alone is about 5%. Below that "
    "line it is 'Too little data'.",
    "Better or worse: a segment's conversions are compared with what its spend would have bought at the baseline. It "
    "is called better or worse only when chance alone would give a gap that size less than 1 time in 10. 'Main lever' "
    "says whether conversion rate or cost per click moved its cost per conversion more.",
    "Not enough data to judge: the segment's cost per conversion is at least 50% above, or a third below, the baseline, "
    "but its volume cannot show the gap is more than chance. It is listed under 'Worth watching' and is never acted on as proven.",
    "Every verdict prints what it was compared with, by name and value, and the cost per conversion of the other segments "
    "in the same comparison.",
    "Wasted is spend on segments judged 'No conversions': they spent enough to judge and brought none. Less efficient is, "
    "for segments judged 'Worse', the cost above what their conversions would have cost at the baseline. The two are "
    "never added. Spend with no conversions below the line is listed apart and is not called waste.",
    "The same spend sits in several reviews (a click has a device, an hour and a location). Money is never added across "
    "reviews, nor across the account level and the inside campaigns level of one review.",
    "What can act on a finding inside a campaign depends on its bid strategy, from references/bid-adjustments.md (Official).",
]
STRATEGIES = {}  # campaign -> Bid strategy type, from any file that has both columns; filled in main()
ACTS = {
    "devices": {"manual": "Device bid adjustment, -100% to +900%",
                "tcpa": "A device adjustment changes the CPA target for that device; -100% stops the device",
                "smart": "Only -100%, which stops the device; other device adjustments are not supported"},
    "locations": {"manual": "Location bid adjustment, -90% to +900%, or exclude the location",
                  "smart": "No location bid adjustment with this strategy; exclude the location if it is not served"},
    "schedule": {"manual": "Ad schedule bid adjustment, -90% to +900% (needs a custom ad schedule), or change the ad schedule",
                 "smart": "No ad schedule bid adjustment with this strategy; the ad schedule itself still applies"},
    "audiences": {"manual": "Audience bid adjustment, -90% to +900%, or exclude the segment",
                  "smart": "No audience bid adjustment with this strategy; change targeting or exclude the segment"},
}
WATCH_VERDICT = "Not enough data to judge"


# ----- formatting

def m(value):
    return "n/a" if value is None else "{:,.2f}".format(value)


def num(value):
    if value is None:
        return "n/a"
    return "{:,.0f}".format(value) if abs(value - round(value)) < 0.005 else "{:,.2f}".format(value)


def pc(value, digits=1):
    return metrics.pct(value, digits)


def signed(value):
    if value is None:
        return "n/a"
    return ("+" if value >= 0 else "") + "{:.0f}%".format(value * 100)


def r2(value):
    return None if value is None else round(value, 2)


def r4(value):
    return None if value is None else round(value, 4)


def short(text, size=70):
    text = " ".join(str(text or "").split())
    return text if len(text) <= size else text[:size - 3] + "..."


def count(n, singular, plural=None):
    return "%d %s" % (n, singular if n == 1 else (plural or singular + "s"))


def verdict_text(slot):
    return slot["verdict"] + (", %s" % slot["lever"] if slot.get("lever") else "")


# The columns every segment table carries in the workbook: header, value, format.
SEG_COLS = [
    ("Impr.", lambda s: s["impressions"], "int"), ("Clicks", lambda s: s["clicks"], "int"),
    ("Cost", lambda s: r2(s["cost"]), "money"), ("Conversions", lambda s: r2(s["conversions"]), "money"),
    ("CTR", lambda s: r4(s["ctr"]), "pct"), ("Avg. CPC", lambda s: r2(s["cpc"]), "money"),
    ("Conv. rate", lambda s: r4(s["cvr"]), "pct"), ("Cost / conv.", lambda s: r2(s["cpa"]), "money"),
    ("Compared with", lambda s: s.get("against", ""), None),
    ("Its cost / conv.", lambda s: r2(s.get("against_cpa")), "money"), ("Its conv. rate", lambda s: r4(s.get("against_cvr")), "pct"),
    ("Others' cost / conv.", lambda s: r2(s.get("rest_cpa")), "money"),
    ("Cost / conv. vs baseline", lambda s: r4(s.get("vs_cpa")), "pct"),
    ("Conv. rate vs baseline", lambda s: r4(s.get("vs_cvr")), "pct"),
    ("Conversions expected at baseline", lambda s: r2(s.get("expected")), "money"),
    ("Verdict", lambda s: s.get("verdict", ""), None), ("Main lever", lambda s: s.get("lever", ""), None),
    ("Wasted", lambda s: r2(s.get("wasted")) or None, "money"), ("Less efficient", lambda s: r2(s.get("extra")) or None, "money"),
    ("What can act on it", lambda s: s.get("acts", ""), None),
]
PRINT_HEADER = ["Cost", "Conv.", "Cost / conv.", "Conv. rate", "Compared with (cost / conv., conv. rate)", "Cost / conv. vs it",
                "Conv. rate vs it", "Others' cost / conv.", "Verdict", "Wasted", "Less efficient"]


def print_cells(slot):
    against = "%s (%s, %s)" % (short(slot["against"], 34), m(slot.get("against_cpa")), pc(slot.get("against_cvr"))) if slot.get("against") else ""
    return [m(slot["cost"]), num(slot["conversions"]), m(slot["cpa"]), pc(slot["cvr"]), against, signed(slot.get("vs_cpa")),
            signed(slot.get("vs_cvr")), m(slot.get("rest_cpa")) if slot.get("against") else "", verdict_text(slot),
            m(slot["wasted"]) if slot.get("wasted") else "", m(slot["extra"]) if slot.get("extra") else ""]


def compare(slot, base, name):
    """Judge a segment against a baseline, and record what it was compared with and the rest of that baseline."""
    R.judge(slot, base)
    rest = R.blank()
    for field in R.SUMS:
        rest[field] = base[field] - slot[field]
    R.rates(rest)
    slot.update(against=name, against_cpa=base["cpa"], against_cvr=base["cvr"], rest_cpa=rest["cpa"], rest_cvr=rest["cvr"])
    return slot


def strategy_kind(text):
    cell = " ".join((text or "").lower().replace("maximise", "maximize").split())
    if not cell:
        return "unknown"
    if "target cpa" in cell:
        return "tcpa"
    if any(w in cell for w in ("target roas", "maximize conversion", "target impression share")):
        return "smart"
    if "manual cpc" in cell:
        return "manual"
    return "other"


def acts_for(key, campaign):
    """Which adjustments can act on a finding inside this campaign, given its bid strategy."""
    if key not in ACTS:
        return ""
    text = STRATEGIES.get(campaign)
    if not text:
        return "Bid strategy not in the files"
    kind = strategy_kind(text)
    if kind == "other":
        return "%s: not covered by the reference, check in the account" % text
    return "%s: %s" % (text, ACTS[key].get(kind) or ACTS[key]["smart"])


def make_tab(name, lead, slots, lead_of, lead_formats=None):
    """A workbook tab: lead columns, then the segment columns."""
    header = list(lead) + [c[0] for c in SEG_COLS]
    formats = dict(lead_formats or {})
    for index, col in enumerate(SEG_COLS):
        if col[2]:
            formats[len(lead) + index] = col[2]
    rows = [list(lead_of(s)) + [c[1](s) for c in SEG_COLS] for s in slots]
    return {"name": name, "header": header, "rows": rows, "formats": formats}


def base_info(base):
    return {"cost": r2(base["cost"]), "conversions": r2(base["conversions"]), "clicks": base["clicks"],
            "cpa": r2(base["cpa"]), "cvr": r4(base["cvr"]), "cpc": r2(base["cpc"]),
            "line": r2(R.MIN_EXPECTED * base["cpa"]) if base["cpa"] else None}


def base_line(base, scope):
    if not base["cpa"]:
        return "%s have no conversions in this file, so nothing can be judged better or worse. Rows are listed by cost." % scope
    return ("Baseline, %s: cost per conversion %s (cost %s over %s conversions), conversion rate %s. Enough to judge: %s "
            "spent." % (scope, m(base["cpa"]), m(base["cost"]), num(base["conversions"]), pc(base["cvr"]),
                        m(R.MIN_EXPECTED * base["cpa"])))


def money_lines(money, noun, plural):
    lines = ["Wasted: %s on %s that spent enough to judge and brought no conversions." % (m(money["wasted"]), count(money["wasted_count"], noun, plural))
             if money["wasted_count"] else "Wasted: none. No %s spent enough to judge without converting." % noun,
             "Less efficient (not waste, never added to it): %s across %s judged worse." % (m(money["less_efficient"]), count(money["worse_count"], noun, plural))
             if money["worse_count"] else "Less efficient: none. No %s was judged worse." % noun]
    if money["too_early_count"]:
        lines.append("No conversions yet, under the line (not called waste): %s on %s." % (m(money["too_early"]), count(money["too_early_count"], noun, plural)))
    return lines


# ----- rows left out

def split(rows, brand_campaigns, brand_out=True):
    used, paused, brand = [], [], []
    for row in rows:
        if R.stopped(row):
            paused.append(row)
        elif brand_out and (row.get("campaign") or "").strip() in brand_campaigns:
            brand.append(row)
        else:
            used.append(row)
    counts = {"rows": len(rows), "used": len(used), "paused_rows": len(paused), "paused_cost": r2(metrics.total(paused, "cost")),
              "brand_rows": len(brand), "brand_cost": r2(metrics.total(brand, "cost")),
              "no_campaign": bool(brand_campaigns) and brand_out and not any(r.get("campaign") for r in rows)}
    return used, counts


def left_lines(counts):
    parts = ["Rows read: %d. Judged: %d." % (counts["rows"], counts["used"])]
    if counts["paused_rows"]:
        parts.append("Left out, paused, removed or ended (not serving now): %s, cost %s." % (count(counts["paused_rows"], "row"), m(counts["paused_cost"])))
    if counts["brand_rows"]:
        parts.append("Left out, in the brand campaigns you named: %s, cost %s." % (count(counts["brand_rows"], "row"), m(counts["brand_cost"])))
    if counts.get("no_campaign"):
        parts.append("This file has no Campaign column, so brand traffic could not be set apart and sits inside the baseline.")
    return [" ".join(parts)]


# ----- one segment split, at the account level and inside each campaign

def group(rows, label_of, extra_of=None):
    slots, order, unlabeled = {}, [], R.blank()
    for row in rows:
        key = label_of(row)
        if not key:
            R.add(unlabeled, row)
            continue
        slot = slots.get(key)
        if slot is None:
            slot = R.blank(label=key)
            slots[key] = slot
            order.append(key)
        R.add(slot, row)
        if extra_of:
            extra_of(slot, row)
    return [R.rates(slots[k]) for k in order], unlabeled


def dimension(name, rows, label_of, sort_key=None, by_campaign=True, extra_of=None, everyone="all segments", key=""):
    slots, unlabeled = group(rows, label_of, extra_of)
    labeled = [r for r in rows if label_of(r)]
    base = R.total_of(labeled)
    for slot in slots:
        compare(slot, base, everyone)
    slots.sort(key=sort_key or (lambda s: -s["cost"]))
    part = {"name": name, "base": base, "segments": slots, "money": R.money_of(slots), "inner": [], "inner_money": None,
            "unlabeled": {"rows": unlabeled["rows"], "cost": r2(unlabeled["cost"])}}
    campaigns = []
    for row in labeled:
        camp = (row.get("campaign") or "").strip()
        if camp and camp not in campaigns:
            campaigns.append(camp)
    for slot in slots:
        slot["acts"] = acts_for(key, campaigns[0] if len(campaigns) == 1 else "") if len(campaigns) <= 1 else (
            "Depends on each campaign's bid strategy; see inside campaigns" if key in ACTS else "")
    if by_campaign and len(campaigns) > 1:
        for camp in campaigns:
            inside = [r for r in labeled if (r.get("campaign") or "").strip() == camp]
            cbase = R.total_of(inside)
            cslots, _ = group(inside, label_of, extra_of)
            for slot in cslots:
                slot["campaign"] = camp
                compare(slot, cbase, camp)
                slot["acts"] = acts_for(key, camp)
            cslots.sort(key=sort_key or (lambda s: -s["cost"]))
            part["inner"] += cslots
        part["inner_money"] = R.money_of(part["inner"])
    return part


def judged_first(slots):
    """Segments judged better, worse or with no conversions, by the money at stake."""
    hits = [s for s in slots if s["verdict"] in ("Worse", "No conversions", "Better")]
    return sorted(hits, key=lambda s: (s["verdict"] == "Better", -(s.get("wasted") or s.get("extra") or 0), -s["cost"]))


IDENTICAL_MIN_CLICKS = 10   # below this, real rows repeat by chance (a long tail of placements at one click and 0.01)


def identical(slots):
    """Groups of three or more segments with exactly the same cost, clicks and conversions.

    Only segments with enough clicks count: on a real download hundreds of
    placements share one click and a cent of cost, which says nothing about
    the file.
    """
    groups = {}
    for slot in slots:
        if slot["cost"] > 0 and slot["clicks"] >= IDENTICAL_MIN_CLICKS:
            groups.setdefault((round(slot["cost"], 2), round(slot["conversions"], 2), slot["clicks"]), []).append(slot["label"])
    return [names for names in groups.values() if len(names) >= 3]


def watch_table(slots, label_header, title="Worth watching: a wide gap the volume cannot prove yet"):
    watch = sorted([s for s in slots if s["verdict"] == WATCH_VERDICT], key=lambda s: -s["cost"])
    acts = any(s.get("acts") for s in watch)
    return {"title": title, "header": ["Scope", label_header] + PRINT_HEADER + (["What can act on it"] if acts else []),
            "rows": [[short(s.get("campaign") or "Account", 40), short(s["label"])] + print_cells(s) + ([s.get("acts", "")] if acts else [])
                     for s in watch[:SHOW]]}


def part_output(part, noun, plural, label_header, show_all=True):
    """Facts, tables and money for one segment split."""
    facts, tables = [base_line(part["base"], "all %s judged" % plural)], []
    facts += ["Account level. " + line for line in money_lines(part["money"], noun, plural)]
    for names in identical(part["segments"]):
        facts.append("Check the export: %s have identical cost, clicks and conversions (%s). Real accounts rarely repeat "
                     "figures exactly, so the file may be a sample, a copy or a broken download."
                     % (count(len(names), noun, plural), ", ".join(short(n, 30) for n in names[:8])))
    shown = part["segments"] if show_all else judged_first(part["segments"])
    acts = any(s.get("acts") for s in part["segments"] + part["inner"])
    tables.append({"title": "%s, against the account baseline" % part["name"],
                   "header": [label_header] + PRINT_HEADER + (["What can act on it"] if acts else []),
                   "rows": [[short(s["label"])] + print_cells(s) + ([s.get("acts", "")] if acts else []) for s in shown[:SHOW * 2]]})
    if part["inner_money"]:
        facts += ["Inside campaigns, each %s against its own campaign's baseline. " % noun + line
                  for line in money_lines(part["inner_money"], "%s in a campaign" % noun, "%s in campaigns" % plural)]
        hits = judged_first(part["inner"])
        if hits:
            tables.append({"title": "%s inside campaigns, judged against their own campaign" % part["name"],
                           "header": ["Campaign", label_header] + PRINT_HEADER + (["What can act on it"] if acts else []),
                           "rows": [[short(s["campaign"], 40), short(s["label"])] + print_cells(s) + ([s.get("acts", "")] if acts else [])
                                    for s in hits[:SHOW]]})
    watch = watch_table(part["segments"] + part["inner"], label_header)
    if watch["rows"]:
        tables.append(watch)
    if part["unlabeled"]["rows"]:
        facts.append("%s had no %s and were left out (cost %s)." % (count(part["unlabeled"]["rows"], "row"), noun, m(part["unlabeled"]["cost"])))
    return facts, tables


def part_tab_rows(part, extra_cols=()):
    rows = [("All campaigns", "Account") + tuple(s.get(c, "") for c in extra_cols) + (s["label"],) for s in part["segments"]]
    rows += [(s["campaign"], "Inside campaign") + tuple(s.get(c, "") for c in extra_cols) + (s["label"],) for s in part["inner"]]
    return rows, part["segments"] + part["inner"]


def part_json(part):
    keep = ("label", "campaign", "impressions", "clicks", "cost", "conversions", "conv_value", "cpa", "cvr", "cpc", "ctr",
            "vs_cpa", "vs_cvr", "expected", "verdict", "lever", "wasted", "extra", "against", "against_cpa", "against_cvr",
            "rest_cpa", "acts")

    def slim(s):
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items() if k in keep or k.startswith("x_")}
    return {"name": part["name"], "baseline": base_info(part["base"]), "money": part["money"], "inner_money": part["inner_money"],
            "segments": [slim(s) for s in part["segments"]], "inside_campaigns": [slim(s) for s in part["inner"]],
            "unlabeled": part["unlabeled"]}


def simple_review(key, report, rows, brand, name, noun, plural, label_of, label_header, sort_key=None, by_campaign=True,
                  extra_of=None, extra_cols=(), extra_headers=(), more_facts=None):
    used, counts = split(rows, brand)
    part = dimension(name, used, label_of, sort_key, by_campaign, extra_of, "all %s" % plural, key)
    facts, tables = part_output(part, noun, plural, label_header)
    if more_facts:
        facts += more_facts(part)
    tab_lead, slots = part_tab_rows(part, extra_cols)
    tab = make_tab(TITLES[key], ["Scope", "Level"] + list(extra_headers) + [label_header], slots, lambda s: (),)
    tab["rows"] = [list(lead) + row for lead, row in zip(tab_lead, tab["rows"])]
    return {"left_out": left_lines(counts), "counts": counts, "facts": facts, "tables": tables, "tabs": [tab],
            "money": {"account": part["money"], "inside_campaigns": part["inner_money"]}, "baseline": base_info(part["base"]),
            "data": part_json(part)}


# ----- the weekly review

LEVER_NAMES = {"impressions": "how often ads showed", "clicks": "clicks", "ctr": "click through rate", "cvr": "conversion rate"}


def lever_value(lever, value):
    return num(value) if lever in ("impressions", "clicks") else pc(value)


def shift_day(subset, start, end, lever):
    """The day that best splits one lever's daily series into before and after, with the average of each side."""
    daily = {}
    for day, row in subset:
        if start <= day <= end:
            R.add(daily.setdefault(day, R.blank()), row)
    series, day = [], start
    while day <= end:
        s = daily.get(day)
        if s:
            point = {"impressions": s["impressions"], "clicks": s["clicks"], "ctr": metrics.div(s["clicks"], s["impressions"]),
                     "cvr": metrics.div(s["conversions"], s["clicks"])}[lever]
            if point is not None:
                series.append((day, point))
        day += datetime.timedelta(days=1)
    best, best_score = None, 0.0
    for cut in range(3, len(series) - 2):
        before, after = [v for _, v in series[:cut]], [v for _, v in series[cut:]]
        gap = abs(sum(after) / len(after) - sum(before) / len(before))
        score = gap * (len(before) * len(after) / float(len(series))) ** 0.5
        if score > best_score:
            best, best_score = (series[cut][0], sum(before) / len(before), sum(after) / len(after)), score
    return {"day": best[0].isoformat(), "before": best[1], "after": best[2]} if best else None

def review_weekly(name, meta, rows, brand):
    dated, undated = [], 0
    for row in rows:
        day = dates.parse_day(row.get("day"))
        if day is None:
            undated += 1
        else:
            dated.append((day, row))
    if not dated:
        raise SystemExit("The campaign report segmented by Day (%s) has no dates in its Day column. Download it again "
                         "segmented by Day." % name)
    period = R.period_of(meta)
    first, last_seen = min(d for d, _ in dated), max(d for d, _ in dated)
    start = dates.parse_day(period["start"]) if period else first
    end = dates.parse_day(period["end"]) if period else last_seen
    if (end - start).days + 1 < 14:
        raise SystemExit("The weekly review needs at least 14 days segmented by Day. %s covers %d days, %s to %s. Download "
                         "the campaign report again for the last 14 days or more (28 for the trend), segmented by Day."
                         % (name, (end - start).days + 1, start.isoformat(), end.isoformat()))
    delta = datetime.timedelta
    last, prior = (end - delta(days=6), end), (end - delta(days=13), end - delta(days=7))

    def window(lo, hi, subset):
        return R.total_of([r for d, r in subset if lo <= d <= hi])

    campaigns, status = [], {}
    for _, row in dated:
        camp = (row.get("campaign") or "").strip()
        if camp not in status:
            campaigns.append(camp)
            status[camp] = ""
        if not status[camp]:
            status[camp] = R.stopped(row) or ("enabled" if (row.get("campaign_status") or row.get("status")) else "")

    def line(scope, subset, flag="", now=""):
        a, b = window(last[0], last[1], subset), window(prior[0], prior[1], subset)
        R.judge(a, b)
        a.update(against="week before", against_cpa=b["cpa"], against_cvr=b["cvr"])
        parts = ("impressions", "ctr", "cvr") if a["impressions"] and b["impressions"] else ("clicks", "cvr")
        levers = metrics.log_shares({k: a[k] for k in parts}, {k: b[k] for k in parts})
        main = max(levers, key=lambda k: abs(levers[k])) if levers else None
        return {"scope": scope, "brand": flag, "status": now, "last": a, "prior": b, "levers": levers, "main_lever": main,
                "shift": shift_day(subset, prior[0], last[1], main) if main else None,
                "cost_change": metrics.change(a["cost"], b["cost"]), "conv_change": metrics.change(a["conversions"], b["conversions"]),
                "conv_delta": a["conversions"] - b["conversions"], "cost_delta": a["cost"] - b["cost"],
                "cpa_change": metrics.change(a["cpa"], b["cpa"]), "cvr_change": metrics.change(a["cvr"], b["cvr"]),
                "clicks_change": metrics.change(a["clicks"], b["clicks"]), "value_change": metrics.change(a["conv_value"], b["conv_value"])}

    lines = [line("Account", dated)]
    if brand:
        lines.append(line("Without brand", [(d, r) for d, r in dated if (r.get("campaign") or "").strip() not in brand]))
        lines.append(line("Brand campaigns", [(d, r) for d, r in dated if (r.get("campaign") or "").strip() in brand], "Brand"))
    per = [line(c, [(d, r) for d, r in dated if (r.get("campaign") or "").strip() == c], "Brand" if c in brand else "",
                {"paused": "Paused now", "removed": "Removed now", "ended": "Ended"}.get(status[c], "Enabled" if status[c] else ""))
           for c in campaigns]
    per.sort(key=lambda l: -abs(l["conv_delta"]))
    trend = []
    for i in range(4):
        hi = end - delta(days=7 * i)
        lo = hi - delta(days=6)
        if lo < start:
            break
        slot = window(lo, hi, dated)
        trend.append({"from": lo.isoformat(), "to": hi.isoformat(), "cost": r2(slot["cost"]), "clicks": slot["clicks"],
                      "conversions": r2(slot["conversions"]), "cpa": r2(slot["cpa"]), "cvr": r4(slot["cvr"]),
                      "conv_value": r2(slot["conv_value"])})
    days_with_rows = {k: len({d for d, _ in dated if lo <= d <= hi}) for k, (lo, hi) in (("last", last), ("prior", prior))}

    acc = lines[0]
    facts = ["Last 7 days, %s to %s, against the 7 before, %s to %s." % (last[0], last[1], prior[0], prior[1])]
    for l in lines:
        a, b = l["last"], l["prior"]
        facts.append("%s: cost %s (was %s, %s). Conversions %s (was %s, %s). Cost / conv. %s (was %s, %s). Conv. rate %s (was %s). "
                     "Clicks %s (was %s).%s Cost per conversion against the week before: %s."
                     % (l["scope"], m(a["cost"]), m(b["cost"]), signed(l["cost_change"]), num(a["conversions"]), num(b["conversions"]),
                        signed(l["conv_change"]), m(a["cpa"]), m(b["cpa"]), signed(l["cpa_change"]), pc(a["cvr"]), pc(b["cvr"]),
                        num(a["clicks"]), num(b["clicks"]),
                        (" Conv. value %s (was %s, %s)." % (m(a["conv_value"]), m(b["conv_value"]), signed(l["value_change"])))
                        if a["conv_value"] or b["conv_value"] else "", verdict_text(a)))
    facts.append("The change in conversions, by campaign, adds up to the account's change of %s: %s." % (
        num(acc["conv_delta"]), "; ".join("%s %s" % (l["scope"], ("+" if l["conv_delta"] >= 0 else "") + num(l["conv_delta"])) for l in per)))
    facts.append("The change in cost, by campaign, adds up to the account's change of %s: %s." % (
        m(acc["cost_delta"]), "; ".join("%s %s" % (l["scope"], ("+" if l["cost_delta"] >= 0 else "") + m(l["cost_delta"]))
                                        for l in sorted(per, key=lambda l: -abs(l["cost_delta"])))))
    moved = [l for l in lines if l["scope"] != "Brand campaigns"] + [l for l in per if l["last"]["verdict"] in ("Better", "Worse", "No conversions")]
    if len(moved) == len([l for l in lines if l["scope"] != "Brand campaigns"]) and per:
        moved.append(per[0])
    for l in moved:
        if not l["levers"]:
            continue
        shares = ", ".join("%s %s" % (LEVER_NAMES[k], pc(v, 0)) for k, v in l["levers"].items())
        shift = l["shift"]
        when = (" Its daily %s shifted on %s: it averaged %s a day before that day and %s from then on." % (
            LEVER_NAMES[l["main_lever"]], shift["day"], lever_value(l["main_lever"], shift["before"]),
            lever_value(l["main_lever"], shift["after"]))) if shift else " No single day splits its daily series clearly."
        facts.append("%s: the change in conversions splits as %s (shares of the change, rounded). Main lever: %s.%s"
                     % (l["scope"], shares, LEVER_NAMES[l["main_lever"]], when))
    stopped = [l for l in per if l["status"] in ("Paused now", "Removed now", "Ended")]
    for l in stopped:
        facts.append("%s is %s. It spent %s in the week before and %s in the last 7 days. Its drop is not a loss to fix."
                     % (l["scope"], l["status"].lower(), m(l["prior"]["cost"]), m(l["last"]["cost"])))
    for key, label in (("last", "last 7 days"), ("prior", "7 days before")):
        if days_with_rows[key] < 7:
            facts.append("Only %d of the %s have rows. Days with no row had no impressions, or the file is incomplete."
                         % (days_with_rows[key], label))
    if first > start:
        facts.append("The first row is dated %s, after the report's start, %s. Earlier days had no impressions." % (first, start))
    if undated:
        facts.append("%d rows had no date in the Day column and were left out." % undated)
    if "campaign_type" not in meta["columns"]:
        facts.append("This file has no Campaign type column, so a Demand Gen campaign in it gets no review of its own. "
                     "Add Campaign type (and Budget, and Target CPA if one is set) to the campaign report.")
    facts.append("The last days can still gain conversions that are reported late, so the last 7 days may rise.")
    if len(trend) < 4:
        facts.append("The file covers %d full weeks, so the trend shows %d. 28 days or more gives four." % (len(trend), len(trend)))

    def row_cells(l):
        a, b = l["last"], l["prior"]
        return [short(l["scope"], 40), l["status"] or l["brand"], m(a["cost"]), m(b["cost"]), signed(l["cost_change"]),
                num(a["conversions"]), num(b["conversions"]), ("+" if l["conv_delta"] >= 0 else "") + num(l["conv_delta"]),
                m(a["cpa"]), m(b["cpa"]), verdict_text(a)]
    head = ["Scope", "Status", "Cost, last 7", "Cost, prior 7", "Change", "Conv., last 7", "Conv., prior 7", "Conv. change",
            "Cost / conv., last 7", "Cost / conv., prior 7", "Cost / conv. against the week before"]
    tables = [{"title": "Account and campaigns, last 7 days against the 7 before", "header": head,
               "rows": [row_cells(l) for l in lines + per]},
              {"title": "Trend, 7 days at a time, newest first", "header": ["From", "To", "Cost", "Clicks", "Conv.", "Cost / conv.", "Conv. rate"],
               "rows": [[t["from"], t["to"], m(t["cost"]), num(t["clicks"]), num(t["conversions"]), m(t["cpa"]), pc(t["cvr"])] for t in trend]}]
    tab_head = ["Scope", "Brand", "Status now", "Cost, last 7", "Cost, prior 7", "Cost change", "Clicks, last 7", "Clicks, prior 7",
                "Conversions, last 7", "Conversions, prior 7", "Conversions change", "Conv. rate, last 7", "Conv. rate, prior 7",
                "Cost / conv., last 7", "Cost / conv., prior 7", "Cost / conv. change", "Conv. value, last 7", "Conv. value, prior 7",
                "Cost / conv. against the week before"]
    fmt = {3: "money", 4: "money", 5: "pct", 6: "int", 7: "int", 8: "money", 9: "money", 10: "money", 11: "pct", 12: "pct",
           13: "money", 14: "money", 15: "pct", 16: "money", 17: "money"}
    tab_rows = [[l["scope"], l["brand"], l["status"], r2(l["last"]["cost"]), r2(l["prior"]["cost"]), r4(l["cost_change"]),
                 l["last"]["clicks"], l["prior"]["clicks"], r2(l["last"]["conversions"]), r2(l["prior"]["conversions"]), r2(l["conv_delta"]),
                 r4(l["last"]["cvr"]), r4(l["prior"]["cvr"]), r2(l["last"]["cpa"]), r2(l["prior"]["cpa"]), r4(l["cpa_change"]),
                 r2(l["last"]["conv_value"]), r2(l["prior"]["conv_value"]), verdict_text(l["last"])] for l in lines + per]
    trend_tab = {"name": "Weekly trend", "header": ["From", "To", "Cost", "Clicks", "Conversions", "Cost / conv.", "Conv. rate", "Conv. value"],
                 "rows": [[t["from"], t["to"], t["cost"], t["clicks"], t["conversions"], t["cpa"], t["cvr"], t["conv_value"]] for t in trend],
                 "formats": {2: "money", 3: "int", 4: "money", 5: "money", 6: "pct", 7: "money"}}

    def slim(l):
        keep = ("cost", "clicks", "impressions", "conversions", "conv_value", "cpa", "cvr", "ctr", "cpc")
        return {"scope": l["scope"], "brand": l["brand"], "status": l["status"],
                "last": {k: r4(l["last"][k]) for k in keep}, "prior": {k: r4(l["prior"][k]) for k in keep},
                "conv_delta": r2(l["conv_delta"]), "cost_delta": r2(l["cost_delta"]), "cost_change": r4(l["cost_change"]),
                "conv_change": r4(l["conv_change"]), "cpa_change": r4(l["cpa_change"]), "verdict": l["last"]["verdict"],
                "levers": {k: r4(v) for k, v in (l["levers"] or {}).items()}, "main_lever": l["main_lever"],
                "shift": dict(l["shift"], before=r4(l["shift"]["before"]), after=r4(l["shift"]["after"])) if l["shift"] else None}
    return {"left_out": ["Rows read: %d. Every row counts here, paused campaigns too, because this review reports what "
                         "happened. Paused campaigns are named." % len(rows)],
            "counts": {"rows": len(rows), "used": len(dated), "undated": undated},
            "facts": facts, "tables": tables, "money": None,
            "pointer": "For why it moved, the performance diagnosis skill splits the change by lever (how often ads showed, "
                       "click through rate, cost per click, conversion rate), finds the day it started and lines up the "
                       "account changes made before it. It reads this same file.",
            "tabs": [{"name": TITLES["weekly"], "header": tab_head, "rows": tab_rows, "formats": fmt}, trend_tab],
            "baseline": {"rule": "Each line's last 7 days are judged against its own 7 days before."},
            "data": {"last": [last[0].isoformat(), last[1].isoformat()], "prior": [prior[0].isoformat(), prior[1].isoformat()],
                     "lines": [slim(l) for l in lines], "campaigns": [slim(l) for l in per], "trend": trend,
                     "days_with_rows": days_with_rows}}


# ----- Demand Gen

DG_RULE = ("Google's Demand Gen guide asks for at least 50 conversions before moving from Maximize conversions to Target CPA "
           "or Target ROAS, 30 to 50 conversions after a change before judging it, a daily budget of at least 10 times the "
           "target CPA, and bid changes of 5% to 10% a week, never more than 15% (references/demand-gen.md, Official).")


def conv_band(n):
    return "under 30" if n < 30 else "30 to 50" if n < 50 else "50 or more"


def review_demand_gen(name, meta, rows):
    """Each Demand Gen campaign in the campaign report by Day, read across the whole file. None when there is none."""
    camps = []
    for row in rows:
        camp = (row.get("campaign") or "").strip()
        if camp and "demand gen" in (row.get("campaign_type") or "").lower() and camp not in camps:
            camps.append(camp)
    dated = [(dates.parse_day(r.get("day")), r) for r in rows if (r.get("campaign") or "").strip() in camps]
    dated = sorted([(d, r) for d, r in dated if d is not None], key=lambda p: p[0])
    if not dated:
        return None
    period = R.period_of(meta)
    start = dates.parse_day(period["start"]) if period else dated[0][0]
    end = dates.parse_day(period["end"]) if period else dated[-1][0]
    days = (end - start).days + 1
    delta = datetime.timedelta
    has_budget, has_target = "budget" in meta["columns"], "target_cpa" in meta["columns"]
    facts, data = [DG_RULE], []
    for camp in camps:
        mine = [(d, r) for d, r in dated if (r.get("campaign") or "").strip() == camp]
        whole, latest = R.total_of([r for _, r in mine]), mine[-1][1]
        weeks = []
        for i in range(4):
            hi = end - delta(days=7 * i)
            if hi - delta(days=6) < start:
                break
            weeks.append(R.total_of([r for d, r in mine if hi - delta(days=6) <= d <= hi])["conversions"])
        budget = latest.get("budget") if has_budget else None
        target = latest.get("target_cpa") if has_target else None
        item = {"campaign": camp, "status": {"paused": "Paused now", "removed": "Removed now", "ended": "Ended"}.get(R.stopped(latest), "Enabled"),
                "bid_strategy": STRATEGIES.get(camp, ""), "days": len({d for d, _ in mine}), "cost": r2(whole["cost"]),
                "conversions": r2(whole["conversions"]), "cpa": r2(whole["cpa"]), "conv_by_week": [r2(w) for w in weeks],
                "budget": r2(budget), "target_cpa": r2(target), "budget_per_target": r2(metrics.div(budget, target)),
                "budget_per_cpa": r2(metrics.div(budget, whole["cpa"])), "band": conv_band(whole["conversions"])}
        data.append(item)
        line = ("%s (%s, %s): %s conversions on %d days with rows (the file covers %d), %s; cost %s, cost / conv. %s. "
                "Conversions by week, newest first: %s."
                % (camp, item["status"].lower(), item["bid_strategy"] or "no bid strategy in the file", num(whole["conversions"]),
                   item["days"], days, item["band"], m(whole["cost"]), m(whole["cpa"]), ", ".join(num(w) for w in weeks) or "none"))
        if budget is None:
            line += " No Budget column, so the budget rule cannot be checked here."
        elif target:
            line += (" Daily budget %s on the last day is %s times the Target CPA of %s; 10 times would be %s."
                     % (m(budget), num(item["budget_per_target"]), m(target), m(target * 10)))
        elif whole["cpa"]:
            line += (" Daily budget %s on the last day is %s times its cost per conversion in the file; 10 times would be %s. %s, "
                     "so that is the nearest check against the 10 times rule." % (m(budget), num(item["budget_per_cpa"]), m(whole["cpa"] * 10),
                                                                                 "No Target CPA is set" if has_target else "No Target CPA column"))
        else:
            line += " Daily budget %s on the last day. No conversions, so the budget rule cannot be checked." % m(budget)
        if target:
            line += (" A weekly Target CPA step of 5%% to 10%% is %s to %s; 15%% is %s."
                     % (m(target * 0.05), m(target * 0.10), m(target * 0.15)))
        facts.append(line)
    if period and dated[0][0] > start:
        facts.append("The first Demand Gen row is dated %s, after the report's start, %s. A new or migrated campaign has less "
                     "history than the file." % (dated[0][0], start))
    head = ["Campaign", "Status", "Bid strategy", "Days with rows", "Cost", "Conv.", "Cost / conv.", "Conv. by week, newest first",
            "Daily budget", "Target CPA", "Budget / Target CPA", "Budget / cost per conv."]
    cells = [[short(d["campaign"], 40), d["status"], d["bid_strategy"], d["days"], m(d["cost"]), num(d["conversions"]), m(d["cpa"]),
              ", ".join(num(w) for w in d["conv_by_week"]), m(d["budget"]), m(d["target_cpa"]), num(d["budget_per_target"]),
              num(d["budget_per_cpa"])] for d in data]
    tab_rows = [[d["campaign"], d["status"], d["bid_strategy"], d["days"], d["cost"], d["conversions"], d["cpa"],
                 ", ".join(num(w) for w in d["conv_by_week"]), d["budget"], d["target_cpa"], d["budget_per_target"], d["budget_per_cpa"]]
                for d in data]
    return {"left_out": ["Rows read: %d, for %s. Each is read across the whole file, paused ones too." % (len(dated), count(len(camps), "Demand Gen campaign"))],
            "counts": {"rows": len(dated), "campaigns": len(camps)}, "facts": facts, "money": None,
            "tables": [{"title": "Demand Gen campaigns across the whole file", "header": head, "rows": cells}],
            "tabs": [{"name": TITLES["demand_gen"], "header": head, "rows": tab_rows,
                      "formats": {3: "int", 4: "money", 5: "money", 6: "money", 8: "money", 9: "money", 10: "money", 11: "money"}}],
            "baseline": {"rule": "Each Demand Gen campaign is read on its own, against Google's Demand Gen thresholds."},
            "data": {"campaigns": data}}


# ----- keywords and Quality Score

def rating(text):
    cell = " ".join((text or "").replace("_", " ").lower().split())
    if cell.startswith("below"):
        return "Below average"
    if cell.startswith("above"):
        return "Above average"
    if cell == "average":
        return "Average"
    return None


def keyword_slots(rows, phrases, brand):
    merged, order, negatives = {}, [], 0
    for row in rows:
        text = (row.get("keyword") or "").strip()
        if not text:
            continue
        if text.startswith("-"):
            negatives += 1
            continue
        clean, match = R.keyword_parts(text, row.get("match_type"))
        key = ((row.get("campaign") or "").strip(), (row.get("ad_group") or "").strip(), clean, match)
        slot = merged.get(key)
        if slot is None:
            slot = R.blank(campaign=key[0], ad_group=key[1], label=text, text=clean, match=match, stop="", qs=None,
                           exp_ctr=None, ad_relevance=None, landing_page_exp=None, final_url=(row.get("final_url") or "").strip())
            merged[key] = slot
            order.append(key)
        R.add(slot, row)
        slot["stop"] = slot["stop"] or R.stopped(row)
        if slot["qs"] is None and row.get("quality_score") is not None:
            slot["qs"] = row["quality_score"]
        for field, _ in COMPONENTS:
            slot[field] = slot[field] or rating(row.get(field))
    slots = [R.rates(merged[k]) for k in order]
    for slot in slots:
        slot["brand"] = slot["campaign"] in brand or R.is_brand(slot["text"], phrases)
        slot["role"] = "Paused or removed" if slot["stop"] else "Brand" if slot["brand"] else "Judged"
    return slots, negatives


def review_keywords(name, meta, rows, phrases, brand):
    slots, negatives = keyword_slots(rows, phrases, brand)
    judged = [s for s in slots if s["role"] == "Judged"]
    base = R.total_of(judged)
    for slot in judged:
        compare(slot, base, "non brand keywords")
    for slot in slots:
        if slot["role"] != "Judged":
            slot.update(verdict="Left out: %s" % slot["role"].lower(), expected=None, vs_cpa=None, vs_cvr=None, lever="", wasted=0.0, extra=0.0)
    money = R.money_of(judged)
    paused = [s for s in slots if s["role"] == "Paused or removed"]
    branded = [s for s in slots if s["role"] == "Brand"]
    counts = {"rows": len(rows), "keywords": len(slots), "judged": len(judged), "paused": len(paused),
              "paused_cost": r2(metrics.total(paused, "cost")), "brand": len(branded), "brand_cost": r2(metrics.total(branded, "cost")),
              "negative_rows": negatives}
    left = ["Rows read: %d, %d keywords. Judged: %d. Left out, paused or removed: %d (cost %s). Left out, brand: %d (cost %s)."
            % (len(rows), len(slots), len(judged), len(paused), m(counts["paused_cost"]), len(branded), m(counts["brand_cost"]))]
    if negatives:
        left.append("%s negative keywords and were not counted." % ("1 row is" if negatives == 1 else "%d rows are" % negatives))
    if "clicks" in meta["columns"] and meta["columns"]["clicks"].strip().lower() == "interactions":
        left.append("This file has Interactions, not Clicks. Interactions were counted as clicks.")
    if branded:
        b = R.total_of(branded)
        left.append("Brand keywords: cost %s, %s conversions, cost / conv. %s. Kept out of the baseline so they do not pull it down."
                    % (m(b["cost"]), num(b["conversions"]), m(b["cpa"])))

    facts = [base_line(base, "every enabled non brand keyword")] + money_lines(money, "keyword", "keywords")
    spending = sorted([s for s in judged if s["cost"] > 0], key=lambda s: -s["cost"])
    if spending:
        top10 = sum(s["cost"] for s in spending[:10])
        running, needed = 0.0, 0
        for s in spending:
            running += s["cost"]
            needed += 1
            if running >= 0.8 * base["cost"]:
                break
        facts.append("Spend concentration: %d judged keywords spent. The 10 largest took %s of their cost; %d keywords make up 80%% of it."
                     % (len(spending), pc(metrics.div(top10, base["cost"])), needed))
    winners = sorted([s for s in judged if s["verdict"] == "Better"], key=lambda s: -s["conversions"])
    converters = sorted([s for s in judged if s["conversions"] > 0], key=lambda s: -s["conversions"])
    nothing = sorted([s for s in judged if s["conversions"] <= 0 and s["cost"] > 0], key=lambda s: -s["cost"])
    worse = sorted([s for s in judged if s["verdict"] == "Worse"], key=lambda s: -s["extra"])
    by_match = {}
    for slot in judged:
        R.add(by_match.setdefault(slot["match"], R.blank(label=slot["match"].capitalize())), slot)
    matches = [compare(R.rates(s), base, "non brand keywords") for s in sorted(by_match.values(), key=lambda s: -s["cost"])]

    head = ["Keyword", "Campaign", "Ad group"] + PRINT_HEADER

    def cells(s):
        return [short(s["label"], 40), short(s["campaign"], 30), short(s["ad_group"], 30)] + print_cells(s)
    tables = [
        {"title": "Keyword winners: better than the baseline, by conversions" if winners else
                  "Most conversions (none is better than the baseline beyond chance)",
         "header": head, "rows": [cells(s) for s in (winners or converters)[:SHOW]]},
        {"title": "Keywords with cost and no conversions, by cost", "header": head, "rows": [cells(s) for s in nothing[:SHOW]]},
        {"title": "Keywords that cost more per conversion than the baseline, by the extra cost", "header": head,
         "rows": [cells(s) for s in worse[:SHOW]]},
        {"title": "Worth watching: a wide gap the volume cannot prove yet", "header": head,
         "rows": [cells(s) for s in sorted([s for s in judged if s["verdict"] == WATCH_VERDICT], key=lambda s: -s["cost"])[:SHOW]]},
        {"title": "By match type", "header": ["Match type"] + PRINT_HEADER, "rows": [[s["label"]] + print_cells(s) for s in matches]},
    ]
    qs_cols = [c for c in ("qs",) + tuple(f for f, _ in COMPONENTS) if any(s.get(c) for s in slots)]
    lead = ["Campaign", "Ad group", "Keyword", "Match type", "Role"] + [{"qs": "Quality Score", "exp_ctr": "Exp. CTR",
                                                                      "ad_relevance": "Ad relevance", "landing_page_exp": "Landing page exp."}[c] for c in qs_cols]
    ordered = sorted(slots, key=lambda s: (s["role"] != "Judged", -s["cost"]))
    tab = make_tab(TITLES["keywords"], lead, ordered,
                   lambda s: [s["campaign"], s["ad_group"], s["label"], s["match"].capitalize(), s["role"]] + [s.get(c) for c in qs_cols],
                   {5: "int"} if "qs" in qs_cols else {})

    def slim(s):
        return {k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()
                if k in ("campaign", "ad_group", "label", "match", "role", "cost", "clicks", "impressions", "conversions", "cpa", "cvr",
                         "vs_cpa", "vs_cvr", "expected", "verdict", "lever", "wasted", "extra", "qs", "exp_ctr", "ad_relevance", "landing_page_exp",
                         "final_url", "against", "against_cpa", "rest_cpa")}
    keywords = {"left_out": left, "counts": counts, "facts": facts, "tables": tables, "tabs": [tab],
                "money": {"account": money}, "baseline": base_info(base),
                "data": {"winners": [slim(s) for s in winners], "no_conversions": [slim(s) for s in nothing],
                         "worse": [slim(s) for s in worse], "match_types": [slim(s) for s in matches],
                         "keywords": [slim(s) for s in ordered]}}

    have = [f for f, _ in COMPONENTS if f in meta["columns"]]
    if not have and "quality_score" not in meta["columns"]:
        return keywords, None
    live = [s for s in slots if s["role"] != "Paused or removed"]
    plain = [s for s in live if not s["brand"]]
    scored = [s for s in live if s.get("qs") is not None]

    def shares(group_):
        out = {}
        for field, label in COMPONENTS:
            rated = [s for s in group_ if s.get(field)]
            below = [s for s in rated if s[field] == "Below average"]
            cost_rated = metrics.total(rated, "cost")
            b, rest = R.total_of(below), R.total_of([s for s in rated if s[field] != "Below average"])
            out[field] = {"label": label, "keywords_rated": len(rated), "cost_rated": r2(cost_rated), "keywords_below": len(below),
                          "cost_below": r2(b["cost"]), "share_below": r4(metrics.div(b["cost"], cost_rated)),
                          "cvr_below": r4(b["cvr"]), "cvr_rest": r4(rest["cvr"]), "cpa_below": r2(b["cpa"]), "cpa_rest": r2(rest["cpa"])}
        return out
    scopes = [("Non brand keywords", shares(plain))]
    if any(s["brand"] for s in live):
        scopes.append(("Brand keywords", shares([s for s in live if s["brand"]])))
    for camp in sorted({s["campaign"] for s in plain}):
        scopes.append(("Campaign: " + camp, shares([s for s in plain if s["campaign"] == camp])))
    main = scopes[0][1]
    qfacts = ["Base for every share: the cost of the enabled keywords, in the scope named, that have a rating for that "
              "component. Keywords with no rating are not in the base. Quality Score is never averaged here."]
    for field, label in COMPONENTS:
        s = main[field]
        if field not in have:
            qfacts.append("%s: not in the file." % label)
            continue
        qfacts.append("%s: %s of the non brand cost with a rating sits on keywords rated Below average (%d of %d keywords, cost %s of %s). "
                      "Their conv. rate %s, cost / conv. %s; the rest: %s, %s."
                      % (label, pc(s["share_below"]), s["keywords_below"], s["keywords_rated"], m(s["cost_below"]), m(s["cost_rated"]),
                         pc(s["cvr_below"]), m(s["cpa_below"]), pc(s["cvr_rest"]), m(s["cpa_rest"])))
    by_score = []
    for score in range(1, 11):
        at = [s for s in scored if int(round(s["qs"])) == score]
        if at:
            by_score.append([str(score), len(at), m(metrics.total(at, "cost"))])
    unscored = [s for s in live if s.get("qs") is None]
    qfacts.append("Cost by Quality Score, enabled keywords: see the table. %s no score (cost %s)."
                  % ("1 enabled keyword shows" if len(unscored) == 1 else "%d enabled keywords show" % len(unscored),
                     m(metrics.total(unscored, "cost"))))
    fix = sorted([s for s in plain if any(s.get(f) == "Below average" for f, _ in COMPONENTS)], key=lambda s: -s["cost"])
    qtables = [
        {"title": "Share of cost rated Below average, by scope", "header": ["Scope"] + [l for _, l in COMPONENTS],
         "rows": [[short(n, 45)] + ["%s of %s" % (pc(v[f]["share_below"]), m(v[f]["cost_rated"])) if v[f]["keywords_rated"] else "n/a"
                                    for f, _ in COMPONENTS] for n, v in scopes]},
        {"title": "Cost by Quality Score", "header": ["Quality Score", "Keywords", "Cost"], "rows": by_score},
        {"title": "Non brand keywords with a component rated Below average, by cost", "header":
            ["Keyword", "Campaign", "Ad group", "QS", "Below average", "Cost", "Conv.", "Cost / conv.", "Verdict"],
         "rows": [[short(s["label"], 40), short(s["campaign"], 30), short(s["ad_group"], 30), num(s["qs"]) if s.get("qs") is not None else "",
                   ", ".join(l for f, l in COMPONENTS if s.get(f) == "Below average"), m(s["cost"]), num(s["conversions"]), m(s["cpa"]),
                   s["verdict"]] for s in fix[:SHOW]]},
    ]
    qtab = {"name": TITLES["quality_score"], "header": ["Scope"] + sum([["%s: keywords rated" % l, "%s: cost rated" % l,
                                                                         "%s: share Below average" % l] for _, l in COMPONENTS], []),
            "rows": [[n] + sum([[v[f]["keywords_rated"], v[f]["cost_rated"], v[f]["share_below"]] for f, _ in COMPONENTS], []) for n, v in scopes],
            "formats": {i: ("int", "money", "pct")[(i - 1) % 3] for i in range(1, 10)}}
    quality = {"left_out": ["Keywords with a score: %d of %d enabled. Brand keywords are shown on their own line." % (len(scored), len(live))],
               "counts": {"enabled": len(live), "scored": len(scored), "unscored": len(unscored)},
               "facts": qfacts, "tables": qtables, "tabs": [qtab], "money": None,
               "baseline": {"rule": "Shares are of cost, not of keyword counts."},
               "data": {"scopes": [{"scope": n, "components": v} for n, v in scopes],
                        "by_score": [{"score": int(r[0]), "keywords": r[1]} for r in by_score],
                        "fix_first": [slim(s) for s in fix]}}
    if len(have) < 3:
        quality["left_out"].append("Missing components: %s. Add them to the keyword report for the full review."
                                   % ", ".join(l for f, l in COMPONENTS if f not in have))
    return keywords, quality


# ----- ads, compared only with their siblings

def review_ads(name, meta, rows, brand):
    ads, disapproved = [], []
    used, counts = split(rows, (), brand_out=False)
    for number, row in enumerate(used, start=1):
        review = " ".join(str(row.get(f) or "") for f in ("status", "approval_status", "status_reasons")).lower()
        label = (row.get("ad") or row.get("headline_1") or row.get("final_url") or "").strip()
        if not label and row.get("ad_id"):
            label = "Ad ID %s" % row["ad_id"]
        slot = R.blank(campaign=(row.get("campaign") or "").strip(), ad_group=(row.get("ad_group") or "").strip(),
                       label=label or "Ad in row %d" % number, ad_type=row.get("ad_type") or "", strength=row.get("ad_strength") or "",
                       ad_id=row.get("ad_id") or "")
        R.add(slot, row)
        R.rates(slot)
        (disapproved if "disapproved" in review else ads).append(slot)
    groups = {}
    for slot in ads:
        groups.setdefault((slot["campaign"], slot["ad_group"]), []).append(slot)
    single = 0
    for members in groups.values():
        whole = R.total_of(members)
        for slot in members:
            slot.update(expected=None, vs_cpa=None, vs_cvr=None, lever="", wasted=0.0, extra=0.0, basis="", gap=None)
            if len(members) < 2:
                slot["verdict"] = "Only ad in its ad group"
                continue
            sib = R.blank()
            for f in R.SUMS:
                sib[f] = whole[f] - slot[f]
            R.rates(sib)
            slot["vs_cpa"], slot["vs_cvr"] = metrics.change(slot["cpa"], sib["cpa"]), metrics.change(slot["cvr"], sib["cvr"])
            share = metrics.div(slot["impressions"], whole["impressions"])
            slot["gap"] = metrics.change(metrics.div(slot["conversions"], slot["impressions"]), metrics.div(sib["conversions"], sib["impressions"]))
            for basis, field, rate in (("conversions per impression", "conversions", metrics.div(whole["conversions"], whole["impressions"])),
                                       ("CTR", "clicks", whole["ctr"])):
                if share and rate and slot["impressions"] * rate >= R.MIN_EXPECTED and sib["impressions"] * rate >= R.MIN_EXPECTED:
                    break
            else:
                slot["verdict"] = "Too little data"
                continue
            if field == "clicks":
                slot["gap"] = metrics.change(slot["ctr"], sib["ctr"])
            slot["basis"], slot["expected"] = basis, whole[field] * share
            slot["against"] = ("its siblings, %s conv. per 1,000 impr." % num(1000 * metrics.div(sib["conversions"], sib["impressions"]))
                               if field == "conversions" else "its siblings, CTR %s" % pc(sib["ctr"]))
            result = R.test_share(slot[field], whole[field], share)
            if result == "low" and field == "conversions" and slot["conversions"] <= 0:
                slot["verdict"], slot["wasted"] = "No conversions", slot["cost"]
            elif result == "low":
                slot["verdict"] = "Trails its siblings"
                if field == "conversions" and sib["cpa"]:
                    slot["extra"] = max(0.0, slot["cost"] - slot["conversions"] * sib["cpa"])
            elif result == "high":
                slot["verdict"] = "Leads its siblings"
            elif field == "conversions" and slot["conversions"] <= 0:
                slot["verdict"] = "Too little data"
            else:
                slot["verdict"] = WATCH_VERDICT if slot["gap"] is not None and R.wide(1.0 + slot["gap"], 1.0) else "In line"
        single += 1 if len(members) < 2 else 0
    money = {"wasted": r2(sum(s["wasted"] for s in ads)), "wasted_count": sum(1 for s in ads if s["wasted"]),
             "less_efficient": r2(sum(s["extra"] for s in ads)), "worse_count": sum(1 for s in ads if s["verdict"] == "Trails its siblings"),
             "better_count": sum(1 for s in ads if s["verdict"] == "Leads its siblings"), "too_early": 0.0, "too_early_count": 0}
    facts = ["Ads are compared only with the other enabled ads in the same ad group, added together. An ad is judged on "
             "conversions per impression once both it and its siblings have the impressions to expect 3 conversions at the ad "
             "group's rate. Otherwise it is judged on CTR, with the same rule on clicks. Leads or trails means its share of the "
             "ad group's conversions (or clicks) is further from its share of impressions than chance would give 1 time in 10.",
             "Wasted: %s on %s judged on conversions that brought none." % (m(money["wasted"]), count(money["wasted_count"], "ad")),
             "Less efficient (not waste, never added to it): %s, the cost above their siblings' cost per conversion, on %s trailing their siblings."
             % (m(money["less_efficient"]), count(money["worse_count"], "ad")),
             "Ad groups with two or more enabled ads: %d. With only one, so nothing to compare: %d." % (len(groups) - single, single)]
    strengths = {}
    for slot in ads:
        if slot["strength"]:
            strengths[slot["strength"]] = strengths.get(slot["strength"], 0) + 1
    if strengths:
        facts.append("Ad strength of the enabled ads: %s. Ad strength is a diagnostic for asset coverage, not an auction input."
                     % ", ".join("%s %d" % (k, v) for k, v in sorted(strengths.items(), key=lambda kv: -kv[1])))
    for slot in disapproved:
        facts.append("Disapproved, left out of the comparison: %s in %s > %s (cost %s)." % (short(slot["label"], 50), slot["campaign"], slot["ad_group"], m(slot["cost"])))
    hits = sorted([s for s in ads if s["verdict"] in ("Trails its siblings", "Leads its siblings", "No conversions")],
                  key=lambda s: (s["verdict"] == "Leads its siblings", -(s["wasted"] or s["extra"]), -s["cost"]))
    head = ["Ad", "Campaign", "Ad group", "Impr.", "CTR", "Conv.", "Cost", "Judged on", "Compared with", "Gap to siblings", "Verdict", "Wasted",
            "Less efficient"]
    facts.append("Each ad is compared with its siblings in the same ad group; 'Gap to siblings' is its conversions per impression "
                 "(or CTR) against theirs.")
    watch = [s for s in ads if s["verdict"] == WATCH_VERDICT]
    hits += sorted(watch, key=lambda s: -s["cost"])
    tables = [{"title": "Ads that lead or trail their siblings, then those worth watching (a wide gap the volume cannot prove)", "header": head,
               "rows": [[short(s["label"], 45), short(s["campaign"], 30), short(s["ad_group"], 30), num(s["impressions"]), pc(s["ctr"]),
                         num(s["conversions"]), m(s["cost"]), s["basis"], s.get("against", ""), signed(s["gap"]), s["verdict"],
                         m(s["wasted"]) if s["wasted"] else "", m(s["extra"]) if s["extra"] else ""] for s in hits[:SHOW * 2]]}]
    everyone = sorted(ads, key=lambda s: (s["campaign"], s["ad_group"], -s["impressions"])) + disapproved
    for slot in disapproved:
        slot.update(verdict="Disapproved, left out", basis="", gap=None, expected=None, vs_cpa=None, vs_cvr=None, lever="", wasted=0.0, extra=0.0)
    tab = make_tab(TITLES["ads"], ["Campaign", "Ad group", "Ad", "Ad ID", "Ad type", "Ad strength", "Judged on", "Gap to siblings"], everyone,
                   lambda s: [s["campaign"], s["ad_group"], s["label"], s["ad_id"], s["ad_type"], s["strength"], s["basis"], r4(s["gap"])], {7: "pct"})
    left = left_lines(counts)
    left[0] += " Brand campaigns are not set apart here: an ad is only compared with ads in its own ad group."
    return {"left_out": left, "counts": counts, "facts": facts, "tables": tables, "tabs": [tab], "money": {"account": money},
            "baseline": {"rule": "Each ad against its siblings in the same ad group."},
            "data": {"ads": [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()
                              if k in ("campaign", "ad_group", "label", "ad_id", "impressions", "clicks", "cost", "conversions", "ctr",
                                       "cpa", "basis", "gap", "expected", "verdict", "wasted", "extra", "strength")} for s in everyone]}}


# ----- placements and videos

def placement_type(row):
    given = (row.get("segment_type") or "").strip()
    if given:
        return given
    text = ("%s %s" % (row.get("placement") or "", row.get("placement_url") or "")).lower()
    if "mobileapp::" in text or "play.google.com" in text or "apps.apple.com" in text:
        return "Mobile application (inferred)"
    if "youtube.com/channel" in text or "youtube.com/@" in text:
        return "YouTube channel (inferred)"
    if "youtube.com/watch" in text or "youtube.com/video" in text:
        return "YouTube video (inferred)"
    return "Website (inferred)"


def review_placements(name, meta, rows, brand):
    def label_of(row):
        return (row.get("placement") or row.get("placement_url") or "").strip()

    def extra(slot, row):
        slot.setdefault("x_type", placement_type(row))
        slot.setdefault("x_url", (row.get("placement_url") or "").strip())
    out = simple_review("placements", name, rows, brand, "Placements", "placement", "placements", label_of, "Placement",
                        by_campaign=False, extra_of=extra, extra_cols=("x_type",), extra_headers=("Type",))
    part = out["data"]
    segments = [s for s in part["segments"]]
    total_cost = sum(s["cost"] for s in segments) or 0.0
    total_impr = sum(s["impressions"] for s in segments) or 0.0
    types = {}
    for s in segments:
        t = types.setdefault(s.get("x_type", ""), R.blank(label=s.get("x_type", "")))
        for f in ("impressions", "clicks", "cost", "conversions"):
            t[f] += s.get(f) or 0
        t["rows"] += 1
    by_type = sorted((R.rates(t) for t in types.values()), key=lambda t: -t["cost"])
    out["tables"].insert(0, {"title": "By placement type (base: cost and impressions of the placements judged)",
                             "header": ["Type", "Placements", "Share of cost", "Share of impr.", "Cost", "Conv.", "Cost / conv."],
                             "rows": [[t["label"], t["rows"], pc(metrics.div(t["cost"], total_cost)), pc(metrics.div(t["impressions"], total_impr)),
                                       m(t["cost"]), num(t["conversions"]), m(t["cpa"])] for t in by_type]})
    seen = sorted(segments, key=lambda s: -s["impressions"])[:25]
    out["tables"].append({"title": "Where the ads were seen most, by impressions, for the brand suitability check",
                          "header": ["Placement", "Type", "Impr.", "Cost", "Conv."],
                          "rows": [[short(s["label"]), s.get("x_type", ""), num(s["impressions"]), m(s["cost"]), num(s["conversions"])] for s in seen]})
    out["tabs"][0]["name"] = "Placements"
    out["facts"].append("Brand suitability is your judgment: read the placement names above as data. The file cannot show "
                        "what the page or video was about beyond its name.")
    out["data"]["by_type"] = [{"type": t["label"], "placements": t["rows"], "cost": r2(t["cost"]), "impressions": t["impressions"],
                               "conversions": r2(t["conversions"]), "share_of_cost": r4(metrics.div(t["cost"], total_cost))} for t in by_type]
    return out


def review_videos(name, meta, rows, brand):
    used, counts = split(rows, brand)
    groups, order = {}, []
    for row in used:
        label = (row.get("video") or row.get("ad") or row.get("video_id") or "").strip()
        key = ((row.get("campaign") or "").strip(), (row.get("ad_group") or "").strip(), label or "Unnamed")
        slot = groups.get(key)
        if slot is None:
            slot = R.blank(campaign=key[0], ad_group=key[1], label=key[2], q={})
            groups[key] = slot
            order.append(key)
        R.add(slot, row)
        for q in ("played_25", "played_50", "played_75", "played_100"):
            if row.get(q) is not None:
                slot["q"].setdefault(q, row[q])
    slots = [R.rates(groups[k]) for k in order]
    base = R.total_of(used)
    for slot in slots:
        if slot["rows"] > 1:
            slot["q"] = {}
        compare(slot, base, "all videos")
        slot["view_verdict"] = "Too little data"
        if base["view_rate"]:
            slot["view_expected"] = slot["impressions"] * base["view_rate"]
            if slot["view_expected"] >= R.MIN_EXPECTED:
                slot["view_verdict"] = {"low": "Lower view rate", "high": "Higher view rate", "even": "In line"}[
                    R.test_count(slot["views"], slot["view_expected"])]
        steps = [("25% to 50%", "played_25", "played_50"), ("50% to 75%", "played_50", "played_75"), ("75% to 100%", "played_75", "played_100")]
        drops = [(lbl, slot["q"][a] - slot["q"][b]) for lbl, a, b in steps if a in slot["q"] and b in slot["q"]]
        slot["drop"] = max(drops, key=lambda d: d[1]) if drops else None
    slots.sort(key=lambda s: -s["cost"])
    convs = base["conversions"] > 0
    money = R.money_of(slots) if convs else None
    facts = ["Baseline, every video judged: view rate %s (%s views over %s impr.), avg. CPV %s, cost %s."
             % (pc(base["view_rate"]), num(base["views"]), num(base["impressions"]), m(base["cpv"]), m(base["cost"])),
             "View rate is judged the same way as conversions: a video's views are compared with what its impressions would "
             "have brought at the baseline view rate, and called higher or lower only when chance alone would give the gap "
             "less than 1 time in 10. On large counts a small gap can pass that test, so read the size of the gap too."]
    if convs:
        facts.append(base_line(base, "every video judged"))
        facts += money_lines(money, "video", "videos")
        facts.append("If a campaign's goal is awareness or views, spend with no conversions is not waste for it.")
    else:
        facts.append("No conversions in this file, so videos are judged on views only.")
    facts.append("Video played to 25%, 50%, 75% and 100% are shown as the file gives them. The largest drop is the step "
                 "between quarters where the percentage falls most. A video with more than one row has no quarter figures here.")
    head = ["Video", "Campaign", "Impr.", "Views", "View rate", "vs baseline", "View rate verdict", "Avg. CPV", "Cost", "Conv.",
            "Cost / conv.", "Verdict", "Largest drop"]
    tables = [{"title": "Videos, by cost", "header": head,
               "rows": [[short(s["label"], 45), short(s["campaign"], 30), num(s["impressions"]), num(s["views"]), pc(s["view_rate"]),
                         signed(metrics.change(s["view_rate"], base["view_rate"])), s["view_verdict"], m(s["cpv"]), m(s["cost"]),
                         num(s["conversions"]), m(s["cpa"]), s["verdict"] if convs else "",
                         "%s (%.1f points)" % s["drop"] if s["drop"] else ""] for s in slots[:SHOW * 2]]}]
    tab = make_tab(TITLES["videos"], ["Campaign", "Ad group", "Video", "Views", "View rate", "View rate vs baseline", "View rate verdict",
                                      "Avg. CPV", "Played to 25%", "Played to 50%", "Played to 75%", "Played to 100%", "Largest drop"], slots,
                   lambda s: [s["campaign"], s["ad_group"], s["label"], s["views"], r4(s["view_rate"]), r4(metrics.change(s["view_rate"], base["view_rate"])),
                              s["view_verdict"], r2(s["cpv"])] + [r4(s["q"][q] / 100.0) if q in s["q"] else None
                                                                 for q in ("played_25", "played_50", "played_75", "played_100")] +
                   ["%s, %.1f points" % s["drop"] if s["drop"] else ""],
                   {3: "int", 4: "pct", 5: "pct", 7: "money", 8: "pct", 9: "pct", 10: "pct", 11: "pct"})
    return {"left_out": left_lines(counts), "counts": counts, "facts": facts, "tables": tables, "tabs": [tab],
            "money": {"account": money} if money else None, "baseline": dict(base_info(base), view_rate=r4(base["view_rate"]), cpv=r2(base["cpv"])),
            "data": {"videos": [{"campaign": s["campaign"], "ad_group": s["ad_group"], "label": s["label"], "impressions": s["impressions"],
                                 "views": s["views"], "view_rate": r4(s["view_rate"]), "view_verdict": s["view_verdict"], "cost": r2(s["cost"]),
                                 "conversions": r2(s["conversions"]), "verdict": s["verdict"], "quarters": s["q"],
                                 "largest_drop": list(s["drop"]) if s["drop"] else None} for s in slots]}}


# ----- segment splits: devices, landing pages, audiences, locations, schedule

def review_devices(name, meta, rows, brand):
    def mix(part):
        base = part["base"]
        return ["Mix (base: cost and conversions of the rows judged): " + "; ".join(
            "%s %s of cost, %s of conversions" % (s["label"], pc(metrics.div(s["cost"], base["cost"])),
                                                  pc(metrics.div(s["conversions"], base["conversions"]))) for s in part["segments"])]
    return simple_review("devices", name, rows, brand, "Devices", "device", "devices", lambda r: (r.get("device") or "").strip(),
                         "Device", more_facts=mix)


def review_landing_pages(name, meta, rows, brand):
    raw = {(r.get("landing_page") or "").strip() for r in rows if (r.get("landing_page") or "").strip()}

    def extra(slot, row):
        slot.setdefault("x_campaigns", set()).add((row.get("campaign") or "").strip())
        if row.get("mobile_speed_score") is not None:
            slot.setdefault("x_speed", row["mobile_speed_score"])
        if row.get("mobile_friendly_rate") is not None:
            slot.setdefault("x_mobile_friendly", row["mobile_friendly_rate"] / 100.0)

    def more(part):
        lines = []
        grouped = len(part["segments"])
        if grouped < len(raw):
            lines.append("%d addresses were grouped into %d pages by leaving out what follows '?' or '#'." % (len(raw), grouped))
        scored = [s for s in part["segments"] if s.get("x_speed") is not None or s.get("x_mobile_friendly") is not None]
        if scored:
            lines.append("Mobile speed score and mobile-friendly click rate, as the file gives them: " + "; ".join(
                "%s %s, %s" % (short(s["label"], 60), num(s["x_speed"]) if s.get("x_speed") is not None else "n/a",
                               pc(s.get("x_mobile_friendly"))) for s in scored[:SHOW]) + ".")
        if "campaign" in meta["columns"]:
            for s in judged_first(part["segments"])[:SHOW]:
                if s["verdict"] != "Better":
                    lines.append("%s gets traffic from %s." % (short(s["label"]), count(len({c for c in s.get("x_campaigns", ()) if c}), "campaign")))
        return lines
    out = simple_review("landing_pages", name, rows, brand, "Landing pages", "page", "pages",
                        lambda r: R.clean_url(r.get("landing_page")), "Landing page", extra_of=extra,
                        extra_cols=("x_speed", "x_mobile_friendly"), extra_headers=("Mobile speed score", "Mobile-friendly click rate"),
                        more_facts=more)
    out["tabs"][0]["formats"].update({3: "pct"})
    for seg in out["data"]["segments"] + out["data"]["inside_campaigns"]:
        seg.pop("x_campaigns", None)
    return out


def review_audiences(name, meta, rows, brand):
    def extra(slot, row):
        if row.get("targeting_setting"):
            slot.setdefault("x_setting", row["targeting_setting"])
        if row.get("segment_type"):
            slot.setdefault("x_type", row["segment_type"])
    out = simple_review("audiences", name, rows, brand, "Audiences", "audience segment", "audience segments",
                        lambda r: (r.get("audience") or "").strip(), "Audience segment", extra_of=extra,
                        extra_cols=("x_type", "x_setting"), extra_headers=("Type", "Targeting setting"))
    out["facts"].append("One person can sit in several audience segments, so the same click can appear in more than one row. "
                        "The baseline is the cost per conversion across the rows in this file, not the campaign's own.")
    return out


def location_label(row):
    if (row.get("location") or "").strip():
        return row["location"].strip()
    return ", ".join(row[g].strip() for g in R.GEO if (row.get(g) or "").strip())


def review_locations(name, meta, rows, brand):
    def extra(slot, row):
        if row.get("location_type"):
            slot.setdefault("x_location_type", row["location_type"])
    return simple_review("locations", name, rows, brand, "Locations", "location", "locations", location_label, "Location",
                         extra_of=extra, extra_cols=("x_location_type",), extra_headers=("Location type",))


def hour_of(text):
    cell = str(text or "").strip().lower()
    if not cell:
        return None
    try:
        return int(float(cell))
    except ValueError:
        pass
    parts = cell.replace(".", "").split()
    if parts and parts[0].isdigit():
        hour = int(parts[0]) % 12
        return hour + 12 if len(parts) > 1 and parts[1].startswith("p") else hour
    return None


def review_schedule(name, meta, rows, brand):
    used, counts = split(rows, brand)
    parts = []
    if "day_of_week" in meta["columns"]:
        def day_label(r):
            cell = (r.get("day_of_week") or "").strip().lower()
            return cell.capitalize() if cell in R.WEEKDAYS else ""
        parts.append(dimension("Day of the week", used, day_label, sort_key=lambda s: R.WEEKDAYS.index(s["label"].lower()),
                               everyone="all days", key="schedule"))
        parts[-1]["nouns"] = ("day", "days")
    if "hour" in meta["columns"]:
        def hour_label(r):
            hour = hour_of(r.get("hour"))
            return "%02d:00" % hour if hour is not None else ""
        parts.append(dimension("Hour of day", used, hour_label, sort_key=lambda s: s["label"], everyone="all hours", key="schedule"))
        parts[-1]["nouns"] = ("hour", "hours")
    if "ad_schedule" in meta["columns"]:
        parts.append(dimension("Ad schedule", used, lambda r: (r.get("ad_schedule") or "").strip(), everyone="all schedule rows",
                               key="schedule"))
        parts[-1]["nouns"] = ("schedule row", "schedule rows")
    facts, tables, tab_rows, slots, money = [], [], [], [], {}
    for part in parts:
        f, t = part_output(part, part["nouns"][0], part["nouns"][1], part["name"])
        facts += ["%s. %s" % (part["name"], line) for line in f]
        tables += t
        lead, segs = part_tab_rows(part)
        tab_rows += [(part["name"],) + l for l in lead]
        slots += segs
        money[part["name"]] = {"account": part["money"], "inside_campaigns": part["inner_money"]}
    if len(parts) > 1:
        facts.append("The same spend is in each split. Money is never added across them.")
    tab = make_tab(TITLES["schedule"], ["Split", "Scope", "Compared with", "Segment"], slots, lambda s: ())
    tab["rows"] = [list(l) + r for l, r in zip(tab_rows, tab["rows"])]
    return {"left_out": left_lines(counts), "counts": counts, "facts": facts, "tables": tables, "tabs": [tab],
            "money": money, "baseline": {p["name"]: base_info(p["base"]) for p in parts}, "data": {"splits": [part_json(p) for p in parts]}}


RUN = {"devices": review_devices, "landing_pages": review_landing_pages, "audiences": review_audiences,
       "locations": review_locations, "schedule": review_schedule, "placements": review_placements, "videos": review_videos,
       "ads": review_ads}


# ----- the run

def print_review(key, review):
    print("\n%s  (from %s)" % (TITLES[key].upper(), review["report"]))
    print("Open: %s" % OPEN[key])
    for line in review["left_out"]:
        print(line)
    for line in review["facts"]:
        print("- " + line)
    if review.get("pointer"):
        print("- " + review["pointer"])
    for table in review["tables"]:
        if table["rows"]:
            print("\n%s\n%s" % (table["title"], outputs.md_table(table["header"], table["rows"])))


def main():
    parser = argparse.ArgumentParser(description="Run every performance review the given Google Ads reports allow.")
    parser.add_argument("reports", nargs="+", help="Google Ads report files (.csv, Excel .csv or .xlsx)")
    parser.add_argument("--work", required=True, help="Folder for the working files")
    parser.add_argument("--brand", default="", help="Brand terms, comma separated")
    parser.add_argument("--brand-campaign", action="append", default=[], help="A brand campaign's exact name. Repeat for more.")
    args = parser.parse_args()

    loaded = {}
    for path in args.reports:
        kind, meta, rows = R.read(path)
        if kind in loaded:
            raise SystemExit("Two files are both the %s: %s and %s. Give one of each report."
                             % (R.REPORTS[kind]["title"], loaded[kind][0], os.path.basename(path)))
        loaded[kind] = (os.path.basename(path), meta, rows)

    names = set()
    for _, meta, rows in loaded.values():
        names |= {(r.get("campaign") or "").strip() for r in rows}
    brand = [b.strip() for b in args.brand_campaign if b.strip()]
    unknown = [b for b in brand if b not in names]
    if unknown:
        raise SystemExit("These brand campaigns are not in the reports: %s. Copy the names exactly as the Campaign column shows them."
                         % ", ".join(unknown))
    phrases = [metrics.tokens(t) for t in args.brand.split(",") if metrics.tokens(t)]
    sources = {}
    for name, meta, rows in loaded.values():
        for row in rows:
            camp, text = (row.get("campaign") or "").strip(), (row.get("bid_strategy") or "").strip()
            if camp and text and camp not in STRATEGIES:
                STRATEGIES[camp], sources[camp] = text, name

    files, reviews = [], {}
    for kind in R.ORDER:
        if kind not in loaded:
            continue
        name, meta, rows = loaded[kind]
        cost = metrics.total(rows, "cost")
        files.append({"file": name, "report": R.REPORTS[kind]["title"], "kind": kind, "period": R.period_of(meta),
                      "title_rows": meta["title_rows"], "rows": len(rows), "cost": r2(cost),
                      "conversions": r2(metrics.total(rows, "conversions")), "reconcile": R.reconcile(meta, cost, len(rows), kind),
                      "columns_not_used": meta["unknown_headers"]})
        if kind == "weekly":
            found = {"weekly": review_weekly(name, meta, rows, brand)}
            demand_gen = review_demand_gen(name, meta, rows)
            if demand_gen:
                found["demand_gen"] = demand_gen
        elif kind == "keywords":
            kw, qs = review_keywords(name, meta, rows, phrases, brand)
            found = {"keywords": kw}
            if qs:
                found["quality_score"] = qs
        else:
            found = {kind: RUN[kind](name, meta, rows, brand)}
        for key, review in found.items():
            review.update(key=key, title=TITLES[key], report=name, open=OPEN[key], period=R.period_of(meta))
            reviews[key] = review

    not_run = []
    for key in REVIEW_ORDER:
        # Demand Gen runs only when the campaign report names a Demand Gen campaign; most accounts have none.
        if key in reviews or key == "demand_gen":
            continue
        source = R.REPORTS[SOURCE[key]]
        if key == "quality_score" and "keywords" in reviews:
            unlock = "Add Quality Score, Exp. CTR, Ad relevance and Landing page exp. to the keyword report (%s)." % source["path"]
        else:
            unlock = "Give the %s. In Google Ads: %s." % (source["title"], source["path"])
        not_run.append({"key": key, "title": TITLES[key], "unlock": unlock})

    periods = {json_period(f["period"]) for f in files}
    result = {"files": files, "brand": {"campaigns": brand, "terms": [" ".join(p) for p in phrases]}, "rules": RULES,
              "reviews": {k: reviews[k] for k in REVIEW_ORDER if k in reviews}, "not_run": not_run,
              "same_period": len(periods) == 1, "strategies": dict(STRATEGIES), "across": across(reviews)}

    outputs.ensure_dir(args.work)
    outputs.write_json(os.path.join(args.work, "review.json"), result)
    template = {"headline": "", "assumptions": [],
                "reviews": {k: {"summary": "", "actions": [{"action": "", "label": "", "source": ""}]} for k in result["reviews"]}}
    outputs.write_json(os.path.join(args.work, "notes.template.json"), template)

    print("PERFORMANCE REVIEWS\n\nFILES READ")
    for f in files:
        rec = f["reconcile"]
        check = ("rows match the file's own total (%s, cost %s), and every review of this file reconciles against it." % (rec["label"], m(rec["file_total"]))
                 if rec and rec["matches"]
                 else "rows do NOT match the file's own total (%s, cost %s against %s in the rows)." % (rec["label"], m(rec["file_total"]), m(rec["rows"]))
                 if rec else "no total row to check against.")
        others = [t for t in (rec or {}).get("totals", []) if t["label"] != rec["label"] and abs(t["gap"]) > 0.005]
        if others:
            check += " Other totals in the file: " + "; ".join(
                ("%s %s, the same as the rows once each row's rounding to the cent is allowed for" % (t["label"], m(t["value"])))
                if abs(t["gap"]) <= rec["tolerance"] else
                "%s %s, %s %s the rows, which covers %s" % (t["label"], m(t["value"]), m(abs(t["gap"])), "more than" if t["gap"] > 0 else "less than",
                                                            t["meaning"]) for t in others) + "."
        when = ("%s to %s (%d days)" % (f["period"]["start"], f["period"]["end"], f["period"]["days"])) if f["period"] else "no date range found"
        print("- %s: the %s, %s, %d rows, cost %s, %s conversions; %s" % (f["file"], f["report"], when, f["rows"], m(f["cost"]),
                                                                           num(f["conversions"]), check))
    if not result["same_period"]:
        print("- The files cover different date ranges. Each review uses its own file's dates.")
    if len({f["cost"] for f in files}) > 1:
        print("- The files' costs differ because each report covers a different part of the account (keyword rows, every ad, "
              "every campaign, one segment) and its own dates. Totals from different files are never compared or added.")
    if STRATEGIES:
        print("- Bid strategy by campaign: %s." % "; ".join("%s: %s (from %s)" % (c, t, sources[c]) for c, t in STRATEGIES.items()))
    else:
        print("- No file has a Bid strategy type column, so the reviews cannot say which bid adjustments act on a finding. "
              "Add Bid strategy type to the campaign report.")
    if brand or phrases:
        print("- Brand set apart: campaigns %s; terms %s." % (", ".join(brand) or "none", ", ".join(result["brand"]["terms"]) or "none"))
    else:
        print("- No brand campaigns or terms were given, so brand rows are inside every baseline and pull it down.")
    print("\nHOW EVERY REVIEW JUDGES")
    for line in RULES:
        print("- " + line)
    for key, review in result["reviews"].items():
        print_review(key, review)
    if result["across"]:
        print("\nACROSS REPORTS")
        for line in result["across"]:
            print("- " + line)
    print("\nREVIEWS NOT RUN")
    for item in not_run:
        print("- %s: %s" % (item["title"], item["unlock"]))
    if not not_run:
        print("- None.")
    print("\nNEXT\nCopy %s to %s and fill it in, then run:\n  python3 scripts/write_report.py --work %s --out OUTPUT"
          % (os.path.join(args.work, "notes.template.json"), os.path.join(args.work, "notes.json"), args.work))


THEME_SKIP = set("www com net org html htm php aspx index page pages home the and a an for of in to on our us".split())


def theme(words):
    return {w[:-1] if w.endswith("s") and len(w) > 3 else w for w in words if w not in THEME_SKIP and not w.isdigit()}


def across(reviews):
    """Where a keyword and a landing page on the same theme agree or disagree."""
    if "keywords" not in reviews or "landing_pages" not in reviews:
        return []
    keywords = [k for k in reviews["keywords"]["data"]["keywords"] if k["role"] == "Judged"]
    notes = []
    for page in reviews["landing_pages"]["data"]["segments"]:
        if page["verdict"] not in ("No conversions", "Worse", WATCH_VERDICT):
            continue
        path = page["label"].split("://", 1)[-1].partition("/")[2]
        words = theme(metrics.tokens(path.replace("-", " ").replace("_", " ").replace("/", " ")))
        if not words:
            continue
        match = [k for k in keywords if words <= theme(metrics.tokens(R.keyword_parts(k["label"], "")[0]))]
        if not match:
            continue
        conv, cost = sum(k["conversions"] for k in match), sum(k["cost"] for k in match)
        text = ("%s: the page is judged '%s' (cost %s, %s conversions), and the keywords on the same theme (%s) brought %s conversions on %s."
                % (path.strip("/") or page["label"], page["verdict"], m(page["cost"]), num(page["conversions"]),
                   ", ".join(k["label"] for k in match[:5]), num(conv), m(cost)))
        if page["conversions"] <= 0 < conv:
            text += " They disagree: the keywords convert and the page shows none."
        elsewhere = sorted({R.clean_url(k["final_url"]) for k in match if k.get("final_url") and R.clean_url(k["final_url"]) != page["label"]})
        if elsewhere:
            text += " Their final URL is %s, not this page, so the page's results come from other traffic." % ", ".join(elsewhere)
        below = [k for k in match if k.get("landing_page_exp") == "Below average"]
        if below:
            text += " Landing page exp. is rated Below average on %d of them, which agrees with the page's result." % len(below)
        notes.append(text)
    return notes


def json_period(period):
    return (period or {}).get("start"), (period or {}).get("end")


if __name__ == "__main__":
    main()
