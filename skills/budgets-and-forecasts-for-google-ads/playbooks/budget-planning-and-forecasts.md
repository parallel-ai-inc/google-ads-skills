# Playbook: Plan a budget, and answer forecast questions honestly

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: set a monthly budget from what today's budgets bill and spend, and answer scenario, sensitivity, demand and results questions by saying plainly what needs a model this skill does not have. It reads "Account", "A whole month at the target", "Campaigns", "Evidence for moving budget" and "What this did not cover" in the summary `scripts/pacing.py` prints. Run it with the planned monthly figure as `--monthly-target`.

## When to use it

- The person asks for next month's budget, or how to set daily budgets for a monthly figure.
- They ask what a bigger or smaller budget would bring, which of cost per click or conversion rate matters most, what demand will do, or how many conversions to expect.
- This month's landing: `pacing-and-month-end.md`. Where to move budget: `moving-budget-between-campaigns.md`. Seasonality and market demand: `competitive-and-market-for-google-ads`.

## What this skill measures, and what it does not

It measures the spend side, and every figure is printed:

- what today's budgets can bill in a month ("Google's monthly limit across the campaigns that are serving") and what their daily budgets total;
- what they are on pace to spend ("Forecast once each campaign stops at its monthly limit");
- the daily budget total that caps a whole month at a figure ("Daily budgets that cap a whole month at ... total ... a day") and how far today's total is from it;
- the budget underspending campaigns leave unused, and where budget limits a campaign, with its room a day.

It does not model what a different budget would buy: conversions, cost per conversion or conv. value at another budget, how cost per click or conversion rate would respond, demand ahead, seasonality, or a results forecast. "What this did not cover" lists this. Say so once, plainly, and do not estimate it.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Today's budgets total "... more than that" | Today's budgets can bill more than the planned month | Cut daily budgets by that total. Take the unused budget first: it lowers Google's limit without lowering spend. The rest ("The other ... a day") comes from campaigns that spend their budget, held out ones first, ones that "could take more" last | Practitioner rule |
| "... less than that" and "Today's budgets cannot bill the target in a full month" | The planned month is more than today's budgets can spend | Add only to campaigns that "could take more", a first step each. Money beyond their room has nowhere useful to go in today's campaigns: it needs more reach, such as keywords, locations or campaigns, not budget | Practitioner rule |
| A request for what a budget would buy | No model of response to budget here | Give the spend side above, and point to Google's budget simulator and Performance Planner, both named in `references/spend-troubleshooting.md`. Never multiply an average by a new budget | Practitioner rule |
| A request for sensitivity | Cost / conv. is Avg. CPC divided by conv. rate | Say a rise in cost per click raises cost per conversion by the same share, and a fall in conv. rate raises it a little more. The only measured split is on held out campaigns, for one change over two 14 day windows | Practitioner rule |
| A request for a demand outlook | The only trend printed is cost per conversion, 14 days against 14 | Say the skill does not read demand. Route to `competitive-and-market-for-google-ads` | Practitioner rule |
| A results target, such as a number of leads | This skill forecasts spend, not results | Turn it into what must become true: the cost per conversion the budget would need, the conversion delay, the season. Name the assumption that would most change the plan. Leave the numbers to a model | Practitioner rule |

## How big a change

- **A month bills at most 30.4 times the daily budget**, whatever its length. **Official** (`references/spend-troubleshooting.md`). That is why the printed daily total for a whole month is the planned figure divided by 30.4.
- **A daily total is not a daily stop.** **Official** (same file): a campaign can spend up to twice its daily budget on one day.
- **If the month has already started**, the whole month figure no longer fits. A change made mid month limits the rest of the month to the new budget times the remaining calendar days. **Official** (same file). Use the capped gap, "about ... a day", through `pacing-and-month-end.md` instead.
- **Raises go in steps.** A first step is at most the printed "first step", half the room. Read it after 1 to 2 conversion cycles. **Practitioner rule** for the steps; **Official** (`references/smart-bidding.md`) for the 1 to 2 cycles after a budget increase.
- **Exceptions the script does not read.** **Official** (`references/spend-troubleshooting.md`): campaign total budgets have no twice daily cap, and a campaign whose ad schedule leaves it 15 or fewer active days in a month can spend at most twice its daily budget times those days. Ask whether any campaign uses either.

## Failure modes

- **Presenting an average times a budget as a forecast.** It assumes the next dollar costs what the average did. The rule against it is in SKILL.md; hold to it even when asked twice.
- **Planning from a held out campaign's month figures.** They blend two levels. Use "Cost / conv. last 14 days".
- **Treating the analyst methods in `references/predictive-analytics.md` as done.** They describe what a forecasting model would use. This skill runs none of them.
- **Mixing units.** **Practitioner rule:** confirm the figure is media spend in the report's currency, and a ceiling or a goal.
- **Shared budgets.** Each campaign is read as having its own budget, so a shared one is counted more than once.

## Worked example

Northside Plumbing plans a 15,000.00 ceiling for next month.

- Daily budgets that cap a whole month at 15,000.00 total 493.42 a day. Today they total 560.00, 66.58 more than that.
- Underspending campaigns, Plumbing | Water Heaters and Brand on the Campaigns table, left about 60.48 a day unused. That covers 60.48 of the 66.58 cut, with no loss of traffic.
- The other 6.10 a day comes from a campaign that spends its budget. Drain Cleaning | Search is held out, so it goes there before Plumbing | Emergency, which could take more.
- Asked how many leads 15,000.00 will bring: this skill does not model that. Point to the budget simulator and Performance Planner.

## What to tell the client

"To keep next month at 15,000.00, your daily budgets should add up to 493.42, against 560.00 today. Most of the difference is budget Water Heaters and Brand are not using, so trimming it costs no traffic; the last 6.10 a day comes from Drain Cleaning. How many leads 15,000.00 will bring is a forecast this report cannot make: Google's budget simulator and Performance Planner are built for that."
