#!/usr/bin/env python3
"""Write sample search results for the live data skill.

SYNTHETIC DATA. The business, the campaigns and every number are made up.
These files stand in for what Google's Google Ads MCP search tool returns. Its
exact output shape is not documented, so the samples use three shapes the
converter must read:
- a list of rows keyed by field path (most files),
- nested objects in camel case with int64 values as strings and zero values
  left out, inside a "results" wrapper (search terms),
- a text content wrapper holding the rows as JSON text (keywords).

Planted problems the skill must surface:
1. The ads search returned exactly its limit of 6 rows, so it may be cut off.
2. "Old call tracking" is not an enabled conversion action but still recorded
   conversions, so the summary must say they are left out.
3. "Drain Cleaning | Search" is paused. Its keywords must read "Campaign paused".
4. Its impression share was reported as 0.0999, which must read "< 10%".
5. "GA4 generate_lead" records nothing from 2026-11-04 while clicks carry on.

    python3 dev/samples/make_samples_live-data.py
"""
import datetime as dt
import json
import os
import random

HERE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "examples")
OUT = os.path.join(HERE, "exports", "live-data")
TODAY = dt.date(2026, 11, 13)
LAST = dt.date(2026, 11, 12)
FIRST_30, FIRST_60 = LAST - dt.timedelta(days=29), LAST - dt.timedelta(days=59)
PAUSED_ON = dt.date(2026, 11, 5)
CUSTOMER = "1234567890"
CAMPAIGNS = [
    # name, id, status, budget, strategy, clicks a day, cpc, conv rate, value per conv, impression share, lost to budget
    ("Plumbing | Emergency", 111, "ENABLED", 240.0, "MANUAL_CPC", 27, 8.9, 0.22, 300.0, 0.51, 0.32),
    ("Plumbing | Water Heaters", 222, "ENABLED", 160.0, "MAXIMIZE_CONVERSIONS", 17, 6.9, 0.11, 520.0, 0.58, 0.21),
    ("Drain Cleaning | Search", 333, "PAUSED", 120.0, "MAXIMIZE_CONVERSIONS", 15, 6.1, 0.09, 210.0, 0.0999, 0.04),
    ("Brand", 444, "ENABLED", 40.0, "MANUAL_CPC", 15, 1.5, 0.30, 300.0, 0.92, 0.0),
]
AD_GROUPS = [("Plumbing | Emergency", "Emergency", 1001), ("Plumbing | Emergency", "Burst Pipes", 1002),
             ("Plumbing | Water Heaters", "Repair", 2001), ("Plumbing | Water Heaters", "Install", 2002),
             ("Drain Cleaning | Search", "Drains", 3001), ("Brand", "Brand", 4001)]
STATUS = {c[0]: c[2] for c in CAMPAIGNS}
MICROS = 1000000


def write(name, data):
    with open(os.path.join(OUT, name), "w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=1)


def days(first, last):
    day = first
    while day <= last:
        yield day
        day += dt.timedelta(days=1)


def daily(rng):
    rows = []
    for day in days(FIRST_60, LAST):
        for name, cid, status, budget, strategy, clicks, cpc, rate, value, share, lost in CAMPAIGNS:
            if status == "PAUSED" and day >= PAUSED_ON:
                continue  # a paused campaign has no rows: Google returns no row without metrics
            n = max(1, int(round(clicks * rng.uniform(0.8, 1.2))))
            cost = round(n * cpc * rng.uniform(0.9, 1.1), 2)
            conv = round(n * rate * rng.uniform(0.6, 1.4), 2)
            impressions = int(n / rng.uniform(0.05, 0.09))
            rows.append({"segments.date": day.isoformat(), "campaign.name": name, "campaign.status": status,
                         "campaign_budget.amount_micros": int(budget * MICROS), "campaign_budget.period": "DAILY",
                         "campaign.advertising_channel_type": "SEARCH", "campaign.bidding_strategy_type": strategy,
                         "metrics.impressions": impressions, "metrics.clicks": n, "metrics.cost_micros": int(cost * MICROS),
                         "metrics.conversions": conv, "metrics.conversions_value": round(conv * value, 2),
                         "metrics.search_impression_share": share if share == 0.0999 else round(share * rng.uniform(0.95, 1.05), 4),
                         "metrics.search_budget_lost_impression_share": round(lost * rng.uniform(0.9, 1.1), 4)})
    return rows


def campaigns(by_day):
    out = {}
    for row in by_day:
        if row["segments.date"] < FIRST_30.isoformat():
            continue
        slot = out.setdefault(row["campaign.name"], {k: v for k, v in row.items() if not k.startswith("metrics.") and k != "segments.date"})
        for key in ("metrics.impressions", "metrics.clicks", "metrics.cost_micros", "metrics.conversions", "metrics.conversions_value"):
            slot[key] = round(slot.get(key, 0) + row[key], 2)
        slot.setdefault("_share", []).append(row["metrics.search_impression_share"])
        slot.setdefault("_lost", []).append(row["metrics.search_budget_lost_impression_share"])
    rows = []
    for name, slot in out.items():
        share, lost = slot.pop("_share"), slot.pop("_lost")
        slot["campaign_budget.name"] = name
        slot["metrics.impressions"] = int(slot["metrics.impressions"])
        slot["metrics.clicks"] = int(slot["metrics.clicks"])
        slot["metrics.cost_micros"] = int(slot["metrics.cost_micros"])
        slot["metrics.ctr"] = round(slot["metrics.clicks"] / slot["metrics.impressions"], 6)
        slot["metrics.average_cpc"] = int(slot["metrics.cost_micros"] / slot["metrics.clicks"])
        slot["metrics.cost_per_conversion"] = int(slot["metrics.cost_micros"] / slot["metrics.conversions"]) if slot["metrics.conversions"] else 0
        slot["metrics.search_impression_share"] = 0.0999 if 0.0999 in share else round(sum(share) / len(share), 4)
        slot["metrics.search_rank_lost_impression_share"] = round(max(0.0, 1 - slot["metrics.search_impression_share"] - sum(lost) / len(lost)), 4)
        slot["metrics.search_budget_lost_impression_share"] = round(sum(lost) / len(lost), 4)
        rows.append(slot)
    rows.sort(key=lambda r: -r["metrics.cost_micros"])
    return rows


def search_terms():
    terms = [("emergency plumber near me", "Plumbing | Emergency", "Emergency", "PHRASE", "NONE", 212, 9.0, 31),
             ("24 hour plumber", "Plumbing | Emergency", "Emergency", "EXACT", "ADDED", 148, 8.6, 22),
             ("burst pipe repair", "Plumbing | Emergency", "Burst Pipes", "PHRASE", "NONE", 60, 8.2, 8),
             ("plumber jobs near me", "Plumbing | Emergency", "Emergency", "BROAD", "NONE", 14, 6.5, 0),
             ("plumbing apprenticeship", "Plumbing | Emergency", "Emergency", "BROAD", "NONE", 9, 6.0, 0),
             ("how to fix a leaking pipe", "Plumbing | Emergency", "Burst Pipes", "BROAD", "NONE", 12, 5.5, 0),
             ("water heater installation", "Plumbing | Water Heaters", "Install", "NEAR_PHRASE", "NONE", 70, 7.9, 9),
             ("tankless water heater repair", "Plumbing | Water Heaters", "Repair", "PHRASE", "NONE", 25, 7.0, 3),
             ("water heater element replacement diy", "Plumbing | Water Heaters", "Repair", "BROAD", "NONE", 8, 5.0, 0),
             ("drain cleaning near me", "Drain Cleaning | Search", "Drains", "PHRASE", "NONE", 90, 5.1, 12),
             ("drain snake rental", "Drain Cleaning | Search", "Drains", "BROAD", "NONE", 11, 4.2, 0),
             ("northside plumbing", "Brand", "Brand", "EXACT", "ADDED", 120, 1.5, 30),
             ("northside plumbing reviews", "Brand", "Brand", "NEAR_EXACT", "NONE", 18, 1.4, 2)]
    rng = random.Random(7)
    results = []
    for term, campaign, ad_group, match, status, clicks, cpc, conv in terms:
        impressions = int(clicks / rng.uniform(0.04, 0.09))
        cost = int(clicks * cpc * MICROS)
        metrics = {"impressions": str(impressions), "clicks": str(clicks), "ctr": round(clicks / impressions, 6),
                   "averageCpc": str(int(cpc * MICROS)), "costMicros": str(cost)}
        if conv:  # zero values are left out, as JSON results do
            metrics.update({"conversions": float(conv), "costPerConversion": str(int(cost / conv)), "conversionsValue": float(conv * 300)})
        results.append({"searchTermView": {"searchTerm": term, "status": status}, "segments": {"searchTermMatchType": match},
                        "campaign": {"name": campaign, "advertisingChannelType": "SEARCH"}, "adGroup": {"name": ad_group},
                        "metrics": metrics})
    return {"results": results, "fieldMask": "searchTermView.searchTerm,..."}


def keywords():
    rows = []
    items = [("Emergency", "emergency plumber", "PHRASE", 7, "ABOVE_AVERAGE", "AVERAGE", "AVERAGE", 410, 8.3, 52),
             ("Emergency", "24 hour plumber", "EXACT", 8, "ABOVE_AVERAGE", "ABOVE_AVERAGE", "AVERAGE", 148, 8.6, 26),
             ("Burst Pipes", "burst pipe repair", "PHRASE", 6, "AVERAGE", "AVERAGE", "AVERAGE", 85, 8.2, 10),
             ("Repair", "water heater repair", "PHRASE", 4, "AVERAGE", "AVERAGE", "BELOW_AVERAGE", 160, 7.0, 12),
             ("Install", "water heater installation", "EXACT", 7, "AVERAGE", "ABOVE_AVERAGE", "AVERAGE", 162, 7.9, 11),
             ("Drains", "drain cleaning", "BROAD", 5, "BELOW_AVERAGE", "AVERAGE", "AVERAGE", 250, 6.1, 20),
             ("Brand", "northside plumbing", "EXACT", 10, "ABOVE_AVERAGE", "ABOVE_AVERAGE", "ABOVE_AVERAGE", 330, 1.5, 98),
             ("Install", "commercial water heater", "PHRASE", None, None, None, None, 0, 0, 0)]
    for ad_group, text, match, qs, ctr, rel, lp, clicks, cpc, conv in items:
        campaign = next(c for c, g, _ in AD_GROUPS if g == ad_group)
        row = {"ad_group_criterion.status": "ENABLED", "ad_group_criterion.keyword.text": text,
               "ad_group_criterion.keyword.match_type": match, "campaign.name": campaign, "ad_group.name": ad_group,
               "campaign.status": STATUS[campaign], "ad_group.status": "ENABLED",
               "metrics.impressions": int(clicks * 13), "metrics.clicks": clicks, "metrics.ctr": round(1 / 13, 6) if clicks else 0.0,
               "metrics.average_cpc": int(cpc * MICROS), "metrics.cost_micros": int(clicks * cpc * MICROS),
               "metrics.conversions": float(conv), "metrics.cost_per_conversion": int(clicks * cpc * MICROS / conv) if conv else 0,
               "metrics.conversions_value": float(conv * 300),
               "ad_group_criterion.quality_info.quality_score": qs,
               "ad_group_criterion.quality_info.search_predicted_ctr": ctr,
               "ad_group_criterion.quality_info.creative_quality_score": rel,
               "ad_group_criterion.quality_info.post_click_quality_score": lp}
        rows.append(row)
    return {"content": [{"type": "text", "text": json.dumps(rows)}]}


def ad_groups():
    rows = []
    for (campaign, name, gid), clicks, cpc, conv in zip(AD_GROUPS, (558, 85, 160, 162, 250, 330), (8.4, 8.2, 7.0, 7.9, 6.1, 1.5),
                                                        (78, 10, 12, 11, 20, 98)):
        cost = int(clicks * cpc * MICROS)
        rows.append({"ad_group.status": "ENABLED", "ad_group.name": name, "campaign.name": campaign, "campaign.status": STATUS[campaign],
                     "ad_group.type": "SEARCH_STANDARD", "metrics.impressions": clicks * 13, "metrics.clicks": clicks,
                     "metrics.ctr": round(1 / 13, 6), "metrics.average_cpc": int(cpc * MICROS), "metrics.cost_micros": cost,
                     "metrics.conversions": float(conv), "metrics.cost_per_conversion": int(cost / conv),
                     "metrics.conversions_value": float(conv * 300)})
    return rows


def ads():
    items = [("Emergency", "24/7 Emergency Plumber", "EXCELLENT", "APPROVED", 300, 45),
             ("Emergency", "Plumber At Your Door In 60 Min", "GOOD", "APPROVED", 258, 33),
             ("Burst Pipes", "Burst Pipe Repair Today", "AVERAGE", "APPROVED_LIMITED", 85, 10),
             ("Repair", "Water Heater Repair Experts", "POOR", "APPROVED", 160, 12),
             ("Install", "Same Week Water Heater Install", "GOOD", "DISAPPROVED", 162, 11),
             ("Brand", "Northside Plumbing Official Site", "EXCELLENT", "APPROVED", 330, 98)]
    rows = []
    for index, (ad_group, headline, strength, approval, clicks, conv) in enumerate(items):
        campaign = next(c for c, g, _ in AD_GROUPS if g == ad_group)
        rows.append({"ad_group_ad.status": "ENABLED", "ad_group_ad.ad.responsive_search_ad.headlines": [{"text": headline}, {"text": "Licensed Local Plumbers"}],
                     "ad_group_ad.ad.name": "", "ad_group_ad.ad.id": 90000 + index, "ad_group_ad.ad.type": "RESPONSIVE_SEARCH_AD",
                     "ad_group_ad.ad_strength": strength, "campaign.name": campaign, "ad_group.name": ad_group,
                     "campaign.status": STATUS[campaign], "ad_group.status": "ENABLED",
                     "ad_group_ad.policy_summary.approval_status": approval,
                     "ad_group_ad.ad.final_urls": ["https://www.northsideplumbing.example/%s" % ad_group.lower().replace(" ", "-")],
                     "metrics.impressions": clicks * 14, "metrics.clicks": clicks, "metrics.cost_micros": int(clicks * 7.1 * MICROS),
                     "metrics.conversions": float(conv)})
    return rows


def conversion_actions():
    settings = [("Website lead form", True, "WEBPAGE", "SUBMIT_LEAD_FORM", "MANY_PER_CLICK", 30, 1),
                ("GA4 generate_lead", True, "GOOGLE_ANALYTICS_4_CUSTOM", "SUBMIT_LEAD_FORM", "ONE_PER_CLICK", 30, 0),
                ("Calls from ads", True, "AD_CALL", "PHONE_CALL_LEAD", "ONE_PER_CLICK", 30, 0),
                ("Directions clicks", False, "WEBPAGE", "GET_DIRECTIONS", "MANY_PER_CLICK", 30, 1)]
    rows = [{"conversion_action.name": n, "conversion_action.primary_for_goal": p, "conversion_action.type": t,
             "conversion_action.category": c, "conversion_action.counting_type": k,
             "conversion_action.click_through_lookback_window_days": ct, "conversion_action.view_through_lookback_window_days": vt,
             "conversion_action.attribution_model_settings.attribution_model": "GOOGLE_SEARCH_ATTRIBUTION_DATA_DRIVEN"}
            for n, p, t, c, k, ct, vt in settings]
    split = {"Plumbing | Emergency": 0.5, "Plumbing | Water Heaters": 0.25, "Drain Cleaning | Search": 0.1, "Brand": 0.15}
    totals = {"Website lead form": (100, 100, 150), "GA4 generate_lead": (60, 92, 150), "Calls from ads": (70, 70, 100),
              "Directions clicks": (0, 40, 0), "Old call tracking": (0, 18, 0)}
    by_action = []
    for action, (conv, all_conv, value) in totals.items():
        for campaign, share in split.items():
            by_action.append({"segments.conversion_action_name": action, "metrics.conversions": round(conv * share, 2),
                              "metrics.conversions_value": round(conv * share * value, 2),
                              "metrics.all_conversions": round(all_conv * share, 2),
                              "metrics.all_conversions_value": round(all_conv * share * value, 2)})
    return rows, by_action


def conversions_by_day(rng):
    rows = []
    rates = {"Website lead form": 3.0, "GA4 generate_lead": 2.6, "Calls from ads": 2.2}
    for day in days(FIRST_60, LAST):
        for action, rate in rates.items():
            if action == "GA4 generate_lead" and day >= dt.date(2026, 11, 4):
                continue  # the planted break: Google returns no row for a day with no conversions
            for campaign, share in (("Plumbing | Emergency", 0.65), ("Plumbing | Water Heaters", 0.35)):
                conv = round(rate * share * rng.uniform(0.7, 1.3), 2)
                rows.append({"segments.date": day.isoformat(), "segments.conversion_action_name": action, "campaign.name": campaign,
                             "campaign.status": "ENABLED", "metrics.conversions": conv, "metrics.all_conversions": conv,
                             "metrics.conversions_value": round(conv * 150, 2), "metrics.all_conversions_value": round(conv * 150, 2)})
    return rows


def change_history():
    def event(when, kind, op, fields, campaign=None, ad_group=None, user="manager@example.com", client="GOOGLE_ADS_WEB_CLIENT"):
        return {"change_event.change_date_time": when, "change_event.user_email": user, "change_event.client_type": client,
                "change_event.change_resource_type": kind, "change_event.resource_change_operation": op,
                "change_event.changed_fields": fields,
                "change_event.campaign": "customers/%s/campaigns/%d" % (CUSTOMER, campaign) if campaign else "",
                "change_event.ad_group": "customers/%s/adGroups/%d" % (CUSTOMER, ad_group) if ad_group else ""}
    events = [event("2026-11-10 09:12:03.204118", "CAMPAIGN_BUDGET", "UPDATE", "amountMicros", 111),
              event("2026-11-05 16:40:11.000000", "CAMPAIGN", "UPDATE", "status", 333),
              event("2026-10-30 09:02:44.517000", "AD_GROUP_CRITERION", "CREATE", "keyword.text,keyword.matchType,status", 333, 3001),
              event("2026-10-28 11:00:41.000000", "CAMPAIGN", "UPDATE", "biddingStrategyType,maximizeConversions", 222),
              event("2026-10-21 07:30:00.000000", "AD_GROUP_AD", "UPDATE", "status", 222, 2002,
                    user="Recommendations", client="GOOGLE_ADS_RECOMMENDATIONS")]
    names = [{"campaign.resource_name": "customers/%s/campaigns/%d" % (CUSTOMER, cid), "campaign.name": name}
             for name, cid, *_ in CAMPAIGNS]
    groups = [{"ad_group.resource_name": "customers/%s/adGroups/%d" % (CUSTOMER, gid), "ad_group.name": name}
              for _, name, gid in AD_GROUPS]
    return events, names, groups


def main():
    rng = random.Random(42)
    os.makedirs(OUT, exist_ok=True)
    by_day = daily(rng)
    write("campaigns-by-day.result.json", by_day)
    write("campaigns.result.json", campaigns(by_day))
    write("search-terms.result.json", search_terms())
    write("keywords.result.json", keywords())
    write("ad-groups.result.json", ad_groups())
    write("ads.result.json", ads())
    settings, by_action = conversion_actions()
    write("conversion-actions.result.json", settings)
    write("conversions-by-action.result.json", by_action)
    write("conversions-by-action-and-day.result.json", conversions_by_day(rng))
    events, names, groups = change_history()
    write("change-history.result.json", events)
    write("campaign-names.result.json", names)
    write("ad-group-names.result.json", groups)
    print("Sample search results written to %s" % OUT)


if __name__ == "__main__":
    main()
