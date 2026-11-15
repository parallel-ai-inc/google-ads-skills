"""Tests for the conversion tracking skill.

    python3 -m unittest dev/tests/test_conversion_tracking.py
"""
import json
import math
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

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, "skills", "conversion-tracking-for-google-ads")
SCRIPTS = os.path.join(SKILL, "scripts")
EXPORTS = os.path.join(ROOT, "examples", "exports", "conversion-tracking")
SUMMARY = os.path.join(EXPORTS, "conversion-actions-summary.csv")
BY_DAY = os.path.join(EXPORTS, "conversions-by-action-and-day.csv")
OUT = tempfile.mkdtemp()


def run(script, *args, ok=True):
    done = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True)
    if ok and done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done


def setUpModule():
    run(os.path.join(ROOT, "dev", "tools", "build.py"), "conversion-tracking-for-google-ads")
    run(os.path.join(ROOT, "dev", "samples", "make_samples_conversion-tracking.py"))
    run(os.path.join(SCRIPTS, "audit_actions.py"), SUMMARY, "--out", OUT)
    run(os.path.join(SCRIPTS, "find_breaks.py"), BY_DAY, "--out", OUT, "--actions", SUMMARY,
        "--clicks", os.path.join(EXPORTS, "campaigns-by-day.csv"), "--changes", os.path.join(EXPORTS, "change-history.csv"))


def tearDownModule():
    shutil.rmtree(OUT)


def load(name):
    with open(os.path.join(OUT, name), encoding="utf-8") as handle:
        return json.load(handle)


class PlantedProblems(unittest.TestCase):
    def test_the_audit_finds_all_three(self):
        audit = load("conversion-audit.json")
        found = {(f["type"], tuple(sorted(f["actions"]))) for f in audit["findings"]}
        self.assertIn(("primary_not_recording", ("Online booking",)), found)
        self.assertIn(("double_count", ("GA4 generate_lead", "Website lead form")), found)
        self.assertIn(("lead_every", ("Website lead form",)), found)
        self.assertEqual(audit["findings"][0]["type"], "primary_not_recording")

    def test_the_breaks_are_found_on_the_right_day(self):
        breaks = {b["action"]: b for b in load("conversion-breaks.json")["breaks"]}
        self.assertEqual((breaks["Online booking"]["kind"], breaks["Online booking"]["day"]), ("stopped", "2026-11-04"))
        self.assertEqual((breaks["GA4 generate_lead"]["kind"], breaks["GA4 generate_lead"]["day"]), ("joined", "2026-10-27"))
        self.assertEqual(set(breaks), {"Online booking", "GA4 generate_lead"}, "a steady action was called broken")

    def test_the_stop_shows_clicks_carried_on_and_no_account_change(self):
        booking = next(b for b in load("conversion-breaks.json")["breaks"] if b["action"] == "Online booking")
        self.assertGreater(booking["clicks"]["per_day_after"], 0.8 * booking["clicks"]["per_day_before"])
        self.assertEqual(booking["clicks"]["per_click_after"], 0)
        self.assertEqual(booking["changes_before"], [])
        self.assertEqual(len(booking["kept_recording"]), 4)

    def test_the_switch_to_primary_is_tied_to_its_change(self):
        joined = next(b for b in load("conversion-breaks.json")["breaks"] if b["action"] == "GA4 generate_lead")
        self.assertIn("Secondary action to Primary action", joined["changes_before"][0]["changes"])


class TheCustomersQuestion(unittest.TestCase):
    def test_the_switch_is_linked_to_the_double_counting_finding(self):
        audit = {f["id"]: f for f in load("conversion-audit.json")["findings"]}
        joined = next(b for b in load("conversion-breaks.json")["breaks"] if b["action"] == "GA4 generate_lead")
        link = next(f for f in joined["findings"] if f["type"] == "double_count")
        self.assertEqual(audit[link["id"]]["type"], "double_count")
        self.assertEqual(link["with"], ["Website lead form"])

    def test_the_net_effect_on_conversions_is_given(self):
        result = load("conversion-breaks.json")
        net, periods = result["net_effect_on_conversions"], result["conversions_by_period"]
        self.assertEqual([p["from"] for p in periods], ["2026-10-14", "2026-10-27", "2026-11-04"])
        self.assertEqual(sorted(net["open_at_end"]), ["B1", "B2"])
        self.assertGreater(net["per_day_at_end"], 0)
        self.assertLess(net["last_period_without_open_breaks"], net["first_period_per_day"])
        self.assertEqual(sum(p["days"] for p in periods), result["days"])

    def test_each_break_shows_days_to_the_end_and_checks_have_owners(self):
        result = load("conversion-breaks.json")
        for b in result["breaks"]:
            self.assertEqual(b["daily"][-1][0], result["last_day"])
            self.assertTrue(all(c["owner"] for c in b["checks"]))


class Numbers(unittest.TestCase):
    def test_rows_reconcile_with_the_files_own_totals(self):
        for name in ("conversion-audit.json", "conversion-breaks.json"):
            self.assertTrue(load(name)["reconcile"]["matches"], name)

    def test_shares_add_up_to_the_whole(self):
        audit = load("conversion-audit.json")
        self.assertAlmostEqual(sum(a["share"] for a in audit["actions"]), 1.0)
        breaks = load("conversion-breaks.json")
        self.assertAlmostEqual(sum(r["share"] for r in breaks["action_totals"]), 1.0)
        self.assertAlmostEqual(sum(r["total"] for r in breaks["action_totals"]), breaks["reconcile"]["file_total"], places=2)
        self.assertAlmostEqual(breaks["total"], audit["volume_total"], places=2)

    def test_a_steady_action_is_not_called_broken(self):
        sys.dont_write_bytecode = True
        sys.path.insert(0, SCRIPTS)
        import find_breaks
        rng = random.Random(7)

        def poisson(rate):
            limit, k, p = math.exp(-rate), 0, 1.0
            while True:
                p *= rng.random()
                if p <= limit:
                    return k
                k += 1
        alarms = sum(1 for _ in range(100) if find_breaks.detect([poisson(6) for _ in range(60)]))
        self.assertLessEqual(alarms, 3)
        self.assertEqual(find_breaks.detect([6.0] * 40 + [0.0] * 5)["kind"], "stopped")


class PlainMessages(unittest.TestCase):
    def test_a_missing_column_is_named(self):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "summary.csv")
            with open(path, "w") as handle:
                handle.write('Conversion actions\n"October 14, 2026 - November 12, 2026"\nAction optimization,Conversion source,Category,All conv.\nPrimary action,Website,Purchase,3.00\n')
            done = run(os.path.join(SCRIPTS, "audit_actions.py"), path, "--out", folder, ok=False)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("I can't find these columns", done.stderr)
            self.assertIn("Conversion action", done.stderr)
            self.assertNotIn("Traceback", done.stderr)
        finally:
            shutil.rmtree(folder)

    def test_a_wrong_action_name_is_refused(self):
        done = run(os.path.join(SCRIPTS, "find_breaks.py"), BY_DAY, "--out", OUT, "--action", "Online bookings", ok=False)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("Did you mean: Online booking?", done.stderr)

    def test_an_excel_csv_download_gives_the_same_answer(self):
        folder = tempfile.mkdtemp()
        try:
            path = os.path.join(folder, "by-day.csv")
            with open(BY_DAY, encoding="utf-8") as source, open(path, "w", encoding="utf-16") as target:
                import csv
                csv.writer(target, delimiter="\t").writerows(csv.reader(source))
            run(os.path.join(SCRIPTS, "find_breaks.py"), path, "--out", folder)
            with open(os.path.join(folder, "conversion-breaks.json"), encoding="utf-8") as handle:
                result = json.load(handle)
            self.assertTrue(result["reconcile"]["matches"])
            self.assertEqual({b["action"] for b in result["breaks"]}, {"Online booking", "GA4 generate_lead"})
        finally:
            shutil.rmtree(folder)


class Deliverables(unittest.TestCase):
    def test_no_file_carries_a_vendor_name(self):
        for name in os.listdir(OUT):
            path = os.path.join(OUT, name)
            if name.endswith(".xlsx"):
                with zipfile.ZipFile(path) as archive:
                    text = " ".join(archive.read(n).decode("utf-8") for n in archive.namelist())
            else:
                with open(path, encoding="utf-8") as handle:
                    text = handle.read()
            self.assertNotIn("parallel", text.lower(), name)

    def test_workbooks_are_valid(self):
        for name in ("conversion-audit.xlsx", "conversion-breaks.xlsx"):
            with zipfile.ZipFile(os.path.join(OUT, name)) as archive:
                for part in archive.namelist():
                    minidom.parseString(archive.read(part))

    def test_every_playbook_is_named_and_every_name_exists(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w-]+\.md)", handle.read()))
        on_disk = {name for name in os.listdir(os.path.join(SKILL, "playbooks")) if name.endswith(".md")}
        self.assertTrue(named)
        self.assertEqual(named - on_disk, set(), "named in SKILL.md but missing")
        self.assertEqual(on_disk - named, set(), "in playbooks/ but not named in SKILL.md")

    def test_no_dashes_used_as_pauses(self):
        for name in ("conversion-audit.md", "conversion-breaks.md"):
            with open(os.path.join(OUT, name), encoding="utf-8") as handle:
                text = handle.read()
            self.assertNotIn("—", text)
            self.assertNotIn("–", text)
            for line in text.replace("October 14, 2026 - November 12, 2026", "").splitlines():
                self.assertIsNone(re.search(r"\w - \w", line.lstrip(" -")), line)


if __name__ == "__main__":
    unittest.main()
