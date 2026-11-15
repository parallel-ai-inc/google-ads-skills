# Google Ads platform changes, with their dates

Written by hand. To be re-read against the source before release.

Every change below is **Official**. Each keeps its date and names the file in this folder that holds it. One change, the August 17, 2026 rule, was in no other file here, so its Google page is restated in full at the end. The Google page behind it was read on 2026-11-13.

## The changes, in date order

| Date | What changed | Held in | What the exports show |
|---|---|---|---|
| March 31, 2025 | Enhanced CPC is no longer available for Search and Display campaigns. | `search-campaign-setup.md`, Retired Search Settings | Bid strategy type in the campaign report. The audit's check BB-01 reads it. |
| January 26, 2026 | The "Add responsive search ads" recommendation no longer suggests or applies new responsive search ads automatically, and is gone from the auto-apply settings. | `recommendations-and-auto-apply.md` | Nothing. Read the auto-apply settings in Google Ads. |
| June 11, 2026 (announced) | Google's Dynamic Search Ads update: Dynamic Search Ads are to be upgraded to AI Max, with their sunset and automatic upgrade scheduled for February 2027. New Dynamic Search Ads are a transition surface, not the growth path. | `search-campaign-setup.md`, AI Max And Legacy DSA Transition | Ad type in the ads report. The audit lists dynamic search ads under DATED PLATFORM CHANGES. |
| July 21, 2026 | A policy decision older than 6 months can no longer be appealed in the account. | `compliance.md`, appeals | Nothing about the decision's date. The ads report shows which ads are disapproved (AD-02). |
| August 17, 2026 (rollout finished August 27, 2026) | Target CPA and Target ROAS campaigns that are limited by budget bid toward their target instead of beating it. | This file, below | Bid strategy type, Status and Search lost IS (budget) in the campaign report. The audit lists those campaigns under DATED PLATFORM CHANGES. |
| September 1 to 30, 2026 | Campaigns that used automatically created assets or campaign level broad match were upgraded to AI Max. A migrated campaign kept equivalent settings, not the full AI Max suite. | `search-campaign-setup.md`, AI Max And Legacy DSA Transition | Nothing. Read each Search campaign's settings. |
| September 2026 | Manual language targeting is no longer supported for Search campaigns or AI Max for Search. Performance Max keeps the setting for its other channels, but it no longer limits Performance Max ads on Google Search. | `search-campaign-setup.md`, Retired Search Settings | Nothing. Old language settings can still be read in each campaign. |

Facts on the same pages that are not tied to a date, but decide how a change is judged:

- AI Max is on by default for new Search campaigns. Search term matching does not work with Manual CPC, and Google says AI Max needs conversion based Smart Bidding to work well and will not be effective while the campaign is limited by budget. After turning it on, wait at least 2 weeks before changes such as adding negatives. Turning it off also turns off its brand exclusions and ignores its URL rules. (`search-campaign-setup.md`)
- Merging campaigns or ad groups that keep the same creatives and goal should not need much learning, while adopting AI Max or changing the bidding goal does. Restructure a handful of campaigns at a time. This is spoken guidance from a Google product lead, ranked below Help pages. (`account-structure.md`)

## The August 17, 2026 rule for budget limited target campaigns

Source: Google Ads Help, "Frequently asked questions about changes to Target-based bid strategies", https://support.google.com/google-ads/answer/17125145

**What changed.** The change rolled out globally on August 17, 2026 and finished on August 27, 2026. Target CPA and Target ROAS campaigns that are limited by budget now optimize more consistently to their set target, even when budgets change. In practice a campaign that used to beat its target trends toward it.

**Included.** Target CPA and Target ROAS across most campaign types, including Search, Shopping, Performance Max, Demand Gen and Travel. Target CPC on Demand Gen. All conversion types, online and offline, in those campaign types.

**Not included.** Manual CPC and Target impression share. Target CPA and Target ROAS campaigns that are not limited by budget, which keep their current behaviour. Campaigns on campaign total budgets, unless they are limited by their target. Smart Bidding Exploration, in general.

**What Google does not change.** It does not adjust bid targets or daily budgets for you. Auction mechanics do not change. Daily and monthly budget limits are still respected, and the change is not meant to raise spend by itself.

**What Google tells advertisers to do.**

- Review budget limited campaigns on target based strategies, above all those beating their targets.
- Keep the target, set it to match recent performance, or set a different one. Switching to Maximize conversions or Maximize conversion value is also an option.
- Give campaigns budget room where possible.
- Consider portfolio bid strategies or shared budgets to consolidate.
- Wait 1 to 2 conversion cycles before judging performance in the bid strategy report.
- Do not add data exclusions or new bid limits only because of this change, since that can cause swings.

## What these pages do not settle

- Which of an account's campaigns were upgraded to AI Max in September 2026. Google's schedule is not proof of one campaign's state. Read each campaign.
- Whether a Maximize conversions campaign with a target CPA set shows "Target CPA" in the Bid strategy type column of a download. Read the campaign's bid strategy in Google Ads.
