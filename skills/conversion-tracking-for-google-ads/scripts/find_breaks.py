#!/usr/bin/env python3
"""Step 2 of the conversion tracking review: find breaks in conversions by day.

Reads a Google Ads report segmented by Conversion action and Day. For each
action it finds the day a steady action went to zero, stopped for a while and
came back, stepped up or down, started, or joined or left the Conversions
column. It says what share of the account's conversions each broken action
carries, which other actions broke on the same day, and, with the optional
files, whether clicks continued and which account changes came just before.
Writes a JSON file, a workbook and a summary, and prints the summary.

    python3 scripts/find_breaks.py REPORT --out OUTPUTDIR [--actions SUMMARY_EXPORT]
        [--clicks CAMPAIGN_REPORT_BY_DAY] [--changes CHANGE_HISTORY] [--action "Action name"]
"""
import argparse
import datetime as dt
import difflib
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io, metrics, outputs, xlsx  # noqa: E402
import tracking as t  # noqa: E402
import audit_actions  # noqa: E402

REPORT = "report segmented by Conversion action and Day"
MIN_RUN = 3  # the shortest run of empty days, and the fewest days around it
STEP_DAYS = 7  # a step needs a full week on each side, so a weekly pattern cannot make one
CHANCE = 0.01  # empty days count only when the action's usual rate makes them rarer than 1 in 100
STEP = 0.20  # a step must move the daily average by at least 20%
NOISE = 3.0  # and by at least three times the day to day noise
SAME_DAY = 1  # breaks this many days apart or less are grouped
CHANGE_LOOKBACK_DAYS = 3
SHOW_DAYS = 7
DOWN = ("stopped", "gap", "step_down", "left")
UP = ("started", "step_up", "joined")
KIND_TEXT = {"stopped": "Stopped", "gap": "Stopped, then came back", "step_down": "Stepped down", "step_up": "Stepped up",
             "started": "Started", "left": "Left the Conversions column", "joined": "Joined the Conversions column"}
SITUATION = {"stopped": "down", "gap": "down", "step_down": "down", "started": "up", "step_up": "up", "left": "counting", "joined": "counting"}
RULES = {"stopped": ["repair_first", "exclusion", "provisional"], "gap": ["exclusion", "provisional"],
         "step_down": ["repair_first", "provisional"], "started": ["double", "provisional"], "step_up": ["double", "provisional"],
         "left": ["bidding", "cycles"], "joined": ["bidding", "double", "cycles"]}


def mean(values):
    return sum(values) / len(values) if values else 0.0


def variance(values):
    middle = mean(values)
    return sum((v - middle) ** 2 for v in values) / len(values) if values else 0.0


def short(value):
    return ("%.2f" % value).rstrip("0").rstrip(".") if value is not None else "n/a"


def odds(chance):
    if chance < 1e-6:
        return "less than 1 in a million"
    return "about 1 in {:,.0f}".format(1 / chance) if chance > 0 else "nil"


def zero_runs(series):
    """Every run of empty days, as (first index, last index)."""
    runs, start = [], None
    for index in range(len(series) + 1):
        if index < len(series) and series[index] == 0:
            start = index if start is None else start
        elif start is not None:
            runs.append((start, index - 1))
            start = None
    return runs


def empty_run(series):
    """A run of empty days too long to be chance, or None.

    A run at the end (a stop) or at the start (a start) is one question each,
    so its chance is used as it is. A run in the middle could have fallen on
    any day, so its chance is multiplied by the number of days.
    """
    n = len(series)
    runs = [r for r in zero_runs(series) if r[1] - r[0] + 1 >= MIN_RUN]
    for first, last in sorted(runs, key=lambda r: (r[1] != n - 1, r[0] != 0, r[0] - r[1])):
        length = last - first + 1
        outside = series[:first] + series[last + 1:]
        if len(outside) < MIN_RUN:
            continue
        rate = mean(outside)
        chance = math.exp(-rate * length)
        kind = "stopped" if last == n - 1 else ("started" if first == 0 else "gap")
        tested = chance if kind != "gap" else min(1.0, chance * n)
        if tested < CHANCE:
            return first, last, kind, rate, tested
    return None


def split_day(series):
    """The index that best splits a daily series into a before and an after.

    Each side keeps at least STEP_DAYS days. The score is the gap between the
    two averages, weighted so that a split near either end needs a larger gap.
    """
    best, best_score = None, 0.0
    for cut in range(STEP_DAYS, len(series) - STEP_DAYS + 1):
        before, after = series[:cut], series[cut:]
        score = abs(mean(after) - mean(before)) * math.sqrt(len(before) * len(after) / float(len(series)))
        if score > best_score:
            best, best_score = cut, score
    return best


def split_chance(before, after):
    """The chance of conversions splitting at least this unevenly between the
    two periods if the rate never changed. An exact binomial test on the
    counts, with a normal approximation above 2,000 conversions."""
    total, low = int(round(sum(before) + sum(after))), int(round(sum(before)))
    share = len(before) / float(len(before) + len(after))
    if total == 0:
        return 1.0
    if total > 2000:
        spread = math.sqrt(total * share * (1 - share))
        return math.erfc(abs(low - total * share) / spread / math.sqrt(2))

    def log_p(k):
        return (math.lgamma(total + 1) - math.lgamma(k + 1) - math.lgamma(total - k + 1)
                + k * math.log(share) + (total - k) * math.log(1 - share))
    observed = log_p(low)
    return min(1.0, sum(math.exp(v) for v in (log_p(k) for k in range(total + 1)) if v <= observed + 1e-9))


def detect(series):
    """The one break in a daily series, or None."""
    n = len(series)
    if n < 2 * MIN_RUN or not any(series):
        return None
    run = empty_run(series)
    if run:
        first, last, kind, rate, chance = run
        cut = last + 1 if kind == "started" else first
        return {"kind": kind, "cut": cut, "end": last if kind == "gap" else n - 1, "before": mean(series[:cut]),
                "after": mean(series[cut:last + 1]) if kind == "gap" else mean(series[cut:]),
                "after_return": mean(series[last + 1:]) if kind == "gap" else None,
                "usual_rate": rate, "empty_days": last - first + 1, "chance": chance, "noise_multiple": None}
    cut = split_day(series)
    if cut is None:
        return None
    before, after = series[:cut], series[cut:]
    low, high = mean(before), mean(after)
    if low == 0:
        return None
    change = (high - low) / low
    # Counts that arrive at random vary at least as much as their average, so
    # the noise is never taken as smaller than that.
    noise = math.sqrt(max(variance(before), low) / len(before) + max(variance(after), high) / len(after))
    multiple = abs(high - low) / noise if noise else None
    if abs(change) < STEP or (multiple is not None and multiple < NOISE):
        return None
    # The split day was searched for, so the chance is multiplied by the number of days tried.
    chance = min(1.0, split_chance(before, after) * (n - 2 * STEP_DAYS + 1))
    if chance < CHANCE:
        return {"kind": "step_up" if change > 0 else "step_down", "cut": cut, "end": n - 1, "before": low, "after": high,
                "after_return": None, "usual_rate": low, "change": change, "noise_multiple": multiple, "chance": chance}
    return None


def column_break(conv_found, all_found):
    """A break in the Conversions column while All conv. held steady."""
    if not conv_found or all_found:
        return None
    moved = dict(conv_found)
    moved["kind"] = "joined" if conv_found["kind"] in UP else "left"
    return moved


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("report", help="report segmented by Conversion action and Day")
    parser.add_argument("--out", required=True, help="folder for the files")
    parser.add_argument("--actions", help="the conversions summary export, for each action's source and settings")
    parser.add_argument("--clicks", help="a campaign report segmented by Day, without the conversion segment, for clicks")
    parser.add_argument("--changes", help="a change history export")
    parser.add_argument("--action", action="append", default=[], help="an action to show in full even with no break; repeat for more")
    args = parser.parse_args()

    meta, rows = t.load(args.report, REPORT)
    io.require(meta, ["day", "conversion_action"], REPORT, labels=t.LABELS)
    has = meta["columns"]
    if "all_conv" not in has and "conversions" not in has:
        raise SystemExit("I can't find a Conversions or All conv. column in the %s. Add All conv. and Conversions and download it again." % REPORT)
    key = "all_conv" if "all_conv" in has else "conversions"
    label = "All conv." if key == "all_conv" else "Conversions"
    both = "all_conv" in has and "conversions" in has

    per_action, campaign_status, skipped = {}, {}, {"no_day": 0, "no_action": 0}
    for row in rows:
        day, name = dates.parse_day(row.get("day")), t.clean(row.get("conversion_action"))
        if not day:
            skipped["no_day"] += 1
            continue
        if not name:
            skipped["no_action"] += 1
            continue
        slot = per_action.setdefault(name, {"volume": {}, "conv": {}, "campaigns": {}})
        volume = row.get(key) or 0.0
        slot["volume"][day] = slot["volume"].get(day, 0.0) + volume
        slot["conv"][day] = slot["conv"].get(day, 0.0) + (row.get("conversions") or 0.0)
        campaign = t.clean(row.get("campaign"))
        if campaign:
            days_of = slot["campaigns"].setdefault(campaign, {})
            days_of[day] = days_of.get(day, 0.0) + volume
            if t.clean(row.get("campaign_status")):
                campaign_status[campaign] = t.clean(row.get("campaign_status"))
    if not per_action:
        raise SystemExit("I can't read any rows with a day and a conversion action. Add the Day and Conversion action segments and download the report again.")

    data_days = sorted({d for slot in per_action.values() for d in slot["volume"]})
    span = t.title_range(meta)
    first, last = data_days[0], data_days[-1]
    if span:
        first, last = min(first, span[0]), max(last, span[1])
    days = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
    n = len(days)
    if n < 2 * MIN_RUN:
        raise SystemExit("The report covers %d days. A break needs %d days on each side, so download at least 30 days." % (n, MIN_RUN))
    starts_late = bool(span) and data_days[0] > span[0]

    def series(slot_days):
        return [slot_days.get(d, 0.0) for d in days]

    names = sorted(per_action, key=lambda name: -sum(per_action[name]["volume"].values()))
    focus = []
    for wanted in args.action:
        match = next((name for name in names if name.lower() == wanted.strip().lower()), None)
        if not match:
            near = difflib.get_close_matches(wanted, names, n=3, cutoff=0.4)
            raise SystemExit("There is no conversion action named \"%s\" in the report. %s" % (
                wanted, "Did you mean: %s?" % "; ".join(near) if near else "The actions in it are: %s." % "; ".join(names)))
        focus.append(match)

    settings, not_in_summary, audit_findings = {}, [], []
    if args.actions:
        smeta, listed, info = t.read_actions(args.actions)
        settings = {a["name"].lower(): a for a in listed + info["removed"]}
        not_in_summary = [name for name in names if name.lower() not in settings]
        if listed:
            # The same findings, with the same numbers, as audit_actions.py gives.
            audit_findings = audit_actions.assess(smeta, listed, info)["findings"]
    conv_account = None

    clicks, clicks_status, clicks_note = {}, {}, None
    if args.clicks:
        cmeta, crows = t.load(args.clicks, "campaign report segmented by Day")
        io.require(cmeta, ["day", "clicks"], "campaign report segmented by Day", labels=t.LABELS)
        for row in crows:
            day = dates.parse_day(row.get("day"))
            if not day:
                continue
            campaign = t.clean(row.get("campaign")) or "(account)"
            clicks.setdefault(campaign, {})[day] = clicks.get(campaign, {}).get(day, 0.0) + (row.get("clicks") or 0.0)
            if t.clean(row.get("campaign_status")):
                clicks_status[campaign] = t.clean(row.get("campaign_status"))
        if not any(v for c in clicks.values() for v in c.values()):
            clicks_note = ("The clicks report has no clicks in it. A report segmented by Conversion action shows no clicks, "
                           "so download the campaign report by Day without that segment.")
            clicks = {}
        else:
            ours = {c for slot in per_action.values() for c in slot["campaigns"]}
            if ours and not ours & set(clicks):
                clicks_note = "No campaign name in the clicks report matches the conversions report, so clicks were added up for the whole account."
    for campaign, status in clicks_status.items():
        campaign_status.setdefault(campaign, status)

    changes = []
    if args.changes:
        hmeta, hrows = t.load(args.changes, "change history export")
        io.require(hmeta, ["changed_at", "changes"], "change history export", labels=t.LABELS)
        for row in hrows:
            day = dates.parse_day(row.get("changed_at"))
            if day:
                text = "; ".join(part.strip() for part in t.clean(row.get("changes")).splitlines() if part.strip())
                changes.append({"day": day, "campaign": t.clean(row.get("campaign")), "user": t.clean(row.get("user")), "changes": text})

    account = [sum(per_action[name]["volume"].get(d, 0.0) for name in names) for d in days]
    account_conv = [sum(per_action[name]["conv"].get(d, 0.0) for name in names) for d in days] if both else None
    conv_account = account_conv if both else (account if key == "conversions" else None)
    rows_total = sum(r.get(key) or 0 for r in rows)
    sums, doubtful = t.file_totals(args.report, meta, [key])
    check = t.reconcile(sums, key, rows_total, len(rows))

    def window(found):
        """Day indexes of the base period: before a fall, after a rise."""
        cut = found["cut"]
        return list(range(0, cut)) if found["kind"] in DOWN else list(range(cut, found["end"] + 1))

    def period(indexes):
        return "%s to %s" % (days[indexes[0]].isoformat(), days[indexes[-1]].isoformat())

    breaks, steady = [], []
    for name in names:
        slot = per_action[name]
        vol = series(slot["volume"])
        conv = series(slot["conv"]) if both else None
        found = detect(vol)
        column = "volume"
        if both and not found:
            found = column_break(detect(conv) if any(conv) else None, None)
            column = "conv" if found else column
        setting = settings.get(name.lower())
        in_conversions = (setting["optimization"] == "Primary") if setting and setting["optimization"] else (
            sum(conv) > 0 if both else (key == "conversions" or None))
        summary_row = {"action": name, "total": sum(vol), "share": metrics.div(sum(vol), sum(account)),
                       "days_with_conversions": sum(1 for v in vol if v), "in_conversions": in_conversions,
                       "optimization": setting["optimization"] if setting else "", "source": setting["source"] if setting else "",
                       "first_day": next((days[i].isoformat() for i, v in enumerate(vol) if v), None),
                       "last_day": next((days[i].isoformat() for i in range(n - 1, -1, -1) if vol[i]), None)}
        if not found:
            summary_row["break"] = ""
            steady.append(summary_row)
            continue
        used = conv if column == "conv" else vol
        base = window(found)
        affected = list(range(found["cut"], found["end"] + 1))
        expected = found["usual_rate"] * len(affected) if found["kind"] in DOWN else found["before"] * len(affected)
        actual = sum(used[i] for i in affected)
        item = dict(found)
        item.update({"action": name, "day": days[found["cut"]].isoformat(), "end_day": days[found["end"]].isoformat(),
                     "what": KIND_TEXT[found["kind"]], "direction": "down" if found["kind"] in DOWN else "up",
                     "column": "Conversions" if column == "conv" else label, "runs_to_end": found["end"] == n - 1,
                     "base_period": period(base), "affected_period": period(affected), "affected_days": len(affected),
                     "share": metrics.div(sum(vol[i] for i in base), sum(account[i] for i in base)),
                     "conversions_share": metrics.div(sum(conv[i] for i in base), sum(account_conv[i] for i in base)) if both else None,
                     "difference": actual - expected, "expected": expected, "actual": actual,
                     "in_conversions": in_conversions, "source": setting["source"] if setting else "",
                     "optimization": setting["optimization"] if setting else "", "status": setting["status"] if setting else "",
                     "family": setting["family"] if setting else "other", "summary_row": summary_row,
                     "share_whole": summary_row["share"],
                     "conversions_share_whole": metrics.div(sum(conv), sum(account_conv)) if both else None,
                     "daily": [[days[i].isoformat(), round(used[i], 2)] for i in range(max(0, found["cut"] - SHOW_DAYS), n)]})
        conv_used = conv if both else (vol if key == "conversions" else None)
        if conv_used is not None:
            rate_before, rate_during = mean(conv_used[:found["cut"]]), mean([conv_used[i] for i in affected])
            item["conversions_effect"] = {"before": rate_before, "during": rate_during, "per_day": rate_during - rate_before,
                                          "total": (rate_during - rate_before) * len(affected), "open_at_end": found["end"] == n - 1}
        item["findings"] = [{"id": f["id"], "type": f["type"], "title": f["title"], "category": f["category"],
                             "with": [a for a in f["actions"] if a.lower() != name.lower()]}
                            for f in audit_findings if name.lower() in [a.lower() for a in f["actions"]]]
        carriers = {c: sum(v for d, v in cdays.items() if first + dt.timedelta(days=base[0]) <= d <= first + dt.timedelta(days=base[-1]))
                    for c, cdays in slot["campaigns"].items()}
        carried = sum(carriers.values())
        item["campaigns"] = [{"campaign": c, "share_of_action": metrics.div(v, carried), "status": campaign_status.get(c, "")}
                             for c, v in sorted(carriers.items(), key=lambda kv: -kv[1]) if v]
        item["paused_campaigns"] = [c["campaign"] for c in item["campaigns"] if c["status"].lower().startswith("paused")]
        if clicks:
            names_for_clicks = [c["campaign"] for c in item["campaigns"] if c["campaign"] in clicks] or list(clicks)
            before_idx = list(range(0, found["cut"]))

            def per_day(indexes):
                present = [i for i in indexes if any(days[i] in clicks[c] for c in names_for_clicks)]
                total_clicks = sum(clicks[c].get(days[i], 0.0) for c in names_for_clicks for i in present)
                return metrics.div(total_clicks, len(present)), total_clicks, present
            b_rate, b_clicks, b_days = per_day(before_idx)
            a_rate, a_clicks, a_days = per_day(affected)
            item["clicks"] = {"campaigns": names_for_clicks, "per_day_before": b_rate, "per_day_after": a_rate,
                              "change": metrics.change(a_rate, b_rate),
                              "per_click_before": metrics.div(sum(used[i] for i in b_days), b_clicks),
                              "per_click_after": metrics.div(sum(used[i] for i in a_days), a_clicks)}
        item["changes_before"] = [
            {"day": c["day"].isoformat(), "user": c["user"], "campaign": c["campaign"], "changes": c["changes"]} for c in changes
            if 0 <= (days[found["cut"]] - c["day"]).days <= CHANGE_LOOKBACK_DAYS
            and (c["campaign"] in ("",) or c["campaign"] in carriers or name.lower() in c["changes"].lower())]
        item["rules"] = [t.rule(r) for r in RULES[found["kind"]] + (["click_date"] if item["runs_to_end"] and item["direction"] == "down" else [])]
        item["checks"] = t.outside_checks(SITUATION[found["kind"]], item["family"], item["day"])
        summary_row["break"] = "%s on %s" % (item["what"], item["day"])
        breaks.append(item)

    for item in breaks:
        here = dt.date.fromisoformat(item["day"])
        item["same_day"] = [o["action"] for o in breaks if o is not item and abs((dt.date.fromisoformat(o["day"]) - here).days) <= SAME_DAY]
        if item["direction"] == "down":
            cut = item["cut"]
            item["kept_recording"] = [name for name in names if name != item["action"] and name not in item["same_day"]
                                      and sum(per_action[name]["volume"].get(days[i], 0.0) for i in range(cut, n)) > 0]
        else:
            item["kept_recording"] = []
    breaks.sort(key=lambda b: -(b["share"] or 0))
    for number, item in enumerate(breaks, start=1):
        item["id"] = "B%d" % number

    # The account's Conversions column, between the days the breaks start and end.
    edges = sorted({b["cut"] for b in breaks} | {b["end"] + 1 for b in breaks if b["kind"] == "gap"})
    bounds = [0] + [e for e in edges if 0 < e < n] + [n]
    periods = [{"from": days[lo].isoformat(), "to": days[hi - 1].isoformat(), "days": hi - lo,
                "conversions_per_day": mean(conv_account[lo:hi]) if conv_account else None, "volume_per_day": mean(account[lo:hi]),
                "breaks_starting": [b["id"] for b in breaks if b["cut"] == lo]} for lo, hi in zip(bounds, bounds[1:]) if hi > lo]
    for b in breaks:
        b["account_conversions"] = {"before": mean(conv_account[:b["cut"]]), "after": mean(conv_account[b["cut"]:])} if conv_account else None
    effects = [b for b in breaks if b.get("conversions_effect")]
    still_open = [b for b in effects if b["conversions_effect"]["open_at_end"]]
    net = None
    if conv_account:
        at_end = sum(b["conversions_effect"]["per_day"] for b in still_open)
        net = {"rises": sum(b["conversions_effect"]["total"] for b in effects if b["conversions_effect"]["total"] > 0),
               "falls": sum(b["conversions_effect"]["total"] for b in effects if b["conversions_effect"]["total"] < 0),
               "total": sum(b["conversions_effect"]["total"] for b in effects), "per_day_at_end": at_end,
               "open_at_end": [b["id"] for b in still_open], "first_period_per_day": periods[0]["conversions_per_day"],
               "last_period_per_day": periods[-1]["conversions_per_day"], "last_period_without_open_breaks": periods[-1]["conversions_per_day"] - at_end}

    account_break = detect(account)
    account_conv_break = detect(account_conv) if both else None

    def describe_account(found, column):
        if not found:
            return None
        return {"column": column, "what": KIND_TEXT[found["kind"]], "day": days[found["cut"]].isoformat(),
                "before": found["before"], "after": found["after"]}

    out = outputs.ensure_dir(args.out)
    result = {"report": os.path.basename(args.report), "title_rows": meta["title_rows"], "column": label, "both_columns": both,
              "first_day": first.isoformat(), "last_day": last.isoformat(), "days": n, "starts_late": starts_late,
              "first_day_with_conversions": data_days[0].isoformat(), "range_from": "the date range above the header" if span else "the days in the file",
              "actions": len(names), "total": sum(account), "reconcile": check, "rows_named_total": doubtful, "skipped_rows": skipped,
              "account_break": describe_account(account_break, label), "account_conversions_break": describe_account(account_conv_break, "Conversions"),
              "thresholds": {"min_empty_days": MIN_RUN, "step_days": STEP_DAYS, "chance": CHANCE, "step": STEP, "noise": NOISE, "same_day": SAME_DAY, "change_lookback_days": CHANGE_LOOKBACK_DAYS},
              "summary_read": bool(args.actions), "not_in_summary": not_in_summary, "clicks_read": bool(clicks), "clicks_note": clicks_note,
              "change_history_read": bool(args.changes), "breaks": [{k: v for k, v in b.items() if k != "summary_row"} for b in breaks],
              "steady": steady, "action_totals": [b["summary_row"] for b in breaks] + steady, "focus": focus,
              "conversions_by_period": periods, "net_effect_on_conversions": net, "audit_findings_linked": bool(audit_findings)}
    outputs.write_json(os.path.join(out, "conversion-breaks.json"), result)

    def r2(value):
        return None if value is None else round(value, 2)

    def yes_no(value):
        return "" if value is None else ("Yes" if value else "No")

    check_pairs = [(c, b["id"]) for b in breaks for c in b["checks"]]
    every_row = [b["summary_row"] for b in breaks] + steady
    book = xlsx.Workbook()
    book.add_sheet("Summary", ["Measure", "Value"], [
        ["Report", " / ".join(meta["title_rows"]) or os.path.basename(args.report)], ["Days", "%d, %s to %s" % (n, first.isoformat(), last.isoformat())],
        ["Conversion actions", str(len(names))], ["Column used", label], [label + ", all actions", t.two(sum(account))],
        ["Breaks found", str(len(breaks))], ["Check against the file's own total", t.reconcile_line(check, label)]], widths={0: 36, 1: 100})
    book.add_sheet("Breaks", ["Id", "Conversion action", "What happened", "From", "To", "Column", "Daily before", "Daily after",
                              "Share of %s, whole report" % label, "Share of %s, days before a fall or since a rise" % label,
                              "Share of Conversions, whole report", "Share of Conversions, days before a fall or since a rise",
                              "Effect on Conversions a day", "Effect on Conversions, total", "Difference from usual rate", "In Conversions",
                              "Source", "Linked audit findings", "Same day", "Clicks a day before", "Clicks a day after", "Account changes just before"],
                   [[b["id"], b["action"], b["what"], b["day"], b["end_day"], b["column"], r2(b["before"]), r2(b["after"]), b["share_whole"], b["share"],
                     b["conversions_share_whole"], b["conversions_share"], r2(b.get("conversions_effect", {}).get("per_day")),
                     r2(b.get("conversions_effect", {}).get("total")), r2(b["difference"]), yes_no(b["in_conversions"]), b["source"],
                     "; ".join("%s %s" % (f["id"], f["title"]) for f in b["findings"]), "; ".join(b["same_day"]),
                     r2(b.get("clicks", {}).get("per_day_before")), r2(b.get("clicks", {}).get("per_day_after")),
                     "; ".join("%s: %s" % (c["day"], c["changes"]) for c in b["changes_before"])] for b in breaks],
                   formats={6: "money", 7: "money", 8: "pct", 9: "pct", 10: "pct", 11: "pct", 12: "money", 13: "money", 14: "money",
                            19: "money", 20: "money", 21: "wrap"}, widths={1: 30, 17: 40, 21: 70})
    book.add_sheet("Conversions by period", ["From", "To", "Days", "Conversions a day", "%s a day" % label, "Breaks that start"],
                   [[p["from"], p["to"], p["days"], r2(p["conversions_per_day"]), r2(p["volume_per_day"]), ", ".join(p["breaks_starting"])] for p in periods],
                   formats={2: "int", 3: "money", 4: "money"})
    book.add_sheet("Checks outside Google Ads", ["Who usually does it", "Check", "Label", "Source", "For breaks"],
                   [[owner, i["check"]["check"], i["check"]["label"], i["check"]["source"], ", ".join(i["refs"])]
                    for owner, items in t.by_owner(check_pairs) for i in items],
                   formats={1: "wrap"}, widths={0: 40, 1: 90, 3: 50})
    book.add_sheet("Actions", ["Conversion action", "Optimization", "Source", label, "Share of " + label, "Days with conversions",
                               "First day", "Last day", "In Conversions", "Break"],
                   [[r["action"], r["optimization"], r["source"], r2(r["total"]), r["share"], r["days_with_conversions"], r["first_day"],
                     r["last_day"], yes_no(r["in_conversions"]), r["break"]] for r in sorted(every_row, key=lambda r: -r["total"])],
                   formats={3: "money", 4: "pct", 5: "int"}, widths={0: 30, 9: 40})
    daily_header = ["Day", label + ", all actions"] + (["Conversions, all actions"] if both else []) + names
    daily_rows = [[d.isoformat(), r2(account[i])] + ([r2(account_conv[i])] if both else []) +
                  [r2(per_action[name]["volume"].get(d, 0.0)) for name in names] for i, d in enumerate(days)]
    book.add_sheet("Daily by action", daily_header, daily_rows, formats={i: "money" for i in range(1, len(daily_header))})
    book.save(os.path.join(out, "conversion-breaks.xlsx"))

    lines = ["# Conversion breaks", ""]
    lines += ["%s." % title for title in meta["title_rows"]] or [os.path.basename(args.report)]
    lines += ["", "## What was read", "",
              "- %d days, %s to %s, taken from %s." % (n, first.isoformat(), last.isoformat(), result["range_from"])]
    if starts_late:
        lines.append("- No action recorded anything before %s. Every average below uses all %d days of the range." % (data_days[0].isoformat(), n))
    lines.append("- %d conversion actions. %s across all of them: %s. %s" % (
        len(names), label, t.two(sum(account)), "The Conversions column was read too, to see actions join or leave it." if both else
        ("Without All conv., a Secondary action shows nothing, so add All conv. to see every action." if key == "conversions" else
         "Without the Conversions column, an action joining or leaving it cannot be seen.")))
    lines.append("- " + t.reconcile_line(check, label))
    if skipped["no_day"] or skipped["no_action"]:
        lines.append("- Rows left out: %d with no readable day, %d with no conversion action." % (skipped["no_day"], skipped["no_action"]))
    if doubtful:
        lines.append("- Rows that start with the word Total were read as total rows: %s." % ", ".join(doubtful))
    lines.append("- Conversions summary: %s." % ("read" + ("; not in it: %s" % ", ".join(not_in_summary) if not_in_summary else "") if args.actions
                                                 else "not provided, so each action's source and settings are unknown and the checks are general"))
    lines.append("- Clicks: %s" % (clicks_note or ("read." if clicks else "not provided, so it is not known whether traffic continued.")))
    lines.append("- Change history: %s" % ("read." if args.changes else "not provided, so account changes before each break are not listed."))

    lines += ["", "## Account", ""]
    if conv_account and breaks:
        lines += ["The Conversions column for the whole account, between the days the breaks start and end:", "",
                  outputs.md_table(["From", "To", "Days", "Conversions a day", "%s a day" % label, "Breaks that start"],
                                   [[p["from"], p["to"], p["days"], short(p["conversions_per_day"]), short(p["volume_per_day"]), ", ".join(p["breaks_starting"])]
                                    for p in periods]), ""]
        lines.append("- Effect of the breaks on Conversions over the report, each at its action's earlier rate: rises add %s, falls take away %s, net %s. These are estimates." % (
            short(net["rises"]), short(-net["falls"]), "%+.2f" % net["total"]))
        if still_open:
            lines.append("- On the last day the breaks still open change Conversions by %+.2f a day: %s. Conversions ran at %s a day from %s; without those breaks it would be about %s a day, against %s a day from %s to %s. This is an estimate." % (
                net["per_day_at_end"], "; ".join("%s %+.2f" % (b["id"], b["conversions_effect"]["per_day"]) for b in still_open),
                short(net["last_period_per_day"]), periods[-1]["from"], short(net["last_period_without_open_breaks"]),
                short(net["first_period_per_day"]), periods[0]["from"], periods[0]["to"]))
    elif not conv_account:
        lines.append("- The report has no Conversions column, so the effect on the column bidding uses cannot be shown. Add Conversions to the report.")
    for found, column in ((account_break, label), (account_conv_break, "Conversions")):
        if found:
            lines.append("- %s for all actions together: %s on %s, from %s a day to %s a day." % (
                column, KIND_TEXT[found["kind"]].lower(), days[found["cut"]].isoformat(), short(found["before"]), short(found["after"])))
    if not account_break and not account_conv_break:
        lines.append("- No break in the account total. A break in one action can hide inside a steady total when another action grows, so each action was checked on its own.")

    lines += ["", "## Breaks found", ""]
    if not breaks:
        lines.append("- None. No action stopped, came back after a stop, stepped up or down, started, or moved in or out of the Conversions column under the rules below.")
    for b in breaks:
        lines += ["### %s. %s: %s on %s" % (b["id"], b["action"], b["what"], b["day"]), ""]
        if b["kind"] in ("stopped", "gap"):
            lines.append("- %s recorded %s a day on the other days, then nothing on %d days in a row, %s to %s. At that earlier rate a run that long is very unlikely by chance, "
                         "if conversions arrive at random around a steady rate." % (b["column"], short(b["usual_rate"]), b["empty_days"], b["day"], b["end_day"]))
            if b["kind"] == "gap":
                lines.append("- It came back on %s at %s a day." % ((dt.date.fromisoformat(b["end_day"]) + dt.timedelta(days=1)).isoformat(), short(b["after_return"])))
        elif b["kind"] == "started" or (b["kind"] == "joined" and b["before"] == 0):
            lines.append("- %s showed nothing from %s, then %s a day from %s to %s." % (b["column"], days[0].isoformat(), short(b["after"]), b["day"], b["end_day"]))
        else:
            lines.append("- %s went from %s a day before %s to %s a day after, a change of %s. The difference is %s the day to day noise." % (
                b["column"], short(b["before"]), b["day"], short(b["after"]), metrics.pct(metrics.change(b["after"], b["before"])),
                "%.1f times" % b["noise_multiple"] if b["noise_multiple"] else "far above"))
        if b["kind"] in ("left", "joined"):
            lines.append("- All conv. for this action held steady, so the action kept recording and only its place in the Conversions column changed.")
        near = "the days before it" if b["direction"] == "down" else "the days since"
        lines.append("- Share of %s for all actions: %s over the whole report, %s to %s; %s over %s, %s." % (
            label, metrics.pct(b["share_whole"]), first.isoformat(), last.isoformat(), metrics.pct(b["share"]), near, b["base_period"]))
        if b["conversions_share"] is not None:
            lines.append("- Share of Conversions for all actions: %s over the whole report; %s over %s." % (
                metrics.pct(b["conversions_share_whole"]), metrics.pct(b["conversions_share"]), near))
        if b.get("conversions_effect"):
            e = b["conversions_effect"]
            lines.append("- Effect on the Conversions column: %+.2f a day, from %s a day before %s to %s a day after, about %+.2f in all. This is an estimate." % (
                e["per_day"], short(e["before"]), b["day"], short(e["during"]), e["total"]))
        if b.get("account_conversions"):
            lines.append("- Conversions for the whole account: %s a day before %s, %s a day from then to %s." % (
                short(b["account_conversions"]["before"]), b["day"], short(b["account_conversions"]["after"]), last.isoformat()))
        for f in b["findings"]:
            if f["type"] == "double_count" and b["direction"] == "up":
                lines.append("- **Linked to audit finding %s, %s.** It is Primary in %s, where %s %s also Primary from another source. From %s both can count the same conversion." % (
                    f["id"], f["title"], f["category"], " and ".join(f["with"]), "is" if len(f["with"]) == 1 else "are", b["day"]))
            else:
                lines.append("- Linked to audit finding %s, %s." % (f["id"], f["title"]))
        if b["direction"] == "down":
            lines.append("- At its usual rate, about %s fewer in %s than expected from %s to %s. This is an estimate." % (short(-b["difference"]), b["column"], b["day"], b["end_day"]))
        elif b["column"] != "Conversions" or not b.get("conversions_effect"):
            lines.append("- That is about %s more in %s than its earlier rate would give, from %s to %s." % (short(b["difference"]), b["column"], b["day"], b["end_day"]))
        counted = {True: "Yes", False: "No", None: "unknown"}[b["in_conversions"]]
        lines.append("- Counts in Conversions, the column bidding uses: %s.%s" % (counted, " Source: %s. Status: %s." % (b["source"] or "not shown", b["status"] or "not shown") if b["source"] or b["status"] else ""))
        lines.append("- Other actions that broke within %d day: %s." % (SAME_DAY, ", ".join(b["same_day"]) if b["same_day"] else "none"))
        if b["direction"] == "down":
            lines.append("- Actions that kept recording after %s: %d of %d others." % (b["day"], len(b["kept_recording"]), len(names) - 1))
        if b["campaigns"]:
            lines.append("- Campaigns that carried it: %s." % "; ".join("%s %s%s" % (c["campaign"], metrics.pct(c["share_of_action"]), " (%s now)" % c["status"] if c["status"] else "") for c in b["campaigns"]))
        if b["paused_campaigns"]:
            lines.append("- Paused now: %s. **Official:** Google names paused campaigns as a usual reason for no recent conversions. Check the date they were paused." % ", ".join(b["paused_campaigns"]))
        if b.get("clicks"):
            c = b["clicks"]
            lines.append("- Clicks in those campaigns: %s a day before, %s a day from %s (%s). This action per click: %s before, %s after." % (
                short(c["per_day_before"]), short(c["per_day_after"]), b["day"], metrics.pct(c["change"]), "{:.4f}".format(c["per_click_before"]) if c["per_click_before"] is not None else "n/a",
                "{:.4f}".format(c["per_click_after"]) if c["per_click_after"] is not None else "n/a"))
        if args.changes:
            if b["changes_before"]:
                lines.append("- Account changes in the %d days before:" % CHANGE_LOOKBACK_DAYS)
                lines += ["  - %s by %s%s: %s" % (c["day"], c["user"] or "unknown", ", " + c["campaign"] if c["campaign"] else "", c["changes"]) for c in b["changes_before"]]
            else:
                lines.append("- No account change is recorded in the %d days before." % CHANGE_LOOKBACK_DAYS)
        lines.append("- Daily %s from %s to %s, the last day of the report: %s" % (
            b["column"], b["daily"][0][0], last.isoformat(), ", ".join("%s %s" % (d[5:], short(v)) for d, v in b["daily"])))
        lines += ["", "Rules that apply:", ""] + ["- " + t.rule_text(r) for r in RULES[b["kind"]] + (["click_date"] if b["runs_to_end"] and b["direction"] == "down" else [])]
        lines += ["", "Checks outside Google Ads reports: in the list below, marked %s." % b["id"], ""]
    if breaks:
        lines += ["## Checks outside Google Ads, by who usually does them", ""] + t.owner_lines(check_pairs, "break")

    if focus:
        lines += ["", "## Actions you asked about", ""] if not breaks else ["## Actions you asked about", ""]
        for name in focus:
            row = next(r for r in every_row if r["action"] == name)
            vol = series(per_action[name]["volume"])
            half = n // 2
            lines.append("- **%s:** %s %s over %d days, %s of the total. %s a day in the first %d days, %s a day in the last %d. %s." % (
                name, t.two(row["total"]), label, n, metrics.pct(row["share"]), short(mean(vol[:half])), half, short(mean(vol[half:])), n - half,
                row["break"] or "No break under the rules below"))
        lines.append("")
    lines += ["## Actions with no break", ""]
    lines.append(outputs.md_table(["Conversion action", label, "Share", "Days with conversions", "Last day"],
                                  [[r["action"], t.two(r["total"]), metrics.pct(r["share"]), "%d of %d" % (r["days_with_conversions"], n), r["last_day"] or ""] for r in steady])
                 if steady else "- None.")
    lines += ["", "## How the numbers were made", "",
              "- A day with no row for an action counts as zero for that action. Every day from %s to %s is in the series." % (first.isoformat(), last.isoformat()),
              "- A stop is a run of at least %d days with nothing, when the action's rate on the other days makes such a run rarer than 1 in %d. "
              "This assumes conversions arrive at random around a steady rate." % (MIN_RUN, round(1 / CHANCE)),
              "- A step is the day that best splits the series into a before and an after, each at least %d days long so that a weekly pattern cannot make one. "
              "It counts when the daily average moves %d%% or more and the move is at least %d times the day to day noise. The noise is never taken as smaller "
              "than conversions arriving at random would give." % (STEP_DAYS, STEP * 100, NOISE),
              "- A share is the action's part of %s or Conversions for all actions in this report. Each break gives it over the whole report and over the days before a fall or since a rise, with both periods named." % label,
              "- The effect on Conversions is the action's daily Conversions after the break minus its daily Conversions before it. The net effect adds these up. Both are estimates.",
              "- Breaks within %d day of each other are listed together. Account changes are listed from the %d days before a break." % (SAME_DAY, CHANGE_LOOKBACK_DAYS),
              "- A change just before a break is a lead to check, not proof of the cause.", "",
              "## What this did not cover", "",
              "- The website, the tags, the consent banner and any upload. The checks above say what to look at there.",
              "- Which goals each campaign uses. A report does not show this.",
              "- Conversions are reported on the day of the click, and recent days can still fill in. A fall in the last days of the file can be a delay, not a break.",
              "- An action whose conversions are too few to tell a stop from chance. The table above shows how often each one recorded."]
    text = "\n".join(lines) + "\n"
    with open(os.path.join(out, "conversion-breaks.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    print("Wrote conversion-breaks.json, conversion-breaks.xlsx and conversion-breaks.md to %s" % out)


if __name__ == "__main__":
    main()
