# Playbook: Debug a break in conversion tracking

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: for each break, name the failure layer to suspect first, the check that confirms it, and what bidding does meanwhile. It reads `conversion-breaks.md` from `scripts/find_breaks.py`, with the audit findings it links to.

## When to use it

- Conversions stopped, dropped, doubled, or an action moved in or out of the Conversions column. Run with `--actions`, and with `--clicks` and `--changes` whenever the person has them.
- For the audit's settings alone, open `audit-the-setup.md`. For a gap with another system, `explain-a-mismatch.md`.

## What to read in the output

For each break: its kind and day; both shares, each with its period; "Effect on the Conversions column"; "Linked to audit finding"; "Counts in Conversions ... Source ... Status"; "Other actions that broke within 1 day"; "Actions that kept recording"; "Campaigns that carried it" and "Paused now"; "Clicks in those campaigns" and "This action per click"; the account changes from the 3 days before; and the daily series.

## Which layer to suspect first

Stop at the first step the output supports. The cheap explanations come first. **Practitioner rule** for the order.

1. **Reporting delay.** The low days run only to the last day of the report, and the audit status still reads Recording conversions or Active. **Official** (references/conversion-action-settings.md): a conversion lands on the click's day, up to 90 days later, and Recording conversions means one was recorded in the last 7 days. Check: the Days to conversion segment.
2. **Traffic.** "Paused now" is printed, or clicks fell about as much as the action while "This action per click" held. **Official** (same file): paused campaigns are a usual reason for no recent conversions.
3. **Goal configuration.** Joined or Left the Conversions column, All conv. held, usually with a change history entry. Check: the goals the carrying campaigns use, and any custom goal.
4. **Double counting.** Started or Stepped up, or Joined with a link to the double counting finding: a second tag, a second action, or Count changed to Every. Check: one real conversion, and which actions count it.
5. **Something actions share.** "Other actions that broke within 1 day" names others: the tag manager, the consent banner, a site release.
6. **Collection for one action.** Stopped, the others kept recording, clicks carried on, no account change, source Website: its tag, page or form. Check: Tag Assistant from its Tracking status in Goals, Conversions, All conversions.
7. **Import.** Source Google Analytics: the key event, the link, the import delay. Source an upload: its schedule, identifiers, timestamps and path.
8. **Matching.** Stepped down rather than Stopped, often after a site change or a booking tool on another domain: lost click identifiers (gclid, gbraid, wbraid), consent, enhanced conversions.
9. **Attribution.** A model change in the change history. **Official** (references/attribution.md): it applies going forward.

## Read a break and its audit finding together

| Break | Audit finding or status | Read together as | First check | Label |
|---|---|---|---|---|
| Stopped | Linked to "Primary actions that are not recording" | One fault seen twice: Google also stopped seeing conversions | Hover the status, then Tag Assistant | **Official** (references/conversion-action-settings.md) |
| Stopped | Status Recording conversions or Active | Conversions still arrive, on earlier click days: delay, or files downloaded at different times | Days to conversion; both files for the same dates | Practitioner rule |
| Stepped down | Status Needs attention | Recording has not stopped entirely: a partial loss | Hover the status for Google's action items | **Official** (references/conversion-action-settings.md) |
| Joined the Conversions column | Linked to "Two Primary actions in one category from different sources" | Goal configuration that can count one event twice | One real conversion; Google's fix is to switch the extra action to Secondary | Practitioner rule for the flag, **Official** (references/conversion-action-settings.md) for the fix |
| Joined, no double counting finding | none | A promotion, intended or not | Ask who changed it and why | Practitioner rule |
| Left the Conversions column | none, or "Categories with only Secondary actions" | Bidding has lost that outcome | Confirm whether the business still wants it bid on | **Official** (references/conversion-action-settings.md): Secondary actions do not bid unless a custom goal includes them |
| Started or Stepped up | Linked to "Lead actions counted as Every" | A Count change, or a repeat converter now counted again | Change history for Count | **Official** (references/conversion-action-settings.md): a Count change applies to future conversions only |

A break can fit two layers of the list above, such as a Joined break that is both goal configuration and double counting. When this table links it to a finding, name the layer as the table reads it, as one cause. **Practitioner rule.**

Several breaks open at once are fixed in the order of `audit-the-setup.md`: what changes what bidding learns today first (not recording, double counting), larger share of Conversions first, one fix at a time so each effect can be read. **Practitioner rule.**

## While the break is open

- **Practitioner rule:** tracking repair comes before optimization. Mark every bid, target or budget idea provisional or blocked.
- **Official** (references/conversion-action-settings.md, references/tracking-and-signals.md): for an outage, a data exclusion protects Smart Bidding. Date it by the affected clicks plus the usual delay, cover at least 90% of them, and never remove it. Not for issues older than 14 days, or 60 on Shopping.
- **Official** (references/tracking-and-signals.md): after a goal or action change, Smart Bidding needs 1 to 2 conversion cycles in most cases.

## Practitioner rules for the checks

- **Find the step that stopped.** The trigger, consent, the sender in the browser or on a server, Google's receipt, any import, the action, the reporting window. A tag that fires, a conversion that is accepted, one that is reported and one that bidding uses are different facts.
- **Follow the click identifier through every handoff:** redirects, a booking or payment tool on another domain, a login. A later campaign tag can overwrite the original click. Never rewrite timestamps to get an upload accepted.
- **An upload accepted is not an upload completed.** Read its diagnostics. Never resend a batch because the result is unclear; order or lead IDs keep a resend from counting twice.
- **Test and staff conversions count** until excluded; an exclusion added now does not clean the past.
- **Prove the repair without fake outcomes:** Tag Assistant or one real test, then the daily report. Say which of fixed, received, reported and used for bidding you have seen.

## Failure modes

- **A late or traffic fall called a break.** Rule out steps 1 and 2 first.
- **A join called double counting untested.**
- **A website cause stated as fact.** Call it judgment; name the check.

## Worked example

B1, GA4 generate_lead, Joined the Conversions column on 2026-10-27: 0 to 6.41 a day, about +109.00 in all, an estimate. All conv. held, clicks -1.5%, the change history shows Secondary to Primary that day, linked to F2. Layer: goal configuration, causing double counting. B2, Online booking, Stopped on 2026-11-04: nothing for 9 days, 17.3% of Conversions before it; linked to F1, status No recent conversions; 4 of 4 others kept recording; clicks -6.9% while this action per click fell from 0.0344 to 0.0000; no account change. The status agrees, so not delay. Layer: collection for that one action.

## What to tell the client

On October 27 a second lead action started counting in your leads, so Google Ads may now count many form fills twice. On November 4 online bookings stopped recording while everything else carried on, which points to the booking page or its tag. We will test both before any bidding change.
