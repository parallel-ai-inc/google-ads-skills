"""Dates as Google Ads exports write them."""
import calendar
import datetime as dt
import re

_FORMATS = ("%Y-%m-%d", "%b %d, %Y", "%B %d, %Y", "%m/%d/%Y", "%d/%m/%Y", "%d %b %Y", "%Y/%m/%d", "%m/%d/%y")


def parse_day(text):
    """'2026-11-12', 'Nov 12, 2026' or 'Nov 2, 2026, 4:41:55 PM' -> date, else None."""
    if not text:
        return None
    text = str(text).strip()
    stamp = re.match(r"^([A-Za-z]{3,9} \d{1,2}, \d{4})", text)
    candidates = [stamp.group(1)] if stamp else []
    candidates += [text, text.split(" ")[0], text.split("T")[0]]
    for candidate in candidates:
        for pattern in _FORMATS:
            try:
                return dt.datetime.strptime(candidate, pattern).date()
            except ValueError:
                continue
    return None


def days_in_month(day):
    return calendar.monthrange(day.year, day.month)[1]


def month_key(day):
    return "%04d-%02d" % (day.year, day.month)
