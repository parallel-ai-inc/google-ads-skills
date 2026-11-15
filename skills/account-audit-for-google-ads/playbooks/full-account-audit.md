# Playbook: Full account audit, judged and put in fix order

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: decide which failed checks matter for this account, write each fix, and hand the person a plan that runs in the order of `references/fix-order.md`. You read the output of `scripts/audit.py` and fill `notes.json`.

## When to use it

Every audit, as the base for the other audit jobs. Readiness and QA continue in `playbooks/scale-readiness-and-qa.md`. Search term waste in depth belongs to the search terms skill, and bid and budget step sizes to the bidding and scaling skill.

## What to read in the output

- **FILES READ:** each file's rows against its own total. A difference means a filtered or cut file. Say so first.
- **WHAT THE RUN ASSUMED** and **THRESHOLDS:** brand terms, target, and the "spent enough to judge" lines, each the account's own non brand cost per conversion.
- **FAILED CHECKS, ... BY MONEY**, **CLEAR WASTE, COUNTED ONCE** (the only figure for "how much are we wasting") and **FIX ORDER.**
- Each failed check's **Looked at, Evidence, Threshold, Left out, Money** and its items, and **LIMITED BY BUDGET BY DESIGN.**

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| CT-03 or CT-04 failed | Bidding steers by conversions that are counted wrong. The exposed money is the cost of the campaigns that bid on conversions. | Fix first. Keep one primary action per real outcome and set the copy to secondary. Keep the one closest to the real outcome: an import from the business's own records over a site tag, a confirmed form submission over a page view or click, the one already counted One. Ask the person to confirm before switching. Count leads as One. Say the Count change applies to future conversions only. | Official (references/audit-check-sources.md) for primary, secondary and counting. Practitioner rule for calling two primaries double counting and for which one to keep. |
| CT-04 failed, and one of the two actions is a useful step in the journey | Not every extra action is waste. | Make it secondary, do not remove it. A secondary action still reports in All conv. | Practitioner rule |
| A lead action is primary, but the business sells on a later step | Optimizing a signup, a trial and a paying customer are different goals. | Ask which outcome the business wants more of, and write the fix for that action. A custom goal can bid on a secondary action, so read the campaign's goal before calling an action unused. | Official (references/audit-check-sources.md) for custom goals. Practitioner rule for the rest. |
| AD-01, AD-02 or SE-01 failed | Nothing in those ad groups or campaigns can serve, so later stages have no data there. | Stage 2. Fix the cause, then ask for a review. | Official (references/compliance.md) |
| SQ-01 or KW-05 failed | Spend at or above the threshold with no conversion. | Before writing a negative, ask whether the search is someone trying to do the work the business sells. Job seekers and do it yourself searches for a service business are waste. The same words can be customers for a business that sells templates or guides. | Practitioner rule |
| A negative is proposed | It applies at every level where it is attached: account, shared list, campaign or ad group. | Name the level, and check the list is not shared with campaigns that need the search. Test it against the converting searches first. | Practitioner rule |
| ST-01 failed for a distinct service with its own page | Google's guidance is themed ad groups, but one keyword for one service is not a mistake. | Mark it `no` and say why. | Official (references/account-structure.md) for the guidance. Practitioner rule for the exception. |
| KW-03 failed for a seasonal keyword | No impressions out of season is expected. | Mark it `no`, or say to leave it until the season. | Practitioner rule |
| BB-03 failed | Budget held back a campaign that converts at or below the line. The figure is an upper bound. | Stage 6, after measurement. Never call it waste. | Practitioner rule, with Official facts in references/audit-check-sources.md |
| A Maximize campaign shows under LIMITED BY BUDGET BY DESIGN | Built to spend the full budget, so Search lost IS (budget) does not mean it is starved. | Judge its headroom with the budget simulator, and by whether its cost per conversion holds as the budget rises. | Official (references/audit-check-sources.md) |

## How big a change

The audit decides what to fix and in which order, not how far to move a bid or a budget. Those sizes are judgments. Bound them with printed numbers: the held back figure in BB-03 is the ceiling of what more budget could buy at today's prices, and the campaign's Search lost IS (budget) is the room left. A bid strategy can enter Learning after a new strategy, a strategy setting change, a budget change or a conversion setting change, so make measurement and bidding changes once, in that order, not in separate rounds (Official, references/fix-order.md).

## Failure modes

- **Adding money across checks or kinds.** The same cost sits under several checks. Only CLEAR WASTE, COUNTED ONCE answers "how much is wasted". Check every total you quote is printed.
- **Ranking by money and calling it the fix order.** State both orders: findings by money within each kind, fixes by stage.
- **Calling exposed or held back money "lost".** Exposed spend still bought results. It rests on a problem.
- **A fix that undoes another.** Moving a campaign to a conversion strategy before CT-04 is fixed teaches it from inflated numbers. Read FIX ORDER before writing each fix.
- **Brand in the baseline.** If WHAT THE RUN ASSUMED says no brand terms were given, the thresholds are pulled down by cheap brand conversions. Ask for brand terms, or suggest the business name, record it under `assumptions`, and run again.
- **Taking a saved setting as proof.** A primary action that records, or a tag that fires, does not prove the right outcome steers bidding.

## Worked example

Northside Plumbing, October 14 to November 12, 2026. 23 checks ran: 7 passed, 16 failed. CT-03 and CT-04 failed with exposed money of 4,413.70 each, the cost of the two Maximize Conversions campaigns, because GA4 generate_lead and Contact form submit are both primary for the same form. That is stage 1, so it leads, even though SQ-01 (wasted 2,301.80) and BB-03 (held back 5,115.87) carry more money. AD-01 and AD-02 come next: Hydro Jetting has no working ad. ST-01 failed on Hydro Jetting, but it is a distinct service with its own page, so it is judged `no`. Clear waste, counted once, is 2,389.00, because 1,432.80 of search term cost sits inside flagged keywords. BB-03 names Plumbing | Emergency for more budget, last, after the conversion fix.

## What to tell the client

"Your campaigns that bid on conversions are counting the same lead twice, so they are steering by numbers that look better than they are. We fix that first, then the ad that cannot show, then the searches that spend with no result. More budget comes last, once the numbers it will scale are right."
