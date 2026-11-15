# Bid adjustments, Smart Bidding and audience settings

Written by hand. To be re-read against the source before release.

Read from Google Ads Help on 2026-11-13:

| Page | Link |
|---|---|
| About bid adjustments | https://support.google.com/google-ads/answer/2732132 |
| About Smart Bidding | https://support.google.com/google-ads/answer/7065882 |
| About "Targeting" and "Observation" settings | https://support.google.com/google-ads/answer/7365594 |

## What Google documents

These lines are **Official**.

- Bid adjustment ranges: device -100% to +900%; location -90% to +900%; ad scheduling -90% to +900%; audiences -90% to +900%.
- When several adjustments apply to one auction they are typically multiplied together. Combined, they cannot raise a bid by more than 900%, and the lowest combined adjustment is -90%. Multiple device and location adjustments behave differently.
- An ad schedule bid adjustment needs a custom ad schedule first.
- Smart Bidding means Target CPA, Target ROAS, Maximize conversions and Maximize conversion value. It optimizes for conversions or conversion value in every auction, using signals that include device, physical location (down to the city), and the searcher's local time of day and day of week.
- "If you make a manual bid adjustment to your automated Smart Bidding strategy, it won't be supported." The page's table shows device adjustments as "-100% only" for Target ROAS, Maximize conversions, Maximize conversion value and Target impression share. For Target CPA, a device adjustment changes the CPA target for that device rather than the bid. Location, ad scheduling and audience adjustments are shown as not supported for those strategies.
- Smart Bidding respects the campaign's ad schedule settings, so when ads run still applies.
- Audience settings: **Targeting** restricts the reach of the campaign or ad group to the chosen segments. **Observation** does not restrict reach. Custom bids or bid adjustments can be set on criteria under either setting.

## How the reviews use it

These lines are **Practitioner rules**.

- Manual CPC: device, location, ad schedule and audience bid adjustments can all act on a finding inside a campaign.
- Smart Bidding: a device finding can be acted on only by -100% (stopping that device), or for Target CPA by the device target adjustment. For a location, an hour or an audience, the levers are an exclusion, the ad schedule itself, the targeting setting, or the conversion data the strategy learns from. A finding the strategy already sees in its own signals may need no action.
- An account level finding spans campaigns with different strategies, so act on it campaign by campaign.
- An exclusion (a location, a placement, an audience segment) removes that traffic whatever the bid strategy.

## Not verified

- Part of the table on the bid adjustments page is images. Support under Maximize clicks and Enhanced CPC was not readable, so the reviews say to check those in the account.
- The page gives no date of last update.
