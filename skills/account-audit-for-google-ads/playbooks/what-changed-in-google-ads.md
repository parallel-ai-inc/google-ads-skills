# Playbook: What changed in Google Ads, dated, checked against this account

Written by hand from Parallel AI's operating knowledge. Reviewed 2026-11-13.

The job: check the account against Google's dated platform changes, say which ones touch it, and fold each into the fix plan at its stage. Every change keeps its date and its reference file, listed in `references/platform-changes-2026.md`. You read the **DATED PLATFORM CHANGES THE FILES CAN SHOW** section of `scripts/audit.py`, BB-01 and AD-02, and SE-M2 under CHECKS NOT RUN.

## When to use it

Every full audit, because some changes alter what a finding means. Also when performance moved and nobody changed anything, or the person asks what is new in Google Ads.

## What to read in the output

- **August 17, 2026 line:** enabled campaigns whose Bid strategy type names Target CPA or Target ROAS, and how many are limited by budget, with a table of those: Campaign, Bid strategy type, Status, Search lost IS (budget), Cost / conv.
- **June 11, 2026 line:** dynamic search ads in the ads report, how many serving, and their ad groups.
- **BB-01:** Enhanced CPC on Search or Display, the March 31, 2025 change.
- **AD-02:** disapproved ads, for the July 21, 2026 appeal window.
- **FILES READ:** the date range. A file that spans a change date blends the before and the after.
- **SE-M2:** the AI Max settings no export shows.

## The decisions

| Date and change | What the output shows | What it means | What to do | Label |
|---|---|---|---|---|
| March 31, 2025. Enhanced CPC gone for Search and Display. | BB-01 fails | The campaign runs on a strategy Google no longer offers. | Stage 5. For Search, target based bidding is Maximize conversions with a target CPA, or Maximize conversion value with a target ROAS. Choose after measurement is fixed. | Official (references/search-campaign-setup.md) |
| January 26, 2026. "Add responsive search ads" no longer applies automatically. | Nothing in the files | An ad group with one ad will not get a second from auto-apply. | Write the second ad by hand where AD-04 fails. | Official (references/recommendations-and-auto-apply.md) |
| June 11, 2026, announced. Dynamic Search Ads to be upgraded to AI Max, with sunset and automatic upgrade scheduled for February 2027. | Dynamic search ads listed, serving | These ads have a fixed end. New ones are a transition surface. | Build no new Dynamic Search Ads. Plan the move to AI Max before February 2027, in a campaign that bids on conversions and is not limited by budget, because Google says AI Max needs conversion based Smart Bidding and is not effective while limited by budget. | Official (references/search-campaign-setup.md) |
| July 21, 2026. Policy decisions older than 6 months cannot be appealed in the account. | AD-02 fails | The appeal window is limited. | Fix the cause, then appeal soon. 3 appeals per ad, at least 24 hours apart. If an appeal of a fixed ad fails, a small edit to the text or final URL forces a new crawl. | Official (references/compliance.md) |
| August 17, 2026, rollout finished August 27, 2026. Budget limited Target CPA and Target ROAS campaigns bid toward their target. | A campaign in the August 17 table | Added budget buys conversions at about the target, not at today's better figure. A campaign that beat its target before August will trend toward it. | Confirm the target is the one the business wants before any budget change. Do not add data exclusions or new bid limits only because of this. Judge after 1 to 2 conversion cycles. | Official (references/platform-changes-2026.md) |
| Same | Cost per conversion rose after August on a target campaign that is limited by budget | It may be the campaign moving to a loose target, not a fault. | Compare its cost per conversion with its target before diagnosing anything else. | Practitioner rule |
| Same | A Maximize campaign limited by budget, strategy name only | The file cannot show whether a target is set. | Ask the person to read the campaign's bid strategy. If a target is set, the rule applies. | Official (references/platform-changes-2026.md) |
| September 1 to 30, 2026. Campaigns with automatically created assets or campaign level broad match upgraded to AI Max. Migrated campaigns kept equivalent settings. | SE-M2, by hand | Any Search campaign may now have AI Max features on. | Ask the person to read each Search campaign's AI Max settings: search term matching, text customization, Final URL expansion. | Official (references/search-campaign-setup.md) |
| Same | AI Max on in a Manual CPC campaign | Search term matching does not work with Manual CPC. | Move the campaign to conversion based bidding at stage 5, or say AI Max is doing little there. | Official (references/search-campaign-setup.md) |
| Same | Final URL expansion on, with a tracking template | Dynamic landing pages can break when the landing page URL is handled wrong. | Check the tracking template before keeping it on. | Official (references/search-campaign-setup.md) |
| September 2026. Manual language targeting retired for Search and AI Max for Search. | Nothing in the files | Old language settings still show but no longer limit Search ads. | Never recommend adding or changing language targeting on Search. If the business relied on it, say it no longer does that job on Search. | Official (references/search-campaign-setup.md) |

## How big a change

- After turning AI Max on, wait at least 2 weeks before changes such as adding negatives (Official, references/search-campaign-setup.md).
- Target campaigns under the August 17 rule: judge after 1 to 2 conversion cycles (Official, references/platform-changes-2026.md).
- Adopting AI Max or changing the bidding goal needs learning, so change a handful of campaigns at a time (Official, spoken guidance, references/account-structure.md).
- No source gives a step size for a target. It is the person's decision.

## Failure modes

- **Treating Google's schedule as the account's state.** "Upgraded in September 2026" is a schedule. Read each campaign.
- **Blaming the team for Google's change.** A target campaign drifting toward its target after August 17, 2026 is the rule working.
- **A file that spans a change date.** Averages across August 17 mix two behaviours. Say so from FILES READ, and ask for a range after August 27, 2026 when it matters.

## Worked example

Northside Plumbing, files from October 14 to November 12, 2026, all after August 27, 2026. The August 17 line shows 0 campaigns on Target CPA or Target ROAS. Plumbing | Water Heaters is on Maximize Conversions and limited by budget, so ask whether a target CPA is set: if it is, the rule applies to it. Dynamic search ads: 0. BB-01 passed: 0 campaigns on Enhanced CPC. AD-02 failed on Hydro Jetting Specialists, so repair the destination and appeal inside the window. SE-M2 is open: ask for each Search campaign's AI Max settings, starting with Plumbing | Emergency, which is on Manual CPC with broad match keywords.

## What to tell the client

"Google changed several things this year. Two matter here: since August 17, a campaign with a target that is limited by budget bids toward that target, and since September, AI Max may be switched on in your Search campaigns. We check both settings before changing budgets."
