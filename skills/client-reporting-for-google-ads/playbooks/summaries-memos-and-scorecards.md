# Playbook: Executive and board summaries, decision memos and KPI scorecards

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-14.

The documents written for someone who will not read a full review: an executive, a board, a person who must approve a decision, or a team that works from a scorecard. They read the same summary from `scripts/measure.py` as the recurring reports, but say much less, and each ends in a different thing: a next step, a decision, a recommendation or an owner.

## When to use it

- `--report-type executive`, `board`, `decision` or `scorecard`. These have no period of their own: pass `--period week|month|quarter` or `--current`. A whole calendar month or quarter given as dates is compared with the one before it.
- For every movement you write about, also open `explaining-results-and-targets.md`.
- A scheduled weekly, monthly or quarterly report: `recurring-client-reports.md`.

## What to read in the output

- "Account (acct)", "Account without brand (nb)" and the NOTE lines.
- "KPI scorecard": KPI, Target, Actual, Difference, Difference %, Status, and its ids (target.*, score.*).
- "Biggest movers vs previous period".
- "Changes made in the current period", for what the team and Google's systems did.
- Any given number (given1, given2): figures from outside Google Ads the person passed with `--given`, such as leads in the CRM.

## What each document says, in order

**Executive summary.** Summary, Business implication, Next step. One movement, the few numbers that defend it, what it means for the business, and the one next step or decision. Everything else stays in the tables.

**Board summary.** Business impact, Strategic risks, Budget implication, Decision needed. Business result first and channel detail second. A risk goes in only when the data shows it. The budget implication says what the results mean for next period's spend, in the person's own targets.

**Decision memo.** Decision context, Options and tradeoffs, Recommendation, Confidence and next step. State the decision and why it matters before arguing for an option. Keep three things apart: facts (cited ids), assumptions (what the person told you, said as theirs) and the recommendation (your judgment). Include doing nothing as an option, and say why each option not chosen loses.

**KPI scorecard.** Scorecard, Biggest misses or wins, What needs follow-up. The table carries the numbers. The text names the largest misses and wins with one line of cause each, then an owner and a next check for every miss.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Status "Above target" on a cost per conversion row, or "Below target" on Conv. value / cost or conversions | A miss | It goes in Biggest misses, with an owner and the next check | Practitioner rule |
| Two cost per conversion rows, one "without brand", with different statuses | Brand is an outlier and the blended figure hides the miss | Lead with the row without brand. Ask which figure the target was set for, and say it in the text | Practitioner rule |
| Spend row "Below target" or "Above target" | Spend is off the plan the person gave | Say why from the data: a paused campaign, a budget change in the period. A spend gap is not a performance result | Practitioner rule |
| "CHECK THE TARGET" | The target may be for another period, old or a typo | Stop and follow `explaining-results-and-targets.md` before writing | Practitioner rule |
| A given number (givenN) beside Google Ads conversions | Two systems count different things | Name each by its source. Never add them or call conversions sales | Practitioner rule |
| Conv. value / cost in a board summary | Attributed return, not what the ads caused | Say "attributed". For profit at the business's margin, use the experiments skill's return on investment job | Official (references/attribution.md) |
| A decision memo option that needs a number no id carries | The data cannot support it | State it as an assumption, or leave it out | Practitioner rule |

## How big a recommendation

These documents recommend; they never size a change the data cannot size. A budget, bid or target step belongs to the skill that measures it (budgets, bidding, experiments). Name the step and its waiting period from that skill's output, or say no step is sized yet.

## Failure modes

- **Every metric in the executive summary.** Shows as the account table restated in prose. Check: the Summary cites the few ids that defend one movement.
- **A board risk the data does not show.** Shows as "rising competition" with no figure. Check: every risk cites an id or is labelled as the person's report.
- **A memo that argues before it frames.** Shows as a recommendation in the first paragraph. Check: Decision context comes first and names the decision.
- **A scorecard read only on the blended row.** Shows as "At or better than target" while the row without brand is "Above target". Check: brand rows first.
- **A miss with no owner.** Check: each miss in What needs follow-up names who and when.

## Worked example

Northside Plumbing, October 2026, as a scorecard.

- Cost / conv., without brand: 50.24 against 40.00, +25.6%, Above target. Cost / conv.: 34.88, At or better than target. The scorecard leads with the first.
- Spend: 14,423.32 against 16,000.00, 9.9% below target, because Drain Cleaning | Search was paused on October 20.
- Biggest miss: Plumbing | Water Heaters, cost per conversion 74.20, up 38.3%, after its move to Target CPA on October 6. Follow up: the account manager reviews its Target CPA once November's numbers settle.
- As a decision memo on Drain Cleaning | Search: the facts are its 90.69 per conversion and 2.31 Conv. value / cost in October. Whether 2.31 pays depends on margin, which this report does not have: that is an assumption to state, or a return on investment run first.

## What to tell the client

The document is the client's words. Keep each to what its reader acts on: the executive the one movement and the step, the board the impact and the decision, the approver the options and the call.
