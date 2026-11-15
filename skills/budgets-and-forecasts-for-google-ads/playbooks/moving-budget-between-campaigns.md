# Playbook: Move budget between campaigns, or decide not to

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: decide whether budget moves, where and how much, and what happens next to a campaign held out because its cost per conversion just jumped. It reads "Evidence for moving budget" in the summary `scripts/pacing.py` prints, with the Account lines and the "Status" and "Limited by budget" columns.

## When to use it

- The person asks where to move budget, whether to, or how to scale or cut spend safely.
- A campaign is "held out" and the person asks what to do with it.
- Whether the month lands on its target: open `pacing-and-month-end.md` first, because a ceiling decides whether a move may add spend. Changing a bid target: use `bidding-and-scaling-for-google-ads`.

## What to read in the output

- The comparison line: "Cost per conversion is compared with X".
- "is held out": cost per conversion in both 14 day windows, conversions in each, "Avg. CPC went from ... and conv. rate from ...", and "most of the change came from" either "the price of clicks" or "conversions per click". The script holds out a change of 25% or more, with at least 5 conversions in the earlier window.
- "could take more": Limited by budget, at or below the comparison, at least 10 conversions this month, with "about ... a day, an upper bound" and "A first step of up to ... a day".
- "could give": not limited, at least 25% above the comparison, at least 5 conversions.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| "could take more", and the target has room or there is none | Budget limits a campaign that converts at or below the comparison | Raise it by no more than the printed first step. Read that step before a second | Practitioner rule |
| "could take more", and the capped forecast already reaches a ceiling | Any raise adds spend the person ruled out | Fund it only with an equal cut from a campaign that spends its budget and is not held out. If none qualifies, no move this month | Practitioner rule |
| "could give" with Status "Underspending the budget" | Cutting its budget does not lower its spend | It frees no money. Never use it to pay for a raise | Practitioner rule |
| "is held out" | Cost per conversion changed sharply, cause unknown | No move either way. Follow "A held campaign: what comes next" | Practitioner rule |
| "No campaign meets both tests" | The numbers do not support a move | Say no move, and name what is missing: no campaign limited by budget, none clearly more efficient, or too few conversions | Practitioner rule |
| The receiver uses Target CPA or Target ROAS (ask) | Since August 17, 2026 a budget limited campaign on these strategies bids toward its target | Say added budget buys conversions at about the target, not at today's average | Official (references/smart-bidding.md) |
| The receiver uses Maximize conversions or Maximize conversion value (ask) | Limited by budget by design | The room is not headroom for these. Size the step with the budget simulator | Official (references/spend-troubleshooting.md) |
| No margin, lead quality or capacity given | The case rests on Google Ads results alone | Say so, and ask whether the business can take more leads | Practitioner rule |

## A held campaign: what comes next

1. **Keep its budget where it is.** **Practitioner rule:** more budget into a campaign whose cost just jumped buys more of the new cost, and a cut acts on days whose conversions may still be arriving. The one exception is a cut to hold a spend ceiling, in `pacing-and-month-end.md`.
2. **Look where the script points.**
   - "Conversions per click": clicks cost the same, fewer turn into conversions. Check in this order: conversions still arriving (ask how many days usually pass from click to conversion), a change to conversion tracking or a conversion setting, the landing page, the search terms bought. **Official** (`references/spend-troubleshooting.md`) names each of these checks.
   - "The price of clicks": clicks cost more, the conv. rate held. **Official** (`references/spend-troubleshooting.md`): since August 17, 2026 a budget limited Target CPA or Target ROAS campaign that used to beat its target trends toward it. Run `bidding-and-scaling-for-google-ads`, which measures each campaign against its own target. If it now sits within chance of its target, the fix is the target, not the budget. Otherwise look at competition and recent bid changes.
   - No driver printed: the report has no Clicks column. Ask for it.
   - The full diagnosis belongs to `performance-diagnosis-for-google-ads`.
3. **Bring it back.** Once the cause is fixed, run the check again when 14 days have passed since the fix: only then does the script's recent window hold only days after it. If the cause is explained and accepted instead, judge the campaign on "Cost / conv. last 14 days", never on the month's blend of two levels.

## How big a change

- **A first step is at most the printed first step, half the room.** **Practitioner rule:** we move budget in at least two steps and read each before the next. The room is an upper bound at today's cost per click, so never plan past it.
- **Read a step after 1 to 2 conversion cycles.** **Official** (`references/smart-bidding.md`). Ask the person for their cycle.

## Failure modes

- **A move on paper only.** Money taken from an underspending campaign was never being spent. Check Status before naming a donor.
- **Arguing around a hold.** The month's cost per conversion blends two levels, so it cannot outvote the held out line.
- **Reading late conversions as a collapse.** A fall in conversions per click in the latest days is the pattern conversion delay leaves.

## Worked example

Northside Plumbing, against a 15,000.00 ceiling, comparison 56.40.

- Plumbing | Emergency could take more: 41.18 against 56.40, room about 123.48 a day, a first step of up to 61.74 a day.
- Plumbing | Water Heaters is held out: 56.61 to 94.26, Avg. CPC 7.19 to 7.21, conv. rate 12.7% to 7.6%. Most of it came from conversions per click: check conversion delay and tracking, then the landing page.
- Drain Cleaning | Search is held out: 55.67 to 76.79, Avg. CPC up 37.9%, conv. rate flat. Most of it came from the price of clicks: check it against its target.
- The capped forecast is 198.52 over the ceiling, and the only other campaign spending its budget is held out. The call: no move this month. Diagnose both; check again 14 days after any fix.

## What to tell the client

"Emergency is your best campaign and runs out of budget most days, so it is where more money would go first. I would not move money yet: Water Heaters is turning fewer clicks into leads, Drain Cleaning is paying more for each click, and you are already a little over your ceiling. Once we know why, Emergency's first step is up to 61.74 a day."
