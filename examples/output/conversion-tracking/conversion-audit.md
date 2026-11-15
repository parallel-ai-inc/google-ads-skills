# Conversion tracking audit

Conversion actions.
October 14, 2026 - November 12, 2026.

## What was read

- 5 conversion actions: 4 Primary, 1 Secondary. Not recording or needing attention: 1.
- Removed actions, listed apart and not audited: Old contact form.
- All conv. across the audited actions: 608.00.
- All conv.: the rows add up to 608.00 and the file's own "Total: Conversion actions" row says 608.00.

## What the audit found

### F1. Primary actions that are not recording

Online booking (Website, Book appointment, status No recent conversions, All conv. 57.00, 9.4% of All conv. over the whole report (2026-10-14 to 2026-11-12)) is Primary, so bidding uses it, and its status is No recent conversions.

Share: 9.4% of All conv. over the whole report (2026-10-14 to 2026-11-12).

- **Official:** Awaiting conversions and No recent conversions mean no conversion was recorded in the last 7 days. Misconfigured means recording has stopped because of a setup error or a broken tag. Tag inactive means Google no longer sees the tag. (Google Ads Help, Troubleshooting conversion tracking status.)
- **Official:** Bidding uses a conversion action only when it is Primary and in a goal the campaign uses. Secondary actions are reported in All conv. only, unless a custom goal includes them. (Google Ads Help, About primary and secondary conversion actions.)
- **Practitioner rule:** When the conversion signal is broken, repairing tracking comes before any optimization.

Checks outside Google Ads reports: in the list below, marked F1.

### F2. Two Primary actions in one category from different sources

In Submit lead form, 2 Primary actions come from 2 different sources: GA4 generate_lead (Google Analytics (GA4), Submit lead form, status Recording conversions, All conv. 182.00, 29.9% of All conv. over the whole report (2026-10-14 to 2026-11-12)); Website lead form (Website, Submit lead form, status Recording conversions, All conv. 181.00, 29.8% of All conv. over the whole report (2026-10-14 to 2026-11-12)). GA4 generate_lead and Website lead form carry a value, so value can be counted twice too. **Official:** Non purchase actions that are Primary and carry a value can double count value. Google's fix is to switch them to Secondary or to remove their value. (Google Ads Help, Data discrepancies: Factors and troubleshooting.)

Share: 59.7% of All conv. over the whole report (2026-10-14 to 2026-11-12).

- **Practitioner rule:** Two Primary actions in one category from different sources can be the same event counted twice. Confirm what each one records before changing either.
- **Official:** Google sets conversion actions created from Google Analytics to Secondary to prevent counting the same event twice for bidding, and its fix for double counting is to switch the extra action to Secondary. (Analytics Help, Create Google Ads conversions based on Google Analytics key events.)
- **Official:** Bidding uses a conversion action only when it is Primary and in a goal the campaign uses. Secondary actions are reported in All conv. only, unless a custom goal includes them. (Google Ads Help, About primary and secondary conversion actions.)

Checks outside Google Ads reports: in the list below, marked F2.

### F3. Lead actions counted as Every

Website lead form (Website, Submit lead form, status Recording conversions, All conv. 181.00, 29.8% of All conv. over the whole report (2026-10-14 to 2026-11-12)) is a Primary action counted as Every, so a second form or call from one click counts again.

Share: 29.8% of All conv. over the whole report (2026-10-14 to 2026-11-12).

- **Official:** Every counts each conversion after an ad interaction. One counts only one conversion per ad click. Google calls Every a good choice for sales, and gives leads as the case for One: only one unique lead per click. (Google Ads Help, About conversion counting options.)
- **Official:** A change to the count setting applies to future conversions only. (Google Ads Help, About conversion counting options.)

Checks outside Google Ads reports: in the list below, marked F3.

### F4. Categories with only Secondary actions

Get directions has only Secondary actions: Directions clicks (Website, Get directions, status Recording conversions, All conv. 62.00, 10.2% of All conv. over the whole report (2026-10-14 to 2026-11-12)). Bidding does not use them unless a custom goal includes them.

Share: 10.2% of All conv. over the whole report (2026-10-14 to 2026-11-12).

- **Official:** Bidding uses a conversion action only when it is Primary and in a goal the campaign uses. Secondary actions are reported in All conv. only, unless a custom goal includes them. (Google Ads Help, About primary and secondary conversion actions.)

Checks outside Google Ads reports: in the list below, marked F4.

## Checks outside Google Ads, by who usually does them

**You, in Google Ads**

1. In Google Ads, open Goals, Conversions, All conversions and hover over the Tracking status of this action. Google shows its own diagnosis there. (Official: Google Ads Help, Troubleshooting conversion tracking status) For finding F1.
2. Read the change history for the days just before it stopped. Look for edits to conversion actions, to goals, and to the goals a campaign uses. (Practitioner rule) For finding F1.
3. Check which goals each affected campaign uses, and whether a custom goal is in play. A report does not show this. (Official: Google Ads Help, About conversion goals) For findings F2, F4.
4. Ask whether any campaign bids on value (Maximize conversion value or Target ROAS). If one does, a value counted twice is in what it bids on. (Practitioner rule) For finding F2.

**The website developer**

1. Ask what changed on the website on or just before it stopped: a release, a new form or checkout, a new confirmation page address, or a tag manager publish. (Practitioner rule) For finding F1.
2. Check the consent banner. Default consent states must be set before any tag sends data, and updated after the visitor chooses. Check ad_user_data and ad_personalization, not only cookie storage. (Official: Google for Developers, Set up consent mode on websites) For finding F1.
3. Confirm the click identifiers still reach the site and the tag: gclid, gbraid or wbraid. (Practitioner rule) For finding F1.

**Whoever manages Google Tag Manager or GA4**

1. Trigger the conversion yourself on the live site and watch the tag. Tag Assistant does this: in Goals, Conversions, All conversions, hover over the Tracking status and choose Troubleshoot. (Official: Google Ads Help, Use Tag Assistant to troubleshoot your unverified or inactive conversion actions) For finding F1.
2. Find out what each action records. Make one real conversion and see which actions count it. (Practitioner rule) For finding F2.
3. Check whether a tag now fires twice: on a reloaded confirmation page, on two pages, or from two tags for the same action. (Practitioner rule) For finding F2.

**Whoever owns the booking or form tool**

1. Ask whether the booking or form tool changed on or just before it stopped: a new version, a new domain or a new confirmation page. A tool on another domain can lose the tag or the click identifier. (Practitioner rule) For finding F1.

**The business**

1. Ask the business whether a second form or call from the same person is a second lead. (Practitioner rule) For finding F3.
2. Ask the business whether this is an outcome it would pay for. (Practitioner rule) For finding F4.

## Where the conversions are

The fewest actions that carry most of the All conv., meaning more than half: GA4 generate_lead, Website lead form. A fault in one of these moves the numbers most.

| Conversion action | Optimization | Source | All conv. | Share | Running share |
|---|---|---|---|---|---|
| GA4 generate_lead | Primary | Google Analytics (GA4) | 182.00 | 29.9% | 29.9% |
| Website lead form | Primary | Website | 181.00 | 29.8% | 59.7% |
| Calls from ads | Primary | Calls from ads | 126.00 | 20.7% | 80.4% |
| Directions clicks | Secondary | Website | 62.00 | 10.2% | 90.6% |
| Online booking | Primary | Website | 57.00 | 9.4% | 100.0% |

## Categories

| Category | Actions | Primary | Secondary | All conv. | Share |
|---|---|---|---|---|---|
| Submit lead form | 2 | 2 | 0 | 363.00 | 59.7% |
| Phone call lead | 1 | 1 | 0 | 126.00 | 20.7% |
| Get directions | 1 | 0 | 1 | 62.00 | 10.2% |
| Book appointment | 1 | 1 | 0 | 57.00 | 9.4% |

## How the numbers were made

- Every share is a share of All conv. over the whole report (2026-10-14 to 2026-11-12) across the audited actions. Removed actions and heading rows are not in the base.
- A purchase action is one whose category contains the word Purchase. A lead action is one whose category contains Lead, Contact, Sign-up, Quote or Appointment. A page view action is one whose category is Page view.
- Two Primary actions are flagged as possible double counting when they share a category and their Conversion source differs.
- An action is not recording when its status reads Misconfigured, Awaiting conversions, No recent conversions, Unverified, Tag inactive or Inactive, and needs attention when it reads Needs attention.
- "Most of the conversions" means more than half. That is a definition, not a benchmark.

## What this did not cover

- Which goals each campaign uses, and what a custom goal contains. A report does not show this, so an action may be used for bidding in some campaigns and not others.
- The website, the tags, the consent banner and any upload. The checks above say what to look at there.
- Changes over time. Run the breaks step on a report by conversion action and day for that.
