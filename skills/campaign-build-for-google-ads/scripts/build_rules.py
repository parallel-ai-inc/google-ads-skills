"""Limits, plan fields and small helpers shared by the three campaign build steps.

Every limit names the reference file it was taken from, so the template, the
check and the files always agree. This file is a module. It has no command.
"""
import datetime
import re
import unicodedata

HAND = "references/build-limits-and-editor-import.md"
SPECS = "references/ad-specs-limits.md"
SETUP = "references/search-campaign-setup.md"
STRUCTURE = "references/account-structure.md"
KEYWORDS = "references/keywords.md"
LAUNCH = "references/campaign-launch.md"
CREATIVE = "references/creative.md"
CUSTOMIZERS = "references/ad-customizers.md"

HEADLINES_MIN, HEADLINES_MAX, HEADLINE_CHARS = 3, 15, 30
DESCRIPTIONS_MIN, DESCRIPTIONS_MAX, DESCRIPTION_CHARS = 2, 4, 90
PATH_CHARS = 15
ADS_PER_AD_GROUP = 3
KEYWORD_WORDS, KEYWORD_CHARS = 10, 80
AD_GROUPS_PER_CAMPAIGN = 20000
KEYWORDS_PER_AD_GROUP = 20000
NEGATIVES_PER_CAMPAIGN = 10000
NEGATIVES_PER_LIST = 5000
DAY_LIMIT_TIMES = 2
MONTH_LIMIT_TIMES = 30.4
# Codes in braces that Google reads in a responsive search ad. See references/ad-customizers.md.
KEYWORD_CODES = ("keyword", "Keyword", "KeyWord", "KEYWord", "KeyWORD")
LOCATION_LEVELS = ("City", "State", "Country")
LOCATION_PER_HEADLINE, LOCATION_PER_DESCRIPTION = 1, 2
COUNTDOWN_CHARS = 8
HEADLINES_WITHOUT_COUNTDOWN = 3
CUSTOMIZER_ATTRIBUTES = 40

# What the check enforces, in plain words, with the file each line comes from.
LIMIT_LINES = [
    ("Headlines in one ad: %d to %d. Each %d characters or fewer." % (HEADLINES_MIN, HEADLINES_MAX, HEADLINE_CHARS), HAND),
    ("Descriptions in one ad: %d to %d. Each %d characters or fewer." % (DESCRIPTIONS_MIN, DESCRIPTIONS_MAX, DESCRIPTION_CHARS), HAND),
    ("Path 1 and Path 2: %d characters or fewer each." % PATH_CHARS, HAND),
    ("A double width character, as in Chinese, Japanese or Korean, counts as 2.", HAND),
    ("Responsive search ads in one ad group: %d enabled at most." % ADS_PER_AD_GROUP, SPECS),
    ("One keyword: %d words and %d characters at most." % (KEYWORD_WORDS, KEYWORD_CHARS), HAND),
    ("Daily budget: above zero.", HAND),
    ("Start date: YYYY-MM-DD, today or later. End date: on or after the start date.", HAND),
    ("Every campaign needs a location. A campaign with no location can show in all locations.", HAND),
    ("Bid strategies this version writes: Manual CPC, Maximize clicks, Maximize conversions, Maximize conversion value, Target CPA, Target ROAS.", HAND),
    ("Enhanced CPC is no longer available for Search campaigns.", SETUP),
    ("Language targeting is no longer set by hand on Search campaigns, so the file has no language column.", SETUP),
    ("Networks: Google Search, with or without Search Partners.", HAND),
    ("Negative keywords: %s per campaign, %s per negative keyword list." % ("{:,}".format(NEGATIVES_PER_CAMPAIGN), "{:,}".format(NEGATIVES_PER_LIST)), HAND),
    ("Ad groups in one campaign: %s. Keywords in one ad group: %s." % ("{:,}".format(AD_GROUPS_PER_CAMPAIGN), "{:,}".format(KEYWORDS_PER_AD_GROUP)), HAND),
    ("A campaign can spend up to %d times its daily budget in one day and at most %s times in one month." % (DAY_LIMIT_TIMES, MONTH_LIMIT_TIMES), HAND),
    ("Codes in ad text: {KeyWord:default text}, {LOCATION(City):default text} with City, State or Country, "
     "{COUNTDOWN(yyyy-MM-dd HH:mm:ss,daysBefore)} or GLOBAL_COUNTDOWN, and {CUSTOMIZER.Name:default text}. No IF function, no code in the Final URL.", CUSTOMIZERS),
    ("A line with a code is counted with its default text in place of the code, and a countdown as %d characters. "
     "At least %d headlines without a countdown. One location code per headline, %d per description. %d customizer attributes per account."
     % (COUNTDOWN_CHARS, HEADLINES_WITHOUT_COUNTDOWN, LOCATION_PER_DESCRIPTION, CUSTOMIZER_ATTRIBUTES), CUSTOMIZERS),
]

# Lowercase name in the plan -> the value Google Ads Editor takes.
BID_STRATEGIES = {
    "manual cpc": {"name": "Manual CPC", "conversion_based": False},
    "maximize clicks": {"name": "Maximize clicks", "conversion_based": False},
    "maximize conversions": {"name": "Maximize conversions", "conversion_based": True},
    "maximize conversion value": {"name": "Maximize conversion value", "conversion_based": True},
    "target cpa": {"name": "Target CPA", "conversion_based": True},
    "target roas": {"name": "Target ROAS", "conversion_based": True},
}
NETWORKS = {"google search": "Google Search", "search partners": "Search Partners"}
MATCH_TYPES = {"exact": "Exact", "phrase": "Phrase", "broad": "Broad"}
PAUSED = "Paused"

# The people a launch needs. The plan names each one under brief.owners.
OWNER_ROLES = [
    ("build", "Build and import", "Builds the plan, imports the file and checks it in Google Ads Editor"),
    ("tracking", "Conversion tracking", "Confirms the conversion action records what the campaign is meant to drive"),
    ("landing_pages", "Landing pages", "Confirms every final URL loads and matches its ad group"),
    ("approval", "Approval", "Approves the budget, the ad text and the billing set up for the business"),
    ("launch", "Launch", "Enables the campaign on launch day and watches the first 14 days"),
]

# What must be true before anything is enabled. Only the person can answer yes.
READY_ITEMS = [
    ("conversion_tracking", "tracking", "The conversion action named in the brief is recording conversions",
     "In Google Ads: Goals, Conversions, All conversions. Find the conversion action and check that it has recorded recent conversions."),
    ("billing", "approval", "Billing is set up and the payment method works",
     "In Google Ads: Billing, Summary. Check there is no payment alert on the account."),
    ("landing_pages", "landing_pages", "Every final URL loads on mobile and on desktop, and matches its ad group",
     "Open each final URL on the Ads sheet of the workbook on a phone and on a computer. Check the page offers what the ad offers."),
    ("budget_approved", "approval", "The budget holder approved the daily budget and what it can add up to in a month",
     "Show the budget holder the daily budget and the monthly spending limit on the Campaigns sheet, and get a yes in writing."),
    ("locations_confirmed", "approval", "The business confirmed the locations",
     "Read the locations on the Campaigns sheet to the business and confirm they are the places it serves."),
    ("ad_copy_approved", "approval", "The business approved the ad text",
     "Send the Ad text sheet to the business. Every claim, price and offer in it must be true."),
]
READY_ANSWERS = ("yes", "no", "unknown")

ALLOWED = {
    "plan": ["how_to_fill", "brief", "negative_keyword_list", "campaigns"],
    "brief": ["business", "offer", "goal", "primary_conversion", "hypothesis", "success_metric", "early_warning",
              "assumptions", "owners", "ready"],
    "owners": [key for key, _, _ in OWNER_ROLES],
    "ready": [key for key, _, _, _ in READY_ITEMS],
    "negative_keyword_list": ["name", "keywords"],
    "campaign": ["name", "daily_budget", "bid_strategy", "target_cpa", "target_roas_percent", "networks", "ai_max", "locations",
                 "start_date", "end_date", "negatives", "ad_groups"],
    "ad_group": ["name", "max_cpc", "keywords", "negatives", "ads"],
    "keyword": ["text", "match", "final_url"],
    "negative": ["text", "match", "why"],
    "ad": ["final_url", "path_1", "path_2", "headlines", "descriptions"],
}

FIELD_LINES = [
    "brief.business, offer, goal, primary_conversion: what the person told you, in their words.",
    "brief.hypothesis, success_metric, early_warning: what the campaign is expected to do, how success is measured, and the first sign it is going wrong.",
    "brief.assumptions: a list. Every choice you made that the person did not state.",
    "brief.owners: a name for each of build, tracking, landing_pages, approval and launch. Leave blank when nobody was named.",
    "brief.ready: yes, no or unknown for conversion_tracking, billing, landing_pages, budget_approved, locations_confirmed and ad_copy_approved. Write yes only when the person said so.",
    "negative_keyword_list: name and keywords. Searches that are wrong for the whole business. It applies to every campaign in the plan.",
    "campaigns[].name: a name the account has never used.",
    "campaigns[].daily_budget: a plain number above zero, such as 90 or 90.50.",
    "campaigns[].bid_strategy: Manual CPC, Maximize clicks, Maximize conversions, Maximize conversion value, Target CPA or Target ROAS.",
    "campaigns[].target_cpa: a number, only with Target CPA. campaigns[].target_roas_percent: a number such as 400 for 400%, only with Target ROAS.",
    "campaigns[].networks: Google Search, and Search Partners if wanted.",
    "campaigns[].ai_max: on or off, as the person chose. Google turns AI Max on for every new Search campaign, imported ones included, unless the file says off. It widens matching beyond the keywords and can change ad text and final URLs.",
    "campaigns[].locations: one or more place names as Google Ads shows them, such as \"Austin, Texas, United States\".",
    "campaigns[].start_date and end_date: YYYY-MM-DD, or blank. Blank means the campaign starts on the day it is enabled.",
    "campaigns[].negatives: negative keywords for this campaign. Each has text, match (exact, phrase or broad) and why.",
    "ad_groups[].name: unique inside its campaign. ad_groups[].max_cpc: a number, needed with Manual CPC.",
    "ad_groups[].keywords: each has text in plain words, match (exact, phrase or broad) and an optional final_url.",
    "ad_groups[].negatives: negative keywords for this ad group only.",
    "ad_groups[].ads: 1 to %d responsive search ads. Each has final_url, path_1, path_2, %d to %d headlines and %d to %d descriptions."
    % (ADS_PER_AD_GROUP, HEADLINES_MIN, HEADLINES_MAX, DESCRIPTIONS_MIN, DESCRIPTIONS_MAX),
    "There is no status field and no pin field. Everything is written paused, and nothing is pinned.",
]


def template():
    """The empty plan the AI tool copies and fills in."""
    return {
        "how_to_fill": "Fill in every field from the brief. Add campaigns, ad groups, keywords, ads and negatives by copying the "
                       "empty ones. Write keywords and negatives as plain words and put the match type in match. Under ready, "
                       "write yes only when the person said so. List every choice the person did not state under assumptions. "
                       "Then run check_plan.py. Everything is written paused.",
        "brief": {
            "business": "", "offer": "", "goal": "", "primary_conversion": "",
            "hypothesis": "", "success_metric": "", "early_warning": "",
            "assumptions": [],
            "owners": {key: "" for key, _, _ in OWNER_ROLES},
            "ready": {key: "unknown" for key, _, _, _ in READY_ITEMS},
        },
        "negative_keyword_list": {"name": "", "keywords": [{"text": "", "match": "phrase", "why": ""}]},
        "campaigns": [{
            "name": "", "daily_budget": 0, "bid_strategy": "", "target_cpa": None, "target_roas_percent": None,
            "networks": ["Google Search"], "ai_max": "", "locations": [""], "start_date": "", "end_date": "",
            "negatives": [{"text": "", "match": "phrase", "why": ""}],
            "ad_groups": [{
                "name": "", "max_cpc": None,
                "keywords": [{"text": "", "match": "phrase", "final_url": ""}],
                "negatives": [{"text": "", "match": "phrase", "why": ""}],
                "ads": [{"final_url": "", "path_1": "", "path_2": "", "headlines": ["", "", ""], "descriptions": ["", ""]}],
            }],
        }],
    }


def display_len(text):
    """Characters as Google counts them: a double width character counts as 2."""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in text)


CODE = re.compile(r"\{([^{}]*)\}")
COUNTDOWN_CODE = re.compile(r"^(GLOBAL_COUNTDOWN|COUNTDOWN)\((\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})(?:,(\d+))?\)$")
CODE_FORMS = ("{KeyWord:default text}, {LOCATION(City):default text}, {COUNTDOWN(2026-12-24 18:00:00,5)} "
              "and {CUSTOMIZER.Name:default text}")


def read_code(inner):
    """One code in braces, read the way a responsive search ad reads it.

    Returns kind, default (the text that shows when nothing is inserted), attribute,
    end (a countdown's end) and problem (empty when Google reads the code)."""
    code = {"code": "{%s}" % inner, "kind": "unknown", "default": "", "attribute": "", "end": None, "problem": ""}
    head, _, default = inner.partition(":")
    upper = inner.strip().upper()
    if inner.startswith("="):
        code["problem"] = "is the old text ad form. A responsive search ad code has no equals sign and no quotation marks"
    elif upper.startswith("IF("):
        code["problem"] = "uses the IF function, which responsive search ads do not support"
    elif "COUNTDOWN(" in upper:
        code["kind"] = "countdown"
        found = COUNTDOWN_CODE.match(inner)
        if not found:
            code["problem"] = "is not a countdown Google reads. Write it as {COUNTDOWN(yyyy-MM-dd HH:mm:ss,daysBefore)}, such as {COUNTDOWN(2026-12-24 18:00:00,5)}, with no default text"
        else:
            try:
                code["end"] = datetime.datetime.strptime(found.group(2), "%Y-%m-%d %H:%M:%S").date().isoformat()
            except ValueError:
                code["problem"] = "has an end date or time that does not exist"
    elif upper.startswith("LOCATION"):
        code["kind"] = "location"
        found = re.match(r"^LOCATION\(([^()]*)\)$", head)
        if not found or found.group(1) not in LOCATION_LEVELS:
            code["problem"] = "is not a location code Google reads. Write {LOCATION(City):default text}, with City, State or Country, in these capitals"
        code["default"] = default.strip()
    elif upper.startswith("CUSTOMIZER."):
        code["kind"] = "customizer"
        name = head[len("CUSTOMIZER."):].strip()
        code["attribute"] = name
        code["default"] = default.strip()
        if not head.startswith("CUSTOMIZER."):
            code["problem"] = "must start with CUSTOMIZER in capitals, as {CUSTOMIZER.Name:default text}"
        elif not re.match(r"^[^\W_][\w ]*$", name):
            code["problem"] = 'names the attribute "%s". An attribute name cannot start with an underscore or hold symbols or punctuation, or ads may be disapproved' % name
    elif head.strip().lower() == "keyword":
        code["kind"] = "keyword"
        code["default"] = default.strip()
        if head.strip() not in KEYWORD_CODES:
            code["problem"] = "writes keyword as %s. Google reads keyword, Keyword, KeyWord, KEYWord or KeyWORD, and the capitals set how the keyword shows" % head.strip()
    else:
        code["problem"] = "is not a code Google Ads reads in a responsive search ad. The codes are %s" % CODE_FORMS
    if not code["problem"] and code["kind"] in ("keyword", "location", "customizer") and not code["default"]:
        code["problem"] = "has no default text after the colon. This skill asks for default text on every code, so the line can be counted and always shows words"
    return code


def codes(text):
    """Every code in braces in one line of ad text, with a stray brace reported as a code of its own."""
    found = [read_code(m.group(1)) for m in CODE.finditer(text)]
    rest = CODE.sub("", text)
    if "{" in rest or "}" in rest:
        found.append({"code": "{" if "{" in rest else "}", "kind": "unknown", "default": "", "attribute": "", "end": None,
                      "problem": "is a brace with no partner. A code needs both { and }"})
    return found


def shown_text(text):
    """The line as it reads when every code shows its default text. A countdown shows nothing here."""
    def swap(match):
        code = read_code(match.group(1))
        return match.group(0) if code["problem"] else code["default"]
    return CODE.sub(swap, text)


def text_len(text):
    """Characters Google counts for a line of ad text: default text in place of each code, and a countdown's own length."""
    countdowns = sum(1 for code in codes(text) if code["kind"] == "countdown" and not code["problem"])
    return display_len(shown_text(text)) + COUNTDOWN_CHARS * countdowns


def words(text):
    """Lowercase words in any alphabet. Punctuation and symbols are dropped."""
    return re.findall(r"[^\W_]+(?:['&][^\W_]+)*", (text or "").lower())


def money(value):
    """Plain number, two decimals, no currency symbol."""
    return "" if value is None else "%.2f" % value


def shown(value):
    """Two decimals with thousands separators, for text a person reads."""
    return "" if value is None else "{:,.2f}".format(value)


def plural(count, one, many=None):
    return "%s %s" % ("{:,}".format(count), one if count == 1 else (many or one + "s"))
