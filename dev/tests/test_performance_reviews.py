"""Tests for the performance reviews skill.

    python3 -m unittest dev/tests/test_performance_reviews.py
"""
import csv
import datetime
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
SKILL = os.path.join(ROOT, "skills", "performance-reviews-for-google-ads")
SCRIPTS = os.path.join(SKILL, "scripts")
EXPORTS = os.path.join(ROOT, "examples", "exports", "performance-reviews")
NOTES = os.path.join(ROOT, "examples", "output", "performance-reviews", "example-notes.json")
FILES = ["campaign-report-by-day.csv", "keyword-report.csv", "ads-report.csv", "campaign-report-by-device.csv",
         "landing-page-report.csv", "audience-report.csv", "location-report.csv", "ad-schedule-report.csv",
         "placement-report.csv", "video-report.csv"]


def run(script, *args, ok=True):
    done = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + list(args), capture_output=True, text=True, cwd=SKILL)
    if ok and done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done


def review(work, files=FILES, *extra):
    run("review.py", *([os.path.join(EXPORTS, f) if not os.path.isabs(f) else f for f in files] + ["--work", work] + list(extra)))
    with open(os.path.join(work, "review.json")) as handle:
        return json.load(handle)


def without_column(source, column, target):
    with open(source, newline="") as handle:
        rows = list(csv.reader(handle))
    drop = rows[2].index(column)
    with open(target, "w", newline="") as handle:
        csv.writer(handle).writerows([r[:drop] + r[drop + 1:] if len(r) > drop else r for r in rows])
    return target


def setUpModule():
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "tools", "build.py"), "performance-reviews-for-google-ads"], check=True, capture_output=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "samples", "make_samples_performance-reviews.py")], check=True, capture_output=True)


class AllReviews(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work, cls.out = tempfile.mkdtemp(), tempfile.mkdtemp()
        cls.result = review(cls.work, FILES, "--brand", "northside", "--brand-campaign", "Brand")
        cls.r = cls.result["reviews"]
        shutil.copy(NOTES, os.path.join(cls.work, "notes.json"))
        cls.written = run("write_report.py", "--work", cls.work, "--out", cls.out).stdout

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work)
        shutil.rmtree(cls.out)

    def test_every_review_runs_and_every_file_reconciles(self):
        self.assertEqual(set(self.r), {"weekly", "keywords", "quality_score", "ads", "devices", "landing_pages", "audiences",
                                       "locations", "schedule", "placements", "videos"})
        self.assertEqual(self.result["not_run"], [])
        for entry in self.result["files"]:
            self.assertTrue(entry["reconcile"]["matches"], entry["file"])
            self.assertEqual(entry["reconcile"]["difference"], 0, entry["file"])

    def test_weekly_names_the_campaign_behind_the_drop_and_the_paused_one(self):
        data = self.r["weekly"]["data"]
        self.assertEqual(data["last"], ["2026-11-06", "2026-11-12"])
        top = data["campaigns"][0]
        self.assertEqual((top["scope"], top["verdict"]), ("Plumbing | Emergency", "Worse"))
        self.assertAlmostEqual(sum(c["conv_delta"] for c in data["campaigns"]), data["lines"][0]["conv_delta"], places=1)
        old = next(c for c in data["campaigns"] if c["scope"] == "Drain Cleaning | Old")
        self.assertEqual(old["status"], "Paused now")
        self.assertIn("performance diagnosis skill", self.r["weekly"]["pointer"])
        # The day the drop began, and its lever, are printed for the campaign that moved.
        self.assertEqual((top["main_lever"], top["shift"]["day"]), ("cvr", "2026-11-06"))
        self.assertGreater(top["shift"]["before"], top["shift"]["after"])

    def test_keywords_find_the_waste_and_keep_it_apart_from_less_efficient(self):
        rows = {k["label"]: k for k in self.r["keywords"]["data"]["keywords"]}
        self.assertEqual(rows["plumbing jobs"]["verdict"], "No conversions")
        self.assertEqual(rows["tankless water heater"]["verdict"], "Worse")
        self.assertEqual(rows["[24 hour plumber]"]["verdict"], "Better")
        self.assertEqual(rows["diy drain unclog"]["verdict"], "Too little data")
        self.assertEqual(rows["[burst pipe plumber]"]["role"], "Paused or removed")
        self.assertEqual(rows["[northside plumbing]"]["role"], "Brand")
        money = self.r["keywords"]["money"]["account"]
        self.assertAlmostEqual(money["wasted"], 640.00, places=2)
        self.assertAlmostEqual(money["less_efficient"], sum(k["extra"] for k in rows.values() if k["verdict"] == "Worse"), places=1)
        self.assertAlmostEqual(money["too_early"], 230.00 + 85.00, places=2)
        counts = self.r["keywords"]["counts"]
        self.assertEqual(counts["judged"] + counts["paused"] + counts["brand"], counts["keywords"])
        # Brand is out of the baseline: 170 non brand conversions, not 210.
        self.assertAlmostEqual(self.r["keywords"]["baseline"]["conversions"], 170, places=2)

    def test_a_wide_gap_on_low_volume_is_worth_watching_not_in_line(self):
        rows = {k["label"]: k for k in self.r["keywords"]["data"]["keywords"]}
        self.assertEqual(rows["hydro jetting"]["verdict"], "Not enough data to judge")
        placements = {s["label"]: s for s in self.r["placements"]["data"]["segments"]}
        self.assertEqual(placements["Home Repair Weekly"]["verdict"], "Not enough data to judge")
        titles = [t["title"] for t in self.r["keywords"]["tables"] if t["rows"]]
        self.assertTrue(any(t.startswith("Worth watching") for t in titles))

    def test_every_verdict_says_what_it_was_compared_with(self):
        days = {s["label"]: s for s in self.r["schedule"]["data"]["splits"][0]["segments"]}
        sunday = days["Sunday"]
        self.assertEqual(sunday["against"], "all days")
        self.assertLess(sunday["rest_cpa"], sunday["cpa"])
        inside = [s for s in self.r["schedule"]["data"]["splits"][0]["inside_campaigns"] if s["label"] == "Sunday"]
        self.assertEqual({s["against"] for s in inside}, {s["campaign"] for s in inside})

    def test_what_can_act_follows_the_bid_strategy(self):
        inside = {(s["campaign"], s["label"]): s for s in self.r["devices"]["data"]["inside_campaigns"]}
        self.assertTrue(inside[("Plumbing | Emergency", "Computers")]["acts"].startswith("Manual CPC: Device bid adjustment"))
        self.assertIn("Only -100%", inside[("Plumbing | Water Heaters", "Tablets")]["acts"])

    def test_totals_that_disagree_are_explained(self):
        keyword_file = next(f for f in self.result["files"] if f["kind"] == "keywords")
        totals = {t["label"]: t for t in keyword_file["reconcile"]["totals"]}
        self.assertEqual(keyword_file["reconcile"]["label"], "Total: Keywords in your account")
        self.assertAlmostEqual(totals["Total: Account"]["gap"], 512.30, places=2)
        self.assertIn("not keyword based", totals["Total: Account"]["meaning"])

    def test_across_reports_notes_the_hydro_jetting_disagreement(self):
        hydro = next(n for n in self.result["across"] if n.startswith("hydro-jetting"))
        self.assertIn("They disagree", hydro)
        self.assertIn("/drain-cleaning/", hydro)

    def test_report_prints_only_paths_and_one_line(self):
        self.assertLess(len(self.written), 1000)
        self.assertIn("performance-review.md", self.written)

    def test_quality_score_shares_are_cost_weighted_and_say_their_base(self):
        scopes = {s["scope"]: s["components"] for s in self.r["quality_score"]["data"]["scopes"]}
        landing = scopes["Non brand keywords"]["landing_page_exp"]
        self.assertAlmostEqual(landing["cost_below"], 4786.20, places=2)
        self.assertAlmostEqual(landing["share_below"], 4786.20 / 16348.20, places=3)
        self.assertEqual(scopes["Campaign: Plumbing | Water Heaters"]["landing_page_exp"]["share_below"], 1.0)
        self.assertIn("Base for every share", self.r["quality_score"]["facts"][0])

    def test_ads_are_compared_only_with_their_siblings(self):
        ads = {a["label"][:26]: a for a in self.r["ads"]["data"]["ads"]}
        self.assertEqual(ads["Emergency Plumbing Service"]["verdict"], "Trails its siblings")
        self.assertAlmostEqual(ads["Emergency Plumbing Service"]["extra"], 2500.00 - 12 * 5300.00 / 66, places=1)
        self.assertEqual(ads["Water Heater Installation "]["verdict"], "Only ad in its ad group")
        self.assertEqual(ads["Hydro Jetting Specialists"]["verdict"], "Disapproved, left out")
        # A tiny sibling never makes the big ad a winner.
        self.assertEqual(ads["Drain Cleaning Experts | C"]["verdict"], "In line")

    def test_devices_find_tablets_and_emergency_computers_and_skip_the_paused_campaign(self):
        data = self.r["devices"]["data"]
        account = {s["label"]: s for s in data["segments"]}
        self.assertEqual(account["Tablets"]["verdict"], "Worse")
        inside = {(s["campaign"], s["label"]): s for s in data["inside_campaigns"]}
        self.assertEqual(inside[("Plumbing | Emergency", "Computers")]["verdict"], "Worse")
        self.assertNotIn("Drain Cleaning | Old", {s["campaign"] for s in data["inside_campaigns"]})
        counts = self.r["devices"]["counts"]
        self.assertEqual(counts["used"] + counts["paused_rows"] + counts["brand_rows"], counts["rows"])

    def test_pages_audiences_locations_schedule_placements_and_videos(self):
        pages = {s["label"]: s for s in self.r["landing_pages"]["data"]["segments"]}
        heater = pages["https://www.northsideplumbing.com/water-heaters/"]
        self.assertEqual((heater["verdict"], round(heater["cost"], 2)), ("Worse", 4786.20))
        self.assertEqual(pages["https://www.northsideplumbing.com/hydro-jetting/"]["verdict"], "No conversions")
        audiences = {s["label"]: s for s in self.r["audiences"]["data"]["segments"]}
        self.assertEqual(audiences["Home Improvement"]["verdict"], "Worse")
        places = {s["label"]: s for s in self.r["locations"]["data"]["segments"]}
        self.assertEqual(places["Gary, Indiana, United States"]["verdict"], "No conversions")
        self.assertAlmostEqual(self.r["locations"]["money"]["account"]["wasted"], 1000.00, places=2)
        days = {s["label"]: s for s in self.r["schedule"]["data"]["splits"][0]["segments"]}
        self.assertEqual(days["Sunday"]["verdict"], "Worse")
        self.assertEqual([d for d, s in days.items() if s["verdict"] == "Worse"], ["Sunday"])
        placements = {s["label"]: s for s in self.r["placements"]["data"]["segments"]}
        self.assertEqual(placements["Bubble Shooter Classic"]["verdict"], "No conversions")
        videos = {v["label"]: v for v in self.r["videos"]["data"]["videos"]}
        self.assertEqual(videos["Meet Our Plumbers (60s)"]["view_verdict"], "Lower view rate")
        self.assertEqual(videos["Meet Our Plumbers (60s)"]["largest_drop"][0], "25% to 50%")

    def test_workbook_is_valid_with_one_tab_per_review(self):
        with zipfile.ZipFile(os.path.join(self.out, "performance-review.xlsx")) as archive:
            for name in archive.namelist():
                minidom.parseString(archive.read(name))
            book = archive.read("xl/workbook.xml").decode()
        for tab in ("Summary", "Weekly performance review", "Top and bottom keywords", "Quality Score review", "Ad performance",
                    "Devices", "Landing pages", "Audiences", "Locations", "Ad schedule", "Placements", "YouTube ads", "Actions"):
            self.assertIn('name="%s"' % tab, book)

    def test_no_file_carries_a_vendor_name(self):
        for name in ("performance-review.md", "performance-review.json"):
            with open(os.path.join(self.out, name), encoding="utf-8") as handle:
                self.assertNotIn("parallel", handle.read().lower(), name)
        with zipfile.ZipFile(os.path.join(self.out, "performance-review.xlsx")) as archive:
            for name in archive.namelist():
                self.assertNotIn(b"parallel", archive.read(name).lower(), name)


class Refusals(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_missing_column_is_a_plain_message(self):
        path = without_column(os.path.join(EXPORTS, "keyword-report.csv"), "Cost", os.path.join(self.work, "keywords.csv"))
        done = run("review.py", path, "--work", self.work, ok=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("I can't find these columns in the keyword report: Cost", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_unknown_report_is_refused_with_what_it_can_read(self):
        path = without_column(os.path.join(EXPORTS, "campaign-report-by-day.csv"), "Day", os.path.join(self.work, "campaigns.csv"))
        done = run("review.py", path, "--work", self.work, ok=False)
        self.assertIn("I can't tell which report campaigns.csv is", done.stderr)
        self.assertIn("I can read: the campaign report segmented by Day", done.stderr)
        search = os.path.join(ROOT, "examples", "exports", "search-terms-report.csv")
        done = run("review.py", search, "--work", self.work, ok=False)
        self.assertIn("search terms skill", done.stderr)

    def test_a_wrong_brand_campaign_name_is_refused(self):
        done = run("review.py", os.path.join(EXPORTS, "campaign-report-by-device.csv"), "--work", self.work,
                   "--brand-campaign", "Brand Search", ok=False)
        self.assertIn("not in the reports: Brand Search", done.stderr)

    def test_identical_segments_raise_a_warning(self):
        path = os.path.join(self.work, "flat.csv")
        with open(path, "w", newline="") as handle:
            out = csv.writer(handle)
            out.writerows([["Location report"], ["October 14, 2026 - November 12, 2026"], ["Location", "Campaign", "Clicks", "Cost", "Conversions"]])
            out.writerows([[town, "Plumbing | Emergency", "50", "400.00", "5.00"] for town in ("Evanston", "Skokie", "Wilmette", "Chicago")])
        result = review(self.work, [path])
        self.assertTrue(any(f.startswith("Check the export: 4 locations have identical") for f in result["reviews"]["locations"]["facts"]))

    def test_a_long_tail_of_one_click_rows_is_not_called_a_broken_download(self):
        # A real placement report (2026-11-14) had 89 channels at one interaction and 0.01 each.
        path = os.path.join(self.work, "tail.csv")
        with open(path, "w", newline="") as handle:
            out = csv.writer(handle)
            out.writerows([["Location report"], ["October 14, 2026 - November 12, 2026"], ["Location", "Campaign", "Clicks", "Cost", "Conversions"]])
            out.writerows([["Town %d" % n, "Plumbing | Emergency", "1", "0.01", "0.00"] for n in range(120)])
            out.writerow(["Total: Account", "", "120", "1.32", "0.00"])
        result = review(self.work, [path])
        self.assertFalse(any(f.startswith("Check the export") for f in result["reviews"]["locations"]["facts"]))
        self.assertTrue(result["files"][0]["reconcile"]["matches"])

    def test_one_report_runs_its_review_and_names_the_rest(self):
        result = review(self.work, ["location-report.csv"])
        self.assertEqual(list(result["reviews"]), ["locations"])
        unlock = {n["key"]: n["unlock"] for n in result["not_run"]}
        self.assertIn("When and where ads showed", unlock["schedule"])
        self.assertIn("segment icon, Device", unlock["devices"])

    def test_report_refuses_unjudged_reviews_and_unsourced_official_claims(self):
        review(self.work, ["location-report.csv"])
        notes = {"headline": "x", "reviews": {"locations": {"summary": ""}}}
        with open(os.path.join(self.work, "notes.json"), "w") as handle:
            json.dump(notes, handle)
        done = run("write_report.py", "--work", self.work, "--out", os.path.join(self.work, "out"), ok=False)
        self.assertIn("these reviews have no summary yet: Locations", done.stderr)
        notes["reviews"]["locations"] = {"summary": "y", "actions": [{"action": "z", "label": "Official", "source": ""}]}
        with open(os.path.join(self.work, "notes.json"), "w") as handle:
            json.dump(notes, handle)
        done = run("write_report.py", "--work", self.work, "--out", os.path.join(self.work, "out"), ok=False)
        self.assertIn("needs a source file", done.stderr)


def opened_files_exist(test, text):
    for path in set(re.findall(r"(?:playbooks|references)/[a-z0-9-]+\.md", text)):
        test.assertTrue(os.path.isfile(os.path.join(SKILL, path)), path)


class DemandGen(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_a_demand_gen_campaign_gets_its_own_review_against_googles_thresholds(self):
        path = os.path.join(self.work, "campaigns.csv")
        start = datetime.date(2026, 10, 16)
        with open(path, "w", newline="") as handle:
            out = csv.writer(handle)
            out.writerows([["Campaign report"], ["October 16, 2026 - November 12, 2026"],
                           ["Day", "Campaign status", "Campaign", "Campaign type", "Bid strategy type", "Budget", "Target CPA",
                            "Cost", "Impr.", "Clicks", "Conversions"]])
            for i in range(28):
                day = (start + datetime.timedelta(days=i)).isoformat()
                out.writerow([day, "Enabled", "Plumbing | Emergency", "Search", "Manual CPC", "300.00", "--", "100.00", "500", "20", "2.00"])
                out.writerow([day, "Enabled", "Demand Gen | Homeowners", "Demand Gen", "Target CPA", "300.00", "60.00", "70.00", "4000", "40", "1.00"])
        result = review(self.work, [path])
        found = result["reviews"]["demand_gen"]
        self.assertEqual([c["campaign"] for c in found["data"]["campaigns"]], ["Demand Gen | Homeowners"])
        dg = found["data"]["campaigns"][0]
        # 28 conversions is under Google's 30 to 50, and a 300.00 budget is 5 times a 60.00 target, under Google's 10.
        self.assertEqual((dg["conversions"], dg["band"], dg["conv_by_week"]), (28, "under 30", [7, 7, 7, 7]))
        self.assertEqual((dg["budget"], dg["target_cpa"], dg["budget_per_target"]), (300, 60, 5))
        self.assertTrue(any("5 times the Target CPA" in f for f in found["facts"]))
        self.assertNotIn("demand_gen", [n["key"] for n in result["not_run"]])
        opened_files_exist(self, found["open"])


class Playbooks(unittest.TestCase):
    def test_every_playbook_named_in_skill_md_exists_and_every_playbook_is_named(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/[a-z0-9-]+\.md", handle.read()))
        present = {"playbooks/" + f for f in os.listdir(os.path.join(SKILL, "playbooks")) if not f.startswith(".")}
        self.assertEqual(named, present)
        work = tempfile.mkdtemp()
        try:
            done = run("review.py", *[os.path.join(EXPORTS, f) for f in FILES], "--work", work)
        finally:
            shutil.rmtree(work)
        opened_files_exist(self, done.stdout)


if __name__ == "__main__":
    unittest.main()
