"""Tests for the competition and market skill: what a customer would lose if it broke.

    python3 -m unittest dev/tests/test_competitive_and_market.py
"""
import csv
import importlib.util
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
SKILL = os.path.join(ROOT, "skills", "competitive-and-market-for-google-ads")
EXPORTS = os.path.join(ROOT, "examples", "exports", "competitive-and-market")
CAMPAIGNS = os.path.join(EXPORTS, "campaigns-by-month.csv")
ACCOUNT = os.path.join(EXPORTS, "auction-insights-account-by-month.csv")
EMERGENCY = os.path.join(EXPORTS, "auction-insights-emergency-by-month.csv")
HEATERS = os.path.join(EXPORTS, "auction-insights-water-heaters-by-month.csv")
OUT = None
DATA = None
TEXT = None


def call(*args):
    return subprocess.run([sys.executable, os.path.join(SKILL, "scripts", "market.py")] + list(args), capture_output=True, text=True, cwd=SKILL)


def run(*args):
    done = call(*args)
    if done.returncode != 0:
        raise AssertionError(done.stdout + done.stderr)
    return done.stdout


def full_args(out):
    return ["--out", out, "--campaigns", CAMPAIGNS, "--auction", ACCOUNT, "--scope", "Account", "--auction", EMERGENCY, "--scope", "Plumbing | Emergency",
            "--auction", HEATERS, "--scope", "Plumbing | Water Heaters", "--brand", "Brand"]


def setUpModule():
    global OUT, DATA, TEXT
    for command in ([os.path.join(ROOT, "dev", "tools", "build.py"), "competitive-and-market-for-google-ads"],
                    [os.path.join(ROOT, "dev", "samples", "make_samples_competitive-and-market.py")]):
        subprocess.run([sys.executable] + command, check=True, capture_output=True)
    OUT = tempfile.mkdtemp()
    TEXT = run(*full_args(OUT))
    with open(os.path.join(OUT, "market.json"), encoding="utf-8") as handle:
        DATA = json.load(handle)


def tearDownModule():
    shutil.rmtree(OUT)


def scope(name):
    return next(s for s in DATA["auction"] if s["scope"] == name)


def campaign(name):
    return next(c for c in DATA["share_of_voice"]["campaigns"] if c["campaign"] == name)


def competitor(scope_name, domain):
    return next(c for c in scope(scope_name)["competitors"] if c["domain"] == domain)


def read_rows(path):
    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.reader(handle))


def write_rows(path, rows, encoding="utf-8", delimiter=","):
    with open(path, "w", encoding=encoding, newline="") as handle:
        csv.writer(handle, delimiter=delimiter).writerows(rows)


class PlantedProblems(unittest.TestCase):
    def test_a_new_rival_took_emergency_share_in_the_auction(self):
        self.assertEqual(campaign("Plumbing | Emergency")["reading"], "Share fell, mostly lost to rank")
        emergency = scope("Plumbing | Emergency")
        self.assertEqual(emergency["campaign_report"]["reading"], "Share fell, mostly lost to rank")
        rival = competitor("Plumbing | Emergency", "rapidrooter.example")
        self.assertTrue(rival["large_moves"]["position_above_rate"])
        self.assertTrue(rival["large_moves"]["impression_share"])
        self.assertEqual(rival["first_seen"], "2026-08")
        self.assertIn("showed above you more often by a large move, or entered: rapidrooter.example", TEXT)

    def test_water_heaters_gave_its_share_away_through_budget(self):
        heaters = campaign("Plumbing | Water Heaters")
        self.assertEqual(heaters["reading"], "Share fell, mostly lost to budget")
        self.assertAlmostEqual(heaters["changes"]["lost_budget"]["low_points"], 16.0, places=6)
        self.assertEqual(scope("Plumbing | Water Heaters")["campaign_report"]["reading"], "Share fell, mostly lost to budget")
        self.assertFalse(any(c["large_moves"]["position_above_rate"] for c in scope("Plumbing | Water Heaters")["competitors"]))
        self.assertIn("No competitor's position above rate rose by a large move", TEXT)

    def test_a_share_below_ten_percent_is_a_band_never_zero(self):
        rival = competitor("Account", "rapidrooter.example")["impression_share"]
        self.assertEqual(rival["earlier"]["shown"], "< 10%")
        self.assertEqual((rival["earlier"]["low"], rival["earlier"]["high"]), (0.0, 0.1))
        self.assertEqual(rival["change"]["direction"], "rose")
        self.assertAlmostEqual(rival["change"]["high_points"] - rival["change"]["low_points"], 10.0, places=6)
        self.assertEqual(competitor("Account", "bluepipeplumbing.example")["impression_share"]["change"]["shown"], "stayed < 10%")
        spec = importlib.util.spec_from_file_location("competitive_market_reports", os.path.join(SKILL, "scripts", "reports.py"))
        reports = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(reports)
        for text, low, high in (("< 10%", 0.0, 0.10), ("> 90%", 0.90, 1.0), ("45.30%", 0.453, 0.453), (0.453, 0.453, 0.453)):
            share = reports.parse_share(text)
            self.assertAlmostEqual(share.lo, low)
            self.assertAlmostEqual(share.hi, high)
        self.assertIsNone(reports.parse_share(" --"))

    def test_seasonality_finds_the_winter_peak_and_a_worse_october(self):
        season = DATA["seasonality"]
        self.assertTrue(season["readable"])
        self.assertEqual(len(season["cycles"]), 2)
        clicks = season["pattern"]["clicks"]
        self.assertTrue({1, 2, 12} <= set(clicks["rise"]))
        self.assertTrue({6, 7} <= set(clicks["fall"]))
        october = season["same_period_last_year"][-1]
        self.assertEqual((october["period"], october["prior"]), ("2026-10", "2025-10"))
        self.assertLess(october["change"]["conversions"], 0)
        self.assertGreater(october["change"]["cpa"], 0)
        emergency = next(c for c in season["campaigns"] if c["campaign"] == "Plumbing | Emergency")
        self.assertGreater(emergency["recent"]["change"]["cpa"], 0.15)

    def test_the_winter_months_ahead_carry_last_years_step(self):
        ahead = DATA["seasonality"]["ahead"]
        self.assertEqual([(a["period"], a["prior"]) for a in ahead], [("2026-11", "2025-11"), ("2026-12", "2025-12"), ("2027-01", "2026-01")])
        self.assertTrue(ahead[0]["in_progress"])
        for a in ahead:
            self.assertEqual((a["base"], a["usually"]), ("2025-10", "rises"))
            self.assertGreater(a["step"]["clicks"], 0.15)
        self.assertIn("It is last year's step, not a forecast.", TEXT)
        self.assertIn("| 2026-11 (in progress) | 2025-11 | rises |", TEXT)

    def test_the_partial_month_is_never_the_default_comparison(self):
        self.assertEqual((DATA["compared"]["earlier"], DATA["compared"]["later"]), ("2026-09", "2026-10"))
        self.assertIn({"period": "2026-11", "note": "partial: 12 of 30 days"}, DATA["seasonality"]["partial"])
        self.assertNotIn("2026-11", DATA["seasonality"]["complete"])

    def test_a_paused_campaign_is_not_judged(self):
        self.assertEqual(campaign("Plumbing | Spring Promo")["reading"], "Not serving in 2026-10")
        self.assertIn("Plumbing | Spring Promo", DATA["seasonality"]["part_year_campaigns"])


    def test_each_campaign_gets_its_own_answer_and_brand_stays_out(self):
        short = TEXT.split("## In short")[1].split("## Auction insights")[0]
        emergency = next(line for line in short.splitlines() if line.startswith("- **Plumbing | Emergency:**"))
        self.assertIn("mostly lost to rank", emergency)
        self.assertIn("rapidrooter.example showed above you more often", emergency)
        self.assertIn("the factor that moved them most is Search impr. share", emergency)
        self.assertNotIn("**Brand", short)
        self.assertIn("Brand campaigns are left out of these readings: Brand.", short)
        self.assertIn("Campaigns in the report: Brand (brand); Drain Cleaning | Search;", TEXT)

    def test_why_emergency_conversions_fell_year_on_year(self):
        levers = {x["campaign"]: x for x in DATA["seasonality"]["levers"]}
        emergency = levers["Plumbing | Emergency"]
        self.assertEqual((emergency["period"], emergency["prior"]), ("2026-10", "2025-10"))
        self.assertLess(emergency["conversions_change"], 0)
        self.assertEqual(emergency["main_lever"], "sis")
        self.assertAlmostEqual(sum(emergency["levers"].values()), 1.0, places=6)
        self.assertEqual(levers["Brand"]["split"], "impressions x CTR x conv. rate")

    def test_water_heaters_spends_its_budget_and_is_not_flagged(self):
        heaters = campaign("Plumbing | Water Heaters")
        self.assertGreater(heaters["detail"]["later"]["budget_used"], 0.95)
        self.assertIsNone(heaters["budget_does_not_add_up"])
        self.assertEqual(DATA["auction"][0]["identical"], [])

    def test_partial_cells_are_marked(self):
        self.assertIn("| 2026-11 (partial) |", TEXT)
        self.assertIn("| 43.0% (partial) |", TEXT)


class FiguresThatLookWrong(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_a_budget_loss_that_does_not_add_up_and_equal_figures_are_explained(self):
        rows = read_rows(CAMPAIGNS)
        header = rows[2]
        for r in rows:
            if r[:3] == ["October 2026", "Enabled", "Plumbing | Water Heaters"]:
                r[header.index("Cost")] = "1,978.44"
                r[header.index("Search lost IS (rank)")] = "26.00%"
        path = os.path.join(self.work, "campaigns.csv")
        write_rows(path, rows)
        text = run("--out", self.work, "--campaigns", path, "--brand", "Brand")
        with open(os.path.join(self.work, "market.json"), encoding="utf-8") as handle:
            heaters = next(c for c in json.load(handle)["share_of_voice"]["campaigns"] if c["campaign"] == "Plumbing | Water Heaters")
        self.assertIsNotNone(heaters["budget_does_not_add_up"])
        self.assertIn("**Does not add up.** Plumbing | Water Heaters: lost to budget +16.0 pts while the daily budget stayed 85.00", text)
        self.assertIn("first confirm in the change history that the budget did not change", text)
        self.assertIn("The two figures are equal because lost to budget and lost to rank are both 26.0% in 2026-10.", text)
        self.assertIn("Did any budget change in the period?", text)

    def test_a_measure_that_never_moves_is_flagged(self):
        rows = read_rows(ACCOUNT)
        for r in rows[3:]:
            if r[1] == "You":
                r[5] = "55.20%"
        path = os.path.join(self.work, "auction.csv")
        write_rows(path, rows)
        text = run("--out", self.work, "--auction", path, "--scope", "Account")
        self.assertIn("**Check this file:** these values are exactly the same in every period: You top of page rate 55.2% (7 periods)", text)


class Reconciles(unittest.TestCase):
    def test_campaign_rows_match_the_files_own_totals(self):
        check = DATA["checks"]["campaign_report"]
        self.assertTrue(check["matched"])
        self.assertEqual(check["difference"], 0.0)
        self.assertEqual(check["label"], "Total: Filtered campaigns")

    def test_the_you_row_agrees_with_the_campaign_report(self):
        lines = {line["scope"]: line for line in DATA["checks"]["auction"]}
        for x in lines["Plumbing | Emergency"]["against_campaign_report"]:
            self.assertAlmostEqual(x["difference"]["low_points"], 0.0, places=6)
        for x in lines["Account"]["against_campaign_report"]:
            self.assertLessEqual(x["difference"]["low_points"], 0.0)
            self.assertGreaterEqual(x["difference"]["high_points"], 0.0)

    def test_the_index_averages_one_hundred(self):
        index = DATA["seasonality"]["index"]["Without brand"]["last"]
        self.assertAlmostEqual(sum(v["clicks"] for v in index.values()) / len(index), 100.0, places=6)

    def test_a_utf16_tab_download_gives_the_same_numbers(self):
        work = tempfile.mkdtemp()
        try:
            path = os.path.join(work, "campaigns.csv")
            write_rows(path, read_rows(CAMPAIGNS), encoding="utf-16", delimiter="\t")
            run("--out", work, "--campaigns", path, "--brand", "Brand")
            with open(os.path.join(work, "market.json"), encoding="utf-8") as handle:
                again = json.load(handle)
            self.assertEqual(again["seasonality"]["totals"], DATA["seasonality"]["totals"])
        finally:
            shutil.rmtree(work)


class OtherLayouts(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def test_two_unsegmented_downloads_are_compared_as_two_months(self):
        rows = read_rows(ACCOUNT)
        paths = []
        for month, text in (("2026-09-01", "September 1, 2026 - September 30, 2026"), ("2026-10-01", "October 1, 2026 - October 31, 2026")):
            path = os.path.join(self.work, "auction-%s.csv" % month)
            write_rows(path, [["Auction insights report"], [text], rows[2][1:]] + [r[1:] for r in rows[3:] if r[0] == month])
            paths += ["--auction", path, "--scope", "Account"]
        run("--out", self.work, *paths)
        with open(os.path.join(self.work, "market.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual((data["compared"]["earlier"], data["compared"]["later"]), ("2026-09", "2026-10"))
        self.assertEqual(data["auction"][0]["gained"][0], "rapidrooter.example")

    def test_month_names_and_week_segments_are_read(self):
        rows = read_rows(EMERGENCY)
        names = {"2026-%02d-01" % m: n for m, n in ((8, "August 2026"), (9, "September 2026"), (10, "October 2026"))}
        month_path = os.path.join(self.work, "months.csv")
        write_rows(month_path, rows[:3] + [[names[r[0]]] + r[1:] for r in rows[3:] if r[0] in names])
        run("--out", self.work, "--auction", month_path, "--scope", "Plumbing | Emergency")
        with open(os.path.join(self.work, "market.json"), encoding="utf-8") as handle:
            self.assertEqual(json.load(handle)["compared"]["later"], "2026-10")
        week_path = os.path.join(self.work, "weeks.csv")
        weeks = {"2026-09-01": "Sep 28, 2026", "2026-10-01": "Oct 5, 2026"}
        write_rows(week_path, [rows[0], ["September 28, 2026 - October 11, 2026"], ["Week"] + rows[2][1:]]
                   + [[weeks[r[0]]] + r[1:] for r in rows[3:] if r[0] in weeks])
        run("--out", self.work, "--auction", week_path)
        with open(os.path.join(self.work, "market.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        self.assertEqual((data["compared"]["earlier"], data["compared"]["later"]), ("2026-09-28", "2026-10-05"))

    def test_less_than_a_year_says_seasonality_cannot_be_read(self):
        rows = read_rows(CAMPAIGNS)
        keep = ("May 2026", "June 2026", "July 2026", "August 2026", "September 2026", "October 2026")
        path = os.path.join(self.work, "short.csv")
        write_rows(path, [rows[0], ["May 1, 2026 - October 31, 2026"], rows[2]] + [r for r in rows[3:] if r[0] in keep])
        text = run("--out", self.work, "--campaigns", path)
        self.assertIn("The report covers 6 complete months. Seasonality needs at least 12, so it cannot be read from this file.", text)

    def test_real_layouts_one_auction_file_and_only_top_lost_columns(self):
        # The shapes of real downloads on 2026-11-14: one unsegmented auction insights file, and a
        # campaign report carrying Search lost top IS but not Search lost IS.
        auction = os.path.join(self.work, "auction.csv")
        write_rows(auction, [["Auction insights report"], ["November 11, 2026 - November 14, 2026"],
                             ["Display URL domain", "Impression share", "Overlap rate", "Position above rate", "Top of page rate", "Abs. Top of page rate", "Outranking share"],
                             ["rival.example", "< 10%", "11.11%", "100.00%", "94.12%", "29.41%", "27.69%"],
                             ["You", "31.15%", " --", " --", "55.56%", "8.64%", " --"],
                             ["big.example", "75.38%", "70.37%", "100.00%", "98.47%", "92.35%", "9.23%"]])
        campaigns = os.path.join(self.work, "campaigns.csv")
        write_rows(campaigns, [["Campaign report"], ["November 11, 2026 - November 13, 2026"],
                               ["Campaign", "Campaign type", "Budget", "Impr.", "Clicks", "Cost", "Conversions", "Search impr. share",
                                "Search lost top IS (rank)", "Search lost top IS (budget)"],
                               ["Brand", "Search", "10.00", "90", "2", "2.16", "0.00", "30.60%", "78.10%", "4.60%"],
                               ["Total: Account", "", "", "90", "2", "2.16", "0.00", "", "", ""]])
        text = run("--out", self.work, "--campaigns", campaigns, "--auction", auction, "--scope", "Account")
        with open(os.path.join(self.work, "market.json"), encoding="utf-8") as handle:
            data = json.load(handle)
        rows = data["auction"][0]["landscape"]["rows"]
        self.assertEqual([r["domain"] for r in rows], ["You", "big.example", "rival.example"])
        self.assertEqual(rows[2]["impression_share"]["shown"], "< 10%")
        self.assertIn("so it is not read as share lost", text)
        self.assertNotIn("78.1%", text)
        self.assertNotIn("None", text)


class PlainMessages(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.work)

    def refused(self, done, *parts):
        self.assertNotEqual(done.returncode, 0)
        self.assertNotIn("Traceback", done.stderr)
        for part in parts:
            self.assertIn(part, done.stderr)

    def test_a_missing_column_is_a_plain_message(self):
        path = os.path.join(self.work, "auction.csv")
        with open(path, "w", encoding="utf-8") as handle:
            handle.write('Auction insights report\n"October 1, 2026 - October 31, 2026"\nDisplay URL domain,Overlap rate,Position above rate,Outranking share\nYou, --, --, --\n')
        self.refused(call("--out", self.work, "--auction", path), "Impression share")

    def test_the_campaign_a_file_covers_is_read_from_its_title_rows(self):
        rows = read_rows(EMERGENCY)
        path = os.path.join(self.work, "auction.csv")
        write_rows(path, [["Auction insights report: Plumbing | Emergency"]] + rows[1:])
        text = run("--out", self.work, "--campaigns", CAMPAIGNS, "--auction", path)
        with open(os.path.join(self.work, "market.json"), encoding="utf-8") as handle:
            source = json.load(handle)["inputs"]["auction"][0]
        self.assertEqual((source["covers"], source["scope_source"]), ("Plumbing | Emergency", "read from its title rows"))
        self.assertIn("Is one of the campaigns listed at the top a brand campaign?", text)
        self.refused(call("--out", self.work, "--auction", ACCOUNT, "--auction", HEATERS), "do not say which campaigns they cover", "--scope")

    def test_a_wrong_campaign_name_is_refused(self):
        self.refused(call("--out", self.work, "--campaigns", CAMPAIGNS, "--auction", EMERGENCY, "--scope", "Emergency"), "Plumbing | Emergency")
        self.refused(call("--out", self.work, "--campaigns", CAMPAIGNS, "--brand", "Northside Brand"), "Brand; Drain Cleaning | Search")

    def test_a_period_not_in_the_files_is_refused(self):
        self.refused(call("--out", self.work, "--auction", ACCOUNT, "--earlier", "2026-01", "--later", "2026-10"), "2026-05, 2026-06")

    def test_a_device_split_is_refused(self):
        rows = read_rows(ACCOUNT)
        path = os.path.join(self.work, "device.csv")
        write_rows(path, rows[:2] + [["Device"] + rows[2]] + [[d] + r for r in rows[3:] for d in ("Mobile phones", "Computers")])
        self.refused(call("--out", self.work, "--auction", path), "Device")


class Deliverables(unittest.TestCase):
    def test_files_are_valid_and_carry_no_vendor_name(self):
        self.assertEqual(sorted(os.listdir(OUT)), ["competitive-and-market.md", "competitive-and-market.xlsx", "market.json"])
        for name in os.listdir(OUT):
            full = os.path.join(OUT, name)
            if name.endswith(".xlsx"):
                with zipfile.ZipFile(full) as archive:
                    self.assertIn(b"Share of voice", archive.read("xl/workbook.xml"))
                    for member in archive.namelist():
                        content = archive.read(member)
                        minidom.parseString(content)
                        self.assertNotIn(b"parallel", content.lower(), member)
            else:
                with open(full, encoding="utf-8") as handle:
                    self.assertNotIn("parallel", handle.read().lower(), name)

    def test_every_playbook_is_named_in_skill_md_and_exists(self):
        with open(os.path.join(SKILL, "SKILL.md"), encoding="utf-8") as handle:
            named = set(re.findall(r"playbooks/([\w.-]+\.md)", handle.read()))
        present = set(os.listdir(os.path.join(SKILL, "playbooks")))
        self.assertTrue(named, "SKILL.md names no playbook")
        self.assertEqual(named - present, set(), "named in SKILL.md but missing")
        self.assertEqual(present - named, set(), "in playbooks/ but not named in SKILL.md")


if __name__ == "__main__":
    unittest.main()
