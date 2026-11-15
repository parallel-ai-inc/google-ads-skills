#!/usr/bin/env python3
"""Step 2 of the campaign build: check the plan, and refuse a bad one.

Reads WORKDIR/plan.json. Counts every headline, description and path against
Google's limits, looks for duplicate headlines and duplicate keywords, tests
every negative keyword against the build's own keywords, and checks budgets,
names, dates and final URLs. A plan with a problem is refused with a plain
message for each one, and no file can be written from it.

    python3 scripts/check_plan.py --work WORKDIR [--today YYYY-MM-DD]
"""
import argparse
import datetime as dt
import hashlib
import os
import re
import sys
import unicodedata
from urllib.parse import urlsplit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_rules as rules  # noqa: E402
from gads import negatives, outputs  # noqa: E402

PLAN_FORMAT = "this skill's plan format"
OWN_NUMBERS = "the plan's own numbers"
STRATEGY_NAMES = ", ".join(s["name"] for s in rules.BID_STRATEGIES.values())
FIELD_HINTS = {
    "languages": "Language targeting is no longer set by hand on Search campaigns, so the file has no language column. (Official: %s)" % rules.SETUP,
    "language": "Language targeting is no longer set by hand on Search campaigns, so the file has no language column. (Official: %s)" % rules.SETUP,
    "status": "Everything is written paused. There is no status to set.",
    "pins": "This version writes no pins. Pin in Google Ads Editor after import.",
    "pinned": "This version writes no pins. Pin in Google Ads Editor after import.",
}
PHONE = re.compile(r"(?<!\d)(?:\+?\d[\s().\-]*){7,}")
REPEATED = re.compile(r"([^\w\s.])\1+")
CAPITAL_WORD = re.compile(r"[^\W\d_]{2,}")

# key, what the check proves, source, label. Refusing checks first, then warnings.
CHECKS = [
    ("plan_fields", "The plan uses only fields and values this version knows", PLAN_FORMAT, "Build rule"),
    ("names", "Campaign and ad group names are filled in and unique", rules.HAND, "Official"),
    ("account_names", "No new campaign uses a name the account already has", rules.HAND, "Official"),
    ("budget", "Every daily budget is a plain number above zero", rules.HAND, "Official"),
    ("bidding", "Every bid strategy is one the file can carry, with the bid or target it needs", rules.HAND, "Official"),
    ("networks", "Networks are Google Search, with or without Search Partners", rules.HAND, "Official"),
    ("ai_max", "Every campaign says whether AI Max is on or off, because Google turns it on unless the file says off", rules.HAND, "Official"),
    ("locations", "Every campaign has at least one location", rules.HAND, "Official"),
    ("dates", "Start and end dates are real dates and not in the past", rules.HAND, "Official"),
    ("structure", "Every ad group has keywords and 1 to %d responsive search ads" % rules.ADS_PER_AD_GROUP, rules.SPECS, "Official"),
    ("keyword_form", "Every keyword is plain words with a match type, within %d words and %d characters" % (rules.KEYWORD_WORDS, rules.KEYWORD_CHARS), rules.HAND, "Official"),
    ("duplicate_keywords", "No keyword and match type is in two ad groups", rules.STRUCTURE, "Official"),
    ("headline_count", "Every ad has %d to %d headlines" % (rules.HEADLINES_MIN, rules.HEADLINES_MAX), rules.HAND, "Official"),
    ("headline_chars", "Every headline is %d characters or fewer" % rules.HEADLINE_CHARS, rules.HAND, "Official"),
    ("description_count", "Every ad has %d to %d descriptions" % (rules.DESCRIPTIONS_MIN, rules.DESCRIPTIONS_MAX), rules.HAND, "Official"),
    ("description_chars", "Every description is %d characters or fewer" % rules.DESCRIPTION_CHARS, rules.HAND, "Official"),
    ("paths", "Every path is %d characters or fewer" % rules.PATH_CHARS, rules.HAND, "Official"),
    ("duplicate_text", "No ad repeats a headline or a description", rules.HAND, "Official"),
    ("customizers", "Every code in braces is one Google reads in a responsive search ad, with default text, inside the limits", rules.CUSTOMIZERS, "Official"),
    ("final_urls", "Every final URL is a well formed web address", rules.HAND, "Official"),
    ("negative_form", "Every negative keyword is plain words with a match type", PLAN_FORMAT, "Build rule"),
    ("negative_conflicts", "No negative keyword blocks one of the build's own keywords", rules.KEYWORDS, "Official"),
    ("account_limits", "The build is inside Google's account limits", rules.HAND, "Official"),
    ("editorial", "Ad text has no phone number, repeated punctuation, symbol or word in capitals", rules.HAND, "Official"),
    ("keyword_in_headline", "Every ad has a headline that carries one of its ad group's keywords", rules.HAND, "Official"),
    ("asset_depth", "Every ad has more than the minimum number of headlines and descriptions", rules.HAND, "Official"),
    ("ads_per_ad_group", "Every ad group has at least 2 responsive search ads", rules.HAND, "Official"),
    ("themed_ad_groups", "No ad group is built on a single keyword", rules.STRUCTURE, "Official"),
    ("split_keywords", "No keyword text is split across ad groups or campaigns", rules.STRUCTURE, "Official"),
    ("broad_bidding", "Broad match keywords sit in campaigns that bid on conversions", rules.KEYWORDS, "Official"),
    ("account_keywords", "No new keyword repeats one the account already has", rules.STRUCTURE, "Official"),
    ("budget_reach", "Every daily budget covers one click at the Max CPC, or one conversion at the target", OWN_NUMBERS, "Practitioner rule"),
    ("destinations", "Final URLs use https and point at one website", rules.LAUNCH, "Practitioner rule"),
    ("negative_cover", "Every campaign starts with negative keywords", rules.LAUNCH, "Practitioner rule"),
]


class Report:
    """Collects what each check tested and what it found."""

    def __init__(self):
        self.errors, self.warnings, self.notes = [], [], []
        self.blank = 0
        self.checks = {key: {"key": key, "check": title, "source": source, "label": label, "tested": 0,
                             "refused": 0, "warnings": 0, "not_run": ""} for key, title, source, label in CHECKS}

    def tested(self, key, count=1):
        self.checks[key]["tested"] += count

    def _add(self, target, counter, key, where, text):
        check = self.checks[key]
        check[counter] += 1
        target.append({"check": key, "where": where, "text": text, "label": check["label"], "source": check["source"]})

    def error(self, key, where, text):
        self._add(self.errors, "refused", key, where, text)

    def warn(self, key, where, text):
        self._add(self.warnings, "warnings", key, where, text)

    def not_run(self, key, reason):
        self.checks[key]["not_run"] = reason

    def results(self):
        rows = []
        for check in self.checks.values():
            if check["refused"]:
                result = "Refused: %d" % check["refused"]
            elif check["not_run"]:
                result = "Not run"
            elif check["warnings"]:
                result = "Warning: %d" % check["warnings"]
            else:
                result = "Passed"
            rows.append(dict(check, result=result))
        return rows


def clean(value):
    """Any JSON value as one line of trimmed text."""
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return re.sub(r"\s+", " ", str(value)).strip()


def number(value):
    """A JSON number, or None. Text such as "$90" is not read, so nothing is guessed."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def as_list(value, where, name, report):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    report.error("plan_fields", where, "%s must be a list in square brackets." % name)
    return []


def as_object(value, where, name, report):
    if isinstance(value, dict):
        return value
    if value is not None:
        report.error("plan_fields", where, "%s must be a set of fields in curly brackets." % name)
    return {}


def known(obj, kind, where, report):
    for key in obj:
        if key not in rules.ALLOWED[kind]:
            hint = FIELD_HINTS.get(str(key).lower()) or "Remove it, or check the spelling. The fields here are: %s." % ", ".join(rules.ALLOWED[kind])
            report.error("plan_fields", where, 'The field "%s" is not one this version uses. %s' % (key, hint))


def url_problem(url):
    """Why this is not a usable final URL, or None."""
    if any(ch.isspace() for ch in url):
        return "has a space in it. Google Ads Editor reads a space as the start of a second URL"
    try:
        parts = urlsplit(url)
        host = parts.hostname or ""
    except ValueError:
        return "is not a web address"
    if parts.scheme not in ("http", "https"):
        return "must start with https:// or http://"
    labels = host.split(".")
    if len(labels) < 2 or any(not label or label.startswith("-") or label.endswith("-") or not all(ch.isalnum() or ch == "-" for ch in label) for label in labels):
        return 'has no proper website name after "%s://"' % parts.scheme
    return None


def contains(haystack, needle):
    span = len(needle)
    return bool(span) and any(haystack[i:i + span] == needle for i in range(len(haystack) - span + 1))


def quoted(items, limit=6):
    shown = ['"%s"' % item for item in items[:limit]]
    return ", ".join(shown) + (" and %d more" % (len(items) - limit) if len(items) > limit else "")


def read_negatives(raw_list, where, level, campaign, ad_group, report):
    found, seen = [], set()
    for raw in as_list(raw_list, where, "negatives", report):
        if isinstance(raw, str):
            raw = {"text": raw}
        if not isinstance(raw, dict):
            report.error("plan_fields", where, "Each negative keyword must have the fields text, match and why.")
            continue
        known(raw, "negative", where, report)
        text = clean(raw.get("text"))
        if not text:
            report.blank += 1
            continue
        report.tested("negative_form")
        match = clean(raw.get("match")).lower().replace(" match", "")
        spot = '%s > Negative "%s"' % (where, text)
        if re.search(r'[\[\]"+]', text) or text.startswith("-"):
            report.error("negative_form", spot, "It is written with match type symbols. Write plain words and put exact, phrase or broad in match.")
            continue
        if match not in negatives.MATCH_TYPES:
            report.error("negative_form", spot, 'It has the match type "%s". Use exact, phrase or broad.' % match)
            continue
        key = (" ".join(rules.words(text)) or text.lower(), match)
        if key in seen:
            report.notes.append('%s is listed twice with the same match type. One copy was kept.' % spot)
            continue
        seen.add(key)
        found.append({"level": level, "campaign": campaign, "ad_group": ad_group, "text": text, "match": match,
                      "why": clean(raw.get("why")), "tested_against": 0, "blocks": []})
    return found


def read_text_list(raw_list, where, name, report):
    texts = []
    for raw in as_list(raw_list, where, name, report):
        text = clean(raw) if not isinstance(raw, (dict, list)) else ""
        if isinstance(raw, (dict, list)):
            report.error("plan_fields", where, "Each of the %s must be one line of text in quotation marks." % name)
        elif text:
            texts.append(text)
        else:
            report.blank += 1
    return texts


def check_ad_text(ad, where, report):
    """Count, length, repeats and editorial flags for one ad."""
    for kind, count_key, chars_key, low, high, limit in (
            ("headline", "headline_count", "headline_chars", rules.HEADLINES_MIN, rules.HEADLINES_MAX, rules.HEADLINE_CHARS),
            ("description", "description_count", "description_chars", rules.DESCRIPTIONS_MIN, rules.DESCRIPTIONS_MAX, rules.DESCRIPTION_CHARS)):
        items = ad[kind + "s"]
        report.tested(count_key)
        if len(items) < low:
            report.error(count_key, where, "It has %s. A responsive search ad needs at least %d." % (rules.plural(len(items), kind), low))
        elif len(items) > high:
            report.error(count_key, where, "It has %d %ss. A responsive search ad takes at most %d. Drop %d." % (len(items), kind, high, len(items) - high))
        positions = {}
        for index, item in enumerate(items, start=1):
            spot = "%s > %s %d" % (where, kind.capitalize(), index)
            report.tested(chars_key)
            if item["characters"] > limit:
                counted = ", counted with the default text in place of each code%s" % (" and %d characters for each countdown" % rules.COUNTDOWN_CHARS if any(c["kind"] == "countdown" for c in item["codes"]) else "") if item["codes"] else ""
                report.error(chars_key, spot, '"%s" is %d characters%s. The limit is %d. Shorten it by %d.' % (item["text"], item["characters"], counted, limit, item["characters"] - limit))
            check_codes(item, kind, spot, report)
            positions.setdefault(item["text"].casefold(), []).append(index)
        report.tested("duplicate_text")
        for same in positions.values():
            if len(same) > 1:
                report.error("duplicate_text", where, '%ss %s are the same text: "%s". Each one must be different.'
                             % (kind.capitalize(), " and ".join(str(i) for i in same), items[same[0] - 1]["text"]))

    report.tested("customizers")
    plain = [h for h in ad["headlines"] if not any(c["kind"] == "countdown" for c in h["codes"])]
    if len(plain) < len(ad["headlines"]) and len(plain) < rules.HEADLINES_WITHOUT_COUNTDOWN:
        report.error("customizers", where, "Only %s without a countdown. Google needs at least %d, because a countdown has no default text."
                     % (rules.plural(len(plain), "headline"), rules.HEADLINES_WITHOUT_COUNTDOWN))
    ends = sorted({c["end"] for part in ad["headlines"] + ad["descriptions"] for c in part["codes"] if c["kind"] == "countdown" and c["end"]})
    for end in ends:
        if end < str(report.today):
            report.error("customizers", where, "A countdown ends on %s, which has passed. Today is %s. An ad with a countdown stops showing after its end date." % (end, report.today))
    if ends:
        report.warn("customizers", where, "It counts down to %s. Google stops showing an ad with a countdown after its end date. Change the headline then, and confirm the date with the business."
                    % " and ".join(ends))

    report.tested("paths")
    for name in ("path_1", "path_2"):
        for code in rules.codes(ad[name]):
            label = name.replace("_", " ").capitalize()
            if code["problem"]:
                report.error("customizers", where, '%s: the code %s %s.' % (label, code["code"], code["problem"]))
            elif code["kind"] == "countdown":
                report.error("customizers", where, "%s holds a countdown. Google does not allow a countdown in the display path." % label)
            else:
                report.warn("customizers", where, "%s holds the code %s. Google's Help allows it in the display path, and its API guide says codes go only in headlines and descriptions. Read the ad in Google Ads Editor." % (label, code["code"]))
        size = rules.text_len(ad[name])
        if size > rules.PATH_CHARS:
            report.error("paths", where, '%s "%s" is %d characters. The limit is %d. Shorten it by %d.' % (name.replace("_", " ").capitalize(), ad[name], size, rules.PATH_CHARS, size - rules.PATH_CHARS))
        if " " in ad[name] or "/" in ad[name]:
            report.warn("destinations", where, '%s "%s" has a space or a slash in it. A path shows as one part of the web address under the headline. Check it in Google Ads Editor.' % (name.replace("_", " ").capitalize(), ad[name]))
    if ad["path_2"] and not ad["path_1"]:
        report.error("paths", where, "Path 2 is filled in and Path 1 is empty. Fill in Path 1 first.")

    report.tested("final_urls")
    if "{" in ad["final_url"] or "}" in ad["final_url"]:
        report.error("customizers", where, 'The final URL "%s" holds a code in braces. No code can go in the Final URL.' % ad["final_url"])
    if not ad["final_url"]:
        report.error("final_urls", where, "It has no final URL. Every ad needs the address of the page it sends people to.")
    else:
        problem = url_problem(ad["final_url"])
        if problem:
            report.error("final_urls", where, 'The final URL "%s" %s.' % (ad["final_url"], problem))

    report.tested("editorial")
    capitals = []
    for kind in ("headline", "description"):
        for index, item in enumerate(ad[kind + "s"], start=1):
            spot = "%s > %s %d" % (where, kind.capitalize(), index)
            text = rules.shown_text(item["text"])
            phone = next((m.group(0).strip() for m in PHONE.finditer(text) if sum(ch.isdigit() for ch in m.group(0)) >= 7), None)
            if phone:
                report.warn("editorial", spot, '"%s" has what looks like a phone number, %s. Google\'s editorial policy does not allow a phone number in ad text. Use a call asset for the number.' % (text, phone))
            repeat = REPEATED.search(text)
            if repeat:
                report.warn("editorial", spot, '"%s" repeats a punctuation mark or symbol: %s. Google\'s editorial policy does not allow that.' % (text, repeat.group(0)))
            symbols = sorted({ch for ch in text if ord(ch) >= 0x1F000 or (ord(ch) >= 0x2190 and unicodedata.category(ch) == "So")})
            if symbols:
                report.warn("editorial", spot, '"%s" has a symbol Google may not accept in ad text, such as an emoji, a star or an arrow: %s' % (text, " ".join(symbols)))
            capitals += ["%s (%s %d)" % (word, kind, index) for word in CAPITAL_WORD.findall(text) if word.isupper()]
    if capitals:
        report.warn("editorial", where, "Words in capital letters: %s. Google's editorial policy does not allow capitals used for effect. Common abbreviations may be allowed. Keep the abbreviations and reword the rest."
                    % ", ".join(capitals))

    report.tested("asset_depth")
    thin = [text for text, short in (("%d headlines" % len(ad["headlines"]), len(ad["headlines"]) == rules.HEADLINES_MIN),
                                     ("%d descriptions" % len(ad["descriptions"]), len(ad["descriptions"]) == rules.DESCRIPTIONS_MIN)) if short]
    if thin:
        report.warn("asset_depth", where, "It has %s, the fewest Google accepts. Google's tip is to give as many different headlines as you can, up to %d, and up to %d descriptions."
                    % (" and ".join(thin), rules.HEADLINES_MAX, rules.DESCRIPTIONS_MAX))


def check_codes(item, kind, spot, report):
    """Every code in braces in one headline or description: Google reads it, and location codes stay within their number."""
    report.tested("customizers")
    for code in item["codes"]:
        if code["problem"]:
            report.error("customizers", spot, '"%s": the code %s %s.' % (item["text"], code["code"], code["problem"]))
    most = rules.LOCATION_PER_HEADLINE if kind == "headline" else rules.LOCATION_PER_DESCRIPTION
    places = sum(1 for code in item["codes"] if code["kind"] == "location")
    if places > most:
        report.error("customizers", spot, '"%s" has %d location codes. Google takes %d in a %s.' % (item["text"], places, most, kind))


def attribute_checks(ads, report):
    """Customizer attributes the ads use: within Google's limit, and named so the person creates them before posting."""
    names = {}
    for ad in ads:
        for part in ad["headlines"] + ad["descriptions"]:
            for code in part["codes"]:
                if code["kind"] == "customizer" and not code["problem"]:
                    names.setdefault(code["attribute"].casefold(), code["attribute"])
    if len(names) > rules.CUSTOMIZER_ATTRIBUTES:
        report.error("customizers", "Plan", "The ads use %d customizer attributes. An account can have %d enabled. Reuse broader attributes."
                     % (len(names), rules.CUSTOMIZER_ATTRIBUTES))
    for name in sorted(names.values(), key=str.lower):
        report.warn("customizers", "Plan", 'The ads use the customizer attribute "%s". The import file does not create it. Before posting, create it in Google Ads '
                    '(Tools, Business data, Ad customizer attributes) and give it a value at the account level or below, or ads that use it cannot be reviewed. '
                    'Count it against the account\'s limit of %d attributes.' % (name, rules.CUSTOMIZER_ATTRIBUTES))


def read_plan(plan, report):
    """Turn the plan into flat lists, checking each item on the way in."""
    known(plan, "plan", "Plan", report)
    brief_raw = as_object(plan.get("brief"), "Plan", "brief", report)
    known(brief_raw, "brief", "brief", report)
    owners_raw = as_object(brief_raw.get("owners"), "brief", "owners", report)
    known(owners_raw, "owners", "brief.owners", report)
    ready_raw = as_object(brief_raw.get("ready"), "brief", "ready", report)
    known(ready_raw, "ready", "brief.ready", report)
    ready = {}
    for key, _, _, _ in rules.READY_ITEMS:
        answer = clean(ready_raw.get(key)).lower() or "unknown"
        if answer not in rules.READY_ANSWERS:
            report.error("plan_fields", "brief.ready", '%s is "%s". Write yes, no or unknown.' % (key, answer))
            answer = "unknown"
        ready[key] = answer
    brief = {key: clean(brief_raw.get(key)) for key in ("business", "offer", "goal", "primary_conversion", "hypothesis", "success_metric", "early_warning")}
    brief["assumptions"] = read_text_list(brief_raw.get("assumptions"), "brief", "assumptions", report)
    brief["owners"] = {key: clean(owners_raw.get(key)) for key, _, _ in rules.OWNER_ROLES}
    brief["ready"] = ready

    list_raw = as_object(plan.get("negative_keyword_list"), "Plan", "negative_keyword_list", report)
    known(list_raw, "negative_keyword_list", "negative_keyword_list", report)
    list_name = clean(list_raw.get("name"))
    all_negatives = read_negatives(list_raw.get("keywords"), "Negative keyword list", "account", "", "", report)

    campaigns, ad_groups, keywords, ads = [], [], [], []
    campaign_names = set()
    raw_campaigns = [c for c in as_list(plan.get("campaigns"), "Plan", "campaigns", report)]
    if not raw_campaigns:
        report.error("structure", "Plan", "It has no campaign. Add at least one under campaigns.")
    for c_index, raw in enumerate(raw_campaigns, start=1):
        if not isinstance(raw, dict):
            report.error("plan_fields", "Campaign %d" % c_index, "A campaign must be a set of fields in curly brackets.")
            continue
        name = clean(raw.get("name"))
        where = 'Campaign "%s"' % name if name else "Campaign %d" % c_index
        known(raw, "campaign", where, report)

        report.tested("names")
        if not name:
            report.error("names", where, "It has no name.")
        elif name.lower() in campaign_names:
            report.error("names", where, "Two campaigns in the plan use this name. Google Ads Editor matches rows by name, so the two would merge. Rename one.")
        campaign_names.add(name.lower())

        report.tested("budget")
        budget = number(raw.get("daily_budget"))
        if budget is None:
            report.error("budget", where, "The daily budget must be a plain number, such as 90 or 90.50, with no currency symbol and no quotation marks.")
        elif budget <= 0:
            report.error("budget", where, "The daily budget is %s. It must be above zero." % rules.shown(budget))
        elif abs(budget * 100 - round(budget * 100)) > 1e-6:
            report.error("budget", where, "The daily budget %s has more than two decimals." % raw.get("daily_budget"))

        report.tested("bidding")
        strategy_text = clean(raw.get("bid_strategy"))
        strategy = rules.BID_STRATEGIES.get(strategy_text.lower())
        if not strategy_text:
            report.error("bidding", where, "It has no bid strategy. Use one of: %s." % STRATEGY_NAMES)
        elif "enhanced" in strategy_text.lower() or strategy_text.lower() == "ecpc":
            report.error("bidding", where, "Enhanced CPC is no longer available for Search campaigns (Official: %s). Use one of: %s." % (rules.SETUP, STRATEGY_NAMES))
        elif "impression share" in strategy_text.lower():
            report.error("bidding", where, "Target impression share is not written by this version, because Google does not show its import columns. Choose another bid strategy for the file, and set Target impression share in Google Ads Editor after import.")
        elif not strategy:
            report.error("bidding", where, '"%s" is not a bid strategy this version writes. Use one of: %s.' % (strategy_text, STRATEGY_NAMES))
        targets = {}
        for field, needed_by, example in (("target_cpa", "Target CPA", "45"), ("target_roas_percent", "Target ROAS", "400 for 400%")):
            value = number(raw.get(field))
            if raw.get(field) is not None and value is None:
                report.error("bidding", where, "%s must be a plain number, such as %s, or null." % (field, example))
            elif strategy and strategy["name"] == needed_by and (value is None or value <= 0):
                report.error("bidding", where, "The bid strategy %s needs %s, a number above zero, such as %s." % (needed_by, field, example))
            elif strategy and strategy["name"] != needed_by and value is not None:
                report.error("bidding", where, "%s is set, and the bid strategy is %s. The file would not carry it. Use %s as the bid strategy, or set %s to null." % (field, strategy["name"], needed_by, field))
            targets[field] = value if strategy and strategy["name"] == needed_by else None

        report.tested("networks")
        networks, bad_network = [], False
        for item in as_list(raw.get("networks"), where, "networks", report):
            label = clean(item)
            if not label:
                report.blank += 1
            elif label.lower() not in rules.NETWORKS:
                bad_network = True
                report.error("networks", where, '"%s" is not a network this build writes. This is a Search build. Use Google Search, and Search Partners if wanted.' % label)
            elif rules.NETWORKS[label.lower()] not in networks:
                networks.append(rules.NETWORKS[label.lower()])
        if not networks and not bad_network:
            networks = ["Google Search"]
            report.notes.append("%s named no network, so Google Search alone was used. Search Partners is off." % where)
        elif networks and "Google Search" not in networks:
            report.error("networks", where, "Search Partners is listed without Google Search. Add Google Search.")
        networks.sort(key=list(rules.NETWORKS.values()).index)

        report.tested("ai_max")
        ai_max_text = clean(raw.get("ai_max")).lower()
        ai_max = {"on": True, "off": False}.get(ai_max_text)
        if ai_max is None:
            report.error("ai_max", where, 'ai_max must be on or off%s. Ask the person: Google turns AI Max on for every new Search campaign, '
                         'imported ones included, unless the file says off, and it widens matching beyond the keywords. (Official: %s)'
                         % (', not "%s"' % raw.get("ai_max") if ai_max_text else "", rules.HAND))
        elif ai_max and strategy and not strategy["conversion_based"]:
            report.warn("ai_max", where, "AI Max is on with %s. Google says AI Max needs bidding on conversions to work well, and its search term matching "
                        "does not work with Manual CPC. (Official: %s)" % (strategy["name"], rules.SETUP))

        report.tested("locations")
        locations = []
        for label in read_text_list(raw.get("locations"), where, "locations", report):
            if label.lower() in [known_label.lower() for known_label in locations]:
                report.error("locations", where, 'The location "%s" is listed twice.' % label)
            else:
                locations.append(label)
        if not locations:
            report.error("locations", where, "It has no location. A campaign with no location can show in all locations. Add at least one place, such as a city or a country.")

        report.tested("dates")
        days = {}
        for field in ("start_date", "end_date"):
            text = clean(raw.get(field))
            days[field] = None
            if not text:
                continue
            try:
                if not re.match(r"^\d{4}-\d{2}-\d{2}$", text):
                    raise ValueError
                days[field] = dt.date(int(text[:4]), int(text[5:7]), int(text[8:]))
            except ValueError:
                report.error("dates", where, 'The %s "%s" is not a date written YYYY-MM-DD, such as 2027-01-15.' % (field.replace("_", " "), text))
        if days["start_date"] and days["start_date"] < report.today:
            report.error("dates", where, "The start date %s is in the past. Today is %s. Google Ads Editor does not take a past start date. Use today or later, or leave it blank to start on the day the campaign is enabled."
                         % (days["start_date"], report.today))
        if days["end_date"] and days["end_date"] < (days["start_date"] or report.today):
            report.error("dates", where, "The end date %s is before %s." % (days["end_date"], "the start date %s" % days["start_date"] if days["start_date"] else "today, %s" % report.today))

        campaign = {"name": name, "daily_budget": budget, "bid_strategy": strategy["name"] if strategy else strategy_text,
                    "conversion_based": bool(strategy and strategy["conversion_based"]), "target_cpa": targets["target_cpa"],
                    "target_roas_percent": targets["target_roas_percent"], "networks": networks, "ai_max": ai_max, "locations": locations,
                    "start_date": str(days["start_date"] or ""), "end_date": str(days["end_date"] or ""), "where": where}
        campaigns.append(campaign)
        all_negatives += read_negatives(raw.get("negatives"), where, "campaign", name, "", report)

        group_names = set()
        raw_groups = as_list(raw.get("ad_groups"), where, "ad_groups", report)
        if not raw_groups:
            report.error("structure", where, "It has no ad group.")
        for g_index, graw in enumerate(raw_groups, start=1):
            if not isinstance(graw, dict):
                report.error("plan_fields", "%s > Ad group %d" % (where, g_index), "An ad group must be a set of fields in curly brackets.")
                continue
            gname = clean(graw.get("name"))
            gwhere = '%s > Ad group "%s"' % (where, gname) if gname else "%s > Ad group %d" % (where, g_index)
            known(graw, "ad_group", gwhere, report)
            report.tested("names")
            if not gname:
                report.error("names", gwhere, "It has no name.")
            elif gname.lower() in group_names:
                report.error("names", gwhere, "Two ad groups in this campaign use this name. Google Ads Editor matches rows by name, so the two would merge. Rename one.")
            group_names.add(gname.lower())

            max_cpc = number(graw.get("max_cpc"))
            if graw.get("max_cpc") is not None and max_cpc is None:
                report.error("bidding", gwhere, "max_cpc must be a plain number, such as 4.50, or null.")
            elif max_cpc is not None and max_cpc <= 0:
                report.error("bidding", gwhere, "max_cpc is %s. It must be above zero, or null." % rules.shown(max_cpc))
                max_cpc = None
            elif max_cpc is None and strategy and strategy["name"] == "Manual CPC":
                report.error("bidding", gwhere, "The campaign bids with Manual CPC, so this ad group needs max_cpc, a number above zero.")
            group = {"campaign": name, "name": gname, "max_cpc": max_cpc, "where": gwhere}
            ad_groups.append(group)

            group_keywords = []
            for kraw in as_list(graw.get("keywords"), gwhere, "keywords", report):
                if isinstance(kraw, str):
                    kraw = {"text": kraw}
                if not isinstance(kraw, dict):
                    report.error("plan_fields", gwhere, "Each keyword must have the fields text and match.")
                    continue
                known(kraw, "keyword", gwhere, report)
                text = clean(kraw.get("text"))
                if not text:
                    report.blank += 1
                    continue
                kwhere = '%s > Keyword "%s"' % (gwhere, text)
                report.tested("keyword_form")
                match = clean(kraw.get("match")).lower().replace(" match", "")
                valid = True
                if re.search(r'[\[\]"+]', text) or text.startswith("-"):
                    valid = False
                    report.error("keyword_form", kwhere, "It is written with match type symbols. Write plain words and put exact, phrase or broad in match.")
                if match not in rules.MATCH_TYPES:
                    valid = False
                    report.error("keyword_form", kwhere, 'It has the match type "%s". Use exact, phrase or broad.' % match)
                if len(text.split()) > rules.KEYWORD_WORDS:
                    report.error("keyword_form", kwhere, "It has %d words. A keyword takes at most %d." % (len(text.split()), rules.KEYWORD_WORDS))
                if len(text) > rules.KEYWORD_CHARS:
                    report.error("keyword_form", kwhere, "It is %d characters. A keyword takes at most %d." % (len(text), rules.KEYWORD_CHARS))
                url = clean(kraw.get("final_url"))
                if url:
                    report.tested("final_urls")
                    problem = url_problem(url)
                    if problem:
                        report.error("final_urls", kwhere, 'The final URL "%s" %s.' % (url, problem))
                keyword = {"campaign": name, "ad_group": gname, "text": text, "match": match, "final_url": url, "valid": valid,
                           "words": len(text.split()), "characters": len(text), "key": " ".join(rules.words(text)) or text.lower(),
                           "in_account": [], "where": kwhere}
                group_keywords.append(keyword)
            keywords += group_keywords
            all_negatives += read_negatives(graw.get("negatives"), gwhere, "ad_group", name, gname, report)

            group_ads = []
            for araw in as_list(graw.get("ads"), gwhere, "ads", report):
                if not isinstance(araw, dict):
                    report.error("plan_fields", gwhere, "Each ad must have the fields final_url, path_1, path_2, headlines and descriptions.")
                    continue
                known(araw, "ad", gwhere, report)
                ad = {"campaign": name, "ad_group": gname, "final_url": clean(araw.get("final_url")),
                      "path_1": clean(araw.get("path_1")), "path_2": clean(araw.get("path_2"))}
                for kind in ("headlines", "descriptions"):
                    ad[kind] = [{"text": text, "characters": rules.text_len(text), "codes": rules.codes(text)}
                                for text in read_text_list(araw.get(kind), gwhere, kind, report)]
                if not (ad["final_url"] or ad["path_1"] or ad["path_2"] or ad["headlines"] or ad["descriptions"]):
                    report.blank += 1
                    continue
                ad["number"] = len(group_ads) + 1
                ad["where"] = "%s > Ad %d" % (gwhere, ad["number"])
                check_ad_text(ad, ad["where"], report)
                sequences = [rules.words(k["text"]) for k in group_keywords]
                ad["headlines_with_keyword"] = sum(1 for h in ad["headlines"] if any(c["kind"] == "keyword" and not c["problem"] for c in h["codes"])
                                                   or any(contains(rules.words(rules.shown_text(h["text"])), s) for s in sequences))
                report.tested("keyword_in_headline")
                if sequences and ad["headlines"] and not ad["headlines_with_keyword"]:
                    report.warn("keyword_in_headline", ad["where"], "No headline carries one of this ad group's keywords word for word. Google's tip is to put at least one keyword in the headlines.")
                group_ads.append(ad)
            ads += group_ads

            report.tested("structure")
            if not group_keywords:
                report.error("structure", gwhere, "It has no keyword.")
            if not group_ads:
                report.error("structure", gwhere, "It has no ad. An ad group cannot show without one.")
            elif len(group_ads) > rules.ADS_PER_AD_GROUP:
                report.error("structure", gwhere, "It has %d ads. Google allows %d enabled responsive search ads in one ad group. Drop %d."
                             % (len(group_ads), rules.ADS_PER_AD_GROUP, len(group_ads) - rules.ADS_PER_AD_GROUP))
            report.tested("themed_ad_groups")
            if len({k["key"] for k in group_keywords}) == 1:
                report.warn("themed_ad_groups", gwhere, 'It is built on one keyword, "%s". Google\'s Search guidance is ad groups built on a theme, not on a single keyword. Add the close searches that belong to the same theme, or fold it into a wider ad group.' % group_keywords[0]["text"])
    return brief, list_name, campaigns, ad_groups, keywords, ads, all_negatives


def cross_checks(campaigns, ad_groups, keywords, ads, all_negatives, account, report):
    """Checks that compare one part of the build with another, or with the account."""
    valid = [k for k in keywords if k["valid"]]
    locations = {c["name"]: {place.lower() for place in c["locations"]} for c in campaigns}

    # The same keyword and match type in two places.
    report.tested("duplicate_keywords", len(valid))
    by_key = {}
    for keyword in valid:
        by_key.setdefault((keyword["key"], keyword["match"]), []).append(keyword)
    for (_, match), group in by_key.items():
        text = group[0]["text"]
        by_campaign = {}
        for keyword in group:
            by_campaign.setdefault(keyword["campaign"], []).append(keyword["ad_group"])
        for campaign, groups in by_campaign.items():
            if len(groups) > 1 and len(set(groups)) == 1:
                report.error("duplicate_keywords", 'Campaign "%s" > Ad group "%s"' % (campaign, groups[0]),
                             'The %s match keyword "%s" is listed %d times. Keep one.' % (match, text, len(groups)))
            elif len(groups) > 1:
                report.error("duplicate_keywords", 'Campaign "%s"' % campaign,
                             'The %s match keyword "%s" is in %d ad groups: %s. Two copies compete for the same searches, and Google\'s Search guidance is to remove duplicate keywords. Keep it in one ad group.'
                             % (match, text, len(set(groups)), quoted(sorted(set(groups)))))
        names = sorted(by_campaign)
        for i, first in enumerate(names):
            for second in names[i + 1:]:
                shared = sorted(locations.get(first, set()) & locations.get(second, set()))
                if shared:
                    report.error("duplicate_keywords", 'Campaigns "%s" and "%s"' % (first, second),
                                 'Both hold the %s match keyword "%s" and both target %s. They would compete for the same searches. Keep it in one.' % (match, text, shared[0]))
                else:
                    report.warn("split_keywords", 'Campaigns "%s" and "%s"' % (first, second),
                                'Both hold the %s match keyword "%s". Their location names differ, so this is allowed. Check the places do not overlap, because only the names were compared.' % (match, text))

    # The same words under different match types, in different ad groups of one campaign.
    by_text = {}
    for keyword in valid:
        by_text.setdefault((keyword["campaign"], keyword["key"]), []).append(keyword)
    report.tested("split_keywords", len(by_text))
    for (campaign, _), group in by_text.items():
        places = sorted({(k["ad_group"], k["match"]) for k in group})
        if len({group_name for group_name, _ in places}) > 1 and len({match for _, match in places}) > 1:
            report.warn("split_keywords", 'Campaign "%s"' % campaign,
                        'The keyword text "%s" sits in more than one ad group under different match types: %s. Searches for it can land in either. Google\'s Search guidance keeps a theme\'s match types together in one ad group.'
                        % (group[0]["text"], ", ".join("%s (%s)" % place for place in places)))

    # Every negative against every keyword of the build it can reach.
    report.tested("negative_conflicts", len(all_negatives))
    for negative in all_negatives:
        reach = [k for k in valid if negatives.in_scope(negative, k)]
        hits = [k for k in reach if negatives.blocks(negative["text"], negative["match"], k["text"])]
        negative["tested_against"] = len(reach)
        negative["blocks"] = [{"keyword": k["text"], "match": k["match"], "campaign": k["campaign"], "ad_group": k["ad_group"]} for k in hits]
        if hits:
            level = {"account": "The list negative", "campaign": "The campaign negative", "ad_group": "The ad group negative"}[negative["level"]]
            where = {"account": "Negative keyword list", "campaign": 'Campaign "%s"' % negative["campaign"],
                     "ad_group": 'Campaign "%s" > Ad group "%s"' % (negative["campaign"], negative["ad_group"])}[negative["level"]]
            report.error("negative_conflicts", where, '%s "%s" (%s match) would block %s: %s. Narrow the negative, or drop it.'
                         % (level, negative["text"], negative["match"], "your own keyword" if len(hits) == 1 else "%d of your own keywords" % len(hits),
                            ", ".join('"%s" (%s match, ad group "%s")' % (k["text"], k["match"], k["ad_group"]) for k in hits[:6])
                            + (" and %d more" % (len(hits) - 6) if len(hits) > 6 else "")))
    other_letters = sorted({item["text"] for item in valid + all_negatives if any(ord(ch) > 127 and ch.isalnum() for ch in item["text"])})
    if other_letters and all_negatives:
        report.notes.append("The negative keyword test reads the letters a to z and the digits only. These hold other letters, so check by hand that no negative blocks them: %s." % quoted(other_letters, 12))

    # Google's account limits.
    report.tested("account_limits", len(campaigns) + len(ad_groups) + 1)
    for campaign in campaigns:
        group_count = sum(1 for g in ad_groups if g["campaign"] == campaign["name"])
        negative_count = sum(1 for n in all_negatives if n["level"] != "account" and n["campaign"] == campaign["name"])
        if group_count > rules.AD_GROUPS_PER_CAMPAIGN:
            report.error("account_limits", campaign["where"], "It has %s ad groups. Google allows %s in one campaign." % ("{:,}".format(group_count), "{:,}".format(rules.AD_GROUPS_PER_CAMPAIGN)))
        if negative_count > rules.NEGATIVES_PER_CAMPAIGN:
            report.error("account_limits", campaign["where"], "It has %s negative keywords. Google allows %s in one campaign." % ("{:,}".format(negative_count), "{:,}".format(rules.NEGATIVES_PER_CAMPAIGN)))
    for group in ad_groups:
        count = sum(1 for k in keywords if k["campaign"] == group["campaign"] and k["ad_group"] == group["name"])
        if count > rules.KEYWORDS_PER_AD_GROUP:
            report.error("account_limits", group["where"], "It has %s keywords. Google allows %s targeting items in one ad group." % ("{:,}".format(count), "{:,}".format(rules.KEYWORDS_PER_AD_GROUP)))
    list_count = sum(1 for n in all_negatives if n["level"] == "account")
    if list_count > rules.NEGATIVES_PER_LIST:
        report.error("account_limits", "Negative keyword list", "It has %s keywords. Google allows %s in one list." % ("{:,}".format(list_count), "{:,}".format(rules.NEGATIVES_PER_LIST)))

    # One ad in an ad group, as one line for the whole build.
    report.tested("ads_per_ad_group", len(ad_groups))
    single = [g["name"] for g in ad_groups if sum(1 for a in ads if a["campaign"] == g["campaign"] and a["ad_group"] == g["name"]) == 1]
    if single:
        report.warn("ads_per_ad_group", "Build", "%d of %d ad groups have one responsive search ad: %s. Google's tip is at least 2 in each ad group. One is enough to launch. Add a second when there is a different message to test."
                    % (len(single), len(ad_groups), quoted(single)))

    hosts, plain = set(), set()
    for item in ads + keywords:
        url = item.get("final_url")
        if url and not url_problem(url):
            hosts.add(urlsplit(url).hostname.lower())
            if url.lower().startswith("http://"):
                plain.add(url)
    report.tested("destinations")
    if len(hosts) > 1:
        report.warn("destinations", "Build", "The final URLs point at %d websites: %s. Check that each one belongs to the business." % (len(hosts), ", ".join(sorted(hosts))))
    for url in sorted(plain):
        report.warn("destinations", "Build", 'The final URL "%s" starts with http://. Use https:// if the site has it.' % url)

    for campaign in campaigns:
        mine = [k for k in valid if k["campaign"] == campaign["name"]]
        broad = [k for k in mine if k["match"] == "broad"]
        report.tested("broad_bidding")
        if broad and campaign["bid_strategy"] in [s["name"] for s in rules.BID_STRATEGIES.values()] and not campaign["conversion_based"]:
            report.warn("broad_bidding", campaign["where"], "It has %s and bids with %s. Google ties broad match to Smart Bidding on conversions. Use exact and phrase here, or move to a conversion bid strategy once conversion tracking is confirmed."
                        % (rules.plural(len(broad), "broad match keyword"), campaign["bid_strategy"]))
        report.tested("budget_reach")
        budget = campaign["daily_budget"] or 0
        bids = [g["max_cpc"] for g in ad_groups if g["campaign"] == campaign["name"] and g["max_cpc"]]
        if budget > 0 and campaign["bid_strategy"] == "Manual CPC" and bids and max(bids) > budget:
            report.warn("budget_reach", campaign["where"], "The daily budget is %s and the highest Max CPC is %s, so the budget does not cover one click at that bid." % (rules.shown(budget), rules.shown(max(bids))))
        if budget > 0 and campaign["target_cpa"] and campaign["target_cpa"] > budget:
            report.warn("budget_reach", campaign["where"], "The daily budget is %s and the target CPA is %s, so the budget does not cover one conversion a day at the target." % (rules.shown(budget), rules.shown(campaign["target_cpa"])))
        report.tested("negative_cover")
        if not any(n["level"] == "account" or n["campaign"] == campaign["name"] for n in all_negatives):
            report.warn("negative_cover", campaign["where"], "It has no negative keyword at any level. Add the searches that are plainly wrong for the business before launch, then build the rest from the search terms report.")

    # Against the account's own campaigns and keywords, when the exports were given.
    existing_campaigns = (account or {}).get("campaigns") or []
    if not (account or {}).get("campaigns_report"):
        report.not_run("account_names", "No campaigns report was given, so names were not compared with the account.")
    else:
        by_name = {c["name"].lower(): c for c in existing_campaigns}
        for campaign in campaigns:
            report.tested("account_names")
            hit = by_name.get(campaign["name"].lower())
            if hit and "remov" in (hit.get("status") or "").lower():
                report.warn("account_names", campaign["where"], "A removed campaign in the account has this name. A new name is safer.")
            elif hit:
                report.error("account_names", campaign["where"], "The account already has a campaign with this name%s. Google Ads Editor matches rows by name, so the import would edit that campaign, pause it and change its budget. Choose a name the account has never used."
                             % (" (%s)" % hit["status"] if hit.get("status") else ""))
    if not (account or {}).get("keywords_report"):
        report.not_run("account_keywords", "No keywords report was given, so keywords were not compared with the account.")
    else:
        index = {}
        for existing in account.get("keywords") or []:
            if "remov" not in (existing.get("status") or "").lower():
                index.setdefault((" ".join(rules.words(existing["text"])), existing.get("match")), []).append(existing)
        for keyword in valid:
            report.tested("account_keywords")
            hits = index.get((keyword["key"], keyword["match"]), [])
            keyword["in_account"] = [{"campaign": h["campaign"], "ad_group": h["ad_group"], "status": h.get("status", "")} for h in hits]
            if hits:
                report.warn("account_keywords", keyword["where"], "The account already has this keyword with the same match type: %s. Two copies compete for the same searches. Decide which one keeps the search, and pause the other when this build goes live."
                            % "; ".join('campaign "%s", ad group "%s"%s' % (h["campaign"], h["ad_group"], " (%s)" % h["status"] if h.get("status") else "") for h in hits[:4]))


def totals_for(campaigns, ad_groups, keywords, ads, all_negatives):
    """Every count and sum the reply or the files will need."""
    def keyword_counts(pool):
        return {"keywords": len(pool), "exact": sum(1 for k in pool if k["match"] == "exact"),
                "phrase": sum(1 for k in pool if k["match"] == "phrase"), "broad": sum(1 for k in pool if k["match"] == "broad")}

    for group in ad_groups:
        mine = lambda item: item["campaign"] == group["campaign"] and item["ad_group"] == group["name"]  # noqa: E731
        group.update(keyword_counts([k for k in keywords if mine(k)]))
        group_ads = [a for a in ads if mine(a)]
        group.update(ads=len(group_ads), headlines=sum(len(a["headlines"]) for a in group_ads),
                     descriptions=sum(len(a["descriptions"]) for a in group_ads),
                     negatives=sum(1 for n in all_negatives if n["level"] == "ad_group" and mine(n)))
    for campaign in campaigns:
        mine = lambda item: item["campaign"] == campaign["name"]  # noqa: E731
        campaign.update(keyword_counts([k for k in keywords if mine(k)]))
        budget = campaign["daily_budget"] if campaign["daily_budget"] and campaign["daily_budget"] > 0 else None
        campaign.update(ad_groups=sum(1 for g in ad_groups if mine(g)), ads=sum(1 for a in ads if mine(a)),
                        campaign_negatives=sum(1 for n in all_negatives if n["level"] == "campaign" and mine(n)),
                        ad_group_negatives=sum(1 for n in all_negatives if n["level"] == "ad_group" and mine(n)),
                        day_limit=budget * rules.DAY_LIMIT_TIMES if budget else None,
                        month_limit=budget * rules.MONTH_LIMIT_TIMES if budget else None)
    totals = keyword_counts(keywords)
    budgets = [c["daily_budget"] for c in campaigns if c["daily_budget"] and c["daily_budget"] > 0]
    by_level = {level: sum(1 for n in all_negatives if n["level"] == level) for level in ("account", "campaign", "ad_group")}
    totals.update(campaigns=len(campaigns), ad_groups=len(ad_groups), ads=len(ads),
                  headlines=sum(len(a["headlines"]) for a in ads), descriptions=sum(len(a["descriptions"]) for a in ads),
                  locations=sum(len(c["locations"]) for c in campaigns), negatives=len(all_negatives),
                  list_negatives=by_level["account"], campaign_negatives=by_level["campaign"], ad_group_negatives=by_level["ad_group"],
                  daily_budget=sum(budgets), day_limit=sum(budgets) * rules.DAY_LIMIT_TIMES, month_limit=sum(budgets) * rules.MONTH_LIMIT_TIMES,
                  paused_items=len(campaigns) + len(ad_groups) + len(keywords) + len(ads))
    totals["import_rows"] = (totals["campaigns"] + totals["locations"] + totals["ad_groups"] + totals["keywords"]
                             + totals["campaign_negatives"] + totals["ad_group_negatives"] + totals["ads"])
    return totals


def blockers_for(brief, campaigns):
    """The readiness items the person has not answered yes to."""
    found = []
    bidding_on_conversions = [c for c in campaigns if c["conversion_based"]]
    for key, role, text, verify in rules.READY_ITEMS:
        answer = brief["ready"][key]
        extra = ""
        if key == "conversion_tracking" and bidding_on_conversions:
            extra = " %s on conversions (%s), so %s nothing to learn from without it." % (
                quoted([c["name"] for c in bidding_on_conversions]) + (" bids" if len(bidding_on_conversions) == 1 else " bid"),
                ", ".join(sorted({c["bid_strategy"] for c in bidding_on_conversions})), "it has" if len(bidding_on_conversions) == 1 else "they have")
        found.append({"key": key, "check": text, "detail": extra.strip(), "owner_role": role, "owner": brief["owners"].get(role, ""),
                      "verify": verify, "answer": answer, "open": answer != "yes"})
    return found


def print_report(result, work):
    totals, errors, warnings = result["totals"], result["errors"], result["warnings"]
    open_blockers = [b for b in result["blockers"] if b["open"]]
    account = result["account"]
    if errors:
        print("PLAN CHECK: REFUSED. %s. No file can be written until every one is fixed." % rules.plural(len(errors), "problem"))
        for number_, item in enumerate(errors, start=1):
            print("  %d. %s: %s (%s: %s)" % (number_, item["where"], item["text"], item["label"], item["source"]))
    else:
        print("PLAN CHECK: PASSED. No problems, %s, %s." % (rules.plural(len(warnings), "warning"), rules.plural(len(open_blockers), "open launch blocker")))
    print("  Checked on %s. Compared with the account: %s; %s." % (
        result["checked_on"],
        "%s from the campaigns report" % rules.plural(account["campaigns"], "campaign") if account["campaigns_report"] else "no campaigns report",
        "%s from the keywords report" % rules.plural(account["keywords"], "keyword") if account["keywords_report"] else "no keywords report"))

    if not errors:
        print()
        print("WHAT THE PLAN BUILDS. Everything will be written paused.")
        print("  %s, %s, %s (%d exact, %d phrase, %d broad), %s (%s, %s), %s (%d in the list, %d campaign, %d ad group), %s."
              % (rules.plural(totals["campaigns"], "campaign"), rules.plural(totals["ad_groups"], "ad group"), rules.plural(totals["keywords"], "keyword"),
                 totals["exact"], totals["phrase"], totals["broad"], rules.plural(totals["ads"], "responsive search ad"),
                 rules.plural(totals["headlines"], "headline"), rules.plural(totals["descriptions"], "description"),
                 rules.plural(totals["negatives"], "negative keyword"), totals["list_negatives"], totals["campaign_negatives"], totals["ad_group_negatives"],
                 rules.plural(totals["locations"], "location")))
        print("  Daily budget, all campaigns: %s. The most Google can spend in one day: %s. The most it can charge in one month: %s."
              % (rules.shown(totals["daily_budget"]), rules.shown(totals["day_limit"]), rules.shown(totals["month_limit"])))
        print("  Those two limits are the daily budget times %d and times %s. (Official: %s)" % (rules.DAY_LIMIT_TIMES, rules.MONTH_LIMIT_TIMES, rules.HAND))
        print(outputs.md_table(["Campaign", "Daily budget", "Most in a month", "Bid strategy", "Networks", "Locations", "Ad groups", "Keywords", "Ads", "Campaign negatives"],
                               [[c["name"], rules.shown(c["daily_budget"]), rules.shown(c["month_limit"]), bid_text(c), ", ".join(c["networks"]),
                                 "; ".join(c["locations"]), c["ad_groups"], c["keywords"], c["ads"], c["campaign_negatives"]] for c in result["campaigns"]]))
        print()
        print(outputs.md_table(["Campaign", "Ad group", "Max CPC", "Keywords", "Exact", "Phrase", "Broad", "Ads", "Headlines", "Descriptions", "Ad group negatives"],
                               [[g["campaign"], g["name"], rules.shown(g["max_cpc"]), g["keywords"], g["exact"], g["phrase"], g["broad"], g["ads"],
                                 g["headlines"], g["descriptions"], g["negatives"]] for g in result["ad_groups"]]))
        print()
        print("KEYWORDS")
        print(outputs.md_table(["Campaign", "Ad group", "Keyword", "Match type", "Already in the account"],
                               [[k["campaign"], k["ad_group"], k["text"], k["match"],
                                 "; ".join("%s > %s" % (h["campaign"], h["ad_group"]) for h in k["in_account"])] for k in result["keywords"]]))
        print()
        print("AD TEXT. Characters are counted the way Google counts them. A double width character counts as 2.")
        for ad in result["ads"]:
            print("  %s. Final URL: %s. Paths: %s. Headlines with a keyword of the ad group: %d of %d."
                  % (ad["where"], ad["final_url"], " / ".join(p for p in (ad["path_1"], ad["path_2"]) if p) or "none", ad["headlines_with_keyword"], len(ad["headlines"])))
            print(outputs.md_table(["Part", "Text", "Characters", "Limit"],
                                   [["Headline %d" % i, h["text"], h["characters"], rules.HEADLINE_CHARS] for i, h in enumerate(ad["headlines"], start=1)]
                                   + [["Description %d" % i, d["text"], d["characters"], rules.DESCRIPTION_CHARS] for i, d in enumerate(ad["descriptions"], start=1)]))
        print()
        print("NEGATIVE KEYWORDS. Each was tested against every keyword of the build it can reach. None blocks one.")
        print(outputs.md_table(["Level", "Campaign", "Ad group", "Negative keyword", "Match type", "Own keywords tested", "Why"],
                               [[level_text(n["level"]), n["campaign"], n["ad_group"], n["text"], n["match"], n["tested_against"], n["why"]] for n in result["negatives"]]))
        print()
        print("CHECKS. Tested is the number of items each check looked at.")
        print(outputs.md_table(["Check", "Result", "Tested", "Source"],
                               [[c["check"], c["result"], c["tested"] if not c["not_run"] else c["not_run"], "%s: %s" % (c["label"], c["source"])] for c in result["checks"]]))

    if warnings:
        print()
        print("WARNINGS (%d). A warning does not stop the files. Decide each one with the person, and say what was decided." % len(warnings))
        for number_, item in enumerate(warnings, start=1):
            print("  %d. %s: %s (%s: %s)" % (number_, item["where"], item["text"], item["label"], item["source"]))
    if not errors:
        print()
        print("LAUNCH BLOCKERS. The files can be written. Nothing may be enabled until every one reads yes.")
        print(outputs.md_table(["Must be true before launch", "Answer in the plan", "Owner"],
                               [[(b["check"] + ". " + b["detail"]).strip(), b["answer"], b["owner"] or "Not assigned"] for b in result["blockers"]]))
        unassigned = [label for key, label, _ in rules.OWNER_ROLES if not result["brief"]["owners"].get(key)]
        if unassigned:
            print("  No owner is named for: %s. Ask the person who owns each." % ", ".join(unassigned))
        if result["brief"]["assumptions"]:
            print()
            print("ASSUMPTIONS WRITTEN IN THE PLAN. Tell the person each one.")
            for line in result["brief"]["assumptions"]:
                print("  - " + line)
        missing = [name.replace("_", " ") for name in ("business", "goal", "primary_conversion", "hypothesis", "success_metric", "early_warning") if not result["brief"][name]]
        if missing:
            print()
            print("NOT FILLED IN UNDER brief: %s. The launch checklist will show each as not recorded." % ", ".join(missing))
    if result["notes"]:
        print()
        print("NOTES")
        for line in result["notes"]:
            print("  - " + line)
    print()
    if errors:
        print("Next: fix %s and run python3 scripts/check_plan.py --work %s again." % (os.path.join(work, "plan.json"), work))
    else:
        print("Next: python3 scripts/write_build.py --work %s --out OUTPUTDIR" % work)


def bid_text(campaign):
    if campaign["target_cpa"]:
        return "%s, target %s" % (campaign["bid_strategy"], rules.shown(campaign["target_cpa"]))
    if campaign["target_roas_percent"]:
        return "%s, target %s%%" % (campaign["bid_strategy"], ("%f" % campaign["target_roas_percent"]).rstrip("0").rstrip("."))
    return campaign["bid_strategy"]


def level_text(level):
    return {"account": "List", "campaign": "Campaign", "ad_group": "Ad group"}[level]


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True, help="the folder that holds plan.json")
    parser.add_argument("--today", help="the date to treat as today, YYYY-MM-DD. Left out, it is this computer's date")
    args = parser.parse_args()

    plan_path = os.path.join(args.work, "plan.json")
    if not os.path.exists(plan_path):
        raise SystemExit("No plan.json in %s. Run python3 scripts/start_build.py --work %s, copy plan.template.json to plan.json and fill it in." % (args.work, args.work))
    try:
        plan = outputs.read_json(plan_path)
    except ValueError as error:
        raise SystemExit("plan.json is not valid JSON, so it cannot be read: %s. Fix that and run the check again." % error)
    if not isinstance(plan, dict):
        raise SystemExit("plan.json must start with a curly bracket and hold the fields of plan.template.json.")
    try:
        today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    except ValueError:
        raise SystemExit('--today must be a date written YYYY-MM-DD. "%s" is not.' % args.today)
    account_path = os.path.join(args.work, "account.json")
    account = outputs.read_json(account_path) if os.path.exists(account_path) else None

    report = Report()
    report.today = today
    brief, list_name, campaigns, ad_groups, keywords, ads, all_negatives = read_plan(plan, report)
    attribute_checks(ads, report)
    cross_checks(campaigns, ad_groups, keywords, ads, all_negatives, account, report)
    totals = totals_for(campaigns, ad_groups, keywords, ads, all_negatives)
    if report.blank:
        report.notes.append("%s left empty in the plan %s ignored." % (rules.plural(report.blank, "entry", "entries"), "was" if report.blank == 1 else "were"))
    performance_max = [c["name"] for c in (account or {}).get("campaigns") or []
                       if "performance max" in (c.get("type") or "").lower() and "remov" not in (c.get("status") or "").lower()]
    with open(plan_path, "rb") as handle:
        plan_hash = hashlib.sha256(handle.read()).hexdigest()
    account_hash = None
    if os.path.exists(account_path):
        with open(account_path, "rb") as handle:
            account_hash = hashlib.sha256(handle.read()).hexdigest()
    result = {
        "plan_hash": plan_hash, "account_hash": account_hash, "checked_on": str(today), "passed": not report.errors,
        "brief": brief, "negative_list_name": list_name,
        "account": {"campaigns_report": (account or {}).get("campaigns_report"), "keywords_report": (account or {}).get("keywords_report"),
                    "campaigns": len((account or {}).get("campaigns") or []), "keywords": len((account or {}).get("keywords") or []),
                    "performance_max": performance_max},
        "totals": totals, "campaigns": campaigns, "ad_groups": ad_groups, "keywords": keywords, "ads": ads, "negatives": all_negatives,
        "checks": report.results(), "errors": report.errors, "warnings": report.warnings, "notes": report.notes,
        "blockers": blockers_for(brief, campaigns),
    }
    outputs.write_json(os.path.join(args.work, "checked.json"), result)

    # Keep what each refused run found, so the summary can say what the check caught on the way.
    history_path = os.path.join(args.work, "check-history.json")
    history = outputs.read_json(history_path) if os.path.exists(history_path) else []
    if not history or history[-1]["plan_hash"] != plan_hash:
        history.append({"run": len(history) + 1, "plan_hash": plan_hash, "passed": not report.errors,
                        "problems": [{"where": e["where"], "text": e["text"]} for e in report.errors]})
        outputs.write_json(history_path, history)

    print_report(result, args.work)
    if report.errors:
        sys.exit(1)


if __name__ == "__main__":
    main()
