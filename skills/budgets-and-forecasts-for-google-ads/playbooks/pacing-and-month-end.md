# Playbook: Check pacing and land the month

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: say whether this month lands on the person's spend target, which campaigns drive the answer, and what to change this week. It reads the "Account" and "Campaigns" sections of the summary `scripts/pacing.py` prints.

## When to use it

- The person asks how budgets are pacing, whether the account will overspend or underspend, or what to change before the month closes.
- Where to move budget between campaigns, or what to do about a campaign that is held out: open `moving-budget-between-campaigns.md`.
- Next month's budget, scenarios, or how many conversions a budget will bring: open `budget-planning-and-forecasts.md`.

## What to read in the output

- The line "Month ..., read through ...: day N of M, K days left", and the warning "The report starts on ..." when it appears.
- Under "Account": "Spend so far", the two forecasts, "Google's monthly limit across the campaigns that are serving", the bold "Forecast once each campaign stops at its monthly limit" (the capped forecast), "Your target for the month", and the bold line "The forecast once limits apply is X above (or below) the target: about Y a day for the K days left".
- Under "Campaigns": "Status" and "Limited by budget" for each campaign.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| The target is a ceiling and the capped forecast is above it | The month overshoots even after Google slows the campaigns that reach their limit | Take the printed "about Y a day" out of the daily budgets of campaigns whose Status is "Will reach Google's monthly limit" or "On pace to use the budget". Take it first from a campaign that is held out, last from one that "could take more". Call it a spend control, not a verdict, and restore it once the cause is known | Practitioner rule |
| The target is a ceiling and the capped forecast is at or below it | The month lands inside the ceiling at today's pace | No pacing change. Say how many days are left and that the forecast assumes the recent pace | Practitioner rule |
| The target is a goal and the capped forecast is below it | There is room to spend "about Y a day" more | Add budget only where Limited by budget is "Yes", through `moving-budget-between-campaigns.md` | Practitioner rule |
| "Will reach Google's monthly limit around" a date | Google bills at most 30.4 times the daily budget in a month, so the campaign slows or stops near that date | Say "around" the date. The capped forecast already counts it. Decide whether the campaign's leads matter enough late in the month to raise its budget | Official (references/spend-troubleshooting.md) |
| Spend above the daily budget on some days | Google can spend up to twice the daily budget on one day | Not a fault. Judge the month against the monthly limit | Official (references/spend-troubleshooting.md) |
| "Underspending the budget" | Budget is not what holds it back | Never lower its budget to save money: that lowers nothing it spends. Check eligibility, then targeting and demand, then bid strategy tightness, then what the strategy sees, in that order | Practitioner rule, order from references/spend-troubleshooting.md |
| Limited by budget "Yes" on a Maximize conversions or Maximize conversion value campaign | These strategies are limited by budget by design | Do not read lost impression share as room. Point to the budget simulator | Official (references/spend-troubleshooting.md) |
| "The report starts on ..." | Spend earlier in the month is missing, so every forecast is low | Ask for the report from the first of the month before judging a ceiling | Practitioner rule |

## How big a change

- **A ceiling cut is the printed "about Y a day".** The script spreads the gap between the capped forecast and the target over the days left. **Official** (`references/spend-troubleshooting.md`): on a day a budget is edited, the rest of the month is limited by the new budget times the remaining calendar days, so a cut made today works over those days. It is still about: Google can spend up to twice a daily budget on any one day.
- **Use the capped gap, not the pace gap.** The line "The last 7 days averaged ... a day more than that" ignores Google's limits and overstates the cut when campaigns will reach them. The script says so beside the figure.
- **Check again after a full day.** The script warns that today's partial data makes the last day look low, so read a change from a report that ends yesterday.

## Failure modes

- **Judging a ceiling on the uncapped forecast.** It shows a bigger overshoot than will be billed. Quote the bold capped line, every time.
- **Cutting a campaign that is underspending.** Its Status says so. The cut lowers Google's limit, not its spend, so the overshoot stays.
- **Calling an alert or an automated rule a ceiling.** **Practitioner rule:** reports arrive late, so nothing built on them stops spend at once. Only daily budgets, and Google's monthly limit of 30.4 times them, bound what a month costs. Say this when the person relies on an alert.
- **Shared budgets and ad schedules.** The script reads each campaign as having its own daily budget. Shared budgets are counted once per campaign, which overstates the limit. **Official** (`references/spend-troubleshooting.md`): since June 1, 2026, a campaign whose ad schedule switches off whole days and serves 15 days or fewer in a month can spend at most twice its daily budget times its active days. Ask before trusting the limit for such a campaign.
- **A target in another unit.** **Practitioner rule:** confirm the target is media spend in the report's currency, not an invoice with fees or tax.

## Worked example

Northside Plumbing, read through 2026-11-12: day 12 of 30, 18 days left, against a 15,000.00 ceiling.

- The capped forecast is 15,198.52, 101.3% of the target: 198.52 above it, about 11.03 a day.
- Plumbing | Emergency and Drain Cleaning | Search will reach Google's monthly limit around 2026-11-30 and 2026-11-28. Plumbing | Water Heaters and Brand are underspending, so cutting them saves nothing this month.
- Of the two campaigns that spend their budget, Emergency "could take more" and Drain Cleaning is held out.
- The call: lower Drain Cleaning's daily budget by about 11.03 as a spend control while its rise in cost per click is diagnosed, and leave Emergency alone. Restore Drain Cleaning once the cause is known.

## What to tell the client

"At the current pace the month finishes at about 15,198.52 against your 15,000.00 ceiling, even after Google's own monthly limits slow two campaigns near the end of the month. To land on 15,000.00, I would take about 11.03 a day out of Drain Cleaning, where leads got more expensive in the last two weeks, and leave Emergency, your strongest campaign, as it is. Water Heaters and Brand are not spending their full budgets, so cutting them would not save anything."
