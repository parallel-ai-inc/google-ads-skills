#!/usr/bin/env python3
"""Step 4 of a client report: write it.

Runs only after fact_check.py passed on the same narrative and the same
numbers. Writes the client report as a Word document and as Markdown, and a
workbook with every table. Every figure comes from the numbers file. The files
carry the agency's and the client's names when given, and no vendor name.

    python3 write_report.py --work WORKDIR --out OUTPUTDIR [--client "Northside Plumbing"] [--agency "Your agency"]
"""
import argparse
import datetime as dt
import hashlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gads import outputs, xlsx  # noqa: E402
import claims  # noqa: E402
import docx_writer  # noqa: E402
import fact_check  # noqa: E402

ROAS = "Return on ad spend (conv. value / cost)"
ACCOUNT_ROWS = (("cost", "Cost"), ("impr", "Impr."), ("clicks", "Clicks"), ("ctr", "CTR"), ("cpc", "Avg. CPC"), ("conv", "Conversions"),
                ("cvr", "Conv. rate"), ("cpa", "Cost / conv."), ("value", "Conv. value"), ("roas", ROAS))


def cap(text):
    """Table labels start with a capital letter."""
    text = str(text)
    return text[:1].upper() + text[1:] if text else text


def client_label(text):
    return str(text).replace("Conv. value / cost", ROAS)


def file_hash(path):
    with open(path, "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()


class Tables:
    """Every table the report can hold, as (header, text rows, workbook rows, formats, right aligned columns)."""

    def __init__(self, data):
        self.data, self.n = data, data["numbers"]
        self.has_ly = bool(data["periods"]["last_year"])
        self.scopes = {s["id"]: s for s in data["scopes"]}

    def text(self, nid, signed=None):
        entry = self.n.get(nid)
        if not entry:
            return "n/a"
        return claims.display(entry, signed=claims.is_change(entry) if signed is None else signed)

    def raw(self, nid):
        entry = self.n.get(nid)
        return entry["value"] if entry else None

    def account(self, sid):
        header = ["Measure", "This period", "Previous period", "Change"] + (["Same period last year", "Change vs last year"] if self.has_ly else [])
        rows = list(ACCOUNT_ROWS)
        p = self.data["periods"]
        if self._days(p["current"]) != self._days(p["previous"]):
            rows += [("cost_per_day", "Cost per day"), ("conv_per_day", "Conversions per day")]
        text, book = [], []
        for key, label in rows:
            if "%s.%s.cur" % (sid, key) not in self.n:
                continue
            ids = ["%s.%s.%s" % (sid, key, c) for c in (["cur", "prev", "chg_prev"] + (["ly", "chg_ly"] if self.has_ly else []))]
            text.append([label] + [self.text(i) for i in ids])
            book.append([label] + [self.raw(i) for i in ids])
        return header, text, book, {}, range(1, len(header))

    def account_sheets(self, sid):
        """The account table for the workbook: one row per period, one format per column."""
        keys = [(k, label) for k, label in ACCOUNT_ROWS + (("cost_per_day", "Cost per day"), ("conv_per_day", "Conversions per day"))
                if "%s.%s.cur" % (sid, k) in self.n]
        kinds = {"impr": "int", "clicks": "int", "ctr": "pct", "cvr": "pct"}
        name = self.scopes[sid]["name"]
        comps = [("cur", "This period"), ("prev", "Previous period")] + ([("ly", "Same period last year")] if self.has_ly else [])
        values = [[label] + [self.raw("%s.%s.%s" % (sid, k, c)) for k, _ in keys] for c, label in comps]
        changes = [[label] + [self.raw("%s.%s.%s" % (sid, k, c)) for k, _ in keys]
                   for c, label in [("chg_prev", "Change vs previous period")] + ([("chg_ly", "Change vs last year")] if self.has_ly else [])]
        header = ["Period"] + [label for _, label in keys]
        return [(name, header, values, {i + 1: kinds.get(k, "money") for i, (k, _) in enumerate(keys)}),
                (name + ", change", header, changes, {i + 1: "pct" for i in range(len(keys))})]

    @staticmethod
    def _days(pair):
        return (dt.date.fromisoformat(pair[1]) - dt.date.fromisoformat(pair[0])).days + 1

    def campaigns(self, last_year=False):
        comp = "ly" if last_year else "prev"
        header = ["Campaign", "Status", "Cost", "Change", "Conversions", "Change", "Cost / conv.", "Change"]
        if self.data["has_value"]:
            header += ["Return on ad spend", "Change"]
        if not last_year:
            header += ["Share of cost", "Share of conversions"]
        text, book = [], []
        for s in self.data["scopes"]:
            if s["kind"] != "campaign":
                continue
            sid = s["id"]
            ids = []
            for key in ("cost", "conv", "cpa") + (("roas",) if self.data["has_value"] else ()):
                ids += ["%s.%s.cur" % (sid, key), "%s.%s.chg_%s" % (sid, key, comp)]
            if not last_year:
                ids += ["%s.cost.share_cur" % sid, "%s.conv.share_cur" % sid]
            name = s["name"] + (" (Brand)" if s.get("brand") and "brand" not in s["name"].lower() else "")
            text.append([name, s["status"]] + [self.text(i) for i in ids])
            book.append([name, s["status"]] + [self.raw(i) for i in ids])
        formats = {i: ("pct" if h in ("Change", "Share of cost", "Share of conversions") else "money") for i, h in enumerate(header) if i >= 2}
        if last_year:
            header = [h if h != "Change" else "Change vs last year" for h in header]
        return header, text, book, formats, range(2, len(header))

    def campaign_types(self):
        header = ["Campaign type", "Cost", "Change", "Conversions", "Change", "Cost / conv.", "Change"]
        text, book = [], []
        for s in self.data["scopes"]:
            if s["kind"] == "type":
                ids = [x for key in ("cost", "conv", "cpa") for x in ("%s.%s.cur" % (s["id"], key), "%s.%s.chg_prev" % (s["id"], key))]
                text.append([s["name"]] + [self.text(i) for i in ids])
                book.append([s["name"]] + [self.raw(i) for i in ids])
        return header, text, book, {1: "money", 2: "pct", 3: "money", 4: "pct", 5: "money", 6: "pct"}, range(1, 7)

    def scorecard(self):
        header = ["KPI", "Target", "Actual", "Difference", "Difference %", "Previous period", "Status"]
        text, book = [], []
        for r in self.data["scorecard"]:
            ids = [r["target_id"], r["actual_id"], r.get("diff_id"), r.get("diff_pct_id"), r["prev_id"]]
            kpi = cap(client_label(r["kpi"]))
            text.append([kpi] + [self.text(i) if i else "n/a" for i in ids] + [r["status"]])
            book.append([kpi] + [self.raw(i) if i else None for i in ids] + [r["status"]])
        return header, text, book, {1: "money", 2: "money", 3: "money", 4: "pct", 5: "money"}, range(1, 6)

    def movers(self):
        keys = [("conv", "Conversions"), ("cost", "Cost")] + ([("value", "Conv. value")] if self.data["has_value"] else [])
        header = ["Campaign"] + [h for _, label in keys for h in (label + " change", label + " change %")]
        order = list(self.data["movers"].get("conv") or [])
        order += [sid for sid in self.data["movers"].get("cost") or [] if sid not in order]
        text, book = [], []
        for sid in order[:5]:
            ids = [x for key, _ in keys for x in ("%s.%s.delta_prev" % (sid, key), "%s.%s.chg_prev" % (sid, key))]
            name = self.scopes[sid]["name"] + (" (%s)" % cap(self.scopes[sid]["status"].lower()) if self.scopes[sid]["status"].lower() in ("paused", "removed") else "")
            text.append([name] + [self.text(i) for i in ids])
            book.append([name] + [self.raw(i) for i in ids])
        formats = {i: ("pct" if i % 2 == 0 else "money") for i in range(1, len(header))}
        return header, text, book, formats, range(1, len(header))

    def changes(self):
        header = ["Date", "Campaign", "Ad group", "Change", "Made by"]
        rows = [[claims.long_date(c["date"]), c["campaign"] or "Whole account", c["ad_group"] or "All", cap(c["changes"]),
                 "Google's systems" if c["by_system"] else "Team"] for c in self.data["changes"]["items"]]
        return header, rows, rows, {3: "wrap"}, ()

    def get(self, name):
        if name == "account":
            return self.account("acct")
        if name == "account_without_brand":
            return self.account("nb")
        if name == "campaigns_last_year":
            return self.campaigns(last_year=True)
        return getattr(self, name)()


TABLE_TITLES = {"account": "Account", "account_without_brand": "Account without brand", "campaign_types": "By campaign type",
                "campaigns": "Campaigns", "campaigns_last_year": "Campaigns against last year", "scorecard": "KPI scorecard",
                "movers": "Biggest movers against the previous period", "changes": "Changes made in the period"}

# Workbook sheet names hold 31 characters at most.
SHEET_TITLES = {"campaigns_last_year": "Campaigns vs last year", "movers": "Biggest movers", "changes": "Changes in the period"}


def about(data, tables):
    """The closing section, written from the numbers file."""
    p = data["periods"]

    def period(pair):
        return "%s to %s" % (claims.long_date(pair[0]), claims.long_date(pair[1]))

    made = ["This report covers %s (%d days) and compares it with %s (%d days)%s." % (
        period(p["current"]), tables._days(p["current"]), period(p["previous"]), tables._days(p["previous"]),
        " and with the same period last year, %s" % period(p["last_year"]) if p["last_year"] else ""),
        "All figures come from the Google Ads campaign report for those dates%s." % (". Amounts are in %s" % data["currency"] if data["currency"] else ""),
        "A change is the difference between the periods divided by the earlier period. Cost per conversion and return on ad spend (conv. value / cost) "
        "are worked out from the period totals."]
    if tables._days(p["current"]) != tables._days(p["previous"]):
        made.append("The periods differ in length, so per day figures are shown too.")
    if data["brand"]:
        made.append("Account without brand leaves out: %s." % ", ".join(data["brand"]))
    outlier = data.get("brand_outlier")
    if outlier:
        line = "Brand campaigns ran at a cost per conversion of %s, against %s for the account without brand" % (
            tables.text("brand.cpa.cur"), tables.text("nb.cpa.cur"))
        if outlier.get("roas") is not None and "nb.roas.cur" in tables.n:
            line += ", and a return on ad spend of %s, against %s without brand" % (tables.text("brand.roas.cur"), tables.text("nb.roas.cur"))
        made.append(line + ". Searches for a business's own name convert cheaply by nature, so the figures without brand show how the rest of the account performs.")
    if data["scorecard"]:
        made.append("Targets are the ones agreed for this period." if data.get("targets_agreed") else "Targets are the ones you gave for this period.")
    if data["changes"]["read"]:
        made.append("Account changes come from the account's change history.")
    cannot = ["Conversions for the last days of the period can still rise as late conversions are reported.",
              "Conversions are counted under the account's conversion and attribution settings. They are not the same as sales or leads in your own systems.",
              "Nothing outside Google Ads: the website, other channels, or what happened after a lead came in.",
              "A change made in the period shows timing, not proof of cause.",
              "Campaign status is as of the day the data was downloaded."]
    if not p["last_year"]:
        cannot.append("The same period last year is not compared, because the data does not reach back that far.")
    if not data["changes"]["read"]:
        cannot.append("Changes made in the account are not listed.")
    return made, cannot


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--work", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--client", help="the client's name, shown on the report")
    parser.add_argument("--agency", help="your agency's name, shown on the report")
    args = parser.parse_args()

    numbers_path = os.path.join(args.work, "numbers.json")
    narrative_path = os.path.join(args.work, "narrative.json")
    checked_path = os.path.join(args.work, "checked.json")
    if not os.path.exists(checked_path) or not os.path.exists(narrative_path):
        raise SystemExit("Run scripts/fact_check.py first. No report is written until its numbers have been checked.")
    checked = outputs.read_json(checked_path)
    if file_hash(narrative_path) != checked["narrative_hash"] or file_hash(numbers_path) != checked["numbers_hash"]:
        raise SystemExit("narrative.json or numbers.json changed after the last fact check. Run scripts/fact_check.py again.")
    if not checked["passed"]:
        raise SystemExit("The last fact check did not pass. Fix narrative.json and run scripts/fact_check.py until it passes.")

    data = outputs.read_json(numbers_path)
    narrative = outputs.read_json(narrative_path)
    _, _, matchers, names = fact_check.setup(args.work)
    client = (args.client if args.client is not None else data.get("client") or "").strip()
    agency = (args.agency if args.agency is not None else data.get("agency") or "").strip()
    tables = Tables(data)

    def render(text):
        return claims.analyse(text, data["numbers"], matchers, names)[0]

    # The report as blocks, rendered to Word and Markdown from the same list.
    p = data["periods"]
    blocks = [("title", render(narrative["title"]))]
    kind = data["type_title"].replace("Google Ads ", "")
    by = " ".join(x for x in ("for %s" % client if client and client not in narrative["title"] else "", "by %s" % agency if agency else "") if x)
    blocks.append(("subtitle", "%s, prepared %son %s." % (cap(kind), by + " " if by else "", claims.long_date(data["prepared"]))))
    period_line = "Reporting period: %s to %s. Compared with %s to %s%s." % (
        claims.long_date(p["current"][0]), claims.long_date(p["current"][1]), claims.long_date(p["previous"][0]), claims.long_date(p["previous"][1]),
        " and with %s to %s" % (claims.long_date(p["last_year"][0]), claims.long_date(p["last_year"][1])) if p["last_year"] else "")
    blocks.append(("small", period_line))
    used = []
    for section in narrative["sections"]:
        blocks.append(("h1", render(section["heading"])))
        for unit in claims.units_from_text(section.get("text") or ""):
            blocks.append(("p", render(unit)))
        for bullet in section.get("bullets") or []:
            if bullet.strip():
                blocks.append(("bullet", render(bullet.strip())))
        for name in section.get("tables") or []:
            header, rows, _, _, numeric = tables.get(name)
            if rows:
                blocks.append(("h2", TABLE_TITLES[name]))
                rows = [[cap(client_label(row[0]))] + list(row[1:]) for row in rows]
                blocks.append(("table", [cap(h) for h in header], rows, set(numeric)))
            if name not in used:
                used.append(name)
    made, cannot = about(data, tables)
    blocks += [("h1", "About these numbers"), ("h2", "How the numbers were made")] + [("bullet", m) for m in made]
    blocks += [("h2", "What these numbers cannot show")] + [("bullet", c) for c in cannot]

    out = outputs.ensure_dir(args.out)
    doc = docx_writer.Document()
    md = []
    for block in blocks:
        kind = block[0]
        if kind == "title":
            doc.title(block[1])
            md += ["# " + block[1], ""]
        elif kind == "subtitle":
            doc.subtitle(block[1])
            md += [block[1], ""]
        elif kind == "small":
            doc.small(block[1])
            md += ["_%s_" % block[1], ""]
        elif kind == "h1":
            doc.heading(block[1], 1)
            md += ["## " + block[1], ""]
        elif kind == "h2":
            doc.heading(block[1], 2)
            md += ["### " + block[1], ""]
        elif kind == "p":
            doc.paragraph(block[1])
            md += [block[1], ""]
        elif kind == "bullet":
            doc.bullet(block[1])
            md.append("- " + block[1])
            continue
        elif kind == "table":
            doc.table(block[1], block[2], numeric=block[3])
            md += [outputs.md_table(block[1], block[2]), ""]
        if md and md[-1] != "" and kind != "bullet":
            md.append("")
    # A blank line after each run of bullets.
    lines = []
    for index, line in enumerate(md):
        lines.append(line)
        if line.startswith("- ") and (index + 1 == len(md) or not md[index + 1].startswith("- ")) and (index + 1 == len(md) or md[index + 1] != ""):
            lines.append("")
    doc.save(os.path.join(out, "client-report.docx"), title=blocks[0][1], author=agency)
    with open(os.path.join(out, "client-report.md"), "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines).rstrip() + "\n")

    book = xlsx.Workbook()
    for name in data["available_tables"]:
        header, text_rows, rows, formats, _ = tables.get(name)
        if not rows:
            continue
        if name in ("account", "account_without_brand"):
            sid = "acct" if name == "account" else "nb"
            for title, sheet_header, sheet_rows, sheet_formats in tables.account_sheets(sid):
                book.add_sheet(title, sheet_header, sheet_rows, formats=sheet_formats, widths={0: 30})
            continue
        book.add_sheet(SHEET_TITLES.get(name, TABLE_TITLES[name]), header, rows, formats=formats, widths={0: 34, 2: 70} if name == "changes" else {0: 34})
    daily_header = ["Day", "Period", "Cost", "Impr.", "Clicks", "Conversions"] + (["Conv. value"] if data["has_value"] else [])
    book.add_sheet("Daily", daily_header, [r[:len(daily_header)] for r in data["daily"]], formats={2: "money", 3: "int", 4: "int", 5: "money", 6: "money"})
    book.add_sheet("Every number", ["id", "What it is", "Value"], [[nid, e["label"], e["display"]] for nid, e in sorted(data["numbers"].items())], widths={0: 28, 1: 80, 2: 22})
    book.save(os.path.join(out, "client-report-tables.xlsx"))
    outputs.write_json(os.path.join(out, "report-numbers.json"), {nid: {"label": e["label"], "value": e["value"], "shown": e["display"]}
                                                                 for nid, e in sorted(data["numbers"].items())})

    cited = sum(1 for r in outputs.read_json(checked_path)["results"] if r["kind"] not in ("date", "month", "year"))
    print("Wrote client-report.docx, client-report.md, client-report-tables.xlsx and report-numbers.json to %s" % out)
    print('"%s": %d sections, %d tables, %d numbers in the narrative, all checked.' % (
        blocks[0][1], len(narrative["sections"]), sum(1 for b in blocks if b[0] == "table"), cited))
    if not client or not agency:
        print("NOTE: %s not given, so the report does not show %s. Add --client and --agency to name them." % (
            "the client's and the agency's names were" if not client and not agency else "the client's name was" if not client else "the agency's name was",
            "them" if not client and not agency else "it"))


if __name__ == "__main__":
    main()
