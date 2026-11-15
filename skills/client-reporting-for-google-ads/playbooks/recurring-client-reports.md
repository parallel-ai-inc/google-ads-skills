# Playbook: The weekly update, the monthly review and the quarterly review

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-14.

The three reports a client gets on a schedule, each answering a different question in its own order. They read the summary `scripts/measure.py` prints. The headings below are the narrative template's; the fact check warns when one is missing.

## When to use it

- `--report-type weekly`, `monthly` or `quarterly`.
- For every movement you write about, also open `explaining-results-and-targets.md`: how to write a change, a lead and a target.
- An executive summary, board summary, decision memo or KPI scorecard: `summaries-memos-and-scorecards.md`. Checking a draft someone wrote: `reading-a-fact-check.md`.

## What to read in the output

- The period lines, including "The periods differ in length", every NOTE, and any "CHECK THE TARGET".
- "Account (acct)" and "Account without brand (nb)".
- "Campaigns, current period and change vs previous": Status, Share of cost, Share of conv., "Conv. chg vs LY".
- "Biggest movers vs previous period", "KPI scorecard" and "Changes made in the current period".

## What each report says, in order

**Weekly update.** The question: is anything off course, and what did we do. Keep it short.

1. **Performance snapshot.** Conversions, cost and cost per conversion against the week before, in two or three sentences. Last year here means the same weekdays 52 weeks earlier.
2. **What drove it.** The one or two campaigns at the top of the movers list, each with its lead from the change history.
3. **Work completed.** The team's changes ({count.changes.team}) and what the person tells you was done. Keep it apart from next steps.
4. **Open risks.** A paused campaign, a day with no conversions where there are usually some, a budget running short, and conversions still to come in.
5. **Next steps.** Owned and dated, with any ask of the client.

**Monthly review.** The question: what the month achieved, what drove it, where the money went, and what we do next month.

1. **Month-over-month snapshot.** Conversions and cost per conversion first, without brand when Brand is an outlier, then the scorecard, then last year.
2. **Main drivers.** The campaigns that carried the change, each with its share of the account's change ({cN.conv.share_chg_prev}) and its lead. Say which movements also show against last year.
3. **Budget shifts.** Where spend moved ({cN.cost.delta_prev}, {cN.cost.share_cur}) and what it bought ({cN.conv.delta_prev}, {cN.conv.share_cur}). Budget changes from the change history ({chgN.n1} to {chgN.n2}).
4. **Recommended next actions.** In order of the money at stake, each tied to a finding above, each with an owner.

**Quarterly review.** The question: what the quarter established, and what the next one needs. Fewer numbers, more themes.

1. **Quarterly snapshot.** The quarter against the quarter before and the same quarter last year. Last year carries more weight here, because quarters hold seasons.
2. **Wins and risks.** Themes that held across the quarter, with the `campaigns_last_year` table. One month's spike is not a quarter's theme.
3. **Roadmap priorities.** What the next quarter should focus on, and the budget or time each needs.
4. **Decisions needed.** Each decision, its tradeoff, who decides and by when.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| NOTE "Brand is an outlier" | The whole account's cost per conversion flatters the rest | Give the nb figures first and say brand searches convert cheaply by nature. The fact check refuses the blended figure alone | Practitioner rule |
| NOTE "is paused on the day of download", with its last day with cost | The campaign stopped | Write that it was paused and when, and how much cost that removed ({cN.cost.delta_prev.abs}). Never "declined" | Practitioner rule |
| "The periods differ in length" | A total can fall only because the month is shorter | Put the per day figure (cost_per_day, conv_per_day) beside any total you cite | Practitioner rule |
| A campaign moves the same way in "chg" and "chg vs LY" | Likely a lasting change, not the season | Call it a trend | Practitioner rule |
| It moves against the previous period only | Could be the season or a one off | Call it a watch item, and say what next period would confirm it | Practitioner rule |
| Share of cost well above share of conv. for an enabled campaign | It costs more than it brings, by attributed conversions | Name it in drivers or risks, with both shares | Practitioner rule |
| A chgN made by Google's systems | An automatic change, not the team's | Say Google's systems made it. Auto-applied recommendations show in Change history and never raise budgets | Official (references/reporting-and-diagnostics.md) |
| No change history, or "No change in the change history falls in the current period" | Work completed has no source | Ask the person what was done. Never invent work | Practitioner rule |
| "The report starts on ..., so the same period last year is not compared" | No ly ids exist | Say last year is not compared and why. For a quarterly review, ask for the longer download | Practitioner rule |
| A weekly report | Every day in it is recent | Say conversions can still rise, and do not call a drop in the last days a decline | Practitioner rule |

## How big a movement to report

No source gives a size below which a movement is noise, so this is a judgment. Bound it with what the summary prints: the movers list order, each campaign's share of the account's change, and the conversions behind it. A campaign with a large percentage on a handful of conversions gets a watch item, not a headline.

## Failure modes

- **The monthly review written as an executive summary.** It shows as one paragraph and a next step, with no drivers or budget shifts. Check: all four monthly headings are filled, and Budget shifts names where spend moved.
- **A total compared across months of different length.** October's conversions rose 1.5% on September while conversions per day fell. Check: the period line, then the per day figure.
- **Work completed padded with Google's changes.** Check: count.changes.team against count.changes.system.

## Worked example

Northside Plumbing, October 2026, monthly (`examples/output/client-reporting/`).

- Brand is an outlier: 4.13 per conversion against 50.24 for the rest. The snapshot leads with 50.24, 25.6% above the 40.00 target, then the account's 34.88.
- Conversions rose 1.5% (413.49 against 407.22), but conversions per day fell 1.7%: October has 31 days, September 30. Both go in.
- Main drivers: Plumbing | Water Heaters conversions fell 34.1% after its move to Target CPA on October 6; Plumbing | Emergency rose 19.3% after its budget went from 200.00 to 240.00 on October 1. Both are leads, written with "after".
- Emergency also rose 40.4% on last year, so it reads as a trend.
- Budget shifts: Emergency took 58.1% of cost and 50.2% of conversions. Drain Cleaning | Search was paused on October 20, and its cost fell 1,410.48.

## What to tell the client

The report is the client's words: what the period did for the business, the campaigns by name, what we do not know yet, and what we will do next.
