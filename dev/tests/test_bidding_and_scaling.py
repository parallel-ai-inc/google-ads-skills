"""Tests for the bidding and scaling skill: what a customer would lose if it broke.

    python3 -m unittest dev/tests/test_bidding_and_scaling.py
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
SKILL = os.path.join(ROOT, "skills", "bidding-and-scaling-for-google-ads")
EXPORTS = os.path.join(ROOT, "examples", "exports", "bidding-and-scaling")
REPORT = os.path.join(EXPORTS, "campaigns-by-day.csv")
CHANGES = os.path.join(EXPORTS, "change-history.csv")
STATE = {}


def call(script, *args):
    return subprocess.run([sys.executable, os.path.join(SKILL, "scripts", script)] + list(args), capture_output=True, text=True, cwd=SKILL)


def run(script, *args):
    done = call(script, *args)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def review(out, report=REPORT, *extra):
    run("review.py", report, "--out", out, "--changes", CHANGES, "--cycle-days", "3", "--brand", "Brand", *extra)
    with open(os.path.join(out, "bidding-review.json"), encoding="utf-8") as handle:
        return json.load(handle)


def setUpModule():
    for command in ([os.path.join(ROOT, "dev", "tools", "build.py"), "bidding-and-scaling-for-google-ads"],
                    [os.path.join(ROOT, "dev", "samples", "make_samples_bidding-and-scaling.py")]):
        subprocess.run([sys.executable] + command, check=True, capture_output=True)
    STATE["out"] = tempfile.mkdtemp()
    STATE["review"] = review(STATE["out"])


def tearDownModule():
    shutil.rmtree(STATE["out"])


def by_name():
    return {c["campaign"]: c for c in STATE["review"]["campaigns"]}


class Review(unittest.TestCase):
    def test_planted_problems_are_found(self):
        c = by_name()
        self.assertEqual(c["Plumbing | Emergency"]["category"], "Scale candidate")
        self.assertTrue(c["Plumbing | Emergency"]["lever"].startswith("Budget"))
        self.assertTrue(any("August 17, 2026" in n for n in c["Plumbing | Emergency"]["notes"]))
        heaters = c["Plumbing | Water Heaters"]
        self.assertEqual((heaters["category"], heaters["limit"], heaters["lever"]), ("Scale candidate", "Rank or target", "A looser target"))
        self.assertEqual(heaters["read_start"], "2026-10-01")  # the day after its target change
        self.assertEqual(c["Sewer Line | Search"]["category"], "Missing its target")
        self.assertEqual(c["Gas Line | Demand Gen"]["category"], "Pause candidate")
        drain = c["Drain Cleaning | Search"]
        self.assertEqual(drain["category"], "Hold: learning")
        self.assertEqual([s["kinds"] for s in drain["stacked_changes"]], [["strategy", "target"], ["budget"]])
        self.assertEqual(drain["changes"]["budget"]["days_since"], 4)
        self.assertEqual(c["Plumbing | Holiday Promo"]["category"], "Not serving")
        self.assertEqual(c["Brand"]["category"], "Not judged on conversions")

    def test_numbers_reconcile_with_the_file(self):
        res = STATE["review"]
        self.assertTrue(res["account"]["reconcile"]["reconciled"])
        end = dt.date.fromisoformat(res["read_end"])
        cost = conversions = 0.0
        with open(REPORT, encoding="utf-8", newline="") as handle:
            rows = list(csv.reader(handle))[3:]
        for row in rows:
            if row[1].startswith("Total") or dt.date.fromisoformat(row[0]) > end:
                continue
            cost += float(row[13].replace(",", ""))
            conversions += float(row[22])
        whole = res["account"]["read_whole"]
        self.assertAlmostEqual(whole["cost"], cost, places=2)
        self.assertAlmostEqual(whole["conversions"], conversions, places=2)
        self.assertAlmostEqual(sum(g["cost"] for g in res["account"]["by_category"].values()), cost, places=2)
        compared = [x for x in res["campaigns"] if x["serving"] and x["campaign"] != "Brand"]
        self.assertAlmostEqual(res["comparison_cpa"], sum(x["whole"]["cost"] for x in compared) / sum(x["whole"]["conversions"] for x in compared), places=6)

    def test_the_impression_share_column_read_is_named(self):
        self.assertEqual(STATE["review"]["budget_column_read"], "Search lost top IS (budget)")
        work = tempfile.mkdtemp()
        try:
            plain = os.path.join(work, "plain.csv")
            with open(REPORT, encoding="utf-8") as src, open(plain, "w", encoding="utf-8") as dst:
                dst.write(src.read().replace("Search lost top IS", "Search lost IS"))
            res = review(os.path.join(work, "out"), plain)
            self.assertEqual((res["budget_column_read"], res["rank_column_read"]), ("Search lost IS (budget)", "Search lost IS (rank)"))
        finally:
            shutil.rmtree(work)

    def test_a_missing_column_is_a_plain_message(self):
        work = tempfile.mkdtemp()
        try:
            for header, needle in (("Day,Campaign status,Campaign,Budget,Cost,Conversions\n", "Bid strategy type"),
                                   ("Campaign status,Campaign,Bid strategy type,Cost,Conversions\n", "Segment, Time, Day")):
                path = os.path.join(work, "report.csv")
                with open(path, "w", encoding="utf-8") as handle:
                    handle.write("Campaign report\n" + header + ("2026-11-01," if header.startswith("Day") else "") + "Enabled,Brand,Target CPA,12.00,1.00\n")
                done = call("review.py", path, "--out", os.path.join(work, "out"))
                self.assertNotEqual(done.returncode, 0)
                self.assertIn(needle, done.stderr)
                self.assertNotIn("Traceback", done.stderr)
        finally:
            shutil.rmtree(work)


class DefaultCycleAndGoal(unittest.TestCase):
    """No conversion cycle given, and a goal of 60 per conversion, as a customer ran it."""

    @classmethod
    def setUpClass(cls):
        cls.out = tempfile.mkdtemp()
        run("review.py", REPORT, "--out", cls.out, "--changes", CHANGES, "--brand", "Brand", "--goal-cpa", "60")
        with open(os.path.join(cls.out, "bidding-review.json"), encoding="utf-8") as handle:
            cls.res = json.load(handle)
        with open(os.path.join(cls.out, "bidding-review.md"), encoding="utf-8") as handle:
            cls.text = handle.read()
        cls.camps = {c["campaign"]: c for c in cls.res["campaigns"]}

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.out)

    def test_an_empty_read_window_shows_an_early_read_and_never_an_inverted_range(self):
        self.assertEqual((self.res["cycle_days"], self.res["cycle_assumed"]), (7, True))
        self.assertIn("7 days was assumed", self.text)
        drain = self.camps["Drain Cleaning | Search"]
        self.assertEqual(drain["read_days"], 0)
        early = drain["early_read"]
        self.assertEqual((early["start"], early["end"], early["days"]), ("2026-11-06", "2026-11-12", 7))
        cost = conversions = 0.0
        with open(REPORT, encoding="utf-8", newline="") as handle:
            for row in list(csv.reader(handle))[3:]:
                if row[2] == "Drain Cleaning | Search" and "2026-11-06" <= row[0] <= "2026-11-12":
                    cost += float(row[13].replace(",", ""))
                    conversions += float(row[22])
        self.assertAlmostEqual(early["cost"], cost, places=2)
        self.assertAlmostEqual(early["conversions"], conversions, places=2)
        self.assertTrue(early["proper_read_on"] > "2026-11-12")
        self.assertIn("not yet judgeable", self.text)
        self.assertIn("%s (early)" % "{:,.2f}".format(cost / conversions), self.text)
        for first, last in re.findall(r"(\d{4}-\d{2}-\d{2}) to (\d{4}-\d{2}-\d{2})", self.text):
            self.assertLessEqual(first, last)

    def test_the_goal_is_the_limit(self):
        sewer = self.camps["Sewer Line | Search"]
        self.assertEqual((sewer["category"], sewer["target_vs_goal"]), ("Missing its target", "stricter"))
        self.assertIn("already at or stricter than your goal", sewer["lever"])
        self.assertIn("Your goal", self.text)
        heaters = self.camps["Plumbing | Water Heaters"]
        self.assertIn("Moved the unexpected way", " ".join(heaters["reasons"]))
        gas = self.camps["Gas Line | Demand Gen"]
        self.assertTrue(any(n.startswith("Which wins") for n in gas["notes"]))
        out = os.path.join(self.out, "plan")
        run("plan.py", "--review", os.path.join(self.out, "bidding-review.json"), "--plan", os.path.join(EXPORTS, "example-plan.json"), "--out", out)
        with open(os.path.join(out, "change-plan.json"), encoding="utf-8") as handle:
            plan = json.load(handle)
        emergency = next(c for s in plan["steps"] for c in s["changes"] if c["campaign"] == "Plumbing | Emergency")
        self.assertEqual(emergency["check"]["rollback_above"], 60.0)
        self.assertGreater(emergency["check"]["rollback_without_goal"], 60.0)
        self.assertAlmostEqual(emergency["added_per_day"], 40.0)
        self.assertIsNotNone(emergency["implied_extra_per_day_left"])


class Plan(unittest.TestCase):
    def setUp(self):
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out)

    def plan(self, data):
        path = os.path.join(self.out, "plan.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle)
        return call("plan.py", "--review", os.path.join(STATE["out"], "bidding-review.json"), "--plan", path, "--out", os.path.join(self.out, "plan"))

    def test_planted_mistakes_are_refused_and_nothing_is_written(self):
        done = call("plan.py", "--review", os.path.join(STATE["out"], "bidding-review.json"), "--plan", os.path.join(EXPORTS, "example-plan-first-draft.json"),
                    "--out", os.path.join(self.out, "plan"))
        self.assertNotEqual(done.returncode, 0)
        found = {line.split("]")[0].lstrip("- [") for line in done.stderr.splitlines() if line.startswith("- [")}
        self.assertEqual(found, {"unknown_campaign", "held", "demand_gen_step", "why_numbers", "one_change_per_step"})
        self.assertIn("Did you mean Plumbing | Emergency?", done.stderr)
        self.assertFalse(os.path.exists(os.path.join(self.out, "plan")))

    def test_a_held_campaign_needs_a_reason_and_demand_gen_keeps_its_limit(self):
        change = {"step": 1, "campaign": "Drain Cleaning | Search", "change": "budget", "to": 180, "why": "The owner wants more calls."}
        self.assertNotEqual(self.plan({"steps": [change]}).returncode, 0)
        self.assertEqual(self.plan({"steps": [dict(change, override="Owner asked for it")]}).returncode, 0)
        within = {"step": 1, "campaign": "Gas Line | Demand Gen", "change": "target_cpa", "to": 77, "why": "One weekly step."}
        self.assertEqual(self.plan({"steps": [within]}).returncode, 0)

    def test_files_chain_steps_reconcile_and_carry_no_vendor_name(self):
        out = os.path.join(self.out, "plan")
        run("plan.py", "--review", os.path.join(STATE["out"], "bidding-review.json"), "--plan", os.path.join(EXPORTS, "example-plan.json"), "--out", out)
        with open(os.path.join(out, "change-plan.json"), encoding="utf-8") as handle:
            result = json.load(handle)
        steps = {s["step"]: s for s in result["steps"]}
        second = steps[2]["changes"][0]
        self.assertEqual((second["from"], second["to"]), (3.6, 3.3))  # starts from step 1's value
        self.assertEqual(steps[2]["starts_on_day"], max(c["check"]["days"] for c in steps[1]["changes"] if c["change"] in ("budget", "target_roas", "pause")))
        emergency = next(c for c in steps[1]["changes"] if c["campaign"] == "Plumbing | Emergency")
        self.assertAlmostEqual(emergency["monthly_limit"], 280 * 30.4)
        with open(os.path.join(out, "step-1-for-google-ads-editor.csv"), encoding="utf-8", newline="") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), sum(1 for c in steps[1]["changes"] if c["change"] in ("budget", "target_cpa", "target_roas", "bid_strategy", "pause")))
        self.assertEqual({r["Campaign"]: (r["Campaign daily budget"], r["Target ROAS"], r["Campaign status"]) for r in rows},
                         {"Plumbing | Emergency": ("280.00", "", ""), "Plumbing | Water Heaters": ("", "360.00%", ""), "Gas Line | Demand Gen": ("", "", "Paused")})
        for folder in (out, STATE["out"]):
            for name in os.listdir(folder):
                path = os.path.join(folder, name)
                if name.endswith(".xlsx"):
                    with zipfile.ZipFile(path) as archive:
                        for member in archive.namelist():
                            content = archive.read(member)
                            minidom.parseString(content)
                            self.assertNotIn(b"parallel", content.lower(), member)
                else:
                    with open(path, encoding="utf-8") as handle:
                        self.assertNotIn("parallel", handle.read().lower(), name)


class StepSize(unittest.TestCase):
    """A step is sized from printed evidence, never by feel."""

    def setUp(self):
        self.out = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.out)

    def warnings_for(self, to):
        path = os.path.join(self.out, "plan.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump({"steps": [{"step": 1, "campaign": "Plumbing | Emergency", "change": "budget", "to": to, "why": "Limited by budget."}]}, handle)
        out = os.path.join(self.out, "plan-%s" % to)
        run("plan.py", "--review", os.path.join(STATE["out"], "bidding-review.json"), "--plan", path, "--out", out)
        with open(os.path.join(out, "change-plan.json"), encoding="utf-8") as handle:
            return " ".join(next(c for s in json.load(handle)["steps"] for c in s["changes"])["warnings"])

    def test_a_first_budget_step_takes_at_most_half_the_room(self):
        emergency = by_name()["Plumbing | Emergency"]
        ev = emergency["budget_evidence"]
        self.assertAlmostEqual(ev["first_step_per_day"], ev["implied_extra_per_day"] / 2)
        within = round(emergency["budget"] + ev["first_step_per_day"] - 1, 2)
        beyond = round(emergency["budget"] + ev["first_step_per_day"] + 1, 2)
        self.assertNotIn("half the room", self.warnings_for(within))
        self.assertIn("half the room", self.warnings_for(beyond))

    def test_a_budget_step_prints_the_room_left_and_the_monthly_change(self):
        # The next step and the monthly cost of this one are printed, so the AI never subtracts.
        emergency = by_name()["Plumbing | Emergency"]
        ev = emergency["budget_evidence"]
        to = round(emergency["budget"] + ev["first_step_per_day"] - 1, 2)
        self.warnings_for(to)
        with open(os.path.join(self.out, "plan-%s" % to, "change-plan.json"), encoding="utf-8") as handle:
            change = next(c for s in json.load(handle)["steps"] for c in s["changes"])
        self.assertAlmostEqual(change["room_left_after_step"], ev["implied_extra_per_day"] - (to - emergency["budget"]), places=6)
        self.assertAlmostEqual(change["monthly_limit_change"], (to - emergency["budget"]) * 30.4, places=6)

    def test_a_looser_target_stops_at_the_goal_and_shows_the_halfway_point(self):
        result = review(self.out, REPORT, "--goal-cpa", "70")
        guidance = next(c for c in result["campaigns"] if c["campaign"] == "Plumbing | Emergency")["step_guidance"]
        self.assertEqual((guidance["goal"], guidance["halfway_to_goal"]), (70.0, 65.0))


class Playbooks(unittest.TestCase):
    def test_every_playbook_named_exists_and_every_file_is_named(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w.-]+\.md)", handle.read()))
        files = {name for name in os.listdir(os.path.join(SKILL, "playbooks")) if not name.startswith(".")}
        self.assertTrue(named)
        self.assertEqual(named, files)


if __name__ == "__main__":
    unittest.main()
