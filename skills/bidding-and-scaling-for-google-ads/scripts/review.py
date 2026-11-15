#!/usr/bin/env python3
"""Bid strategy review: each campaign against its target, its learning state, what limits it,
and whether to scale, tighten, pause or hold it.

Reads a Google Ads campaign report segmented by Day and, if given, the change history. For
each campaign it computes the actual cost per conversion or conv. value / cost against its
target, conversion volume against Google's guidance, whether it is learning, the days since
its last bid strategy, target, budget or conversion change, what limits it (budget, rank or
neither), and a category: scale, tighten, pause, hold or on target. Nothing is changed in any
account.

    python3 scripts/review.py REPORT --out OUTPUTDIR [--changes CHANGE_HISTORY]
        [--cycle-days 7] [--brand "Brand"] [--goal-cpa 60] [--goal-roas 4]
"""
import argparse
import datetime as dt
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics, outputs, xlsx  # noqa: E402
import bidding_rules as rules  # noqa: E402

EXTRA_ALIASES = {
    "status": "serving_status", "status reasons": "status_reasons", "budget name": "budget_name",
    "bid strategy": "bid_strategy_name", "target cpa": "target_cpa", "avg. target cpa": "target_cpa",
    "target roas": "target_roas_raw", "avg. target roas": "target_roas_raw",
    "search impr. share": "is_raw", "search lost is (budget)": "lb_raw", "search lost is (rank)": "lr_raw",
    "search lost top is (budget)": "ltb_raw", "search lost top is (rank)": "ltr_raw",
}
LABELS = {"day": "Day", "campaign": "Campaign", "cost": "Cost", "conversions": "Conversions",
          "bid_strategy": "Bid strategy type", "campaign_status": "Campaign status", "conv_value": "Conv. value"}
SHARE_KEYS = ("is_raw", "lb_raw", "lr_raw", "ltb_raw", "ltr_raw")
SHARE_HEADERS = {"lb_raw": "Search lost IS (budget)", "lr_raw": "Search lost IS (rank)",
                 "ltb_raw": "Search lost top IS (budget)", "ltr_raw": "Search lost top IS (rank)"}
SUMS = ("cost", "conversions", "conv_value", "clicks", "impressions")
KINDS = (
    ("created", re.compile(r"campaign created|created campaign|new campaign", re.I)),
    ("strategy", re.compile(r"bid(?:ding)? strategy(?: type)?\b[^\n]*\b(?:changed|set|switched)|\bswitched (?:to|from) (?:target|maximi[sz]e|manual)", re.I)),
    ("target", re.compile(r"target (?:cpa|roas)|target return on ad spend|target cost per", re.I)),
    ("budget", re.compile(r"budget", re.I)),
    ("conversion", re.compile(r"conversion (?:goal|action|value|setting|window|count)|campaign goals?|value rule|primary (?:action|conversion)", re.I)),
    ("composition", re.compile(r"\b(?:keyword|ad group|asset group)s?\b[^\n]*\b(?:added|removed|created)\b|\b(?:added|removed|created)\b[^\n]*\b(?:keyword|ad group|asset group)s?\b", re.I)),
)
MATERIAL = ("created", "strategy", "target", "budget", "conversion")
KIND_WORDS = {"created": "campaign created", "strategy": "bid strategy", "target": "target", "budget": "budget",
              "conversion": "conversion setting", "composition": "keywords or ad groups", "other": "other"}
FROM_TO = re.compile(r"target (cpa|roas)[^\n]*?\bfrom\s*[^\d\n]{0,3}([\d,]+(?:\.\d+)?)\s*(%?)\s*to\b", re.I)
TARGET_VALUE = re.compile(r"target (cpa|roas)[^\n]*?\b(?:to|set to|of)\s*[^\d\n]{0,3}([\d,]+(?:\.\d+)?)\s*(%?)", re.I)
LIMITED_BY_BUDGET = re.compile(r"limited by budget|budget[\s-]*(?:limited|constrained)", re.I)
CATEGORY_ORDER = ["Scale candidate", "Missing its target", "Pause candidate", "On target: hold steady", "Hold: learning",
                  "Hold: recent change", "Hold: too few conversions to judge", "No target to judge against",
                  "Not judged on conversions", "Not serving"]


def parse_share(text):
    """'32.6%' -> (32.6, None), '< 10%' -> (0.0, 'below'), '> 90%' -> (90.0, 'above'), '--' -> (None, None)."""
    t = (text or "").strip()
    if t in ("", "--"):
        return None, None
    if t.startswith("<"):
        return 0.0, "below"
    value = io.to_number(t)
    if value is None:
        return None, None
    return value, ("above" if t.startswith(">") else None)


def parse_roas(text):
    t = (text or "").strip()
    value = io.to_number(t)
    if value is None or value <= 0:
        return None
    return value / 100.0 if ("%" in t or value > rules.ROAS_RATIO_MAX) else value


def read_changes(path, names, as_of):
    meta, rows = io.read_report(path)
    io.require(meta, ["changed_at", "changes"], "change history", labels={"changed_at": "Date & time", "changes": "Changes"})
    events = []
    for row in rows:
        day = dates.parse_day(row.get("changed_at"))
        if not day:
            continue
        text = row.get("changes") or ""
        kinds = []
        for line in [part for part in text.splitlines() if part.strip()] or [text]:
            for kind, pattern in KINDS:
                if pattern.search(line) and kind not in kinds:
                    kinds.append(kind)
        targets = {}
        for kind, number, sign in TARGET_VALUE.findall(text):
            value = io.to_number(number)
            if value:
                targets[kind.lower()] = (value / 100.0 if (sign or value > rules.ROAS_RATIO_MAX) else value) if kind.lower() == "roas" else value
        target_from = {}
        for kind, number, sign in FROM_TO.findall(text):
            value = io.to_number(number)
            if value:
                target_from[kind.lower()] = (value / 100.0 if (sign or value > rules.ROAS_RATIO_MAX) else value) if kind.lower() == "roas" else value
        campaign = row.get("campaign") or ""
        events.append({"target_from": target_from, "day": day, "campaign": campaign, "ad_group": row.get("ad_group") or "", "user": row.get("user") or "",
                       "text": text, "kinds": kinds or ["other"], "targets": targets, "matched": campaign in names,
                       "days_before_end": (as_of - day).days})
    events.sort(key=lambda e: e["day"])
    return events


def sum_days(days, start, end):
    total = {k: 0.0 for k in SUMS}
    for day, values in days.items():
        if start <= day <= end:
            for k in SUMS:
                total[k] += values[k]
    total["cpa"] = metrics.div(total["cost"], total["conversions"])
    total["roas"] = metrics.div(total["conv_value"], total["cost"])
    total["cvr"] = metrics.div(total["conversions"], total["clicks"])
    total["cpc"] = metrics.div(total["cost"], total["clicks"])
    return total


def share_avg(days, key, start, end):
    """Average of a lost share, each day weighted by the impressions it was eligible for."""
    num = den = 0.0
    below = counted = 0
    for day, values in days.items():
        if not (start <= day <= end):
            continue
        value, flag = values[key]
        if value is None or values["impressions"] <= 0:
            continue
        share, share_flag = values["is_raw"]
        weight = values["impressions"] / (share / 100.0) if share and share_flag is None else values["impressions"]
        num += value * weight
        den += weight
        counted += 1
        below += flag == "below"
    return (num / den if den else None), counted, below


def judge(c, ref, measure):
    """Gap to the reference and a verdict that only counts gaps wider than chance."""
    conv = c["read"]["conversions"]
    band = rules.band(conv)
    if ref is None or band is None:
        return None, band, None
    if measure == "cpa":
        gap = metrics.change(c["read"]["cpa"], ref)
        if gap is None:
            return None, band, None
        return gap, band, ("beats" if gap < -band else "misses" if gap > band else "near")
    gap = metrics.change(c["read"]["roas"], ref)
    if gap is None:
        return None, band, None
    return gap, band, ("beats" if gap > band else "misses" if gap < -band else "near")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report", help="campaign report segmented by Day")
    parser.add_argument("--out", required=True)
    parser.add_argument("--changes", help="change history export")
    parser.add_argument("--cycle-days", type=int, help="days that usually pass between a click and its conversion. Default: %d, printed as assumed" % rules.DEFAULT_CYCLE_DAYS)
    parser.add_argument("--brand", default="", help="brand campaigns, comma separated, left out of the account comparison")
    parser.add_argument("--goal-cpa", type=float, help="the most the business accepts per conversion. Shown beside each campaign's own target")
    parser.add_argument("--goal-roas", type=float, help="the least conv. value / cost the business needs, as a ratio (4 for 400%%). Shown beside each campaign's own target")
    args = parser.parse_args()
    if args.goal_roas and args.goal_roas > rules.ROAS_RATIO_MAX:
        raise SystemExit("Write --goal-roas as a ratio: 4 for 400%.")
    if args.cycle_days is not None and args.cycle_days < 0:
        raise SystemExit("--cycle-days must be zero or more.")

    if not os.path.isfile(args.report):
        raise SystemExit("I can't find the report file %s." % args.report)
    try:
        meta, rows = io.read_report(args.report, extra_aliases=EXTRA_ALIASES, extra_numeric=("target_cpa",))
    except (OSError, ValueError) as error:
        raise SystemExit(str(error))
    if "day" not in meta["columns"]:
        raise SystemExit("This report is not segmented by Day. In Google Ads open Campaigns, choose Segment, Time, Day, and download it again.")
    io.require(meta, ["campaign", "campaign_status", "bid_strategy", "cost", "conversions"], "campaign report", labels=LABELS)
    columns = meta["columns"]
    for row in rows:
        row["date"] = dates.parse_day(row.get("day"))
    rows = [r for r in rows if r["date"] and r.get("campaign")]
    if not rows:
        raise SystemExit("I can't read any dated campaign rows. Download the campaign report again, segmented by Day.")

    start, as_of = min(r["date"] for r in rows), max(r["date"] for r in rows)
    cycle_assumed = args.cycle_days is None
    cycle = rules.DEFAULT_CYCLE_DAYS if cycle_assumed else args.cycle_days
    eval_end = as_of - dt.timedelta(days=cycle or 0)
    if eval_end < start:
        raise SystemExit("The report covers %d days, fewer than the %d day conversion cycle%s. Download a longer date range." % (
            (as_of - start).days + 1, cycle, " assumed because none was given" if cycle_assumed else ""))
    brand = [n.strip() for n in args.brand.split(",") if n.strip()]

    camps = {}
    for r in rows:
        c = camps.setdefault(r["campaign"], {"name": r["campaign"], "days": {}, "latest": None, "row": None})
        d = c["days"].setdefault(r["date"], dict({k: 0.0 for k in SUMS}, **{k: (None, None) for k in SHARE_KEYS}))
        for k in SUMS:
            d[k] += r.get(k) or 0
        for k in SHARE_KEYS:
            if k in columns:
                d[k] = parse_share(r.get(k))
        d["target_cpa"] = r.get("target_cpa")
        d["target_roas"] = parse_roas(r.get("target_roas_raw"))
        d["budget"] = r.get("budget")
        if c["latest"] is None or r["date"] >= c["latest"]:
            c["latest"], c["row"] = r["date"], r
    unknown_brand = [b for b in brand if b not in camps]
    if unknown_brand:
        raise SystemExit("These brand campaigns are not in the report: %s. Use the names exactly as the report writes them." % ", ".join(unknown_brand))
    currencies = sorted({r.get("currency") for r in rows if r.get("currency")})

    events = []
    if args.changes:
        if not os.path.isfile(args.changes):
            raise SystemExit("I can't find the change history file %s." % args.changes)
        try:
            events = read_changes(args.changes, set(camps), as_of)
        except (OSError, ValueError) as error:
            raise SystemExit(str(error))
    account_events = [e for e in events if not e["campaign"]]

    budget_cols = ("lb_raw", "lr_raw") if "lb_raw" in columns or "lr_raw" in columns else ("ltb_raw", "ltr_raw")
    budget_col = budget_cols[0] if budget_cols[0] in columns else None
    rank_col = budget_cols[1] if budget_cols[1] in columns else None

    campaigns = []
    for c in camps.values():
        row, days = c["row"], c["days"]
        ordered = sorted(days)
        last = lambda key: next((days[d][key] for d in reversed(ordered) if days[d][key] is not None), None)  # noqa: E731
        status = row.get("campaign_status") or ""
        serving_status = row.get("serving_status") or ""
        reasons = row.get("status_reasons") or ""
        state_text = "%s %s" % (serving_status, reasons)
        serving = status.strip().lower() not in ("paused", "removed", "ended") and not serving_status.strip().lower().startswith(("paused", "removed", "ended"))
        mine = [e for e in events if e["campaign"] == c["name"]]
        target_cpa, target_roas = last("target_cpa"), last("target_roas")
        target_source = "report"
        fam = rules.family(row.get("bid_strategy"), target_cpa is not None, target_roas is not None)
        if fam == "tcpa" and target_cpa is None:
            from_history = [e["targets"]["cpa"] for e in mine if "cpa" in e["targets"]]
            target_cpa, target_source = (from_history[-1], "change history") if from_history else (None, None)
        if fam == "troas" and target_roas is None:
            from_history = [e["targets"]["roas"] for e in mine if "roas" in e["targets"]]
            target_roas, target_source = (from_history[-1], "change history") if from_history else (None, None)
        varied = len({days[d]["target_cpa" if fam == "tcpa" else "target_roas"] for d in ordered if start <= d <= eval_end} - {None}) > 1

        # Changes, the latest of each kind, including account level conversion changes.
        last_change = {}
        for e in mine + [e for e in account_events if "conversion" in e["kinds"]]:
            for kind in e["kinds"]:
                if kind not in last_change or e["day"] >= last_change[kind]["day"]:
                    last_change[kind] = {"day": e["day"], "days_since": (as_of - e["day"]).days, "text": e["text"],
                                         "account_level": not e["campaign"], "targets": e["targets"], "target_from": e["target_from"]}
        # The target read starts the day after the latest strategy or target change inside the report.
        read_start = start
        reset = None
        for kind in ("created", "strategy", "target"):
            ch = last_change.get(kind)
            if ch and start <= ch["day"] <= as_of and ch["day"] + dt.timedelta(days=1) > read_start:
                read_start, reset = ch["day"] + dt.timedelta(days=1), dict(ch, kind=kind)
        read_days = max((eval_end - read_start).days + 1, 0)
        read = sum_days(days, read_start, eval_end)
        whole = sum_days(days, start, eval_end)
        before = sum_days(days, start, reset["day"] - dt.timedelta(days=1)) if reset and reset["day"] > start else None
        before_days = (reset["day"] - start).days if before else 0
        # Days since a change that are still inside the conversion cycle, or too few conversions after it:
        # shown as an early read, never judged.
        early = None
        if reset and (read_days == 0 or read["conversions"] < rules.needed(fam)):
            early = sum_days(days, read_start, as_of)
            early.update({"start": read_start.isoformat(), "end": as_of.isoformat(), "days": (as_of - read_start).days + 1, "proper_read_on": None})
            early["conv_per_day"] = metrics.div(early["conversions"], early["days"])
            if early["conv_per_day"]:
                first = read_start + dt.timedelta(days=int(math.ceil(rules.needed(fam) / early["conv_per_day"])) - 1 + cycle)
                floor = reset["day"] + dt.timedelta(days=rules.CYCLES_TO_JUDGE * cycle)
                early["proper_read_on"] = max(first, floor).isoformat()
        last30 = sum_days(days, eval_end - dt.timedelta(days=29), eval_end)
        material = [dict(last_change[k], kind=k) for k in MATERIAL if k in last_change]
        latest_material = max(material, key=lambda m: m["day"]) if material else None
        conv_since = None
        if latest_material and latest_material["day"] >= start:
            conv_since = sum_days(days, latest_material["day"] + dt.timedelta(days=1), eval_end)["conversions"]

        # Impression share does not wait for late conversions, so it is read through the report's last day.
        lost_budget, budget_days, budget_below = share_avg(days, budget_col, read_start, as_of) if budget_col else (None, 0, 0)
        lost_rank, rank_days, rank_below = share_avg(days, rank_col, read_start, as_of) if rank_col else (None, 0, 0)
        limited_status = bool(LIMITED_BY_BUDGET.search(state_text))
        budget_limited = limited_status or (lost_budget is not None and lost_budget >= rules.SHARE_CUT)
        rank_limited = lost_rank is not None and lost_rank >= rules.SHARE_CUT
        learning = "learning" in state_text.lower()
        ctype = (row.get("campaign_type") or "").strip()
        budget = row.get("budget") if row.get("budget") is not None else last("budget")
        entry = {
            "campaign": c["name"], "campaign_type": ctype, "campaign_status": status, "serving": serving, "status": serving_status,
            "status_reasons": reasons, "learning": learning, "bid_strategy": row.get("bid_strategy") or "", "family": fam,
            "strategy_label": rules.LABEL[fam], "portfolio": row.get("bid_strategy_name") or "", "budget": budget,
            "budget_name": row.get("budget_name") or "", "brand": c["name"] in brand,
            "target_cpa": target_cpa if fam == "tcpa" else None, "target_roas": target_roas if fam == "troas" else None,
            "target_source": target_source if fam in ("tcpa", "troas") else None, "target_varied": varied,
            "read_start": read_start.isoformat(), "read_end": eval_end.isoformat(), "read_days": read_days,
            "read": read, "whole": whole, "before_reset": before, "reset": {k: (v.isoformat() if isinstance(v, dt.date) else v) for k, v in reset.items()} if reset else None,
            "conv_last30": last30["conversions"], "before_days": before_days, "early_read": early,
            "conv_per_day": metrics.div(read["conversions"], read_days) or (early or {}).get("conv_per_day"),
            "lost_budget_column": SHARE_HEADERS.get(budget_col), "lost_rank_column": SHARE_HEADERS.get(rank_col),
            "top_is": budget_col == "ltb_raw" or rank_col == "ltr_raw",
            "changes": {k: dict(v, day=v["day"].isoformat()) for k, v in last_change.items()},
            "latest_material_change": dict(latest_material, day=latest_material["day"].isoformat()) if latest_material else None,
            "conv_since_change": conv_since,
            "lost_budget": lost_budget, "lost_rank": lost_rank, "lost_budget_below10_days": budget_below, "lost_rank_below10_days": rank_below,
            "share_days": max(budget_days, rank_days), "limited_by_budget_status": limited_status,
            "budget_limited": budget_limited, "rank_limited": rank_limited, "needed": rules.needed(fam), "reasons": [], "notes": [],
            "_days": days,
        }
        campaigns.append(entry)

    # Shared budgets: the same budget name on two or more campaigns.
    by_budget = {}
    for c in campaigns:
        if c["budget_name"]:
            by_budget.setdefault(c["budget_name"], []).append(c["campaign"])
    for c in campaigns:
        others = [n for n in by_budget.get(c["budget_name"], []) if n != c["campaign"]]
        c["shares_budget_with"] = others

    compared = [c for c in campaigns if c["serving"] and not c["brand"]]
    comparison_cpa = metrics.div(sum(c["whole"]["cost"] for c in compared), sum(c["whole"]["conversions"] for c in compared))
    comparison_roas = metrics.div(sum(c["whole"]["conv_value"] for c in compared), sum(c["whole"]["cost"] for c in compared))

    for c in campaigns:
        classify(c, args, cycle, comparison_cpa)
        c["check"] = check_window(c, cycle)
        c["step_guidance"] = step_guidance(c)
        del c["_days"]
    campaigns.sort(key=lambda c: (CATEGORY_ORDER.index(c["category"]), -c["whole"]["cost"]))

    if any(c["family"] in rules.VALUE_FAMILIES and c["serving"] for c in campaigns) and "conv_value" not in columns:
        raise SystemExit("A campaign bids on conversion value, but the report has no Conv. value column. Add Conv. value and download it again.")

    account = build_account(campaigns, meta, rows, start, as_of, eval_end)
    result = {
        "report": os.path.basename(args.report), "title_rows": meta["title_rows"], "date_range": meta["date_range"],
        "first_day": start.isoformat(), "last_day": as_of.isoformat(), "read_end": eval_end.isoformat(), "days_covered": (as_of - start).days + 1,
        "cycle_days": cycle, "cycle_assumed": cycle_assumed, "brand": brand, "goal_cpa": args.goal_cpa, "goal_roas": args.goal_roas, "currencies": currencies,
        "comparison_cpa": comparison_cpa, "comparison_roas": comparison_roas,
        "budget_column_read": SHARE_HEADERS.get(budget_col), "rank_column_read": SHARE_HEADERS.get(rank_col),
        "has_targets": {"target_cpa": "target_cpa" in columns, "target_roas": "target_roas_raw" in columns},
        "has_status": "serving_status" in columns, "change_history_read": bool(args.changes),
        "thresholds": thresholds(), "campaigns": campaigns, "account": account,
        "changes": [dict(e, day=e["day"].isoformat()) for e in events],
    }
    out = outputs.ensure_dir(args.out)
    outputs.write_json(os.path.join(out, "bidding-review.json"), result)
    write_workbook(result, os.path.join(out, "bidding-review.xlsx"))
    text = summary(result)
    with open(os.path.join(out, "bidding-review.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote the files to %s" % out)


def classify(c, args, cycle, comparison_cpa):
    fam, read = c["family"], c["read"]
    measure = "roas" if fam in rules.VALUE_FAMILIES else "cpa"
    ref, ref_source = None, None
    if fam == "tcpa":
        ref, ref_source = c["target_cpa"], "its Target CPA"
    elif fam == "troas":
        ref, ref_source = c["target_roas"], "its Target ROAS"
    elif fam == "max_value" and args.goal_roas:
        ref, ref_source = args.goal_roas, "your goal for conv. value / cost"
    elif fam not in rules.VALUE_FAMILIES and fam != "tis" and args.goal_cpa:
        ref, ref_source = args.goal_cpa, "your goal cost per conversion"
    c["measure"], c["reference"], c["reference_source"] = measure, ref, ref_source
    c["gap"], c["band"], c["verdict"] = judge(c, ref, measure)
    goal = None if fam == "tis" else (args.goal_roas if measure == "roas" else args.goal_cpa)
    c["goal"] = goal
    c["goal_gap"], _, c["goal_verdict"] = judge(c, goal, measure)
    if read["conversions"] < c["needed"]:
        c["goal_verdict"] = None
    own = c["target_cpa"] if fam == "tcpa" else c["target_roas"] if fam == "troas" else None
    c["target_vs_goal"] = None
    if goal and own:
        c["target_vs_goal"] = "same" if abs(own - goal) < 1e-9 else ("stricter" if (own < goal) == (measure == "cpa") else "looser")
    pause_ref = c["target_cpa"] or args.goal_cpa or comparison_cpa
    c["pause_reference_cpa"] = pause_ref
    lm = c["latest_material_change"]
    recent_by_cycle = bool(lm and cycle and lm["days_since"] < rules.CYCLES_TO_JUDGE * cycle)
    recent_by_volume = bool(lm and c["conv_since_change"] is not None and c["conv_since_change"] < c["needed"])
    after_end = bool(lm and lm["days_since"] < 0)
    reasons = c["reasons"]

    if not c["serving"]:
        category = "Not serving"
        reasons.append("Campaign status is %s, so it is left out of every comparison and every move." % (c["campaign_status"] or c["status"]))
    elif c["learning"]:
        category = "Hold: learning"
        reasons.append("Google shows it as learning: status %s, reason %s." % (c["status"] or "n/a", c["status_reasons"] or "n/a"))
    elif read["conversions"] == 0 and pause_ref and read["cost"] >= rules.PAUSE_MULTIPLE * pause_ref:
        category = "Pause candidate"
        c["spend_multiple"] = read["cost"] / pause_ref
        reasons.append("Spent %s with no conversion between %s and %s: %.1f times the reference cost per conversion of %s, where the test needs %d." % (
            rules.money(read["cost"]), c["read_start"], c["read_end"], c["spend_multiple"], rules.money(pause_ref), rules.PAUSE_MULTIPLE))
    elif after_end or recent_by_cycle or recent_by_volume:
        category = "Hold: recent change"
        if after_end:
            reasons.append("%s came after the report's last day, so the data does not show its effect." % phrase(lm["kind"], True))
        if recent_by_cycle:
            reasons.append("%s was %d days before the report's last day, less than %d conversion cycles of %d days." % (
                phrase(lm["kind"], True), lm["days_since"], rules.CYCLES_TO_JUDGE, cycle))
        if recent_by_volume and not after_end:
            reasons.append("Only %s conversions have come in since %s, fewer than the %d Google suggests for judging a bid strategy." % (
                "{:,.1f}".format(c["conv_since_change"]), phrase(lm["kind"]), c["needed"]))
    elif fam == "tis":
        category = "Not judged on conversions"
        reasons.append("Target impression share bids for visibility, not conversions, so it is not judged against a cost per conversion.")
    elif ref is None:
        category = "No target to judge against"
        reasons.append("It has no target in the report or the change history, and no goal was given for it." if fam in ("tcpa", "troas")
                       else "It has no target, and no goal was given. Give --goal-cpa or --goal-roas to judge it.")
    elif read["conversions"] < c["needed"]:
        category = "Hold: too few conversions to judge"
        reasons.append("%s conversions in the read period, fewer than the %d Google suggests for judging it." % ("{:,.1f}".format(read["conversions"]), c["needed"]))
    elif c["verdict"] == "beats":
        category = "Scale candidate"
    elif c["verdict"] == "misses":
        category = "Missing its target"
    else:
        category = "On target: hold steady"
    c["category"] = category

    actual = read["cpa"] if measure == "cpa" else read["roas"]
    fmt = rules.money if measure == "cpa" else rules.roas_text
    label = "Cost / conv." if measure == "cpa" else "Conv. value / cost"
    early = c.get("early_read")
    if category == "Not serving":
        pass
    elif early and category != "Pause candidate":
        c["verdict"] = None
        e_value = early["cpa"] if measure == "cpa" else early["roas"]
        e_gap = metrics.change(e_value, ref) if ref is not None else None
        when = ("A proper read is possible around %s, at its pace since the change." % early["proper_read_on"]) if early["proper_read_on"] else "No date can be set: no conversion has come in since the change."
        reasons.append("Early read, not yet judgeable: in the %d days since %s (%s to %s), cost %s, conversions %s, %s %s%s. Recent days still gain conversions, and %s conversions is fewer than the %d needed. %s" % (
            early["days"], phrase(c["reset"]["kind"]), early["start"], early["end"], rules.money(early["cost"]), "{:,.1f}".format(early["conversions"]),
            label_for(measure).lower(), fmt_measure(measure, e_value),
            (" against %s of %s (%s)" % (ref_source, fmt_measure(measure, ref), rules.pct(e_gap, signed=True))) if e_gap is not None else "",
            "{:,.1f}".format(early["conversions"]), c["needed"], when))
        if c["read_days"] == 0:
            reasons.append("No day after the change is outside the %d day conversion cycle yet, so there is no read period." % cycle)
    elif c["verdict"] and ref is not None and read["conversions"] < c["needed"]:
        c["verdict"] = None
        reasons.append("%s %s against %s of %s, on %s conversions: too few to say whether it is better or worse (%d needed)." % (
            label, fmt(actual), ref_source, fmt(ref), "{:,.1f}".format(read["conversions"]), c["needed"]))
    elif c["verdict"] and ref is not None:
        word = {"beats": "better than", "misses": "worse than", "near": "within chance of"}[c["verdict"]]
        reasons.append("%s %s against %s of %s: %s apart, %s it. Chance alone moves a figure built on %s conversions by about %s." % (
            label, fmt(actual), ref_source, fmt(ref), rules.pct(abs(c["gap"])),
            word, "{:,.1f}".format(read["conversions"]), rules.pct(c["band"])))
    if goal is not None and c["goal_verdict"] and ref_source and not ref_source.startswith("your"):
        word = {"beats": "better than", "misses": "worse than", "near": "within chance of"}[c["goal_verdict"]]
        reasons.append("Against your goal of %s: %s apart, %s it." % (fmt(goal), rules.pct(abs(c["goal_gap"])), word))
    if c["target_vs_goal"] == "looser":
        c["notes"].append("Its target of %s is looser than your goal of %s. Your goal is your limit: ask whether to bring the target to it." % (fmt(own), fmt(goal)))
    elif c["target_vs_goal"] == "stricter":
        c["notes"].append("Its target of %s is stricter than your goal of %s." % (fmt(own), fmt(goal)))
    if category == "Scale candidate" and c["goal_verdict"] == "misses":
        reasons.append("It beats its own target but misses your goal. Your goal is your limit: ask before scaling it.")
    moved = direction_check(c)
    if moved:
        c["unexpected_move"] = moved
        reasons.append(moved["text"])

    # What limits it.
    if not c["serving"]:
        limit = "Not serving"
    elif fam in ("max_conv", "max_value") and c["budget_limited"]:
        limit = "Budget, by design"
        c["notes"].append("**Official** (%s): Maximize conversions and Maximize conversion value are limited by budget by design. Judge headroom with the budget simulator, not Lost IS (budget)." % rules.SB)
    elif c["budget_limited"] and c["rank_limited"]:
        limit = "Budget and rank" if (c["lost_budget"] or 0) >= (c["lost_rank"] or 0) else "Rank and budget"
    elif c["budget_limited"]:
        limit = "Budget"
    elif c["rank_limited"]:
        limit = "Rank or target"
    elif c["lost_budget"] is None and c["lost_rank"] is None:
        limit = "Unknown: no Search impression share"
    else:
        limit = "Neither: demand or reach"
    c["limit"] = limit
    c["limit_label"] = limit + (" (top IS)" if c["top_is"] and limit not in ("Not serving", "Budget, by design") and not limit.startswith("Unknown") else "")
    if c["serving"] and c["budget_limited"] and fam not in ("max_conv", "max_value"):
        daily = metrics.div(read["cost"], c["read_days"])
        lost = c["lost_budget"]
        implied = daily * lost / (100.0 - lost) if daily and lost and lost < 95 else None
        # Budget moves go in at least two steps, each read before the next, so a first step adds
        # at most half the room. Practitioner rule.
        c["budget_evidence"] = {"avg_daily_cost": daily, "budget": c["budget"], "lost_budget": lost, "column": c["lost_budget_column"],
                                "implied_extra_per_day": implied, "first_step_per_day": implied / 2 if implied else None,
                                "monthly_limit_now": c["budget"] * rules.MONTHLY_LIMIT_FACTOR if c["budget"] else None}
    if fam in ("tcpa", "troas") and c["budget_limited"] and c["serving"]:
        c["notes"].append("**Official** (%s): since August 17, 2026 a %s campaign that is limited by budget bids toward its target rather than beating it, so added budget buys conversions at about the target, not at today's figure. Set the target you want before adding budget." % (rules.SB, c["strategy_label"]))
        if c["read_start"] < rules.AUG17.isoformat():
            c["notes"].append("The read period starts before August 17, 2026. Days before then ran under the earlier budget behaviour.")
    if fam == "manual_ecpc":
        c["notes"].append("**Official** (%s): Enhanced CPC is no longer available for Search and Display since March 31, 2025. This campaign effectively runs on Manual CPC." % rules.SB)
    if fam in rules.VALUE_FAMILIES and c["serving"]:
        meets = c["conv_last30"] >= rules.TROAS_MIN_30D
        c["notes"].append("%s conversions in the 30 days to %s, %s the %d Google asks for before Target ROAS on most campaign types (**Official**, %s)." % (
            "{:,.1f}".format(c["conv_last30"]), c["read_end"], "meeting" if meets else "below", rules.TROAS_MIN_30D, rules.SB))
    if c["shares_budget_with"]:
        c["notes"].append("Shares the budget %s with %s. A budget change moves all of them." % (c["budget_name"], ", ".join(c["shares_budget_with"])))
    if c["portfolio"] and c["family"] in ("tcpa", "troas") and c["portfolio"].lower() not in c["bid_strategy"].lower():
        c["notes"].append("Uses the bid strategy %s. If that is a portfolio, its target is set on the portfolio." % c["portfolio"])
    if c["target_varied"]:
        c["notes"].append("Its target column changes inside the read period. The comparison uses the latest target.")
    reset_day = (dt.date.fromisoformat(c["read_start"]) - dt.timedelta(days=1)).isoformat()
    # One change history row can carry several kinds, such as a new strategy with its target.
    grouped = {}
    for k, v in c["changes"].items():
        if k in MATERIAL and v["day"] >= reset_day:
            grouped.setdefault((v["day"], v["text"]), []).append(k)
    inside = [{"day": day, "kinds": [k for k in MATERIAL if k in kinds]} for (day, _), kinds in sorted(grouped.items())]
    c["stacked_changes"] = inside
    if len(inside) >= 2:
        c["notes"].append("Stacked changes close together: %s. Their effects cannot be told apart in this data (%s)." % (
            ", ".join("%s on %s" % (" and ".join(rules_kind(k) for k in s["kinds"]), s["day"]) for s in inside), rules.LP))
    created = c["changes"].get("created")
    if created and created["days_since"] >= 0:
        ctype = c["campaign_type"].lower()
        if "demand gen" in ctype:
            c["notes"].append("Created %d days before the report's last day. Google's Demand Gen guide asks for no changes during the initial learning period, and its learning page speaks of up to around 50 conversion events or 3 conversion cycles (**Official**, %s)." % (created["days_since"], rules.LP))
            if category == "Pause candidate":
                c["notes"].append("Which wins here: the case for pausing, once tracking is confirmed. **Practitioner rule.** Google's caution protects a campaign that is gathering conversions to learn from. This one has recorded none after spending %.1f times its reference cost per conversion, so the learning period has nothing to learn from, and Smart Bidding is a measurement system first (%s)." % (c["spend_multiple"], rules.SB))
        elif "performance max" in ctype:
            c["notes"].append("Created %d days before the report's last day. Google's Performance Max guidance asks for at least 6 weeks on a new campaign (**Official**, %s)." % (created["days_since"], rules.LP))
    if category == "Pause candidate":
        c["notes"].append("Confirm first that conversions are being recorded for it: the conversion actions it bids toward record conversions in other campaigns over the same days, and its goals include them. If tracking is broken, fix tracking instead of pausing.")
    if c["target_source"] == "change history":
        c["notes"].append("The target was read from the change history, because the report has no target column.")
    conv_changes = c["changes"].get("conversion")
    if conv_changes and conv_changes["days_since"] <= (c["read_days"] or 0) + (cycle or 0):
        c["notes"].append("A conversion setting changed on %s%s. Results across that date measure different things, so treat the read with lower confidence (%s)." % (
            conv_changes["day"], " at account level" if conv_changes["account_level"] else "", rules.LP))

    # The lever, for candidates. Evidence for the judgment, not the judgment.
    lever = None
    if category == "Scale candidate":
        if fam in ("max_conv", "max_value"):
            lever = "Budget, judged with the budget simulator"
        elif limit in ("Budget", "Budget and rank", "Rank and budget"):
            lever = "Budget first, then a looser target" if c["rank_limited"] else "Budget"
        elif limit == "Rank or target":
            lever = "A looser target" if fam in ("tcpa", "troas") else "Bids"
        elif limit.startswith("Neither"):
            lever = "Wider reach (query expansion). Budget and target are not what holds it back"
        else:
            lever = "Budget or target, judged with the simulators"
        half = fragile_check(c)
        if half:
            c["fragile"] = half
            reasons.append("Fragile: the later half of the read period, %s to %s, is %s against the same reference, with %s conversions." % (
                half["start"], half["end"], (rules.money(half["cpa"]) if measure == "cpa" else rules.roas_text(half["roas"])), "{:,.1f}".format(half["conversions"])))
    elif category == "Missing its target":
        checks = "search terms, conversion rate and the landing page"
        if fam in ("tcpa", "troas") and c["target_vs_goal"] in ("stricter", "same"):
            lever = "Its target is already at or stricter than your goal, so %s it further is unlikely to help on its own. Check %s first" % (
                "lowering" if fam == "tcpa" else "raising", checks)
        elif fam in ("tcpa", "troas") and c["target_vs_goal"] == "looser":
            lever = "Check %s first, then bring the target to your goal of %s" % (checks, fmt(goal))
        elif fam == "tcpa":
            lever = "Check %s and tracking first. A target change helps only if the cost per conversion the business accepts is below the current target" % checks
        elif fam == "troas":
            lever = "Check value tracking, %s and pricing first. A target change helps only if the return the business needs is above the current target" % checks
        elif fam == "max_conv":
            lever = "Add a Target CPA at the cost per conversion the business accepts"
        elif fam == "max_value":
            lever = "Add a Target ROAS at the return the business needs"
        else:
            lever = "Bids, or move to a conversion based strategy"
    elif category == "Pause candidate":
        lever = "Pause, or fix tracking if conversions should be there"
    c["lever"] = lever


def label_for(measure):
    return "Cost / conv." if measure == "cpa" else "Conv. value / cost"


def fmt_measure(measure, value):
    return rules.money(value) if measure == "cpa" else rules.roas_text(value)


def direction_check(c):
    """A target change whose result moved the other way from what the change should do."""
    reset, before, measure = c.get("reset"), c.get("before_reset"), c["measure"]
    if not reset or not before or before["conversions"] <= 0 or reset["kind"] not in ("target", "strategy"):
        return None
    early = c.get("early_read")
    after, is_early = (early, True) if early and c["category"] not in ("Pause candidate", "Not serving") else (c["read"], False)
    if not after or after["conversions"] <= 0:
        return None
    key = "cpa" if measure == "cpa" else "roas"
    new, old = (reset.get("targets") or {}).get(key), (reset.get("target_from") or {}).get(key)
    was, now = before[key], after[key]
    if new is None or was is None or now is None:
        return None
    fmt = lambda v: fmt_measure(measure, v)  # noqa: E731
    if old is not None:
        looser = new > old if measure == "cpa" else new < old
        should_improve = not looser
        what = "its target was %s from %s to %s on %s" % ("loosened" if looser else "tightened", fmt(old), fmt(new), reset["day"])
    else:
        should_improve = new < was if measure == "cpa" else new > was
        what = "a target of %s was set on %s, %s its earlier %s" % (fmt(new), reset["day"], "stricter than" if should_improve else "looser than", fmt(was))
    improved = now < was if measure == "cpa" else now > was
    if improved == should_improve or now == was:
        return None
    width = rules.band(min(before["conversions"], after["conversions"]))
    size = metrics.change(now, was)
    days_after = after.get("days") or c["read_days"]
    text = "Moved the unexpected way: %s, yet %s went from %s to %s (%s)%s, and conversions a day from %s to %s. %s The move is %s chance alone explains (about %s on %s conversions). Something else may have moved too: demand, competition, conversion values or the mix of searches." % (
        what, label_for(measure).lower(), fmt(was), fmt(now), rules.pct(size, signed=True), " in the early read" if is_early else "",
        "{:,.2f}".format(before["conversions"] / c["before_days"]) if c["before_days"] else "n/a",
        "{:,.2f}".format(after["conversions"] / days_after) if days_after else "n/a",
        "A looser target usually trades efficiency for volume." if (old is not None and not should_improve) else "A stricter target usually trades volume for efficiency.",
        "within what" if abs(size) <= width else "more than", rules.pct(width), "{:,.1f}".format(min(before["conversions"], after["conversions"])))
    return {"text": text, "was": was, "now": now, "change": size, "band": width, "early": is_early}


def rules_kind(kind):
    return KIND_WORDS.get(kind, kind)


PHRASE = {"created": "its creation", "strategy": "its latest bid strategy change", "target": "its latest target change",
          "budget": "its latest budget change", "conversion": "its latest conversion setting change"}


def phrase(kind, capital=False):
    text = PHRASE.get(kind, "its latest change")
    return text[0].upper() + text[1:] if capital else text


def fragile_check(c):
    """The later half of the read period, judged against the same reference. A scale case
    whose later half misses the reference by more than chance is fragile."""
    days, ref = c.get("_days"), c["reference"]
    if not days or c["read_days"] < 2 or ref is None:
        return None
    end = dt.date.fromisoformat(c["read_end"])
    mid = dt.date.fromisoformat(c["read_start"]) + dt.timedelta(days=c["read_days"] // 2)
    half = sum_days(days, mid, end)
    if half["cost"] <= 0:
        return None
    width = rules.band(half["conversions"])
    if c["measure"] == "cpa":
        miss = half["conversions"] == 0 or metrics.change(half["cpa"], ref) > width
    else:
        miss = half["conv_value"] == 0 or metrics.change(half["roas"], ref) < -width
    if not miss:
        return None
    return {"start": mid.isoformat(), "end": end.isoformat(), "cost": half["cost"], "conversions": half["conversions"],
            "cpa": half["cpa"], "roas": half["roas"]}


def check_window(c, cycle):
    """When a change to this campaign can first be judged, from the reference files and its own pace."""
    parts = {}
    if cycle:
        parts["conversion_cycles"] = rules.CYCLES_TO_JUDGE * cycle
    if c["conv_per_day"]:
        parts["days_to_needed_conversions"] = int(math.ceil(c["needed"] / c["conv_per_day"]))
    ctype = c["campaign_type"].lower()
    if "performance max" in ctype:
        parts["performance_max"] = rules.PMAX_DAYS
    if "demand gen" in ctype:
        parts["demand_gen_week"] = rules.DEMAND_GEN_DAYS
    return {"days": max(parts.values()) if parts else None, "parts": parts, "needed": c["needed"]}


def step_guidance(c):
    """How big a target step may be, and which file says so. No number is invented."""
    if c["category"] not in ("Scale candidate", "Missing its target") or c["family"] not in ("tcpa", "troas"):
        return None
    if c["category"] == "Missing its target" and c.get("target_vs_goal") in ("stricter", "same"):
        return None
    loosen = c["category"] == "Scale candidate"
    current = c["target_cpa"] if c["family"] == "tcpa" else c["target_roas"]
    if current is None:
        return None
    # Looser means a higher Target CPA or a lower Target ROAS.
    sign = (1 if loosen else -1) * (1 if c["family"] == "tcpa" else -1)
    if "demand gen" in c["campaign_type"].lower():
        steps = [{"share": s, "to": round(current * (1 + sign * s), 2)} for s in rules.DEMAND_GEN_STEPS + (rules.DEMAND_GEN_MAX,)]
        return {"source": rules.LP, "official": True, "current": current, "steps": steps,
                "text": "Google's Demand Gen guide asks for bid changes of 5 to 10% a week and no more than 15%."}
    text = "The reference files give no step size for this campaign type. Google says Smart Bidding reacts at once to a target change of any size on Search and Shopping, without resetting learning, and that a large move changes spend or volume by a similar amount. The step is a judgment. The evidence is the gap between actual and target."
    goal, halfway = c.get("goal"), None
    if loosen and goal and c.get("target_vs_goal") == "stricter":
        halfway = round((current + goal) / 2, 2)
        text += " Your goal of %s is the furthest a looser target may go. Halfway from today's target to your goal is %s." % (fmt_target(c, goal), fmt_target(c, halfway))
    elif loosen and goal and c.get("target_vs_goal") == "same":
        text += " Its target is already at your goal, so any looser target goes past your limit. Ask before loosening it."
    return {"source": rules.SB, "official": False, "current": current, "steps": [], "goal": goal, "halfway_to_goal": halfway, "text": text}


def build_account(campaigns, meta, rows, start, as_of, eval_end):
    serving = [c for c in campaigns if c["serving"]]
    serving_cost = sum(c["whole"]["cost"] for c in serving)
    by_family, by_category = {}, {}
    for c in campaigns:
        f = by_family.setdefault(c["strategy_label"], {"campaigns": 0, "cost": 0.0, "conversions": 0.0, "conv_value": 0.0})
        g = by_category.setdefault(c["category"], {"campaigns": 0, "cost": 0.0, "conversions": 0.0, "names": []})
        for slot in (f, g):
            slot["campaigns"] += 1
            slot["cost"] += c["whole"]["cost"]
            slot["conversions"] += c["whole"]["conversions"]
        f["conv_value"] += c["whole"]["conv_value"]
        g["names"].append(c["campaign"])
    for f in by_family.values():
        f["cpa"], f["roas"] = metrics.div(f["cost"], f["conversions"]), metrics.div(f["conv_value"], f["cost"])
    for name, g in by_category.items():
        g["share_of_serving_cost"] = None if name == "Not serving" else metrics.div(g["cost"], serving_cost)
    whole = {k: sum(c["whole"][k] for c in campaigns) for k in ("cost", "conversions", "conv_value")}
    whole["cpa"], whole["roas"] = metrics.div(whole["cost"], whole["conversions"]), metrics.div(whole["conv_value"], whole["cost"])

    # Reconcile every row of the file with the file's own total rows.
    file_sum = {k: sum((r.get(k) or 0) for r in rows) for k in ("cost", "conversions")}
    labels = [t["label"] for t in meta["total_rows"]]
    label = next((l for l in ("Total: Filtered campaigns", "Total: Account") if l in labels), None)
    totals = None
    if label:
        picked = [t for t in meta["total_rows"] if t["label"] == label]
        totals = {k: sum(t["values"].get(k) or 0 for t in picked) for k in ("cost", "conversions")}
    tolerance = 0.01 * max(len({r["date"] for r in rows}), 1)
    reconciled = None if totals is None else all(abs(file_sum[k] - totals[k]) <= tolerance for k in totals)
    compared = [c for c in campaigns if c["serving"] and not c["brand"]]
    cmp_ = {k: sum(c["whole"][k] for c in compared) for k in ("cost", "conversions", "conv_value")}
    cmp_.update({"cpa": metrics.div(cmp_["cost"], cmp_["conversions"]), "roas": metrics.div(cmp_["conv_value"], cmp_["cost"]), "names": [c["campaign"] for c in compared]})
    return {"read_whole": whole, "compared": cmp_, "serving_cost": serving_cost, "serving_campaigns": len(serving), "campaigns": len(campaigns),
            "by_strategy": by_family, "by_category": by_category,
            "reconcile": {"label": label, "file_rows": file_sum, "total_rows": totals, "reconciled": reconciled, "tolerance": tolerance}}


def thresholds():
    return [
        "Enough conversions to judge a bid strategy: %d in the period read, %d for Target ROAS. **Official**, %s." % (rules.NEEDED_DEFAULT, rules.NEEDED_TROAS, rules.SB),
        "Target ROAS readiness: %d conversions in the last 30 days for most campaign types. **Official**, %s." % (rules.TROAS_MIN_30D, rules.SB),
        "Better or worse than target: only a gap wider than chance counts. A figure built on n conversions moves by about 1 / square root of n by chance alone: 18% at 30 conversions, 10% at 100. Statistics from the campaign's own count.",
        "Limited by budget: Google's status says so, or the lost impression share to budget averages %d%% or more. Limited by rank: the lost share to rank averages %d%% or more. **Practitioner rule.** Each day is weighted by the impressions it was eligible for." % (rules.SHARE_CUT, rules.SHARE_CUT),
        "Pause candidate: no conversion after spending %d times the reference cost per conversion (its Target CPA, else your goal, else the account comparison). If it converted at that cost, a run of zero this long would happen about 5%% of the time by chance." % rules.PAUSE_MULTIPLE,
        "Recent change: a bid strategy, target, budget or conversion change less than %d conversion cycles ago, or with fewer conversions since than the number needed to judge. **Practitioner rule**, %s, and **Official** 1 to 2 conversion cycles, %s." % (rules.CYCLES_TO_JUDGE, rules.TCPA, rules.SB),
        "Demand Gen steps: 5 to 10%% a week, no more than %d%%. **Official**, Google's Demand Gen guide, %s." % (rules.DEMAND_GEN_MAX * 100, rules.LP),
        "First budget step: at most half the room that lost impression share to budget implies, so budget moves in at least two steps, each read before the next. **Practitioner rule.**",
        "Performance Max check window: 1 to 2 weeks or one conversion cycle after a significant change. **Official**, %s." % rules.LP,
    ]


def early_cells(e):
    if not e:
        return ["", None, None, None, ""]
    return [e["start"], rules.r2(e["conversions"]), rules.r2(e["cpa"]), rules.r2(e["roas"]), e["proper_read_on"] or ""]


def write_workbook(result, path):
    r2 = rules.r2
    book = xlsx.Workbook()
    header = ["Campaign", "Campaign type", "Campaign status", "Status", "Status reasons", "Bid strategy", "Daily budget", "Target CPA", "Target ROAS",
              "Read from", "Read to", "Cost", "Conversions", "Conv. value", "Cost / conv.", "Conv. value / cost", "Gap to reference", "Chance band",
              "Conversions needed", "Conversions, last 30 days", "%s, avg" % (result["budget_column_read"] or "Lost IS (budget)"),
              "%s, avg" % (result["rank_column_read"] or "Lost IS (rank)"), "Limit", "Category", "Lever", "Check after, days",
              "Your goal", "Gap to goal", "Early read from", "Early read conversions", "Early read cost / conv.", "Early read conv. value / cost", "Proper read around"]
    rows = []
    for c in result["campaigns"]:
        rd = c["read"]
        rows.append([c["campaign"], c["campaign_type"], c["campaign_status"], c["status"], c["status_reasons"], c["strategy_label"], r2(c["budget"]),
                     r2(c["target_cpa"]), r2(c["target_roas"]), c["read_start"], c["read_end"], r2(rd["cost"]), r2(rd["conversions"]),
                     r2(rd["conv_value"]), r2(rd["cpa"]), r2(rd["roas"]), c["gap"], c["band"], c["needed"], r2(c["conv_last30"]),
                     None if c["lost_budget"] is None else c["lost_budget"] / 100.0, None if c["lost_rank"] is None else c["lost_rank"] / 100.0,
                     c["limit_label"], c["category"], c["lever"] or "", c["check"]["days"], r2(c["goal"]), c["goal_gap"]] + early_cells(c["early_read"]))
    book.add_sheet("Campaigns", header, rows, formats={6: "money", 7: "money", 8: "money", 11: "money", 12: "money", 13: "money", 14: "money",
                                                       15: "money", 16: "pct", 17: "pct", 18: "int", 19: "money", 20: "pct", 21: "pct", 25: "int", 24: "wrap",
                                                       26: "money", 27: "pct", 29: "money", 30: "money", 31: "money"},
                   widths={0: 30, 4: 26, 22: 22, 23: 30, 24: 50})
    book.add_sheet("Reasons", ["Campaign", "Category", "Reason or note"],
                   [[c["campaign"], c["category"], text] for c in result["campaigns"] for text in c["reasons"] + c["notes"]],
                   formats={2: "wrap"}, widths={0: 30, 1: 30, 2: 110})
    strat = result["account"]["by_strategy"]
    book.add_sheet("By bid strategy", ["Bid strategy", "Campaigns", "Cost", "Conversions", "Conv. value", "Cost / conv.", "Conv. value / cost"],
                   [[k, v["campaigns"], r2(v["cost"]), r2(v["conversions"]), r2(v["conv_value"]), r2(v["cpa"]), r2(v["roas"])] for k, v in strat.items()],
                   formats={1: "int", 2: "money", 3: "money", 4: "money", 5: "money", 6: "money"}, widths={0: 36})
    cat = result["account"]["by_category"]
    book.add_sheet("By category", ["Category", "Campaigns", "Cost", "Conversions", "Share of serving cost", "Campaign names"],
                   [[k, v["campaigns"], r2(v["cost"]), r2(v["conversions"]), v["share_of_serving_cost"], ", ".join(v["names"])]
                    for k, v in sorted(cat.items(), key=lambda kv: CATEGORY_ORDER.index(kv[0]))],
                   formats={1: "int", 2: "money", 3: "money", 4: "pct", 5: "wrap"}, widths={0: 34, 5: 60})
    book.add_sheet("Change history read", ["Date", "Campaign", "Ad group", "What changed", "Kinds", "Days before the report's last day", "Campaign in the report"],
                   [[e["day"], e["campaign"] or "(account)", e["ad_group"], e["text"], ", ".join(rules_kind(k) for k in e["kinds"]), e["days_before_end"],
                     "Yes" if e["matched"] or not e["campaign"] else "No"] for e in reversed(result["changes"])],
                   formats={3: "wrap", 5: "int"}, widths={1: 30, 3: 70, 4: 26})
    book.save(path)


def summary(res):
    acc = res["account"]
    lines = ["# Bid strategy review", ""]
    lines += ["%s." % t for t in res["title_rows"]]
    cycle = res["cycle_days"]
    lines += ["", "Read from %s to %s (%d days). %s Money is in %s, as the report states." % (
        res["first_day"], res["last_day"], res["days_covered"],
        ("The last %d days are left out of every target comparison, because conversions are still arriving for them, so comparisons end on %s." % (cycle, res["read_end"])) if cycle
        else "The conversion cycle was given as 0 days, so no recent days are left out.",
        ", ".join(res["currencies"]) or "the account's currency")]
    if res["cycle_assumed"]:
        lines.append("**No conversion cycle was given, so %d days was assumed.** It sets three things: the last %d days left out of target comparisons, the hold after a change (%d conversion cycles, %d days), and when a change can first be checked. Rerun with --cycle-days and the real figure to replace it." % (
            cycle, cycle, rules.CYCLES_TO_JUDGE, rules.CYCLES_TO_JUDGE * cycle))
    if res["date_range"] and res["date_range"][0] < res["first_day"]:
        lines.append("**The data starts on %s, later than the report's own range (%s).** Days before it have no rows." % (res["first_day"], res["date_range"][0]))
    if res["days_covered"] < 30:
        lines.append("**The report covers fewer than 30 days.** Download 30 to 60 days for a steadier read.")
    lines += ["", "## The short answer", ""]
    cats = acc["by_category"]
    for name in CATEGORY_ORDER:
        if name in cats:
            g = cats[name]
            share = "" if name == "Not serving" else ", %s of the serving campaigns' cost" % rules.pct(g["share_of_serving_cost"])
            lines.append("- **%s:** %s%s." % (name, ", ".join(g["names"]), share))
    lines += ["", "Shares are of %s, the cost of the %d serving campaigns from %s to %s." % (rules.money(acc["serving_cost"]), acc["serving_campaigns"], res["first_day"], res["read_end"]), ""]

    has_goal = bool(res["goal_cpa"] or res["goal_roas"])
    header = ["Campaign", "Bid strategy", "Target"] + (["Your goal"] if has_goal else []) + ["Actual", "Gap to target"] + (["Gap to goal"] if has_goal else []) + [
        "Conv. read", "Learning", "Latest change", "Limit", "Category"]
    table = []
    for c in res["campaigns"]:
        data, early = shown(c)
        row = [c["campaign"], c["strategy_label"], own_target_text(c)] + ([fmt_measure(c["measure"], c["goal"]) if c["goal"] else "none"] if has_goal else [])
        row += [actual_text(c), gap_text(c, own_target(c))] + ([gap_text(c, c["goal"])] if has_goal else [])
        row += ["{:,.1f}".format(data["conversions"]) + (" (early)" if early else ""), "Yes" if c["learning"] else "No", change_text(c), c["limit_label"], c["category"]]
        table.append(row)
    lines += ["## Campaigns", "", outputs.md_table(header, table), ""]
    lines.append("Target is the campaign's own target.%s Actual is over each campaign's read period, which starts after its latest bid strategy or target change. (early) marks the days since a change that are too recent or too thin to judge." % (
        " Your goal is the limit you gave: the most per conversion, or the least conv. value / cost." if has_goal else ""))

    lines += ["", "## Each campaign", ""]
    for c in res["campaigns"]:
        lines.append("### %s: %s" % (c["campaign"], c["category"]))
        lines.append("")
        rd = c["read"]
        if c["read_days"] > 0:
            lines.append("%s, %s. Read period %s to %s (%d days): cost %s, conversions %s, conv. value %s, cost / conv. %s, conv. value / cost %s, conv. rate %s, avg. CPC %s." % (
                c["strategy_label"], c["campaign_type"] or "type not in the report", c["read_start"], c["read_end"], c["read_days"], rules.money(rd["cost"]),
                "{:,.1f}".format(rd["conversions"]), rules.money(rd["conv_value"]), rules.money(rd["cpa"]), rules.money(rd["roas"]), rules.pct(rd["cvr"], 2), rules.money(rd["cpc"])))
        else:
            lines.append("%s, %s. No read period yet: every day since %s falls inside the %d day conversion cycle." % (
                c["strategy_label"], c["campaign_type"] or "type not in the report", phrase(c["reset"]["kind"]), cycle))
        if c["before_reset"] and c["reset"] and c["before_reset"]["cost"] > 0:
            b = c["before_reset"]
            lines.append("Before %s on %s: cost %s, conversions %s, cost / conv. %s, conv. value / cost %s." % (
                phrase(c["reset"]["kind"]), c["reset"]["day"], rules.money(b["cost"]), "{:,.1f}".format(b["conversions"]), rules.money(b["cpa"]), rules.money(b["roas"])))
        if c["changes"]:
            lines.append("Latest changes read: %s." % ", ".join("%s on %s (%s)" % (rules_kind(k) if k in MATERIAL else '"%s"' % v["text"].splitlines()[0][:60], v["day"], ("%d days before the report's last day" % v["days_since"]) if v["days_since"] >= 0 else "after the report's last day")
                                                              for k, v in sorted(c["changes"].items(), key=lambda kv: kv[1]["day"])))
        lines.append("Daily budget %s. %s %s, %s %s. Limit: %s." % (
            rules.money(c["budget"]), c["lost_budget_column"] or "Lost IS (budget)", share_text(c["lost_budget"], c["lost_budget_below10_days"]),
            c["lost_rank_column"] or "Lost IS (rank)", share_text(c["lost_rank"], c["lost_rank_below10_days"]), c["limit_label"]))
        for text in c["reasons"]:
            lines.append("- %s" % text)
        if c["lever"]:
            lines.append("- Lever: %s." % c["lever"])
        ev = c.get("budget_evidence")
        if ev and ev["avg_daily_cost"]:
            text = "- Budget evidence: it spent %s a day on average in the read period against a daily budget of %s." % (rules.money(ev["avg_daily_cost"]), rules.money(ev["budget"]))
            if ev["implied_extra_per_day"]:
                text += " Its %s of %s implies at most about %s a day more at the same cost per click. That is an upper bound: the next click usually costs more%s." % (
                    ev["column"], share_text(ev["lost_budget"], 0), rules.money(ev["implied_extra_per_day"]),
                    ", and the top version counts only impressions lost among top ads, so it overstates the room" if "top" in (ev["column"] or "") else "")
                text += " A first step of up to %s a day, half of it, leaves room for a second step once the first is read (**Practitioner rule**)." % rules.money(ev["first_step_per_day"])
            if ev["monthly_limit_now"]:
                text += " Google may bill up to %s in a month at today's budget, 30.4 times the daily budget." % rules.money(ev["monthly_limit_now"])
            lines.append(text)
        g = c["step_guidance"]
        if g:
            if g["steps"]:
                lines.append("- Step size (**Official**, %s): %s From %s: %s." % (g["source"], g["text"], fmt_target(c, g["current"]),
                             ", ".join("%s gives %s" % (rules.pct(s["share"], 0), fmt_target(c, s["to"])) for s in g["steps"])))
            else:
                lines.append("- Step size (%s): %s" % (g["source"], g["text"]))
        chk = c["check"]
        if c["category"] not in ("Not serving", "Not judged on conversions") and not (c["category"].startswith("Hold") and (c.get("early_read") or {}).get("proper_read_on")):
            lines.append("- First fair check after a change: %s." % check_text(chk))
        for text in c["notes"]:
            lines.append("- %s" % text)
        lines.append("")

    lines += ["## Account", "", outputs.md_table(["Bid strategy", "Campaigns", "Cost", "Conversions", "Conv. value", "Cost / conv.", "Conv. value / cost"],
                                                  [[k, v["campaigns"], rules.money(v["cost"]), "{:,.1f}".format(v["conversions"]), rules.money(v["conv_value"]),
                                                    rules.money(v["cpa"]), rules.money(v["roas"])] for k, v in acc["by_strategy"].items()]), ""]
    w, cmp_ = acc["read_whole"], acc["compared"]
    lines += ["Two account lines, %s to %s:" % (res["first_day"], res["read_end"]), "", outputs.md_table(
        ["Line", "What it includes", "Cost", "Conversions", "Conv. value", "Cost / conv.", "Conv. value / cost"],
        [["All campaigns", "All %d campaigns in the report, paused ones included" % acc["campaigns"], rules.money(w["cost"]), "{:,.1f}".format(w["conversions"]),
          rules.money(w["conv_value"]), rules.money(w["cpa"]), rules.money(w["roas"])],
         ["Without %s" % ", ".join(res["brand"]) if res["brand"] else "Serving campaigns",
          "The %d serving campaigns%s. This is the account comparison" % (len(cmp_["names"]), (" other than " + ", ".join(res["brand"])) if res["brand"] else ""),
          rules.money(cmp_["cost"]), "{:,.1f}".format(cmp_["conversions"]), rules.money(cmp_["conv_value"]), rules.money(cmp_["cpa"]), rules.money(cmp_["roas"])]]), ""]
    rec = acc["reconcile"]
    if rec["reconciled"] is None:
        lines.append("The file has no Total: Account or Total: Filtered campaigns rows, so the rows could not be checked against Google's totals.")
    else:
        lines.append("Check against the file's own %s rows: cost %s against %s, conversions %s against %s. %s" % (
            rec["label"], rules.money(rec["file_rows"]["cost"]), rules.money(rec["total_rows"]["cost"]), "{:,.2f}".format(rec["file_rows"]["conversions"]),
            "{:,.2f}".format(rec["total_rows"]["conversions"]), "They match." if rec["reconciled"] else "**They do not match.** Some rows may be filtered out or missing."))

    lines += ["", "## Change history", ""]
    if not res["change_history_read"]:
        lines.append("Not given. Days since the last bid strategy, target or budget change are unknown, and read periods start at the report's first day. Ask for Change history, Download.")
    else:
        relevant = [e for e in res["changes"] if any(k in MATERIAL for k in e["kinds"])]
        lines.append("%d changes read, %d of them to a bid strategy, target, budget, conversion setting or a new campaign." % (len(res["changes"]), len(relevant)))
        unmatched = sorted({e["campaign"] for e in res["changes"] if e["campaign"] and not e["matched"]})
        if unmatched:
            lines.append("Campaigns in the change history but not in the report, left out: %s." % ", ".join(unmatched))
        if relevant:
            lines += ["", outputs.md_table(["Date", "Campaign", "What changed", "Days before the report's last day"],
                                           [[e["day"], e["campaign"] or "(account)", e["text"], e["days_before_end"]] for e in reversed(relevant)])]

    lines += ["", "## Thresholds", ""] + ["- %s" % t for t in res["thresholds"]]
    lines += ["", "## How the numbers were made", "",
              "- The conversion cycle is %d days%s. The last %d days are left out of target comparisons, a change is held for %d cycles, and checks wait at least that long." % (
                  res["cycle_days"], ", assumed because none was given" if res["cycle_assumed"] else ", as given", res["cycle_days"], rules.CYCLES_TO_JUDGE),
              "- An early read covers the days since a change, up to the report's last day, when the read period after it is empty or has too few conversions. It is shown, never judged.",
              "- Each campaign's read period runs from the day after its latest bid strategy, target or campaign creation change in the report to %s. Without a change history it is the whole report." % res["read_end"],
              "- Cost / conv. is cost divided by conversions. Conv. value / cost is conv. value divided by cost, written as a ratio: 4.00 is 400%.",
              "- The target is the latest value in the report's target column, or the latest set in the change history.",
              "- Impression share columns read: %s and %s. %s" % (res["budget_column_read"] or "none for budget", res["rank_column_read"] or "none for rank",
                  "These are the top of page versions: they count impressions lost among top ads, not impressions lost altogether, and run higher. Add Search lost IS (budget) and Search lost IS (rank) for the plain read (%s)." % rules.IS
                  if res["budget_column_read"] and "top" in res["budget_column_read"] else "Days written < 10% count as 0, so those averages are floors."),
              "- Status, Status reasons and Campaign status are read from each campaign's latest day.",
              "- Days to the needed conversions use the campaign's average conversions per day in its read period.",
              "", "## What this did not cover", "",
              "- Conversion tracking quality, conversion values, search terms, landing pages, auction insights and the bid strategy report's own simulators. A target can only be as good as the conversions behind it.",
              "- Profit. Conv. value / cost is not margin.",
              "- Portfolio bid strategies and shared budgets are noted where the report shows them, not modelled.",
              "- Nothing was changed in any account.", ""]
    return "\n".join(lines)


def target_text(c):
    if c["reference"] is None:
        return "none"
    return fmt_target(c, c["reference"]) + ("" if c["family"] in ("tcpa", "troas") else " (goal)")


def fmt_target(c, value):
    return rules.money(value) if c["measure"] == "cpa" else rules.roas_text(value)


def shown(c):
    """The read period, or the early read when the read period is empty or too thin to judge."""
    early = c.get("early_read")
    if early and c["category"] not in ("Pause candidate", "Not serving"):
        return early, True
    return c["read"], False


def own_target(c):
    return c["target_cpa"] if c["family"] == "tcpa" else c["target_roas"] if c["family"] == "troas" else None


def own_target_text(c):
    value = own_target(c)
    return "none" if value is None else fmt_measure(c["measure"], value)


def actual_text(c):
    data, early = shown(c)
    value = data["cpa"] if c["measure"] == "cpa" else data["roas"]
    return fmt_measure(c["measure"], value) + (" (early)" if early and value is not None else "")


def gap_text(c, ref):
    data, early = shown(c)
    gap = metrics.change(data["cpa"] if c["measure"] == "cpa" else data["roas"], ref)
    return "n/a" if gap is None else rules.pct(gap, signed=True) + (" (early)" if early else "")


def change_text(c):
    lm = c["latest_material_change"]
    if not lm:
        return "none read"
    return "%s, %d days before" % (rules_kind(lm["kind"]), lm["days_since"]) if lm["days_since"] >= 0 else "%s, after the report ends" % rules_kind(lm["kind"])


def share_text(value, below):
    if value is None:
        return "n/a"
    return "%.1f%%" % value + ((" (%d day written < 10%%)" if below == 1 else " (%d days written < 10%%)") % below if below else "")


def check_text(chk):
    if not chk["days"]:
        return "after %d conversions. It has no conversion pace to count from" % chk["needed"]
    words = {"conversion_cycles": "2 conversion cycles", "days_to_needed_conversions": "time to %d conversions at its pace" % chk["needed"],
             "performance_max": "Performance Max guidance", "demand_gen_week": "one Demand Gen weekly step"}
    parts = ", ".join("%s, %d days" % (words[k], v) for k, v in chk["parts"].items())
    return "about %d days, the longest of: %s" % (chk["days"], parts)


if __name__ == "__main__":
    main()
