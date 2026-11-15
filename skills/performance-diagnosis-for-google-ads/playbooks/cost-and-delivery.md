# Playbook: Cost went up, or delivery fell

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: explain a cost spike or a fall in spend, impressions or clicks before anything is changed. It reads the summary from `scripts/compare.py`.

## When to use it

- A campaign under "Where the change is" has a main lever of cost per click, how often ads showed, or click through rate.
- When the main lever is conversion rate, or the complaint is about leads, sales or value, open `conversions-and-value.md`. For yesterday, the last two weeks, anything unusual or a write up, start with `routine-checks-and-write-ups.md`.

## What to read in the output

For each campaign under "Where the change is": "That is X in cost, against Y for the whole account"; "The main lever is", "The shift starts around" and the lever line; the traffic line "Impr.: ... Clicks: ... CTR: ..."; "Campaign status on <day>"; "Cost per day" before and from the shift; and "Changed on ... by ...", or "No account change is recorded in the 3 days before the shift."

## Which account change fits which lever

Read each change listed before the shift against the lever that moved. A strong fit is the lead to check first. A weak fit stays on the list, but you say it is a weak fit and keep looking.

| Change in the 3 days before | How often ads showed | Click through rate | Cost per click | Label |
|---|---|---|---|---|
| Keywords added, or a looser match type such as broad match | Strong: more searches to enter | Medium: a wider mix of searches is often clicked less | Strong: new auctions, often pricier | Practitioner rule |
| Keywords paused or removed, negative keywords added | Strong, downward | Medium, can rise | Weak | Practitioner rule |
| Budget raised or lowered | Strong | Weak | Weak on Manual CPC. Medium on Maximize conversions or Maximize conversion value, which spend what they are given | Practitioner rule |
| New bid strategy, or a switch of strategy | Strong | Weak | Strong | Official (references/learning-phase.md): a switch starts Learning |
| Target CPA or Target ROAS changed, on Search or Shopping | Strong: a tighter target enters fewer auctions | Weak | Strong: bids move at once | Official (references/learning-phase.md): no Learning, bids react immediately |
| Location, ad schedule, audience or device settings | Strong | Medium: a new mix of people | Medium | Practitioner rule |
| Ads or assets edited, added or paused | Weak, unless every ad in an ad group stopped serving | Strong | Weak | Practitioner rule |
| Conversion action or goal changed, on Smart Bidding | Medium: bidding now reads a different signal | Weak | Medium | Official (references/learning-phase.md): 1 to 2 conversion cycles to settle |

With no change recorded, look outside the account's edits: demand, competitors, the website, billing, or a change older than 3 days.

## What to check first, for each lever

**How often ads showed fell.** 1) The "Campaign status" line: Paused, Removed or Ended is the answer. 2) In Google Ads, the campaign and bid strategy status: disapprovals, billing, Limited by budget, Learning. 3) Search lost IS (budget), except on Maximize conversions and Maximize conversion value, limited by budget by design. 4) Targeting edits. 5) Only then demand and competitors, in Auction insights. **Official** (references/troubleshooting.md): serving eligibility, then bid strategy status, then change history, then tracking, then auction pressure last. **Official** (references/spend-troubleshooting.md) for the Maximize rule.

**Click through rate fell.** 1) Ads: approval status and recent edits, by eye (below). 2) The Search terms report since the shift day, for a new mix of searches. 3) Search lost IS (rank), which reflects both bids and ad quality (**Official**, references/troubleshooting.md). 4) Competitors' ads in Auction insights.

**Cost per click rose.** 1) The change listed before the shift, against the table above. 2) The Search terms report since the shift day: cost and conversions of the searches the new keywords or settings bought. 3) Search lost IS (rank) and Auction insights for new pressure. **Practitioner rule:** competitors come last, after the account's own changes are ruled out.

## Disapproved or limited ads: a check by eye

This skill does not read an ads report and cannot see approval status. Never say an ad is or is not disapproved. When click through rate or impressions fell and no change explains it, ask the person to look: in Google Ads, open Campaigns, then Ads, filter to the campaign, and read the Status column for Disapproved and Eligible (limited), and when each changed. **Practitioner rule:** fix eligibility before any bid or budget advice.

## How big a change

This job proposes. It never changes the account.

- **Official** (references/spend-troubleshooting.md): a campaign can spend up to 2 times its average daily budget on one day, while the monthly limit stays near 30.4 times it, so one day near double is not by itself a fault. Since June 1, 2026, campaigns whose ad schedule switches off whole days also pace toward 30.4 times a month.
- **Official** (references/spend-troubleshooting.md): since August 17, 2026, budget limited Target CPA and Target ROAS campaigns deliver toward their target instead of beating it. A cost per conversion rising toward its target may be the campaign meeting a loose target.
- **Official** (references/learning-phase.md): judge a new target after 1 to 2 conversion cycles. On Demand Gen, Google asks for bid changes of 5% to 10% a week, no more than 15%.
- To contain a spike, size the proposal by "Cost per day" before and from the shift and by "That is X in cost", against the person's own budget. **Practitioner rule:** after the Search terms check, narrow or pause only what fits the lever, never the whole campaign first.
- **Practitioner rule:** a budget alert or a saved script does not stop spend, and costs reach reports late. Never call an alert a cap.

## Failure modes

- **Bidding blamed for a delivery drop** while the status line reads Paused. Read the status line first.
- **Lost IS (budget) quoted on a Maximize strategy.** Check the strategy first.
- **One campaign told as the whole story.** Quote "against Y for the whole account": others can move the other way.
- **A weak fit called the cause.** Give the fit from the table.

## Worked example

Drain Cleaning | Search: cost +80.7%, +579.15 against +584.17 for the whole account. The main lever is cost per click, 5.24 before and 7.54 now, from around 2026-11-05. Impr. +23.3%, clicks +25.5%, CTR 5.61% to 5.71%. Changed on 2026-11-05: 12 keywords added (broad match), a strong fit on both levers that moved. The call: those keywords are the lead. First check: the Search terms report since 2026-11-05. Value / conv. held at 210.00, so do not pause them before that check.

## What to tell the client

Almost all of the extra spend is in Drain Cleaning, where each click cost about 7.54 instead of 5.24 from November 5, the day 12 broad match keywords were added. We are checking which searches they bought before deciding whether to keep, narrow or pause them. The other campaigns are steady.
