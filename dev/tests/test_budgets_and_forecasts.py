"""Tests for the budgets and forecasts skill: what a customer would lose if it broke.

    python3 -m unittest dev/tests/test_budgets_and_forecasts.py

The engine, the sample export and the core pacing checks are covered in tests/test_pack.py.
These cover the numbers the playbooks decide from.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, "skills", "budgets-and-forecasts-for-google-ads")
REPORT = os.path.join(ROOT, "examples", "exports", "campaigns-by-day.csv")
STATE = {}


def setUpModule():
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "tools", "build.py"), "budgets-and-forecasts-for-google-ads"], check=True, capture_output=True)
    STATE["out"] = tempfile.mkdtemp()
    done = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "pacing.py"), REPORT, "--out", STATE["out"],
                           "--monthly-target", "15000", "--exclude", "Brand"], capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    STATE["text"] = done.stdout
    with open(os.path.join(STATE["out"], "pacing.json"), encoding="utf-8") as handle:
        STATE["result"] = json.load(handle)


def tearDownModule():
    shutil.rmtree(STATE["out"])


class DecisionNumbers(unittest.TestCase):
    def test_a_held_campaign_says_where_its_jump_came_from(self):
        held = {h["campaign"]: h for h in STATE["result"]["held"]}
        self.assertEqual(held["Plumbing | Water Heaters"]["cpa_driver"], "conversions per click")
        self.assertEqual(held["Drain Cleaning | Search"]["cpa_driver"], "the price of clicks")
        for h in held.values():
            # Cost per conversion is cost per click over conversions per click, before and after.
            self.assertAlmostEqual(h["cpa_prior"], h["cpc_prior"] / h["cvr_prior"], places=6)
            self.assertAlmostEqual(h["cpa_recent"], h["cpc_recent"] / h["cvr_recent"], places=6)
        self.assertIn("most of the change came from conversions per click", STATE["text"])

    def test_the_gap_to_a_ceiling_is_a_daily_figure(self):
        account, result = STATE["result"]["account"], STATE["result"]
        self.assertAlmostEqual(account["gap_to_target"], account["forecast_billed"] - 15000)
        self.assertAlmostEqual(account["gap_per_day"] * result["days_remaining"], account["gap_to_target"])
        self.assertIn("above the target: about %s a day" % "{:,.2f}".format(account["gap_per_day"]), STATE["text"])

    def test_a_ceiling_cut_names_the_campaign_and_its_new_budget(self):
        # The cut covers the daily gap, comes first from a held out campaign that spends its budget,
        # and prints the new daily budget so the AI never subtracts.
        account, result = STATE["result"]["account"], STATE["result"]
        cuts = account["ceiling_cut"]
        self.assertAlmostEqual(sum(c["cut"] for c in cuts), account["gap_per_day"])
        held = {h["campaign"] for h in result["held"]}
        self.assertIn(cuts[0]["campaign"], held)
        for c in cuts:
            self.assertAlmostEqual(c["new_daily_budget"], c["daily_budget"] - c["cut"])
            self.assertIn("to about %s" % "{:,.2f}".format(c["new_daily_budget"]), STATE["text"])

    def test_a_whole_month_at_the_target_reconciles_with_the_budgets(self):
        account, campaigns = STATE["result"]["account"], STATE["result"]["campaigns"]
        serving = [c for c in campaigns if not c["not_serving"]]
        self.assertAlmostEqual(account["daily_budget_total"], sum(c["daily_budget"] for c in serving))
        self.assertAlmostEqual(account["daily_total_for_target"] * 30.4, 15000)
        unused = sum(c["daily_budget"] - c["recent_avg_daily"] for c in serving if c["status"] == "Underspending the budget")
        self.assertAlmostEqual(account["unused_budget_per_day"], unused)
        self.assertIn("## A whole month at the target", STATE["text"])

    def test_a_first_budget_step_is_half_the_room(self):
        receiver = STATE["result"]["receivers"][0]
        self.assertAlmostEqual(receiver["first_step_per_day"], receiver["extra_per_day"] / 2)
        self.assertIn("A first step of up to", STATE["text"])
        self.assertIn("## What this did not cover", STATE["text"])
        self.assertIn("What a different budget would buy", STATE["text"])


class Playbooks(unittest.TestCase):
    def test_every_playbook_named_exists_and_every_file_is_named(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w.-]+\.md)", handle.read()))
        files = {name for name in os.listdir(os.path.join(SKILL, "playbooks")) if not name.startswith(".")}
        self.assertTrue(named)
        self.assertEqual(named, files)


if __name__ == "__main__":
    unittest.main()
