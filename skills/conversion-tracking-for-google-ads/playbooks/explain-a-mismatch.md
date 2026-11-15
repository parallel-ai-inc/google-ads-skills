# Playbook: Explain a mismatch between Google Ads and another count

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: when Google Ads shows more or fewer conversions than GA4, a CRM or the office, separate a real break from two systems counting by different rules, and say which. It reads the "Account" section and the breaks in `conversion-breaks.md`, with the audit in `conversion-audit.md`.

## When to use it

- "Google Ads says more leads than ever, the office sees fewer." "GA4 and Google Ads do not match." "The CRM shows fewer sales."
- When a break is found, open `debug-a-break.md` for its layer. For the settings, `audit-the-setup.md`.

## What to read in the output

- Under "Account": the table of "Conversions a day" and "All conv. a day" between the days the breaks start; "Effect of the breaks on Conversions over the report", with rises, falls and the net; and "On the last day the breaks still open change Conversions by ...", which gives Conversions a day now and without the open breaks.
- Each break's kind, "Effect on the Conversions column" and "Conversions for the whole account" before and after.
- The audit's "Lead actions counted as Every" and "Two Primary actions in one category from different sources".
- "Actions you asked about", when the person named one.

## The decisions

| What the output shows | What it means | What to do | Label |
|---|---|---|---|
| Google Ads higher, with a Joined, Started or Stepped up break, or a double counting finding | Google Ads counts more than happened | Lead with the net effect line and the Conversions a day without the open breaks | Practitioner rule |
| Google Ads higher, a lead action counted as Every | Repeat forms or calls from one click each count | Ask whether a second form is a second lead. A Count change applies to future conversions only | **Official** (references/conversion-action-settings.md) |
| Google Ads lower, with a Stopped, Stepped down or Left break | Google Ads missed or stopped bidding on real outcomes | Open `debug-a-break.md` | Practitioner rule |
| Google Ads lower, no break | Google Ads counts only conversions after a Google Ads interaction. The office counts every channel | Expected. Do not call it broken | **Official** (references/conversion-action-settings.md) |
| Google Ads and GA4 differ, no break | Different rules: the date a conversion lands on, attribution, count, Primary or Secondary, cross device, view through, invalid traffic, processing time | Name the factors that apply, from the table "Why Google Ads and another system can differ" | **Official** (references/conversion-action-settings.md) |
| GA4's own screens and its BigQuery export differ | Identity, thresholding, modeling or the export path | A modeling or export question before a tracking one | **Official** (references/ga4-engineering.md) |
| The person compares All conv. with their leads | All conv. includes Secondary actions | Compare the Conversions column, or the one action that records the outcome | **Official** (references/conversion-action-settings.md) |

## Make the two counts comparable first

Before calling any gap real, line up five things. **Practitioner rule** for the list; the date rule is **Official**.

1. **The outcome.** One action that records the same thing the other system counts. A form fill, a qualified lead and a paying customer are three outcomes.
2. **The date.** Google Ads puts a conversion on the day of the click. Most other tools use the day it happened. Add "Conversions (by conv. time)" in Google Ads to compare like with like. **Official** (references/conversion-action-settings.md).
3. **Maturity.** Recent days keep filling in for up to 90 days. Compare periods old enough on both sides.
4. **Time zone and currency** of each system.
5. **Filters.** Test, internal and spam records the other system removed or kept.

**Practitioner rules from reconciling real accounts:**

- Keep one ledger of real customers and payments in the business's own records. Each ad platform keeps its own window and model. When two platforms both claim one customer, each is right by its own rules, and adding them overcounts.
- Fractional attribution credit is not a count of people. Dividing two Google Ads totals does not give a customer rate.
- An import that is linked does not prove that past event definitions were right.

## How big a change

- **Official** (references/conversion-action-settings.md): allow 24 to 48 hours between Google Analytics and Google Ads before comparing, and up to 7 days after a significant change or a new account link. A key event imported from Google Analytics can take up to 24 hours to reach Google Ads.
- **Official** (references/attribution.md): data driven attribution works for every action, but Google recommends about 200 conversions and 2,000 ad interactions in 30 days for stronger precision. A model change applies going forward.
- **Official** (references/tracking-and-signals.md): consent mode modeling starts at 700 ad clicks over 7 days for each country and domain grouping. A smaller account may not have the conversions lost to declined consent modeled back.
- Never compute the gap between Google Ads and the other system yourself. If the person gives their number, show it beside the script's number and name the factors. The script's net effect and "without those breaks" lines are the only adjusted figures to quote, and both are estimates.

## Failure modes

- **Every gap treated as a fault.** Name the rule that explains it first.
- **Click date compared with conversion date.** Shows as a gap that moves day to day while totals agree over a month.
- **Recent days compared.** The newest days are still filling in.
- **All conv. compared with leads.** It includes Secondary actions.
- **Two platforms added together.** The customer is counted twice.
- **An adjusted figure worked out in your head.** Quote the script's estimate or nothing.

## Worked example

The trial message: "Google Ads says more leads than ever, the office sees fewer." The Account table shows Conversions at 13.08 a day from 2026-10-14 to 2026-10-26, 19.88 a day from 2026-10-27 to 2026-11-03, and 16 a day from 2026-11-04. The breaks add 109 and take away 24.43, net +84.57, estimates. On the last day the open breaks add +3.70 a day: B1 +6.41, B2 -2.71. Without them, Conversions would be about 12.3 a day, against 13.08 before. So both are right: Google Ads rose because GA4 generate_lead joined the column, while the office's real leads are close to where they were, a little lower with bookings missing.

## What to tell the client

You are both right. Since October 27 Google Ads also counts a second lead action, which inflates its lead count, and since November 4 it has stopped seeing online bookings. Without those two, Google Ads would show about 12.3 leads a day, close to the 13.08 a day before October 27 and a little lower, which fits the office seeing fewer.
