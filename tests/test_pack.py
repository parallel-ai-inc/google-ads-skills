"""Tests for the engine and the three example skills.

    python3 -m unittest discover -s tests -v
"""
import csv
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from xml.dom import minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "engine"))
from gads import dates, io, metrics, negatives, outputs, xlsx  # noqa: E402

EXPORTS = os.path.join(ROOT, "examples", "exports")
SEARCH = os.path.join(ROOT, "skills", "search-terms-for-google-ads", "scripts")
BUDGET = os.path.join(ROOT, "skills", "budgets-and-forecasts-for-google-ads", "scripts")
DIAG = os.path.join(ROOT, "skills", "performance-diagnosis-for-google-ads", "scripts")


def run(script, *args):
    done = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def setUpModule():
    run(os.path.join(ROOT, "tools", "build.py"))
    run(os.path.join(ROOT, "examples", "make_samples.py"))


class Numbers(unittest.TestCase):
    def test_google_formats(self):
        cases = {"1,234.50": 1234.5, "$1,234.50": 1234.5, "US$12.30": 12.3, "12.3%": 12.3, "--": None, "": None,
                 " --": None, "< 10%": None, "> 90%": 90.0, "1.234,50": 1234.5, "12,5": 12.5, "1,234": 1234.0, "0": 0.0}
        for text, expected in cases.items():
            self.assertEqual(io.to_number(text), expected, text)

    def test_dates(self):
        self.assertEqual(dates.parse_day("2026-11-12").isoformat(), "2026-11-12")
        self.assertEqual(dates.parse_day("Nov 2, 2026, 4:41:55 PM").isoformat(), "2026-11-02")
        self.assertEqual(dates.parse_day("November 12, 2026").isoformat(), "2026-11-12")
        self.assertIsNone(dates.parse_day("Total"))

    def test_lever_shares_add_up(self):
        shares = metrics.log_shares({"a": 120.0, "b": 0.05, "c": 0.08}, {"a": 100.0, "b": 0.06, "c": 0.16})
        self.assertAlmostEqual(sum(shares.values()), 1.0)
        self.assertEqual(max(shares, key=lambda k: abs(shares[k])), "c")


class Reading(unittest.TestCase):
    def test_title_rows_totals_and_dashes(self):
        meta, rows = io.read_report(os.path.join(EXPORTS, "search-terms-report.csv"))
        self.assertEqual(meta["title_rows"][0], "Search terms report")
        self.assertEqual(len(rows), 34)
        self.assertTrue(any("Total: Search terms" == k for k in meta["totals"]))
        self.assertAlmostEqual(sum(r["cost"] for r in rows), meta["totals"]["Total: Search terms"]["cost"], places=2)

    def test_utf16_tab_file(self):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "report.tsv")
            lines = ["Search terms report", "Nov 1, 2026 - Nov 12, 2026", "Search term\tCampaign\tClicks\tCost\tConversions",
                     "red shoes\tShoes\t1,204\t$2,410.50\t --", "Total: Search terms\t--\t1,204\t$2,410.50\t0.00"]
            with open(path, "w", encoding="utf-16") as handle:
                handle.write("\n".join(lines))
            meta, rows = io.read_report(path)
            self.assertEqual(rows[0]["clicks"], 1204.0)
            self.assertEqual(rows[0]["cost"], 2410.5)
            self.assertIsNone(rows[0]["conversions"])
        finally:
            shutil.rmtree(folder)

    def test_missing_header_is_a_plain_message(self):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "notes.csv")
            with open(path, "w") as handle:
                handle.write("hello,world\n1,2\n")
            with self.assertRaises(ValueError):
                io.read_report(path)
        finally:
            shutil.rmtree(folder)


class NegativeRules(unittest.TestCase):
    def test_no_close_variants(self):
        # Google's own example: "flowers" blocks "red flowers" but not "red flower".
        self.assertTrue(negatives.blocks("flowers", "broad", "red flowers"))
        self.assertFalse(negatives.blocks("flowers", "broad", "red flower"))

    def test_match_types(self):
        self.assertTrue(negatives.blocks("running shoes", "broad", "shoes for running"))
        self.assertFalse(negatives.blocks("running shoes", "phrase", "shoes for running"))
        self.assertTrue(negatives.blocks("running shoes", "phrase", "blue running shoes sale"))
        self.assertFalse(negatives.blocks("running shoes", "exact", "blue running shoes"))
        self.assertTrue(negatives.blocks("Running Shoes", "exact", "running shoes"))

    def test_scope(self):
        negative = {"level": "campaign", "campaign": "A"}
        self.assertTrue(negatives.in_scope(negative, {"campaign": "A"}))
        self.assertFalse(negatives.in_scope(negative, {"campaign": "B"}))
        self.assertTrue(negatives.in_scope({"level": "account"}, {"campaign": "B"}))

    def test_editor_values(self):
        self.assertEqual(outputs.editor_criterion_type("phrase", "campaign"), "Campaign Negative Phrase")
        self.assertEqual(outputs.editor_criterion_type("exact", "ad_group"), "Negative Exact")
        self.assertEqual(negatives.symbol_form("ice cream", "phrase"), '-"ice cream"')


class Workbooks(unittest.TestCase):
    def test_workbook_is_valid_and_never_runs_a_formula(self):
        folder = tempfile.mkdtemp()
        try:
            book = xlsx.Workbook()
            book.add_sheet("Review: all/terms", ["Search", "Cost"], [["=HYPERLINK(\"http://x\")", 12.5], ["a & b <c>", None]], formats={1: "money"})
            path = book.save(os.path.join(folder, "book.xlsx"))
            with zipfile.ZipFile(path) as archive:
                for name in archive.namelist():
                    minidom.parseString(archive.read(name))
                sheet = archive.read("xl/worksheets/sheet1.xml").decode()
            self.assertIn('t="inlineStr"><is><t xml:space="preserve">=HYPERLINK', sheet)
            self.assertNotIn("<f>", sheet)
            meta, rows = None, None
            grid = io._grid_from_xlsx(path)
            self.assertEqual(grid[0], ["Search", "Cost"])
            self.assertEqual(float(grid[1][1]), 12.5)
        finally:
            shutil.rmtree(folder)


class SearchTermReview(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        self.out = tempfile.mkdtemp()
        run(os.path.join(SEARCH, "measure.py"), os.path.join(EXPORTS, "search-terms-report.csv"), "--work", self.work, "--brand", "northside")
        with open(os.path.join(self.work, "measured.json")) as handle:
            self.measured = json.load(handle)

    def tearDown(self):
        shutil.rmtree(self.work)
        shutil.rmtree(self.out)

    def term(self, text):
        return next(t for t in self.measured["terms"] if t["search_term"] == text)

    def write_verdicts(self, verdicts, negs):
        with open(os.path.join(self.work, "verdicts.json"), "w") as handle:
            json.dump({"verdicts": verdicts, "negatives": negs}, handle)

    def checked(self, *extra):
        run(os.path.join(SEARCH, "check_negatives.py"), "--work", self.work, *extra)
        with open(os.path.join(self.work, "checked.json")) as handle:
            return json.load(handle)

    def test_rows_reconcile_with_the_file_total(self):
        self.assertEqual(self.measured["reconcile"]["difference"], 0)
        self.assertEqual(self.term("northside plumbing reviews")["class"], "Keep")

    def test_a_negative_that_blocks_a_converting_search_is_rejected(self):
        self.write_verdicts([{"id": self.term("free plumbing course")["id"], "verdict": "Exclude", "reason": "training"}],
                            [{"text": "free", "match": "phrase", "level": "campaign", "campaign": "Plumbing | Emergency"}])
        result = self.checked()
        negative = result["negatives"][0]
        self.assertFalse(negative["passed"])
        self.assertIn("free estimate plumber", [hit["search_term"] for hit in negative["blocks_protected"]])

    def test_own_keywords_are_protected(self):
        self.write_verdicts([{"id": self.term("water heater repair jobs")["id"], "verdict": "Exclude", "reason": "jobs"}],
                            [{"text": "water heater repair", "match": "phrase", "level": "campaign", "campaign": "Plumbing | Water Heaters"}])
        result = self.checked("--keywords", os.path.join(EXPORTS, "keywords-report.csv"))
        self.assertTrue(result["negatives"][0]["blocks_keywords"])

    def test_a_converting_search_can_never_be_excluded(self):
        converting = self.term("emergency plumber near me")
        self.write_verdicts([{"id": converting["id"], "verdict": "Exclude", "reason": "wrong"}], [])
        result = self.checked()
        final = next(t for t in result["terms"] if t["id"] == converting["id"])
        self.assertEqual(final["verdict"], "Keep")
        self.assertTrue(any("cannot be Exclude" in p for p in result["problems"]))

    def test_outputs_refuse_untested_verdicts(self):
        jobs = self.term("plumbing jobs near me")
        self.write_verdicts([{"id": jobs["id"], "verdict": "Exclude", "reason": "jobs"}], [{"text": "jobs", "match": "broad", "level": "account"}])
        self.checked()
        self.write_verdicts([{"id": jobs["id"], "verdict": "Exclude", "reason": "edited after the test"}], [{"text": "plumbing", "match": "broad", "level": "account"}])
        done = subprocess.run([sys.executable, os.path.join(SEARCH, "write_outputs.py"), "--work", self.work, "--out", self.out], capture_output=True, text=True)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("Run check_negatives.py again", done.stderr + done.stdout)

    def test_files_are_written_and_carry_no_vendor_name(self):
        names = ("plumbing jobs near me", "plumber jobs hiring", "water heater repair jobs", "plumbing supply store")
        self.write_verdicts([{"id": self.term(name)["id"], "verdict": "Exclude", "reason": "not a customer"} for name in names],
                            [{"text": "jobs", "match": "broad", "level": "account"},
                             {"text": "supply store", "match": "phrase", "level": "campaign", "campaign": "Plumbing | Emergency"}])
        self.checked()
        run(os.path.join(SEARCH, "write_outputs.py"), "--work", self.work, "--out", self.out)
        with open(os.path.join(self.out, "negatives-for-google-ads-editor.csv")) as handle:
            editor = list(csv.reader(handle))
        self.assertEqual(editor[0], ["Campaign", "Ad Group", "Keyword", "Criterion Type"])
        self.assertEqual(editor[1], ["Plumbing | Emergency", "", "supply store", "Campaign Negative Phrase"])
        for name in ("search-term-review.md", "search-term-review.csv", "account-level-negatives.txt"):
            with open(os.path.join(self.out, name)) as handle:
                self.assertNotIn("parallel", handle.read().lower(), name)


class PacingAndDiagnosis(unittest.TestCase):
    def test_pacing(self):
        out = tempfile.mkdtemp()
        try:
            run(os.path.join(BUDGET, "pacing.py"), os.path.join(EXPORTS, "campaigns-by-day.csv"), "--out", out, "--exclude", "Brand")
            with open(os.path.join(out, "pacing.json")) as handle:
                result = json.load(handle)
            self.assertEqual((result["days_elapsed"], result["days_in_month"]), (12, 30))
            emergency = next(c for c in result["campaigns"] if c["campaign"] == "Plumbing | Emergency")
            self.assertAlmostEqual(emergency["monthly_limit"], 240 * 30.4)
            self.assertTrue(emergency["limited_by_budget"])
            self.assertEqual([r["campaign"] for r in result["receivers"]], ["Plumbing | Emergency"])
            total = sum(c["mtd_cost"] for c in result["campaigns"])
            self.assertAlmostEqual(result["account"]["mtd_cost"], total)
            # A campaign whose cost per conversion jumped is held out of any budget move.
            self.assertEqual(sorted(h["campaign"] for h in result["held"]), ["Drain Cleaning | Search", "Plumbing | Water Heaters"])
            self.assertNotIn("Plumbing | Water Heaters", [d["campaign"] for d in result["donors"]])
            capped = sum(min(c["forecast_recent"], c["monthly_limit"]) for c in result["campaigns"])
            self.assertAlmostEqual(result["account"]["forecast_billed"], capped)
        finally:
            shutil.rmtree(out)

    def test_diagnosis_finds_both_shifts_and_their_changes(self):
        out = tempfile.mkdtemp()
        try:
            run(os.path.join(DIAG, "compare.py"), os.path.join(EXPORTS, "campaigns-by-day.csv"), "--out", out, "--days", "10",
                "--changes", os.path.join(EXPORTS, "change-history.csv"))
            with open(os.path.join(out, "diagnosis.json")) as handle:
                result = json.load(handle)
            by_name = {c["scope"]: c for c in result["campaigns"]}
            heaters, drains = by_name["Plumbing | Water Heaters"], by_name["Drain Cleaning | Search"]
            self.assertEqual((heaters["main_lever"], heaters["shift_day"]), ("cvr", "2026-11-03"))
            self.assertEqual((drains["main_lever"], drains["shift_day"]), ("cpc", "2026-11-05"))
            self.assertIn("Target CPA", heaters["changes_before_shift"][0]["changes"])
            self.assertFalse(by_name["Brand"]["notable"])
            with open(os.path.join(out, "performance-diagnosis.md")) as handle:
                summary = handle.read()
            # The numbers the reply needs are in the summary, so nobody works them out by hand.
            self.assertIn("Conversion rate: 12.48% before, 5.76% now.", summary)
            self.assertIn("Amounts are in USD.", summary)
        finally:
            shutil.rmtree(out)


class OnePackForEveryStore(unittest.TestCase):
    """The Claude and OpenAI directories both bar software that serves advertisements,
    so one pack, with no promotional sentence, goes to every store."""

    def test_no_skill_or_playbook_promotes_a_product(self):
        provenance = ("Written by hand from Parallel AI's operating knowledge", "<!-- Generated ")
        found = []
        for folder, _, files in os.walk(os.path.join(ROOT, "skills")):
            for name in files:
                if not name.endswith(".md"):
                    continue
                path = os.path.join(folder, name)
                with open(path, encoding="utf-8") as handle:
                    for number, line in enumerate(handle, 1):
                        if ("withparallel" in line or "Parallel AI" in line) and not line.strip().startswith(provenance):
                            found.append("%s:%d" % (os.path.relpath(path, ROOT), number))
        self.assertEqual(found, [])

    def test_every_store_manifest_names_the_same_pack(self):
        def load(path):
            with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
                return json.load(handle)
        claude, cursor, gemini = load(".claude-plugin/plugin.json"), load(".cursor-plugin/plugin.json"), load("gemini-extension.json")
        for key in ("name", "version", "description"):
            self.assertEqual(claude[key], cursor[key], key)
            self.assertEqual(claude[key], gemini[key], key)
        self.assertEqual(load(".claude-plugin/marketplace.json")["plugins"][0]["name"], claude["name"])
        self.assertTrue(os.path.isfile(os.path.join(ROOT, cursor["logo"])))


if __name__ == "__main__":
    unittest.main()
