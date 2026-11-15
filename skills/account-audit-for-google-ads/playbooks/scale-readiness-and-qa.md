# Playbook: Ready to scale, and QA before or after a change

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

Two gate decisions on one audit run. Readiness answers "can this account take more spend": ready, ready after named fixes, or not ready. QA answers "is this change safe to make" or "did it break anything". Both read `scripts/audit.py` run with `--job readiness` or `--job qa`, and QA after a change also reads `--before OLD_WORK/audit.json`.

## When to use it

- Readiness: the person plans more spend, a new season, or a push for growth. Run the full audit judgment first (`playbooks/full-account-audit.md`), then decide here.
- QA before a change: the person names the change. QA after: the same files and date length, plus the audit.json from the run before the change.
- How large each budget step should be is the bidding and scaling skill's job, not this one.

## What to read in the output

- **READINESS CHECKS:** every check that gates more spend, with Result and Money at stake. They are CT-01 to CT-04, KW-05, AD-01, AD-02, BB-02 to BB-06, SQ-01 and SE-01, plus SE-M3 and SE-M4 by hand.
- **QA: MUST PASS:** CT-01 to CT-04, AD-01, AD-02, BB-01, BB-02, BB-05 and SE-01, plus SE-M3 and SE-M4 by hand. **QA: OTHER CHECKS** do not block a change.
- **SINCE THE EARLIER RUN:** each check whose status or money moved, with Before, Now, Money before and Money now.
- **LIMITED BY BUDGET BY DESIGN**, BB-03's items (the held back figure per campaign) and **DATED PLATFORM CHANGES THE FILES CAN SHOW** for the August 17, 2026 rule.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Any CT check in READINESS CHECKS fails | More budget would scale miscounted conversions. | Not ready. Fix measurement first. | Practitioner rule (references/fix-order.md, references/checklists.md Before Scaling) |
| AD-01, AD-02 or SE-01 fails | Part of the account cannot serve, so new spend goes elsewhere. | Ready after named fixes, if the rest passes. | Practitioner rule |
| SQ-01, KW-05 or BB-04 fails | Some spend already buys nothing. | Ready after the waste fix. New spend would add more of it. | Practitioner rule |
| Only BB-03 fails | The budget is the limit on campaigns that convert at or below the line. | Ready. BB-03's campaigns are where more spend goes first. | Practitioner rule |
| A campaign under LIMITED BY BUDGET BY DESIGN | Maximize strategies spend the full budget by design. | Judge its headroom with the budget simulator, not Search lost IS (budget). | Official (references/audit-check-sources.md) |
| A Target CPA or Target ROAS campaign is listed as limited by budget | Since August 17, 2026 it bids toward its target, so added budget buys conversions at about the target, not at today's better figure. | Confirm the target is the one the business wants before adding budget. | Official (references/platform-changes-2026.md) |
| The planned extra spend is larger than BB-03's held back figure | The figure is an upper bound on what budget alone can buy at today's prices. | Say more spend needs more reach (keywords, locations, campaigns), not only budget. | Practitioner rule |
| The person has a revenue goal | The audit does not forecast. | Work back from their actual cost per conversion and their own sales records to the conversions the goal needs. Name the assumptions that could reverse it. Do not promise it. | Practitioner rule |
| QA after: a must pass check went from pass to fail | The change broke something that stops serving, counting or bidding. | Stop. Undo or fix the change before anything else. | Practitioner rule |
| QA after: only money moved | The periods differ. Late conversions still arrive. | Report it, and judge again after 1 to 2 conversion cycles. | Official (references/platform-changes-2026.md) for the wait on target campaigns. Practitioner rule elsewhere. |
| QA before: SE-M3 or SE-M4 not yet checked by hand | Tags and landing pages decide whether the change can be measured. | Put both on the QA list with an owner. | Practitioner rule |

Before Scaling also asks for things no export holds (Practitioner rule, references/checklists.md): tracking and conversion meaning stable, conversion delay allowed for, landing pages and creative inspected, and stock, sales capacity, promotions and service area known. Ask the person each one. An unknown is a named condition, not a pass.

## How big a change

No reference gives a step size for budget. It is a judgment bounded by BB-03's held back figure, the campaign's Search lost IS (budget), the person's planned spend and their capacity. A budget change can put a bid strategy into Learning (Official, references/fix-order.md). For target campaigns, Google says to wait 1 to 2 conversion cycles before judging performance and not to add data exclusions or new bid limits only because of the August 17 change (Official, references/platform-changes-2026.md). For QA, compare runs of the same length, and say the newest days may still gain late conversions.

## Failure modes

- **Calling a configured account ready.** A saved conversion action, a linked tool or a structure that exists is not proof the right outcome steers bidding, or that the ad's promise matches what the business delivers. Readiness names each dependency it could not see.
- **Reading Google Ads conversions as customers.** Conversions are interactions credited by Google's attribution, not unique customers. For a scaling case, compare with the business's own sales records.
- **Counting the same customer twice across platforms.** If the business also advertises elsewhere, each platform claims its own credit. Do not add them.
- **QA on mismatched periods.** A 30 day run against a 90 day run moves every money figure. Check FILES READ for both runs.
- **Blocking on a QA OTHER check.** Those do not stop the change. Say so.

## Worked example

Northside Plumbing, run with `--job readiness`. CT-03 and CT-04 fail, so the answer is ready after named fixes, and the first fix is measurement: GA4 generate_lead and Contact form submit both count the same form. AD-01 and AD-02 fail on Hydro Jetting, and SQ-01 and KW-05 show waste. BB-03 names Plumbing | Emergency, with Search lost IS (budget) of 34.2% and a held back figure of 5,115.87, an upper bound. Plumbing | Water Heaters is limited by budget by design on Maximize Conversions, so its headroom is judged with the budget simulator. No campaign is on Target CPA or Target ROAS, so the August 17 rule touches none, unless Water Heaters has a target set, which the file cannot show.

## What to tell the client

"The account can take more spend once three things are fixed: the double counted lead, the ad that cannot show, and the searches that spend with no result. After that, the Emergency campaign is where more budget goes first. We raise it in steps and watch whether the cost per lead holds."
