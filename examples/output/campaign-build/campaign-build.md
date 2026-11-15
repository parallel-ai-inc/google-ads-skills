# Campaign build: Northside Plumbing

**Everything is built paused.** Every campaign, ad group, keyword and ad in the import file is set to Paused. Nothing serves until a person enables it.

**Review every row in Google Ads Editor before you post.** Files in this layout were test imported into Google Ads Editor 2.14.2 with no errors.

## What the plan builds

- 1 campaign, 3 ad groups, 14 keywords (5 exact, 9 phrase, 0 broad), 4 responsive search ads with 41 headlines and 14 descriptions.
- 9 negative keywords: 5 in the list, 2 at campaign level, 2 at ad group level. Each was tested against every keyword of the build it can reach, and none blocks one.
- Daily budget, all campaigns: 120.00. The most Google can spend in one day is 240.00, and the most it can charge in one month is 3,648.00. (Official: references/build-limits-and-editor-import.md)

| Campaign | Daily budget | Most in a month | Bid strategy | Networks | Locations | Ad groups | Keywords | Ads |
|---|---|---|---|---|---|---|---|---|
| Sewer Line \| Search | 120.00 | 3,648.00 | Maximize conversions | Google Search | Denver, Colorado, United States; Aurora, Colorado, United States | 3 | 14 | 4 |

| Campaign | Ad group | Keywords | Exact | Phrase | Broad | Ads | Ad group negatives |
|---|---|---|---|---|---|---|---|
| Sewer Line \| Search | Sewer Line Repair | 5 | 2 | 3 | 0 | 2 | 1 |
| Sewer Line \| Search | Sewer Line Replacement | 5 | 1 | 4 | 0 | 1 | 1 |
| Sewer Line \| Search | Sewer Camera Inspection | 4 | 2 | 2 | 0 | 1 | 0 |

## What the check caught

The plan passed the check the first time.

The final plan passed 34 checks. Each names its source on the Checks sheet.

## Warnings to decide

A warning does not stop the files. Decide each one with the person.

1. Build: 2 of 3 ad groups have one responsive search ad: "Sewer Line Replacement", "Sewer Camera Inspection". Google's tip is at least 2 in each ad group. One is enough to launch. Add a second when there is a different message to test.
2. Campaign "Sewer Line | Search" > Ad group "Sewer Line Repair" > Keyword "sewer line repair": The account already has this keyword with the same match type: campaign "Drain Cleaning | Search", ad group "Sewer Repair" (Enabled). Two copies compete for the same searches. Decide which one keeps the search, and pause the other when this build goes live.

## Before launch

2 Stop launch items still open. Nothing may be enabled until each reads yes:

- Every final URL loads on mobile and on desktop, and matches its ad group. Owner: Not assigned. Open: not answered.
- The business approved the ad text. Owner: Dana. Open: answered no.

## Assumptions in the plan

- Maximize conversions, because the booking conversion already records in the account.
- Search Partners is off until results on Google Search are known.
- AI Max is off, because the person wants searches matched to the keywords in the plan at launch.
- Locations are Denver and Aurora only, the places the person named.
- One responsive search ad in the replacement and inspection ad groups. A second can follow once there is a different message to test.

## Files

- `build-for-google-ads-editor.csv`: 28 rows for Google Ads Editor, all paused: 1 campaign, 2 locations, 3 ad groups, 14 keywords, 4 negative keywords, 4 responsive search ads.
- `negative-keyword-list.txt`: 5 keywords for the negative keyword list "Northside | Never relevant". Paste it into a negative keyword list in Google Ads and apply the list to every campaign of this build. Quotation marks mean phrase match and square brackets mean exact match.
- `campaign-build.xlsx`: summary, campaigns, ad groups, keywords, ads, every line of ad text with its character count, negative keywords, the launch checklist, warnings, checks and what the check caught.
- `launch-checklist.md`: what must be true before launch, the import and review in Editor, launch day and the first 14 days, each with an owner.
- `campaign-build.json`: every number in this summary.

## How to import

1. In Google Ads Editor: Account, Import, From file. Choose `build-for-google-ads-editor.csv`. Check the column headers Editor shows. (Official: references/build-limits-and-editor-import.md)
2. Read the list of errors and warnings. Fix a problem in the plan and write the files again, so the workbook keeps matching.
3. Review imported changes. They arrive as proposed changes, and nothing reaches the account until it is posted. Keep them, resolve every location, then post. (Official: references/build-limits-and-editor-import.md)
4. Enable on launch day only, after the launch checklist's Stop launch items all read yes. Enable the campaign last.

## How the numbers were made

- Every count and sum comes from the checked plan. The import file was read back after writing. It holds 28 rows, one for each of the plan's 1 campaign, 2 locations, 3 ad groups, 14 keywords, 4 campaign or ad group negative keywords and 4 ads, and every status in it is Paused.
- Characters are counted the way Google counts them: a double width character, as in Chinese, Japanese or Korean, counts as 2. A code in braces is counted with its default text in its place, and a countdown as 8 characters. Every limit comes from references/build-limits-and-editor-import.md or references/ad-customizers.md and names its page there. (Official)
- The most in one day is the daily budget times 2. The most in one month is the daily budget times 30.4. (Official: references/build-limits-and-editor-import.md)
- Negative keywords were tested with Google's matching rules: exact, phrase and broad, with no close variants. (Official: references/keywords.md)
- Compared with the account: 4 campaigns from campaigns-report.csv; 9 keywords from keywords-report.csv.

## What this did not cover

- Search volume, cost per click and forecasts. Nothing here estimates traffic or results.
- Assets such as sitelinks, callouts and call assets, audiences, ad schedules, devices and location options. Set them in Editor.
- Pins. None are written. Pin in Editor after import if wanted.
- Customizer attributes and their values. Codes in the ad text are written as planned, but an attribute used by {CUSTOMIZER.Name:default text} must be created in Google Ads, with a value, before posting. Google Ads Editor 2.14.2 imported every code unchanged in a test on 2026-11-14, but did not flag an attribute missing from the account.
- Searches that have not happened. The negative test knows only this build's keywords. Negatives do not match close variants, so plural and singular forms each need their own.
- Location names were compared as text only. Overlapping places with different names were not found.
- Tested in Google Ads Editor 2.14.2 on 2026-11-14: this layout imports with no errors, and Editor reads each row as written. Review every row in Editor before you post.
