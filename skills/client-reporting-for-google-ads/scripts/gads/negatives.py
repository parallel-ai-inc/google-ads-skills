"""Test negative keywords against searches, using Google's matching rules.

Rules applied (Google Ads Help, "About negative keywords"):
- Negative exact blocks a search made of the same words in the same order,
  with nothing added.
- Negative phrase blocks a search that contains the same words in the same
  order, with other words allowed before or after.
- Negative broad blocks a search that contains every word of the negative, in
  any order.
- Negatives do not match close variants. "flowers" blocks "red flowers" but
  not "red flower". Singular, plural and synonyms each need their own negative.

One limit of this test: Google says negative keywords also account for casing
and misspellings. Casing is handled here. Misspellings are not, so a negative
can block slightly more in the account than this test shows.
"""
from .metrics import tokens

MATCH_TYPES = ("exact", "phrase", "broad")


def blocks(negative_text, match_type, search):
    """True when this negative would stop this search from showing an ad."""
    neg, words = tokens(negative_text), tokens(search)
    if not neg or not words:
        return False
    match_type = match_type.lower()
    if match_type == "exact":
        return neg == words
    if match_type == "phrase":
        span = len(neg)
        return any(words[i:i + span] == neg for i in range(len(words) - span + 1))
    if match_type == "broad":
        return all(word in words for word in neg)
    raise ValueError("Unknown match type: %s" % match_type)


def in_scope(negative, row):
    """A campaign negative reaches only that campaign, and so on."""
    level = negative.get("level", "campaign")
    if level == "account":
        return True
    if negative.get("campaign") and negative["campaign"] != row.get("campaign"):
        return False
    if level == "ad_group" and negative.get("ad_group") and negative["ad_group"] != row.get("ad_group"):
        return False
    return True


def list_form(text, match_type):
    """How the negative is typed into a negative keyword list: word, "a phrase", [exact]."""
    match_type = match_type.lower()
    if match_type == "exact":
        return "[%s]" % text
    if match_type == "phrase":
        return '"%s"' % text
    return text


def symbol_form(text, match_type):
    """How the negative is written in a keyword list: -word, -"a phrase", -[exact]."""
    match_type = match_type.lower()
    if match_type == "exact":
        return "-[%s]" % text
    if match_type == "phrase":
        return '-"%s"' % text
    return "-%s" % text
