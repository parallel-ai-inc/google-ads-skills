# Playbook: Audit the conversion setup

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: decide whether the account counts the right outcomes, once, with the right settings, and the order of the fixes. It reads `conversion-audit.md` from `scripts/audit_actions.py`.

## When to use it

- An audit, a new account, or a check before a bidding change.
- After a Google product was linked to the account: Google Analytics, YouTube, a store.
- When an action stopped, dropped, jumped or moved in or out of the Conversions column, open `debug-a-break.md` too: it reads breaks and findings together. When Google Ads does not match GA4, a CRM or the office's count, open `explain-a-mismatch.md`.

## What to read in the output

"What was read", with the Primary and Secondary counts and the line that the rows match the file's own total; "What the audit found", each finding with its "Share" of All conv. and labelled rules; "Checks outside Google Ads, by who usually does them"; "Where the conversions are"; "Categories"; and "What this did not cover".

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Primary actions that are not recording | Bidding uses an action that sends nothing. Awaiting conversions has three usual reasons: a new action, paused campaigns, or low traffic | A failure. Hover its Tracking status in Goals, Conversions, All conversions for Google's own diagnosis. Run the breaks step to date it | **Official** (references/conversion-action-settings.md) |
| Primary actions with no conversions in the range | A dead action, or an outcome that is rare | Ask the business whether the outcome happened. If it should have, treat it as not recording | Practitioner rule |
| Two Primary actions in one category from different sources | Possibly one event counted twice, and its value twice when both carry one | Make one real conversion and see which actions count it. If both do, switch the extra one to Secondary | Practitioner rule for the flag. **Official** (references/conversion-action-settings.md) for the fix |
| A purchase action with no value | Value bidding has nothing to bid on | Ask whether any campaign bids on value. If one does, set values | **Official** (references/conversion-action-settings.md): values must be set up before Smart Bidding can use them |
| A lead action counted as Every | A second form or call from one click counts again | A setting to confirm with the business | **Official** (references/conversion-action-settings.md): Google's example for One is a lead |
| A Primary page view action | Bidding learns from visits, not outcomes | A setting to confirm. Do not optimize toward an action until it represents the business outcome | Practitioner rule |
| A category with only Secondary actions | Bidding ignores it unless a custom goal includes it | Ask whether it is an outcome the business would pay for. Often it is correctly left out | **Official** (references/conversion-action-settings.md) |
| "Where the conversions are" | A fault in these few actions moves the numbers most | Check them first, even with no finding | Practitioner rule |
| Removed actions, listed apart | History only | Not audited and not in the base. Past totals keep their old meaning | Practitioner rule |

## The order of the fix path

Present findings in the script's order. Order the fix path differently:

1. Findings that change what bidding learns today: not recording and double counting. Larger share first.
2. Primary actions with no conversions in the range.
3. Settings to confirm: a purchase with no value, a lead counted as Every, a Primary page view, a category with only Secondary actions. These have no failure layer. Each is a question for the business or for you in Google Ads.

**Practitioner rule:** while a failure in step 1 is open, every bid, target or budget idea is provisional.

## What the export cannot show

- **Which goals each campaign uses.** **Official** (references/conversion-action-settings.md): a report does not show it, and a Secondary action inside a custom goal is used for bidding. So Primary on the summary does not prove an action bids in every campaign, and Secondary does not prove it bids in none.
- **Practitioner rule:** trace the real outcome through to bidding. The outcome, the action that records it, its category, Primary or Secondary, the account's default goals, the campaign's own goals or custom goal, then the bid strategy. A tag that fires proves only the first step. A campaign that bids on conversion count does not bid on value because values are present.
- **Practitioner rule:** after linking a Google product, compare the action list and the account default goals with what they were before. A link can add Primary actions with values and change the goals that campaigns inherit.
- **Practitioner rule:** an action should record the completed outcome. A form view, a click and a valid lead are different outcomes.

## How big a change

- **Official** (references/conversion-action-settings.md): a change to Count, or to a conversion window, applies to future conversions only.
- **Official** (references/tracking-and-signals.md): after a goal or action change, Smart Bidding needs 1 to 2 conversion cycles in most cases. Google recommends moving targets gradually, and for a goal migration a Target ROAS from the previous 4 weeks, leaving out the conversion delay.
- **Official** (references/conversion-action-settings.md): actions created from Google Analytics start as Secondary, and data can take up to 24 hours to reach Google Ads.
- **Practitioner rule:** make the double counting fix on its own, first, so its effect can be read before the next change.
- **Practitioner rule:** retiring a duplicate takes two steps. Switching the action to Secondary or removing it does not stop the tag sending. Ask the developer to remove the extra sender too, and confirm both.

## Failure modes

- **A Secondary action promoted because it "looks wrong".** Directions clicks are often right as Secondary.
- **The older action deleted to fix double counting.** Switch the extra one to Secondary.
- **Skipped checks read as a clean bill.** The audit names the checks a missing column skipped. Say so.
- **No break read as no problem.** A double count older than the report shows as a finding with no break.

## Worked example

Northside Plumbing: 5 actions, 4 Primary; All conv. 608.00 matches the file's own total. F1: Online booking, Primary, No recent conversions, 9.4%. F2: GA4 generate_lead (29.9%) and Website lead form (29.8%), both Primary in Submit lead form from different sources, 59.7% together, both valued. F3: Website lead form counts Every. F4: Directions clicks, Secondary, alone in Get directions, 10.2%. Fix path: F2 first, since those two carry more than half of All conv. and may be one form counted twice; then F1, since bidding has lost bookings; then F3 and F4 as questions for the business.

## What to tell the client

Two of your lead actions may be counting the same form, and together they are most of what your bidding learns from. Online bookings have recorded nothing in the last 7 days. Until both are settled, treat recent lead counts and cost per lead as unreliable. We will confirm with one test lead before switching anything.
