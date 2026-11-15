"""Tests for the live data skill: what a customer would lose if it broke.

    python3 -m unittest dev/tests/test_live_data.py
"""
import csv
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SKILL = os.path.join(ROOT, "skills", "live-data-for-google-ads")
SAMPLES = os.path.join(ROOT, "examples", "exports", "live-data")
REPORTS = ["search-terms", "keywords", "campaigns", "campaigns-by-day", "ad-groups", "ads", "conversion-actions",
           "change-history", "conversions-by-action-and-day"]
WRITE_TOOLS = ("create_asset", "upload_video_asset", "manage_labels", "manage_label_associations")
TMP = WORK = OUT = None
sys.path.insert(0, os.path.join(SKILL, "scripts"))


def call(script, *args, cwd=SKILL):
    path = script if os.path.isabs(script) else os.path.join(SKILL, "scripts", script)
    return subprocess.run([sys.executable, path] + list(args), capture_output=True, text=True, cwd=cwd)


def run(script, *args, cwd=SKILL):
    done = call(script, *args, cwd=cwd)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def report_args(name, work):
    args = ["report", name, "--customer", "123-456-7890", "--work", work, "--today", "2026-11-13"]
    if name != "change-history":
        args += ["--end", "2026-11-12"]
    if name == "ads":
        args += ["--limit", "6"]
    return args


def grid(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def files_under(folder):
    return [os.path.join(top, name) for top, _, names in os.walk(folder) for name in names]


def setUpModule():
    global TMP, WORK, OUT
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "tools", "build.py"), "live-data-for-google-ads"], check=True, capture_output=True)
    subprocess.run([sys.executable, os.path.join(ROOT, "dev", "samples", "make_samples_live-data.py")], check=True, capture_output=True)
    TMP = tempfile.mkdtemp()
    WORK, OUT = os.path.join(TMP, "work"), os.path.join(TMP, "out")
    os.makedirs(WORK)
    for path in glob.glob(os.path.join(SAMPLES, "*.result.json")):
        shutil.copy(path, WORK)
    for name in REPORTS:
        run("queries.py", *report_args(name, WORK))
        run("convert.py", "--query", os.path.join(WORK, "%s.query.json" % name), "--out", OUT, "--currency", "USD")


def tearDownModule():
    shutil.rmtree(TMP, ignore_errors=True)


class NamedQueries(unittest.TestCase):
    def test_every_field_is_checked_against_the_known_fields(self):
        with open(os.path.join(SKILL, "scripts", "known_fields.json"), encoding="utf-8") as handle:
            known = json.dumps(json.load(handle))
        for name in REPORTS:
            with open(os.path.join(WORK, "%s.query.json" % name), encoding="utf-8") as handle:
                query = json.load(handle)
            statuses = {c["status"] for c in query["field_checks"]}
            self.assertTrue(statuses <= {"seen", "attributed", "hand"}, (name, statuses))
            for field in query["parameters"]["fields"]:
                if field != "ad_group_ad.ad_strength":  # the one field added by hand, from Google's field reference
                    self.assertIn('"%s"' % field, known, (name, field))
            self.assertEqual(query["tool"], "search_search")

    def test_change_history_keeps_to_googles_rules(self):
        with open(os.path.join(WORK, "change-history.query.json"), encoding="utf-8") as handle:
            params = json.load(handle)["parameters"]
        self.assertLessEqual(params["limit"], 10000)
        self.assertTrue(any(c.startswith("change_event.change_date_time >=") for c in params["conditions"]))
        done = call("queries.py", "report", "change-history", "--customer", "1234567890", "--work", TMP, "--today", "2026-11-13", "--days", "45")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("30 days", done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_the_field_count_matches_the_parameters(self):
        for name in REPORTS:
            text = run("queries.py", *report_args(name, TMP))
            counts = [int(n) for n in re.findall(r"Field check: (\d+) fields selected", text)]
            blocks = [json.loads(b) for b in re.findall(r"```json\n(.*?)\n```", text, re.S)]
            self.assertEqual(counts, [len(b["fields"]) for b in blocks], name)
            self.assertNotIn("scripts/convert.py --query", text.replace(os.path.join(SKILL, "scripts", "convert.py"), "ABS"))

    def test_no_printed_step_calls_a_write_tool(self):
        for name in REPORTS + ["check"]:
            args = ["check", "--customer", "1234567890", "--work", TMP] if name == "check" else report_args(name, TMP)
            text = run("queries.py", *args)
            for tool in WRITE_TOOLS:
                self.assertNotIn(tool, text)


class CustomQueries(unittest.TestCase):
    def test_unknown_field_is_refused_with_the_nearest_names(self):
        done = call("queries.py", "custom", "--name", "spend", "--resource", "campaign", "--fields", "campaign.name, metrics.cost",
                    "--customer", "1234567890", "--work", TMP, "--today", "2026-11-13")
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("metrics.cost_micros", done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr)

    def test_unknown_resource_is_refused(self):
        done = call("queries.py", "custom", "--name", "x", "--resource", "keywords_view", "--fields", "campaign.name",
                    "--customer", "1234567890", "--work", TMP)
        self.assertIn("keyword_view", done.stdout + done.stderr)
        self.assertNotEqual(done.returncode, 0)

    def test_a_field_not_seen_with_the_resource_is_sent_to_the_metadata_tool(self):
        text = run("queries.py", "custom", "--name", "kw-is", "--resource", "keyword_view",
                   "--fields", "ad_group_criterion.keyword.text, metrics.search_budget_lost_impression_share",
                   "--customer", "1234567890", "--work", TMP, "--today", "2026-11-13")
        self.assertIn("metadata_get_resource_metadata", text)
        self.assertIn("segments.date BETWEEN", text)

    def test_a_condition_cannot_smuggle_a_second_query(self):
        done = call("queries.py", "custom", "--name", "x", "--resource", "campaign", "--fields", "campaign.name",
                    "--where", "campaign.status = 'ENABLED'; SELECT customer.id FROM customer", "--customer", "1234567890", "--work", TMP)
        self.assertNotEqual(done.returncode, 0)


class Converter(unittest.TestCase):
    def test_files_have_the_download_layout_and_read_back(self):
        from gads import io
        expected = {"search-terms-report.csv": "Search terms report", "keyword-report.csv": "Search keyword report",
                    "campaign-report.csv": "Campaign report", "campaigns-by-day.csv": "Campaign report",
                    "ad-group-report.csv": "Ad group report", "ads-report.csv": "Ads report",
                    "conversion-actions-summary.csv": "Conversion actions", "change-history.csv": "Change history report",
                    "conversions-by-action-and-day.csv": "Conversions by action and day"}
        for name, title in expected.items():
            rows = grid(os.path.join(OUT, name))
            self.assertEqual(rows[0], [title])
            self.assertRegex(rows[1][0], r"^[A-Z][a-z]+ \d{1,2}, \d{4} - [A-Z][a-z]+ \d{1,2}, \d{4}$")
            report = name.replace("-report.csv", "").replace("-summary.csv", "").replace(".csv", "")
            report = {"search-terms": "search-terms", "keyword": "keywords", "campaign": "campaigns", "ad-group": "ad-groups",
                      "ads": "ads", "conversion-actions": "conversion-actions"}.get(report, report)
            with open(os.path.join(OUT, "%s.conversion.json" % report), encoding="utf-8") as handle:
                self.assertTrue(json.load(handle)["check"]["matches"], name)
        meta, rows = io.read_report(os.path.join(OUT, "search-terms-report.csv"))
        self.assertEqual(meta["date_range"], ["2026-10-14", "2026-11-12"])
        self.assertAlmostEqual(sum(r["cost"] for r in rows), meta["totals"]["Total: Search terms"]["cost"], places=2)

    def test_values_are_written_as_the_interface_shows_them(self):
        keywords = grid(os.path.join(OUT, "keyword-report.csv"))
        header = keywords[2]
        by_keyword = {r[header.index("Keyword")]: dict(zip(header, r)) for r in keywords[3:-1]}
        self.assertEqual(by_keyword["[24 hour plumber]"]["Match type"], "Exact match")
        self.assertEqual(by_keyword["drain cleaning"]["Status"], "Campaign paused")
        self.assertEqual(by_keyword["drain cleaning"]["Exp. CTR"], "Below average")
        self.assertEqual(by_keyword['"commercial water heater"']["Quality Score"], " --")
        days = grid(os.path.join(OUT, "campaigns-by-day.csv"))
        share = days[2].index("Search impr. share")
        self.assertTrue(all(r[share] == "< 10%" for r in days[3:-1] if r[2] == "Drain Cleaning | Search"))
        terms = grid(os.path.join(OUT, "search-terms-report.csv"))
        by_term = {r[0]: dict(zip(terms[2], r)) for r in terms[3:-1]}
        self.assertEqual(by_term["emergency plumber near me"]["Cost"], "1,908.00")
        self.assertEqual(by_term["water heater installation"]["Match type"], "Phrase match (close variant)")
        self.assertEqual(by_term["plumber jobs near me"]["Conversions"], "0.00")
        changes = grid(os.path.join(OUT, "change-history.csv"))
        self.assertIn(["Nov 10, 2026, 9:12:03 AM", "manager@example.com", "Plumbing | Emergency", "", "Campaign budget changed: amount",
                       "Google Ads web interface"], changes)

    def test_planted_problems_are_surfaced(self):
        with open(os.path.join(OUT, "ads.conversion.json"), encoding="utf-8") as handle:
            self.assertTrue(any("limit" in w for w in json.load(handle)["warnings"]))
        with open(os.path.join(OUT, "conversion-actions.conversion.json"), encoding="utf-8") as handle:
            self.assertTrue(any("Old call tracking" in n for n in json.load(handle)["notes"]))

    def test_other_result_shapes_give_the_same_file(self):
        with open(os.path.join(WORK, "ad-groups.result.json"), encoding="utf-8") as handle:
            rows = json.load(handle)
        with open(os.path.join(WORK, "ad-groups.query.json"), encoding="utf-8") as handle:
            fields = json.load(handle)["parameters"]["fields"]
        shapes = {"lists.json": json.dumps([[r.get(f) for f in fields] for r in rows]),
                  "lines.json": "\n".join(json.dumps(r) for r in rows),
                  "wrapped.json": json.dumps({"content": [{"type": "text", "text": json.dumps({"results": rows})}]})}
        reference = grid(os.path.join(OUT, "ad-group-report.csv"))
        for name, text in shapes.items():
            path, out = os.path.join(TMP, name), os.path.join(TMP, "shape-" + name)
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(text)
            run("convert.py", "--query", os.path.join(WORK, "ad-groups.query.json"), "--result", path, "--out", out, "--currency", "USD")
            self.assertEqual(grid(os.path.join(out, "ad-group-report.csv")), reference, name)

    def test_a_result_from_another_search_is_refused(self):
        done = call("convert.py", "--query", os.path.join(WORK, "ad-groups.query.json"),
                    "--result", os.path.join(WORK, "campaigns.result.json"), "--out", os.path.join(TMP, "mismatch"))
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("does not match the ad-groups search", done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        self.assertFalse(os.path.exists(os.path.join(TMP, "mismatch", "ad-group-report.csv")))
        done = call("convert.py", "--query", os.path.join(WORK, "campaigns-by-day.query.json"),
                    "--result", os.path.join(WORK, "campaigns.result.json"), "--out", os.path.join(TMP, "mismatch"))
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("does not match", done.stdout + done.stderr)

    def test_a_missing_field_gives_a_plain_message(self):
        with open(os.path.join(WORK, "campaigns.result.json"), encoding="utf-8") as handle:
            rows = json.load(handle)
        for row in rows:
            row.pop("metrics.cost_micros")
        path = os.path.join(TMP, "no-cost.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(rows, handle)
        done = call("convert.py", "--query", os.path.join(WORK, "campaigns.query.json"), "--result", path, "--out", TMP)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("has no metrics.cost_micros", done.stdout + done.stderr)
        self.assertNotIn("Traceback", done.stderr)
        done = call("convert.py", "--query", os.path.join(WORK, "campaigns.query.json"), "--result", os.path.join(TMP, "none.json"), "--out", TMP)
        self.assertIn("Save the search tool's whole result there", done.stdout + done.stderr)


class Bridge(unittest.TestCase):
    """The converted files run through the other skills' own scripts, unchanged."""

    def other(self, skill, script, *args):
        folder = os.path.join(ROOT, "skills", skill)
        return run(os.path.join(folder, "scripts", script), *args, cwd=folder)

    def test_search_terms_skill_reads_it(self):
        text = self.other("search-terms-for-google-ads", "measure.py", os.path.join(OUT, "search-terms-report.csv"),
                          "--work", os.path.join(TMP, "st"), "--brand", "northside plumbing, northside")
        self.assertIn("Searches read: 13", text)
        self.assertIn("Difference from rows: 0.00", text)
        self.assertIn("plumber jobs near me", text)

    def test_budgets_skill_reads_it(self):
        text = self.other("budgets-and-forecasts-for-google-ads", "pacing.py", os.path.join(OUT, "campaigns-by-day.csv"),
                          "--out", os.path.join(TMP, "pace"), "--exclude", "Brand")
        self.assertRegex(text, r"Drain Cleaning \\\| Search \|.*\| Paused \|")
        self.assertIn("Will reach Google's monthly limit", text)

    def test_account_audit_reads_every_file(self):
        text = self.other("account-audit-for-google-ads", "audit.py", "--work", os.path.join(TMP, "audit"),
                          "--campaigns", os.path.join(OUT, "campaign-report.csv"), "--ad-groups", os.path.join(OUT, "ad-group-report.csv"),
                          "--keywords", os.path.join(OUT, "keyword-report.csv"), "--ads", os.path.join(OUT, "ads-report.csv"),
                          "--search-terms", os.path.join(OUT, "search-terms-report.csv"),
                          "--conversions", os.path.join(OUT, "conversion-actions-summary.csv"), "--brand", "northside plumbing",
                          "--brand-campaign", "Brand")
        self.assertEqual(text.count("Matches the file's own total"), 5)

    def test_conversion_tracking_reads_it(self):
        text = self.other("conversion-tracking-for-google-ads", "audit_actions.py", os.path.join(OUT, "conversion-actions-summary.csv"),
                          "--out", os.path.join(TMP, "ct"))
        self.assertIn("Two Primary actions in one category from different sources", text)
        text = self.other("conversion-tracking-for-google-ads", "find_breaks.py", os.path.join(OUT, "conversions-by-action-and-day.csv"),
                          "--out", os.path.join(TMP, "fb"), "--clicks", os.path.join(OUT, "campaigns-by-day.csv"),
                          "--changes", os.path.join(OUT, "change-history.csv"))
        self.assertIn("GA4 generate_lead: Stopped on 2026-11-04", text)
        self.assertIn("Change history: read.", text)


class Setup(unittest.TestCase):
    def test_setup_files_are_read_only_and_hold_no_secret(self):
        folder = os.path.join(TMP, "setup")
        run("setup.py", "--out", folder, "--project-id", "northside-ads", "--login-customer", "111-222-3333", "--customer", "1234567890",
            "--client-id-file", "/home/me/Downloads/client_secret_123.apps.googleusercontent.com.json")
        self.assertIn("Read only", run("setup.py", "--verify-config", os.path.join(folder, "tools_config.yaml")))
        with open(os.path.join(folder, "mcp-server.json"), encoding="utf-8") as handle:
            entry = json.load(handle)["mcpServers"]["google-ads"]
        self.assertEqual(entry["args"], ["run", "--spec", "google-ads-mcp==0.0.6", "google-ads-mcp"])
        self.assertEqual(set(entry["env"]), {"GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_PROJECT_ID", "GOOGLE_ADS_MCP_TOOLS_CONFIG",
                                             "GOOGLE_ADS_LOGIN_CUSTOMER_ID"})
        self.assertTrue(os.path.isabs(entry["env"]["GOOGLE_ADS_MCP_TOOLS_CONFIG"]))
        for path in glob.glob(os.path.join(folder, "*")):
            with open(path, encoding="utf-8") as handle:
                text = handle.read()
            self.assertNotRegex(text, r"GOCSPX-|ya29\.|-----BEGIN|\"refresh_token\"")
            self.assertNotIn("GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET =", text)
        with open(os.path.join(folder, "setup-checklist.md"), encoding="utf-8") as handle:
            text = handle.read()
        commands = re.findall(r"`([^`\n]*(?:python3|gcloud|claude) [^`\n]*)`", text) + re.findall(r"```\n(.*?)\n```", text, re.S)
        self.assertTrue(commands)
        for command in commands:
            self.assertNotRegex(command, r"(?<![A-Z_])(WORK|SETUP_DIR|PROJECT_ID|ACCOUNT_ID|YOUR_)|python3 scripts/", command)
        self.assertIn("python3 %s --verify-config %s" % (os.path.join(SKILL, "scripts", "setup.py"), os.path.join(folder, "tools_config.yaml")), text)
        self.assertIn("--customer 123-456-7890 --work %s" % os.path.join(folder, "work"), text)
        add = max((c for c in commands if c.startswith("claude mcp add")), key=len)
        self.assertIn("--scope user", add)
        self.assertIn("GOOGLE_ADS_MCP_TOOLS_CONFIG=%s" % os.path.join(folder, "tools_config.yaml"), add)
        self.assertTrue(add.endswith("-- pipx run --spec google-ads-mcp==0.0.6 google-ads-mcp"), add)
        self.assertIn("/mcp", text)
        self.assertIn("Apply for access", text)

    def test_setup_asks_for_the_three_things_instead_of_guessing(self):
        folder = os.path.join(TMP, "unasked")
        done = call("setup.py", "--out", folder, "--project-id", "northside-ads")
        self.assertNotEqual(done.returncode, 0)
        text = done.stdout + done.stderr
        for words in ("project ID", "client file", "account ID", "Do not run setup with placeholders"):
            self.assertIn(words, text)
        self.assertFalse(os.path.exists(folder))

    def test_a_config_with_write_tools_on_is_refused(self):
        path = os.path.join(TMP, "open.yaml")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("namespaces:\n  search: true\n  labels: false\n  assets:\n    enabled: true\n")
        done = call("setup.py", "--verify-config", path)
        self.assertNotEqual(done.returncode, 0)
        self.assertIn("assets", done.stdout)

    def test_a_secret_is_never_taken(self):
        for value in ("GOCSPX-abcdef123", "ya29.a0Abc", '{"client_secret": "x"}'):
            done = call("setup.py", "--out", os.path.join(TMP, "s"), "--project-id", "northside-ads", "--customer", "1234567890",
                        "--client-id-file", value)
            self.assertNotEqual(done.returncode, 0)
            self.assertIn("looks like a secret", done.stdout + done.stderr)
            self.assertNotIn(value, done.stdout + done.stderr)


class AdsScripts(unittest.TestCase):
    def test_scripts_only_read_and_write_the_sheet(self):
        import ads_script
        folder = os.path.join(TMP, "js")
        for name in ads_script.SUPPORTED:
            run("ads_script.py", name, "--out", folder, "--sheet-url", "https://docs.google.com/spreadsheets/d/abc123/edit")
            with open(os.path.join(folder, "%s.ads-script.js" % name), encoding="utf-8") as handle:
                text = handle.read()
            calls = set(re.findall(r"\.([A-Za-z_]\w*)\s*\(", text))
            self.assertTrue(calls <= set(ads_script.ALLOWED_CALLS), calls - set(ads_script.ALLOWED_CALLS))
            self.assertNotRegex(text, r"mutate|Builder|\.pause\(|\.enable\(|\.remove\(|\.apply|UrlFetchApp|MailApp")
            if shutil.which("node"):
                self.assertEqual(subprocess.run(["node", "--check", os.path.join(folder, "%s.ads-script.js" % name)]).returncode, 0)
        done = call("ads_script.py", "keywords", "--out", folder, "--sheet-url", "https://example.com/sheet")
        self.assertNotEqual(done.returncode, 0)


class Hygiene(unittest.TestCase):
    def test_no_output_names_a_vendor(self):
        setup, js = os.path.join(TMP, "hygiene-setup"), os.path.join(TMP, "hygiene-js")
        run("setup.py", "--out", setup, "--project-id", "northside-ads", "--customer", "123-456-7890",
            "--client-id-file", "/Users/you/Downloads/client_secret_1.apps.googleusercontent.com.json")
        run("ads_script.py", "search-terms", "--out", js)
        for folder in (OUT, os.path.join(ROOT, "examples", "output", "live-data"), setup, js):
            paths = files_under(folder)
            self.assertTrue(paths, folder)
            for path in paths:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    self.assertNotIn("parallel", handle.read().lower(), path)

    def test_samples_carry_no_real_home_folder(self):
        home = os.path.expanduser("~")
        for folder in (os.path.join(ROOT, "examples", "output", "live-data"), SAMPLES):
            paths = files_under(folder)
            self.assertTrue(any(p.endswith("setup-checklist.md") for p in paths) or folder == SAMPLES)
            for path in paths:
                with open(path, encoding="utf-8", errors="replace") as handle:
                    text = handle.read()
                self.assertNotIn(home, text, path)
                self.assertNotRegex(text, r"/Users/(?!you/)[A-Za-z0-9._-]+/|/home/(?!you/)[A-Za-z0-9._-]+/|[A-Z]:\\{1,2}Users\\{1,2}(?!YOU)", path)


if __name__ == "__main__":
    unittest.main()
