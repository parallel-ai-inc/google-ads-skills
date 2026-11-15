"""Tests for the account audit skill.

    python3 -m unittest dev/tests/test_account_audit.py
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, "skills", "account-audit-for-google-ads")
SCRIPTS = os.path.join(SKILL, "scripts")
EXPORTS = os.path.join(ROOT, "examples", "exports", "account-audit")
NOTES = os.path.join(ROOT, "examples", "output", "account-audit", "example-notes.json")
OLD = "Drain Cleaning | Old"
FILES = {"--campaigns": "campaign-report.csv", "--ad-groups": "ad-group-report.csv", "--keywords": "keyword-report.csv",
         "--ads": "ads-report.csv", "--search-terms": "search-terms-report.csv", "--conversions": "conversions-summary.csv",
         "--networks": "campaign-report-by-network.csv"}


def run(script, *args, ok=True):
    done = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True, cwd=SKILL)
    if ok and done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done


def audit(work, *extra, files=FILES):
    args = ["--work", work]
    for flag, name in files.items():
        args += [flag, name if os.path.isabs(name) else os.path.join(EXPORTS, name)]
    run(os.path.join(SCRIPTS, "audit.py"), *(args + list(extra)))
    with open(os.path.join(work, "audit.json")) as handle:
        return json.load(handle)


def setUpModule():
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "tools", "build.py"), "account-audit-for-google-ads"], check=True, capture_output=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "samples", "make_samples_account-audit.py")], check=True, capture_output=True)


class FullAudit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.mkdtemp()
        cls.out = tempfile.mkdtemp()
        cls.result = audit(cls.work, "--brand", "northside", "--brand-campaign", "Brand")
        cls.checks = {c["id"]: c for c in cls.result["checks"]}
        shutil.copy(NOTES, os.path.join(cls.work, "notes.json"))
        run(os.path.join(SCRIPTS, "write_report.py"), "--work", cls.work, "--out", cls.out)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work)
        shutil.rmtree(cls.out)

    def test_ad_group_with_no_active_ad_is_found(self):
        check = self.checks["AD-01"]
        self.assertEqual(check["status"], "fail")
        self.assertEqual([(i["campaign"], i["ad_group"]) for i in check["items"]], [("Drain Cleaning | Search", "Hydro Jetting")])
        self.assertAlmostEqual(check["money"], 357.00, places=2)
        self.assertEqual(self.checks["AD-02"]["items"][0]["item"], "Hydro Jetting Specialists")

    def test_double_counted_lead_form_is_found(self):
        self.assertEqual(sorted(i["item"] for i in self.checks["CT-04"]["items"]), ["Contact form submit", "GA4 generate_lead"])
        self.assertEqual([i["item"] for i in self.checks["CT-03"]["items"]], ["GA4 generate_lead"])
        # The money is the spend that bids on conversions: the two Maximize Conversions campaigns.
        self.assertAlmostEqual(self.checks["CT-04"]["money"], 2526.70 + 1887.00, places=2)

    def test_budget_check_names_emergency_and_leaves_out_maximize(self):
        check = self.checks["BB-03"]
        self.assertEqual([i["campaign"] for i in check["items"]], ["Plumbing | Emergency"])
        self.assertIn("Plumbing | Water Heaters", check["left_out"])
        self.assertEqual([c["campaign"] for c in check["by_design"]], ["Plumbing | Water Heaters"])
        with open(os.path.join(self.out, "account-audit.md"), encoding="utf-8") as handle:
            summary = handle.read()
        self.assertIn("Plumbing | Water Heaters uses Maximize Conversions", summary)
        self.assertIn("No target cost per conversion was given", summary)

    def test_money_is_split_into_three_kinds(self):
        kinds = {c["id"]: c["kind"] for c in self.result["checks"] if c["status"] == "fail"}
        self.assertEqual((kinds["SQ-01"], kinds["KW-05"], kinds["CT-04"], kinds["BB-03"]), ("wasted", "wasted", "exposed", "held back"))
        # The held back estimate is never headlined as a share of the account's cost.
        self.assertIsNone(self.checks["BB-03"]["share_of_account_cost"])
        for kind in ("wasted", "exposed", "held back"):
            ranked = sorted((c for c in self.result["checks"] if c.get("kind") == kind and c["status"] == "fail"), key=lambda c: c["rank"])
            self.assertEqual([c["money"] for c in ranked], sorted((c["money"] for c in ranked), reverse=True))

    def test_clear_waste_counts_each_amount_once(self):
        waste = self.result["clear_waste"]
        # "plumber near me" and three other searches it served sit under both SQ-01 and KW-05. They count once, inside the keyword.
        self.assertAlmostEqual(waste["overlap_removed"], 640.20 + 468.60 + 184.80 + 139.20, places=2)
        self.assertAlmostEqual(waste["total"], self.checks["SQ-01"]["money"] + self.checks["KW-05"]["money"] - waste["overlap_removed"], places=2)
        self.assertAlmostEqual(sum(v for _, v in waste["by_campaign"]), waste["total"], places=2)

    def test_broad_match_check_is_named_for_what_fails_and_skips_idle_keywords(self):
        check = self.checks["KW-04"]
        self.assertEqual(check["name"], "Broad match keywords without conversion based bidding")
        self.assertNotIn("frozen pipe repair", [i["item"] for i in check["items"]])

    def test_paused_campaign_is_never_judged(self):
        for check in self.result["checks"]:
            for found in check.get("items", []):
                self.assertNotEqual(found["campaign"], OLD, check["id"])

    def test_rows_reconcile_with_the_files_own_totals(self):
        for entry in self.result["files"]:
            if entry["cost"] is not None:
                self.assertTrue(entry["reconcile"]["matches"], entry["report"])
                self.assertEqual(entry["reconcile"]["difference"], 0, entry["report"])

    def test_counts_add_up(self):
        counts = self.result["counts"]
        self.assertEqual(sum(counts.values()), len(self.result["checks"]))
        self.assertEqual(self.checks["BB-06"]["status"], "not run")
        self.assertIn("target cost per conversion", self.checks["BB-06"]["unlock"])

    def test_workbook_is_valid_and_has_every_tab(self):
        with zipfile.ZipFile(os.path.join(self.out, "account-audit.xlsx")) as archive:
            for name in archive.namelist():
                minidom.parseString(archive.read(name))
            book = archive.read("xl/workbook.xml").decode()
        for tab in ("Findings", "Conversion tracking and goals", "Structure", "Keywords and match types", "Ads and assets",
                    "Budgets and bidding", "Search terms and negatives", "Settings", "Checks not run"):
            self.assertIn('name="%s"' % tab, book)

    def test_no_file_carries_a_vendor_name(self):
        for name in ("account-audit.md", "audit.json"):
            with open(os.path.join(self.out, name), encoding="utf-8") as handle:
                self.assertNotIn("parallel", handle.read().lower(), name)
        with zipfile.ZipFile(os.path.join(self.out, "account-audit.xlsx")) as archive:
            for name in archive.namelist():
                self.assertNotIn(b"parallel", archive.read(name).lower(), name)


class PartialFiles(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_one_report_runs_what_it_can_and_names_the_rest(self):
        result = audit(self.work, "--brand-campaign", "Brand", files={"--campaigns": "campaign-report.csv"})
        checks = {c["id"]: c for c in result["checks"]}
        self.assertEqual(checks["BB-03"]["status"], "fail")
        self.assertEqual(checks["AD-01"]["status"], "not run")
        self.assertIn("Campaigns menu, Campaigns, Ads", checks["AD-01"]["unlock"])

    def test_missing_optional_column_names_the_column(self):
        path = os.path.join(self.work, "campaigns.csv")
        with open(os.path.join(EXPORTS, "campaign-report.csv"), newline="") as handle:
            rows = list(csv.reader(handle))
        drop = rows[2].index("Search lost IS (budget)")
        with open(path, "w", newline="") as handle:
            csv.writer(handle).writerows([r[:drop] + r[drop + 1:] if len(r) > drop else r for r in rows])
        result = audit(self.work, files={"--campaigns": path})
        check = next(c for c in result["checks"] if c["id"] == "BB-03")
        self.assertEqual(check["status"], "not run")
        self.assertIn("Search lost IS (budget)", check["unlock"])

    def test_missing_required_column_is_a_plain_message(self):
        path = os.path.join(self.work, "keywords.csv")
        with open(os.path.join(EXPORTS, "keyword-report.csv"), newline="") as handle:
            rows = list(csv.reader(handle))
        drop = rows[2].index("Cost")
        with open(path, "w", newline="") as handle:
            csv.writer(handle).writerows([r[:drop] + r[drop + 1:] if len(r) > drop else r for r in rows])
        done = run(os.path.join(SCRIPTS, "audit.py"), "--work", self.work, "--keywords", path, ok=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("I can't find these columns in the keyword report: Cost", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_a_wrong_brand_campaign_name_is_refused(self):
        done = run(os.path.join(SCRIPTS, "audit.py"), "--work", self.work, "--campaigns", os.path.join(EXPORTS, "campaign-report.csv"),
                   "--brand", "northside", "--brand-campaign", "Brand Search", ok=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("not in the reports: Brand Search", done.stderr)

    def test_brand_is_kept_out_of_the_baseline(self):
        # Brand converts cheaply. Left in the baseline it hides the budget finding, so the threshold says so.
        blended = {c["id"]: c for c in audit(self.work, files={"--campaigns": "campaign-report.csv"})["checks"]}
        self.assertEqual(blended["BB-03"]["status"], "pass")
        self.assertIn("pull it down", blended["BB-03"]["threshold"])

    def test_report_refuses_unjudged_findings(self):
        audit(self.work, "--brand-campaign", "Brand", files={"--campaigns": "campaign-report.csv"})
        with open(os.path.join(self.work, "notes.json"), "w") as handle:
            json.dump({"findings": []}, handle)
        done = run(os.path.join(SCRIPTS, "write_report.py"), "--work", self.work, "--out", os.path.join(self.work, "out"), ok=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("have no judgment yet: BB-03", done.stderr)

    def test_readiness_and_qa_jobs(self):
        for job, heading in (("readiness", "READINESS CHECKS"), ("qa", "QA: MUST PASS")):
            done = run(os.path.join(SCRIPTS, "audit.py"), "--work", self.work, "--job", job, "--campaigns", os.path.join(EXPORTS, "campaign-report.csv"))
            self.assertIn(heading, done.stdout)

    def test_naming_pattern_is_counted_and_the_odd_name_found(self):
        campaigns = audit(self.work, files={"--campaigns": "campaign-report.csv"})["naming"][0]
        self.assertEqual((campaigns["main_pattern"], campaigns["main_count"], campaigns["names"]), ('2 parts split by "|"', 4, 5))
        self.assertEqual([o["name"] for o in campaigns["off_pattern"]], ["Brand"])
        # The second part mixes services with a campaign type and a status word: four different values.
        self.assertEqual(sorted(v for v, _ in campaigns["positions"][1]), ["Emergency", "Old", "Search", "Water Heaters"])

    def test_budget_limited_target_cpa_campaign_is_named_for_the_august_17_rule(self):
        path = os.path.join(self.work, "campaigns.csv")
        with open(os.path.join(EXPORTS, "campaign-report.csv"), newline="") as handle:
            rows = list(csv.reader(handle))
        header = rows[2]
        for row in rows[3:]:
            if row[header.index("Campaign")] == "Drain Cleaning | Search":
                row[header.index("Bid strategy type")] = "Target CPA"
                row[header.index("Status")] = "Limited by budget"
        with open(path, "w", newline="") as handle:
            csv.writer(handle).writerows(rows)
        dated = audit(self.work, files={"--campaigns": path})["dated_changes"]["target_limited_by_budget"]
        self.assertEqual([c["campaign"] for c in dated["limited"]], ["Drain Cleaning | Search"])


class Playbooks(unittest.TestCase):
    def test_every_playbook_is_named_in_skill_md_and_exists(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w-]+\.md)", handle.read()))
        on_disk = set(os.listdir(os.path.join(SKILL, "playbooks")))
        self.assertTrue(named)
        self.assertEqual(named, on_disk)


if __name__ == "__main__":
    unittest.main()
