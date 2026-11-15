#!/usr/bin/env python3
"""Step 3 of a client report: fact check every number.

Reads the narrative you wrote (WORK/narrative.json), finds every number in it
(ids in braces, amounts, percentages, counts and dates) and traces each one to
WORK/numbers.json within the rounding it was written with. A number that
cannot be traced, that matches a different measure, campaign or comparison, or
whose direction contradicts the data, is refused with the sentence it sits in.
The report is written only after this check passes.

The same step fact checks a report someone already wrote, in Markdown, plain
text or Word (.docx), against the numbers of the same period.

    python3 fact_check.py --work WORKDIR
    python3 fact_check.py --work WORKDIR --report REPORT.md --out OUTPUTDIR [--current 2026-10-01:2026-10-31]

For a report someone wrote, the period is read from its header. If it cannot be
read, pass the period with --current. Either way it must be the period WORK was
measured for.
"""
import argparse
import calendar
import datetime as dt
import hashlib
import os
import re
import sys
import zipfile
from xml.etree import ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import dates, outputs, xlsx  # noqa: E402
import claims  # noqa: E402

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
GROUPS = (("Verified", ("traced",)),
          ("Contradicted by the data", ("wrong_value", "contradicted")),
          ("Unclear or overclaimed", ("wrong_metric", "wrong_scope", "wrong_comparison", "rounded", "points_as_percent")),
          ("Needs data", ("not_traced", "words", "unknown_id")))
DATE_KINDS = ("date", "month", "year")
COMPARISON_WORDS = re.compile(r"\b(compared|previous|prior|last year|year over year|month over month|week over week|quarter over quarter|vs\.?|versus|against)\b", re.I)
LIMIT_WORDS = re.compile(r"\b(late conversions?|attribution|cannot show|can't show|does not include|doesn't include|not included|limitations?|caveats?|still (?:rise|come in|change))\b", re.I)


def file_hash(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


def setup(work):
    path = os.path.join(work, "numbers.json")
    if not os.path.exists(path):
        raise SystemExit("No numbers.json in %s. Run scripts/measure.py first." % work)
    data = outputs.read_json(path)
    campaigns = [(s["id"], s["name"]) for s in data["scopes"] if s["kind"] in ("campaign", "type")]
    names = [n for _, n in campaigns] + [data.get("client") or "", data.get("agency") or ""]
    return path, data, claims.campaign_matchers(campaigns), names


def check_units(units, data, matchers, names):
    results = []
    for where, text in units:
        _, found = claims.analyse(text, data["numbers"], matchers, names)
        for result in found:
            result["where"] = where
            results.append(result)
    return results


def narrative_units(narrative, data):
    """Every piece of text in the narrative, with where it sits, and structural problems."""
    problems, units = [], []
    title = narrative.get("title")
    if not isinstance(title, str) or not title.strip():
        problems.append("The narrative needs a title.")
    else:
        units.append(("Title", title))
    sections = narrative.get("sections")
    if not isinstance(sections, list) or not sections:
        problems.append("The narrative has no sections.")
        return units, problems
    available = set(data["available_tables"])
    for number, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            problems.append("Section %d is not an object with heading, text, bullets and tables." % number)
            continue
        heading = (section.get("heading") or "").strip()
        label = 'Section "%s"' % heading if heading else "Section %d" % number
        if not heading:
            problems.append("Section %d has no heading." % number)
        else:
            units.append((label + ", heading", heading))
        text = section.get("text") or ""
        bullets = section.get("bullets") or []
        if not isinstance(text, str) or not isinstance(bullets, list) or not all(isinstance(b, str) for b in bullets):
            problems.append("%s: text must be a string and bullets a list of strings." % label)
            continue
        if not text.strip() and not any(b.strip() for b in bullets):
            problems.append("%s is empty. Write it or remove it." % label)
        for index, unit in enumerate(claims.units_from_text(text), start=1):
            units.append(("%s, paragraph %d" % (label, index), unit))
        for index, bullet in enumerate(bullets, start=1):
            if bullet.strip():
                units.append(("%s, bullet %d" % (label, index), bullet.strip()))
        for table in section.get("tables") or []:
            if table not in available:
                if table in ("account", "account_without_brand", "campaign_types", "campaigns", "campaigns_last_year", "scorecard", "movers", "changes"):
                    problems.append('%s asks for the table "%s", which this data cannot fill (for example no targets, no brand campaigns, no change history or no last year).' % (label, table))
                else:
                    problems.append('%s asks for the table "%s", which does not exist. The tables are: %s.' % (label, table, ", ".join(sorted(available))))
    return units, problems


def read_report_text(path):
    if path.lower().endswith(".docx"):
        try:
            with zipfile.ZipFile(path) as archive:
                root = ET.fromstring(archive.read("word/document.xml"))
        except (OSError, KeyError, zipfile.BadZipFile, ET.ParseError):
            raise SystemExit("I can't read %s as a Word document. Save it again as .docx, or as Markdown or plain text." % path)
        lines = []
        body = root.find(W + "body")
        for child in list(body if body is not None else []):
            if child.tag == W + "p":
                lines += ["".join(t.text or "" for t in child.iter(W + "t")), ""]
            elif child.tag == W + "tbl":
                for row in child.iter(W + "tr"):
                    cells = ["".join(t.text or "" for t in cell.iter(W + "t")) for cell in row.findall(W + "tc")]
                    lines.append("| " + " | ".join(cells) + " |")
                lines.append("")
        return "\n".join(lines)
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return handle.read()
    except (OSError, UnicodeDecodeError):
        raise SystemExit("I can't read %s. Give the report as Markdown, plain text or .docx." % path)


def draft_period(units):
    """The period a report states in its header: a date range, or a month or quarter in the title."""
    head = units[:8]
    ordered = [u for u in head if re.search(r"\b(period|covering|covers|dates)\b", u, re.I)] + head
    for unit in ordered:
        found = [t for t in claims.tokens(unit) if t["kind"] == "date"]
        if len(found) >= 2:
            year = found[1]["y"] or found[0]["y"]
            if year:
                try:
                    a = dt.date(found[0]["y"] or year, found[0]["m"], found[0]["d"])
                    b = dt.date(found[1]["y"] or year, found[1]["m"], found[1]["d"])
                except ValueError:
                    continue
                if a <= b:
                    return a.isoformat(), b.isoformat()
    for unit in ordered:
        quarter = re.search(r"\bQ([1-4])\s+(\d{4})\b", unit)
        if quarter:
            q, year = int(quarter.group(1)), int(quarter.group(2))
            end_month = 3 * q
            return dt.date(year, end_month - 2, 1).isoformat(), dt.date(year, end_month, calendar.monthrange(year, end_month)[1]).isoformat()
        months = [t for t in claims.tokens(unit) if t["kind"] == "month"]
        if months:
            m, year = months[0]["m"], months[0]["y"]
            return dt.date(year, m, 1).isoformat(), dt.date(year, m, calendar.monthrange(year, m)[1]).isoformat()
    return None


def refusal_lines(results):
    lines = []
    for r in results:
        if r["status"] == "traced":
            continue
        lines.append('- %s: "%s" in: %s' % (claims.STATUS_TEXT[r["status"]], r["raw"], r["sentence"]))
        lines.append("  %s (%s)" % (r["reason"], r["where"]))
    return lines


def check_narrative(args):
    numbers_path, data, matchers, names = setup(args.work)
    narrative_path = os.path.join(args.work, "narrative.json")
    if not os.path.exists(narrative_path):
        raise SystemExit("No narrative.json in %s. Copy narrative.template.json to narrative.json and write it first." % args.work)
    try:
        narrative = outputs.read_json(narrative_path)
    except ValueError as error:
        raise SystemExit("narrative.json is not valid JSON: %s" % error)
    units, problems = narrative_units(narrative, data)
    results = check_units(units, data, matchers, names)
    headings = {(s.get("heading") or "").strip().lower() for s in narrative.get("sections") or [] if isinstance(s, dict)}
    warnings = ['The playbook asks for a section "%s", and the narrative has none by that name.' % h
                for h in data.get("required_sections", []) if h.lower() not in headings]
    cited = [r["id"] for r in results if r["kind"] == "ref" and r["id"]]
    tables = [t for sec in narrative.get("sections") or [] if isinstance(sec, dict) for t in sec.get("tables") or []]
    if data.get("target_warnings") and not data.get("targets_confirmed") and (
            "scorecard" in tables or any(i.startswith(("target.", "score.")) for i in cited)):
        for warning in data["target_warnings"]:
            problems.append("%s Then run measure.py again with the right target, or with --confirm-targets if the person says it is right." % warning)
    if data.get("brand_outlier"):
        for key in ("cpa", "roas"):
            blended, without = "acct.%s.cur" % key, "nb.%s.cur" % key
            if blended in cited and without not in cited:
                problems.append("The narrative cites %s but not %s. Brand is an outlier, so give the figure without brand, first." % (blended, without))
            elif blended in cited and cited.index(blended) < cited.index(without):
                warnings.append("Brand is an outlier: give %s before %s, and say brand searches convert cheaply by nature." % (without, blended))
    refused = [r for r in results if r["status"] != "traced"]
    passed = not problems and not refused
    outputs.write_json(os.path.join(args.work, "checked.json"), {
        "narrative_hash": file_hash(narrative_path), "numbers_hash": file_hash(numbers_path), "passed": passed,
        "problems": problems, "warnings": warnings, "results": results})

    figures = [r for r in results if r["kind"] not in DATE_KINDS]
    lines = ["# Fact check of the narrative", "",
             "- Numbers: %d found, %d traced, %d refused." % (len(figures), sum(1 for r in figures if r["status"] == "traced"),
                                                             sum(1 for r in figures if r["status"] != "traced")),
             "- Dates: %d found, %d match the data." % (len(results) - len(figures), sum(1 for r in results if r["kind"] in DATE_KINDS and r["status"] == "traced"))]
    if problems:
        lines += ["", "## Problems with the narrative", ""] + ["- " + p for p in problems]
    if refused:
        lines += ["", "## Refused numbers", "", "Fix each one: cite the right id, or remove the claim. Do not work a figure out yourself.", ""]
        lines += refusal_lines(results)
    if warnings:
        lines += ["", "## Warnings", ""] + ["- " + w for w in warnings]
    lines += ["", "PASSED. Next: python3 scripts/write_report.py --work %s --out OUTPUTDIR" % args.work if passed else
              "NOT PASSED. Edit narrative.json and run this check again. The report is not written until it passes."]
    text = "\n".join(lines).rstrip() + "\n"
    with open(os.path.join(args.work, "fact-check.md"), "w", encoding="utf-8") as handle:
        handle.write(text)
    print(text)
    if not passed:
        sys.exit(1)


def check_existing(args):
    if not args.out:
        raise SystemExit("Give --out OUTPUTDIR for the fact check files.")
    _, data, matchers, names = setup(args.work)
    text = read_report_text(args.report)
    unit_texts = claims.units_from_text(text)
    measured = tuple(data["periods"]["current"])
    if args.current:
        a, _, b = args.current.partition(":")
        a, b = dates.parse_day(a), dates.parse_day(b)
        if not a or not b:
            raise SystemExit("Write the period as START:END, for example 2026-10-01:2026-10-31.")
        stated, source = (a.isoformat(), b.isoformat()), "--current"
    else:
        stated, source = draft_period(unit_texts), "the report's header"
    if not stated:
        raise SystemExit("I can't read the period this report covers from its header. Ask the person which dates it covers, run measure.py for "
                         "that period into a separate work folder (--current START:END), then run this again with --current START:END.")
    if stated != measured:
        raise SystemExit("The report covers %s to %s (from %s), but %s was measured for %s to %s. Run measure.py into a separate work folder with "
                         "--report-type fact-check --current %s:%s, then run this again with that folder." % (
                             stated[0], stated[1], source, args.work, measured[0], measured[1], stated[0], stated[1]))
    units = [("Line %d" % i, u) for i, u in enumerate(unit_texts, start=1)]
    results = check_units(units, data, matchers, names)
    cur = data["periods"]["current"]
    states_range = any(r["status"] == "traced" and r["id"] in ("period.cur.start", "period.cur.end") for r in results) or \
        any(r["status"] == "traced" and r["kind"] == "month" and r["id"].startswith("period.cur") for r in results)
    caveats = [("States the reporting period (%s to %s)" % (cur[0], cur[1]), states_range),
               ("Says what it compares against", bool(COMPARISON_WORDS.search(text))),
               ("Says what the numbers cannot show (late conversions, attribution, what is not included)", bool(LIMIT_WORDS.search(text)))]
    dates_missed = sum(1 for r in results if r["kind"] in ("date", "month") and r["status"] != "traced")

    out = outputs.ensure_dir(args.out)
    outputs.write_json(os.path.join(out, "fact-check.json"), {"report": os.path.basename(args.report), "periods": data["periods"],
                                                             "results": results, "caveats": [{"check": c, "present": ok} for c, ok in caveats]})
    book = xlsx.Workbook()
    book.add_sheet("Numbers checked", ["Group", "Result", "Number", "Sentence", "Matched to", "Value in the data", "id", "Why", "Where"],
                   [[("Date" if r["kind"] in DATE_KINDS else next(g for g, statuses in GROUPS if r["status"] in statuses)),
                     claims.STATUS_TEXT[r["status"]], r["raw"], r["sentence"],
                     r["label"], r["value"], r["id"], r["reason"], r["where"]] for r in results],
                   formats={3: "wrap", 7: "wrap"}, widths={3: 70, 4: 45, 7: 60})
    book.add_sheet("Caveats", ["Check", "Present"], [[c, "Yes" if ok else "No"] for c, ok in caveats], widths={0: 80})
    book.save(os.path.join(out, "fact-check.xlsx"))

    figures = [r for r in results if r["kind"] not in DATE_KINDS]
    date_results = [r for r in results if r["kind"] in DATE_KINDS]
    lines = ["# Fact check: %s" % os.path.basename(args.report), "",
             "Checked against the numbers for %s to %s, compared with %s to %s%s." % (
                 cur[0], cur[1], data["periods"]["previous"][0], data["periods"]["previous"][1],
                 " and the same period last year" if data["periods"]["last_year"] else ""),
             "", "- %d numbers found, dates not counted." % len(figures)]
    for group, statuses in GROUPS:
        lines.append("- %s: %d." % (group, sum(1 for r in figures if r["status"] in statuses)))
    lines.append("- Dates, counted apart: %d found, %d match the period and the data." % (len(date_results), sum(1 for r in date_results if r["status"] == "traced")))
    if dates_missed:
        lines.append("- %d dates are not dates the data covers: %s." % (dates_missed, ", ".join('"%s"' % r["raw"] for r in date_results if r["status"] != "traced")))
    for group, statuses in GROUPS[1:]:
        picked = [r for r in results if r["status"] in statuses]
        if group == "Needs data":
            picked = [r for r in picked if r["kind"] not in DATE_KINDS]
        if picked:
            lines += ["", "## %s" % group, ""] + refusal_lines(picked)
    verified = [r for r in figures if r["status"] == "traced"]
    if verified:
        lines += ["", "## Verified", "", outputs.md_table(["Number", "Matched to", "Value in the data"],
                                                          [[r["raw"], r["label"], r["value"]] for r in verified])]
    lines += ["", "## Caveats", "", outputs.md_table(["Check", "Present"], [[c, "Yes" if ok else "No"] for c, ok in caveats]),
              "", "## How the check works", "",
              "- Every number is matched to the numbers of the period within the rounding it was written with: 12% matches 11.5% to 12.5%.",
              "- The words around it are read too: the measure, the campaign, the comparison and whether it rose or fell. A value that matches only a different one is flagged.",
              "- A number that matches by coincidence passes. The Verified table shows what each was matched to, so check it reads right.",
              "- The caveat checks look for words only. Read the report to judge them.",
              "", "## What this did not cover", "",
              "- Claims without numbers, such as causes and recommendations. Judge those against the summary from measure.py.",
              "- Numbers written in words, other than doubled, halved and the like, which are flagged.",
              "- Numbers from outside Google Ads, such as CRM leads or revenue, unless they were given to measure.py with --given."]
    text_out = "\n".join(lines) + "\n"
    with open(os.path.join(out, "fact-check.md"), "w", encoding="utf-8") as handle:
        handle.write(text_out)
    print(text_out)
    print("Wrote the files to %s" % out)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True)
    parser.add_argument("--report", help="a report someone already wrote: .md, .txt or .docx")
    parser.add_argument("--out", help="where to write the fact check of --report")
    parser.add_argument("--current", help="the period the report covers, START:END, when its header does not say")
    args = parser.parse_args()
    if args.report:
        check_existing(args)
    else:
        check_narrative(args)


if __name__ == "__main__":
    main()
