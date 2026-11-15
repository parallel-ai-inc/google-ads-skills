"""Tests for the Performance Max skill: what a customer would lose if it broke.

    python3 -m unittest tests/test_performance_max.py
"""
import csv
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

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "performance-max-for-google-ads")
EXPORTS = os.path.join(ROOT, "examples", "exports", "performance-max")
REPORTS = {"--campaigns": "campaigns-report.csv", "--asset-groups": "asset-groups-report.csv", "--channels": "channel-performance.csv",
           "--search-terms": "search-terms-report.csv", "--products": "products-report.csv", "--prices": "price-benchmarks.csv"}
OUT = None
REVIEW = None


def call(script, *args):
    return subprocess.run([sys.executable, os.path.join(SKILL, "scripts", script)] + list(args), capture_output=True, text=True, cwd=SKILL)


def run(script, *args):
    done = call(script, *args)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def all_reports():
    args = []
    for flag, name in REPORTS.items():
        args += [flag, os.path.join(EXPORTS, name)]
    return args + ["--brand", "northside plumbing, northside", "--target-roas", "400"]


def setUpModule():
    global OUT, REVIEW
    for command in ([os.path.join(ROOT, "tools", "build.py"), "performance-max-for-google-ads"],
                    [os.path.join(ROOT, "examples", "make_samples_performance-max.py")]):
        subprocess.run([sys.executable] + command, check=True, capture_output=True)
    OUT = tempfile.mkdtemp()
    run("audit.py", "--out", OUT, *all_reports())
    with open(os.path.join(OUT, "pmax-review.json"), encoding="utf-8") as handle:
        REVIEW = json.load(handle)


def tearDownModule():
    shutil.rmtree(OUT)


def finding(title_part):
    return next(f for f in REVIEW["findings"] if title_part in f["title"])


class PlantedProblems(unittest.TestCase):
    def test_brand_searches_carry_a_large_share_of_conversions(self):
        brand = REVIEW["parts"]["search_terms"]["brand"]
        self.assertEqual(brand["searches"], 3)
        self.assertAlmostEqual(brand["share_of_conversions"], 44 / 91)
        self.assertIn("Brand exclusions", finding("Brand searches")["surface"])

    def test_spend_in_asset_groups_below_good(self):
        below = REVIEW["parts"]["asset_groups"]["below_good"]
        self.assertEqual(sorted(below["names"]), ["Drain Tools", "Water Heaters | General"])
        self.assertAlmostEqual(below["cost"], 5000.00)
        self.assertIn("campaign still learning", finding("below Good")["detail"])

    def test_drain_tools_spend_without_converting_and_sit_above_benchmark(self):
        products = REVIEW["parts"]["products"]
        self.assertEqual({p["product_type"] for p in products["over_line"]}, {"Drain Tools"})
        self.assertAlmostEqual(products["over_line_cost"], 1410.00)
        detail = finding("Products with cost and no conversions")["detail"]
        for part in ("6 products had cost and no conversions, costing 1,455.00", "5 of them spent at least 84.51",
                     "5 of those that spent enough to judge are priced above their benchmark"):
            self.assertIn(part, detail)

    def test_every_search_with_no_conversions_is_shown_for_judging(self):
        searches = REVIEW["parts"]["search_terms"]
        self.assertEqual(len(searches["no_conv_terms"]), 11)
        below = {t["search_term"]: t for t in searches["below_line_with_word"]}
        self.assertEqual(below["plumber jobs denver"]["candidate_word"], "jobs")
        self.assertFalse(below["plumber jobs denver"]["over_line"])
        self.assertIn("The other 6 cost 335.00", finding("Non brand searches")["detail"])

    def test_words_that_name_the_business_are_never_negative_candidates(self):
        searches = REVIEW["parts"]["search_terms"]
        candidates = {g["phrase"] for g in searches["waste_words"]}
        self.assertEqual({g["phrase"] for g in searches["held_back_words"]} & {"drain", "snake"}, {"drain", "snake"})
        self.assertFalse(candidates & {"drain", "snake"})
        self.assertIn("jobs", candidates)

    def test_brand_overlap_with_a_search_campaign_points_to_the_priority_rule(self):
        detail, rule = finding("Brand searches")["detail"], finding("Brand searches")["rule"]
        self.assertIn("Brand (its keywords include", detail)
        self.assertIn("of the listed Performance Max search cost", detail)
        self.assertIn("exact match identical to the search is preferred over Performance Max", rule)

    def test_campaigns_with_different_goals_are_judged_apart(self):
        camp = REVIEW["parts"]["campaigns"]
        self.assertTrue(camp["value_mixed"])
        goals = {c["campaign"]: c["goal"] for c in camp["campaigns"]}
        self.assertEqual(goals["PMax | Plumbing Supplies"], "conv. value / cost")
        self.assertEqual(goals["PMax | Water Heater Leads"], "cost / conv.")
        with open(os.path.join(OUT, "pmax-review.md"), encoding="utf-8") as handle:
            self.assertIn("Judge each against its own goal", handle.read())

    def test_each_campaign_is_set_against_the_target_for_its_own_goal(self):
        camp = {c["campaign"]: c for c in REVIEW["parts"]["campaigns"]["campaigns"]}
        self.assertEqual(camp["PMax | Plumbing Supplies"]["against_target"], "worse than target by 5.3%")
        self.assertEqual(camp["PMax | Water Heater Leads"]["against_target"], "no target given")
        work = tempfile.mkdtemp()
        try:
            run("audit.py", "--out", work, "--campaigns", os.path.join(EXPORTS, REPORTS["--campaigns"]), "--target-cpa", "150", "--target-roas", "400")
            with open(os.path.join(work, "pmax-review.json"), encoding="utf-8") as handle:
                camp = {c["campaign"]: c for c in json.load(handle)["parts"]["campaigns"]["campaigns"]}
            self.assertEqual(camp["PMax | Water Heater Leads"]["against_target"], "worse than target by 14.3% (still learning)")
            self.assertEqual(camp["PMax | Plumbing Supplies"]["target"], 4.0)
            self.assertEqual(camp["PMax | Spring Promo"]["against_target"], "paused, not judged")
        finally:
            shutil.rmtree(work)

    def test_an_expensive_channel_is_a_question_and_never_a_cut(self):
        display = [f for f in REVIEW["findings"] if f["area"] == "Channels" and f["title"].startswith("Google Display Network")]
        self.assertEqual(len(display), 2)
        for f in display:
            self.assertEqual(f["kind"], "Question")
            self.assertTrue(f["no_fix"])
        self.assertFalse(any("Spring Promo" in f["title"] for f in display), "a paused campaign was judged")
        work = tempfile.mkdtemp()
        try:
            path = os.path.join(work, "actions.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"actions": [{"finding": display[0]["id"], "kind": "fix", "action": "Exclude Display", "label": "Official", "priority": 1}]}, handle)
            refused = call("add_actions.py", "--out", OUT, "--actions", path)
            self.assertNotEqual(refused.returncode, 0)
            self.assertIn("marginal return", refused.stderr)
            self.assertNotIn("Traceback", refused.stderr)
        finally:
            shutil.rmtree(work)


class Reconciles(unittest.TestCase):
    def test_rows_match_the_files_own_totals(self):
        parts = REVIEW["parts"]
        for kind in ("campaigns", "asset_groups", "channels", "products"):
            self.assertEqual(parts[kind]["reconcile"]["difference"], 0.0, kind)
        self.assertEqual(parts["campaigns"]["other_types_left_out"], 4)
        searches = parts["search_terms"]
        self.assertAlmostEqual(searches["total"]["cost"] + searches["not_listed_cost"], searches["reconcile"]["file_cost"])

    def test_reports_agree_with_the_campaign_report(self):
        rows = {r["report"]: r for r in REVIEW["consistency"]["reports"]}
        self.assertEqual(rows["Asset group report"]["difference"], 0.0)
        self.assertEqual(rows["Channel performance report"]["difference"], 0.0)
        self.assertFalse(REVIEW["consistency"]["date_ranges_differ"])
        self.assertFalse(any(f["kind"] == "Data check" and "does not add up" in f["title"] for f in REVIEW["findings"]))

    def test_a_utf16_tab_download_gives_the_same_numbers(self):
        work = tempfile.mkdtemp()
        try:
            with open(os.path.join(EXPORTS, "products-report.csv"), encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))
            path = os.path.join(work, "products.csv")
            with open(path, "w", encoding="utf-16", newline="") as handle:
                csv.writer(handle, delimiter="\t").writerows(rows)
            run("audit.py", "--out", work, "--products", path)
            with open(os.path.join(work, "pmax-review.json"), encoding="utf-8") as handle:
                again = json.load(handle)
            self.assertAlmostEqual(again["parts"]["products"]["total"]["cost"], REVIEW["parts"]["products"]["total"]["cost"])
        finally:
            shutil.rmtree(work)


class PlainMessages(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_a_missing_column_is_a_plain_message(self):
        path = os.path.join(self.work, "products.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('Products report\n"October 14, 2026 - November 12, 2026"\nItem ID,Title,Clicks,Conversions\nab-1,Drain Snake,4,0\n')
        done = call("audit.py", "--out", self.work, "--products", path)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("Cost", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_a_wrong_campaign_name_is_refused(self):
        done = call("audit.py", "--out", self.work, "--campaigns", os.path.join(EXPORTS, "campaigns-report.csv"), "--campaign", "Brand")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("PMax | Plumbing Supplies", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_missing_reports_are_named_with_what_unlocks_them(self):
        run("audit.py", "--out", self.work, "--products", os.path.join(EXPORTS, "products-report.csv"))
        with open(os.path.join(self.work, "pmax-review.md"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertIn("Spend in asset groups below Good. Needs the asset group report", text)
        self.assertIn("Price competitiveness. Needs the price benchmarks from Merchant Center", text)

    def test_a_clone_of_an_unknown_campaign_is_refused(self):
        done = call("launch_checklist.py", "--out", self.work, "--review", os.path.join(OUT, "pmax-review.json"), "--source", "PMax | Shop")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("PMax | Plumbing Supplies", done.stderr)


class Judgments(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()
        run("audit.py", "--out", self.work, *all_reports())
        with open(os.path.join(self.work, "pmax-review.json"), encoding="utf-8") as handle:
            self.review = json.load(handle)

    def tearDown(self):
        shutil.rmtree(self.work)

    def add(self, content):
        path = os.path.join(self.work, "actions.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(content, handle)
        return call("add_actions.py", "--out", self.work, "--actions", path)

    def test_a_converting_or_brand_search_is_never_a_negative(self):
        for search, word in (("kitchen faucet with sprayer", "converted"), ("northside plumbing supply", "brand search")):
            done = self.add({"negatives": [{"search": search, "reason": "Not wanted"}]})
            self.assertNotEqual(done.returncode, 0)
            self.assertIn(word, done.stderr)

    def test_a_mixed_label_needs_each_sentence_labelled(self):
        fid = self.review["findings"][0]["id"]
        done = self.add({"actions": [{"finding": fid, "kind": "investigate", "action": "Wait two weeks.", "label": "Both", "priority": 1}]})
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("Official:", done.stderr)

    def test_negatives_judged_irrelevant_are_listed_with_cost(self):
        done = self.add({"negatives": [{"search": "plumber jobs denver", "campaign": "PMax | Water Heater Leads", "reason": "Job seekers"},
                                       {"search": "free water heater", "reason": "Free products"}]})
        self.assertEqual(done.returncode, 0, done.stderr)
        with open(os.path.join(self.work, "pmax-review.json"), encoding="utf-8") as handle:
            negatives = json.load(handle)["negatives"]
        self.assertEqual([(n["negative"], n["cost"]) for n in negatives], [("[plumber jobs denver]", 95.0), ("[free water heater]", 70.0)])
        with zipfile.ZipFile(os.path.join(self.work, "pmax-review.xlsx")) as archive:
            self.assertIn(b"Negatives to review", archive.read("xl/workbook.xml"))

    def test_a_clone_of_the_weakest_group_is_fix_first_and_holds_back_its_own_words(self):
        done = call("launch_checklist.py", "--out", self.work, "--review", os.path.join(self.work, "pmax-review.json"),
                    "--source", "PMax | Plumbing Supplies", "--name", "PMax | Drain Tools")
        self.assertEqual(done.returncode, 0, done.stderr)
        text = done.stdout
        self.assertIn("**Go or no go: fix first.**", text)
        self.assertIn("Product group Drain Tools (Product type (1st level)) is the weakest of 5", text)
        candidates = next(line for line in text.splitlines() if "to review as negatives" in line)
        self.assertNotIn('"drain"', candidates)
        self.assertNotIn('"snake"', candidates)
        self.assertIn('Held back, never to be added as negatives here: "drain"', text)


class Deliverables(unittest.TestCase):
    def test_actions_checklist_and_files_carry_no_vendor_name(self):
        work = tempfile.mkdtemp()
        try:
            run("audit.py", "--out", work, *all_reports())
            with open(os.path.join(work, "pmax-review.json"), encoding="utf-8") as handle:
                review = json.load(handle)
            brand = next(f["id"] for f in review["findings"] if f["title"].startswith("Brand searches"))
            path = os.path.join(work, "actions.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump({"actions": [{"finding": brand, "kind": "investigate", "action": "Confirm whether Search should own brand searches",
                                        "label": "Practitioner rule", "priority": 1}]}, handle)
            run("add_actions.py", "--out", work, "--actions", path)
            os.remove(path)
            run("launch_checklist.py", "--out", work, "--review", os.path.join(work, "pmax-review.json"), "--source", "PMax | Plumbing Supplies",
                "--daily-budget", "150", "--start", "2026-11-20")
            with open(os.path.join(work, "pmax-review.md"), encoding="utf-8") as handle:
                self.assertIn("Confirm whether Search should own brand searches", handle.read())
            with open(os.path.join(work, "pmax-launch-checklist.md"), encoding="utf-8") as handle:
                checklist = handle.read()
            self.assertIn("2026-12-31: earliest full judgment", checklist)
            self.assertIn("1.65 conversions a day", checklist)
            for name in os.listdir(work):
                full = os.path.join(work, name)
                if name.endswith(".xlsx"):
                    with zipfile.ZipFile(full) as archive:
                        for member in archive.namelist():
                            content = archive.read(member)
                            minidom.parseString(content)
                            self.assertNotIn(b"parallel", content.lower(), member)
                else:
                    with open(full, encoding="utf-8") as handle:
                        self.assertNotIn("parallel", handle.read().lower(), name)
        finally:
            shutil.rmtree(work)

    def test_every_playbook_is_named_in_skill_md_and_exists(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w.-]+\.md)", handle.read()))
        present = set(os.listdir(os.path.join(SKILL, "playbooks")))
        self.assertTrue(named, "SKILL.md names no playbook")
        self.assertEqual(named - present, set(), "named in SKILL.md but missing")
        self.assertEqual(present - named, set(), "in playbooks/ but not named in SKILL.md")


if __name__ == "__main__":
    unittest.main()
