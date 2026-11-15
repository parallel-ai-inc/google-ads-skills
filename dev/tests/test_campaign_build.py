"""Tests for the campaign build skill: what a customer would lose if it broke.

    python3 -m unittest dev/tests/test_campaign_build.py
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
SKILL = os.path.join(ROOT, "skills", "campaign-build-for-google-ads")
EXPORTS = os.path.join(ROOT, "examples", "exports", "campaign-build")
TODAY = "2026-11-13"
STATUS_COLUMNS = ("Campaign Status", "Ad Group Status", "Status")


def call(script, *args):
    return subprocess.run([sys.executable, os.path.join(SKILL, "scripts", script)] + list(args), capture_output=True, text=True, cwd=SKILL)


def run(script, *args):
    done = call(script, *args)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def setUpModule():
    for command in ([os.path.join(ROOT, "dev", "tools", "build.py"), "campaign-build-for-google-ads"],
                    [os.path.join(ROOT, "dev", "samples", "make_samples_campaign-build.py")]):
        subprocess.run([sys.executable] + command, check=True, capture_output=True)


class CampaignBuild(unittest.TestCase):
    def setUp(self):
        self.work, self.out = tempfile.mkdtemp(), tempfile.mkdtemp()
        run("start_build.py", "--work", self.work, "--campaigns", os.path.join(EXPORTS, "campaigns-report.csv"),
            "--keywords", os.path.join(EXPORTS, "keywords-report.csv"))

    def tearDown(self):
        shutil.rmtree(self.work)
        shutil.rmtree(self.out)

    def plan(self, name="example-plan.json"):
        with open(os.path.join(EXPORTS, name), encoding="utf-8") as handle:
            return json.load(handle)

    def check(self, plan):
        with open(os.path.join(self.work, "plan.json"), "w", encoding="utf-8") as handle:
            json.dump(plan, handle, ensure_ascii=False)
        done = call("check_plan.py", "--work", self.work, "--today", TODAY)
        with open(os.path.join(self.work, "checked.json"), encoding="utf-8") as handle:
            return done, json.load(handle)

    def write(self):
        return call("write_build.py", "--work", self.work, "--out", self.out, "--today", TODAY)

    def test_planted_problems_are_refused_and_nothing_is_written(self):
        done, checked = self.check(self.plan("example-plan-first-draft.json"))
        self.assertNotEqual(done.returncode, 0)
        self.assertEqual({e["check"] for e in checked["errors"]}, {"headline_chars", "paths", "duplicate_keywords", "negative_conflicts"})
        camera = next(n for n in checked["negatives"] if n["text"] == "camera")
        self.assertEqual(sorted(b["keyword"] for b in camera["blocks"]), ["sewer camera inspection", "sewer line camera inspection"])
        refused = self.write()
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("refused the plan", refused.stderr)
        self.assertEqual(os.listdir(self.out), [])

    def test_google_limits_are_enforced(self):
        plan = self.plan()
        campaign = plan["campaigns"][0]
        campaign["daily_budget"] = 0
        ad = campaign["ad_groups"][2]["ads"][0]
        ad["headlines"] = ["水管工" * 5 + "下水道", "Sewer Camera Inspection"]  # 18 double width characters count as 36
        ad["descriptions"] = ["x" * 91, "Licensed plumbers serving Denver and Aurora."]
        ad["final_url"] = "www.northsideplumbing.example/inspection"
        other = campaign["ad_groups"][0]["ads"][0]["headlines"]
        other[2] = other[0]
        done, checked = self.check(plan)
        self.assertNotEqual(done.returncode, 0)
        found = {e["check"] for e in checked["errors"]}
        for key in ("budget", "headline_count", "headline_chars", "description_chars", "final_urls", "duplicate_text"):
            self.assertIn(key, found)
        wide = next(e for e in checked["errors"] if e["check"] == "headline_chars")
        self.assertIn("is 36 characters", wide["text"])

    def test_ai_max_must_be_chosen_and_is_written_as_chosen(self):
        plan = self.plan()
        del plan["campaigns"][0]["ai_max"]
        done, checked = self.check(plan)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("ai_max must be on or off", next(e for e in checked["errors"] if e["check"] == "ai_max")["text"])

        plan = self.plan()
        plan["campaigns"][0]["ai_max"] = "on"
        plan["campaigns"][0]["bid_strategy"] = "Maximize clicks"
        done, checked = self.check(plan)
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertTrue(any(w["check"] == "ai_max" for w in checked["warnings"]))
        self.assertEqual(self.write().returncode, 0)
        with open(os.path.join(self.out, "build-for-google-ads-editor.csv"), encoding="utf-8", newline="") as handle:
            self.assertEqual({r["AI Max"] for r in csv.DictReader(handle) if r["Campaign Type"]}, {"Enabled"})

    def test_a_name_the_account_already_uses_is_refused(self):
        plan = self.plan()
        plan["campaigns"][0]["name"] = "Drain Cleaning | Search"
        done, checked = self.check(plan)
        self.assertNotEqual(done.returncode, 0)
        self.assertTrue(any(e["check"] == "account_names" for e in checked["errors"]))

    def test_files_are_paused_reconciled_and_carry_no_vendor_name(self):
        done, checked = self.check(self.plan())
        self.assertEqual(done.returncode, 0, done.stdout)
        self.assertTrue(any(w["check"] == "account_keywords" and "sewer line repair" in w["where"] for w in checked["warnings"]))
        written = self.write()
        self.assertEqual(written.returncode, 0, written.stderr)

        with open(os.path.join(self.out, "build-for-google-ads-editor.csv"), encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        totals = checked["totals"]
        self.assertEqual(len(rows), totals["import_rows"])
        self.assertEqual(sum(1 for r in rows if r["Keyword"] and r["Status"]), totals["keywords"])
        statuses = [r[c] for r in rows for c in STATUS_COLUMNS if r[c]]
        self.assertEqual(set(statuses), {"Paused"})
        self.assertEqual(len(statuses), totals["paused_items"])
        self.assertEqual(totals["month_limit"], 120 * 30.4)
        # Google Ads Editor will not post a campaign without the EU political ads declaration
        # (found by a real import into Editor 2.14.2, 2026-11-14). Every campaign row carries it.
        campaign_rows = [r for r in rows if r["Campaign Type"]]
        self.assertTrue(campaign_rows)
        self.assertEqual({r["EU political ads"] for r in campaign_rows}, {"Doesn't have EU political ads"})
        # Google turns AI Max on for every imported Search campaign unless the file says off
        # (Editor 2.14.2, 2026-11-14). The sample plan chose off, and the file says so.
        self.assertEqual({r["AI Max"] for r in campaign_rows}, {"Disabled"})

        with open(os.path.join(self.out, "campaign-build.json"), encoding="utf-8") as handle:
            result = json.load(handle)
        self.assertTrue(result["all_paused"])
        self.assertEqual(result["refused_versions"], 0)

        for name in os.listdir(self.out):
            path = os.path.join(self.out, name)
            if name.endswith(".xlsx"):
                with zipfile.ZipFile(path) as archive:
                    for member in archive.namelist():
                        content = archive.read(member)
                        minidom.parseString(content)
                        self.assertNotIn(b"parallel", content.lower(), member)
            else:
                with open(path, encoding="utf-8") as handle:
                    self.assertNotIn("parallel", handle.read().lower(), name)

    def test_write_refuses_a_plan_changed_after_the_check(self):
        plan = self.plan()
        done, _ = self.check(plan)
        self.assertEqual(done.returncode, 0, done.stdout)
        plan["campaigns"][0]["daily_budget"] = 900
        with open(os.path.join(self.work, "plan.json"), "w", encoding="utf-8") as handle:
            json.dump(plan, handle)
        refused = self.write()
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn("changed after the last check", refused.stderr)

    def test_customizer_codes_are_counted_with_their_default_text_and_bad_ones_refused(self):
        plan = self.plan()
        ad = plan["campaigns"][0]["ad_groups"][0]["ads"][0]
        ad["headlines"][:3] = ["Sewer Repair in {LOCATION(City):Denver}", "{KeyWord:Sewer Line Repair}", "Sale Ends {COUNTDOWN(2026-12-24 18:00:00,5)}"]
        ad["descriptions"][0] = "Camera inspection first, then {CUSTOMIZER.Price:fair upfront prices} before any digging starts."
        done, checked = self.check(plan)
        self.assertEqual(done.returncode, 0, done.stdout)
        first = checked["ads"][0]
        # Counted as Google shows them: "Sewer Repair in Denver" is 22, and a countdown takes 8 next to "Sale Ends ".
        self.assertEqual([h["characters"] for h in first["headlines"][:3]], [22, 17, 18])
        self.assertTrue(any(w["check"] == "customizers" and '"Price"' in w["text"] for w in checked["warnings"]))
        self.assertEqual(self.write().returncode, 0)
        with open(os.path.join(self.out, "build-for-google-ads-editor.csv"), encoding="utf-8", newline="") as handle:
            self.assertIn("{KeyWord:Sewer Line Repair}", [r["Headline 2"] for r in csv.DictReader(handle)])

        ad["headlines"][:3] = ["{KEYWORD:Sewer Repair}", "Plumbers in {LOCATION(Town):Denver}", "{KeyWord:Emergency Sewer Line Repair Now}"]
        ad["descriptions"][0] = "{=COUNTDOWN(\"2026/12/24 18:00:00\",\"en\",5)} left to book."
        ad["final_url"] = "https://www.northsideplumbing.example/{KeyWord:repair}"
        done, checked = self.check(plan)
        self.assertNotEqual(done.returncode, 0)
        refused = [e["text"] for e in checked["errors"] if e["check"] == "customizers"]
        for code in ("{KEYWORD:Sewer Repair}", "{LOCATION(Town):Denver}", "{=COUNTDOWN", "final URL"):
            self.assertTrue(any(code in text for text in refused), code)
        # A default text too long for the headline is refused like any long headline.
        self.assertTrue(any(e["check"] == "headline_chars" and "default text" in e["text"] for e in checked["errors"]))

    def test_a_missing_column_is_a_plain_message(self):
        path = os.path.join(self.work, "keywords.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("Search keyword report\nCampaign,Ad group,Clicks,Cost\nBrand,Brand,4,12.00\n")
        done = call("start_build.py", "--work", self.work, "--keywords", path)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("Keyword", done.stderr)
        self.assertNotIn("Traceback", done.stderr)


class Playbooks(unittest.TestCase):
    def test_every_playbook_is_named_in_skill_md_and_exists(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w-]+\.md)", handle.read()))
        on_disk = set(os.listdir(os.path.join(SKILL, "playbooks")))
        self.assertTrue(named)
        self.assertEqual(named, on_disk)


if __name__ == "__main__":
    unittest.main()
