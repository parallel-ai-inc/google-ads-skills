"""Tests for the search terms skill's playbooks and the measure step's newer output.

    python3 -m unittest dev/tests/test_search_terms.py

The engine and the review itself are tested in tests/test_pack.py.
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
SKILL = os.path.join(ROOT, "skills", "search-terms-for-google-ads")
REPORT = os.path.join(ROOT, "examples", "exports", "search-terms-report.csv")


def setUpModule():
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "tools", "build.py"), "search-terms-for-google-ads"], check=True, capture_output=True)
    if not os.path.exists(REPORT):
        subprocess.run([sys.executable, os.path.join(ROOT, "dev", "samples", "make_samples.py")], check=True, capture_output=True)


def measure(work, *extra):
    done = subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "measure.py"), REPORT, "--work", work,
                           "--brand", "northside, northside plumbing"] + list(extra), capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    with open(os.path.join(work, "measured.json")) as handle:
        return done.stdout, json.load(handle)


class Measure(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_a_converting_search_above_the_line_shows_by_how_much(self):
        out, measured = measure(self.work)
        term = next(t for t in measured["terms"] if t["search_term"] == "water heater replacement cost")
        # 4 conversions at 127.10 each, against the non brand line of 90.35.
        self.assertAlmostEqual(term["cpa"], 127.10, places=2)
        self.assertAlmostEqual(term["cpa_vs_line"], (127.10 - 90.35) / 90.35, places=2)
        self.assertIn("| 127.10 | +41% |", out)
        self.assertIn("COST OF AT LEAST 45.18 (HALF THE LINE)", out)

    def test_competitor_searches_are_listed_with_their_total(self):
        out, measured = measure(self.work, "--competitors", "home depot, rheem, roto rooter")
        named = sorted(t["search_term"] for t in measured["terms"] if t["competitor"])
        self.assertEqual(named, ["rheem water heater manual", "water heater parts home depot"])
        self.assertIn("2 searches, cost 328.50, conversions 0.00", out)

    def test_no_competitor_table_without_names(self):
        out, measured = measure(self.work)
        self.assertNotIn("SEARCHES THAT NAME A COMPETITOR", out)
        self.assertFalse(any(t["competitor"] for t in measured["terms"]))


class Playbooks(unittest.TestCase):
    def test_every_playbook_named_in_skill_md_exists_and_every_playbook_is_named(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/[a-z0-9-]+\.md", handle.read()))
        present = {"playbooks/" + f for f in os.listdir(os.path.join(SKILL, "playbooks")) if not f.startswith(".")}
        self.assertEqual(named, present)


if __name__ == "__main__":
    unittest.main()
