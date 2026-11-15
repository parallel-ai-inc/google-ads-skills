#!/usr/bin/env python3
"""Write synthetic inputs for the campaign build skill to examples/exports/campaign-build/.

Northside Plumbing wants a new Search campaign for sewer line work. The
folder gets the account's campaigns report and keywords report, laid out the
way Google Ads downloads them, and two plans as the AI tool would write them:

- example-plan-first-draft.json, with four planted problems the check must refuse:
  a list negative "camera" that blocks two of the build's own keywords, the
  phrase keyword "broken sewer line" in two ad groups, a 33 character
  headline, and a 17 character path.
- example-plan.json, the same plan with those fixed. It still repeats a
  keyword the account already has, which the check must warn about.

    python3 dev/samples/make_samples_campaign-build.py
"""
import copy
import csv
import json
import os
import random

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples")
OUT = os.path.join(ROOT, "exports", "campaign-build")
EMERGENCY, HEATERS, DRAINS, BRAND = "Plumbing | Emergency", "Plumbing | Water Heaters", "Drain Cleaning | Search", "Brand"
SITE = "https://www.northsideplumbing.example"


def fmt(value, places=2):
    return "{:,.{p}f}".format(value, p=places)


def write(name, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as handle:
        csv.writer(handle).writerows(rows)


def campaigns_report(rng):
    header = ["Campaign status", "Campaign", "Budget", "Budget type", "Currency code", "Status", "Campaign type",
              "Bid strategy type", "Cost", "Impr.", "Clicks", "Conversions"]
    specs = [("Enabled", EMERGENCY, 240.0, "Maximize Conversions"), ("Enabled", HEATERS, 160.0, "Target CPA"),
             ("Enabled", DRAINS, 90.0, "Maximize Conversions"), ("Enabled", BRAND, 40.0, "Maximize clicks")]
    rows, sums = [], [0.0, 0, 0, 0.0]
    for status, name, budget, strategy in specs:
        cost = round(budget * 30 * rng.uniform(0.82, 0.97), 2)
        clicks = int(cost / rng.uniform(4.5, 9.0))
        impr = clicks * rng.randint(9, 16)
        conv = round(clicks * rng.uniform(0.06, 0.14), 2)
        sums = [sums[0] + cost, sums[1] + impr, sums[2] + clicks, sums[3] + conv]
        rows.append([status, name, fmt(budget), "Daily", "USD", "Eligible", "Search", strategy, fmt(cost), fmt(impr, 0), fmt(clicks, 0), fmt(conv)])
    total = lambda label: [" --", label, " --", " --", "USD", " --", " --", " --", fmt(sums[0]), fmt(sums[1], 0), fmt(sums[2], 0), fmt(sums[3])]  # noqa: E731
    write("campaigns-report.csv", [["Campaign report"], ["October 14, 2026 - November 12, 2026"], header] + rows
          + [total("Total: Filtered campaigns"), total("Total: Account"), total("Total: Search")])


def keywords_report(rng):
    header = ["Keyword status", "Keyword", "Match type", "Campaign", "Ad group", "Status", "Final URL", "Currency code",
              "Impr.", "Interactions", "Cost", "Conversions"]
    specs = [
        ("[emergency plumber]", "Exact match", EMERGENCY, "Emergency", "/emergency"),
        ('"24 hour plumber"', "Phrase match", EMERGENCY, "Emergency", "/emergency"),
        ("plumber near me", "Broad match", EMERGENCY, "Emergency", "/emergency"),
        ('"water heater repair"', "Phrase match", HEATERS, "Water Heaters", "/water-heaters"),
        ("[tankless water heater installation]", "Exact match", HEATERS, "Water Heaters", "/water-heaters"),
        ('"drain cleaning"', "Phrase match", DRAINS, "Drains", "/drain-cleaning"),
        ("[clogged drain]", "Exact match", DRAINS, "Drains", "/drain-cleaning"),
        # Planted: the account already has this keyword. The new build repeats it.
        ('"sewer line repair"', "Phrase match", DRAINS, "Sewer Repair", "/drain-cleaning"),
        ("[northside plumbing]", "Exact match", BRAND, "Brand", "/"),
    ]
    rows, sums = [], [0, 0, 0.0, 0.0]
    for text, match, campaign, ad_group, path in specs:
        clicks = rng.randint(20, 400)
        impr = clicks * rng.randint(8, 15)
        cost = round(clicks * rng.uniform(4.0, 11.0), 2)
        conv = round(clicks * rng.uniform(0.04, 0.15), 2)
        sums = [sums[0] + impr, sums[1] + clicks, sums[2] + cost, sums[3] + conv]
        rows.append(["Enabled", text, match, campaign, ad_group, "Eligible", SITE + path, "USD", fmt(impr, 0), fmt(clicks, 0), fmt(cost), fmt(conv)])
    total = lambda label: [" --", label, " --", " --", " --", " --", " --", "USD", fmt(sums[0], 0), fmt(sums[1], 0), fmt(sums[2]), fmt(sums[3])]  # noqa: E731
    write("keywords-report.csv", [["Search keyword report"], ["October 14, 2026 - November 12, 2026"], header] + rows
          + [total("Total: Keywords in your account"), total("Total: All but removed keywords"), total("Total: Account"), total("Total: Search")])


def kw(text, match):
    return {"text": text, "match": match, "final_url": ""}


def neg(text, match, why):
    return {"text": text, "match": match, "why": why}


def fixed_plan():
    repair, replace, inspect = SITE + "/sewer-line-repair", SITE + "/sewer-line-replacement", SITE + "/sewer-camera-inspection"
    return {
        "brief": {
            "business": "Northside Plumbing, a residential plumber serving Denver and Aurora.",
            "offer": "Sewer line repair, trenchless sewer line replacement and sewer camera inspection.",
            "goal": "Booked sewer jobs from people whose sewer line has failed or who are buying a home.",
            "primary_conversion": "Booked appointment (online booking form)",
            "hypothesis": "Searches for sewer line repair, replacement and inspection in Denver and Aurora book jobs at a cost the business can carry, kept apart from drain cleaning.",
            "success_metric": "Booked sewer appointments and cost per booking over the first 30 days.",
            "early_warning": "Spend with no bookings after 14 days, or search terms about septic tanks or drain cleaning.",
            "assumptions": [
                "Maximize conversions, because the booking conversion already records in the account.",
                "Search Partners is off until results on Google Search are known.",
                "AI Max is off, because the person wants searches matched to the keywords in the plan at launch.",
                "Locations are Denver and Aurora only, the places the person named.",
                "One responsive search ad in the replacement and inspection ad groups. A second can follow once there is a different message to test.",
            ],
            "owners": {"build": "Sam", "tracking": "Lee", "landing_pages": "", "approval": "Dana", "launch": "Sam"},
            "ready": {"conversion_tracking": "yes", "billing": "yes", "landing_pages": "unknown", "budget_approved": "yes",
                      "locations_confirmed": "yes", "ad_copy_approved": "no"},
        },
        "negative_keyword_list": {"name": "Northside | Never relevant", "keywords": [
            neg("jobs", "phrase", "Job seekers"), neg("salary", "phrase", "Job seekers"), neg("diy", "phrase", "Do it yourself"),
            neg("how to", "phrase", "Do it yourself"), neg("course", "phrase", "Training"),
        ]},
        "campaigns": [{
            "name": "Sewer Line | Search", "daily_budget": 120, "bid_strategy": "Maximize conversions", "target_cpa": None,
            "target_roas_percent": None, "networks": ["Google Search"], "ai_max": "off",
            "locations": ["Denver, Colorado, United States", "Aurora, Colorado, United States"],
            "start_date": "2026-12-01", "end_date": "",
            "negatives": [neg("septic", "phrase", "The business does not service septic systems"),
                          neg("drain cleaning", "phrase", "Drain cleaning searches belong to the Drain Cleaning campaign")],
            "ad_groups": [
                {"name": "Sewer Line Repair", "max_cpc": None,
                 "keywords": [kw("sewer line repair", "phrase"), kw("sewer line repair", "exact"), kw("broken sewer line", "phrase"),
                              kw("sewer pipe repair", "phrase"), kw("main sewer line repair", "exact")],
                 "negatives": [neg("replacement", "phrase", "Sends replacement searches to the replacement ad group")],
                 "ads": [
                     {"final_url": repair, "path_1": "sewer-line", "path_2": "repair",
                      "headlines": ["Sewer Line Repair in Denver", "Broken Sewer Line? Call Us", "Licensed Denver Plumbers", "Same Day Sewer Repair",
                                    "Camera Inspection First", "Upfront Written Quotes", "Fix the Pipe, Not the Lawn", "Sewer Pipe Repair Experts",
                                    "Serving Denver and Aurora", "Main Sewer Line Repair", "Northside Plumbing", "Book a Sewer Repair Today"],
                      "descriptions": ["We find the break with a camera and show you the video before any digging starts.",
                                       "Licensed and insured plumbers. Written quote before work begins. No surprise fees.",
                                       "Sewer backing up? We repair main sewer lines across Denver and Aurora.",
                                       "Most repairs finished in one day. Book online or call to schedule a visit."]},
                     {"final_url": repair, "path_1": "sewer-line", "path_2": "repair",
                      "headlines": ["Sewer Line Repair Specialists", "Trenchless Repair Options", "Stop Sewer Backups for Good",
                                    "Denver Sewer Line Repair", "Video Camera Diagnosis", "Written Quote Before We Dig",
                                    "Licensed and Insured", "Repair Broken Sewer Pipes"],
                      "descriptions": ["Trenchless repair can save your yard. We tell you if it fits before we start.",
                                       "See the camera video of your line and get a written quote. No surprise fees.",
                                       "Local plumbers serving Denver and Aurora. Book a sewer line repair today."]},
                 ]},
                {"name": "Sewer Line Replacement", "max_cpc": None,
                 "keywords": [kw("sewer line replacement", "phrase"), kw("sewer line replacement", "exact"), kw("trenchless sewer replacement", "phrase"),
                              kw("replace sewer line", "phrase"), kw("sewer line replacement cost", "phrase")],
                 "negatives": [neg("repair", "phrase", "Sends repair searches to the repair ad group")],
                 "ads": [
                     {"final_url": replace, "path_1": "sewer-line", "path_2": "replacement",
                      "headlines": ["Sewer Line Replacement", "Trenchless Replacement", "Replace Your Sewer Line", "Denver Sewer Replacement",
                                    "Less Digging, Less Mess", "Written Quote Before We Dig", "Licensed Denver Plumbers", "Clear Upfront Pricing",
                                    "Old Clay Pipe? Replace It", "Serving Denver and Aurora", "Sewer Line Replacement Cost"],
                      "descriptions": ["Trenchless sewer line replacement with less digging. Ask if your line qualifies.",
                                       "Camera inspection first, then a written quote for the full replacement.",
                                       "Licensed and insured plumbers serving Denver and Aurora. Book an estimate today.",
                                       "We replace failing clay, cast iron and Orangeburg sewer pipes with modern pipe."]},
                 ]},
                {"name": "Sewer Camera Inspection", "max_cpc": None,
                 "keywords": [kw("sewer camera inspection", "phrase"), kw("sewer line inspection", "phrase"), kw("sewer scope inspection", "exact"),
                              kw("sewer line camera inspection", "exact")],
                 "negatives": [],
                 "ads": [
                     {"final_url": inspect, "path_1": "sewer", "path_2": "inspection",
                      "headlines": ["Sewer Camera Inspection", "See Inside Your Sewer Line", "Sewer Line Inspection", "Buying a Home? Scope It",
                                    "Video of Your Sewer Line", "Licensed Denver Plumbers", "Same Week Appointments", "Find Roots, Cracks, Breaks",
                                    "Sewer Scope Inspection", "Serving Denver and Aurora"],
                      "descriptions": ["A camera inspection shows roots, cracks and breaks. You get the video and a report.",
                                       "Buying a home? Scope the sewer line before you close. Book an inspection today.",
                                       "Licensed plumbers serving Denver and Aurora. Clear pricing before we start."]},
                 ]},
            ],
        }],
    }


def first_draft(plan):
    """The same plan with four problems a practitioner would catch in review."""
    draft = copy.deepcopy(plan)
    draft["negative_keyword_list"]["keywords"].append(neg("camera", "phrase", "People shopping for inspection cameras"))
    groups = draft["campaigns"][0]["ad_groups"]
    groups[1]["keywords"].append(kw("broken sewer line", "phrase"))
    groups[1]["ads"][0]["headlines"][1] = "Trenchless Sewer Line Replacement"
    groups[1]["ads"][0]["path_1"] = "sewer-replacement"
    return draft


def main():
    os.makedirs(OUT, exist_ok=True)
    rng = random.Random(20261113)
    campaigns_report(rng)
    keywords_report(rng)
    plan = fixed_plan()
    for name, data in (("example-plan.json", plan), ("example-plan-first-draft.json", first_draft(plan))):
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=1, ensure_ascii=False)
    print("Wrote the campaign build samples to %s" % OUT)


if __name__ == "__main__":
    main()
