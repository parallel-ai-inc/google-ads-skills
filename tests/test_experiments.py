"""Tests for the experiments skill.

    python3 -m unittest tests/test_experiments.py
"""
import csv
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from xml.dom import minidom

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILL = os.path.join(ROOT, "skills", "experiments-for-google-ads")
SCRIPTS = os.path.join(SKILL, "scripts")
EXPORTS = os.path.join(ROOT, "examples", "exports", "experiments")
CAMPAIGNS = os.path.join(EXPORTS, "campaigns-by-day.csv")
ARMS = os.path.join(EXPORTS, "experiment-arms-by-day.csv")
SCORECARD = os.path.join(EXPORTS, "experiment-scorecard.csv")
LEADS = os.path.join(EXPORTS, "leads-by-city-by-day.csv")
COST = os.path.join(EXPORTS, "cost-by-city-by-day.csv")
TEST_CITIES = "Evanston;Skokie;Oak Park"
OUT = tempfile.mkdtemp()


def run(script, *args, ok=True):
    done = subprocess.run([sys.executable, os.path.join(SCRIPTS, script)] + list(args), capture_output=True, text=True)
    if ok and done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done


def out(name):
    return os.path.join(OUT, name)


def setUpModule():
    subprocess.run([sys.executable, os.path.join(ROOT, "tools", "build.py"), "experiments-for-google-ads"], check=True, capture_output=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "examples", "make_samples_experiments.py")], check=True, capture_output=True)
    run("design.py", CAMPAIGNS, "--out", out("design"), "--campaign", "Plumbing | Emergency", "--since", "2026-10-01", "--lift", "0.15",
        "--change", "Switch the bid strategy to Target CPA")
    run("design.py", CAMPAIGNS, "--out", out("design-geo"), "--design", "geo", "--geo", LEADS, "--geo-metric", "leads", "--until", "2026-10-21",
        "--test-regions", TEST_CITIES, "--lift", "0.2")
    run("readout.py", "experiment", ARMS, "--out", out("arms"), "--from", "2026-10-01")
    run("readout.py", "experiment", SCORECARD, "--out", out("scorecard"))
    run("readout.py", "daily", LEADS, "--out", out("geo"), "--test", TEST_CITIES, "--during", "2026-10-22:2026-11-11",
        "--value-metric", "revenue", "--cost-report", COST, "--margin", "0.40")
    run("readout.py", "find", COST, "--outcome", LEADS, "--out", out("find"))
    run("readout.py", "daily", LEADS, "--out", out("geo-two-weeks"), "--test", TEST_CITIES, "--during", "2026-10-22:2026-11-04",
        "--value-metric", "revenue", "--cost-report", COST, "--margin", "0.40", "--inferred")
    run("readout.py", "onoff", LEADS, "--out", out("onoff"), "--names", TEST_CITIES, "--off", "2026-10-22:2026-11-11")
    run("roi.py", CAMPAIGNS, "--out", out("roi"), "--margin", "0.40")


def tearDownModule():
    shutil.rmtree(OUT)


def load(folder, name):
    with open(os.path.join(OUT, folder, name), encoding="utf-8") as handle:
        return json.load(handle)


class PlantedFindings(unittest.TestCase):
    def test_water_heaters_lose_money_and_emergency_next_dollar_does_not_pay(self):
        roi = {c["campaign"]: c for c in load("roi", "roi.json")["campaigns"]}
        self.assertEqual(roi["Plumbing | Water Heaters"]["verdict"], "Loses money")
        emergency = roi["Plumbing | Emergency"]
        self.assertEqual(emergency["verdict"], "Profitable")
        self.assertEqual(emergency["curve"]["shape"], "Returns fall as spend rises")
        self.assertEqual(emergency["curve"]["next_dollar"], "Does not pay")
        self.assertLess(emergency["curve"]["marginal_high"], 2.5)

    def test_every_unanswered_next_dollar_says_why_and_what_would_allow_it(self):
        for c in load("roi", "roi.json")["campaigns"]:
            k = c["curve"]
            if k.get("next_dollar") not in ("Pays", "Does not pay"):
                self.assertTrue(k.get("reason"), c["campaign"])
                self.assertTrue(k.get("needs"), c["campaign"])

    def test_brand_is_named_and_paused_is_not_judged_on_spend(self):
        roi = load("roi", "roi.json")
        self.assertEqual(roi["brand"], ["Brand"])
        self.assertLess(roi["account_without_brand"]["profit"], roi["account"]["profit"])
        sewer = next(c for c in roi["campaigns"] if c["campaign"] == "Sewer Line | Search")
        self.assertEqual(sewer["status"], "Paused")
        self.assertNotIn("next_dollar", sewer["curve"])

    def test_the_experiment_lift_is_not_called_and_settling_days_are_left_out(self):
        arms = load("arms", "readout.json")
        result = {r["metric"]: r for r in arms["results"]}
        conv = result["Conversions"]
        self.assertGreater(conv["difference"], 0.1)
        self.assertLess(conv["low"], 0)
        self.assertFalse(conv["significant"])
        self.assertTrue(result["Conv. rate"]["significant"])
        self.assertEqual(arms["arms"]["days"], 42)
        self.assertEqual(arms["arms"]["rows_skipped"], 14)

    def test_googles_figures_are_shown_not_replaced(self):
        card = load("scorecard", "readout.json")
        result = {r["metric"]: r for r in card["results"]}
        self.assertTrue(card["google_significance_used"])
        self.assertAlmostEqual(result["Conversions"]["difference"], 0.17)
        self.assertAlmostEqual(result["Conversions"]["low"], -0.095)
        self.assertEqual(result["Conversions"]["source"], "Google")
        self.assertFalse(result["Conversions"]["significant"])
        self.assertTrue(result["Conv. rate"]["significant"])
        self.assertAlmostEqual(result["Conv. rate"]["control"], 0.1185)

    def test_the_geo_test_finds_the_ads_cause_fewer_than_attributed(self):
        geo = load("geo", "readout.json")
        self.assertTrue(geo["distinguishable_from_zero"])
        self.assertTrue(geo["pre_is_three_times_test"])
        self.assertLess(geo["effect"]["relative_high"], 0)
        cost = geo["cost"]
        self.assertAlmostEqual(cost["incremental_share_of_attributed"], geo["caused_by_ads"]["per_day"] / cost["attributed_per_day_before"])
        self.assertLess(cost["incremental_share_of_attributed"], 1)
        self.assertGreater(cost["spend_change"], 0)

    def test_profit_per_unit_of_spend_and_break_even(self):
        cost = load("geo", "readout.json")["cost"]
        self.assertAlmostEqual(cost["breakeven_value_per_spend"], 2.5)
        self.assertAlmostEqual(cost["incremental_profit_per_spend"], cost["incremental_value_per_spend"] * 0.4 - 1)

    def test_the_contaminated_control_is_flagged_and_left_out(self):
        geo = load("geo", "readout.json")
        self.assertEqual([c["region"] for c in geo["controls_check"] if c["moved"]], ["Niles"])
        self.assertEqual(geo["without_moved_controls"]["left_out"], ["Niles"])
        self.assertEqual(len(geo["without_moved_controls"]["controls"]), 4)
        self.assertIn(geo["without_moved_controls"]["verdict"], ("Strong", "Directional only", "Not readable"))

    def test_the_verdict_comes_from_the_placebo_check(self):
        geo = load("geo", "readout.json")
        self.assertEqual(geo["verdict"], "Strong")
        self.assertGreaterEqual(geo["stated"]["placebo"]["windows"], 10)
        self.assertLessEqual(geo["stated"]["placebo"]["share_as_large"], 0.05)

    def test_the_test_is_found_in_the_data(self):
        found = load("find", "find.json")["candidates"]
        self.assertEqual(len(found), 1)
        self.assertEqual(sorted(found[0]["regions"]), ["Evanston", "Oak Park", "Skokie"])
        self.assertEqual((found[0]["from_latest"], found[0]["to"]), ("2026-10-22", "2026-11-11"))
        self.assertTrue(found[0]["still_off_at_end"])
        self.assertLess(found[0]["outcome_change_against_controls"], 0)
        self.assertNotIn("Evanston", found[0]["controls"])

    def test_a_stated_length_shorter_than_the_data_is_flagged(self):
        short = load("geo-two-weeks", "readout.json")
        self.assertTrue(short["inferred"])
        self.assertIn("stayed off until 2026-11-11", short["length"]["note"])
        self.assertEqual(short["full_off_period"]["window"], ["2026-10-22", "2026-11-11"])
        self.assertEqual(short["stated"]["window"], ["2026-10-22", "2026-11-04"])
        with open(os.path.join(OUT, "geo-two-weeks", "readout.md"), encoding="utf-8") as handle:
            text = handle.read()
        self.assertLess(text.index("## The answer"), text.index("## To confirm with the person"))
        self.assertIn("found from the data", text)

    def test_the_on_and_off_reading_agrees_on_direction(self):
        onoff = load("onoff", "readout.json")
        self.assertTrue(onoff["distinguishable_from_zero"])
        self.assertLess(onoff["effect_per_off_day"], 0)


class Design(unittest.TestCase):
    def test_a_small_campaign_is_called_too_little_volume(self):
        plan = load("design", "test-plan.json")
        self.assertFalse(plan["readable"])
        self.assertTrue(plan["verdict"].startswith("Too little volume"))
        self.assertGreater(plan["days_needed"], plan["max_days"])
        self.assertEqual(plan["data_from"], "2026-10-01")

    def test_the_plan_has_dates_rule_and_checks(self):
        plan = load("design", "test-plan.json")
        p = plan["plan"]
        self.assertEqual(p["measured_days"] % 7, 0)
        self.assertIn(p["stop"], plan["decision_rule"])
        self.assertTrue(plan["weekly_checks"]["checks"])
        self.assertEqual(plan["weekly_checks"]["dates"][-1], p["stop"])
        self.assertEqual(p["change"], "Switch the bid strategy to Target CPA")

    def test_the_geo_plan_is_readable_with_a_long_enough_pre_period(self):
        plan = load("design-geo", "test-plan.json")
        self.assertTrue(plan["readable"])
        self.assertTrue(plan["weekday"]["present"])
        self.assertEqual(plan["plan"]["pre_period_days"], 3 * plan["plan"]["run_days"])
        self.assertEqual(plan["geo"]["test"], ["Evanston", "Skokie", "Oak Park"])

    def test_sizes_are_consistent(self):
        sys.dont_write_bytecode = True
        sys.path.insert(0, SCRIPTS)
        import design
        import testmath
        z = testmath.z_two_sided(0.95) + testmath.z_power(0.8)
        for kind in ("experiment", "geo", "onoff"):
            need = design.days_needed(kind, 0.2, z, 10.0, 12.0, 0.5, True)
            self.assertLessEqual(design.detectable(kind, need, z, 10.0, 12.0, 0.5, True), 0.2 + 1e-9, kind)
            self.assertGreater(design.detectable(kind, need - 1, z, 10.0, 12.0, 0.5, True), 0.2 - 1e-3, kind)
        self.assertAlmostEqual(testmath.t_quantile(0.975, 10), 2.228, places=2)

    def test_a_null_geo_test_rarely_finds_an_effect(self):
        sys.path.insert(0, SCRIPTS)
        import testmath
        rng = random.Random(3)
        alarms = 0
        for _ in range(200):
            control = [rng.gauss(50, 8) for _ in range(84)]
            test = [0.6 * c + rng.gauss(0, 4) for c in control]
            fit = testmath.tbr(control[:63], test[:63], control[63:], test[63:], 0.95)
            alarms += fit["low"] > 0 or fit["high"] < 0
        self.assertLessEqual(alarms, 20)
        import geo
        strong = 0
        for _ in range(40):
            control = [rng.gauss(50, 8) for _ in range(84)]
            test = [0.6 * c + rng.gauss(0, 4) for c in control]
            fit = testmath.tbr(control[:63], test[:63], control[63:], test[63:], 0.95)
            plac = geo.placebo(control[:63], test[:63], 21, fit["relative"])
            strong += geo.trust(fit["low"] > 0 or fit["high"] < 0, plac, True)[0] == "Strong"
        self.assertLessEqual(strong, 3)


class Numbers(unittest.TestCase):
    def test_rows_reconcile_with_the_files_own_totals(self):
        self.assertTrue(load("roi", "roi.json")["reconcile"]["matches"])
        self.assertTrue(load("design", "test-plan.json")["reconcile"]["matches"])
        self.assertTrue(load("geo", "readout.json")["cost_reconcile"]["matches"])

    def test_campaigns_add_up_to_the_account(self):
        roi = load("roi", "roi.json")
        self.assertAlmostEqual(sum(c["cost"] for c in roi["campaigns"]), roi["account"]["cost"], places=2)
        self.assertAlmostEqual(sum(c["profit"] for c in roi["campaigns"]), roi["account"]["profit"], places=2)
        self.assertAlmostEqual(sum(c["share_of_cost"] for c in roi["campaigns"]), 1.0)
        self.assertAlmostEqual(roi["breakeven_roas"], 2.5)


class PlainMessages(unittest.TestCase):
    def test_a_missing_column_is_named(self):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "report.csv")
            with open(path, "w") as handle:
                handle.write('Campaign report\n"November 1, 2026 - November 12, 2026"\nCampaign,Cost,Conversions,Clicks\nBrand,10.00,2.00,5\n')
            done = run("roi.py", path, "--out", folder, "--margin", "0.4", ok=False)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("I can't find these columns", done.stderr)
            self.assertIn("Conv. value", done.stderr)
            self.assertNotIn("Traceback", done.stderr)
        finally:
            shutil.rmtree(folder)

    def test_a_wrong_name_is_refused_with_the_nearest(self):
        done = run("design.py", CAMPAIGNS, "--out", OUT, "--campaign", "Plumbing | Emergencies", ok=False)
        self.assertIn("Did you mean: Plumbing | Emergency", done.stderr)
        done = run("readout.py", "daily", LEADS, "--out", OUT, "--test", "Evanstown", "--during", "2026-10-22:2026-11-11", ok=False)
        self.assertIn("Did you mean: Evanston", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_no_margin_is_a_plain_message(self):
        done = run("roi.py", CAMPAIGNS, "--out", OUT, ok=False)
        self.assertIn("--margin", done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_an_excel_csv_download_gives_the_same_answer(self):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "campaigns.csv")
            with open(CAMPAIGNS, encoding="utf-8") as source, open(path, "w", encoding="utf-16") as target:
                csv.writer(target, delimiter="\t").writerows(csv.reader(source))
            run("roi.py", path, "--out", folder, "--margin", "0.40")
            with open(os.path.join(folder, "roi.json"), encoding="utf-8") as handle:
                again = json.load(handle)
            self.assertAlmostEqual(again["account"]["profit"], load("roi", "roi.json")["account"]["profit"], places=2)
        finally:
            shutil.rmtree(folder)


class Deliverables(unittest.TestCase):
    def files(self):
        for folder in ("design", "design-geo", "arms", "scorecard", "geo", "geo-two-weeks", "find", "onoff", "roi"):
            for name in os.listdir(out(folder)):
                yield os.path.join(out(folder), name)

    def test_no_file_carries_a_vendor_name(self):
        for path in self.files():
            if path.endswith(".xlsx"):
                with zipfile.ZipFile(path) as archive:
                    text = " ".join(archive.read(n).decode("utf-8") for n in archive.namelist())
            else:
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
            self.assertNotIn("parallel", text.lower(), path)

    def test_workbooks_are_valid(self):
        for path in self.files():
            if path.endswith(".xlsx"):
                with zipfile.ZipFile(path) as archive:
                    for part in archive.namelist():
                        minidom.parseString(archive.read(part))

    def test_no_dashes_used_as_pauses(self):
        for path in self.files():
            if not path.endswith(".md"):
                continue
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            self.assertNotIn("—", text)
            self.assertNotIn("–", text)
            for line in re.sub(r"\w+ \d{1,2}, \d{4} - \w+ \d{1,2}, \d{4}", "", text).splitlines():
                self.assertIsNone(re.search(r"\w - \w", line.lstrip(" -")), line)


class Playbooks(unittest.TestCase):
    def test_every_playbook_named_exists_and_every_file_is_named(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w.-]+\.md)", handle.read()))
        files = {name for name in os.listdir(os.path.join(SKILL, "playbooks")) if not name.startswith(".")}
        self.assertEqual(named, files)


if __name__ == "__main__":
    unittest.main()
