# Conversion action settings and status

Written by hand. To be re-read against the source before release.

Read from Google's Help pages on 2026-11-13. Every statement in this file is **Official** and names the page it comes from. Where a page does not say something, this file says so. The audit rules that are experience and not Google policy are marked **Practitioner rule** in `SKILL.md` and in the scripts' output, not here.

## The Status of a conversion action

Google's pages use two sets of names. An export can carry either, so the scripts read both.

**The Status column** (Goals, Conversions, All conversions, where the column is named Tracking status). Source: [Troubleshooting conversion tracking status](https://support.google.com/google-ads/troubleshooter/10028419).

| Status | What Google says it means |
|---|---|
| Active | Everything is working as intended. |
| Needs attention | There are action items to address, but conversions have not stopped recording entirely. |
| Misconfigured | Conversions have stopped recording entirely because of a setup error or a broken tag. |
| Awaiting conversions | No conversions have been recorded in the last 7 days. Google names three usual reasons: the action is new, the campaigns are paused, or traffic is too low. |
| Removed | The action was deleted or archived and no longer tracks data. |

Google says to hover over the status to see details and the steps to take.

**The Tracking status column.** Sources: [Use Tag Assistant to troubleshoot your unverified or inactive conversion actions](https://support.google.com/google-ads/answer/10989978), and for the definitions, Google's page for the same Google Ads column in Search Ads 360 Help, [Check the tracking status of your Google Ads conversion action](https://support.google.com/sa360/answer/9780742).

| Tracking status | What Google says it means |
|---|---|
| Unverified | Google has not yet verified that the tag is on the website. |
| No recent conversions | Google has seen the tag, but has recorded no conversions in the last 7 days. |
| Recording conversions | Google has seen the tag and recorded conversions within the last 7 days. |
| Tag inactive | Google no longer sees the tag, and has recorded no conversions in the last 7 days. If conversions stopped, Google says something may have changed with the website or the campaigns. |
| Removed | The action has been removed. |

Neither page defines a status named only "Inactive". The scripts treat it like Tag inactive: not recording.

**Tag Assistant.** In the conversions summary, hover over a status of Unverified, Tag inactive or Needs attention and choose Troubleshoot. Tag Assistant opens the site, you trigger the conversion yourself, and it reports whether the tag fired. Google says to enter a landing page or the home page, not the conversion page itself, and that verified actions update after about 30 minutes.

## Primary and Secondary

Source: [About primary and secondary conversion actions](https://support.google.com/google-ads/answer/11461796) and [About conversion goals](https://support.google.com/google-ads/answer/10995103).

- Primary actions are reported in the Conversions column and are used for bidding.
- Secondary actions are reported in the All conv. column and are not used for bidding. The one exception: a Secondary action that is part of a custom goal is used for bidding.
- Conversion actions are grouped into conversion goals by their category. A campaign uses an action for bidding when the action is Primary and its goal is one the campaign uses. New campaigns use all account default goals unless set otherwise.
- A report does not show which goals each campaign uses, or what a custom goal contains.

## Count: Every or One

Source: [About conversion counting options](https://support.google.com/google-ads/answer/3438531).

- **Every** counts every conversion that happens after an ad interaction. Google calls it a good choice for tracking and improving sales, because every sale likely adds value.
- **One** counts only one conversion per ad click. Google's example is a lead form: a business may want every sale counted, but only one unique lead per ad click.
- Google's own worked example: a click that leads to 2 sales and 2 leads shows 3 conversions when the sale action counts Every and the lead action counts One.
- Defaults. Every: website actions, in-app actions, Analytics transactions, clicks on a number on a mobile website, and imports. One: calls from ads, Analytics goals, calls to a phone number on a website, and app installs.
- A change to the count setting applies to future conversions only.
- **Repeat rate**, a column in the conversion actions table, is the average number of conversions from customers who convert at least once. Google describes it as roughly the Every count divided by the One count.

## Value

Source: [About conversion values](https://support.google.com/google-ads/answer/3419241).

- An action can use the same value for each conversion, or a different value for each conversion. The second is closer to what each transaction is worth and takes more work to set up.
- When different values are chosen but the tag sends none, the default value entered in the action is used for all conversions.
- Conversion value measurement has to be set up before values can be used for insights or for Smart Bidding.

Source: [Data discrepancies: Factors and troubleshooting](https://support.google.com/google-ads/answer/7457111), under "Action optimization settings".

- If conversion value looks inflated, Google says to check the settings of the conversion actions. Non purchase actions that are Primary and carry a value can double count value. Google's fix is to switch them to Secondary or to remove their value.

## Conversion windows

Source: [About conversion windows](https://support.google.com/google-ads/answer/3123169).

- The window is the period after an ad interaction during which a conversion is recorded. A conversion after the window is not recorded and does not appear in reports.
- Defaults: 30 days for click-through, 1 day for view-through, 3 days for engaged-view.
- A change to a window applies to conversions going forward.

## Conversion actions created from Google Analytics

Sources: [Create conversions from Google Analytics events in Google Ads](https://support.google.com/google-ads/answer/2375435) and [Create Google Ads conversions based on Google Analytics key events](https://support.google.com/analytics/answer/10632359).

- Actions based on Google Analytics key events, or created from the Google Analytics interface, are set to Secondary. Google's stated reason is to prevent counting the same event twice for bidding. They can be changed to Primary in Google Ads.
- It can take up to 24 hours before conversion data is available in Google Ads after a key event is imported. Renaming a key event or a property can also take up to 24 hours to show in Google Ads.
- The count setting, One or Every, applies to these actions too.
- Some events that Analytics reports can be filtered out on import by Google Ads invalid click detection.

Google's pages do not give a rule for two Primary actions that record the same event from two sources. The check for that in this skill is a **Practitioner rule**.

## Why Google Ads and another system can differ

Source: [Data discrepancies: Factors and troubleshooting](https://support.google.com/google-ads/answer/7457111), with the date rule also stated on [Create conversions from Google Analytics events in Google Ads](https://support.google.com/google-ads/answer/2375435).

| Factor | What Google says |
|---|---|
| The date a conversion is reported on | Google Ads reports a conversion on the date of the ad interaction that led to it. Other tools report it on the date it happened. One page words this as the date and time of the click, the other as the ad impression date. Google suggests adding the "Conversions (by conv. time)" column to compare like with like. |
| Late conversions | Conversions can be reported up to 90 days after the click. Recent days keep filling in. |
| Count setting | Every or One changes the number. |
| Primary and Secondary | Only Primary actions are in the Conversions column. All conv. also holds Secondary actions. |
| Attribution | The attribution model changes how credit is shared. Google Ads reports a conversion only when there was a Google Ads interaction. |
| Cross-device conversions | Google Ads models conversions for people who start on one device and finish on another. |
| View-through conversions | They are not in the Conversions column by default. |
| Invalid traffic | Conversions from invalid clicks can be removed. |
| Processing time | Google says to allow 24 to 48 hours between Google Analytics and Google Ads before comparing, and up to 7 days after a significant change or a new account link. |

The page does not discuss time zones or consent. For consent, use `tracking-and-signals.md`.

## Segments in a table

Source: [Use segments in your tables](https://support.google.com/google-ads/answer/2454072).

- The conversion segments are Conversion action, Conversion category, Conversion source and Days to conversion.
- When a conversion segment is applied, Clicks, Impr. and Cost show "--". Clicks therefore need their own report without the conversion segment.
- The page says a table can be segmented by Day only when the date range is 16 days or less, and that a report may have to be downloaded to apply a segment. For a longer range, build the table in the Report editor.

## Data exclusions after an outage

Source: [About data exclusions](https://support.google.com/google-ads/answer/10370710).

- A data exclusion reduces the effect of a conversion tracking problem on Smart Bidding. It works with conversion based and conversion value based Smart Bidding in Search, Display, Shopping and Performance Max campaigns.
- Dates are chosen by the clicks that were affected, not by the conversions. Google says to allow for the usual delay between click and conversion, and to try to cover at least 90% of the affected clicks.
- Google says not to remove a data exclusion once it is applied, and not to use them often or for long periods.
