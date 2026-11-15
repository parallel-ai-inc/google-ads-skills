# Build limits and the Google Ads Editor import file

Written by hand. To be re-read against the source before release. Every Google page below was read on 2026-11-13. The generated references in this folder do not carry these numbers, so they are kept here with the page each one comes from.

## Official: responsive search ads

Source: Google Ads Help, "About responsive search ads", https://support.google.com/google-ads/answer/7684791

| Part | Limit |
|---|---|
| Headlines in one ad | At least 3, at most 15 |
| Descriptions in one ad | At least 2, at most 4 |
| One headline | 30 characters |
| One description | 90 characters |
| Path 1 and Path 2 | 15 characters each |
| Double width characters, as in Chinese, Japanese and Korean | Each counts as 2 |

- Headlines and descriptions can show in any order, so each one must make sense alone and beside any other.
- Google's tips on the same page: include at least one of the ad group's keywords in the headlines, and provide as many unique headlines as you can.
- Google's tip on the same page: at least 2 responsive search ads per ad group with Good or Excellent Ad Strength.
- Text that must show in every ad has to be pinned to Headline position 1, Headline position 2 or Description position 1. Google says pinning is not recommended for most advertisers.

The generated file `ad-specs-limits.md` carries the limit of 3 enabled responsive search ads per ad group.

## Official: keywords

- A keyword can have up to 10 words. Source: Google Ads Help, "Add keywords", https://support.google.com/google-ads/answer/7476658
- A keyword's text is at most 80 characters and 10 words. Source: Google Ads API reference, KeywordInfo, https://developers.google.com/google-ads/api/reference/rpc/v25/KeywordInfo

## Official: account limits that a build can reach

Source: Google Ads Help, "About your Google Ads account limits", https://support.google.com/google-ads/answer/6372658

- 20,000 ad groups per campaign.
- 20,000 ad group targeting items per ad group. Keywords are targeting items.
- 3 enabled responsive search ads per ad group.
- 10,000 negative keywords per campaign.
- 5,000 keywords per negative keyword list.

## Official: what a daily budget can spend

Source: Google Ads Help, "About spending limits", https://support.google.com/google-ads/answer/10486637

- On one day a campaign can spend up to 2 times its average daily budget.
- In one month a campaign is charged at most 30.4 times its average daily budget.

## Official: ad text that Google's editorial policy does not allow

Sources: Advertising Policies Help, "Editorial", https://support.google.com/adspolicy/answer/6021546, with "Punctuation and symbols", https://support.google.com/adspolicy/answer/14847994, and "Capitalization", https://support.google.com/adspolicy/answer/14848295

- A phone number in ad text.
- Punctuation or symbols repeated one after another. Google's example is "flowers!!".
- Emoji, and other invalid or unsupported characters.
- Capital letters used for effect. Google's example is "FLOWERS". Common abbreviations such as "ASAP" may be allowed.

Google decides these in ad review. The check in this skill only points at text to read again. It does not refuse it.

## Official: the Google Ads Editor import file

Sources: Google Ads Editor Help, "Prepare a CSV file", https://support.google.com/google-ads/editor/answer/56368, "CSV file columns", https://support.google.com/google-ads/editor/answer/57747, "Import a CSV file", https://support.google.com/google-ads/editor/answer/30564, "Manage bid strategies in Google Ads Editor", https://support.google.com/google-ads/editor/answer/94241, and "Add a new location target to a campaign", https://support.google.com/google-ads/editor/answer/33114

**The file**

- Editor imports CSV. It does not import XLS files.
- Each row describes one item, such as a campaign, a targeted location, a keyword or an ad. Rows of different kinds can share one file.
- Column headers must be in English. Capitalisation and spaces do not matter.
- A blank cell means Editor makes no change to that field.
- When a new campaign's settings cannot be read, Editor uses its default campaign settings.

**Columns this skill writes**

| Row | Columns | Values |
|---|---|---|
| Campaign | Campaign, Campaign Type, Networks, Campaign Daily Budget, Bid Strategy Type, Start Date, End Date, Campaign Status | Campaign Type: Search. Networks: Google Search, or Google Search;Search Partners. The budget must be above zero. Dates are YYYY-MM-DD and a start date cannot be in the past. Status: Enabled, Paused or Removed |
| Bid target | Target CPA, Target ROAS | Written on the campaign row. Google's example shows 12.34 for Target CPA and 12.34% for Target ROAS |
| Location | Campaign, Location | One location per row |
| Ad group | Campaign, Ad Group, Max CPC, Ad Group Status | Status: Enabled, Paused or Removed |
| Keyword | Campaign, Ad Group, Keyword, Criterion Type, Final URL, Status | Criterion Type: Broad, Phrase or Exact. Several final URLs in one cell are separated by spaces, so one URL must not contain a space |
| Negative keyword | Campaign, Ad Group, Keyword, Criterion Type | Negative for an ad group negative and Campaign negative for a campaign negative, with the match type. A negative cannot be paused. A status of Paused on a negative has no effect |
| Responsive search ad | Campaign, Ad Group, Headline 1 to Headline 15, Description 1 to Description 4, Path 1, Path 2, Final URL, Status | Status: Enabled, Paused or Removed |

**Bid strategies Editor lists:** Target ROAS, Target CPA, Target impression share, Maximize conversions, Maximize conversion value, Maximize clicks, Manual CPC, Manual CPM, Manual CPV. This skill writes the six that apply to Search and whose import columns Google shows: Manual CPC, Maximize clicks, Maximize conversions, Maximize conversion value, Target CPA and Target ROAS.

**How Editor treats a row**

- Editor decides for each row whether to edit an item that exists or create a new one, from the columns that identify the item. A keyword is identified by its campaign, ad group, keyword text and match type. So a campaign row that carries the name of a campaign already in the account edits that campaign.
- Imported rows arrive as proposed changes. The person keeps or rejects them, and nothing reaches the account until it is posted.
- A campaign with no targeted location can show in all locations.
- A location typed by name must be resolved in Editor before posting. An unresolved location shows a yellow warning.

**The import steps:** Account, Import, From file. Check the column headers Editor shows. Import. Read the list of errors and warnings. Review imported changes. Keep proposed changes or Reject proposed changes.

## Tested in Google Ads Editor 2.14.2 on 2026-11-14

Each file this pack writes for Editor was imported into a test account, read in Editor's review, and rejected. Nothing was posted. The two negative keyword text lists were pasted into a new negative keyword list in the Google Ads web interface: one per line, quotation marks read as phrase match, square brackets as exact match, no symbols as broad match.

- The build file imported with no errors: 1 campaign, 3 ad groups, 14 keywords, 4 negative keywords, 2 locations and 4 responsive search ads, every one Paused, nothing skipped. A responsive search ad row needs no `Ad type` column.
- `Campaign Negative Phrase`, `Campaign Negative Broad` and `Negative Phrase` read as written, at campaign or ad group level.
- `Campaign Daily Budget` reads as the average daily budget. `Target ROAS` written as `360.00%` reads as Target ROAS 360%. A blank cell leaves the setting as it is.
- **Official:** Google Ads asks advertisers to declare for each campaign whether it contains EU political ads (https://support.google.com/adspolicy/answer/15577076). Editor will not post a campaign without the declaration. The column is `EU political ads`, and Editor writes the value `Doesn't have EU political ads` for no.
- AI Max: an imported Search campaign gets AI Max Enabled unless the file says otherwise. The column is `AI Max`, with `Enabled` or `Disabled`; `Disabled` imports as off. Editor's export also carries `Text customization` and `Final URL expansion` with the same values.
- A campaign name that matches no campaign in the account creates a new campaign: Enabled, Manual CPC, with Search partners and the Display Network on. In the import summary, an edit file must show its rows under Updated. A row under Added means a name did not match.
- Check locations resolves a typed name (Denver, Colorado, United States became City 1014485) and turns that proposed location into an unposted change.
- A radius target is written as `15 mi around (34.052235, -118.243683)`. A radius around a named city needs that city's coordinates, so this skill writes the named place and the person sets the radius in Editor.
- New campaigns show two warnings, Search partners and the Display Network off, and new ad groups under Maximize conversions show "no bids". These are Editor's own advice, not errors.

## Not documented by Google

These are not on the pages above. Treat them as unknown until someone has tested an import.

- The values for the `Headline 1 position` and `Description 1 position` columns, which carry pins. The page lists the columns and gives no values. This skill writes no pins.

## Practitioner rules

- Build everything paused, import, review in Editor, post, then enable on launch day. Enable the campaign last.
- Give a new campaign a name the account has never used.
- Put the keyword's words in at least one headline, and send each ad group to the page that matches its theme.
- Keep three levels of negative keywords apart: a list for searches that are wrong for the whole business, campaign negatives for searches that are wrong for this service, and ad group negatives to send a search to the right ad group.
- Test every negative against the build's own keywords before it goes in.
