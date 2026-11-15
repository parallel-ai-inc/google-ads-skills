"""Find every number in report text and trace it to the numbers file.

Shared by fact_check.py and write_report.py. A number is written in two ways:

- as an id in braces, {acct.cost.cur}. The id must exist, and the write step
  puts in the exact figure.
- typed as text, 12.4% or 1,234.56 or October 1, 2026. It must match a number
  in the numbers file within the rounding it was written with.

Either way, the words around the number are read too: the measure it names
(cost, conversions...), the campaign, the comparison (previous period, last
year, target) and the direction (rose, fell). A number that matches only a
different measure, campaign or comparison is refused, and so is a direction
that contradicts the data.

Standard library only.
"""
import datetime as dt
import re

MONTH_NUMBER = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12}
MON = r"(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
REF = re.compile(r"\{([A-Za-z0-9_.]+)\}")
ISO = re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b")
SLASH = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4}|\d{2})\b")
RANGE = re.compile(r"\b" + MON + r"\.?\s+(\d{1,2})(?:st|nd|rd|th)?\s*(?:-|\u2013|\u2014|to|through|until)\s*(\d{1,2})(?:st|nd|rd|th)?\b(?:,?\s+(\d{4})\b)?", re.I)
MDY = re.compile(r"\b" + MON + r"\.?\s+(\d{1,2})(?:st|nd|rd|th)?\b(?:,?\s+(\d{4})\b)?", re.I)
DMY = re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+" + MON + r"\b\.?(?:,?\s+(\d{4})\b)?", re.I)
MY = re.compile(r"\b" + MON + r"\.?,?\s+(\d{4})\b", re.I)
NUMBER = re.compile(r"""
    (?<![\w.,/])
    (?P<sign>[+\-\u2212])?
    (?P<cur>[$\u20ac\u00a3\u00a5]\s?)?
    (?P<sign2>[+\-\u2212])?
    (?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)
    (?P<suffix>%|x|k|K|\s?(?:percentage\ points?|percent|per\ cent|pts?|pp|points?|million|thousand|m)\b)?
    (?![\w/])
""", re.X)
WORD_NUMBERS = re.compile(r"\b(doubled|tripled|quadrupled|halved|twice|double|triple)\b", re.I)
# Abbreviations whose full stop does not end a sentence.
ABBREVIATIONS = re.compile(r"\b(Avg|Conv|Impr|vs|approx|No|e\.g|i\.e|etc)\.", re.I)
BOUNDARY = re.compile(r"[,;:()]|\b(?:and|but|while|whereas|although|though)\b", re.I)
APPROX = re.compile(r"(about|around|roughly|approximately|approx\.?|nearly|almost|close to|just over|just under|over|more than|above|exceeding|under|less than|fewer than|below|up to|some|~)\s*$", re.I)
UP = re.compile(r"\b(rose|rise|rises|rising|risen|up|increased?|increases|increasing|grew|grow|grown|growth|growing|higher|more|gained?|gains|climbed|climbs?|jumped|jumps?|above|ahead|over)\b", re.I)
DOWN = re.compile(r"\b(fell|fall|falls|falling|fallen|down|decreased?|decreases|declined?|declines|declining|dropped|drops?|lower|less|fewer|shrank|shrunk|slipped|slips?|cut|reduced|reduction|below|behind|under)\b", re.I)

METRIC_PHRASES = sorted([
    ("conv. value / cost", "roas"), ("conversion value / cost", "roas"), ("return on ad spend", "roas"), ("roas", "roas"), ("value / cost", "roas"),
    ("cost / conv.", "cpa"), ("cost/conv.", "cpa"), ("cost per conversion", "cpa"), ("cost per lead", "cpa"), ("cost per acquisition", "cpa"),
    ("cost per sale", "cpa"), ("cpa", "cpa"), ("cpl", "cpa"),
    ("cost per click", "cpc"), ("avg. cpc", "cpc"), ("cpc", "cpc"),
    ("click through rate", "ctr"), ("click-through rate", "ctr"), ("ctr", "ctr"),
    ("conversion rate", "cvr"), ("conv. rate", "cvr"),
    ("conversion value", "value"), ("conv. value", "value"), ("revenue", "value"), ("sales value", "value"),
    ("conversions", "conv"), ("conversion", "conv"), ("conv.", "conv"), ("leads", "conv"), ("lead", "conv"), ("sales", "conv"),
    ("purchases", "conv"), ("bookings", "conv"), ("enquiries", "conv"), ("inquiries", "conv"), ("calls", "conv"), ("orders", "conv"),
    ("impressions", "impr"), ("impr.", "impr"), ("clicks", "clicks"), ("click", "clicks"),
    ("spend", "cost"), ("spent", "cost"), ("spending", "cost"), ("cost", "cost"), ("costs", "cost"), ("investment", "cost"), ("budget", "cost"),
    ("per day", "per_day"), ("a day", "per_day"), ("daily", "per_day"),
    ("changes", "changes"), ("edits", "changes"), ("campaigns", "campaigns"), ("days", "days"),
], key=lambda pair: -len(pair[0]))
COMP_PHRASES = sorted([
    ("same period last year", "ly"), ("same month last year", "ly"), ("same week last year", "ly"), ("same quarter last year", "ly"),
    ("last year", "ly"), ("a year ago", "ly"), ("year over year", "ly"), ("year-over-year", "ly"), ("year on year", "ly"),
    ("previous year", "ly"), ("prior year", "ly"), ("yoy", "ly"),
    ("previous", "prev"), ("prior", "prev"), ("the week before", "prev"), ("the month before", "prev"), ("the quarter before", "prev"),
    ("week over week", "prev"), ("month over month", "prev"), ("quarter over quarter", "prev"), ("wow", "prev"), ("mom", "prev"), ("qoq", "prev"),
    ("target", "target"), ("goal", "target"), ("plan", "target"), ("planned", "target"), ("budgeted", "target"),
], key=lambda pair: -len(pair[0]))
# Bid strategy names read as names, not as a measure or a target comparison.
BID_STRATEGIES = re.compile(r"\b(target cpa|target roas|target impression share|maximi[sz]e conversions?(?: value)?|maximi[sz]e clicks|manual cpc|enhanced cpc)\b", re.I)
ACCOUNT_WORDS = re.compile(r"\b(account|overall|in total|all campaigns)\b", re.I)
NON_BRAND_WORDS = re.compile(r"\b(non-brand|non brand|nonbrand|without brand|excluding brand|outside brand)\b", re.I)
# Parts of a campaign name too generic to stand for the campaign on their own.
GENERIC_PARTS = {"search", "display", "video", "shopping", "pmax", "performance max", "demand gen", "campaign", "google", "ads", "test", "new", "old"}

CHANGE_COMPS = {"chg_prev", "chg_ly", "delta_prev", "delta_ly", "pp_prev", "pp_ly", "diff", "diff_pct"}
COMP_FAMILY = {"ly": {"ly", "chg_ly", "delta_ly", "pp_ly"}, "prev": {"prev", "chg_prev", "delta_prev", "pp_prev", "share_chg_prev"},
               "target": {"target", "diff", "diff_pct"}}
NEUTRAL_COMPS = {"cur", ""}
METRIC_FAMILY = {"cost_per_day": {"cost"}, "conv_per_day": {"conv"}}
PLAIN_KINDS = {"money", "int", "conv", "ratio", "plain"}

STATUS_TEXT = {
    "traced": "Traced",
    "not_traced": "No figure in the data supports it",
    "wrong_value": "Contradicted by the data",
    "wrong_metric": "Matches a different measure",
    "wrong_scope": "Matches a different campaign",
    "wrong_comparison": "Matches a different comparison",
    "contradicted": "Contradicted by the data: wrong direction",
    "rounded": "Matches only when rounded",
    "points_as_percent": "A change in points written as a percent",
    "unknown_id": "Unknown id",
    "words": "Written in words, so not checked",
}


# Display ---------------------------------------------------------------

def long_date(iso):
    day = dt.date.fromisoformat(iso)
    return "%s %d, %d" % (day.strftime("%B"), day.day, day.year)


def display(entry, signed=False, absolute=False):
    """How a number is written in the report."""
    kind, value = entry["kind"], entry["value"]
    if kind == "date":
        return long_date(value)
    if kind == "plain":
        return entry.get("raw") or "{:,}".format(value)
    shown = abs(value) if (signed or absolute) else value
    if kind in ("money", "conv", "ratio"):
        text = "{:,.2f}".format(shown)
    elif kind == "int":
        text = "{:,.0f}".format(shown)
    elif kind == "pct":
        text = ("{:,.%df}%%" % entry.get("digits", 1)).format(shown * 100)
    elif kind == "pp":
        text = "{:.2f} percentage points".format(shown)
    else:
        text = str(shown)
    if signed:
        text = ("+" if value > 0 else "-" if value < 0 else "") + text
    return text


def is_change(entry):
    return entry.get("comp") in CHANGE_COMPS


# Splitting text --------------------------------------------------------

def units_from_text(text):
    """Split a Markdown or plain text report into units: headings, bullets,
    table rows and paragraphs (wrapped lines joined)."""
    units, paragraph = [], []

    def flush():
        if paragraph:
            units.append(" ".join(paragraph))
            del paragraph[:]

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        if re.match(r"^\|?\s*:?-{3,}", line):
            continue
        marker = re.match(r"^(#{1,6}\s+|[-*+]\s+|\d{1,3}[.)]\s+|>\s*)", line)
        if marker or line.startswith("|"):
            flush()
            body = line[marker.end():] if marker else line
            units.append(body)
            continue
        paragraph.append(line)
    flush()
    return [re.sub(r"(\*\*|__|`)", "", u).strip() for u in units if u.strip()]


def sentences(text):
    """(start, end) spans of the sentences in one unit."""
    guarded = ABBREVIATIONS.sub(lambda m: m.group(0)[:-1] + "\u2024", text)
    spans, start = [], 0
    for match in re.finditer(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(\[{$\u20ac\u00a3])", guarded):
        spans.append((start, match.start()))
        start = match.end()
    spans.append((start, len(text)))
    return [(a, b) for a, b in spans if text[a:b].strip()]


def _mask(text, spans):
    chars = list(text)
    for a, b in spans:
        for i in range(a, b):
            chars[i] = " "
    return "".join(chars)


def _year(text):
    if not text:
        return None
    year = int(text)
    return year + 2000 if year < 100 else year


def tokens(text, names=()):
    """Every number in one sentence: ids, dates, numbers and number words."""
    found = []
    for match in REF.finditer(text):
        found.append({"start": match.start(), "end": match.end(), "raw": match.group(0), "kind": "ref", "id": match.group(1)})
    work = _mask(text, [(t["start"], t["end"]) for t in found])
    lowered = work.lower()
    hidden = []
    for name in names:
        if name and re.search(r"\d", name):
            for m in re.finditer(re.escape(name.lower()), lowered):
                hidden.append((m.start(), m.end()))
    work = _mask(work, hidden)

    def take(pattern, build):
        nonlocal work
        spans = []
        for match in pattern.finditer(work):
            for item in build(match):
                item.update({"start": match.start(), "end": match.end(), "raw": match.group(0)})
                found.append(item)
            spans.append((match.start(), match.end()))
        work = _mask(work, spans)

    take(ISO, lambda m: [{"kind": "date", "y": int(m.group(1)), "m": int(m.group(2)), "d": int(m.group(3))}])
    take(SLASH, lambda m: [{"kind": "date", "y": _year(m.group(3)), "m": int(m.group(1)), "d": int(m.group(2)), "alt": (int(m.group(2)), int(m.group(1)))}])
    take(RANGE, lambda m: [{"kind": "date", "y": _year(m.group(4)), "m": MONTH_NUMBER[m.group(1)[:3].lower()], "d": int(m.group(2))},
                           {"kind": "date", "y": _year(m.group(4)), "m": MONTH_NUMBER[m.group(1)[:3].lower()], "d": int(m.group(3))}])
    take(MDY, lambda m: [{"kind": "date", "y": _year(m.group(3)), "m": MONTH_NUMBER[m.group(1)[:3].lower()], "d": int(m.group(2))}])
    take(DMY, lambda m: [{"kind": "date", "y": _year(m.group(3)), "m": MONTH_NUMBER[m.group(2)[:3].lower()], "d": int(m.group(1))}])
    take(MY, lambda m: [{"kind": "month", "y": int(m.group(2)), "m": MONTH_NUMBER[m.group(1)[:3].lower()]}])

    for match in NUMBER.finditer(work):
        raw_num = match.group("num")
        suffix = (match.group("suffix") or "").strip().lower()
        sign = match.group("sign") or match.group("sign2")
        value = float(raw_num.replace(",", ""))
        decimals = len(raw_num.split(".")[1]) if "." in raw_num else 0
        trailing = 0 if decimals else len(raw_num.replace(",", "")) - len(raw_num.replace(",", "").rstrip("0"))
        mult = 1.0
        kind = "num"
        if suffix == "%" or suffix.startswith("percent") and "point" not in suffix or suffix == "per cent":
            kind = "pct"
        elif "point" in suffix or suffix in ("pts", "pt", "pp"):
            kind = "pp"
        elif suffix == "x":
            kind = "ratio"
        elif suffix in ("k", "thousand"):
            mult = 1000.0
        elif suffix in ("m", "million"):
            mult = 1000000.0
        if kind == "num" and not sign and not match.group("cur") and not suffix and "," not in raw_num and decimals == 0 and 1990 <= value <= 2099:
            kind = "year"
        signed_value = -value if sign in ("-", "\u2212") else value
        found.append({"start": match.start(), "end": match.end(), "raw": match.group(0).strip(), "kind": kind, "value": signed_value * mult,
                      "decimals": decimals, "trailing": trailing, "mult": mult, "signed": bool(sign)})
    for match in WORD_NUMBERS.finditer(work):
        found.append({"start": match.start(), "end": match.end(), "raw": match.group(0), "kind": "words"})
    return sorted(found, key=lambda t: t["start"])


# Reading the words around a number ---------------------------------------

def _phrases(text, table):
    lowered, found = " " + text.lower() + " ", set()
    for phrase, name in table:
        pattern = r"(?<![\w])" + re.escape(phrase) + r"(?![\w])"
        if re.search(pattern, lowered):
            found.add(name)
            lowered = re.sub(pattern, " ", lowered)
    return found


def campaign_matchers(campaigns):
    """[(regex, scope id)] for each campaign name and each distinctive part of it."""
    parts = {}
    for scope_id, name in campaigns:
        pieces = {name.strip().lower()}
        pieces.update(p.strip().lower() for p in re.split(r"[|:\-/>]", name) if len(p.strip()) >= 4)
        for piece in pieces:
            if piece and piece not in GENERIC_PARTS:
                parts.setdefault(piece, set()).add(scope_id)
    matchers = []
    for piece, owners in sorted(parts.items(), key=lambda kv: -len(kv[0])):
        if len(owners) == 1:
            matchers.append((re.compile(r"(?<![\w])" + re.escape(piece) + r"(?![\w])", re.I), next(iter(owners))))
    return matchers


def mentions(text, matchers):
    """[(end position, scope id)] of every scope named in the text."""
    found, rest = [], text
    for pattern in (NON_BRAND_WORDS,):
        for m in pattern.finditer(rest):
            found.append((m.end(), "nb"))
        rest = pattern.sub(lambda m: " " * len(m.group(0)), rest)
    for pattern, scope_id in matchers:
        for m in pattern.finditer(rest):
            found.append((m.end(), scope_id))
        rest = pattern.sub(lambda m: " " * len(m.group(0)), rest)
    for m in ACCOUNT_WORDS.finditer(rest):
        found.append((m.end(), "acct"))
    return found


def direction(text):
    up, down = bool(UP.search(text)), bool(DOWN.search(text))
    if up and not down:
        return "up"
    if down and not up:
        return "down"
    return None


def context(sentence, token, prev_end, next_start, matchers):
    left = sentence[prev_end:token["start"]]
    right = sentence[token["end"]:next_start]
    cuts = list(BOUNDARY.finditer(left))
    left = left[cuts[-1].end():] if cuts else left
    cut = BOUNDARY.search(right)
    right = right[:cut.start()] if cut else right
    approx = APPROX.search(left)
    approx_word = approx.group(1).lower() if approx else None
    if approx:
        left = left[:approx.start()]
    window = left + " " + right
    # The words before a number usually name it ("cost rose 12%"); the words after it
    # only when nothing comes before ("12% more conversions").
    metrics = _phrases(left, METRIC_PHRASES) or _phrases(right, METRIC_PHRASES) or _phrases(sentence, METRIC_PHRASES)
    scopes = {scope for _, scope in mentions(window, matchers)}
    if not scopes:
        before = mentions(sentence[:token["start"]], matchers)
        scopes = {max(before)[1]} if before else set()
    return {"metrics": metrics, "scopes": scopes, "comps": _phrases(window, COMP_PHRASES),
            "direction": direction(left) or direction(right), "approx": approx_word}


# Matching ----------------------------------------------------------------

def _unit(token):
    if token["decimals"]:
        return 10.0 ** -token["decimals"] * token["mult"]
    return 10.0 ** max(token["trailing"], 0) * token["mult"]


def _compare(token, value, approx):
    """'exact', 'rounded' or None for one typed number against one value."""
    typed = token["value"]
    tol = 0.5 * 10.0 ** -token["decimals"] * token["mult"] + 1e-9
    if abs(value - typed) <= tol:
        return "exact"
    unit = _unit(token)
    if approx in ("about", "around", "roughly", "approximately", "approx", "approx.", "some", "~"):
        return "exact" if abs(value - typed) <= unit / 2 + 1e-9 else None
    if approx in ("over", "more than", "above", "exceeding"):
        return "exact" if value > typed else None
    if approx in ("under", "less than", "fewer than", "below"):
        return "exact" if value < typed else None
    if approx == "up to":
        return "exact" if value <= typed + tol else None
    if approx in ("nearly", "almost", "just under"):
        return "exact" if typed - unit <= value < typed + tol else None
    if approx == "just over":
        return "exact" if typed - tol < value <= typed + unit else None
    if token["trailing"] and abs(value - typed) <= unit / 2:
        return "rounded"
    return None


def value_match(token, entry, approx):
    kind, ekind = token["kind"], entry["kind"]
    if ekind == "date":
        return None
    value = entry["value"]
    if kind == "pct":
        if ekind == "pct":
            value = value * 100
        elif ekind == "ratio" and entry.get("metric") == "roas":
            value = value * 100
        else:
            return None
    elif kind == "pp":
        if ekind != "pp":
            return None
    elif kind == "ratio":
        if ekind != "ratio":
            return None
    elif kind == "num":
        if ekind not in PLAIN_KINDS:
            return None
    else:
        return None
    if is_change(entry) and not token["signed"]:
        value = abs(value)
    return _compare(token, value, approx)


def date_match(token, entry):
    if entry["kind"] != "date":
        return False
    day = dt.date.fromisoformat(entry["value"])
    if token["kind"] == "month":
        return day.month == token["m"] and (token["y"] is None or day.year == token["y"])
    if token["kind"] == "year":
        return day.year == int(token["value"])
    options = [(token["m"], token["d"])] + ([token["alt"]] if token.get("alt") else [])
    return any(day.month == m and day.day == d for m, d in options) and (token["y"] is None or day.year == token["y"])


def fit(entry, ctx, token_signed=False):
    """Which context checks one candidate passes."""
    metric = entry.get("metric", "")
    metrics = ctx["metrics"]
    if "per_day" in metrics and metric and not metric.endswith("per_day"):
        metric_ok = False
    else:
        allowed = {metric} | METRIC_FAMILY.get(metric, set())
        metric_ok = not metric or not (metrics - {"per_day"}) or bool(allowed & metrics)
    scope = entry.get("scope_id", "")
    scope_ok = not scope or not ctx["scopes"] or scope in ctx["scopes"]
    comp = entry.get("comp", "")
    if ctx["comps"] and comp not in NEUTRAL_COMPS:
        comp_ok = any(comp in COMP_FAMILY[c] for c in ctx["comps"])
    else:
        comp_ok = True
    dir_ok = True
    if is_change(entry) and ctx["direction"] and not token_signed and entry["value"] != 0:
        dir_ok = (entry["value"] > 0) == (ctx["direction"] == "up")
    return {"metric": metric_ok, "scope": scope_ok, "comparison": comp_ok, "direction": dir_ok}


FAIL_STATUS = (("scope", "wrong_scope"), ("comparison", "wrong_comparison"), ("metric", "wrong_metric"), ("direction", "contradicted"))


def _verdict(entry_id, entry, checks, typed=False):
    if typed and sum(1 for ok in checks.values() if not ok) > 1:
        # A typed number that misses on two counts only shares its value by chance.
        return "not_traced"
    for key, status in FAIL_STATUS:
        if not checks[key]:
            return status
    return "traced"


def _reason(status, entry_id, entry, ctx):
    shown = display(entry, signed=is_change(entry))
    if status == "contradicted":
        return "%s is %s, so it went %s, but the sentence says it went %s." % (entry["label"], shown, "up" if entry["value"] > 0 else "down", ctx["direction"])
    if status in ("wrong_scope", "wrong_comparison", "wrong_metric"):
        what = {"wrong_scope": "campaign", "wrong_comparison": "comparison", "wrong_metric": "measure"}[status]
        return "This value matches %s (%s, id %s). That is a different %s from the one the sentence names." % (entry["label"], shown, entry_id, what)
    if status == "rounded":
        return "%s is %s. Write the exact figure, or say 'about'." % (entry["label"], shown)
    return ""


def check_token(token, ctx, numbers):
    """Trace one token. Returns a result dict."""
    result = {"raw": token["raw"], "kind": token["kind"], "status": "not_traced", "id": "", "label": "", "value": "", "reason": ""}
    if token["kind"] == "words":
        result["reason"] = "A number written in words cannot be checked. Write it as a figure."
        result["status"] = "words"
        return result
    if token["kind"] == "ref":
        entry_id, entry, _ = resolve(token["id"], numbers)
        if not entry:
            result.update(status="unknown_id", reason="There is no number with the id %s in the numbers file." % token["id"])
            return result
        # The id already fixes the measure, the campaign and the period. Only the direction
        # the sentence gives it can be wrong.
        status = "traced" if fit(entry, ctx)["direction"] else "contradicted"
        if entry["kind"] == "date":
            result["kind"] = "date"
        result.update(status=status, id=entry_id, label=entry["label"], value=display(entry, signed=is_change(entry)),
                      reason=_reason(status, entry_id, entry, ctx) if status != "traced" else "")
        return result
    if token["kind"] in ("date", "month", "year"):
        hits = sorted(((i, e) for i, e in numbers.items() if date_match(token, e)), key=lambda h: (not h[0].startswith("period."), h[0]))
        if hits:
            entry_id, entry = hits[0]
            result.update(status="traced", id=entry_id, label=entry["label"], value=display(entry))
        else:
            result["reason"] = "This date is not a date the numbers cover: not a period start or end, a change, or a date you gave."
        return result

    exact, rounded, near_pp = [], [], []
    for entry_id, entry in numbers.items():
        how = value_match(token, entry, ctx["approx"])
        if how == "exact":
            exact.append((entry_id, entry))
        elif how == "rounded":
            rounded.append((entry_id, entry))
        if token["kind"] == "pct" and entry["kind"] == "pp":
            as_points = dict(token, kind="pp")
            if value_match(as_points, entry, ctx["approx"]) == "exact":
                near_pp.append((entry_id, entry))
    scored = []
    for entry_id, entry in exact:
        checks = fit(entry, ctx, token["signed"])
        specific = (entry.get("metric") in ctx["metrics"]) + (entry.get("scope_id") in ctx["scopes"]) + (entry.get("comp") in {c for f in ctx["comps"] for c in COMP_FAMILY[f]})
        scored.append((sum(checks.values()), specific, entry_id, entry, checks))
    scored.sort(key=lambda s: (-s[0], -s[1], s[2]))
    if scored:
        _, _, entry_id, entry, checks = scored[0]
        status = _verdict(entry_id, entry, checks, typed=True)
        if status != "not_traced":
            result.update(status=status, id=entry_id, label=entry["label"], value=display(entry, signed=is_change(entry)),
                          reason=_reason(status, entry_id, entry, ctx) if status != "traced" else "")
            return result
    usable = [(i, e) for i, e in near_pp if all(fit(e, ctx).values())]
    if usable:
        entry_id, entry = usable[0]
        result.update(status="points_as_percent", id=entry_id, label=entry["label"], value=display(entry, signed=True),
                      reason="%s changed by %s. Write 'points', not '%%'." % (entry["label"], display(entry, signed=True)))
        return result
    usable = [(i, e) for i, e in rounded if all(fit(e, ctx, token["signed"]).values())]
    if usable:
        entry_id, entry = usable[0]
        result.update(status="rounded", id=entry_id, label=entry["label"], value=display(entry, signed=is_change(entry)),
                      reason=_reason("rounded", entry_id, entry, ctx))
        return result
    found = expected_entry(token, ctx, numbers)
    if found:
        entry_id, entry = found
        shown = display(entry, signed=is_change(entry))
        result.update(status="wrong_value", id=entry_id, label=entry["label"], value=shown,
                      reason="The data says %s is %s." % (entry["label"], shown))
        return result
    result["reason"] = "No number in the data has this value for this measure, campaign and comparison."
    return result


def resolve(ref_id, numbers):
    """(id, entry, absolute) for a cited id. id.abs is the same number without its sign."""
    if ref_id in numbers:
        return ref_id, numbers[ref_id], False
    if ref_id.endswith(".abs") and ref_id[:-4] in numbers:
        return ref_id[:-4], numbers[ref_id[:-4]], True
    return ref_id, None, False


SIMPLE_METRICS = {"cost", "impr", "clicks", "ctr", "cpc", "conv", "cvr", "cpa", "value", "roas"}


def expected_entry(token, ctx, numbers):
    """The number a sentence speaks of, when its words name one measure, at most one
    campaign and at most one comparison. Used to show the right value of a wrong figure."""
    metrics = ctx["metrics"] & SIMPLE_METRICS
    if len(metrics) != 1 or len(ctx["scopes"]) > 1 or len(ctx["comps"]) > 1:
        return None
    metric = next(iter(metrics))
    if "per_day" in ctx["metrics"] and metric in ("cost", "conv"):
        metric += "_per_day"
    scope = next(iter(ctx["scopes"])) if ctx["scopes"] else "acct"
    fam = next(iter(ctx["comps"])) if ctx["comps"] else None
    kind, moved = token["kind"], bool(ctx["direction"])
    if fam == "target":
        nid = "score.%s%s.diff_pct" % (metric, "_nb" if scope == "nb" else "") if kind == "pct" and metric != "roas" else "target.%s" % metric
    elif kind == "pp":
        nid = "%s.%s.pp_%s" % (scope, metric, fam or "prev")
    elif kind == "pct" and metric not in ("ctr", "cvr", "roas"):
        if moved or fam or scope in ("acct", "nb"):
            nid = "%s.%s.chg_%s" % (scope, metric, fam or "prev")
        else:
            nid = "%s.%s.share_cur" % (scope, metric)
    elif kind == "pct" and moved:
        nid = "%s.%s.chg_%s" % (scope, metric, fam or "prev")
    elif kind == "num" and moved:
        nid = "%s.%s.delta_%s" % (scope, metric, fam or "prev")
    else:
        nid = "%s.%s.%s" % (scope, metric, fam or "cur")
    entry = numbers.get(nid)
    if not entry or entry["kind"] == "date":
        return None
    if kind == "pct" and entry["kind"] != "pct" and not (entry["kind"] == "ratio" and metric == "roas"):
        return None
    if kind in ("num", "ratio") and entry["kind"] not in PLAIN_KINDS:
        return None
    if kind == "pp" and entry["kind"] != "pp":
        return None
    return nid, entry


def analyse(text, numbers, matchers, names=()):
    """Trace every number in one unit of text.

    Returns (rendered text, results). Rendering puts the figure in place of
    each {id}: a change is written without its sign when the sentence says
    which way it went, and with its sign when it does not.
    """
    results, replacements = [], []
    row = text.lstrip().startswith("|")
    for s_start, s_end in ([(0, len(text))] if row else sentences(text)):
        sentence = text[s_start:s_end]
        found = tokens(sentence, names)
        plain = REF.sub(lambda m: " " * len(m.group(0)), sentence)
        plain = BID_STRATEGIES.sub(lambda m: " " * len(m.group(0)), plain)
        label = next((c for c in plain.split("|") if c.strip()), "") if row else ""
        for index, token in enumerate(found):
            prev_end = found[index - 1]["end"] if index else 0
            next_start = found[index + 1]["start"] if index + 1 < len(found) else len(sentence)
            if row:
                # A table row is read by its label only. Other cells hold statuses and other columns.
                ctx = {"metrics": _phrases(label, METRIC_PHRASES), "scopes": {sc for _, sc in mentions(label, matchers)},
                       "comps": set(), "direction": None, "approx": None}
            else:
                ctx = context(plain, token, prev_end, next_start, matchers)
            result = check_token(token, ctx, numbers)
            result["sentence"] = sentence.strip()
            results.append(result)
            if token["kind"] == "ref":
                _, entry, absolute = resolve(token["id"], numbers)
                if entry:
                    signed = is_change(entry) and not ctx["direction"] and not absolute
                    shown = display(entry, signed=signed, absolute=(is_change(entry) or absolute) and not signed)
                else:
                    shown = token["raw"]
                replacements.append((s_start + token["start"], s_start + token["end"], shown))
    rendered = text
    for start, end, shown in sorted(replacements, reverse=True):
        rendered = rendered[:start] + shown + rendered[end:]
    return rendered, results
