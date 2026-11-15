"""Numbers and wording shared by review.py and plan.py.

Every threshold here comes from a file in references/ or from the account's own
numbers. Each one carries the sentence that explains it, so the scripts can print
it in plain words.
"""
import datetime as dt
import math

SB = "references/smart-bidding.md"
LP = "references/learning-phase.md"
SC = "references/scaling.md"
TCPA = "references/tcpa-framework.md"
TROAS = "references/troas-framework.md"
IS = "references/impression-share-and-editor.md"

# Official, smart-bidding.md: evaluate over periods with at least 30 conversions (50 for Target ROAS).
NEEDED_DEFAULT = 30
NEEDED_TROAS = 50
# Official, smart-bidding.md: Target ROAS needs at least 15 conversions in the past 30 days for most campaign types.
TROAS_MIN_30D = 15
# Official, smart-bidding.md and scaling.md: since this date budget limited Target CPA and Target ROAS campaigns bid toward their target.
AUG17 = dt.date(2026, 8, 17)
# Official, scaling.md: a month bills at most about 30.4 times the average daily budget.
MONTHLY_LIMIT_FACTOR = 30.4
# Official, learning-phase.md (Google's Demand Gen guide): bid changes of 5-10% a week, no more than 15%.
DEMAND_GEN_STEPS = (0.05, 0.10)
DEMAND_GEN_MAX = 0.15
DEMAND_GEN_DAYS = 7
# Official, learning-phase.md: Performance Max wants 1-2 weeks or one conversion cycle after a significant change.
PMAX_DAYS = 14
# Practitioner rule, tcpa-framework.md: evaluate a change over 2 full conversion cycles whenever possible.
CYCLES_TO_JUDGE = 2
# Practitioner rule: a lost impression share of 10% or more counts as a limit. Google writes small shares as "< 10%".
SHARE_CUT = 10.0
# Statistics: zero conversions after spending 3 times the reference cost per conversion happens about 5% of the time by chance.
PAUSE_MULTIPLE = 3
# An assumption, not a Google rule: the conversion cycle used when the person gives none. It is printed as assumed.
DEFAULT_CYCLE_DAYS = 7
# A plain Target ROAS above this is read as a percent written without its sign: 400 means 400%.
ROAS_RATIO_MAX = 25

LABEL = {
    "tcpa": "Target CPA", "troas": "Target ROAS", "max_conv": "Maximize conversions", "max_value": "Maximize conversion value",
    "manual": "Manual CPC", "manual_ecpc": "Enhanced CPC (now runs as Manual CPC)", "clicks": "Maximize clicks",
    "tis": "Target impression share", "other": "Other",
}
CPA_FAMILIES = ("tcpa", "max_conv", "manual", "manual_ecpc", "clicks", "other")
VALUE_FAMILIES = ("troas", "max_value")


def family(text, has_cpa_target=False, has_roas_target=False):
    """Bid strategy type as Google writes it -> one family name."""
    t = (text or "").lower()
    if "roas" in t or "return on ad spend" in t:
        return "troas"
    if "cpa" in t or "cost per action" in t or "cost per acquisition" in t:
        return "tcpa"
    if "conversion value" in t:
        return "troas" if has_roas_target else "max_value"
    if "maximize conversions" in t or "maximise conversions" in t:
        return "tcpa" if has_cpa_target else "max_conv"
    if "enhanced" in t:
        return "manual_ecpc"
    if "manual" in t:
        return "manual"
    if "click" in t:
        return "clicks"
    if "impression share" in t:
        return "tis"
    return "other"


def needed(fam):
    return NEEDED_TROAS if fam == "troas" else NEEDED_DEFAULT


def band(conversions):
    """How far chance alone moves a cost per conversion built on this many conversions: 1 / sqrt(n)."""
    return 1 / math.sqrt(conversions) if conversions and conversions > 0 else None


def money(value):
    return "n/a" if value is None else "{:,.2f}".format(value)


def roas_text(value):
    """4.0 -> '4.00 (400%)'."""
    return "n/a" if value is None else "{:,.2f} ({:,.0f}%)".format(value, value * 100)


def pct(value, digits=1, signed=False):
    if value is None:
        return "n/a"
    text = ("{:.%df}%%" % digits).format(value * 100)
    return ("+" + text) if signed and value > 0 else text


def r2(value):
    return round(value, 2) if isinstance(value, (int, float)) else value
