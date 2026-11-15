"""Tests for the performance diagnosis skill's playbooks and summary.

    python3 -m unittest dev/tests/test_performance_diagnosis.py

The planted problems and the reconciliation are tested in tests/test_pack.py.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, "skills", "performance-diagnosis-for-google-ads")
EXPORTS = os.path.join(ROOT, "examples", "exports")
OUT = tempfile.mkdtemp()
SUMMARY = ""


def run(script, *args):
    done = subprocess.run([sys.executable, script] + list(args), capture_output=True, text=True)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def setUpModule():
    global SUMMARY
    run(os.path.join(ROOT, "dev", "tools", "build.py"), "performance-diagnosis-for-google-ads")
    if not os.path.exists(os.path.join(EXPORTS, "campaigns-by-day.csv")):
        run(os.path.join(ROOT, "dev", "samples", "make_samples.py"))
    run(os.path.join(SKILL, "scripts", "compare.py"), os.path.join(EXPORTS, "campaigns-by-day.csv"), "--out", OUT, "--days", "10",
        "--changes", os.path.join(EXPORTS, "change-history.csv"))
    with open(os.path.join(OUT, "performance-diagnosis.md"), encoding="utf-8") as handle:
        SUMMARY = handle.read()


def tearDownModule():
    shutil.rmtree(OUT)


class Playbooks(unittest.TestCase):
    def test_every_playbook_is_named_and_every_name_exists(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w-]+\.md)", handle.read()))
        on_disk = {name for name in os.listdir(os.path.join(SKILL, "playbooks")) if name.endswith(".md")}
        self.assertTrue(named)
        self.assertEqual(named - on_disk, set(), "named in SKILL.md but missing")
        self.assertEqual(on_disk - named, set(), "in playbooks/ but not named in SKILL.md")


class TheNumbersThePlaybooksReadArePrinted(unittest.TestCase):
    def test_steady_clicks_behind_a_conversion_rate_drop(self):
        # The lever fit for a bid strategy change depends on whether traffic held.
        self.assertIn("Clicks: 172 before, 172 now (+0.0%).", SUMMARY)

    def test_value_per_conversion_and_status(self):
        self.assertIn("Value / conv.: 520.00 before, 520.00 now.", SUMMARY)
        self.assertIn("| Value / conv. | 326.97 | 305.66 | -6.5% |", SUMMARY)
        self.assertIn("Campaign status on 2026-11-12: Enabled.", SUMMARY)

    def test_the_summary_says_what_it_did_not_cover(self):
        self.assertIn("## What this did not cover", SUMMARY)
        self.assertNotIn("parallel", SUMMARY.lower())


if __name__ == "__main__":
    unittest.main()
