# Playbook: Seasonality, year on year, and the months ahead

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Which months usually rise or fall, whether a drop against last year is the season or the account, and what the pattern means for budget and timing in the months ahead. It reads the "Seasonality and trends" and "Why conversions moved against the same month last year" sections of `competitive-and-market.md`.

## When to use it

"Is it the seasonal dip?", year on year questions, planning the next quarter, or when to raise or hold budgets. When the answer turns out to be share, go on to `playbooks/share-and-competitors.md`.

## What to read in the output

- **The index table:** Clicks index, Conv. index, Cost / conv. index, and Clicks index a year earlier. 100 is the average month of the last complete year, brand left out.
- **"usually rise in" and "Usually fall in",** with the rule printed beside them.
- **The months ahead table:** Clicks usually, Clicks index then, "Clicks then against" the base month, Cost and Conv. the same way, and Lost to budget then.
- **Same month last year:** the changes, with Lost to budget and Lost to rank a year earlier and now.
- **Each campaign:** Peak and Low (clicks index), and the last 3 months against a year earlier.
- **Why conversions moved:** the four factors and "Moved most".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A month under "usually rise" with the rule "in each of the 2 years covered" | A season that repeated | Plan for it | Practitioner rule |
| The rule is "the three highest and three lowest in the one year covered" | It may be a one off | Plan with care, say so, and ask for 25 months | Practitioner rule |
| A month ahead marked "rises", for a campaign that already loses share to budget (Lost to budget in Share of voice) | It will lose more share as searches grow | Raise the budget before the month starts, not during it. If that month has already begun, raise it now and plan the next rising month ahead. Last year's step ("Clicks then against") is the evidence for the size | Practitioner rule |
| A month ahead marked "rises", with a high "Lost to budget then" | Last year's clicks were capped by budget | Last year's step understates the season. Say so | Practitioner rule |
| A month ahead marked "falls" | Fewer searches are coming | Hold the target. Do not loosen it to force spend, and do not read lower volume as a fault | Practitioner rule |
| A month under "Usually fall in", with Lost to budget and Lost to rank no higher than a year earlier | The season, not the account | Say it is the season | Practitioner rule |
| Conversions down against the same month last year, and Lost to budget or Lost to rank higher than a year earlier | Part of the drop is the account's share, not demand | Name both. Take the share part to the share playbook | Practitioner rule |
| "Moved most": estimated eligible impressions | Demand changed | The season or the market. Adjust budget to demand, not the account's setup | Practitioner rule |
| "Moved most": Search impr. share | The account showed for less of the demand | Auction or budget: use the share playbook | Practitioner rule |
| "Moved most": click through rate | People saw the ads but clicked less | Ads and assets | Practitioner rule |
| "Moved most": conversion rate | Clicks came but did not convert | The site, the offer or tracking, in that order of checking | Practitioner rule |
| Cost / conv. index above 100 in a month that usually rises | Busy months cost more per conversion here | Expect it, and agree whether the target holds in peak months | Practitioner rule |
| A campaign that spent in only part of the year | Its cost is in the account lines for those months | Say which months it touches before quoting the index | Practitioner rule |
| A single campaign's Peak differs from the account's season | Its own season | Plan that campaign by its own Peak, not the account's | Practitioner rule |

## How big a change

- **The size of a seasonal raise.** No source gives a step. Last year's step in the months ahead table bounds it: how far clicks, cost and conversions moved from the base month to that month a year earlier. It is last year's step, not a forecast. The amount is a judgment the person makes; for a month by month budget plan, use the budgets and forecasts skill.
- **When.** Before the first rising month, so any change has settled by the peak. A budget change can put a bid strategy into Learning (references/reporting-and-diagnostics.md). Practitioner rule.
- **Reading the effect.** Impression share updates within 1 to 2 days. Official (references/auction-insights-and-impression-share.md). Read the first complete week of the rising month, not the first day.
- **Enough history.** Seasonality needs 12 complete months (download 13), and a repeat needs 25. With less, the script says it cannot read seasonality.

## Failure modes

- **A one year pattern sold as a season.** Check the printed rule.
- **The account's own budget cap read as a seasonal low.** Check Lost to budget in the same row.
- **A share loss called the seasonal dip.** Check "Moved most" before agreeing with "it is just the season".
- **A month compared with the month before, not the same month last year.** Year on year is the seasonal test.
- **A partial month in the index.** The script leaves it out; never quote it as a full month.
- **A forecast stated as fact.** Last year's step is evidence, not a promise.

## Worked example

Northside Plumbing, campaigns other than brand. Clicks usually rise in January, February, March, November and December, above 100 in both years. The months ahead: 2026-12 and 2027-01 both "rises", with clicks a year earlier +27.6% and +22.0% against 2025-10, and Lost to budget then of 9.3% and 9.7%. Plumbing | Water Heaters already spends 99% of its daily budget, loses 26.0% to budget, and peaked in 2025-12 (index 130). The call: raise Water Heaters' budget before December. Plumbing | Emergency is not the season: conversions fell 20.6% against 2025-10 while estimated eligible impressions rose 8.1%, and "Moved most" is Search impr. share, 59.3% to 44.0%. That goes to the share playbook.

## What to tell the client

Your busy season runs from November to March; last year December had 27.6% more clicks than October. The water heater campaign already spends 99% of its daily budget on average, so it needs more budget before December, not during it. The emergency drop is not the season: more people searched than last year, but your ads showed for fewer of them.
