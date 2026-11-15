# Conversion breaks

Conversions by action and day.
October 14, 2026 - November 12, 2026.

## What was read

- 30 days, 2026-10-14 to 2026-11-12, taken from the date range above the header.
- 5 conversion actions. All conv. across all of them: 608.00. The Conversions column was read too, to see actions join or leave it.
- All conv.: the rows add up to 608.00 and the file's own "Total: Account" row says 608.00.
- Conversions summary: read.
- Clicks: read.
- Change history: read.

## Account

The Conversions column for the whole account, between the days the breaks start and end:

| From | To | Days | Conversions a day | All conv. a day | Breaks that start |
|---|---|---|---|---|---|
| 2026-10-14 | 2026-10-26 | 13 | 13.08 | 21.15 |  |
| 2026-10-27 | 2026-11-03 | 8 | 19.88 | 21.25 | B1 |
| 2026-11-04 | 2026-11-12 | 9 | 16 | 18.11 | B2 |

- Effect of the breaks on Conversions over the report, each at its action's earlier rate: rises add 109, falls take away 24.43, net +84.57. These are estimates.
- On the last day the breaks still open change Conversions by +3.70 a day: B1 +6.41; B2 -2.71. Conversions ran at 16 a day from 2026-11-04; without those breaks it would be about 12.3 a day, against 13.08 a day from 2026-10-14 to 2026-10-26. This is an estimate.
- No break in the account total. A break in one action can hide inside a steady total when another action grows, so each action was checked on its own.

## Breaks found

### B1. GA4 generate_lead: Joined the Conversions column on 2026-10-27

- Conversions showed nothing from 2026-10-14, then 6.41 a day from 2026-10-27 to 2026-11-12.
- All conv. for this action held steady, so the action kept recording and only its place in the Conversions column changed.
- Share of All conv. for all actions: 29.9% over the whole report, 2026-10-14 to 2026-11-12; 32.7% over the days since, 2026-10-27 to 2026-11-12.
- Share of Conversions for all actions: 23.0% over the whole report; 36.0% over the days since.
- Effect on the Conversions column: +6.41 a day, from 0 a day before 2026-10-27 to 6.41 a day after, about +109.00 in all. This is an estimate.
- Conversions for the whole account: 13.08 a day before 2026-10-27, 17.82 a day from then to 2026-11-12.
- **Linked to audit finding F2, Two Primary actions in one category from different sources.** It is Primary in Submit lead form, where Website lead form is also Primary from another source. From 2026-10-27 both can count the same conversion.
- Counts in Conversions, the column bidding uses: Yes. Source: Google Analytics (GA4). Status: Recording conversions.
- Other actions that broke within 1 day: none.
- Campaigns that carried it: Plumbing | Emergency 38.5% (Enabled now); Plumbing | Water Heaters 30.3% (Enabled now); Drain Cleaning | Search 20.2% (Enabled now); Brand 11.0% (Enabled now).
- Clicks in those campaigns: 77.85 a day before, 76.65 a day from 2026-10-27 (-1.5%). This action per click: 0.0000 before, 0.0837 after.
- Account changes in the 3 days before:
  - 2026-10-27 by manager@example.com: Conversion action GA4 generate_lead changed; Action optimization changed from Secondary action to Primary action
- Daily Conversions from 2026-10-20 to 2026-11-12, the last day of the report: 10-20 0, 10-21 0, 10-22 0, 10-23 0, 10-24 0, 10-25 0, 10-26 0, 10-27 5, 10-28 8, 10-29 10, 10-30 11, 10-31 5, 11-01 6, 11-02 7, 11-03 7, 11-04 2, 11-05 7, 11-06 7, 11-07 5, 11-08 4, 11-09 8, 11-10 8, 11-11 2, 11-12 7

Rules that apply:

- **Official:** Bidding uses a conversion action only when it is Primary and in a goal the campaign uses. Secondary actions are reported in All conv. only, unless a custom goal includes them. (Google Ads Help, About primary and secondary conversion actions.)
- **Practitioner rule:** Two Primary actions in one category from different sources can be the same event counted twice. Confirm what each one records before changing either.
- **Official:** Goal and action changes need 1 to 2 conversion cycles in most cases, and Google recommends moving targets gradually. (Google Ads Help, Changing conversion goals and actions used for Smart Bidding.)

Checks outside Google Ads reports: in the list below, marked B1.

### B2. Online booking: Stopped on 2026-11-04

- All conv. recorded 2.71 a day on the other days, then nothing on 9 days in a row, 2026-11-04 to 2026-11-12. At that earlier rate a run that long is very unlikely by chance, if conversions arrive at random around a steady rate.
- Share of All conv. for all actions: 9.4% over the whole report, 2026-10-14 to 2026-11-12; 12.8% over the days before it, 2026-10-14 to 2026-11-03.
- Share of Conversions for all actions: 12.1% over the whole report; 17.3% over the days before it.
- Effect on the Conversions column: -2.71 a day, from 2.71 a day before 2026-11-04 to 0 a day after, about -24.43 in all. This is an estimate.
- Conversions for the whole account: 15.67 a day before 2026-11-04, 16 a day from then to 2026-11-12.
- Linked to audit finding F1, Primary actions that are not recording.
- At its usual rate, about 24.43 fewer in All conv. than expected from 2026-11-04 to 2026-11-12. This is an estimate.
- Counts in Conversions, the column bidding uses: Yes. Source: Website. Status: No recent conversions.
- Other actions that broke within 1 day: none.
- Actions that kept recording after 2026-11-04: 4 of 4 others.
- Campaigns that carried it: Plumbing | Emergency 47.4% (Enabled now); Plumbing | Water Heaters 24.6% (Enabled now); Drain Cleaning | Search 19.3% (Enabled now); Brand 8.8% (Enabled now).
- Clicks in those campaigns: 78.81 a day before, 73.33 a day from 2026-11-04 (-6.9%). This action per click: 0.0344 before, 0.0000 after.
- No account change is recorded in the 3 days before.
- Daily All conv. from 2026-10-28 to 2026-11-12, the last day of the report: 10-28 5, 10-29 5, 10-30 2, 10-31 0, 11-01 3, 11-02 3, 11-03 1, 11-04 0, 11-05 0, 11-06 0, 11-07 0, 11-08 0, 11-09 0, 11-10 0, 11-11 0, 11-12 0

Rules that apply:

- **Practitioner rule:** When the conversion signal is broken, repairing tracking comes before any optimization.
- **Official:** A data exclusion reduces the effect of a tracking outage on Smart Bidding. Its dates are chosen by the affected clicks, allowing for the usual delay between click and conversion. Google says not to remove one once applied. (Google Ads Help, About data exclusions.)
- **Practitioner rule:** While tracking is in doubt, changes to bids, targets and budgets are provisional.
- **Official:** Google Ads reports a conversion on the date of the ad interaction that led to it, not the date it happened, and conversions can be reported up to 90 days after the click. Recent days keep filling in. (Google Ads Help, Data discrepancies: Factors and troubleshooting.)

Checks outside Google Ads reports: in the list below, marked B2.

## Checks outside Google Ads, by who usually does them

**You, in Google Ads**

1. Read the change history for the days just before 2026-10-27. Look for this action changing between Primary and Secondary, or a campaign changing the goals it uses. (Practitioner rule) For break B1.
2. Check which goals each affected campaign uses, and whether a custom goal is in play. A report does not show this. (Official: Google Ads Help, About conversion goals) For break B1.
3. In Google Ads, open Goals, Conversions, All conversions and hover over the Tracking status of this action. Google shows its own diagnosis there. (Official: Google Ads Help, Troubleshooting conversion tracking status) For break B2.
4. Read the change history for the days just before 2026-11-04. Look for edits to conversion actions, to goals, and to the goals a campaign uses. (Practitioner rule) For break B2.

**The website developer**

1. Ask what changed on the website on or just before 2026-11-04: a release, a new form or checkout, a new confirmation page address, or a tag manager publish. (Practitioner rule) For break B2.
2. Check the consent banner. Default consent states must be set before any tag sends data, and updated after the visitor chooses. Check ad_user_data and ad_personalization, not only cookie storage. (Official: Google for Developers, Set up consent mode on websites) For break B2.
3. Confirm the click identifiers still reach the site and the tag: gclid, gbraid or wbraid. (Practitioner rule) For break B2.

**Whoever manages Google Tag Manager or GA4**

1. Trigger the conversion yourself on the live site and watch the tag. Tag Assistant does this: in Goals, Conversions, All conversions, hover over the Tracking status and choose Troubleshoot. (Official: Google Ads Help, Use Tag Assistant to troubleshoot your unverified or inactive conversion actions) For break B2.

**Whoever owns the booking or form tool**

1. Ask whether the booking or form tool changed on or just before 2026-11-04: a new version, a new domain or a new confirmation page. A tool on another domain can lose the tag or the click identifier. (Practitioner rule) For break B2.

## Actions you asked about

- **Website lead form:** 181.00 All conv. over 30 days, 29.8% of the total. 6.13 a day in the first 15 days, 5.93 a day in the last 15. No break under the rules below.

## Actions with no break

| Conversion action | All conv. | Share | Days with conversions | Last day |
|---|---|---|---|---|
| Website lead form | 181.00 | 29.8% | 30 of 30 | 2026-11-12 |
| Calls from ads | 126.00 | 20.7% | 30 of 30 | 2026-11-12 |
| Directions clicks | 62.00 | 10.2% | 27 of 30 | 2026-11-11 |

## How the numbers were made

- A day with no row for an action counts as zero for that action. Every day from 2026-10-14 to 2026-11-12 is in the series.
- A stop is a run of at least 3 days with nothing, when the action's rate on the other days makes such a run rarer than 1 in 100. This assumes conversions arrive at random around a steady rate.
- A step is the day that best splits the series into a before and an after, each at least 7 days long so that a weekly pattern cannot make one. It counts when the daily average moves 20% or more and the move is at least 3 times the day to day noise. The noise is never taken as smaller than conversions arriving at random would give.
- A share is the action's part of All conv. or Conversions for all actions in this report. Each break gives it over the whole report and over the days before a fall or since a rise, with both periods named.
- The effect on Conversions is the action's daily Conversions after the break minus its daily Conversions before it. The net effect adds these up. Both are estimates.
- Breaks within 1 day of each other are listed together. Account changes are listed from the 3 days before a break.
- A change just before a break is a lead to check, not proof of the cause.

## What this did not cover

- The website, the tags, the consent banner and any upload. The checks above say what to look at there.
- Which goals each campaign uses. A report does not show this.
- Conversions are reported on the day of the click, and recent days can still fill in. A fall in the last days of the file can be a delay, not a break.
- An action whose conversions are too few to tell a stop from chance. The table above shows how often each one recorded.
