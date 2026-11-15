"""Shared pieces for the two conversion tracking steps.

Reads the exports, names each setting the same way whatever the export calls
it, and holds the rules with their labels and the checks a report cannot make.
This file is not a step. Run audit_actions.py or find_breaks.py.
"""
import os
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, io  # noqa: E402

# Header text (lowercase) -> short name. Several spellings are accepted, because
# the conversions summary download has not been checked against a real file yet.
ALIASES = {
    "conversion action": "conversion_action", "conversion action name": "conversion_action",
    "conversion name": "conversion_action", "name": "conversion_action",
    "action optimization": "optimization", "action optimisation": "optimization", "optimization": "optimization",
    "primary/secondary": "optimization", 'include in "conversions"': "optimization",
    "include in “conversions”": "optimization", "include in conversions": "optimization",
    "conversion source": "source", "source": "source",
    "category": "category", "conversion category": "category", "conversion goal": "category", "goal": "category",
    "status": "status", "tracking status": "status",
    "count": "count", "counting": "count",
    "click-through conversion window": "click_window", "click-through conv. window": "click_window",
    "click-through window": "click_window", "conversion window": "click_window",
    "view-through conversion window": "view_window", "view-through conv. window": "view_window",
    "view-through window": "view_window",
    "engaged-view conversion window": "engaged_window", "engaged-view conv. window": "engaged_window",
    "attribution model": "attribution_model",
    "value": "value_setting", "value setting": "value_setting", "default value": "value_setting",
    "all conv.": "all_conv", "all conversions": "all_conv",
    "all conv. value": "all_conv_value", "all conversions value": "all_conv_value",
    "repeat rate": "repeat_rate",
    "interactions": "clicks",
}
NUMERIC = ("all_conv", "all_conv_value", "repeat_rate")
LABELS = {"conversion_action": "Conversion action", "optimization": "Action optimization", "source": "Conversion source",
          "category": "Category", "status": "Status", "count": "Count", "all_conv": "All conv.",
          "all_conv_value": "All conv. value", "day": "Day", "clicks": "Clicks", "changed_at": "Date & time",
          "changes": "Changes", "campaign": "Campaign"}

# The audit rules. Each has a label, the rule, and the page or playbook it comes from.
OFFICIAL, PRACTITIONER = "Official", "Practitioner rule"
RULES = {
    "bidding": (OFFICIAL, "Bidding uses a conversion action only when it is Primary and in a goal the campaign uses. "
                          "Secondary actions are reported in All conv. only, unless a custom goal includes them.",
                "Google Ads Help, About primary and secondary conversion actions"),
    "repair_first": (PRACTITIONER, "When the conversion signal is broken, repairing tracking comes before any optimization.", ""),
    "status": (OFFICIAL, "Awaiting conversions and No recent conversions mean no conversion was recorded in the last 7 days. "
                         "Misconfigured means recording has stopped because of a setup error or a broken tag. "
                         "Tag inactive means Google no longer sees the tag.",
               "Google Ads Help, Troubleshooting conversion tracking status"),
    "count": (OFFICIAL, "Every counts each conversion after an ad interaction. One counts only one conversion per ad click. "
                        "Google calls Every a good choice for sales, and gives leads as the case for One: only one unique lead per click.",
              "Google Ads Help, About conversion counting options"),
    "count_future": (OFFICIAL, "A change to the count setting applies to future conversions only.",
                     "Google Ads Help, About conversion counting options"),
    "double": (PRACTITIONER, "Two Primary actions in one category from different sources can be the same event counted twice. "
                             "Confirm what each one records before changing either.", ""),
    "double_fix": (OFFICIAL, "Google sets conversion actions created from Google Analytics to Secondary to prevent counting the "
                             "same event twice for bidding, and its fix for double counting is to switch the extra action to Secondary.",
                   "Analytics Help, Create Google Ads conversions based on Google Analytics key events"),
    "value": (OFFICIAL, "Conversion value has to be set up on the action before values can be used for insights or for Smart Bidding. "
                        "An action uses the same value for each conversion, or a different value for each.",
              "Google Ads Help, About conversion values"),
    "value_non_purchase": (OFFICIAL, "Non purchase actions that are Primary and carry a value can double count value. "
                                     "Google's fix is to switch them to Secondary or to remove their value.",
                           "Google Ads Help, Data discrepancies: Factors and troubleshooting"),
    "outcome": (PRACTITIONER, "Do not optimize toward a conversion action until it represents the business outcome.", ""),
    "cycles": (OFFICIAL, "Goal and action changes need 1 to 2 conversion cycles in most cases, and Google recommends moving targets gradually.",
               "Google Ads Help, Changing conversion goals and actions used for Smart Bidding"),
    "click_date": (OFFICIAL, "Google Ads reports a conversion on the date of the ad interaction that led to it, not the date it happened, "
                             "and conversions can be reported up to 90 days after the click. Recent days keep filling in.",
                   "Google Ads Help, Data discrepancies: Factors and troubleshooting"),
    "exclusion": (OFFICIAL, "A data exclusion reduces the effect of a tracking outage on Smart Bidding. Its dates are chosen by the affected "
                            "clicks, allowing for the usual delay between click and conversion. Google says not to remove one once applied.",
                  "Google Ads Help, About data exclusions"),
    "provisional": (PRACTITIONER, "While tracking is in doubt, changes to bids, targets and budgets are provisional.", ""),
}


def rule(key):
    label, text, source = RULES[key]
    return {"label": label, "rule": text, "source": source}


def rule_text(key):
    label, text, source = RULES[key]
    return "**%s:** %s%s" % (label, text, " (%s.)" % source if source else "")


# Checks a report cannot make. Each: the check, its label, and where it comes from.
_STATUS = ("In Google Ads, open Goals, Conversions, All conversions and hover over the Tracking status of this action. Google shows its own diagnosis there.",
           OFFICIAL, "Google Ads Help, Troubleshooting conversion tracking status")
_HISTORY = ("Read the change history for the days just before {day}. Look for edits to conversion actions, to goals, and to the goals a campaign uses.",
            PRACTITIONER, "")
_GOALS = ("Check which goals each affected campaign uses, and whether a custom goal is in play. A report does not show this.",
          OFFICIAL, "Google Ads Help, About conversion goals")
_TAG = ("Trigger the conversion yourself on the live site and watch the tag. Tag Assistant does this: in Goals, Conversions, All conversions, "
        "hover over the Tracking status and choose Troubleshoot.", OFFICIAL, "Google Ads Help, Use Tag Assistant to troubleshoot your unverified or inactive conversion actions")
_SITE = ("Ask what changed on the website on or just before {day}: a release, a new form or checkout, a new confirmation page address, "
         "or a tag manager publish.", PRACTITIONER, "")
_CONSENT = ("Check the consent banner. Default consent states must be set before any tag sends data, and updated after the visitor chooses. "
            "Check ad_user_data and ad_personalization, not only cookie storage.", OFFICIAL, "Google for Developers, Set up consent mode on websites")
_CLICK_ID = ("Confirm the click identifiers still reach the site and the tag: gclid, gbraid or wbraid.", PRACTITIONER, "")
_KEY_EVENT = ("In Google Analytics, check that the key event still exists under the same name and still receives events, "
              "and that the property is still linked to this Google Ads account.", PRACTITIONER, "")
_GA_DELAY = ("Allow for the delay. Google says Analytics conversions can take up to 24 hours to reach Google Ads, and to allow "
             "24 to 48 hours before comparing the two.", OFFICIAL, "Google Ads Help, Create conversions from Google Analytics events in Google Ads")
_UPLOAD = ("Ask whoever runs the upload whether it still runs, and read its last result: upload status, partial failures and diagnostics.",
           PRACTITIONER, "")
_UPLOAD_IDS = ("Check the identifiers and timestamps in the upload: click IDs or hashed customer data, conversion time and time zone.",
               PRACTITIONER, "")
_UPLOAD_PATH = ("Confirm which path the upload uses. Since June 15, 2026 Google blocks offline conversion imports and enhanced conversions "
                "for leads uploads in the Google Ads API unless there is qualifying upload history or an allowlisting. Data Manager API is the current path.",
                OFFICIAL, "Google Ads Developer Blog, Changes to Offline Click Conversion Import Support in the Google Ads API")
_UPLOAD_LAG = ("Imports are not instant. Read conversion time reporting and the import diagnostics before calling it a failure.", PRACTITIONER, "")
_END_TO_END = ("Ask what changed on or just before {day} in whatever sends this conversion, and test it once from end to end.", PRACTITIONER, "")
_WHAT_RECORDS = ("Find out what each action records. Make one real conversion and see which actions count it.", PRACTITIONER, "")
_FIRES_TWICE = ("Check whether a tag now fires twice: on a reloaded confirmation page, on two pages, or from two tags for the same action.",
                PRACTITIONER, "")
_ORDER_ID = ("Check whether an order ID or a lead ID is sent with each conversion, so that a repeat can be recognised.", PRACTITIONER, "")
_UPLOAD_DUPES = ("Check the upload for the same order or lead sent twice, and for conversions that a website tag already counts.", PRACTITIONER, "")
_NEW_ACTION = ("Read the change history for the days just before {day}. Look for a new conversion action, a Secondary action made Primary, "
               "or a count setting changed from One to Every.", PRACTITIONER, "")
_PRIMARY_SWITCH = ("Read the change history for the days just before {day}. Look for this action changing between Primary and Secondary, "
                   "or a campaign changing the goals it uses.", PRACTITIONER, "")
_TEST_VALUE = ("Make a test conversion and read the value the tag sends. A missing or zero value points at the site's code, not at Google Ads.",
               PRACTITIONER, "")
_VALUE_SETTING = ("Open the action's settings and read Value: the same value for each conversion, or a different value for each.",
                  OFFICIAL, "Google Ads Help, About conversion values")
_ASK_LEAD = ("Ask the business whether a second form or call from the same person is a second lead.", PRACTITIONER, "")
_ASK_OUTCOME = ("Ask the business whether this is an outcome it would pay for.", PRACTITIONER, "")

_TOOL = ("Ask whether the booking or form tool changed on or just before {day}: a new version, a new domain or a new confirmation page. "
         "A tool on another domain can lose the tag or the click identifier.", PRACTITIONER, "")

DOWN = {"website": [_TAG, _SITE, _TOOL, _CONSENT, _CLICK_ID], "analytics": [_KEY_EVENT, _GA_DELAY, _SITE, _CONSENT],
        "import": [_UPLOAD, _UPLOAD_IDS, _UPLOAD_PATH, _UPLOAD_LAG], "other": [_END_TO_END]}
UP = {"website": [_WHAT_RECORDS, _FIRES_TWICE, _ORDER_ID, _SITE], "analytics": [_WHAT_RECORDS, _KEY_EVENT, _SITE],
      "import": [_WHAT_RECORDS, _UPLOAD_DUPES, _UPLOAD_IDS], "other": [_WHAT_RECORDS, _END_TO_END]}
_VALUE_BID = ("Ask whether any campaign bids on value (Maximize conversion value or Target ROAS). If one does, a value counted twice "
              "is in what it bids on.", PRACTITIONER, "")

SITUATIONS = {
    "down": lambda family: DOWN.get(family, DOWN["other"]) + [_STATUS, _HISTORY],
    "up": lambda family: UP.get(family, UP["other"]) + [_NEW_ACTION],
    "counting": lambda family: [_PRIMARY_SWITCH, _GOALS],
    "double": lambda family: [_WHAT_RECORDS, _FIRES_TWICE, _GOALS, _VALUE_BID],
    "value": lambda family: [_TEST_VALUE, _VALUE_SETTING, _SITE],
    "lead_count": lambda family: [_ASK_LEAD],
    "outcome": lambda family: [_ASK_OUTCOME, _GOALS],
}


# Who usually makes each check.
YOU = "You, in Google Ads"
DEVELOPER = "The website developer"
TAGS = "Whoever manages Google Tag Manager or GA4"
TOOL = "Whoever owns the booking or form tool"
UPLOADER = "Whoever runs the upload or the CRM"
BUSINESS = "The business"
OWNER_ORDER = [YOU, DEVELOPER, TAGS, TOOL, UPLOADER, BUSINESS]
OWNERS = {_STATUS: YOU, _HISTORY: YOU, _GOALS: YOU, _TAG: TAGS, _SITE: DEVELOPER, _TOOL: TOOL, _CONSENT: DEVELOPER,
          _CLICK_ID: DEVELOPER, _KEY_EVENT: TAGS, _GA_DELAY: YOU, _UPLOAD: UPLOADER, _UPLOAD_IDS: UPLOADER, _UPLOAD_PATH: UPLOADER,
          _UPLOAD_LAG: YOU, _END_TO_END: TOOL, _WHAT_RECORDS: TAGS, _FIRES_TWICE: TAGS, _ORDER_ID: DEVELOPER, _UPLOAD_DUPES: UPLOADER,
          _NEW_ACTION: YOU, _PRIMARY_SWITCH: YOU, _TEST_VALUE: DEVELOPER, _VALUE_SETTING: YOU, _ASK_LEAD: BUSINESS,
          _ASK_OUTCOME: BUSINESS, _VALUE_BID: YOU}


def outside_checks(situation, family="other", day=None):
    """The checks for one finding, as dictionaries. day fills the date into the wording."""
    when = day or "the break"
    return [{"check": item[0].replace("{day}", when), "label": item[1], "source": item[2], "owner": OWNERS.get(item, YOU)}
            for item in SITUATIONS[situation](family)]


def check_line(item):
    return "%s (%s%s)" % (item["check"], item["label"], ": " + item["source"] if item["source"] else "")


def by_owner(pairs):
    """[(check, reference)] -> [(owner, [{"check", "refs"}])], owners in a fixed order, each check once."""
    slots = {}
    for check, ref in pairs:
        slot = slots.setdefault(check["owner"], {}).setdefault(check["check"], {"check": check, "refs": []})
        if ref not in slot["refs"]:
            slot["refs"].append(ref)
    return [(owner, list(slots[owner].values())) for owner in OWNER_ORDER if owner in slots]


def owner_lines(pairs, what):
    """Markdown: the checks grouped under who usually does them, each marked with the items that need it."""
    lines = []
    for owner, items in by_owner(pairs):
        lines += ["**%s**" % owner, ""]
        lines += ["%d. %s For %s%s %s." % (n, check_line(i["check"]), what, "s" if len(i["refs"]) > 1 else "", ", ".join(i["refs"]))
                  for n, i in enumerate(items, start=1)]
        lines.append("")
    return lines


def load(path, what):
    """io.read_report, with a plain message when the file is missing or is not an export."""
    if not path or not os.path.isfile(path):
        raise SystemExit("I can't find the file %s. Check the path to the %s." % (path, what))
    try:
        return io.read_report(path, extra_aliases=ALIASES, extra_numeric=NUMERIC)
    except ValueError as problem:
        raise SystemExit("%s The file is %s, and it should be the %s." % (problem, os.path.basename(path), what))
    except (zipfile.BadZipFile, KeyError, IndexError, UnicodeError, OSError):
        raise SystemExit("I can't read %s. Download the %s again from Google Ads as CSV." % (os.path.basename(path), what))


def clean(value):
    return "" if value is None else str(value).strip()


def optimization(text):
    low = clean(text).lower()
    if "primary" in low or low in ("yes", "true"):
        return "Primary"
    if "secondary" in low or low in ("no", "false"):
        return "Secondary"
    return ""


def status_class(text):
    """recording, not_recording, needs_attention, removed, or unknown."""
    low = clean(text).lower()
    if "removed" in low or "hidden" in low or "deleted" in low:
        return "removed"
    if "needs attention" in low:
        return "needs_attention"
    if any(word in low for word in ("inactive", "no recent", "awaiting", "misconfigured", "unverified", "not recording")):
        return "not_recording"
    if "recording" in low or low == "active":
        return "recording"
    return "unknown"


def count_setting(text):
    low = clean(text).lower()
    if "every" in low or "many" in low:
        return "Every"
    if "one" in low:
        return "One"
    return ""


LEAD_WORDS = ("lead", "contact", "sign-up", "sign up", "signup", "quote", "appointment")
CATEGORY_RULE = ("A purchase action is one whose category contains the word Purchase. A lead action is one whose category contains "
                 "Lead, Contact, Sign-up, Quote or Appointment. A page view action is one whose category is Page view.")


def category_kind(category):
    low = clean(category).lower()
    if "purchase" in low:
        return "purchase"
    if "page view" in low or "pageview" in low:
        return "page_view"
    if any(word in low for word in LEAD_WORDS):
        return "lead"
    return "other"


def source_family(source):
    """website, analytics, import, calls, app or other. Chooses which outside checks apply."""
    low = clean(source).lower()
    if not low:
        return "other"
    if "analytics" in low or "ga4" in low or "firebase" in low:
        return "analytics"
    if "call" in low or "phone" in low:
        return "calls"
    if any(word in low for word in ("import", "upload", "offline", "crm", "data manager")):
        return "import"
    if "web" in low or "tag" in low:
        return "website"
    if "app" in low:
        return "app"
    return "other"


SETTINGS = ("optimization", "source", "category", "status", "count")


def read_actions(path):
    """The conversion actions list as clean dictionaries. Removed actions are returned apart.

    A row with a name but every setting blank is a heading, such as a goal
    name above its actions. It is left out and counted, because it can carry
    the goal's total and would count those conversions twice.
    """
    meta, rows = load(path, "conversions summary")
    io.require(meta, ["conversion_action"], "conversions summary", labels=LABELS)
    has = meta["columns"]
    volume_key = "all_conv" if "all_conv" in has else ("conversions" if "conversions" in has else None)
    value_key = "all_conv_value" if "all_conv_value" in has else ("conv_value" if "conv_value" in has else None)
    present = [key for key in SETTINGS if key in has]
    actions, removed, blank, headings = [], [], 0, []
    for row in rows:
        name = clean(row.get("conversion_action"))
        if not name:
            blank += 1
            continue
        if present and not any(clean(row.get(key)) for key in present):
            headings.append(name)
            continue
        setting = clean(row.get("value_setting"))
        value = (row.get(value_key) or 0.0) if value_key else None
        if value is None and setting and io.to_number(setting) is not None:
            # A Value column that holds an amount, not a setting.
            value, setting = io.to_number(setting), ""
        item = {
            "name": name, "optimization": optimization(row.get("optimization")), "source": clean(row.get("source")),
            "category": clean(row.get("category")), "status": clean(row.get("status")), "count": count_setting(row.get("count")),
            "click_window": clean(row.get("click_window")), "view_window": clean(row.get("view_window")),
            "engaged_window": clean(row.get("engaged_window")), "attribution_model": clean(row.get("attribution_model")),
            "value_setting": setting, "repeat_rate": row.get("repeat_rate"),
            "volume": (row.get(volume_key) or 0.0) if volume_key else None,
            "conversions": (row.get("conversions") or 0.0) if "conversions" in has else None,
            "value": value,
        }
        item["status_class"] = status_class(item["status"])
        item["kind"] = category_kind(item["category"])
        item["family"] = source_family(item["source"])
        (removed if item["status_class"] == "removed" else actions).append(item)
    info = {"volume_key": volume_key, "value_key": value_key, "removed": removed, "blank_rows": blank, "headings": headings,
            "volume_label": {"all_conv": "All conv.", "conversions": "Conversions"}.get(volume_key),
            "value_label": {"all_conv_value": "All conv. value", "conv_value": "Conv. value"}.get(value_key)}
    return meta, actions, info


def title_range(meta):
    """The date range Google writes above the header, as (first day, last day), or None."""
    for row in meta.get("title_rows", []):
        for mark in (" - ", " – ", " — ", " to "):
            if mark in row:
                first, _, last = row.partition(mark)
                start, end = dates.parse_day(first.strip().strip('"')), dates.parse_day(last.strip().strip('"'))
                if start and end and end >= start:
                    return start, end
    return None


def file_totals(path, meta, keys):
    """The file's own Total rows, added up by label: {label: {key: sum}}.

    A report segmented by Day, or by Day and Conversion action, repeats each
    Total row once per segment. Adding the rows that share a label gives the
    figure for the whole file in every layout. Also returns the labels of rows
    that start with the word Total but have no colon: the reader treats them
    as total rows, and they may be a campaign or an action with that name.
    """
    headers = {key: meta["columns"][key] for key in keys if key in meta["columns"]}
    if not headers:
        return {}, []
    if str(path).lower().endswith(".xlsx"):
        grid = io._grid_from_xlsx(path)
    else:
        with open(path, "rb") as handle:
            grid = io._grid_from_text(io._decode(handle.read()))
    wanted, positions, sums, doubtful = set(meta["columns"].values()), None, {}, []
    for raw in grid:
        cells = [str(c).strip() for c in raw]
        if positions is None:
            if wanted <= set(cells):
                positions = {key: cells.index(header) for key, header in headers.items()}
            continue
        label = next((c for c in cells[:3] if c.lower().startswith("total")), None)
        if not label:
            continue
        if not label.lower().startswith("total:"):
            doubtful.append(label)
        slot = sums.setdefault(label, {})
        for key, position in positions.items():
            number = io.to_number(cells[position]) if position < len(cells) else None
            if number is not None:
                slot[key] = slot.get(key, 0.0) + number
    return sums, sorted(set(doubtful))


def reconcile(sums, key, rows_total, row_count):
    """Compare the rows with the file's own total for one column.

    Each row is rounded to two decimals, so a difference up to half a cent per
    row is rounding. The label that matches the rows is used; when none does,
    Total: Account is shown with its difference.
    """
    candidates = [(label, values[key]) for label, values in sums.items() if key in values]
    if not candidates:
        return None
    tolerance = max(0.01, 0.005 * row_count)
    label, total = min(candidates, key=lambda c: (abs(c[1] - rows_total) > tolerance, "account" not in c[0].lower(), abs(c[1] - rows_total)))
    account = next((value for name, value in candidates if "account" in name.lower()), None)
    return {"label": label, "file_total": total, "rows_total": rows_total, "difference": round(rows_total - total, 2),
            "tolerance": round(tolerance, 2), "matches": abs(rows_total - total) <= tolerance,
            "account_total": account, "part_of_account": account is not None and account - rows_total > tolerance}


def reconcile_line(result, name):
    if not result:
        return "The file has no total row for %s, so the rows could not be checked against one." % name
    if result["matches"]:
        line = "%s: the rows add up to %s and the file's own \"%s\" row says %s." % (
            name, "{:,.2f}".format(result["rows_total"]), result["label"], "{:,.2f}".format(result["file_total"]))
    else:
        line = "%s: the rows add up to %s, but the file's own \"%s\" row says %s. The difference is %s, more than rounding (%s) explains. Download the report again and check its filters." % (
            name, "{:,.2f}".format(result["rows_total"]), result["label"], "{:,.2f}".format(result["file_total"]),
            "{:,.2f}".format(result["difference"]), "{:,.2f}".format(result["tolerance"]))
    if result["part_of_account"] and result["matches"]:
        line += " The \"Total: Account\" row says %s, so this report holds part of the account. Every share below is a share of this report." % "{:,.2f}".format(result["account_total"])
    return line


def two(value):
    return "n/a" if value is None else "{:,.2f}".format(value)
