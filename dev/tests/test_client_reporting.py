"""Tests for the client reporting skill: what a customer would lose if it broke.

    python3 -m unittest dev/tests/test_client_reporting.py
"""
import csv
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from xml.dom import minidom

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, "skills", "client-reporting-for-google-ads")
EXPORTS = os.path.join(ROOT, "examples", "exports", "client-reporting")
REPORT = os.path.join(EXPORTS, "campaigns-by-day.csv")
CHANGES = os.path.join(EXPORTS, "change-history.csv")


def call(script, *args):
    return subprocess.run([sys.executable, os.path.join(SKILL, "scripts", script)] + list(args), capture_output=True, text=True, cwd=SKILL)


def run(script, *args):
    done = call(script, *args)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def setUpModule():
    for command in ([os.path.join(ROOT, "dev", "tools", "build.py"), "client-reporting-for-google-ads"],
                    [os.path.join(ROOT, "dev", "samples", "make_samples_client-reporting.py")]):
        subprocess.run([sys.executable] + command, check=True, capture_output=True)


def valid_zip_xml(test, path):
    with zipfile.ZipFile(path) as archive:
        for member in archive.namelist():
            content = archive.read(member)
            minidom.parseString(content)
            test.assertNotIn(b"parallel", content.lower(), member)


class ClientReport(unittest.TestCase):
    def setUp(self):
        self.work, self.out = tempfile.mkdtemp(), tempfile.mkdtemp()
        run("measure.py", REPORT, "--work", self.work, "--report-type", "monthly", "--changes", CHANGES, "--brand-campaigns", "Brand",
            "--target-cpa", "40", "--target-spend", "16000", "--client", "Northside Plumbing", "--prepared", "2026-11-13")
        with open(os.path.join(self.work, "numbers.json"), encoding="utf-8") as handle:
            self.data = json.load(handle)
        self.n = self.data["numbers"]

    def tearDown(self):
        shutil.rmtree(self.work)
        shutil.rmtree(self.out)

    def use(self, name, edit=None):
        if isinstance(name, dict):
            narrative = name
        else:
            with open(os.path.join(EXPORTS, name), encoding="utf-8") as handle:
                narrative = json.load(handle)
        if edit:
            edit(narrative)
        with open(os.path.join(self.work, "narrative.json"), "w", encoding="utf-8") as handle:
            json.dump(narrative, handle)

    def test_planted_problems_are_found(self):
        scopes = {s["name"]: s for s in self.data["scopes"]}
        self.assertEqual(scopes["Drain Cleaning | Search"]["status"], "Paused")
        self.assertTrue(any("Drain Cleaning | Search" in note and "not as a decline" in note for note in self.data["notes"]))
        self.assertEqual(self.n["c3.last_cost_day"]["value"], "2026-10-19")
        card = {r["kpi"]: r["status"] for r in self.data["scorecard"]}
        self.assertEqual(card["Cost / conv."], "At or better than target")
        self.assertEqual(card["Cost / conv., without brand"], "Above target")
        heaters = scopes["Plumbing | Water Heaters"]["id"]
        declines = [sid for sid in self.data["movers"]["conv"] if self.n["%s.conv.delta_prev" % sid]["value"] < 0]
        self.assertEqual(declines[0], heaters)
        bid_change = next(c for c in self.data["changes"]["items"] if c["campaign"] == "Plumbing | Water Heaters")
        self.assertEqual(bid_change["date"], "2026-10-06")
        self.assertEqual(self.n["count.changes.cur"]["value"], 5)
        self.assertEqual(self.n["count.changes.system"]["value"], 1)

    def test_numbers_reconcile_with_the_file(self):
        self.assertTrue(self.data["reconcile"]["matches"])
        cost = conversions = 0.0
        with open(REPORT, encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))
        header = rows[2]
        cost_at, conv_at = header.index("Cost"), header.index("Conversions")
        for row in rows[3:]:
            if row and row[0].startswith("2026-10-") and not row[1].startswith("Total"):
                cost += float(row[cost_at].replace(",", ""))
                conversions += float(row[conv_at].replace(",", ""))
        self.assertAlmostEqual(self.n["acct.cost.cur"]["value"], cost, places=2)
        self.assertAlmostEqual(self.n["acct.conv.cur"]["value"], conversions, places=2)
        campaigns = [s["id"] for s in self.data["scopes"] if s["kind"] == "campaign"]
        self.assertAlmostEqual(sum(self.n[c + ".cost.cur"]["value"] for c in campaigns), cost, places=2)
        self.assertEqual(self.data["periods"]["current"], ["2026-10-01", "2026-10-31"])
        self.assertEqual(self.data["periods"]["last_year"], ["2025-10-01", "2025-10-31"])

    def test_first_draft_is_refused_and_nothing_is_written(self):
        self.use("example-narrative-first-draft.json")
        done = call("fact_check.py", "--work", self.work)
        self.assertNotEqual(done.returncode, 0)
        with open(os.path.join(self.work, "checked.json"), encoding="utf-8") as handle:
            checked = json.load(handle)
        statuses = {r["raw"]: r["status"] for r in checked["results"]}
        self.assertEqual(statuses["{acct.conv.chg_prev}"], "contradicted")
        self.assertEqual(statuses["35.10"], "wrong_value")
        self.assertEqual(statuses["{c1.conv.chg_prev}"], "contradicted")
        self.assertTrue(any("is empty" in p for p in checked["problems"]))
        self.assertTrue(any('"leaderboard"' in p for p in checked["problems"]))
        refused = call("write_report.py", "--work", self.work, "--out", self.out)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("did not pass", refused.stderr)
        self.assertEqual(os.listdir(self.out), [])

    def test_checked_report_is_written_with_names_and_no_vendor_name(self):
        self.use("example-narrative.json")
        run("fact_check.py", "--work", self.work)
        printed = run("write_report.py", "--work", self.work, "--out", self.out, "--agency", "Harbor Search Partners")
        self.assertLessEqual(len(printed.strip().splitlines()), 3)
        self.assertEqual(sorted(os.listdir(self.out)), ["client-report-tables.xlsx", "client-report.docx", "client-report.md", "report-numbers.json"])
        valid_zip_xml(self, os.path.join(self.out, "client-report.docx"))
        valid_zip_xml(self, os.path.join(self.out, "client-report-tables.xlsx"))
        with zipfile.ZipFile(os.path.join(self.out, "client-report.docx")) as archive:
            body = archive.read("word/document.xml").decode("utf-8")
        for text in ("Northside Plumbing", "Harbor Search Partners", self.n["acct.cost.cur"]["display"], "What these numbers cannot show"):
            self.assertIn(text, body)
        with open(os.path.join(self.out, "client-report.md"), encoding="utf-8") as handle:
            md = handle.read()
        self.assertNotIn("{", md)
        self.assertIn("Conversions rose %s while cost fell %s." % (self.n["acct.conv.chg_prev"]["display"].lstrip("+"),
                                                                  self.n["acct.cost.chg_prev"]["display"].lstrip("-")), md)
        self.assertIn("October 1, 2026 to October 31, 2026", md)
        self.assertTrue(md.startswith("# Northside Plumbing: Google Ads, October 2026\n"))
        self.assertIn("prepared by Harbor Search Partners on November 13, 2026", md)
        self.assertIn("Return on ad spend (conv. value / cost)", md)
        self.assertIn("convert cheaply by nature", md)
        self.assertLess(md.index("### Account without brand"), md.index("### Account\n"))
        for name in os.listdir(self.out):
            if not name.endswith((".docx", ".xlsx")):
                with open(os.path.join(self.out, name), encoding="utf-8") as handle:
                    self.assertNotIn("parallel", handle.read().lower(), name)

    def test_the_written_report_passes_its_own_fact_check(self):
        self.use("example-narrative.json")
        run("fact_check.py", "--work", self.work)
        run("write_report.py", "--work", self.work, "--out", self.out)
        check = os.path.join(self.out, "check")
        run("fact_check.py", "--work", self.work, "--report", os.path.join(self.out, "client-report.docx"), "--out", check)
        with open(os.path.join(check, "fact-check.json"), encoding="utf-8") as handle:
            results = json.load(handle)["results"]
        self.assertGreater(len(results), 100)
        self.assertEqual([r for r in results if r["status"] != "traced"], [])
        valid_zip_xml(self, os.path.join(check, "fact-check.xlsx"))

    def test_write_refuses_a_narrative_changed_after_the_check(self):
        self.use("example-narrative.json")
        run("fact_check.py", "--work", self.work)
        self.use("example-narrative.json", lambda n: n["sections"][0].update(text="Cost rose 50% in October."))
        refused = call("write_report.py", "--work", self.work, "--out", self.out)
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("changed after the last fact check", refused.stderr)

    def test_a_report_someone_wrote_is_fact_checked(self):
        run("fact_check.py", "--work", self.work, "--report", os.path.join(EXPORTS, "draft-report-to-check.md"), "--out", self.out)
        with open(os.path.join(self.out, "fact-check.json"), encoding="utf-8") as handle:
            results = {r["raw"]: r for r in json.load(handle)["results"]}
        self.assertEqual(results[self.n["acct.cpa.chg_prev"]["display"].lstrip("+-")]["status"], "contradicted")
        self.assertEqual(results[self.n["c2.conv.chg_ly"]["display"].lstrip("+-")]["status"], "wrong_comparison")
        self.assertEqual((results["18%"]["status"], results["18%"]["id"]), ("wrong_value", "c3.cost.chg_prev"))
        self.assertEqual((results["9.4x"]["status"], results["9.4x"]["id"]), ("wrong_value", "acct.roas.cur"))
        with open(os.path.join(self.out, "fact-check.md"), encoding="utf-8") as handle:
            summary = handle.read()
        self.assertIn("- Verified: 5.", summary)
        self.assertIn("Dates, counted apart: 4 found", summary)
        self.assertEqual(results[self.n["acct.cost.cur"]["display"]]["status"], "traced")
        self.assertEqual(results["40.00"]["id"], "target.cpa")
        valid_zip_xml(self, os.path.join(self.out, "fact-check.xlsx"))

    def test_cited_ids_are_checked_for_direction_only(self):
        sentences = ["Without Brand, cost per conversion was {nb.cpa.cur}.",
                     "With Brand, cost per conversion was {acct.cpa.cur}.",
                     "Plumbing | Emergency took {c1.cost.share_cur} of account cost.",
                     "September had {period.prev.days} days.",
                     "Google's systems added {chg3.n1} keywords, and Drain Cleaning | Search cost fell {c3.cost.delta_prev.abs}.",
                     "Account conversions fell {acct.conv.chg_prev}."]
        self.use({"title": "Test", "sections": [{"heading": "Summary", "text": "", "bullets": sentences, "tables": []}]})
        done = call("fact_check.py", "--work", self.work)
        with open(os.path.join(self.work, "checked.json"), encoding="utf-8") as handle:
            statuses = [r["status"] for r in json.load(handle)["results"]]
        self.assertEqual(statuses, ["traced"] * 6 + ["contradicted"])
        self.assertNotEqual(done.returncode, 0)

    def test_a_target_far_from_the_actual_must_be_confirmed(self):
        for confirm in ([], ["--confirm-targets"]):
            run("measure.py", REPORT, "--work", self.work, "--report-type", "monthly", "--brand-campaigns", "Brand", "--target-spend", "9000", *confirm)
            with open(os.path.join(self.work, "numbers.md"), encoding="utf-8") as handle:
                self.assertIn("CHECK THE TARGET", handle.read())
            self.use({"title": "Test", "sections": [{"heading": "Spend", "text": "Spend was {score.cost.diff_pct} above the target of {target.cost}.",
                                                    "tables": ["scorecard"]}]})
            done = call("fact_check.py", "--work", self.work)
            self.assertEqual(done.returncode != 0, not confirm, done.stdout)
        run("write_report.py", "--work", self.work, "--out", self.out)
        with open(os.path.join(self.out, "client-report.md"), encoding="utf-8") as handle:
            md = handle.read()
        self.assertIn("the ones you gave", md)
        self.assertNotIn("agreed", md)

    def test_brand_outlier_needs_the_figure_without_brand(self):
        self.assertIsNotNone(self.data["brand_outlier"])
        self.assertIn("brand.cpa.cur", self.n)
        self.use({"title": "Test", "sections": [{"heading": "Summary", "text": "Cost per conversion was {acct.cpa.cur}.", "tables": []}]})
        done = call("fact_check.py", "--work", self.work)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("give the figure without brand", done.stdout)

    def test_a_draft_for_another_period_is_stopped(self):
        other = os.path.join(self.work, "september")
        run("measure.py", REPORT, "--work", other, "--report-type", "fact-check", "--current", "2026-09-01:2026-09-30")
        done = call("fact_check.py", "--work", other, "--report", os.path.join(EXPORTS, "draft-report-to-check.md"), "--out", self.out)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("--current 2026-10-01:2026-10-31", done.stderr)
        bare = os.path.join(self.work, "bare.md")
        with open(bare, "w", encoding="utf-8") as handle:
            handle.write("Cost rose 3.8% and conversions rose 1.5%.\n")
        done = call("fact_check.py", "--work", self.work, "--report", bare, "--out", self.out)
        self.assertIn("--current", done.stderr)
        run("fact_check.py", "--work", self.work, "--report", bare, "--out", self.out, "--current", "2026-10-01:2026-10-31")

    def test_change_lines_name_campaign_and_ad_group(self):
        with open(os.path.join(self.work, "numbers.md"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("in Plumbing | Emergency, ad group Emergency: 6 keywords added", text)
        self.assertIn("chg1.n2 = 240.00", text)

    def test_missing_column_and_uncovered_period_are_plain_messages(self):
        path = os.path.join(self.work, "short.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('Campaign report\n"October 1, 2026 - October 31, 2026"\nDay,Campaign,Clicks,Impr.\n2026-10-01,Brand,4,12\n')
        done = call("measure.py", path, "--work", self.work, "--report-type", "monthly")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("Cost", done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        early = call("measure.py", REPORT, "--work", self.work, "--report-type", "executive", "--current", "2025-07-01:2025-07-31")
        self.assertIn("does not cover the previous period", early.stderr)
        self.assertNotIn("Traceback", early.stderr)

    def test_week_and_quarter_periods(self):
        week = os.path.join(self.work, "week")
        run("measure.py", REPORT, "--work", week, "--report-type", "weekly")
        with open(os.path.join(week, "numbers.json"), encoding="utf-8") as handle:
            periods = json.load(handle)["periods"]
        self.assertEqual(periods["current"], ["2026-11-06", "2026-11-12"])
        self.assertEqual(periods["previous"], ["2026-10-30", "2026-11-05"])
        last_year = dt.date.fromisoformat(periods["last_year"][0])
        self.assertEqual(last_year.weekday(), dt.date(2026, 11, 6).weekday())
        quarter = os.path.join(self.work, "quarter")
        run("measure.py", REPORT, "--work", quarter, "--report-type", "quarterly")
        with open(os.path.join(quarter, "numbers.json"), encoding="utf-8") as handle:
            periods = json.load(handle)["periods"]
        self.assertEqual(periods["current"], ["2026-07-01", "2026-09-30"])
        self.assertEqual(periods["previous"], ["2026-04-01", "2026-06-30"])
        self.assertEqual(periods["last_year"], ["2025-07-01", "2025-09-30"])

    def test_a_whole_month_given_as_dates_is_compared_with_the_month_before(self):
        # A draft "compared with September" was checked against August 31 to September 30,
        # which called a right figure wrong and missed a wrong direction.
        for current, previous in (("2026-10-01:2026-10-31", ["2026-09-01", "2026-09-30"]),
                                  ("2026-07-01:2026-09-30", ["2026-04-01", "2026-06-30"]),
                                  ("2026-10-05:2026-10-18", ["2026-09-21", "2026-10-04"])):
            work = os.path.join(self.work, current.replace(":", "_"))
            run("measure.py", REPORT, "--work", work, "--report-type", "fact-check", "--current", current)
            with open(os.path.join(work, "numbers.json"), encoding="utf-8") as handle:
                self.assertEqual(json.load(handle)["periods"]["previous"], previous, current)


class Playbooks(unittest.TestCase):
    def test_every_playbook_named_exists_and_every_file_is_named(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w.-]+\.md)", handle.read()))
        files = {name for name in os.listdir(os.path.join(SKILL, "playbooks")) if not name.startswith(".")}
        self.assertEqual(named, files)
        # measure.py writes the playbook for each report type into numbers.json.
        with open(os.path.join(SKILL, "scripts", "measure.py"), encoding="utf-8") as handle:
            in_script = set(re.findall(r"playbooks/([\w.-]+\.md)", handle.read()))
        self.assertLessEqual(in_script, files)


if __name__ == "__main__":
    unittest.main()
