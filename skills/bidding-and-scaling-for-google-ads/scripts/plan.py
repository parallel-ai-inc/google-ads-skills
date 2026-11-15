#!/usr/bin/env python3
"""Check a plan of bid strategy, target and budget changes against the review, then write it in steps.

You write the plan as JSON after reading the review. This script checks every change
against the review and the reference files, works out every number (the change in percent,
the new monthly limit, when to check, and what would mean rolling back), and writes a plan a
client can read, a workbook, and one Google Ads Editor file per step. It changes nothing in
any account. When a check fails it prints what to fix and writes nothing.

    python3 scripts/plan.py --review OUTPUT/bidding-review.json --plan PLAN.json --out OUTPUT

Plan format:
    {"steps": [
      {"step": 1, "campaign": "Name as in the report", "change": "budget", "to": 280, "why": "..."},
      {"step": 1, "campaign": "...", "change": "target_cpa", "to": 55, "why": "..."},
      {"step": 2, "campaign": "...", "change": "target_roas", "to": 3.6, "why": "..."},
      {"step": 1, "campaign": "...", "change": "bid_strategy", "to": "Target CPA", "target": 60, "why": "..."},
      {"step": 1, "campaign": "...", "change": "pause" | "hold" | "investigate", "why": "..."}]}
Target ROAS is a ratio: 3.6 for 360%. "override": "reason" lets a change touch a campaign
the review holds.
"""
import argparse
import difflib
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics, outputs, xlsx  # noqa: E402
import bidding_rules as rules  # noqa: E402

CHANGES = ("budget", "target_cpa", "target_roas", "bid_strategy", "pause", "hold", "investigate")
EDITS = ("budget", "target_cpa", "target_roas", "bid_strategy", "pause")
STRATEGIES = {"target cpa": "tcpa", "target roas": "troas", "maximize conversions": "max_conv", "maximize conversion value": "max_value",
              "maximize clicks": "clicks", "manual cpc": "manual", "target impression share": "tis"}
CHANGE_WORDS = {"budget": "Daily budget", "target_cpa": "Target CPA", "target_roas": "Target ROAS", "bid_strategy": "Bid strategy",
                "pause": "Pause", "hold": "Hold", "investigate": "Investigate"}
EDITOR_HEADER = ["Campaign", "Campaign daily budget", "Bid strategy type", "Target CPA", "Target ROAS", "Campaign status"]
DATES = re.compile(r"\d{4}-\d{2}-\d{2}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.? \d{1,2}, \d{4}")
NUMBER = re.compile(r"\d[\d,]*(?:\.\d+)?")
# Numbers a reason may quote without the review holding them: steps, cycles and small counts.
FREE_INTEGER = 10


def load(path, what):
    if not os.path.isfile(path):
        raise SystemExit("I can't find the %s file %s." % (what, path))
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except ValueError as error:
        raise SystemExit("The %s file is not valid JSON: %s." % (what, error))


def numbers_in(obj, found):
    if isinstance(obj, bool):
        return found
    if isinstance(obj, (int, float)):
        found.add(float(obj))
    elif isinstance(obj, dict):
        for value in obj.values():
            numbers_in(value, found)
    elif isinstance(obj, (list, tuple)):
        for value in obj:
            numbers_in(value, found)
    return found


def unknown_numbers(text, allowed):
    """Numbers in a reason that the review does not hold, as written or as a percent."""
    bad = []
    for token in NUMBER.findall(DATES.sub(" ", text or "")):
        plain = token.replace(",", "").rstrip(".")
        try:
            number = float(plain)
        except ValueError:
            continue
        places = len(plain.split(".")[1]) if "." in plain else 0
        if places == 0 and number <= FREE_INTEGER:
            continue
        half = 0.5 * 10 ** -places + 1e-9
        if not any(abs(round(v, places) - number) <= half or abs(round(v * 100, places) - number) <= half for v in allowed):
            bad.append(token)
    return bad


def roas_value(value):
    if isinstance(value, str) and value.strip().endswith("%"):
        number = metrics.div(float(value.strip().rstrip("%").replace(",", "")), 100)
        return number
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def number_value(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", ""))
        except ValueError:
            return None
    return None


def check(review, plan):
    errors, out = [], []
    by_name = {c["campaign"]: c for c in review["campaigns"]}
    allowed = numbers_in(review, set()) | {float(n) for n in (rules.NEEDED_DEFAULT, rules.NEEDED_TROAS, rules.TROAS_MIN_30D, rules.MONTHLY_LIMIT_FACTOR,
                                                              rules.PAUSE_MULTIPLE, 5, 10, 15, 2026)}
    steps = plan.get("steps") if isinstance(plan, dict) else None
    if not isinstance(steps, list) or not steps:
        return [{"check": "steps", "where": "plan", "text": "The plan has no steps. Write {\"steps\": [...]}, one item per change."}], []
    seen, state = set(), {}
    order = sorted(enumerate(steps, start=1), key=lambda pair: pair[1].get("step") if isinstance(pair[1], dict) and isinstance(pair[1].get("step"), int) else 0)
    for index, item in order:
        if not isinstance(item, dict):
            errors.append({"check": "steps", "where": "item %d" % index, "text": "Each step item must be an object with step, campaign, change and why."})
            continue
        step, name, kind, why = item.get("step"), item.get("campaign"), item.get("change"), (item.get("why") or "").strip()
        where = "step %s, %s" % (step, name)
        if not isinstance(step, int) or isinstance(step, bool) or step < 1:
            errors.append({"check": "steps", "where": "item %d" % index, "text": "\"step\" must be a whole number from 1."})
            continue
        if name not in by_name:
            close = difflib.get_close_matches(str(name), list(by_name), n=1)
            errors.append({"check": "unknown_campaign", "where": where, "text": "%s is not a campaign in the review.%s" % (
                name, " Did you mean %s?" % close[0] if close else " Use the name exactly as the report writes it.")})
            continue
        if kind not in CHANGES:
            errors.append({"check": "change", "where": where, "text": "\"change\" must be one of: %s." % ", ".join(CHANGES)})
            continue
        if not why:
            errors.append({"check": "why", "where": where, "text": "Every change needs a \"why\" a client can read."})
        bad = unknown_numbers(why, allowed | numbers_in(item, set()))
        if bad:
            errors.append({"check": "why_numbers", "where": where, "text": "The reason quotes %s, which the review does not hold. Quote the review's numbers or leave numbers out." % ", ".join(bad)})
        if (step, name) in seen:
            errors.append({"check": "one_change_per_step", "where": where, "text": "%s has two changes in step %d. Put the second in a later step, so each can be read on its own (%s)." % (name, step, rules.LP)})
        seen.add((step, name))
        c = by_name[name]
        change = {"step": step, "campaign": name, "change": kind, "why": why, "override": item.get("override") or "", "notes": [], "warnings": [],
                  "family": c["family"], "campaign_type": c["campaign_type"], "category": c["category"], "editor": None}
        st = state.setdefault(name, {"budget": c["budget"], "target_cpa": c["target_cpa"], "target_roas": c["target_roas"], "family": c["family"],
                                     "serving": c["serving"], "changed_in": None, "budget_added": 0.0})
        if kind in EDITS and not st["serving"]:
            errors.append({"check": "not_serving", "where": where, "text": "%s is %s. Plan changes only for serving campaigns." % (
                name, "paused by an earlier step" if c["serving"] else (c["campaign_status"] or "not serving"))})
            continue
        if kind in EDITS and c["category"].startswith("Hold") and not change["override"]:
            errors.append({"check": "held", "where": where, "text": "The review holds %s (%s): %s Leave it out, or add \"override\" with the reason." % (
                name, c["category"], " ".join(c["reasons"]))})
            continue
        problem = describe(change, item, c, review, st)
        if problem:
            errors.append({"check": problem[0], "where": where, "text": problem[1]})
            continue
        if kind == "budget":
            st["budget_added"] += change["added_per_day"] or 0
            st["budget"] = change["to"]
        elif kind == "target_cpa":
            st["target_cpa"], st["family"] = change["to"], "tcpa"
        elif kind == "target_roas":
            st["target_roas"], st["family"] = change["to"], "troas"
        elif kind == "bid_strategy":
            st["family"] = change["new_family"]
            st["target_cpa"] = change["target"] if change["new_family"] == "tcpa" else None
            st["target_roas"] = change["target"] if change["new_family"] == "troas" else None
        elif kind == "pause":
            st["serving"] = False
        if kind in EDITS:
            st["changed_in"] = step
        out.append(change)
    numbers = sorted({c["step"] for c in out} | {s.get("step") for s in steps if isinstance(s, dict) and isinstance(s.get("step"), int)})
    if numbers and numbers != list(range(1, numbers[-1] + 1)):
        errors.append({"check": "steps", "where": "plan", "text": "Steps must run 1, 2, 3 with no gap. The plan has %s." % ", ".join(str(n) for n in numbers)})
    return errors, out


def describe(change, item, c, review, st):
    """Fill in from, to, percent, notes, the check and the Editor row. Return (check, text) on a refusal.
    st holds the campaign as the plan leaves it after its earlier steps."""
    kind, fam = change["change"], st["family"]
    demand_gen = "demand gen" in c["campaign_type"].lower()
    gap_text = None
    if st["changed_in"]:
        change["notes"].append("Follows the change in step %d. Values start from that step." % st["changed_in"])
    elif c["reference"] is not None and c.get("gap") is not None:
        gap_text = "Actual %s against %s (%s)." % (actual(c), fmt(c, c["reference"]), rules.pct(c["gap"], signed=True))
    if kind == "budget":
        to = number_value(item.get("to"))
        if not to or to <= 0:
            return "value", "A budget change needs \"to\": the new daily budget, above zero."
        change.update({"from": st["budget"], "to": to, "pct": metrics.change(to, st["budget"]), "monthly_limit": to * rules.MONTHLY_LIMIT_FACTOR})
        added = to - st["budget"] if st["budget"] is not None else None
        ev = c.get("budget_evidence") or {}
        implied = ev.get("implied_extra_per_day")
        room = implied - st["budget_added"] if implied is not None else None
        change.update({"added_per_day": added, "implied_extra_per_day_left": room})
        text = ""
        if added is not None:
            text = "This step %s %s a day (%s). " % ("adds" if added >= 0 else "takes away", rules.money(abs(added)), rules.pct(change["pct"], signed=True))
        if room is not None:
            text += "The review's %s implies at most about %s a day more%s at the same cost per click, an upper bound. " % (
                ev["column"], rules.money(max(room, 0)), " after the earlier steps" if st["budget_added"] else "")
            if added is not None and added > room:
                change["warnings"].append("Adds more a day than the impression share lost to budget implies it could spend at today's cost per click.")
            elif added is not None and not st["budget_added"] and added > implied / 2 + 0.005:
                change["warnings"].append("Adds more than half the room in one step. Move budget in at least two steps, each read before the next, so a first step adds at most %s a day (**Practitioner rule**)." % rules.money(implied / 2))
        if room is not None and added is not None and added > 0:
            left_after = max(room - added, 0)
            change["room_left_after_step"] = left_after
            text += "After this step about %s a day of that room is left for a next step, once this step's check is read. " % rules.money(left_after)
        before_month = st["budget"] * rules.MONTHLY_LIMIT_FACTOR if st["budget"] else None
        if before_month is not None:
            change["monthly_limit_change"] = change["monthly_limit"] - before_month
        text += "Google may bill up to %s in a month at the new budget%s, 30.4 times the daily budget (**Official**, %s)." % (
            rules.money(change["monthly_limit"]),
            (", against %s now, %s %s" % (rules.money(before_month), rules.money(abs(change["monthly_limit_change"])),
                                          "more" if change["monthly_limit_change"] >= 0 else "less")) if before_month is not None else "", rules.SC)
        change["notes"].append(text)
        if added and added > 0 and c.get("goal_verdict") == "misses":
            change["warnings"].append("Its results are worse than your goal, which is your limit. Ask before adding volume.")
        change["notes"].append("The reference files set no limit on the size of a budget change: there is no universal rule that budget changes stay under 20%% (%s). The step is a judgment." % rules.SC)
        if fam in ("max_conv", "max_value"):
            change["notes"].append("**Official** (%s): %s is limited by budget by design. Size the new budget with the budget simulator, not Lost IS (budget)." % (rules.SB, rules.LABEL[fam]))
        if fam in ("tcpa", "troas") and change["pct"] and change["pct"] > 0:
            change["notes"].append("**Official** (%s): since August 17, 2026 a budget limited %s campaign bids toward its target, so the added budget buys conversions at about the target, not at today's figure. Confirm the target is the one the business wants." % (rules.SB, rules.LABEL[fam]))
        if c.get("shares_budget_with"):
            change["warnings"].append("The budget is shared with %s. This change moves all of them." % ", ".join(c["shares_budget_with"]))
        if change["pct"] and change["pct"] > 0 and c["category"] == "Missing its target":
            change["warnings"].append("Raises the budget of a campaign that misses its target.")
        if change["pct"] and change["pct"] < 0 and c["category"] == "Scale candidate":
            change["warnings"].append("Lowers the budget of a campaign the review found room to scale.")
        change["editor"] = {"Campaign daily budget": rules.money(to).replace(",", "")}
    elif kind in ("target_cpa", "target_roas"):
        want = ("tcpa", "max_conv") if kind == "target_cpa" else ("troas", "max_value")
        if fam not in want:
            return "target_type", "%s uses %s. A %s goes on %s campaigns. To switch strategy, use \"bid_strategy\"." % (
                change["campaign"], rules.LABEL[fam], CHANGE_WORDS[kind], " or ".join(rules.LABEL[w] for w in want))
        to = number_value(item.get("to")) if kind == "target_cpa" else roas_value(item.get("to"))
        if not to or to <= 0:
            return "value", "A %s change needs \"to\" above zero%s." % (CHANGE_WORDS[kind], "" if kind == "target_cpa" else ", as a ratio: 3.6 for 360%")
        if kind == "target_roas" and to > rules.ROAS_RATIO_MAX:
            return "value", "Write Target ROAS as a ratio: 3.6 for 360%."
        current = st["target_cpa"] if kind == "target_cpa" else st["target_roas"]
        pct = metrics.change(to, current)
        looser = None if current is None else (to > current if kind == "target_cpa" else to < current)
        change.update({"from": current, "to": to, "pct": pct, "looser": looser})
        if demand_gen and pct is not None and abs(pct) > rules.DEMAND_GEN_MAX + 1e-9:
            return "demand_gen_step", "%s is a Demand Gen campaign. Google's Demand Gen guide asks for bid changes of 5 to 10%% a week and no more than 15%% (%s). This step is %s. Split it into weekly steps." % (
                change["campaign"], rules.LP, rules.pct(abs(pct)))
        if demand_gen and pct is not None and abs(pct) > max(rules.DEMAND_GEN_STEPS) + 1e-9:
            change["warnings"].append("Above the 5 to 10% a week Google's Demand Gen guide asks for, within its 15% ceiling (%s)." % rules.LP)
        if not demand_gen:
            change["notes"].append("On Search and Shopping a target change moves bids at once and does not start learning, and a large move changes spend or volume by a similar amount (**Official**, %s). The reference files give no step size: this one is a judgment.%s" % (
                rules.SB, (" " + gap_text) if gap_text else ""))
        daily = metrics.div(c["read"]["cost"], c["read_days"]) if c.get("read_days") else None
        if daily and pct is not None and looser is not None and not st["changed_in"]:
            near = daily * (1 + abs(pct)) if looser else daily * (1 - abs(pct))
            change["spend_near_per_day"] = near
            change["notes"].append("So plan for spend near %s a day after this step, against %s a day in the review's read period%s." % (
                rules.money(near), rules.money(daily), ", if the budget allows it" if looser else ""))
        if current is None:
            change["notes"].append("Adds a target to a %s campaign." % rules.LABEL[fam])
            if kind == "target_roas" and c["conv_last30"] < rules.TROAS_MIN_30D:
                change["warnings"].append("%s conversions in the last 30 days, below the %d Google asks for before Target ROAS (**Official**, %s)." % (
                    "{:,.1f}".format(c["conv_last30"]), rules.TROAS_MIN_30D, rules.SB))
        if looser and c["budget_limited"] and fam in ("tcpa", "troas"):
            change["warnings"].append("Limited by budget, so it already bids toward its target (**Official**, %s). A looser target lets each conversion cost more without more budget to spend. **Practitioner rule.**" % rules.SB)
        if looser is False and c["category"] == "Missing its target":
            change["notes"].append("**Practitioner rule** (%s): when traffic quality is sound, fix the funnel, offer or landing page before tightening the target again and again." % (rules.TCPA if kind == "target_cpa" else rules.TROAS))
        if looser is False and c["category"] == "Scale candidate":
            change["warnings"].append("Tightens the target of a campaign the review found room to scale.")
        if looser and c["category"] == "Missing its target":
            change["warnings"].append("Loosens the target of a campaign that already misses it.")
        if looser is False and c["category"] == "Missing its target" and c.get("target_vs_goal") in ("stricter", "same"):
            change["warnings"].append("Its target is already at or stricter than your goal. %s it further is unlikely to help on its own: check search terms, conversion rate and the landing page first." % (
                "Lowering" if kind == "target_cpa" else "Raising"))
        goal = review.get("goal_cpa") if kind == "target_cpa" else review.get("goal_roas")
        if goal and ((kind == "target_cpa" and to > goal) or (kind == "target_roas" and to < goal)):
            change["warnings"].append("The new target is looser than your goal of %s, which is your limit. Ask before going past it." % fmt(c, goal))
        editor = {"Target CPA": rules.money(to).replace(",", "")} if kind == "target_cpa" else {"Target ROAS": "%.2f%%" % (to * 100)}
        if current is None:
            editor["Bid strategy type"] = CHANGE_WORDS[kind]
        change["editor"] = editor
    elif kind == "bid_strategy":
        name = str(item.get("to") or "").strip()
        new = STRATEGIES.get(name.lower())
        if not new:
            return "value", "\"to\" must be one of: %s." % ", ".join(n.title().replace("Cpa", "CPA").replace("Roas", "ROAS").replace("Cpc", "CPC") for n in STRATEGIES)
        if new == fam:
            return "same_strategy", "%s already uses %s." % (change["campaign"], rules.LABEL[fam])
        target = None
        if new in ("tcpa", "troas"):
            target = number_value(item.get("target")) if new == "tcpa" else roas_value(item.get("target"))
            if not target or target <= 0 or (new == "troas" and target > rules.ROAS_RATIO_MAX):
                return "value", "A switch to %s needs \"target\"%s." % (rules.LABEL[new], "" if new == "tcpa" else ", as a ratio: 3.6 for 360%")
        change.update({"from": rules.LABEL[fam], "to": rules.LABEL[new], "target": target, "new_family": new, "pct": None})
        change["notes"].append("A new bid strategy starts a learning period. Calibration typically takes 1 to 2 conversion cycles (**Official**, %s)." % rules.LP)
        if new == "troas" and c["conv_last30"] < rules.TROAS_MIN_30D:
            change["warnings"].append("%s conversions in the last 30 days, below the %d Google asks for before Target ROAS (**Official**, %s)." % (
                "{:,.1f}".format(c["conv_last30"]), rules.TROAS_MIN_30D, rules.SB))
        editor = {"Bid strategy type": rules.LABEL[new]}
        if new == "tcpa":
            editor["Target CPA"] = rules.money(target).replace(",", "")
        if new == "troas":
            editor["Target ROAS"] = "%.2f%%" % (target * 100)
        change["editor"] = editor
    elif kind == "pause":
        change.update({"from": "Enabled", "to": "Paused", "pct": None})
        if c["category"] != "Pause candidate":
            change["warnings"].append("The review does not list %s as a pause candidate. It is %s." % (change["campaign"], c["category"]))
        change["notes"] += [n for n in c["notes"] if n.startswith(("Which wins", "Confirm first"))]
        change["editor"] = {"Campaign status": "Paused"}
    else:
        change.update({"from": None, "to": None, "pct": None})
    if c.get("unexpected_move") and not st["changed_in"]:
        change["notes"].append(c["unexpected_move"]["text"])
    change["check"] = check_after(change, c, review, st)
    return None


def shown(c):
    early = c.get("early_read")
    if early and c["category"] not in ("Pause candidate", "Not serving"):
        return early, True
    return c["read"], False


def actual(c):
    data, early = shown(c)
    value = data["cpa"] if c["measure"] == "cpa" else data["roas"]
    return fmt(c, value) + (" (early)" if early and value is not None else "")


def fmt_measure(measure, value):
    return rules.money(value) if measure == "cpa" else rules.roas_text(value)


def fmt(c, value):
    return rules.money(value) if c["measure"] == "cpa" else rules.roas_text(value)


def check_after(change, c, review, st):
    """What to look at, when, and what result means rolling back. Every number from the review."""
    kind, fam = change["change"], change.get("new_family", st["family"])
    needed = rules.needed(fam)
    days = c["check"]["days"]
    if kind == "bid_strategy":
        parts = dict(c["check"]["parts"])
        if c["conv_per_day"]:
            parts["days_to_needed_conversions"] = int(math.ceil(needed / c["conv_per_day"]))
        days = max(parts.values()) if parts else None
    per_day = c["conv_per_day"]
    result = {"days": days, "needed": needed, "conversions_per_day_before": per_day, "rollback_above": None, "rollback_below": None}
    if kind == "pause":
        result.update({"days": 1, "what": "The next day: the campaign shows Paused and spent nothing. Then watch the other campaigns' conversions for a conversion cycle."})
        return result
    if kind == "investigate":
        result.update({"days": None, "what": "Fix what the investigation finds, then run the review again before changing the target or budget."})
        return result
    if kind == "hold":
        proper = (c.get("early_read") or {}).get("proper_read_on")
        if proper:
            result["what"] = "Run the review again around %s, when a proper read of its latest change is possible." % proper
        elif days:
            result["what"] = "Run the review again after about %d days, when enough data has come in since its latest change." % days
        else:
            result["what"] = "Run the review again once %d conversions have come in since its latest change." % needed
        return result
    measure = "roas" if fam in rules.VALUE_FAMILIES else "cpa"
    if kind in ("target_cpa", "target_roas"):
        ref = change["to"]
    elif kind == "bid_strategy":
        ref = change.get("target")
    elif fam == "tcpa":
        ref = st["target_cpa"]
    elif fam == "troas":
        ref = st["target_roas"]
    else:
        ref = c["reference"]
    if ref is None:
        ref = c["read"]["cpa"] if measure == "cpa" else c["read"]["roas"]
    width = rules.band(needed)
    goal = review.get("goal_cpa") if measure == "cpa" else review.get("goal_roas")
    capped = None
    if ref is not None and measure == "cpa":
        line = ref * (1 + width)
        if goal and line > goal:
            capped, line = line, goal
        result["rollback_above"] = line
    elif ref is not None:
        line = ref * (1 - width)
        if goal and line < goal:
            capped, line = line, goal
        result["rollback_below"] = line
    result["rollback_without_goal"] = capped
    metric = "Cost / conv." if measure == "cpa" else "Conv. value / cost"
    volume = " and conversions a day against %s in the review's read period" % "{:,.2f}".format(per_day) if per_day else ""
    when = "after about %d days, once %d conversions have come in" % (days, needed) if days else "once %d conversions have come in" % needed
    result["what"] = "%s against %s%s, %s." % (metric, fmt_measure(measure, ref), volume, when)
    own = " Your goal is the line: without it, the chance margin at %d conversions would put it at %s." % (needed, fmt_measure(measure, capped)) if capped is not None else ""
    if result["rollback_above"] is not None:
        result["rollback"] = "Roll back if %s is above %s%s at that point.%s" % (metric.lower(), rules.money(result["rollback_above"]), ", your goal," if capped is not None else "", own)
    elif result["rollback_below"] is not None:
        result["rollback"] = "Roll back if %s is below %s%s at that point.%s" % (metric.lower(), rules.roas_text(result["rollback_below"]), ", your goal," if capped is not None else "", own)
    return result


def fmt_measure(measure, value):
    if value is None:
        return "its level before the change"
    return rules.money(value) if measure == "cpa" else rules.roas_text(value)


def schedule(changes):
    """Each step starts once the previous step's checks are due. Holds and investigations do not hold up a step."""
    steps = {}
    for ch in changes:
        steps.setdefault(ch["step"], []).append(ch)
    start, plan = 0, []
    for number in sorted(steps):
        plan.append({"step": number, "starts_on_day": start, "changes": steps[number]})
        gating = [ch["check"]["days"] for ch in steps[number] if ch["change"] in EDITS]
        if start is not None:
            start = None if any(d is None for d in gating) else start + (max(gating) if gating else 0)
    return plan


def value_text(change, key):
    value = change.get(key)
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if change["change"] == "target_roas":
        return rules.roas_text(value)
    return rules.money(value)


def write(review, plan, out):
    r2 = rules.r2
    outputs.ensure_dir(out)
    editor_files = []
    for step in plan:
        rows = []
        for ch in step["changes"]:
            if ch["editor"]:
                rows.append([ch["campaign"]] + [ch["editor"].get(h, "") for h in EDITOR_HEADER[1:]])
        if rows:
            path = os.path.join(out, "step-%d-for-google-ads-editor.csv" % step["step"])
            outputs.write_csv(path, EDITOR_HEADER, rows)
            editor_files.append(os.path.basename(path))
            step["editor_file"] = os.path.basename(path)
    result = {"review": review["report"], "read_end": review["read_end"], "steps": plan, "editor_files": editor_files,
              "changes": sum(len(s["changes"]) for s in plan), "edits": sum(1 for s in plan for c in s["changes"] if c["change"] in EDITS)}
    outputs.write_json(os.path.join(out, "change-plan.json"), result)

    book = xlsx.Workbook()
    header = ["Step", "Starts on day", "Campaign", "Change", "From", "To", "Change, %", "Monthly limit after", "Why", "Check", "Check after, days",
              "Roll back if", "Notes"]
    rows = []
    for step in plan:
        for ch in step["changes"]:
            rows.append([step["step"], step["starts_on_day"], ch["campaign"], CHANGE_WORDS[ch["change"]], value_text(ch, "from"), value_text(ch, "to"),
                         ch.get("pct"), r2(ch.get("monthly_limit")), ch["why"], ch["check"]["what"], ch["check"]["days"], ch["check"].get("rollback", ""),
                         " ".join(ch["warnings"] + ch["notes"]).replace("**", "")])
    book.add_sheet("Plan", header, rows, formats={0: "int", 1: "int", 6: "pct", 7: "money", 8: "wrap", 9: "wrap", 10: "int", 11: "wrap", 12: "wrap"},
                   widths={2: 28, 8: 50, 9: 50, 11: 36, 12: 70})
    stand = [[c["campaign"], c["strategy_label"], r2(own_target(c)), r2(c.get("goal")), r2(shown(c)[0]["cpa"]), r2(shown(c)[0]["roas"]), r2(shown(c)[0]["conversions"]),
              "Early read" if shown(c)[1] else "Read period", c["limit_label"], c["category"]] for c in review["campaigns"]]
    book.add_sheet("Where things stand", ["Campaign", "Bid strategy", "Target", "Your goal", "Cost / conv.", "Conv. value / cost", "Conversions", "Figures from", "Limit", "Finding"],
                   stand, formats={2: "money", 3: "money", 4: "money", 5: "money", 6: "money"}, widths={0: 30, 8: 30, 9: 32})
    book.save(os.path.join(out, "change-plan.xlsx"))

    text = client_summary(review, plan, editor_files)
    with open(os.path.join(out, "change-plan.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    return text


def client_summary(review, plan, editor_files):
    has_goal = bool(review.get("goal_cpa") or review.get("goal_roas"))
    lines = ["# Bid strategy plan", "",
             "Based on the campaign report from %s to %s. Results are read through %s%s. Nothing has been changed in the account." % (
                 review["first_day"], review["last_day"], review["read_end"],
                 ", leaving out the most recent days while their conversions are still arriving" if review["cycle_days"] else ""), "",
             "## Where things stand", "",
             outputs.md_table(["Campaign", "Bid strategy", "Target"] + (["Your goal"] if has_goal else []) + ["Actual", "Limit", "Finding"],
                              [[c["campaign"], c["strategy_label"], target_text(c)] + ([fmt(c, c["goal"]) if c.get("goal") else "none"] if has_goal else [])
                               + [actual(c), c["limit_label"], c["category"]] for c in review["campaigns"]]), "",
             "Target is the campaign's own target.%s Actual is cost per conversion, or conv. value / cost for value bidding, over each campaign's read period. (early) marks the days since a recent change: shown, not yet judged.%s" % (
                 " Your goal is the limit you gave: the most per conversion, or the least conv. value / cost." if has_goal else "",
                 (" Impression share was read from %s%s." % (review["budget_column_read"], ", which counts only impressions lost among top ads" if "top" in review["budget_column_read"] else "")) if review["budget_column_read"] else ""), "",
             "## The plan", "",
             "Each step starts only when the checks of the step before are due. Change one thing per campaign per step, so each result can be read on its own.", ""]
    for step in plan:
        when = "now" if step["starts_on_day"] == 0 else ("about day %d, once step %d's checks are done" % (step["starts_on_day"], step["step"] - 1)
                                                         if step["starts_on_day"] is not None else "once step %d's checks are done" % (step["step"] - 1))
        lines += ["### Step %d: %s" % (step["step"], when), "",
                  outputs.md_table(["Campaign", "Change", "From", "To", "Change, %", "Why"],
                                   [[ch["campaign"], CHANGE_WORDS[ch["change"]], value_text(ch, "from") or "", value_text(ch, "to") or "",
                                     rules.pct(ch.get("pct"), signed=True) if ch.get("pct") is not None else "", ch["why"]] for ch in step["changes"]]), ""]
        for ch in step["changes"]:
            lines.append("**%s: %s.** Check: %s%s" % (ch["campaign"], CHANGE_WORDS[ch["change"]], ch["check"]["what"],
                                                      (" " + ch["check"]["rollback"]) if ch["check"].get("rollback") else ""))
            for note in ch["warnings"] + ch["notes"]:
                lines.append("- %s" % note)
            lines.append("")
        if step.get("editor_file"):
            lines += ["Google Ads Editor file for this step: %s. Import it with Account, Import, From file, review the proposed changes, then post. Blank cells change nothing." % step["editor_file"], ""]
    lines += ["## How the numbers were made", "",
              "- Cost per conversion is cost divided by conversions. Conv. value / cost is written as a ratio: 4.00 is 400%.",
              "- Better or worse than target counts only a gap wider than chance: about 1 / square root of the conversions behind the figure.",
              "- A check waits for the longest of: 2 conversion cycles, the days the campaign needs to bring in %d conversions (%d for Target ROAS) at its recent pace, and Google's own window for Performance Max or Demand Gen." % (rules.NEEDED_DEFAULT, rules.NEEDED_TROAS),
              "- The roll back line allows the same chance margin at that number of conversions: about %s at %d and %s at %d." % (
                  rules.pct(rules.band(rules.NEEDED_DEFAULT), 0), rules.NEEDED_DEFAULT, rules.pct(rules.band(rules.NEEDED_TROAS), 0), rules.NEEDED_TROAS),
              "- A month bills at most about 30.4 times the daily budget.", "",
              "## What this plan does not cover", "",
              "- Profit and margin. Conv. value / cost is not profit.",
              "- Conversion tracking, search terms and landing pages. Check them before tightening a target.",
              "- What Google's own simulators forecast. Look at the bid strategy report and the budget simulator before each step.",
              "- Campaigns that use a portfolio bid strategy take their target on the portfolio, not the campaign.", ""]
    return "\n".join(lines)


def own_target(c):
    return c["target_cpa"] if c["family"] == "tcpa" else c["target_roas"] if c["family"] == "troas" else None


def target_text(c):
    value = own_target(c)
    return "none" if value is None else fmt(c, value)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--review", required=True, help="bidding-review.json written by review.py")
    parser.add_argument("--plan", required=True, help="the plan, as JSON")
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    review = load(args.review, "review")
    if "campaigns" not in review:
        raise SystemExit("%s is not a review written by scripts/review.py. Run the review first." % args.review)
    plan = load(args.plan, "plan")
    errors, changes = check(review, plan)
    if errors:
        sys.stderr.write("I refused the plan. Nothing was written. Fix these and run it again:\n")
        for e in errors:
            sys.stderr.write("- [%s] %s: %s\n" % (e["check"], e["where"], e["text"]))
        raise SystemExit(1)
    text = write(review, schedule(changes), args.out)
    print(text)
    print("Wrote the plan to %s" % args.out)


if __name__ == "__main__":
    main()
