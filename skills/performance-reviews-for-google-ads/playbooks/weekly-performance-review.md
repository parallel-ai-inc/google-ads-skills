# Playbook: Weekly performance review

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The weekly review says what moved in the last 7 days against the 7 before, which campaigns carry the movement, which lever moved, and the day it started. It reads the WEEKLY PERFORMANCE REVIEW section that `scripts/review.py` prints from the campaign report by Day.

## When to use it

- The weekly check in: "how did we do", "leads are down", "what changed this week".
- Use it to name the movement and where it sits. The cause belongs to the performance diagnosis skill in this pack, which lines up the account changes made before the shift day.
- Keyword, ad, device or page findings come from the other reviews. Open `keywords-and-quality-score.md`, `ads-and-landing-pages.md` or `segment-splits.md` for those.
- When the review also prints a DEMAND GEN section, open `demand-gen-review.md` for those campaigns.

## What to read in the output

- "Last 7 days, ... against the 7 before, ...": the two windows. Quote them.
- The lines **Account**, **Without brand** and **Brand campaigns**, each ending "Cost per conversion against the week before": In line, Better or Worse, with its main lever.
- "The change in conversions, by campaign, adds up to the account's change of ...": the answer to "which campaign".
- The lever lines: the split across how often ads showed, click through rate and conversion rate, "Main lever", and "Its daily ... shifted on <day>" or "No single day splits its daily series clearly".
- The paused lines ("Its drop is not a loss to fix"), the campaign table's Status column, and "Trend, 7 days at a time, newest first".
- Warnings: "Only N of the ... have rows", "The first row is dated ... after the report's start", and the missing Campaign type line.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Account In line, and no campaign judged Better or Worse | Normal week to week noise | Say the week was steady, in one line. Do not build a story or a list of drivers | Practitioner rule |
| Without brand Worse, Brand campaigns In line | The movement is in paid demand, not in people looking for the business | Lead with the non brand line. Brand cost per conversion would hide it in the account line | Practitioner rule |
| One campaign carries most of the "change in conversions, by campaign" | That campaign is the story | Name it first, with its own lever line. Call the rest In line by name | Practitioner rule |
| Main lever: conversion rate | Clicks arrived but did not convert | Check conversion tracking, the landing page and the offer for that campaign from the shift day, before any bid or budget change | Practitioner rule (references/reporting-and-diagnostics.md: measurement before structure) |
| Main lever: how often ads showed | Fewer impressions: budget, bids, eligibility, policy or demand | Check serving, billing and policy first, then budget. Send the person to the performance diagnosis skill for the cause | Practitioner rule (references/reporting-and-diagnostics.md) |
| Main lever: click through rate | Same impressions, fewer clicks: ads or the search mix changed | Look at the ads review and the search terms skill for that campaign | Practitioner rule |
| A shift day is printed | The day the daily series changed level | Quote it as the day to check change history against. Change history covers 2 years, and auto applied recommendations show in it | Official (references/reporting-and-diagnostics.md) |
| "No single day splits its daily series clearly" | A slow drift, not a break | Read the trend table. Do not point to one event | Practitioner rule |
| Trend: three earlier weeks close together, the last week apart | A new step change | Call it new. It is worth diagnosing this week | Practitioner rule |
| Trend: the weeks already falling before the last one | A drift that started earlier | Say so, and give the week it started from the trend table | Practitioner rule |
| A campaign shows "Paused now", "Removed now" or "Ended" | Its cost and conversions stopped on purpose | Name it as paused. Never call its drop a loss or a decline | Practitioner rule |
| Status "Cannot judge" | No conversions in either window | Report the cost only | Practitioner rule |
| "Only N of the last 7 days have rows" | The file is short, or the campaigns did not serve | Ask the person before reading a drop from those days | Practitioner rule |
| Conversions down in the last 7 days | Some can still arrive late | Call the last week provisional. The file cannot show the account's conversion delay, so ask or check it in Google Ads | Practitioner rule |

## How big a change

- A weekly review ends with one or two actions with the clearest evidence, not a list of small changes. Practitioner rule (references/daily-optimization.md).
- Review bid strategy reports before changing a target or a budget. Practitioner rule (references/daily-optimization.md).
- The weekly review gives no step size for bids or budgets, and no source here does. If the person asks, send them to the bidding and scaling skill in this pack, and say the weekly review cannot size it.

## Failure modes

- **Explaining the cause from this file.** It shows what moved and when, never why. Every "because" needs a printed number or the diagnosis skill.
- **Brand hiding the drop.** Cheap brand conversions hold the account line up. Check: compare Account and Without brand. If no brand campaign was named, the review says so; ask for the names.
- **A paused campaign called a decline.** Check the Status column before naming any campaign as down.
- **Adding across campaigns by hand.** Use the "adds up to" lines.
- **A percent without its base.** A large percent on a small campaign is few conversions. Quote the Conv. change column.
- **Changing bids on a conversion rate drop.** Bids do not fix a broken form or tracking fault.

## Worked example

Northside Plumbing, last 7 days 2026-11-06 to 2026-11-12 against 2026-10-30 to 2026-11-05.

- Account conversions 39.46, was 51.98 (-24%), on cost 3,425.03, was 3,680.96 (-7%). Without brand: Worse, conversion rate. Brand campaigns: In line, 6.34 against 6.51 per conversion.
- Plumbing | Emergency carries -10.70 of the account's -12.52. Its main lever is conversion rate (95% of its change), which shifted on 2026-11-06 from 9.6% a day to 4.7%.
- The trend shows 51.99, 51.20 and 51.98 conversions in the three weeks before, so this is a new step down.
- Drain Cleaning | Old is paused now; its drop of 109.66 in cost is not a loss.
- The call: one action. Check tracking and the emergency landing page from 2026-11-06, through the performance diagnosis skill, before touching bids or budgets.

## What to tell the client

"Leads fell last week, 39.46 against 51.98, on about the same spend. Almost all of the drop is in the Emergency campaign, where the share of clicks that became leads fell from 9.6% to 4.7% from November 6. Traffic and brand searches held steady. I am checking the tracking and the emergency page from that day before changing any bids or budgets."
