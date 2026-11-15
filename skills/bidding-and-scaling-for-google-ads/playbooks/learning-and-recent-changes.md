# Playbook: Judge learning and recent changes: wait, revert or act

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: say whether a recent change has disturbed Smart Bidding, how sure that is, and whether to wait, revert, adjust or investigate, with the date of the next fair read. It reads the Learning and Latest change columns, the "Hold" categories and each campaign's notes in `bidding-review.md`, with the "Change history" table.

## When to use it

- The person asks whether a campaign is learning, whether an edit reset it, why results moved after a change, or whether it is safe to change it now.
- A campaign that has had time and still misses: `pause-tighten-or-investigate.md`. Scaling once the read is clean: `scaling-a-campaign.md`.

## What to read in the output

- "Google shows it as learning: status ..., reason ...".
- "Hold: recent change" reasons: days since the change against 2 conversion cycles, or conversions since the change against the number needed.
- "Early read, not yet judgeable": cost, conversions and the gap since the change, and "A proper read is possible around" a date.
- "No day after the change is outside the N day conversion cycle yet".
- "Stacked changes close together", "Moved the unexpected way", "A conversion setting changed on ...", and "Created N days before ..." for Demand Gen and Performance Max.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Learning "Yes" with a status reason | Google confirms a learning period | Wait for the printed date. Plan "hold". No edits | Official (references/learning-phase.md) |
| "Hold: recent change", no learning status | Too little time or too few conversions since the change | Wait for the printed date; disruption is likely, not confirmed | Practitioner rule |
| A Target CPA or Target ROAS change on Search or Shopping | It does not start learning or reset what was learned | Never call it a reset. Judge it after 1 to 2 conversion cycles | Official (references/learning-phase.md) |
| A setting change on Demand Gen | Google's Demand Gen guide says some or all learning restarts | Treat it as a reset. No changes in the initial learning period | Official (references/learning-phase.md) |
| A budget change | Google's status codes can report learning after one | Read the actual status reason before saying so | Official (references/learning-phase.md) |
| "A conversion setting changed" | Results across that date measure different things | Lower confidence. Do not judge across it; allow 1 to 2 conversion cycles | Official (references/learning-phase.md) |
| "Stacked changes close together" | Their effects cannot be told apart | Add no third change. Wait for the proper read of the latest | Practitioner rule |
| "Moved the unexpected way", within chance | Noise on a small count | Do not revert on it | Practitioner rule |
| "Moved the unexpected way", more than chance | Something else moved too | Check conversion values, the search mix and competition before reverting | Practitioner rule |
| Little or no traffic, or no conversions, and no recent change | Inactive or starved of data, not learning | Check eligibility and tracking; the pause test may apply | Practitioner rule |
| Performance Max created recently | Google asks for at least 6 weeks on a new campaign | Wait | Official (references/learning-phase.md) |

## How sure, and what to recommend

State one of four, with the reason:

- **Confirmed:** Google's status shows learning. Recommend wait.
- **Likely:** a bid strategy, target, budget or conversion change inside the hold window, with no status column. Recommend wait.
- **Possible:** no change inside the window, but a conversion setting changed or the change history is missing. Recommend investigate: ask for the change history.
- **Unsupported:** no material change in the read, or only a target change on Search or Shopping. Judge the campaign on its read as usual.

**Revert** only when the change is plainly wrong, such as a target in the wrong units, or when harm is urgent: the pause test is met with no conversions at all. **Practitioner rule:** otherwise a revert is one more change stacked on the last.

## How long to wait

- **The printed date wins.** "A proper read is possible around" uses the campaign's own pace since the change. "First fair check after a change" is the longest of 2 conversion cycles, the days to 30 conversions (50 for Target ROAS), and Google's window: 7 days for a Demand Gen weekly step, 14 for Performance Max.
- **Official** (`references/learning-phase.md`): calibration typically takes 1 to 2 conversion cycles, and bid strategies keep learning after the status clears. **Practitioner rule:** the review holds for 2.
- **Not platform rules:** "7 to 14 days" and "20% budget changes" appear on some Google pages, but the status reasons do not include target edits. **Official** (`references/learning-phase.md`). Do not quote them as rules.

## Failure modes

- **Calling every swing a reset.** Check the change history and the status reason first.
- **Missing a conversion change.** A new goal or value setting changes what the numbers mean.
- **A verdict from an early read.** Its conversions are still arriving and too few.
- **Another major change before the evidence.** The review's holds exist for this.

## Worked example

Drain Cleaning | Search, Northside Plumbing.

- Switched from Maximize conversions to Target CPA 50.00 on 2026-11-05; budget 120.00 to 150.00 on 2026-11-08.
- Google shows it as learning, reason bidding strategy learning: confirmed.
- Early read: 69.02 on 11.5 conversions, +38.0% against 50.00. "Moved the unexpected way", but within what chance explains (about 29.5%).
- Stacked changes: the two effects cannot be told apart.
- The call: hold. No third change, no revert. Run the review again around 2026-12-01.

## What to tell the client

"Drain Cleaning had two changes in four days: a new bid strategy, then more budget. Google confirms it is still learning, and it has too few leads since then to judge. The early cost per lead looks high, but with this few leads that can be chance. I would change nothing and look again around December 1."
