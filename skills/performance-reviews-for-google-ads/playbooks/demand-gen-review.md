# Playbook: Demand Gen review

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Whether a Demand Gen campaign has the data, the budget and the stability to be judged, and what may change this week. It reads the DEMAND GEN section that `scripts/review.py` prints from the campaign report by Day when the Campaign type column names a Demand Gen campaign, plus that campaign's rows in the other reviews.

## When to use it

- "How is Demand Gen doing", "should I move it to Target CPA", "can I raise the target", "is the budget enough", "should I migrate Display".
- Demand Gen has its own rules. Google's Search guidance on targets and learning does not carry over. Official (references/demand-gen.md).
- Its placements and videos are read with `placements-and-video.md`, its ads with `ads-and-landing-pages.md`, its audiences with `segment-splits.md`. The rules here come first when they disagree.

## What to read in the output

- The first DEMAND GEN line: Google's thresholds.
- One line per campaign: status, bid strategy, conversions "on N days with rows", the band ("under 30", "30 to 50", "50 or more"), "Conversions by week, newest first", and the budget check: "is N times the Target CPA ...; 10 times would be ...", or the nearest check against its own cost per conversion.
- With a Target CPA: "A weekly Target CPA step of 5% to 10% is ... to ...; 15% is ...".
- "The first Demand Gen row is dated ..., after the report's start": a new or migrated campaign.
- The campaign's row in the weekly review table.
- No DEMAND GEN section and the line "This file has no Campaign type column": ask for the campaign report again with Campaign type, Budget and Target CPA.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Band "under 30" | Too few conversions to judge a change, and the campaign may still be learning | No bid or target change on this data. Quote the weekly conversions so the person sees the pace | Official (references/demand-gen.md: 30 to 50 conversions before judging a change; learning up to around 50 conversions or 3 conversion cycles) |
| Maximize conversions and band "50 or more" | Enough to move to a target | Moving to Target CPA or Target ROAS is open. The printed cost / conv. is the evidence for the first Target CPA; choosing it is a judgment | Official (references/demand-gen.md) |
| Moving to Target ROAS | Value based bidding | Start about 20% below the campaign's history, and make no bid or creative change for 14 days | Official (references/demand-gen.md) |
| Budget under "10 times would be ..." | Below Google's budget guide | Raise the budget toward the printed figure, or do not judge the campaign's results as final while it stays under | Official (references/demand-gen.md) |
| Only the nearest check is printed (no Target CPA) | The rule is stated against a target; this compares with actual cost per conversion | Use it as an indication and say it is not Google's exact test | Practitioner rule |
| Conversions by week rising from a low first week, or a late first row | A new or migrated campaign still ramping | Do not read the week over week change as a decline | Practitioner rule (references/demand-gen.md: learning) |
| Weekly table Worse for the campaign, band 30 or more | A real dip on enough data | Ask what changed in the last weeks: a settings change restarts some or all learning. If a target change is due, use the printed 5% to 10% step, never more than 15% | Official (references/demand-gen.md) |
| The person wants a different conversion goal | Changing the goal on a live campaign | Start a new campaign instead | Official (references/demand-gen.md) |
| Demand Gen ads trailing siblings in the ads review | Creative to refresh | Add new assets first. Remove only assets that ran at least 14 days and missed the goal | Official (references/demand-gen.md) |
| Unsuitable placements for the campaign | Demand Gen serves on the Display Network | Exclude them. Brand safety sits in account level content suitability, and Google's pages disagree on per campaign exclusions, so check the account | Official (references/demand-gen.md) |
| A Display campaign the person wants to migrate | A one way move | It carries settings and up to 42 days of history and cannot be turned back. Not during a lift study | Official (references/demand-gen.md) |
| Comparing Demand Gen with paid social | Two networks crediting the same customers | Compare in Google Ads with the columns Google provides for it, and reconcile against the business's own sales. Never add two platforms' conversions | Practitioner rule |

## Check by eye

No export this skill reads shows these. Name them as checks for the person:

- The channel split (YouTube, Discover, Gmail, Maps, Display): the channel performance report covers Demand Gen. Google recommends all channels; forcing one costs efficiency. Official (references/demand-gen.md).
- The date of the last settings, bid or creative change, from change history.
- Content suitability settings and the Lookalike segment setting.
- Which conversion actions the campaign bids on. A Demand Gen campaign optimizing to a soft action looks cheap and books little.

## How big a change

All Official, from references/demand-gen.md, and printed by the review where they need arithmetic:

- 30 to 50 conversions before judging a change. 50 before moving from Maximize conversions to a target.
- Daily budget at least 10 times the Target CPA.
- Bid or target changes of 5% to 10% a week, never more than 15%. No changes during learning.
- Value based bidding: nothing for 14 days; Target ROAS about 20% below history.
- Creative: replace only assets that ran at least 14 days.

## Failure modes

- **Judging Demand Gen by Search's yardstick.** It reaches people before they search, so a Search cost per conversion is not its benchmark. Read it on its own thresholds.
- **Weekly target changes before 30 conversions.** Each change restarts learning.
- **Removing assets before adding new ones.**
- **Adding conversions across platforms.** One customer, credited twice.
- **Flattening it into Display or YouTube.** Official (references/display-video.md).

## Worked example

The Northside sample runs no Demand Gen campaign, so its review prints no DEMAND GEN section. The skill's test adds one, "Demand Gen | Homeowners" on Target CPA, and the review prints:

- 28 conversions on 28 days with rows, under 30; cost 1,960.00, cost / conv. 70.00; conversions by week 7, 7, 7, 7.
- Daily budget 300.00 is 5 times the Target CPA of 60.00; 10 times would be 600.00. A weekly step of 5% to 10% is 3.00 to 6.00.
- The call: no target change, because 28 conversions is under 30. The budget is under Google's guide, so raise it toward 600.00 or hold judgment on the 70.00 cost per conversion until it is.

## What to tell the client

"Demand Gen is steady at about 7 leads a week, but it is still short of the volume Google asks for before judging a change, and its daily budget is 300.00 where Google's guide for its target is 600.00. I would leave the target alone and raise the budget before deciding whether it works for you."
