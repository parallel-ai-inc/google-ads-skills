"""Arithmetic the skills rely on. The model never does this math itself."""
import math
import re

WORD = re.compile(r"[a-z0-9]+(?:['&][a-z0-9]+)*")


def div(a, b):
    """a / b, or None when it has no meaning."""
    if a is None or b in (None, 0):
        return None
    return a / b


def tokens(text):
    """Lowercase words. Punctuation is dropped, as Google ignores most of it."""
    return WORD.findall((text or "").lower())


def ngrams(text, size):
    words = tokens(text)
    return [" ".join(words[i:i + size]) for i in range(len(words) - size + 1)]


def total(rows, key):
    return sum((row.get(key) or 0) for row in rows)


def money(value, currency=""):
    if value is None:
        return "n/a"
    return ("%s " % currency if currency else "") + "{:,.2f}".format(value)


def pct(value, digits=1):
    """0.123 -> '12.3%'."""
    if value is None:
        return "n/a"
    text = ("{:.%df}%%" % digits).format(value * 100)
    # A tiny negative rounds to "-0.0%". Show it as zero.
    return text[1:] if text.startswith("-") and float(text[1:-1]) == 0 else text


def change(new, old):
    """Relative change, or None when the old value is zero or missing."""
    if new is None or old in (None, 0):
        return None
    return (new - old) / old


def log_shares(parts_new, parts_old):
    """Split a change in a product a*b*c into the share driven by each factor.

    conversions = impressions * CTR * conversion rate, so
    ln(new/old) of conversions equals the sum of ln(new/old) of each factor.
    Returns {factor: share of the total log change}, or None when any value is
    zero or missing (the split has no meaning then).
    """
    logs = {}
    for name in parts_new:
        new, old = parts_new[name], parts_old.get(name)
        if not new or not old or new <= 0 or old <= 0:
            return None
        logs[name] = math.log(new / old)
    whole = sum(logs.values())
    if abs(whole) < 1e-12:
        return {name: 0.0 for name in logs}
    return {name: value / whole for name, value in logs.items()}
