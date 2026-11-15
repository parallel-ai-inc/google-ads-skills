#!/usr/bin/env python3
"""Step 1 of the account audit: read the exports and run every check they allow.

Every report is optional. A check runs when its report and columns are there.
When they are not, the check is listed with the exact download that would let
it run. The script decides every number and every pass or fail. It writes
WORK/audit.json and WORK/notes.template.json and prints what to judge.

    python3 scripts/audit.py --work WORK --campaigns CAMPAIGNS.csv [--ad-groups FILE] [--keywords FILE]
        [--ads FILE] [--search-terms FILE] [--conversions FILE] [--networks FILE]
        [--job audit|readiness|qa] [--brand "acme, acme plumbing"] [--brand-campaign "Brand"]
        [--target-cpa 40] [--before OLD_WORK/audit.json]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import metrics, outputs  # noqa: E402
import loaders  # noqa: E402

JOBS = {"audit": "Full account audit", "readiness": "Acquisition readiness check", "qa": "QA checklist"}
AREAS = (("CT", "Conversion tracking and goals"), ("ST", "Structure"), ("KW", "Keywords and match types"),
         ("AD", "Ads and assets"), ("BB", "Budgets and bidding"), ("SQ", "Search terms and negatives"), ("SE", "Settings"))
AREA_ORDER = [code for code, _ in AREAS]
AREA_NAME = dict(AREAS)
# What a check's money is. Kinds are ranked apart and never added together.
KINDS = ("wasted", "exposed", "held back")
KIND_LABEL = {"wasted": "Wasted", "exposed": "Exposed", "held back": "Held back (estimate, upper bound)"}
KIND_MEANING = {"wasted": "spend with no result",
                "exposed": "spend that depends on a problem. It was not lost, but it rests on something that needs fixing",
                "held back": "an estimate of spend the budget kept out. It is an upper bound"}
# The order fixes are made in, whatever the money. See references/fix-order.md.
STAGES = ((1, "Measurement", ("CT-01", "CT-02", "CT-03", "CT-04")),
          (2, "Serving and policy", ("AD-01", "AD-02", "AD-03", "SE-01")),
          (3, "Waste", ("SQ-01", "SQ-02", "KW-05", "BB-04", "SE-02")),
          (4, "Structure, keywords and ads", ("ST-01", "ST-02", "KW-01", "KW-02", "KW-03", "AD-04")),
          (5, "Bidding", ("BB-01", "BB-02", "BB-05", "BB-06", "KW-04")),
          (6, "Budget", ("BB-03",)))
STAGE_OF = {cid: (number, name) for number, name, ids in STAGES for cid in ids}
SOURCES = "references/audit-check-sources.md"
ARG_UNLOCK = {
    "brand": ("The brand terms", '--brand "name, other name"'),
    "brand_campaign": ("The names of the brand campaigns", '--brand-campaign "Campaign name"'),
    "target_cpa": ("The target cost per conversion", "--target-cpa 40"),
}
MAX_ITEMS_PRINTED = 15
CHECKS = []

# Settings no report download shows. They are always listed, never guessed.
BY_HAND = [
    {"id": "SE-M1", "name": "Auto-applied recommendations", "label": "Official",
     "source": "references/reporting-and-diagnostics.md, Durable Diagnostic Surface Map",
     "page": "About applying recommendations automatically",
     "why": "Auto-applied recommendations are set per account and per type and apply daily. No report download shows which are on.",
     "unlock": "Check by hand in Google Ads: Recommendations, Auto-apply."},
    {"id": "SE-M2", "name": "AI Max and asset optimization settings in each Search campaign", "label": "Official",
     "source": "references/search-campaign-setup.md, AI Max And Legacy DSA Transition",
     "page": "About AI Max for Search campaigns",
     "why": "Search term matching, text customization and Final URL expansion are campaign settings. Campaigns migrated in "
            "September 2026 kept their own settings, so each campaign has to be read.",
     "unlock": "Check by hand in Google Ads: each Search campaign, Settings, AI Max."},
    {"id": "SE-M3", "name": "Conversion tag and enhanced conversions diagnostics", "label": "Official",
     "source": "references/reporting-and-diagnostics.md, Durable Diagnostic Surface Map",
     "page": "About the enhanced conversions for web tag diagnostics report",
     "why": "Whether tags fire, and what the diagnostics reports say, is not in any performance export.",
     "unlock": "Check by hand in Google Ads: Goals, Conversions, open each primary action and its diagnostics."},
    {"id": "SE-M4", "name": "Landing pages load and match the ad", "label": "Practitioner rule",
     "source": "references/checklists.md, Daily", "page": "",
     "why": "An export lists Final URLs but cannot open them.",
     "unlock": "Check by hand: open the Final URL of each ad group that spends, on a phone and a computer."},
]


def check(cid, name, label, source, needs=(), args=(), gate=False, must=False, page="", kind="exposed"):
    """Register a check. needs: (report key, [column or (alternative, columns)])."""
    def wrap(fn):
        CHECKS.append({"id": cid, "area": AREA_NAME[cid[:2]], "name": name, "label": label, "source": source,
                       "page": page, "needs": needs, "args": args, "gate": gate, "must": must, "kind": kind, "fn": fn})
        return fn
    return wrap


def item(campaign="", ad_group="", name="", detail="", cost=None, clicks=None, conversions=None, stake=None):
    return {"campaign": campaign, "ad_group": ad_group, "item": name, "detail": detail, "cost": cost, "clicks": clicks,
            "conversions": conversions, "cpa": metrics.div(cost, conversions), "stake": stake}


def done(status, looked_at, evidence, items=(), threshold="", left_out="", basis="", money=None, by_campaign=None, order=True):
    items = sorted(items, key=lambda i: -(i["stake"] or 0)) if order else list(items)
    if status == "fail" and money is None and any(i["stake"] is not None for i in items):
        money = sum(i["stake"] or 0 for i in items)
    if status == "fail" and by_campaign is None and money is not None:
        slots = {}
        for one in items:
            if one["stake"]:
                slots[one["campaign"] or "Account"] = slots.get(one["campaign"] or "Account", 0.0) + one["stake"]
        by_campaign = sorted(([k, v] for k, v in slots.items()), key=lambda s: -s[1])
    return {"status": status, "looked_at": looked_at, "evidence": list(evidence), "items": items, "threshold": threshold,
            "left_out": left_out, "money": money if status == "fail" else None, "money_basis": basis if status == "fail" else "",
            "by_campaign": by_campaign or [] if status == "fail" else []}


def not_run(why, unlock, flag=""):
    return {"status": "not run", "why": why, "unlock": unlock, "flag": flag}


def m(value):
    return metrics.money(value)


def n(value):
    return "{:,.2f}".format(value or 0)


def whole(value):
    return "{:,.0f}".format(value or 0)


def many(count, singular, plural=None):
    return "%d %s" % (count, singular if count == 1 else (plural or singular + "s"))


def left_text(every, judged, noun):
    """Say how many rows a count left out, and why, so the counts add up."""
    rest = [r for r in every if r not in judged]
    if not rest:
        return ""
    return ("%s left out because %s paused or removed, or under a paused, removed or ended campaign or ad group. "
            "Cost in the period: %s." % (many(len(rest), noun[:-1], noun) + (" was" if len(rest) == 1 else " were"),
                                         "it is" if len(rest) == 1 else "they are", m(metrics.total(rest, "cost"))))


def unmet(acct, opts, spec):
    for key, columns in spec["needs"]:
        report = loaders.REPORTS[key]
        if key not in acct.meta:
            return ("No %s was given." % report["title"], "The %s. In Google Ads: %s." % (report["title"], report["path"]))
        found = acct.meta[key]["columns"]
        missing = []
        for column in columns:
            options = column if isinstance(column, tuple) else (column,)
            if not any(o in found for o in options):
                missing.append(" or ".join(loaders.label(o) for o in options))
        if missing:
            return ("The %s has no %s column." % (report["title"], ", ".join(missing)),
                    "The %s with the column%s %s added. In Google Ads: %s, then the columns icon."
                    % (report["title"], "s" if len(missing) > 1 else "", " and ".join(missing), report["path"]))
    for arg in spec["args"]:
        if not getattr(opts, arg):
            plain, flag = ARG_UNLOCK[arg]
            return ("%s were not given." % plain if plain.endswith("s") else "%s was not given." % plain, "%s." % plain, flag)
    return None


# ---------------------------------------------------------------- conversion tracking and goals

def bidding_stake(acct, x):
    """Money at stake for a measurement fault: the spend that bids on these conversions."""
    if x["bidding_cost"] is None:
        return None, "not tied to a cost here. The campaign report with Bid strategy type would show the spend that bids on these conversions", []
    return (x["bidding_cost"], "the cost of the enabled campaigns that bid on conversions, because their bidding steers by these actions",
            [[c["campaign"], c["cost"]] for c in x["bidding"]])


@check("CT-01", "Conversions are recorded", "Practitioner rule", "references/checklists.md, Daily",
       needs=(("campaigns", ["conversions"]),), gate=True, must=True)
def ct01(a, o, x):
    live = x["live_campaigns"]
    cost, conv = metrics.total(live, "cost"), metrics.total(live, "conversions")
    evidence = ["Enabled campaigns: %d. Cost %s. Conversions %s." % (len(live), m(cost), n(conv))]
    if cost > 0 and conv == 0:
        items = [item(c["campaign"], name=c["campaign"], detail=c.get("bid_strategy") or "", cost=c["cost"], clicks=c["clicks"],
                      conversions=0, stake=c["cost"]) for c in live if c["cost"]]
        return done("fail", "Conversions in every enabled campaign of the campaign report.", evidence, items,
                    left_out=left_text(a.campaigns, live, "campaigns"), basis="the cost of the enabled campaigns, none of which recorded a conversion")
    return done("pass", "Conversions in every enabled campaign of the campaign report.", evidence, left_out=left_text(a.campaigns, live, "campaigns"))


def actions_in_use(a):
    acts = [r for r in a.actions if not r["removed"]]
    hidden = len(a.actions) - len(acts)
    return acts, ("%s left out because %s removed or hidden." % (many(hidden, "conversion action") + (" was" if hidden == 1 else " were"),
                                                                    "it is" if hidden == 1 else "they are") if hidden else "")


@check("CT-02", "Primary conversion actions are recording", "Official", SOURCES + ", Primary and secondary conversion actions",
       needs=(("conversions", [("action_optimization", "include_in_conversions")]),), gate=True, must=True,
       page="About primary and secondary conversion actions")
def ct02(a, o, x):
    acts, left = actions_in_use(a)
    primary = [r for r in acts if r["role"] == "primary"]
    silent = [r for r in primary if not r["recorded"]]
    evidence = ["Conversion actions in use: %d. Primary: %d. Primary that recorded nothing in the period: %d." % (len(acts), len(primary), len(silent))]
    looked = "The Action optimization setting and the count of each conversion action in the conversions summary."
    if primary and not silent:
        return done("pass", looked, evidence, left_out=left)
    money, basis, by_campaign = bidding_stake(a, x)
    items = [item(name=r["name"], detail="Primary. Recorded 0. Source: %s. Status: %s." % (r["source"] or "not shown", r["status"] or "not shown"),
                  conversions=0) for r in silent]
    if not primary:
        items = [item(name="No primary conversion action", detail="Bidding has no primary action to steer by.")]
    return done("fail", looked, evidence, items, left_out=left, basis=basis, money=money, by_campaign=by_campaign,
                threshold="A primary action fails when it recorded no conversion in the period of the file.")


def is_lead(action):
    return any(word in action["category"].lower() for word in loaders.LEAD_CATEGORIES) or "lead" in action["category"].lower()


@check("CT-03", "Lead actions count one conversion per click", "Official", SOURCES + ", Conversion counting: Every or One",
       needs=(("conversions", ["count_setting", "conv_category"]),), gate=True, must=True, page="About conversion counting options")
def ct03(a, o, x):
    acts, left = actions_in_use(a)
    roles_known = any(r["role"] != "unknown" for r in acts)
    pool = [r for r in acts if r["role"] == "primary"] if roles_known else acts
    leads = [r for r in pool if is_lead(r)]
    every = [r for r in leads if "every" in r["count_setting"].lower()]
    noun = "primary lead actions" if roles_known else "lead actions (the file does not say which are primary)"
    evidence = ["%s: %d. Counting Every: %d." % (noun[0].upper() + noun[1:], len(leads), len(every))]
    looked = "The Count setting of each lead action in the conversions summary."
    if not every:
        return done("pass", looked, evidence, left_out=left)
    money, basis, by_campaign = bidding_stake(a, x)
    items = [item(name=r["name"], detail="Category %s. Count: %s. Recorded %s." % (r["category"], r["count_setting"], n(r["recorded"])),
                  conversions=r["recorded"]) for r in every]
    return done("fail", looked, evidence, items, left_out=left, basis=basis, money=money, by_campaign=by_campaign,
                threshold="A lead action fails when its Count is Every. Lead categories read: %s." % ", ".join(loaders.LEAD_CATEGORIES))


@check("CT-04", "One primary action per kind of conversion", "Practitioner rule", SOURCES + ", Primary and secondary conversion actions",
       needs=(("conversions", ["conv_category", ("action_optimization", "include_in_conversions")]),), gate=True, must=True)
def ct04(a, o, x):
    acts, left = actions_in_use(a)
    groups = {}
    for r in acts:
        if r["role"] == "primary" and r["recorded"] and r["category"]:
            groups.setdefault(r["category"].lower(), []).append(r)
    doubled = {k: v for k, v in groups.items() if len(v) > 1}
    evidence = ["Categories with a recording primary action: %d. With two or more: %d." % (len(groups), len(doubled))]
    looked = "Primary actions that recorded conversions, grouped by Category, in the conversions summary."
    if not doubled:
        return done("pass", looked, evidence, left_out=left)
    money, basis, by_campaign = bidding_stake(a, x)
    items = [item(name=r["name"], detail="Category %s, %d primary actions in it. Source: %s." % (r["category"], len(v), r["source"] or "not shown"),
                  conversions=r["recorded"]) for v in doubled.values() for r in v]
    return done("fail", looked, evidence, items, left_out=left, basis=basis, money=money, by_campaign=by_campaign,
                threshold="A category fails when two or more primary actions in it recorded conversions. They may count the same event twice.")


# ---------------------------------------------------------------- structure

@check("ST-01", "No single keyword ad groups under Smart Bidding", "Official", "references/account-structure.md, What Google-Owned Sources Support",
       needs=(("keywords", []),), page="The ABCs of Account Structure")
def st01(a, o, x):
    bids_known = a.has("campaigns", "bid_strategy")
    groups, skipped = {}, set()
    for k in a.keywords:
        if not k["live"]:
            continue
        strategy = a.bid_strategy(k["campaign"])
        if bids_known and strategy is not None and not strategy["conversion"]:
            skipped.add(k["campaign"])
            continue
        groups.setdefault((k["campaign"], k["ad_group"]), []).append(k)
    singles = [(g, v[0]) for g, v in groups.items() if len(v) == 1]
    scope = "ad groups in campaigns that bid on conversions" if bids_known else "ad groups (no campaign report with Bid strategy type, so every campaign is included)"
    evidence = ["Live %s: %d. With exactly one enabled keyword: %d." % (scope, len(groups), len(singles))]
    left = ("Campaigns left out because they do not bid on conversions: %s." % ", ".join(sorted(skipped))) if skipped else ""
    looked = "Enabled keywords per live ad group in the keyword report."
    if not singles:
        return done("pass", looked, evidence, left_out=left)
    items = []
    for (campaign, group), k in singles:
        cost, clicks, conv = x["group_cost"](campaign, group)
        items.append(item(campaign, group, k["keyword"], "The only enabled keyword in the ad group.", cost, clicks, conv, cost))
    return done("fail", looked, evidence, items, left_out=left, basis="the cost of those ad groups in the period",
                threshold="An ad group fails when it has exactly one enabled keyword.")


@check("ST-02", "Brand and non brand keywords sit in separate campaigns", "Practitioner rule",
       "references/search-campaign-setup.md, Normal Setup Inputs (Guardrails)", needs=(("keywords", []),), args=("brand",))
def st02(a, o, x):
    camps = {}
    for k in a.keywords:
        if k["live"]:
            side = "brand" if loaders.is_brand(k["text"], a.brand_phrases) else "plain"
            slot = camps.setdefault(k["campaign"], {"brand": 0.0, "plain": 0.0, "brand_n": 0, "plain_n": 0})
            slot[side] += k["cost"]
            slot[side + "_n"] += 1
    mixed = {c: s for c, s in camps.items() if s["brand_n"] and s["plain_n"]}
    evidence = ["Campaigns with enabled keywords: %d. Holding both brand and non brand keywords: %d." % (len(camps), len(mixed))]
    looked = "Enabled keywords per campaign, sorted into brand and non brand by the brand terms given."
    if not mixed:
        return done("pass", looked, evidence)
    items = [item(c, name=c, detail="Brand keywords %d with cost %s. Non brand keywords %d with cost %s." % (s["brand_n"], m(s["brand"]), s["plain_n"], m(s["plain"])),
                  cost=s["brand"] + s["plain"], stake=min(s["brand"], s["plain"])) for c, s in mixed.items()]
    return done("fail", looked, evidence, items, basis="in each mixed campaign, the cost of the smaller side, which is the part that would move to its own campaign",
                threshold="A campaign fails when it holds enabled brand keywords and enabled non brand keywords.")


# ---------------------------------------------------------------- keywords and match types

@check("KW-01", "Keywords with a Below average Quality Score component", "Official", SOURCES + ", Quality Score",
       needs=(("keywords", [("exp_ctr", "ad_relevance", "landing_page_exp")]),), page="About Quality Score for Search campaigns")
def kw01(a, o, x):
    parts = [(f, loaders.label(f)) for f in ("exp_ctr", "ad_relevance", "landing_page_exp") if a.has("keywords", f)]
    live = [k for k in a.keywords if k["live"]]
    flagged, evidence = [], []
    for field, name in parts:
        below = [k for k in live if "below" in str(k.get(field) or "").lower()]
        evidence.append("%s Below average: %s, cost %s." % (name, many(len(below), "keyword"), m(metrics.total(below, "cost"))))
    for k in live:
        weak = [name for field, name in parts if "below" in str(k.get(field) or "").lower()]
        if weak:
            flagged.append(item(k["campaign"], k["ad_group"], k["keyword"], "Quality Score %s. Below average: %s" % ("%d" % k["quality_score"] if k.get("quality_score") else "--", ", ".join(weak)),
                                k["cost"], k["clicks"], k["conversions"], k["cost"]))
    evidence.insert(0, "Enabled keywords: %d. With at least one Below average component: %d. Quality Score is not averaged, as Google advises." % (len(live), len(flagged)))
    looked = "Exp. CTR, Ad relevance and Landing page exp. of each enabled keyword in the keyword report."
    if not flagged:
        return done("pass", looked, evidence, left_out=left_text(a.keywords, live, "keywords"))
    return done("fail", looked, evidence, flagged, left_out=left_text(a.keywords, live, "keywords"),
                basis="the cost of the keywords with a Below average component", threshold="A keyword fails when any component reads Below average.")


@check("KW-02", "No duplicate keywords", "Official", "references/account-structure.md, What Google-Owned Sources Support",
       needs=(("keywords", []),), page="The ABCs of Account Structure")
def kw02(a, o, x):
    groups = {}
    for k in a.keywords:
        if k["live"]:
            groups.setdefault((k["text"], k["match"]), []).append(k)
    dupes = {key: sorted(v, key=lambda k: -k["cost"]) for key, v in groups.items() if len(v) > 1}
    copies = sum(len(v) - 1 for v in dupes.values())
    evidence = ["Enabled keywords: %d. Keywords with the same text and match type in two or more ad groups: %d, making %s."
                % (sum(len(v) for v in groups.values()), len(dupes), many(copies, "extra copy", "extra copies"))]
    looked = "Enabled keywords with the same words and match type in more than one ad group."
    if not dupes:
        return done("pass", looked, evidence)
    items = []
    for (text, match), copies_of in dupes.items():
        for rank, k in enumerate(copies_of):
            items.append(item(k["campaign"], k["ad_group"], k["keyword"], "%s match, %d copies. %s" % (match.capitalize(), len(copies_of), "Costliest copy." if rank == 0 else "Extra copy."),
                              k["cost"], k["clicks"], k["conversions"], 0.0 if rank == 0 else k["cost"]))
    return done("fail", looked, evidence, items, order=False, basis="the cost of every copy except the costliest one",
                threshold="A keyword fails when its words and match type are enabled in more than one ad group.")


@check("KW-03", "Enabled keywords get impressions", "Official", "references/account-structure.md, What Google-Owned Sources Support",
       needs=(("keywords", ["impressions"]),), page="The ABCs of Account Structure")
def kw03(a, o, x):
    live = [k for k in a.keywords if k["live"]]
    idle = [k for k in live if not k["impressions"]]
    evidence = ["Enabled keywords: %d. With no impressions in the period: %d." % (len(live), len(idle))]
    looked = "Impr. of each enabled keyword in the keyword report."
    if not idle:
        return done("pass", looked, evidence, left_out=left_text(a.keywords, live, "keywords"))
    items = [item(k["campaign"], k["ad_group"], k["keyword"], "No impressions. Status: %s." % (k.get("status") or "not shown"), 0.0, 0.0, 0.0, 0.0) for k in idle]
    return done("fail", looked, evidence, items, left_out=left_text(a.keywords, live, "keywords"), money=0.0,
                basis="zero, because these keywords spent nothing. They are clutter that hides what serves",
                threshold="A keyword fails when it is enabled in a live ad group and had no impressions in the period.")


@check("KW-04", "Broad match keywords without conversion based bidding", "Practitioner rule",
       "references/account-structure.md, What Google-Owned Sources Support; references/search-campaign-setup.md, AI Max",
       needs=(("keywords", []), ("campaigns", ["bid_strategy"])))
def kw04(a, o, x):
    broad = [k for k in a.keywords if k["live"] and k["match"] == "broad"]
    active = [k for k in broad if k["cost"] or k.get("impressions")]
    idle = len(broad) - len(active)

    def manual(k):
        strategy = a.bid_strategy(k["campaign"])
        return strategy is not None and strategy["known"] and not strategy["conversion"]
    bad = [k for k in active if manual(k)]
    evidence = ["Enabled broad match keywords with impressions or cost: %d. In campaigns that do not bid on conversions: %d, with cost %s."
                % (len(active), len(bad), m(metrics.total(bad, "cost")))]
    left = ("%s with no impressions and no cost %s left out. KW-03 covers %s." % (many(idle, "broad match keyword"), "was" if idle == 1 else "were",
                                                                                   "it" if idle == 1 else "them")) if idle else ""
    looked = "Match type of each enabled keyword that served, against the Bid strategy type of its campaign."
    if not bad:
        return done("pass", looked, evidence, left_out=left)
    items = [item(k["campaign"], k["ad_group"], k["keyword"], "Broad match. Bid strategy: %s." % a.campaign_by_name[k["campaign"]].get("bid_strategy"),
                  k["cost"], k["clicks"], k["conversions"], k["cost"]) for k in bad]
    return done("fail", looked, evidence, items, left_out=left, basis="the cost of broad match keywords in campaigns that do not bid on conversions",
                threshold="A keyword fails when it is broad match, had impressions or cost, and its campaign's bid strategy does not bid on conversions.")


@check("KW-05", "Keywords that spent a conversion's cost converted", "Practitioner rule", "references/checklists.md, Weekly",
       needs=(("keywords", ["conversions"]),), gate=True, kind="wasted")
def kw05(a, o, x):
    live = [k for k in a.keywords if k["live"]]
    line = x["lines"]["keywords"]
    flagged = [k for k in live if not k["conversions"] and line["value"] > 0 and k["cost"] >= line["value"]]
    evidence = ["Enabled keywords: %d. With no conversions: %d, cost %s. Of those, spent %s or more: %d."
                % (len(live), len([k for k in live if not k["conversions"]]), m(metrics.total([k for k in live if not k["conversions"]], "cost")), m(line["value"]), len(flagged))]
    looked = "Cost and conversions of each enabled keyword in the keyword report."
    threshold = "A keyword fails when it has no conversions and spent %s or more. That is %s." % (m(line["value"]), line["source"])
    if not flagged:
        return done("pass", looked, evidence, threshold=threshold, left_out=left_text(a.keywords, live, "keywords"))
    items = [item(k["campaign"], k["ad_group"], k["keyword"], "%s match. No conversions." % k["match"].capitalize(), k["cost"], k["clicks"], 0.0, k["cost"]) for k in flagged]
    return done("fail", looked, evidence, items, threshold=threshold, left_out=left_text(a.keywords, live, "keywords"),
                basis="the cost of those keywords, with no conversions")


# ---------------------------------------------------------------- ads and assets

def live_search_groups(a, x):
    """Live ad groups that should carry ads, and how many were left out."""
    keys, skipped = {}, 0
    if a.ad_groups:
        for g in a.ad_groups:
            if g["live"]:
                keys[(g["campaign"], g["ad_group"])] = True
    for ad in a.ads:
        if ad["parent_live"]:
            keys[(ad["campaign"], ad["ad_group"])] = True
    for k in a.keywords:
        if k["live"]:
            keys[(k["campaign"], k["ad_group"])] = True
    out = []
    for key in keys:
        kind = x["kind"](key[0])
        if kind and kind != "search":
            skipped += 1
            continue
        out.append(key)
    return out, skipped


@check("AD-01", "Every live ad group has an active ad", "Practitioner rule", "references/compliance.md, What Google-Owned Sources Support",
       needs=(("ads", []),), gate=True, must=True)
def ad01(a, o, x):
    groups, skipped = live_search_groups(a, x)
    active = {}
    for ad in a.ads:
        if ad["active"]:
            active[(ad["campaign"], ad["ad_group"])] = active.get((ad["campaign"], ad["ad_group"]), 0) + 1
    empty = [g for g in groups if not active.get(g)]
    evidence = ["Live Search ad groups: %d. With no enabled, approved ad: %d." % (len(groups), len(empty))]
    left = "%d ad groups in campaigns that are not Search were left out." % skipped if skipped else ""
    looked = "Enabled ads that are not disapproved, per live ad group, from the ads report%s." % (" and the ad group report" if a.ad_groups else "")
    if not empty:
        return done("pass", looked, evidence, left_out=left)
    items = []
    for campaign, group in empty:
        ads = [ad for ad in a.ads if ad["campaign"] == campaign and ad["ad_group"] == group]
        states = ", ".join(sorted({("disapproved" if ad["disapproved"] else "paused or removed" if not ad["enabled"] else "enabled") for ad in ads})) or "no ads in the report"
        cost, clicks, conv = x["group_cost"](campaign, group)
        items.append(item(campaign, group, group, "Ads: %d (%s)." % (len(ads), states), cost, clicks, conv, cost))
    return done("fail", looked, evidence, items, left_out=left, basis="the cost of those ad groups in the period. They cannot show an ad now",
                threshold="An ad group fails when none of its ads is enabled and approved.")


def ads_needs():
    return (("ads", [("ad_status", "status", "approval_status", "policy_details")]),)


@check("AD-02", "No disapproved ads", "Official", "references/compliance.md, What Google-Owned Sources Support",
       needs=ads_needs(), gate=True, must=True, page="Disapproved: Definition")
def ad02(a, o, x):
    judged = [ad for ad in a.ads if ad["enabled"] and ad["parent_live"]]
    bad = [ad for ad in judged if ad["disapproved"]]
    evidence = ["Enabled ads in live ad groups: %d. Disapproved: %d." % (len(judged), len(bad))]
    looked = "The status and policy columns of each enabled ad in the ads report."
    left = left_text(a.ads, judged, "ads")
    if not bad:
        return done("pass", looked, evidence, left_out=left)
    items = [item(ad["campaign"], ad["ad_group"], ad["name"], "%s. %s" % (ad.get("status") or ad.get("approval_status") or "Disapproved", ad.get("policy_details") or ""),
                  ad["cost"], ad["clicks"], ad["conversions"], ad["cost"]) for ad in bad]
    return done("fail", looked, evidence, items, left_out=left, basis="the cost those ads carried in the period before they stopped",
                threshold="An ad fails when its status or policy column says Disapproved.")


@check("AD-03", "No ads limited by policy", "Official", "references/compliance.md, Review, Appeals And Enforcement",
       needs=ads_needs(), page="Eligible (limited): Definition")
def ad03(a, o, x):
    judged = [ad for ad in a.ads if ad["enabled"] and ad["parent_live"]]
    bad = [ad for ad in judged if ad["limited"]]
    evidence = ["Enabled ads in live ad groups: %d. Limited by policy: %d." % (len(judged), len(bad))]
    looked = "The status and policy columns of each enabled ad in the ads report."
    if not bad:
        return done("pass", looked, evidence)
    items = [item(ad["campaign"], ad["ad_group"], ad["name"], "%s. %s" % (ad.get("status") or ad.get("approval_status") or "", ad.get("policy_details") or ""),
                  ad["cost"], ad["clicks"], ad["conversions"], ad["cost"]) for ad in bad]
    return done("fail", looked, evidence, items, basis="the cost of those ads. They can show only in some places, to some ages or on some devices",
                threshold="An ad fails when its status reads limited, for example Eligible (limited).")


@check("AD-04", "Two responsive search ads rated Good or Excellent per ad group", "Official", SOURCES + ", Ad strength",
       needs=(("ads", ["ad_type", "ad_strength"]),), page="About Ad Strength for responsive search ads")
def ad04(a, o, x):
    groups = {}
    for ad in a.ads:
        if ad["active"] and ad["parent_live"] and ad["kind"] == "rsa":
            groups.setdefault((ad["campaign"], ad["ad_group"]), []).append(ad)
    short = {g: v for g, v in groups.items() if sum(1 for ad in v if ad["strength"] in ("good", "excellent")) < 2}
    evidence = ["Live ad groups with an active responsive search ad: %d. With fewer than two rated Good or Excellent: %d." % (len(groups), len(short))]
    looked = "Ad type and Ad strength of the active ads in each live ad group. Ad groups with no active ad are in AD-01."
    if not short:
        return done("pass", looked, evidence)
    items = []
    for (campaign, group), ads in short.items():
        cost, clicks, conv = x["group_cost"](campaign, group)
        ratings = ", ".join(sorted((ad["strength"] or "not rated").capitalize() for ad in ads))
        items.append(item(campaign, group, group, "Active responsive search ads: %d. Ad strength: %s." % (len(ads), ratings), cost, clicks, conv, cost))
    return done("fail", looked, evidence, items, basis="the cost of those ad groups in the period",
                threshold="An ad group fails when fewer than two of its active responsive search ads are rated Good or Excellent. Ad strength does not decide "
                          "whether an ad serves, so this is about the variety of the assets.")


# ---------------------------------------------------------------- budgets and bidding

@check("BB-01", "No Enhanced CPC left on Search or Display", "Official", "references/search-campaign-setup.md, Retired Search Settings",
       needs=(("campaigns", ["bid_strategy"]),), must=True, page="Feature deprecations and unversioned changes")
def bb01(a, o, x):
    live = x["live_campaigns"]
    bad = [c for c in live if c["strategy"]["ecpc"] and c["kind"] in ("search", "display", "")]
    evidence = ["Enabled campaigns: %d. Using Enhanced CPC: %d." % (len(live), len(bad))]
    looked = "Bid strategy type of each enabled campaign."
    if not bad:
        return done("pass", looked, evidence)
    items = [item(c["campaign"], name=c["campaign"], detail="Bid strategy: %s." % c.get("bid_strategy"), cost=c["cost"], clicks=c["clicks"],
                  conversions=c["conversions"], stake=c["cost"]) for c in bad]
    return done("fail", looked, evidence, items, basis="the cost of those campaigns",
                threshold="A Search or Display campaign fails when its bid strategy is Enhanced CPC, which Google retired for them on March 31, 2025.")


@check("BB-02", "A shared budget is not split across different bid strategies", "Official",
       "references/reporting-and-diagnostics.md, Durable Diagnostic Surface Map (bid strategy status)",
       needs=(("campaigns", ["budget_name", "bid_strategy"]),), gate=True, must=True, page="About bid strategy statuses")
def bb02(a, o, x):
    budgets = {}
    for c in x["live_campaigns"]:
        if c.get("budget_name"):
            budgets.setdefault(c["budget_name"], []).append(c)
    shared = {k: v for k, v in budgets.items() if len(v) > 1}
    bad = {k: v for k, v in shared.items()
           if any(c["strategy"]["maximize"] for c in v) and len({(c.get("bid_strategy") or "").lower() for c in v}) > 1}
    evidence = ["Budgets shared by two or more enabled campaigns: %d. Shared by a Maximize strategy and a different strategy: %d." % (len(shared), len(bad))]
    looked = "Budget name and Bid strategy type of each enabled campaign."
    if not bad:
        return done("pass", looked, evidence)
    items = [item(c["campaign"], name=c["campaign"], detail="Budget %s. Bid strategy: %s." % (name, c.get("bid_strategy")), cost=c["cost"],
                  clicks=c["clicks"], conversions=c["conversions"], stake=c["cost"]) for name, v in bad.items() for c in v]
    return done("fail", looked, evidence, items, basis="the cost of the campaigns on those budgets",
                threshold="A shared budget fails when one of its campaigns uses a Maximize strategy and another uses a different strategy. Google marks this Misconfigured.")


@check("BB-03", "Budget does not hold back campaigns that convert well", "Practitioner rule", SOURCES + ", Impression share lost to budget and to rank",
       needs=(("campaigns", ["lost_is_budget", "conversions", "bid_strategy"]),), gate=True, kind="held back")
def bb03(a, o, x):
    if getattr(a, "segmented_campaigns", False):
        return not_run("The campaign report is segmented, so impression share cannot be read.",
                       "The campaign report without a segment, with Search lost IS (budget). In Google Ads: Campaigns menu, Campaigns, Campaigns.")
    line = x["lines"]["campaigns"]
    reported = [c for c in x["live_campaigns"] if c.get("lost_is_budget") is not None]
    by_design = [c for c in reported if c["strategy"]["maximize"]]
    judged = [c for c in reported if not c["strategy"]["maximize"]]
    held = [c for c in judged if c["conversions"] and c["cost"] / c["conversions"] <= line["value"]]
    evidence = ["Enabled campaigns with a figure for Search lost IS (budget): %d. Left out because they use Maximize conversions or Maximize conversion value: %d. "
                "Judged: %d. Converting at or below %s: %d." % (len(reported), len(by_design), len(judged), m(line["value"]), len(held))]
    left = ("Left out by design: %s. Google says these strategies spend the full budget and Search lost IS (budget) does not apply to them."
            % ", ".join(c["campaign"] for c in by_design)) if by_design else ""
    design = [{"campaign": c["campaign"], "bid_strategy": c.get("bid_strategy"), "lost_is_budget": c["lost_is_budget"], "status": c.get("status") or ""}
              for c in by_design]
    threshold = ("A campaign is judged when the file gives a figure for Search lost IS (budget). The file writes '< 10%%' for small shares, and those are "
                 "read as no figure. It fails when its cost per conversion is at or below %s, which is %s." % (m(line["value"]), line["source"]))
    looked = "Search lost IS (budget), cost and conversions of each enabled campaign."
    if not held:
        return dict(done("pass", looked, evidence, threshold=threshold, left_out=left), by_design=design)
    items = []
    for c in held:
        share = c.get("impr_share")
        held_back = c["cost"] * c["lost_is_budget"] / share if share else c["cost"]
        items.append(item(c["campaign"], name=c["campaign"], detail="Search lost IS (budget) %.1f%%. Search impr. share %s. Budget %s. Bid strategy: %s."
                          % (c["lost_is_budget"], "%.1f%%" % share if share else "not given", m(c.get("budget")), c.get("bid_strategy")),
                          cost=c["cost"], clicks=c["clicks"], conversions=c["conversions"], stake=held_back))
    return dict(done("fail", looked, evidence, items, threshold=threshold, left_out=left,
                basis="an estimate of the spend the budget held back from campaigns that convert at or below the account's own cost per conversion: "
                      "cost times Search lost IS (budget), divided by Search impr. share. It assumes the missed impressions would cost what the "
                      "shown ones did. It is an upper bound, because the searches the ads missed usually convert worse than the ones they won. "
                      "Where Search impr. share is missing, the campaign's whole cost is used"), by_design=design)


@check("BB-04", "Campaigns that spent a conversion's cost converted", "Practitioner rule", "references/checklists.md, Daily",
       needs=(("campaigns", ["conversions"]),), gate=True, kind="wasted")
def bb04(a, o, x):
    line = x["lines"]["campaigns"]
    live = x["live_campaigns"]
    bad = [c for c in live if not c["conversions"] and line["value"] > 0 and c["cost"] >= line["value"]]
    evidence = ["Enabled campaigns: %d. With no conversions and cost of %s or more: %d." % (len(live), m(line["value"]), len(bad))]
    threshold = "A campaign fails when it has no conversions and spent %s or more. That is %s." % (m(line["value"]), line["source"])
    looked = "Cost and conversions of each enabled campaign."
    if not bad:
        return done("pass", looked, evidence, threshold=threshold, left_out=left_text(a.campaigns, live, "campaigns"))
    items = [item(c["campaign"], name=c["campaign"], detail="Bid strategy: %s." % (c.get("bid_strategy") or "not shown"), cost=c["cost"],
                  clicks=c["clicks"], conversions=0.0, stake=c["cost"]) for c in bad]
    return done("fail", looked, evidence, items, threshold=threshold, left_out=left_text(a.campaigns, live, "campaigns"),
                basis="the cost of those campaigns, with no conversions")


@check("BB-05", "Value based bidding has conversion value to bid on", "Practitioner rule", "references/checklists.md, Daily",
       needs=(("campaigns", ["bid_strategy", "conv_value"]),), gate=True, must=True)
def bb05(a, o, x):
    value = [c for c in x["live_campaigns"] if c["strategy"]["value"]]
    bad = [c for c in value if c["cost"] and not c["conv_value"]]
    evidence = ["Enabled campaigns bidding on conversion value: %d. With cost and no Conv. value: %d." % (len(value), len(bad))]
    looked = "Bid strategy type and Conv. value of each enabled campaign."
    if not bad:
        return done("pass", looked, evidence)
    items = [item(c["campaign"], name=c["campaign"], detail="Bid strategy: %s. Conv. value 0." % c.get("bid_strategy"), cost=c["cost"],
                  clicks=c["clicks"], conversions=c["conversions"], stake=c["cost"]) for c in bad]
    return done("fail", looked, evidence, items, basis="the cost of those campaigns",
                threshold="A campaign fails when it bids on conversion value, spent, and recorded no conversion value.")


@check("BB-06", "Campaigns stay within the target cost per conversion", "Practitioner rule", "references/checklists.md, Before Scaling",
       needs=(("campaigns", ["conversions"]),), args=("target_cpa",), gate=True)
def bb06(a, o, x):
    target = o.target_cpa
    live = x["live_campaigns"]
    over = []
    for c in live:
        if c["campaign"] in a.brand_campaigns or not c["cost"]:
            continue
        if c["conversions"] and c["cost"] / c["conversions"] > target:
            over.append(item(c["campaign"], name=c["campaign"], detail="Cost / conv. %s against a target of %s." % (m(c["cost"] / c["conversions"]), m(target)),
                             cost=c["cost"], clicks=c["clicks"], conversions=c["conversions"], stake=c["cost"] - c["conversions"] * target))
        elif not c["conversions"] and c["cost"] > target:
            over.append(item(c["campaign"], name=c["campaign"], detail="No conversions.", cost=c["cost"], clicks=c["clicks"], conversions=0.0, stake=c["cost"]))
    evidence = ["Enabled campaigns judged: %d. Above the target of %s: %d." % (len([c for c in live if c["campaign"] not in a.brand_campaigns and c["cost"]]), m(target), len(over))]
    looked = "Cost per conversion of each enabled campaign, against the target given. Brand campaigns named are left out."
    if not over:
        return done("pass", looked, evidence)
    return done("fail", looked, evidence, over, basis="the cost above the target: cost minus conversions times the target, or all the cost when there were no conversions",
                threshold="A campaign fails when its cost per conversion is above %s, the target you gave." % m(target))


# ---------------------------------------------------------------- search terms and negatives

def judged_terms(a):
    if a.has("campaigns", "campaign_status") or a.has("campaigns", "status"):
        return [t for t in a.terms if a.campaign_by_name.get(t["campaign"], {"live": True})["live"]]
    return list(a.terms)


@check("SQ-01", "Search terms that spent a conversion's cost converted", "Practitioner rule", "references/search-campaign-setup.md, Required Foundations",
       needs=(("search_terms", []),), gate=True, kind="wasted")
def sq01(a, o, x):
    pool = [t for t in judged_terms(a) if not t["excluded"]]
    line = x["lines"]["search_terms"]
    zero = [t for t in pool if not t["conversions"]]
    bad = [t for t in zero if not t["brand"] and line["value"] > 0 and t["cost"] >= line["value"]]
    listed = metrics.total(pool, "cost")
    evidence = ["Search terms judged: %d, cost %s. With no conversions: %d, cost %s, which is %s of the listed search term cost judged. "
                "Of those, non brand and spent %s or more: %d, cost %s."
                % (len(pool), m(listed), len(zero), m(metrics.total(zero, "cost")), metrics.pct(metrics.div(metrics.total(zero, "cost"), listed)),
                   m(line["value"]), len(bad), m(metrics.total(bad, "cost")))]
    left_rows = [t for t in a.terms if t not in pool]
    left = ("%s left out because they are already excluded or sit in paused or removed campaigns. Cost in the period: %s."
            % (many(len(left_rows), "search term") + (" was" if len(left_rows) == 1 else " were"), m(metrics.total(left_rows, "cost")))) if left_rows else ""
    threshold = "A search term fails when it is not brand, has no conversions, and spent %s or more. That is %s." % (m(line["value"]), line["source"])
    looked = "Cost and conversions of each search term in the search terms report."
    if not bad:
        return done("pass", looked, evidence, threshold=threshold, left_out=left)
    items = [item(t["campaign"], t["ad_group"], t["search_term"], "No conversions.", t["cost"], t["clicks"], 0.0, t["cost"]) for t in bad]
    for one, term in zip(items, bad):
        one["keyword"] = term.get("keyword") or ""
    return done("fail", looked, evidence, items, threshold=threshold, left_out=left, basis="the cost of those search terms, with no conversions")


@check("SQ-02", "Brand searches are served by the brand campaigns", "Practitioner rule", "references/search-campaign-setup.md, Normal Setup Inputs (Guardrails)",
       needs=(("search_terms", []),), args=("brand", "brand_campaign"))
def sq02(a, o, x):
    pool = [t for t in judged_terms(a) if not t["excluded"]]
    brand = [t for t in pool if t["brand"]]
    stray = [t for t in brand if t["campaign"] not in a.brand_campaigns]
    evidence = ["Brand search terms: %d, cost %s. Outside the brand campaigns: %d, cost %s, which is %s of the brand search term cost."
                % (len(brand), m(metrics.total(brand, "cost")), len(stray), m(metrics.total(stray, "cost")),
                   metrics.pct(metrics.div(metrics.total(stray, "cost"), metrics.total(brand, "cost"))))]
    looked = "Search terms that contain a brand term, and the campaign that served each."
    if not stray:
        return done("pass", looked, evidence)
    items = [item(t["campaign"], t["ad_group"], t["search_term"], "Brand search in a non brand campaign.", t["cost"], t["clicks"], t["conversions"], t["cost"]) for t in stray]
    return done("fail", looked, evidence, items, basis="the cost of brand searches served outside the brand campaigns",
                threshold="A search term fails when it contains a brand term and was served by a campaign not named as a brand campaign.")


# ---------------------------------------------------------------- settings

@check("SE-01", "Enabled campaigns are eligible to serve", "Official", "references/reporting-and-diagnostics.md, Durable Diagnostic Surface Map (bid strategy status)",
       needs=(("campaigns", ["status"]),), gate=True, must=True, page="About bid strategy statuses")
def se01(a, o, x):
    live = x["live_campaigns"]
    bad, learning, by_design = [], [], []
    for c in live:
        text = (c.get("status") or "").strip().lower()
        if text in ("", "eligible", "enabled") or "learning" in text:
            if "learning" in text:
                learning.append(c["campaign"])
            continue
        if "budget" in text and c["strategy"]["maximize"]:
            by_design.append(c["campaign"])
            continue
        bad.append(c)
    evidence = ["Enabled campaigns: %d. Not plainly eligible: %d. Learning: %d%s." % (len(live), len(bad), len(learning),
                                                                                       " (%s)" % ", ".join(learning) if learning else "")]
    left = ("Limited by budget by design, because they use a Maximize strategy: %s." % ", ".join(by_design)) if by_design else ""
    looked = "The Status column of each enabled campaign."
    if not bad:
        return done("pass", looked, evidence, left_out=left)
    items = [item(c["campaign"], name=c["campaign"], detail="Status: %s. %s" % (c.get("status"), c.get("status_reasons") or ""), cost=c["cost"],
                  clicks=c["clicks"], conversions=c["conversions"], stake=c["cost"]) for c in bad]
    return done("fail", looked, evidence, items, left_out=left, basis="the cost of those campaigns",
                threshold="An enabled campaign fails when its Status is not Eligible or Learning. Limited by budget on a Maximize strategy is left out.")


@check("SE-02", "Search partners and the Display Network earn their cost in Search campaigns", "Practitioner rule", SOURCES + ", Networks in a Search campaign",
       needs=(("networks", []),))
def se02(a, o, x):
    items, judged = [], 0
    for campaign, parts in sorted(a.networks.items()):
        info = a.campaign_by_name.get(campaign)
        if info is not None and (not info["live"] or info["kind"] not in ("search", "")):
            continue
        google = parts.get("search")
        google_cpa = metrics.div(google["cost"], google["conversions"]) if google else None
        for part, name in (("partners", "Search partners"), ("display", "Display Network")):
            slot = parts.get(part)
            if not slot or not slot["cost"]:
                continue
            judged += 1
            if not google_cpa:
                continue
            part_cpa = metrics.div(slot["cost"], slot["conversions"])
            if (part_cpa is None and slot["cost"] >= google_cpa) or (part_cpa is not None and part_cpa > google_cpa):
                items.append(item(campaign, name=name, detail="Cost / conv. %s here against %s on Google search in the same campaign." % (m(part_cpa) if part_cpa else "no conversions", m(google_cpa)),
                                  cost=slot["cost"], clicks=slot["clicks"], conversions=slot["conversions"], stake=slot["cost"]))
    evidence = ["Search partner or Display Network slices with cost, in enabled Search campaigns: %d. Costing more per conversion than Google search: %d." % (judged, len(items))]
    looked = "Cost and conversions by network in the campaign report segmented by Network (with search partners)."
    threshold = ("A slice fails when its cost per conversion is above the same campaign's on Google search, or when it has no conversions and spent at least "
                 "one Google search conversion's cost. Campaigns with no conversions on Google search are not judged.")
    if not items:
        return done("pass", looked, evidence, threshold=threshold)
    return done("fail", looked, evidence, items, threshold=threshold, basis="the cost on those networks")


# ---------------------------------------------------------------- run

def context(acct, opts):
    live = [c for c in acct.campaigns if c["live"]]
    bidding = [c for c in live if c["strategy"]["conversion"]] if acct.has("campaigns", "bid_strategy") else None
    group_index = {}
    if acct.ad_groups:
        for g in acct.ad_groups:
            group_index[(g["campaign"], g["ad_group"])] = (g["cost"], g["clicks"], g["conversions"])
    else:
        for rows in (acct.keywords, acct.ads):
            if rows:
                for r in rows:
                    slot = group_index.setdefault((r["campaign"], r["ad_group"]), [0.0, 0.0, 0.0])
                    slot[0] += r["cost"]
                    slot[1] += r["clicks"]
                    slot[2] += r["conversions"]
                break
    kinds = {c["campaign"]: c["kind"] for c in acct.campaigns}
    for g in acct.ad_groups:
        if g.get("campaign_type") and g["campaign"] not in kinds:
            kinds[g["campaign"]] = loaders.campaign_kind(g["campaign_type"])
    x = {
        "live_campaigns": live,
        "bidding": bidding or [],
        "bidding_cost": metrics.total(bidding, "cost") if bidding is not None else None,
        "group_cost": lambda c, g: tuple(group_index.get((c, g), (0.0, 0.0, 0.0))),
        "kind": lambda c: kinds.get(c, ""),
        "lines": {
            "campaigns": acct.line(live, "campaign report", "enabled campaigns"),
            "keywords": acct.line([k for k in acct.keywords if k["live"]], "keyword report", "enabled keywords"),
            "search_terms": acct.line([t for t in judged_terms(acct) if not t["excluded"]], "search terms report", "search terms"),
        },
    }
    return x


def clear_waste(results, account_cost):
    """Wasted spend at the search term and keyword level, each amount counted once."""
    by_id = {r["id"]: r for r in results}
    sq, kw = by_id["SQ-01"], by_id["KW-05"]
    if sq["status"] not in ("pass", "fail") and kw["status"] not in ("pass", "fail"):
        return None

    def clean(text):
        return loaders.keyword_parts(text, "")[0]
    keywords, terms = {}, {}
    for check_result, slots in ((kw, keywords), (sq, terms)):
        if check_result["status"] == "fail":
            for found in check_result["items"]:
                slots.setdefault((found["campaign"], found["ad_group"]), []).append(found)
    total, inside, by_campaign, guessed = 0.0, 0.0, {}, []
    for group in sorted(set(keywords) | set(terms)):
        kws, sts = keywords.get(group, []), terms.get(group, [])
        kw_cost, st_cost = metrics.total(kws, "cost"), metrics.total(sts, "cost")
        if kws and sts and all(t.get("keyword") for t in sts):
            flagged = {clean(k["item"]) for k in kws}
            under = metrics.total([t for t in sts if clean(t["keyword"]) in flagged], "cost")
            amount, inside = kw_cost + st_cost - under, inside + under
        elif kws and sts:
            amount = max(kw_cost, st_cost)
            inside += min(kw_cost, st_cost)
            guessed.append("%s > %s" % group)
        else:
            amount = kw_cost + st_cost
        total += amount
        by_campaign[group[0]] = by_campaign.get(group[0], 0.0) + amount
    includes = []
    if sq["status"] in ("pass", "fail"):
        includes.append("non brand search terms that spent at least the search term line (SQ-01)")
    if kw["status"] in ("pass", "fail"):
        includes.append("enabled keywords that spent at least the keyword line (KW-05)")
    notes = ["A search served by a flagged keyword is inside that keyword's cost, so it is counted once, as part of the keyword. %s was removed this way."
             % m(inside)]
    if guessed:
        notes.append("In %s (%s) the search terms report does not say which keyword served each search, so only the larger of the keyword and search "
                     "term amounts was counted there. The total can be low." % (many(len(guessed), "ad group"), "; ".join(guessed)))
    for check_result, name in ((sq, "search terms report"), (kw, "keyword report with Conversions")):
        if check_result["status"] not in ("pass", "fail"):
            notes.append("The %s was not given, so it is not in this total." % name)
    return {"total": total, "share_of_account_cost": metrics.div(total, account_cost), "overlap_removed": inside,
            "by_campaign": sorted(([k, v] for k, v in by_campaign.items()), key=lambda s: -s[1]),
            "includes": "Spend with no conversions on " + ", and on ".join(includes) + ".",
            "leaves_out": "Brand searches, searches and keywords below those lines, searches Google does not list, paused campaigns, and every exposed or "
                          "held back amount. Campaign level spend with no conversions (BB-04) is left out because it holds the same spend.",
            "notes": notes}


def assumptions(opts, brand_phrases, results):
    """What the run used or left out because something was not given, and which checks that changed."""
    by_id = {r["id"]: r for r in results}
    lined = [i for i in ("BB-03", "BB-04", "KW-05", "SQ-01") if by_id[i]["status"] in ("pass", "fail")]
    lined_text = ", ".join(lined) if lined else "no check that ran"
    out = []
    if opts.target_cpa:
        out.append("Target cost per conversion used: %s. It is the spent enough to judge line in %s, and BB-06 compares each campaign with it."
                   % (m(opts.target_cpa), lined_text))
    else:
        out.append("No target cost per conversion was given. BB-06 did not run, and %s used the account's own cost per conversion as the line instead."
                   % lined_text)
    terms = ", ".join(" ".join(p) for p in brand_phrases)
    camps = ", ".join(opts.brand_campaign)
    if terms and camps:
        out.append("Brand terms used: %s. Brand campaigns: %s. Brand rows were kept out of the lines in %s." % (terms, camps, lined_text))
    elif camps:
        out.append("Brand campaigns named: %s, with no brand terms. Those campaigns were kept out of the lines, but brand searches and keywords in other "
                   "campaigns were not recognised, so they stay inside the lines, and ST-02 and SQ-02 did not run." % camps)
    elif terms:
        out.append("Brand terms used: %s. No brand campaign was named, so the campaign line in BB-03 and BB-04 includes any brand campaign, and SQ-02 did "
                   "not run." % terms)
    else:
        out.append("No brand terms or brand campaigns were given. Brand rows stay inside the lines in %s, which pulls them down, and ST-02 and SQ-02 "
                   "did not run." % lined_text)
    return out


def validate_names(acct, names):
    known = set(acct.campaign_by_name)
    for rows in (acct.ad_groups, acct.keywords, acct.ads, acct.terms):
        known.update(r["campaign"] for r in rows)
    known.update(acct.networks)
    wrong = [name for name in names if name not in known]
    if wrong:
        raise SystemExit("These brand campaigns are not in the reports: %s. Campaign names found: %s. Copy the names exactly."
                         % (", ".join(wrong), ", ".join(sorted(known)) or "none"))


def compare(before_path, checks):
    if not before_path:
        return None
    if not os.path.isfile(before_path):
        raise SystemExit("I can't find the earlier audit %s. Pass the audit.json from the earlier run's work folder." % before_path)
    old = {c["id"]: c for c in outputs.read_json(before_path).get("checks", [])}
    rows = []
    for c in checks:
        prior = old.get(c["id"])
        if prior and (prior["status"] != c["status"] or (prior.get("money") or 0) != (c.get("money") or 0)):
            rows.append({"id": c["id"], "name": c["name"], "before": prior["status"], "now": c["status"],
                         "money_before": prior.get("money"), "money_now": c.get("money")})
    return {"file": before_path, "changes": rows}


# ---------------------------------------------------------------- naming and dated changes

NAME_SEPARATORS = ("|", " - ", " > ", " / ", ":", "_")
MAX_NAMES_PRINTED = 12


def name_shape(name):
    """The separator a name uses and how many parts it has, such as ("|", 2)."""
    for sep in NAME_SEPARATORS:
        if sep in name:
            return sep, len(name.split(sep))
    return "", 1


def shape_text(shape):
    sep, parts = shape
    return many(parts, "part") + (' split by "%s"' % sep.strip() if sep else ", no separator")


def naming(acct):
    """How campaign and ad group names are built, so a naming system is judged on counts, not by eye."""
    levels = []
    if acct.campaigns:
        camp = [(c["campaign"], c["live"]) for c in acct.campaigns]
        camp_source = "campaign report"
    else:
        seen = []
        for rows in (acct.ad_groups, acct.keywords, acct.ads, acct.terms):
            seen += [r["campaign"] for r in rows if r["campaign"] not in seen]
        camp = [(name, None) for name in seen]
        camp_source = "the other reports"
    groups, group_source = [], "ad group report"
    if acct.ad_groups:
        groups = [((g["campaign"], g["ad_group"]), g.get("live")) for g in acct.ad_groups]
    else:
        group_source = "keyword and ads reports"
        for rows in (acct.keywords, acct.ads):
            for r in rows:
                if (r["campaign"], r["ad_group"]) not in [k for k, _ in groups]:
                    groups.append(((r["campaign"], r["ad_group"]), None))
    for level, source, entries, show_name in (("Campaigns", camp_source, camp, lambda k: k),
                                              ("Ad groups", group_source, groups, lambda k: k[1])):
        if not entries:
            continue
        shapes = {}
        for key, live in entries:
            shapes.setdefault(name_shape(show_name(key)), []).append((key, live))
        ranked = sorted(shapes.items(), key=lambda s: (-len(s[1]), -s[0][1], s[0][0]))
        main_shape, main_rows = ranked[0]
        tie = len(ranked) > 1 and len(ranked[1][1]) == len(main_rows)
        off = [{"name": show_name(k), "campaign": k[0] if level == "Ad groups" else "", "pattern": shape_text(name_shape(show_name(k))),
                "serving": live} for k, live in entries if name_shape(show_name(k)) != main_shape]
        positions = []
        if main_shape[0]:
            for index in range(main_shape[1]):
                values = {}
                for key, _ in main_rows:
                    part = show_name(key).split(main_shape[0])[index].strip()
                    values[part] = values.get(part, 0) + 1
                positions.append(sorted(values.items(), key=lambda v: (-v[1], v[0].lower())))
        folded = {}
        for key, _ in entries:
            folded.setdefault(" ".join(show_name(key).lower().split()), set()).add(show_name(key))
        levels.append({"level": level, "source": source, "names": len(entries),
                       "patterns": [{"pattern": shape_text(s), "count": len(rows)} for s, rows in ranked],
                       "main_pattern": shape_text(main_shape), "main_count": len(main_rows), "tie": tie,
                       "off_pattern": off, "positions": positions,
                       "same_but_case_or_spaces": [sorted(v) for v in folded.values() if len(v) > 1]})
    return levels


def is_target(strategy):
    cell = " ".join((strategy or "").lower().split())
    return "target cpa" in cell or "target roas" in cell


def dated_changes(acct, x):
    """The dated platform changes an export can show, with the campaigns and ads each one touches."""
    out = {}
    if acct.campaigns and acct.has("campaigns", "bid_strategy"):
        target = [c for c in x["live_campaigns"] if is_target(c.get("bid_strategy"))]
        limited = [c for c in target if "budget" in (c.get("status") or "").lower() or (c.get("lost_is_budget") or 0) > 0]
        out["target_limited_by_budget"] = {
            "ran": True, "target_campaigns": [c["campaign"] for c in target],
            "limited": [{"campaign": c["campaign"], "bid_strategy": c.get("bid_strategy"), "status": c.get("status") or "",
                         "lost_is_budget": c.get("lost_is_budget"), "cpa": c.get("cpa")} for c in limited]}
    else:
        out["target_limited_by_budget"] = {"ran": False, "why": "The campaign report with Bid strategy type was not given."}
    if acct.ads and acct.has("ads", "ad_type"):
        dsa = [a for a in acct.ads if a["kind"] == "dsa"]
        out["dynamic_search_ads"] = {
            "ran": True, "serving": len([a for a in dsa if a["enabled"] and a["parent_live"]]),
            "ads": [{"campaign": a["campaign"], "ad_group": a["ad_group"], "serving": bool(a["enabled"] and a["parent_live"]), "cost": a["cost"]} for a in dsa]}
    else:
        out["dynamic_search_ads"] = {"ran": False, "why": "The ads report with Ad type was not given."}
    return out


def show_naming(levels):
    print("NAMING (names as the files spell them; judge them with playbooks/naming-and-labels.md)")
    for lv in levels:
        print("  %s: %d names, from the %s. Patterns: %s." % (lv["level"], lv["names"], lv["source"],
                                                             "; ".join("%s, %d" % (p["pattern"], p["count"]) for p in lv["patterns"])))
        print("    Most common pattern: %s, %d of %d.%s" % (lv["main_pattern"], lv["main_count"], lv["names"],
                                                            " Another pattern has as many names, so there is no single most common one." if lv["tie"] else ""))
        off = lv["off_pattern"]
        if off:
            listed = ["%s%s (%s%s)" % ("%s > " % o["campaign"] if o["campaign"] else "", o["name"], o["pattern"],
                                       ", not serving" if o["serving"] is False else "") for o in off[:MAX_NAMES_PRINTED]]
            print("    Off that pattern: %d. %s%s." % (len(off), "; ".join(listed), "; %d more in audit.json" % (len(off) - MAX_NAMES_PRINTED) if len(off) > MAX_NAMES_PRINTED else ""))
        else:
            print("    Off that pattern: 0.")
        for index, values in enumerate(lv["positions"], start=1):
            print("    Part %d holds %d different values: %s." % (index, len(values), "; ".join("%s (%d)" % v for v in values[:MAX_NAMES_PRINTED])))
        same = lv["same_but_case_or_spaces"]
        print("    Names that differ only in capitals or spaces: %s." % ("; ".join(" and ".join(s) for s in same) if same else "none"))
    print()


def show_dated(dated):
    print("DATED PLATFORM CHANGES THE FILES CAN SHOW (judge them with playbooks/what-changed-in-google-ads.md)")
    t = dated["target_limited_by_budget"]
    if t["ran"]:
        print("  August 17, 2026, budget limited Target CPA and Target ROAS campaigns bid toward their target: enabled campaigns whose Bid strategy type "
              "names Target CPA or Target ROAS: %d. Of those, limited by budget (Status says so, or Search lost IS (budget) above 0): %d."
              % (len(t["target_campaigns"]), len(t["limited"])))
        if t["limited"]:
            table(["Campaign", "Bid strategy type", "Status", "Search lost IS (budget)", "Cost / conv."],
                  [[c["campaign"], c["bid_strategy"] or "", c["status"], "%.1f%%" % c["lost_is_budget"] if c["lost_is_budget"] is not None else "",
                    m(c["cpa"])] for c in t["limited"]])
        print("  A Maximize conversions or Maximize conversion value campaign with a target set can show only its strategy name here. Read its target in Google Ads.")
    else:
        print("  August 17, 2026 rule: not checked. %s" % t["why"])
    d = dated["dynamic_search_ads"]
    if d["ran"]:
        print("  June 11, 2026, Dynamic Search Ads to be upgraded to AI Max: dynamic search ads in the ads report: %d, serving: %d.%s"
              % (len(d["ads"]), d["serving"], " Ad groups: %s." % "; ".join(sorted({"%s > %s" % (a["campaign"], a["ad_group"]) for a in d["ads"]})) if d["ads"] else ""))
    else:
        print("  Dynamic Search Ads: not checked. %s" % d["why"])
    print("  March 31, 2025, Enhanced CPC retired on Search and Display: BB-01. The September 2026 AI Max upgrades and the end of manual "
          "language targeting on Search are settings no export shows.")
    print()


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True, help="folder for work files")
    for key in loaders.ORDER:
        parser.add_argument(loaders.REPORTS[key]["flag"], dest=key, help="the %s" % loaders.REPORTS[key]["title"])
    parser.add_argument("--job", choices=sorted(JOBS), default="audit")
    parser.add_argument("--brand", default="", help="brand terms, comma separated")
    parser.add_argument("--brand-campaign", action="append", default=[], dest="brand_campaign", help="a brand campaign, exactly as named")
    parser.add_argument("--target-cpa", type=float, dest="target_cpa", help="the account's target cost per conversion")
    parser.add_argument("--before", help="audit.json from an earlier run, to compare against")
    opts = parser.parse_args()

    given = [key for key in loaders.ORDER if getattr(opts, key)]
    if not given:
        raise SystemExit("Give at least one export, for example --campaigns campaign-report.csv. The campaign report unlocks the most checks.")
    brand_phrases = [metrics.tokens(p) for p in opts.brand.split(",") if p.strip()]
    acct = loaders.Account(brand_phrases, opts.brand_campaign, opts.target_cpa)
    for key in given:
        acct.add(key, getattr(opts, key))
    validate_names(acct, opts.brand_campaign)
    acct.finish()
    x = context(acct, opts)

    results = []
    for spec in CHECKS:
        base = {k: spec[k] for k in ("id", "area", "name", "label", "source", "page", "gate", "must", "kind")}
        base["stage"], base["stage_name"] = STAGE_OF[spec["id"]]
        blocked = unmet(acct, opts, spec)
        outcome = not_run(*blocked) if blocked else spec["fn"](acct, opts, x)
        base.update(outcome)
        results.append(base)
    for spec in BY_HAND:
        results.append(dict(spec, area="Settings", gate=spec["id"] in ("SE-M3", "SE-M4"), must=spec["id"] in ("SE-M3", "SE-M4"),
                            status="by hand", kind="", stage=None, stage_name=""))

    account_cost = metrics.total(acct.campaigns, "cost") if acct.campaigns else None
    for r in results:
        # A held back estimate is not headlined as a share of the account's cost.
        r["share_of_account_cost"] = metrics.div(r.get("money"), account_cost) if r.get("money") is not None and r.get("kind") != "held back" else None
    failed = [r for r in results if r["status"] == "fail"]
    for kind in KINDS:
        ranked = sorted([r for r in failed if r["kind"] == kind], key=lambda r: (r["money"] is None, -(r["money"] or 0), AREA_ORDER.index(r["id"][:2])))
        for rank, r in enumerate(ranked, start=1):
            r["rank"] = rank
    failed.sort(key=lambda r: (KINDS.index(r["kind"]), r["rank"]))
    counts = {s: len([r for r in results if r["status"] == s]) for s in ("pass", "fail", "not run", "by hand")}

    periods = {}
    for key, entry in acct.reports.items():
        if entry["period"]:
            periods.setdefault(entry["period"]["text"], []).append(entry["report"])
    currencies = sorted({c.get("currency") for c in acct.campaigns if c.get("currency")})
    notes = list(acct.notes)
    if len(periods) > 1:
        notes.append("The files cover different date ranges: %s. Checks that join two files compare different periods."
                     % "; ".join("%s (%s)" % (k, ", ".join(v)) for k, v in periods.items()))
    if len(currencies) > 1:
        notes.append("The campaign report has more than one Currency code: %s. Amounts were added up as they are." % ", ".join(currencies))
    live = x["live_campaigns"]
    account = None
    if acct.campaigns:
        account = {"cost": account_cost, "clicks": metrics.total(acct.campaigns, "clicks"), "conversions": metrics.total(acct.campaigns, "conversions"),
                   "campaigns": len(acct.campaigns), "enabled_campaigns": len(live), "enabled_cost": metrics.total(live, "cost")}
    lines = {k: v for k, v in x["lines"].items() if k in acct.meta}

    audit = {
        "job": opts.job, "job_name": JOBS[opts.job],
        "files": [acct.reports[k] for k in given],
        "not_given": [{"report": loaders.REPORTS[k]["title"], "path": loaders.REPORTS[k]["path"]} for k in loaders.ORDER if k not in given],
        "periods": periods, "currency": currencies[0] if len(currencies) == 1 else "",
        "notes": notes, "account": account, "lines": lines,
        "brand": [" ".join(p) for p in brand_phrases], "brand_campaigns": opts.brand_campaign, "target_cpa": opts.target_cpa,
        "campaigns": [{k: c.get(k) for k in ("campaign", "campaign_status", "status", "campaign_type", "bid_strategy", "budget", "budget_name",
                                              "cost", "clicks", "conversions", "conv_value", "cpa", "lost_is_budget", "live")} for c in acct.campaigns],
        "counts": counts, "checks": results,
        "clear_waste": clear_waste(results, account_cost),
        "assumptions": assumptions(opts, brand_phrases, results),
        "fix_stages": [[number, name] for number, name, _ in STAGES],
    }
    audit["compare"] = compare(opts.before, results)
    audit["naming"] = naming(acct)
    audit["dated_changes"] = dated_changes(acct, x)
    outputs.ensure_dir(opts.work)
    outputs.write_json(os.path.join(opts.work, "audit.json"), audit)
    template = {
        "how_to_fill": "For every failed check below, set relevant to yes or no. For yes, write the fix: what to change, where, and in what order, in one "
                       "to three sentences, after opening the reference the check cites and the playbook. For no, write why it does not apply to this "
                       "account. Use only numbers the audit printed. The checks are listed in fix order. In summary, answer the job in one or two "
                       "sentences. Under assumptions, record anything you assumed, such as brand terms you suggested. Then run write_report.py.",
        "summary": "",
        "assumptions": [],
        "findings": [{"id": r["id"], "name": r["name"], "fix_stage": r["stage_name"], "money_kind": KIND_LABEL[r["kind"]],
                      "money": None if r["money"] is None else round(r["money"], 2), "source": r["source"],
                      "relevant": "", "fix": "", "why": ""} for r in sorted(failed, key=lambda r: (r["stage"], r["id"]))],
    }
    outputs.write_json(os.path.join(opts.work, "notes.template.json"), template)
    show(audit, failed, opts)


def table(header, rows):
    print(outputs.md_table(header, rows))
    print()


def show(audit, failed, opts):
    results = audit["checks"]
    print("%s" % audit["job_name"].upper())
    print()
    print("FILES READ")
    for f in audit["files"]:
        line = "  %s: %s. %s. %d rows." % (f["report"], f["file"], " / ".join(f["title_rows"]), f["rows"])
        if f["cost"] is not None:
            line += " Cost %s." % m(f["cost"])
        rec = f["reconcile"]
        if rec:
            line += (" Matches the file's own total (%s)." % rec["label"]) if rec["matches"] else \
                (" The file's own total (%s) is %s, a difference of %s." % (rec["label"], m(rec["file_total"]), m(rec["difference"])))
        elif f["cost"] is not None:
            line += " No total row to check against."
        print(line)
    for missing in audit["not_given"]:
        print("  Not given: %s (%s)." % (missing["report"], missing["path"]))
    if audit["currency"]:
        print("  Amounts are in %s, from the Currency code column." % audit["currency"])
    for note in audit["notes"]:
        print("  Note: " + note)
    print()
    print("WHAT THE RUN ASSUMED")
    for line in audit["assumptions"]:
        print("  " + line)
    print()
    if audit["account"]:
        acc = audit["account"]
        print("ACCOUNT: %d campaigns, %d enabled. Cost %s (enabled campaigns %s). Clicks %s. Conversions %s. Shares below are of the %s."
              % (acc["campaigns"], acc["enabled_campaigns"], m(acc["cost"]), m(acc["enabled_cost"]), whole(acc["clicks"]), n(acc["conversions"]),
                 "cost of every campaign in the campaign report"))
        table(["Campaign", "Campaign status", "Status", "Type", "Bid strategy type", "Budget", "Cost", "Conversions", "Cost / conv.", "Lost IS (budget)", "Judged"],
              [[c["campaign"], c["campaign_status"] or "", c["status"] or "", c["campaign_type"] or "", c["bid_strategy"] or "",
                m(c["budget"]) if c["budget"] is not None else "", m(c["cost"]), n(c["conversions"]), m(c["cpa"]),
                "%.1f%%" % c["lost_is_budget"] if c["lost_is_budget"] is not None else "", "Serving" if c["live"] else "Not serving, left out"]
               for c in audit["campaigns"]])
    print("THRESHOLDS")
    for key, line in audit["lines"].items():
        print("  Spent enough to judge, %s: %s. That is %s." % (key.replace("_", " "), m(line["value"]), line["source"]))
    if audit["brand"]:
        print("  Brand terms: %s. Brand campaigns: %s." % (", ".join(audit["brand"]), ", ".join(audit["brand_campaigns"]) or "none named"))
    else:
        print("  No brand terms were given.")
    print()
    counts = audit["counts"]
    ran = counts["pass"] + counts["fail"]
    print("RESULT: %d checks ran: %d passed, %d failed. %d could not run with these files. %d more are settings no export shows. No single score is given."
          % (ran, counts["pass"], counts["fail"], counts["not run"], counts["by hand"]))
    print()
    if opts.job == "readiness":
        print("READINESS CHECKS")
        table(["Id", "Check", "Result", "Money at stake"], [[r["id"], r["name"], r["status"], m(r.get("money")) if r.get("money") is not None else ""]
                                                            for r in results if r["gate"]])
    if opts.job == "qa":
        print("QA: MUST PASS")
        table(["Id", "Check", "Result"], [[r["id"], r["name"], r["status"]] for r in results if r["must"]])
        print("QA: OTHER CHECKS (do not block the change)")
        table(["Id", "Check", "Result"], [[r["id"], r["name"], r["status"]] for r in results if not r["must"] and r["status"] != "by hand"])
    print("Money is of three kinds, ranked apart and never added together. Wasted: %s. Exposed: %s. Held back: %s."
          % (KIND_MEANING["wasted"], KIND_MEANING["exposed"], KIND_MEANING["held back"]))
    print()
    for kind in KINDS:
        mine = [r for r in failed if r["kind"] == kind]
        if not mine:
            continue
        print("FAILED CHECKS, %s, BY MONEY" % KIND_LABEL[kind].upper())
        header = ["Rank", "Id", "Check", "Fix stage", "Money"] + (["Share of account cost"] if kind != "held back" else []) + ["Label"]
        table(header, [[r["rank"], r["id"], r["name"], r["stage_name"], m(r["money"]) if r["money"] is not None else "not tied to cost"]
                       + ([metrics.pct(r["share_of_account_cost"]) if r["share_of_account_cost"] is not None else ""] if kind != "held back" else [])
                       + [r["label"]] for r in mine])
    waste = audit["clear_waste"]
    if waste:
        print("CLEAR WASTE, COUNTED ONCE: %s%s" % (m(waste["total"]), ", %s of the account's cost" % metrics.pct(waste["share_of_account_cost"])
                                                   if waste["share_of_account_cost"] is not None else ""))
        print("  Includes: " + waste["includes"])
        print("  Leaves out: " + waste["leaves_out"])
        for note in waste["notes"]:
            print("  " + note)
        if waste["by_campaign"]:
            print("  By campaign: " + "; ".join("%s %s" % (name, m(value)) for name, value in waste["by_campaign"]))
        print()
    print("FIX ORDER (measurement, then serving, waste, structure, bidding, budget; see references/fix-order.md)")
    table(["Stage", "Id", "Check", "Money"], [[r["stage_name"], r["id"], r["name"], "%s %s" % (KIND_LABEL[r["kind"]], m(r["money"])) if r["money"] is not None else ""]
                                            for r in sorted(failed, key=lambda r: (r["stage"], r["id"]))])
    design = next((r.get("by_design") for r in results if r["id"] == "BB-03"), None)
    if design:
        print("LIMITED BY BUDGET BY DESIGN")
        for c in design:
            print("  %s uses %s, which is built to spend its full budget, so Search lost IS (budget) of %s does not mean it is starved. Judge its "
                  "headroom with the budget simulator in Google Ads (Official), and by whether its cost per conversion holds as the budget rises "
                  "(Practitioner rule)." % (c["campaign"], c["bid_strategy"], "%.1f%%" % c["lost_is_budget"]))
        print()
    for r in failed:
        print("### %s %s (%s, %s)" % (r["id"], r["name"], r["label"], r["source"]))
        print("Looked at: " + r["looked_at"])
        for line in r["evidence"]:
            print("Evidence: " + line)
        if r["threshold"]:
            print("Threshold: " + r["threshold"])
        if r["left_out"]:
            print("Left out: " + r["left_out"])
        print("Money, %s: %s, which is %s." % (KIND_LABEL[r["kind"]].lower(), m(r["money"]) if r["money"] is not None else "not tied to cost", r["money_basis"]))
        if len(r["by_campaign"]) > 1:
            print("By campaign: " + "; ".join("%s %s" % (name, m(value)) for name, value in r["by_campaign"]))
        rows = r["items"][:MAX_ITEMS_PRINTED]
        table(["Campaign", "Ad group", "Item", "Detail", "Cost", "Clicks", "Conversions", "At stake"],
              [[i["campaign"], i["ad_group"], i["item"], i["detail"], m(i["cost"]) if i["cost"] is not None else "",
                whole(i["clicks"]) if i["clicks"] is not None else "", n(i["conversions"]) if i["conversions"] is not None else "",
                m(i["stake"]) if i["stake"] is not None else ""] for i in rows])
        if len(r["items"]) > MAX_ITEMS_PRINTED:
            print("%d more in audit.json. The %d shown are the largest by money at stake.\n" % (len(r["items"]) - MAX_ITEMS_PRINTED, MAX_ITEMS_PRINTED))
    print("PASSED CHECKS")
    table(["Id", "Check", "Evidence", "Left out"], [[r["id"], r["name"], " ".join(r["evidence"]), r["left_out"]] for r in results if r["status"] == "pass"])
    print("CHECKS NOT RUN")
    table(["Id", "Check", "Why", "What would unlock it"], [[r["id"], r["name"], r["why"], r["unlock"] + (" Pass it with %s." % r["flag"] if r.get("flag") else "")]
                                                             for r in results if r["status"] in ("not run", "by hand")])
    if audit["naming"]:
        show_naming(audit["naming"])
    show_dated(audit["dated_changes"])
    if audit["compare"]:
        print("SINCE THE EARLIER RUN (%s)" % audit["compare"]["file"])
        table(["Id", "Check", "Before", "Now", "Money before", "Money now"],
              [[c["id"], c["name"], c["before"], c["now"], m(c["money_before"]) if c["money_before"] is not None else "",
                m(c["money_now"]) if c["money_now"] is not None else ""] for c in audit["compare"]["changes"]] or [["", "No check changed", "", "", "", ""]])
    print("Next: copy %s to %s, fill it in, then run python3 scripts/write_report.py --work %s --out OUTPUT"
          % (os.path.join(opts.work, "notes.template.json"), os.path.join(opts.work, "notes.json"), opts.work))


if __name__ == "__main__":
    main()
