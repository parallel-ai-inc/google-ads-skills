# Playbook: Explain a change in performance, and handle a target the data contradicts

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-14.

How to write one movement for a client, how sure to sound about its cause, and what to do when a target the person gave does not fit the data. It reads the summary from `scripts/measure.py`.

## When to use it

- Writing any sentence about why something moved, in any report type.
- The summary prints "CHECK THE TARGET", or a figure the person gave disagrees with the data.

## What to read in the output

- "Biggest movers vs previous period" and each campaign's `share_chg_prev`: how much of the account's change it carried.
- "Changes made in the current period": chgN, its date, the campaign and ad group, who made it, and its numbers (chgN.n1, chgN.n2).
- The campaign table's "Status" and each paused campaign's last day with cost.
- "KPI scorecard" and any line that starts "CHECK THE TARGET".

## How to write one change

Four parts, in this order, one or two sentences each:

1. **What moved,** with its comparison: "Plumbing | Water Heaters conversions fell {c2.conv.chg_prev} on September." Use rose or fell, so the id prints without its sign.
2. **Where it sits:** its share of the account's change, or its share of cost and conversions, so the client knows whether it matters.
3. **Why, at the strength the evidence allows** (the table below).
4. **What we are doing, and when we will know.** The action comes from the person or from a finding; never invent one. Say when the next read is: the next report, or a date.

| Strength | When | Words to use |
|---|---|---|
| A fact | The data shows it directly: the campaign is paused and its cost stopped on its last day with cost | "was paused on ..., so its cost fell by ..." |
| Confirmed | The person confirms the cause | "because" |
| A lead | A change in the period, in the same campaign, before the movement | "after", and "the first thing we are checking" |
| A watch item | No change explains it, or it rests on few conversions or on the last days of the period | "we are watching", and what would confirm it |

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| A chgN in the same campaign, dated before the movement | Timing, not proof | Write it as a lead with "after" | Practitioner rule |
| The chgN is a new bid strategy, a strategy setting, a budget, a campaign composition or a conversion setting change | Each can put the bid strategy into Learning. A Target CPA or Target ROAS change does not | Say the strategy may be learning, as Google documents | Official (references/reporting-and-diagnostics.md) |
| A chgN that changes conversion actions or the attribution model | Conversions can move with no change in demand | Treat the movement as a measurement change until ruled out. A model change applies going forward and can add reporting lag on recent days | Official (references/attribution.md) |
| A chgN by Google's systems | Possibly an auto-applied recommendation | Name Google's systems as the source. Check this before crediting the team | Official (references/reporting-and-diagnostics.md) |
| A movement with no chgN | The change history may be incomplete | Say no recorded change explains it. Some account level and Google representative changes may be missing | Official (references/reporting-and-diagnostics.md) |
| "CHECK THE TARGET" | The target is more than 25% from the whole account's actual | Ask before writing (below). The fact check refuses target and score ids and the scorecard table until then | Practitioner rule, threshold printed by the script |
| A cost per conversion target within 25% of the whole account, but far from the row without brand | The check compares with the whole account only | Ask whether the target is meant with or without brand | Practitioner rule |
| The person states a figure the data contradicts | One of the two is wrong, or they count different things | Put the data's figure first, and raise the gap in your reply. Never write theirs into the report | Practitioner rule |

**Where the person checks a lead in Google Ads.** The bid strategy's status (Learning, Limited or Misconfigured, each with Google's reasons), the recommendations History tab for auto-applied changes, and Change history for the full record. **Official (references/reporting-and-diagnostics.md).** What they report back stays a lead until they confirm the cause.

## A target the data contradicts

Ask in one message, with the gap the summary printed:

1. Which period is the target for: a month, a quarter, a year?
2. Is it the current figure, or an old plan?
3. Does it cover this account alone, or several accounts or channels?
4. For cost per conversion: with brand campaigns or without?

Then run step 1 again with the corrected target, or with `--confirm-targets` if they say it is right. A confirmed target that is still far off goes in plainly, with the scorecard's status. The report calls targets "the targets you gave" unless the person says they were agreed with the client; only then pass `--targets-agreed`.

## How big a gap to raise

The script raises a target more than 25% from the actual. Below that, a gap is judged in the text: give the scorecard's Difference % and leave the size to the client. No source gives a smaller line.

## Failure modes

- **Cause from correlation.** A change dated before a movement written with "because". Check: "because" appears only where the person confirmed it.
- **A target taken on trust.** A spend figure the person gave was written as "above the planned 9,000.00" and called agreed. Check: no CHECK THE TARGET line is open, and "agreed" appears only with `--targets-agreed`.
- **A measurement change reported as performance.** Check: conversion settings in the change history before explaining a conversion movement.
- **An action nobody agreed.** Check: every "we are doing" came from the person or is marked as your recommendation.

## Worked example

Northside Plumbing, October 2026.

- Plumbing | Water Heaters conversions fell 34.1%, and it carried the account's largest conversion drop (22.02). The change history shows chg2 on October 6: bid strategy moved from Maximize conversions to Target CPA at 45.00. That is a lead, written with "after", and a new bid strategy can start a learning period, as Google documents.
- Written for the client: "Water Heaters brought 34.1% fewer conversions than in September, after its bidding moved to a cost per conversion target on October 6. A new bid strategy can spend time learning. We are reviewing the target and will judge it on November's results."
- In the trial run the person said spend was about 9,000 a month; October's cost was 14,423.32. The summary printed CHECK THE TARGET. The right move was to ask which period and accounts that figure covered, not to write "over plan".

## What to tell the client

Use the four parts, as in the worked example: what moved, where, the cause at its true strength, and what we do next.
